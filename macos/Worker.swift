import AppKit
import ApplicationServices
import CoreGraphics
import ScreenCaptureKit
import CoreMedia
import CoreImage
import ImageIO
import UniformTypeIdentifiers
import Foundation
import Darwin

struct Failure: Error {
    let code: String
    let message: String
}

final class FrameCollector: NSObject, SCStreamOutput, SCStreamDelegate, @unchecked Sendable {
    let lock=NSLock()
    var latest:CGImage?
    var failure:String?
    let context=CIContext()
    func stream(_ stream:SCStream,didStopWithError error:Error) {lock.lock();failure=String(describing:error);lock.unlock()}
    func stream(_ stream:SCStream,didOutputSampleBuffer buffer:CMSampleBuffer,of type:SCStreamOutputType) {
        guard type == .screen,buffer.isValid,
              let items=CMSampleBufferGetSampleAttachmentsArray(buffer,createIfNecessary:false) as? [[SCStreamFrameInfo:Any]],
              items.first?[.status] as? Int == SCFrameStatus.complete.rawValue,
              let pixels=buffer.imageBuffer else{return}
        let ci=CIImage(cvPixelBuffer:pixels)
        guard let image=context.createCGImage(ci,from:ci.extent) else{return}
        lock.lock();latest=image;lock.unlock()
    }
    func snapshot()->(CGImage?,String?) {lock.lock();defer{lock.unlock()};return(latest,failure)}
}

@MainActor final class Worker {
    let birth=Date()
    let persistent:Bool
    var children=[Process]()
    var stopping=false
    // No unverified boolean supplied by a caller can enable audio isolation.
    // A measured backend must replace this before generic execution/input is enabled.
    let audioIsolated=false
    init(persistent:Bool){self.persistent=persistent}
    func bound(_ request:[String:Any]) throws -> SessionFacts {
        let facts=currentFacts()
        let uid=(request["expected_uid"] as? NSNumber)?.uint32Value
        let sid=(request["expected_session_id"] as? NSNumber)?.uint32Value
        if let denial=facts.denial(expectedUID:uid,expectedSession:sid,requireBinding:true) {
            throw Failure(code:denial,message:"Operation requires an explicitly bound, different-user, non-console graphical login. No host-desktop fallback is permitted.")
        }
        return facts
    }
    func status(_ facts:SessionFacts)->[String:Any] {
        let p=permissions()
        let eligible=facts.denial(expectedUID:nil,expectedSession:nil,requireBinding:false)==nil
        return ["identity":dictionary(facts),"permissions":p,
            "capabilities":["separate_session_detected":eligible,"capture":eligible && p["screen_capture"]==true,
                "native_input":false,"generic_exec":false,"audio_isolation":false,
                "gpu":"not_measured_in_separate_session","live_acceptance_complete":false],
            "audio":["status":"unverified","policy":"exec_and_input_blocked","reason":"No measured per-session mute or isolated output provider is installed."],
            "lifetime":["worker_pid":ProcessInfo.processInfo.processIdentifier,"started_at":ISO8601DateFormatter().string(from:birth),
                "persistent":persistent,"owns_os_login":false,"stop_logs_off_user":false,"owned_child_count":children.filter{$0.isRunning}.count]]
    }
    func response(_ request:[String:Any]) async -> [String:Any] {
        let op=request["op"] as? String ?? ""
        do {
            if op == "doctor" || op == "preflight" {return ["ok":true,"platform":"macos","session":status(currentFacts()),"result":["read_only":true,"permission_prompts":false]]}
            if op == "start" {throw Failure(code:"macos_session_setup_required",message:"This adapter does not create login sessions. Establish the separately authenticated GUI using the reviewed setup procedure, then attach from that GUI context.")}
            if op == "stop" {
                // No arbitrary PID input: Process objects were created by this worker only.
                var stopped=[Int32]()
                for p in children where p.isRunning {stopped.append(p.processIdentifier);p.terminate()}
                stopping=true
                return ["ok":true,"platform":"macos","result":["owned_processes_signalled":stopped,"os_login_retained":true]]
            }
            let facts=try bound(request)
            switch op {
            case "attach","status":return ["ok":true,"platform":"macos","session":status(facts),"result":["attached_existing_login":true,"live_acceptance_complete":false]]
            case "capture":
                let result=try await capture(request)
                return ["ok":true,"platform":"macos","session":status(try bound(request)),"result":result]
            case "exec","input":
                guard audioIsolated else {throw Failure(code:"audio_isolation_unverified",message:"Generic execution/input could cause audible output. A measured isolated or muted audio provider is required before enabling these operations.")}
                // Implementations are staged behind the non-bypassable audio gate.
                let result=op == "exec" ? try launch(request) : try input(request)
                return ["ok":true,"platform":"macos","session":status(facts),"result":result]
            default:throw Failure(code:"unknown_operation",message:"Unknown native worker operation.")
            }
        } catch let e as Failure {return ["ok":false,"platform":"macos","session":status(currentFacts()),"error":["code":e.code,"message":e.message]]}
        catch {return ["ok":false,"platform":"macos","error":["code":"native_operation_failed","message":String(describing:error)]]}
    }
    func capture(_ req:[String:Any]) async throws -> [String:Any] {
        _=try bound(req)
        guard CGPreflightScreenCaptureAccess() else {throw Failure(code:"screen_capture_permission_required",message:"Screen Recording permission is absent for this worker identity. No permission was requested.")}
        guard let output=req["output"] as? String,output.hasPrefix("/") else {throw Failure(code:"invalid_output",message:"Capture output must be an absolute file path.")}
        let url=URL(fileURLWithPath:output)
        guard !FileManager.default.fileExists(atPath:output) else {throw Failure(code:"output_exists",message:"Capture does not overwrite existing files.")}
        let content=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:false)
        _=try bound(req)
        let filter:SCContentFilter
        let bounds:CGRect
        var target=[String:Any]()
        if let wid=(req["window_id"] as? NSNumber)?.uint32Value {
            guard let w=content.windows.first(where:{$0.windowID==wid}) else {throw Failure(code:"window_not_in_session",message:"Requested window was not enumerated in the guarded GUI session.")}
            filter=SCContentFilter(desktopIndependentWindow:w);bounds=w.frame
            target=["window_id":wid,"pid":w.owningApplication?.processID ?? -1]
        } else {
            let wanted=(req["display_id"] as? NSNumber)?.uint32Value
            guard let display=content.displays.first(where:{wanted == nil || $0.displayID==wanted}) else {throw Failure(code:"display_not_in_session",message:"No matching display exists in the guarded GUI session.")}
            filter=SCContentFilter(display:display,excludingWindows:[]);bounds=display.frame
            target=["display_id":display.displayID]
        }
        let config=SCStreamConfiguration()
        config.width=max(1,min(7680,Int(bounds.width)));config.height=max(1,min(4320,Int(bounds.height)))
        config.showsCursor=false;config.capturesAudio=false;config.ignoreShadowsSingleWindow=true
        config.minimumFrameInterval=CMTime(value:1,timescale:10)
        let collector=FrameCollector()
        let stream=SCStream(filter:filter,configuration:config,delegate:collector)
        try stream.addStreamOutput(collector,type:.screen,sampleHandlerQueue:DispatchQueue(label:"deskhelper.guarded.capture"))
        _=try bound(req)
        try await stream.startCapture()
        do {
            var image:CGImage?
            for _ in 0..<50 {
                _=try bound(req)
                let snap=collector.snapshot()
                if let failure=snap.1 {throw Failure(code:"capture_stream_failed",message:failure)}
                if let frame=snap.0 {image=frame;break}
                try await Task.sleep(nanoseconds:100_000_000)
            }
            try await stream.stopCapture()
            _=try bound(req)
            guard let image else {throw Failure(code:"capture_timeout",message:"No complete frame arrived within five seconds.")}
            let png=NSMutableData()
            guard let dest=CGImageDestinationCreateWithData(png,UTType.png.identifier as CFString,1,nil) else {throw Failure(code:"capture_write_failed",message:"Cannot create PNG encoder.")}
            CGImageDestinationAddImage(dest,image,nil)
            guard CGImageDestinationFinalize(dest) else {throw Failure(code:"capture_write_failed",message:"PNG encoding failed.")}
            _=try bound(req)
            let fd=Darwin.open(url.path,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0o600)
            guard fd>=0 else {throw Failure(code:"capture_write_failed",message:"Cannot exclusively create private PNG output.")}
            let handle=FileHandle(fileDescriptor:fd,closeOnDealloc:true)
            try handle.write(contentsOf:png as Data)
            try handle.close()
            return ["path":output,"width":image.width,"height":image.height,"captured_at":ISO8601DateFormatter().string(from:Date()),"target":target,"audio_captured":false]
        } catch {try? await stream.stopCapture();throw error}
    }
    func launch(_ req:[String:Any]) throws -> [String:Any] {
        _=try bound(req)
        guard persistent else {throw Failure(code:"persistent_worker_required",message:"Execution requires a persistent worker that retains ownership of child processes.")}
        guard let argv=req["argv"] as? [String],let exe=argv.first,exe.hasPrefix("/") else {throw Failure(code:"invalid_argv",message:"Provide an absolute executable and an argument array.")}
        let p=Process();p.executableURL=URL(fileURLWithPath:exe);p.arguments=Array(argv.dropFirst())
        if let cwd=req["cwd"] as? String {p.currentDirectoryURL=URL(fileURLWithPath:cwd)}
        p.standardInput=FileHandle.nullDevice;p.standardOutput=FileHandle.nullDevice;p.standardError=FileHandle.nullDevice
        _=try bound(req);try p.run();children.append(p)
        return ["pid":p.processIdentifier,"ownership":"direct_child_only","descendant_cleanup_guaranteed":false]
    }
    func input(_ req:[String:Any]) throws -> [String:Any] {
        _=try bound(req)
        guard permissions()["accessibility"]==true,CGPreflightPostEventAccess() else {throw Failure(code:"native_input_permission_required",message:"Accessibility/post-event permission is absent. No permission was requested.")}
        let source=CGEventSource(stateID:.privateState)
        var events=[CGEvent]()
        if let text=req["text"] as? String {
            guard text.utf16.count<=4096 else {throw Failure(code:"text_too_long",message:"Maximum 4096 UTF-16 code units per request.")}
            let chars=Array(text.utf16)
            for down in [true,false] {guard let e=CGEvent(keyboardEventSource:source,virtualKey:0,keyDown:down) else {continue};e.keyboardSetUnicodeString(stringLength:chars.count,unicodeString:chars);events.append(e)}
        } else if let key=req["key"] as? String {
            let codes:[String:CGKeyCode]=["return":36,"enter":36,"tab":48,"space":49,"escape":53,"backspace":51,"delete":117,"left":123,"right":124,"down":125,"up":126]
            guard let code=codes[key.lowercased()] else {throw Failure(code:"unsupported_key",message:"Supported named keys: return, tab, space, escape, backspace, delete, arrows.")}
            for down in [true,false] {if let e=CGEvent(keyboardEventSource:source,virtualKey:code,keyDown:down){events.append(e)}}
        } else if let point=(req["click"] ?? req["move"]) as? [Double],point.count==2,point.allSatisfy({$0.isFinite}) {
            let p=CGPoint(x:point[0],y:point[1])
            let button=(req["button"] as? Int) ?? 1
            guard (1...3).contains(button) else {throw Failure(code:"invalid_button",message:"Button must be 1 (left), 2 (middle), or 3 (right).")}
            let b:CGMouseButton=button==1 ? .left : button==2 ? .center : .right
            let types:[CGEventType]=req["click"] != nil ? (button==1 ? [.leftMouseDown,.leftMouseUp] : button==2 ? [.otherMouseDown,.otherMouseUp] : [.rightMouseDown,.rightMouseUp]) : [.mouseMoved]
            for type in types {if let e=CGEvent(mouseEventSource:source,mouseType:type,mouseCursorPosition:p,mouseButton:b){events.append(e)}}
        } else {throw Failure(code:"invalid_input",message:"Provide text, named key, click or move coordinates.")}
        for event in events {_=try bound(req);event.post(tap:.cgSessionEventTap)}
        return ["events_posted":events.count,"tap":"current_login_session","delivery_verified":false]
    }
    func cleanup(){for p in children where p.isRunning {p.terminate()}}
}

@main struct Main {
    @MainActor static func main() async {
        if CommandLine.arguments.contains("--self-test") {emit(guardSelfTest());return}
        NSApplication.shared.setActivationPolicy(.prohibited)
        let persistent=CommandLine.arguments.contains("--stdio")
        let worker=Worker(persistent:persistent)
        defer{worker.cleanup()}
        while let line=readLine() {
            do {
                guard let data=line.data(using:.utf8),let req=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw Failure(code:"invalid_json",message:"Expected one JSON request object per line.")}
                emit(await worker.response(req))
            } catch {emit(["ok":false,"platform":"macos","error":["code":"invalid_request","message":String(describing:error)]])}
            if !persistent || worker.stopping {break}
        }
    }
    static func emit(_ value:[String:Any]) {
        if let data=try? JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]),let text=String(data:data,encoding:.utf8){print(text);fflush(stdout)}
    }
}

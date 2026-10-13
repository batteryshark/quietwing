import AppKit
import ScreenCaptureKit
import CoreMedia
import ImageIO
import UniformTypeIdentifiers
import Darwin
final class FrameCollector:NSObject,SCStreamOutput,SCStreamDelegate,@unchecked Sendable {
    let lock=NSLock();var image:CGImage?;var streamError:String?
    func stream(_ stream:SCStream,didStopWithError error:Error) { lock.lock();streamError=String(describing:error);lock.unlock() }
    func stream(_ stream:SCStream,didOutputSampleBuffer sampleBuffer:CMSampleBuffer,of type:SCStreamOutputType) {
        guard type == .screen,let buffer=sampleBuffer.imageBuffer,
            let attachments=CMSampleBufferGetSampleAttachmentsArray(sampleBuffer,createIfNecessary:false) as? [[SCStreamFrameInfo:Any]],
            let raw=attachments.first?[.status] as? Int,raw == SCFrameStatus.complete.rawValue else {return}
        let context=CIContext();let image=context.createCGImage(CIImage(cvPixelBuffer:buffer),from:CGRect(x:0,y:0,width:CVPixelBufferGetWidth(buffer),height:CVPixelBufferGetHeight(buffer)))
        lock.lock();self.image=image;lock.unlock()
    }
    func read()->(CGImage?,String?) { lock.lock();defer{lock.unlock()};return(image,streamError) }
}

@main struct Capture {
 @MainActor static func main() async {
  NSApplication.shared.setActivationPolicy(.prohibited)
  if CommandLine.arguments.contains("--preflight") {print("{\"ok\":true,\"platform\":\"macos\",\"screen_capture_preflight\":\(CGPreflightScreenCaptureAccess())}");return}
  var r:[String:Any] = ["ok":false,"platform":"macos","screen_capture_preflight":CGPreflightScreenCaptureAccess()]
  do {
   let args=CommandLine.arguments
   guard args.count==4,let pid=Int32(args[1]),let windowID=UInt32(args[2]),args[3].hasPrefix("/") else {throw NSError(domain:"Capture",code:1,userInfo:[NSLocalizedDescriptionKey:"Require owned PID, window and absolute output"])}
   guard CGPreflightScreenCaptureAccess() else {throw NSError(domain:"Capture",code:2,userInfo:[NSLocalizedDescriptionKey:"Capture permission missing; no prompt requested"])}
   guard let app=NSRunningApplication(processIdentifier:pid),app.bundleIdentifier=="dev.desktop-session-helper.vm",!app.isTerminated else{throw NSError(domain:"Capture",code:3,userInfo:[NSLocalizedDescriptionKey:"PID is not the owned VM bundle"])}
   let content=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:false)
   guard let target=content.windows.first(where:{$0.windowID==windowID && $0.owningApplication?.processID==pid}) else{throw NSError(domain:"Capture",code:4,userInfo:[NSLocalizedDescriptionKey:"Exact owned window unavailable"])}
   guard !NSScreen.screens.contains(where:{$0.frame.intersects(target.frame)}) else{throw NSError(domain:"Capture",code:5,userInfo:[NSLocalizedDescriptionKey:"Target is not entirely offscreen"])}
   let config=SCStreamConfiguration();config.width=1024;config.height=768;config.showsCursor=false;config.capturesAudio=false;config.ignoreShadowsSingleWindow=true;config.minimumFrameInterval=CMTime(value:1,timescale:15)
   let collector=FrameCollector();let stream=SCStream(filter:SCContentFilter(desktopIndependentWindow:target),configuration:config,delegate:collector)
   try stream.addStreamOutput(collector,type:.screen,sampleHandlerQueue:DispatchQueue(label:"owned.vm.capture"));try await stream.startCapture()
   var image:CGImage?;var reason:String?
   for _ in 0..<70 {try await Task.sleep(nanoseconds:100_000_000);(image,reason)=collector.read();if image != nil || reason != nil{break}}
   try? await stream.stopCapture();guard let image else{throw NSError(domain:"Capture",code:6,userInfo:[NSLocalizedDescriptionKey:reason ?? "No complete VM frame in 7 seconds"])}
   let data=NSMutableData();guard let destination=CGImageDestinationCreateWithData(data,UTType.png.identifier as CFString,1,nil) else{throw NSError(domain:"Capture",code:7)};CGImageDestinationAddImage(destination,image,nil);guard CGImageDestinationFinalize(destination) else{throw NSError(domain:"Capture",code:8)}
   let fd=open(args[3],O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW,0o600);guard fd>=0 else{throw NSError(domain:"Capture",code:9,userInfo:[NSLocalizedDescriptionKey:"Output must be a new file"])};defer{close(fd)}
   let bytes=data as Data;let written=bytes.withUnsafeBytes{Darwin.write(fd,$0.baseAddress,$0.count)};guard written==bytes.count else{throw NSError(domain:"Capture",code:10)}
   r["ok"]=true;r["result"]=["path":args[3],"width":image.width,"height":image.height,"captured_at":Date().timeIntervalSince1970,"window_id":windowID,"owner_pid":pid,"only_owned_guest_view":true]
  }catch {r["error"]=["code":"vm_capture_failed","message":String(describing:error)]}
  print(String(data:try! JSONSerialization.data(withJSONObject:r,options:.sortedKeys),encoding:.utf8)!);exit(r["ok"] as? Bool == true ? 0:1)
 }
}

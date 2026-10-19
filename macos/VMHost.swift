import AppKit
import Virtualization
import ScreenCaptureKit
import CoreMedia
import ImageIO
import UniformTypeIdentifiers
import Darwin

struct VMFailure: Error { let code:String; let message:String }
func failure(_ c:String,_ m:String)->VMFailure { VMFailure(code:c,message:m) }
func encoded(_ v:[String:Any])->Data { (try? JSONSerialization.data(withJSONObject:v,options:[.sortedKeys])) ?? Data("{}".utf8) }
// All events are constructed before pressing. Delivery is synchronous on the owner
// actor: no lifecycle/input request can interleave and a disconnected caller cannot
// strand a button. Events go to the owned view, never NSApp/global event posting.
@MainActor func guestDrag(_ request:[String:Any],windowNumber:Int,
    deliver:(NSEvent)->Void,pause:(UInt32)->Void = {usleep($0)}) throws -> Int {
    guard let xy=request["drag"] as? [Double],xy.count==4,xy.allSatisfy({$0.isFinite}),
        xy[0]>=0,xy[0]<1024,xy[1]>=0,xy[1]<768,
        xy[2]>=0,xy[2]<1024,xy[3]>=0,xy[3]<768 else {
        throw failure("invalid_input","Drag requires two bounded guest points")
    }
    let button=request["button"] as? Int ?? 1
    guard [1,2,3].contains(button) else{throw failure("invalid_input","Invalid drag button")}
    let down:NSEvent.EventType=button==3 ? .rightMouseDown:button==2 ? .otherMouseDown:.leftMouseDown
    let dragged:NSEvent.EventType=button==3 ? .rightMouseDragged:button==2 ? .otherMouseDragged:.leftMouseDragged
    let up:NSEvent.EventType=button==3 ? .rightMouseUp:button==2 ? .otherMouseUp:.leftMouseUp
    let began=ProcessInfo.processInfo.systemUptime
    func event(_ type:NSEvent.EventType,_ fraction:Double,_ offset:Double) throws -> NSEvent {
        let location=NSPoint(x:xy[0]+(xy[2]-xy[0])*fraction,y:768-(xy[1]+(xy[3]-xy[1])*fraction))
        guard let e=NSEvent.mouseEvent(with:type,location:location,modifierFlags:[],timestamp:began+offset,
            windowNumber:windowNumber,context:nil,eventNumber:0,clickCount:1,pressure:type==up ? 0:1)
            else{throw failure("event_failed","Could not build guest drag event")}
        // AppKit's mouse factory defaults buttonNumber to zero even for non-left
        // event types. Preserve the window-local event and identify the button.
        if button != 1 {
            guard let raw=e.cgEvent else{throw failure("event_failed","Could not identify drag button")}
            raw.setIntegerValueField(.mouseEventButtonNumber,value:button==3 ? 1:2)
            guard let identified=NSEvent(cgEvent:raw) else{throw failure("event_failed","Could not build identified drag event")}
            return identified
        }
        return e
    }
    let press=try event(down,0,0),release=try event(up,1,0.35)
    let moves=try (1...20).map{try event(dragged,Double($0)/20,0.05+Double($0)*0.015)}
    deliver(press);defer{deliver(release)}
    pause(50_000)
    for e in moves{pause(15_000);deliver(e)}
    return moves.count+2
}
// Prebuild both edges. Modifiers use flagsChanged, not ordinary keyDown/up.
// The owner guards this whole async operation against lifecycle/other input.
// Yield between reports: blocking its main actor can coalesce USB key state.
@MainActor func guestKey(code:UInt16,characters:String,modifiers:NSEvent.ModifierFlags,
    holdMS:Int,windowNumber:Int,deliver:(NSEvent)->Void,
    pause:(UInt32) async -> Void = {try? await Task.sleep(nanoseconds:UInt64($0)*1000)}) async throws {
    guard (0...5000).contains(holdMS) else{throw failure("invalid_input","hold_ms must be 0–5000")}
    let keys:[(NSEvent.ModifierFlags,UInt16)]=[(.command,55),(.shift,56),(.option,58),(.control,59)]
    var active:NSEvent.ModifierFlags=[],press=[NSEvent](),release=[NSEvent]()
    func event(_ key:UInt16,_ type:NSEvent.EventType,_ flags:NSEvent.ModifierFlags,_ text:String="") throws -> NSEvent {
        // VZ's keyboard tracks left/right USB modifiers from the device-specific
        // bits, not just AppKit's aggregate command/shift flags. Match real left
        // modifier reports without consulting or adopting the host keyboard.
        var raw=flags.rawValue
        for (flag,bit):(NSEvent.ModifierFlags,UInt) in [(.command,0x8),(.shift,0x2),(.option,0x20),(.control,0x1)] where flags.contains(flag){raw |= bit}
        guard let e=NSEvent.keyEvent(with:type,location:.zero,modifierFlags:NSEvent.ModifierFlags(rawValue:raw),
            timestamp:ProcessInfo.processInfo.systemUptime,windowNumber:windowNumber,context:nil,
            characters:text,charactersIgnoringModifiers:text.lowercased(),isARepeat:false,keyCode:key)
            else{throw failure("event_failed","Could not build guest keyboard event")}
        return e
    }
    for (flag,key) in keys where modifiers.contains(flag){active.insert(flag);press.append(try event(key,.flagsChanged,active))}
    let standalone=keys.first(where:{$0.1==code})
    if let (flag,_) = standalone {
        guard modifiers.isEmpty else{throw failure("invalid_key","Standalone modifier cannot be a chord target")}
        press.append(try event(code,.flagsChanged,flag));release.append(try event(code,.flagsChanged,[]))
    }else{
        press.append(try event(code,.keyDown,modifiers,characters))
        release.append(try event(code,.keyUp,modifiers,characters))
    }
    for (flag,key) in keys.reversed() where modifiers.contains(flag){active.remove(flag);release.append(try event(key,.flagsChanged,active))}
    for e in press.dropLast(){deliver(e);await pause(10_000)}
    deliver(press.last!)
    // Even a tap must survive USB/report scheduling. No synthetic autorepeat.
    await pause(UInt32(holdMS == 0 ? 30:holdMS)*1000)
    // No throwing/cancellable work after press; caller disconnection cannot
    // cancel this owner task. Reverse release runs before clearing its busy gate.
    for e in release{deliver(e);await pause(10_000)}
}
final class QuietPanel:NSPanel {
    override var canBecomeKey:Bool { false }
    override var canBecomeMain:Bool { false }
    override func constrainFrameRect(_ rect:NSRect,to screen:NSScreen?)->NSRect { rect }
}
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
@MainActor final class VMHost:NSObject,NSApplicationDelegate,@preconcurrency VZVirtualMachineDelegate {
    let root:URL;let id:String;let instance=UUID().uuidString;let began=Date();let pid=getpid()
    var phase="starting";var lastError:String?;var machine:VZVirtualMachine?;var installer:VZMacOSInstaller?
    var panel:QuietPanel!;var view:VZVirtualMachineView!;var timer:Timer?;var lockFD:Int32 = -1
    var frontBefore:pid_t = -1;var foregroundSeen=Set<pid_t>();var lastInputAt:Double?;var captures=0;var controllerDisconnects=0;var cursorBefore=CGPoint.zero
    var bridgeBusy=false;var inputBusy=false
    var listener:Int32 = -1;var shouldInstall:Bool;var canSaveRestore=false;var terminating=false;var startupTask:Task<Void,Never>?
    init(root:URL,id:String,install:Bool) {self.root=root;self.id=id;self.shouldInstall=install}
    func file(_ name:String)->URL {root.appendingPathComponent(name)}
    func write(_ object:[String:Any],_ name:String) {try? encoded(object).write(to:file(name),options:.atomic);chmod(file(name).path,0o600)}
    func applicationDidFinishLaunching(_ notification:Notification) {
        signal(SIGPIPE,SIG_IGN)
        frontBefore=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1
        cursorBefore=CGEvent(source:nil)?.location ?? .zero
        do {
            var st=stat();guard lstat(root.path,&st)==0,st.st_uid==getuid(),(st.st_mode & 0o077)==0,(st.st_mode & S_IFMT)==S_IFDIR else {throw failure("unsafe_state","State must be private, owned and not a symlink")}
            lockFD=open(file("owner.lock").path,O_CREAT|O_RDWR|O_NOFOLLOW,0o600)
            guard lockFD>=0,flock(lockFD,LOCK_EX|LOCK_NB)==0 else {throw failure("already_running","Another host owns this VM")}
            try listen()
            panel=QuietPanel(contentRect:NSRect(x:-30000,y:-30000,width:1024,height:768),styleMask:[.borderless,.nonactivatingPanel],backing:.buffered,defer:false)
            panel.isReleasedWhenClosed=false;panel.title="Deskhelper isolated guest";panel.ignoresMouseEvents=true;panel.hidesOnDeactivate=false;panel.isExcludedFromWindowsMenu=true
            view=VZVirtualMachineView(frame:NSRect(x:0,y:0,width:1024,height:768));view.capturesSystemKeys=false;view.automaticallyReconfiguresDisplay=false
            panel.contentView=view;panel.orderFrontRegardless();panel.makeFirstResponder(view)
            timer=Timer.scheduledTimer(withTimeInterval:0.25,repeats:true){[weak self] _ in MainActor.assumeIsolated{self?.observe()}}
            observe()
            startupTask=Task { do { try await configure();try Task.checkCancellation();if terminating{return};if shouldInstall {try await install()} else {try await boot()} } catch {phase="failed";lastError=String(describing:error);observe()} }
        }catch{write(["ok":false,"error":String(describing:error)],"launch-error.json");NSApplication.shared.terminate(nil)}
    }
    func observe() {
        let front=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1;foregroundSeen.insert(front)
        if front==pid {lastError="VM host unexpectedly activated; guest halted for safety";panel.orderOut(nil);if machine?.canStop == true{Task{try? await machine?.stop()}};phase="safety_stopped"}
        write(status(),"host-status.json")
    }
    func status()->[String:Any] {
        var value:[String:Any] = ["id":id,"backend":"apple-virtualization","build":"vmhost-r9-guest-keyboard","controller_disconnects":controllerDisconnects,"instance":instance,"generation":instance,"pid":pid,"started_at":began.timeIntervalSince1970,"phase":phase,
        "cpu_count":2,"memory_bytes":4294967296,"disk_virtual_bytes":68719476736,"audio_devices":0,"audio_isolated":true,"save_restore_supported":canSaveRestore,"network":"NAT, no forwarding or host listener",
        "screen_capture_preflight":CGPreflightScreenCaptureAccess(),"capture_mode":"ScreenCaptureKit currentProcess (no TCC consent)","host_input_posted":false,"host_frontmost_pid_before":frontBefore,"host_frontmost_pids_seen":foregroundSeen.sorted(),
        "host_became_frontmost":foregroundSeen.contains(pid),"host_cursor_before":[cursorBefore.x,cursorBefore.y],"host_cursor_current":[CGEvent(source:nil)?.location.x ?? -1,CGEvent(source:nil)?.location.y ?? -1],"controller_exit_stops_guest":false,"captures_completed":captures,
        "input_mode":"direct guest USB events through owned VZVirtualMachineView",
        "capabilities":["capture":phase == "running","input":phase == "running","keyboard":phase == "running","key_hold":phase == "running","text_paste":phase == "running","pointer":phase == "running","pointer_drag":phase == "running","exec":false,"audio":false,"audio_capture":false,"audio_silent":true,"browser":false,"accessibility":false]]
        if let machine {value["vm_state"]=machine.state.rawValue};if let installer {value["install_fraction"]=installer.progress.fractionCompleted}
        if let lastError {value["last_error"]=lastError};if let panel {value["window_id"]=panel.windowNumber;value["window_offscreen"] = !NSScreen.screens.contains(where:{$0.frame.intersects(panel.frame)});value["window_key"]=panel.isKeyWindow;value["window_main"]=panel.isMainWindow}
        if let lastInputAt {value["last_input_at"]=lastInputAt};return value
    }
    func configure() async throws {
        phase="configuring";let fm=FileManager.default
        let platform=VZMacPlatformConfiguration()
        if !fm.fileExists(atPath:file("HardwareModel.bin").path) {
            guard shouldInstall else {throw failure("not_installed","VM platform does not exist")}
            let restore:VZMacOSRestoreImage=try await withCheckedThrowingContinuation { continuation in VZMacOSRestoreImage.load(from:file("Restore.ipsw")){continuation.resume(with:$0)} }
            guard let requirements=restore.mostFeaturefulSupportedConfiguration,requirements.minimumSupportedCPUCount<=2,requirements.minimumSupportedMemorySize<=4294967296 else {throw failure("minimum_changed","Restore requires larger resources; stop for review")}
            try requirements.hardwareModel.dataRepresentation.write(to:file("HardwareModel.bin"),options:.withoutOverwriting)
            try VZMacMachineIdentifier().dataRepresentation.write(to:file("MachineIdentifier.bin"),options:.withoutOverwriting)
            _=try VZMacAuxiliaryStorage(creatingStorageAt:file("AuxiliaryStorage.bin"),hardwareModel:requirements.hardwareModel,options:[])
            let disk=open(file("Disk.img").path,O_CREAT|O_EXCL|O_RDWR|O_NOFOLLOW,0o600);guard disk>=0 else {throw failure("disk_create_failed","Cannot exclusively create guest disk")};defer{close(disk)}
            guard ftruncate(disk,68719476736)==0 else {throw failure("disk_create_failed","Sparse disk sizing failed")}
        }
        guard let model=VZMacHardwareModel(dataRepresentation:try Data(contentsOf:file("HardwareModel.bin"))),model.isSupported,
            let identifier=VZMacMachineIdentifier(dataRepresentation:try Data(contentsOf:file("MachineIdentifier.bin"))) else{throw failure("invalid_platform","Saved VM platform cannot run here")}
        platform.hardwareModel=model;platform.machineIdentifier=identifier;platform.auxiliaryStorage=VZMacAuxiliaryStorage(contentsOf:file("AuxiliaryStorage.bin"))
        let config=VZVirtualMachineConfiguration();config.platform=platform;config.bootLoader=VZMacOSBootLoader();config.cpuCount=2;config.memorySize=4294967296
        let graphics=VZMacGraphicsDeviceConfiguration();graphics.displays=[VZMacGraphicsDisplayConfiguration(widthInPixels:1024,heightInPixels:768,pixelsPerInch:80)];config.graphicsDevices=[graphics]
        config.keyboards=[VZUSBKeyboardConfiguration()];config.pointingDevices=[VZUSBScreenCoordinatePointingDeviceConfiguration()]
        config.audioDevices=[];config.socketDevices=[];config.serialPorts=[]
        let bridge=file("bridge");try fm.createDirectory(at:bridge,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        var bridgeStat=stat();guard lstat(bridge.path,&bridgeStat)==0,bridgeStat.st_uid==getuid(),(bridgeStat.st_mode & S_IFMT)==S_IFDIR,(bridgeStat.st_mode & 0o077)==0 else{throw failure("unsafe_bridge","Bridge directory must be private, owned and not a symlink")}
        try instance.data(using:.utf8)!.write(to:bridge.appendingPathComponent("owner-instance"),options:.atomic)
        let shared=VZVirtioFileSystemDeviceConfiguration(tag:VZVirtioFileSystemDeviceConfiguration.macOSGuestAutomountTag)
        shared.share=VZSingleDirectoryShare(directory:VZSharedDirectory(url:bridge,readOnly:false));config.directorySharingDevices=[shared]
        let network=VZVirtioNetworkDeviceConfiguration();network.attachment=VZNATNetworkDeviceAttachment()
        if let address=try? String(contentsOf:file("network-mac"),encoding:.utf8),let mac=VZMACAddress(string:address){network.macAddress=mac}else{try network.macAddress.string.data(using:.utf8)!.write(to:file("network-mac"),options:.withoutOverwriting)}
        config.networkDevices=[network]
        let disk=try VZDiskImageStorageDeviceAttachment(url:file("Disk.img"),readOnly:false);config.storageDevices=[VZVirtioBlockDeviceConfiguration(attachment:disk)]
        try config.validate();do{try config.validateSaveRestoreSupport();canSaveRestore=true}catch{canSaveRestore=false};let vm=VZVirtualMachine(configuration:config);vm.delegate=self;machine=vm;view.virtualMachine=vm
        write(["id":id,"backend":"apple-virtualization","cpu_count":2,"memory_bytes":4294967296,"disk_virtual_bytes":68719476736,"audio_devices":0,"created_at":began.timeIntervalSince1970],"config.json")
    }
    func install() async throws {
        guard let machine else{throw failure("not_ready","No machine")};guard !FileManager.default.fileExists(atPath:file("installed.json").path) else {throw failure("already_installed","Refusing to overwrite installed guest")}
        let restore:VZMacOSRestoreImage=try await withCheckedThrowingContinuation { continuation in VZMacOSRestoreImage.load(from:file("Restore.ipsw")){continuation.resume(with:$0)} }
        try Task.checkCancellation();guard !terminating else{throw failure("terminating","VM owner is stopping")}
        let version=restore.operatingSystemVersion
        let description="\(version.majorVersion).\(version.minorVersion).\(version.patchVersion) \(restore.buildVersion)"
        phase="installing";let installer=VZMacOSInstaller(virtualMachine:machine,restoringFromImageAt:file("Restore.ipsw"));self.installer=installer;observe()
        try await installer.install();write(["installed_at":Date().timeIntervalSince1970,"restore":description],"installed.json");phase="installed";observe()
        if machine.state == .stopped {try await boot()} else {phase="running"}
    }
    func boot() async throws {
        guard let machine else{throw failure("not_ready","No machine")};phase="booting"
        if FileManager.default.fileExists(atPath:file("SavedState.vzstate").path) {
            guard canSaveRestore else{throw failure("restore_unsupported","Saved guest state exists but this configuration cannot restore it")}
            try await machine.restoreMachineStateFrom(url:file("SavedState.vzstate"))
            // Never leave a replayable snapshot after the guest starts mutating its disk.
            try FileManager.default.removeItem(at:file("SavedState.vzstate"));try await machine.resume()
        }else{try await machine.start()}
        phase="running";observe()
    }
    func guestDidStop(_ virtualMachine:VZVirtualMachine) {phase=terminating ? "terminating":"stopped";observe()}
    func virtualMachine(_ virtualMachine:VZVirtualMachine,didStopWithError error:Error) {lastError=String(describing:error);phase="failed";observe()}
    func listen() throws {
        let path=file("control.sock").path;guard path.utf8.count<104 else {throw failure("socket_path_too_long","State root is too long for a Unix socket")}
        unlink(path);listener=socket(AF_UNIX,SOCK_STREAM,0);guard listener>=0 else{throw failure("socket_failed","Cannot create private control socket")}
        var address=sockaddr_un();address.sun_family=sa_family_t(AF_UNIX);address.sun_len=UInt8(MemoryLayout<sockaddr_un>.size)
        _ = withUnsafeMutablePointer(to:&address.sun_path){ptr in ptr.withMemoryRebound(to:CChar.self,capacity:104){dest in path.withCString{strcpy(dest,$0)}}}
        let bound=withUnsafePointer(to:&address){$0.withMemoryRebound(to:sockaddr.self,capacity:1){Darwin.bind(listener,$0,socklen_t(MemoryLayout<sockaddr_un>.size))}}
        guard bound==0,Darwin.listen(listener,8)==0 else{throw failure("socket_failed","Cannot bind owned Unix socket")};chmod(path,0o600)
        let socketFD=listener;let owner=getuid()
        DispatchQueue.global(qos:.utility).async { [weak self] in
            while true {
                let client=accept(socketFD,nil,nil);if client<0{if errno==EINTR{continue};return}
                var noSigPipe:Int32=1;guard setsockopt(client,SOL_SOCKET,SO_NOSIGPIPE,&noSigPipe,socklen_t(MemoryLayout<Int32>.size))==0 else{close(client);continue}
                var uid:uid_t=0;var gid:gid_t=0
                guard getpeereid(client,&uid,&gid)==0,uid==owner else{close(client);continue}
                var timeout=timeval(tv_sec:10,tv_usec:0);setsockopt(client,SOL_SOCKET,SO_RCVTIMEO,&timeout,socklen_t(MemoryLayout<timeval>.size));setsockopt(client,SOL_SOCKET,SO_SNDTIMEO,&timeout,socklen_t(MemoryLayout<timeval>.size))
                var data=Data();var chunk=[UInt8](repeating:0,count:8192)
                while data.count<1048576 {let count=Darwin.read(client,&chunk,chunk.count);if count<=0{break};data.append(contentsOf:chunk.prefix(count))}
                guard let req=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] else{close(client);continue}
                Task{@MainActor in
                    guard let self else{close(client);return};let response=await self.handle(req);let bytes=encoded(response)+Data([10]);bytes.withUnsafeBytes{raw in
                        var sent=0
                        while sent<raw.count {let count=Darwin.write(client,raw.baseAddress!.advanced(by:sent),raw.count-sent);if count<0 && errno==EINTR{continue};if count<=0{self.controllerDisconnects+=1;break};sent+=count}
                    };close(client)
                }
            }
        }
    }
    func handle(_ request:[String:Any]) async->[String:Any] {
        do {
            guard let op=request["op"] as? String else{throw failure("invalid_request","op is required")}
            if op != "status",request["instance"] as? String != instance {throw failure("instance_changed","Expected VM owner instance is required and must match")}
            if let expected=request["instance"] as? String,expected != instance {throw failure("instance_changed","VM host instance changed")}
            if terminating && op != "status"{throw failure("terminating","VM owner is shutting down; wait for socket and lock release")}
            if bridgeBusy && ["start","stop","bridge","input"].contains(op){throw failure("guest_operation_in_progress","Wait for the accepted guest operation before lifecycle/input changes")}
            if inputBusy && ["start","stop","bridge","input"].contains(op){throw failure("guest_operation_in_progress","Wait for the accepted input and release before lifecycle/input changes")}
            var result:[String:Any]=[:]
            switch op {
            case "status":result=status()
            case "start":guard FileManager.default.fileExists(atPath:file("installed.json").path),machine?.state == .stopped else{throw failure("not_stopped","Installed guest must be stopped before boot")};try await boot();result=status()
            case "capture":result=try await capture(request)
            case "input":inputBusy=true;defer{inputBusy=false};result=try await input(request)
            case "bridge":
                guard phase=="running",machine?.state == .running else{throw failure("not_running","Guest must be running")}
                bridgeBusy=true;defer{bridgeBusy=false};result=try await guestOperation(request)
            case "stop":
                guard phase != "installing" else{throw failure("install_in_progress","Stopping during Apple installation is unsafe; wait for completion")}
                guard phase != "configuring" && phase != "starting" && phase != "booting" else{throw failure("startup_in_progress","Wait for startup before stopping this owner")}
                terminating=true;startupTask?.cancel()
                if let machine,machine.state == .running {
                    guard canSaveRestore else{terminating=false;throw failure("save_unsupported","Configuration cannot save a logged-in guest; refusing implicit data-losing stop")}
                    guard !FileManager.default.fileExists(atPath:file("SavedState.pending").path),!FileManager.default.fileExists(atPath:file("SavedState.vzstate").path) else{terminating=false;throw failure("snapshot_exists","Refusing to overwrite a retained snapshot")}
                    phase="saving"
                    do{try await machine.pause();try await machine.saveMachineStateTo(url:file("SavedState.pending"));chmod(file("SavedState.pending").path,0o600);try FileManager.default.moveItem(at:file("SavedState.pending"),to:file("SavedState.vzstate"))}
                    catch{
                        if machine.state == .paused{try? await machine.resume()}
                        var partial=stat();if lstat(file("SavedState.pending").path,&partial)==0,partial.st_uid==getuid(),(partial.st_mode & S_IFMT)==S_IFREG{try? FileManager.default.removeItem(at:file("SavedState.pending"))}
                        terminating=false;phase=machine.state == .running ? "running":"pause_failed";throw error
                    }
                }
                if let machine,machine.canStop {try await machine.stop()};phase="terminating";observe();result=["owned_vm_stopped":true,"disk_retained":true,"guest_state_saved":FileManager.default.fileExists(atPath:file("SavedState.vzstate").path)]
                DispatchQueue.main.asyncAfter(deadline:.now()+0.3){NSApplication.shared.terminate(nil)}
            case "exec":throw failure("guest_transport_not_ready","Guest command transport is not installed; no host process was launched")
            default:throw failure("unknown_operation","Unsupported VM operation")
            }
            return ["ok":true,"platform":"macos","session":status(),"result":result]
        }catch let error as VMFailure{return ["ok":false,"platform":"macos","session":status(),"error":["code":error.code,"message":error.message]]}
        catch{return ["ok":false,"platform":"macos","session":status(),"error":["code":"vm_operation_failed","message":String(describing:error)]]}
    }
    func guestExchange(_ payload:[String:Any]) async throws->[String:Any] {
        let bridge=file("bridge"),nonce=UUID().uuidString
        let identity=try String(contentsOf:bridge.appendingPathComponent("bridge-id"),encoding:.utf8).trimmingCharacters(in:.whitespacesAndNewlines)
        guard UUID(uuidString:identity) != nil else{throw failure("invalid_bridge","Guest bridge identity is invalid")}
        var body=payload;body["bridge_id"]=identity
        let pending=bridge.appendingPathComponent(nonce+".pending"),request=bridge.appendingPathComponent(nonce+".request.json"),response=bridge.appendingPathComponent(nonce+".response.json")
        defer{try? FileManager.default.removeItem(at:pending);try? FileManager.default.removeItem(at:request);try? FileManager.default.removeItem(at:response)}
        try encoded(body).write(to:pending,options:.withoutOverwriting);chmod(pending.path,0o600);try FileManager.default.moveItem(at:pending,to:request)
        for _ in 0..<70 {
            if FileManager.default.fileExists(atPath:response.path) {
                let fd=open(response.path,O_RDONLY|O_NOFOLLOW);guard fd>=0 else{throw failure("invalid_bridge_response","Cannot safely open guest response")}
                let handle=FileHandle(fileDescriptor:fd,closeOnDealloc:true);var info=stat()
                guard fstat(fd,&info)==0,(info.st_mode & S_IFMT)==S_IFREG,info.st_size<=1048576 else{throw failure("invalid_bridge_response","Guest response must be a bounded regular file")}
                let data=try handle.readToEnd() ?? Data();try handle.close()
                guard let result=try JSONSerialization.jsonObject(with:data) as? [String:Any],result["request_id"] as? String==nonce else{throw failure("invalid_bridge_response","Guest response nonce differs")}
                return result
            }
            try await Task.sleep(nanoseconds:100_000_000)
        }
        throw failure("guest_bridge_timeout","Guest bridge did not acknowledge the nonce; operation is not automatically retried")
    }
    func guestOperation(_ request:[String:Any]) async throws->[String:Any] {
        guard let op=request["bridge_op"] as? String,["exec","clipboard","type_text"].contains(op) else{throw failure("invalid_bridge_operation","Only guest exec, clipboard or type_text is supported")}
        if op=="type_text"{guard let text=request["text"] as? String,text.utf16.count<=4096 else{throw failure("text_too_long","Maximum 4096 UTF16 units")}}
        let status=try await guestExchange(["op":"status"])
        guard status["ok"] as? Bool==true,let state=status["result"] as? [String:Any],state["virtualized"] as? Bool==true,state["graphical_session"] as? Bool==true,state["vm_owner_instance"] as? String==instance,let guest=status["guest_instance"] as? String else{throw failure("guest_generation_changed","Guest generation/owner does not match this VM")}
        var payload:[String:Any]=["op":op=="type_text" ? "clipboard":op,"guest_instance":guest,"vm_owner_instance":instance]
        if op=="exec"{payload["argv"]=request["argv"];payload["cwd"]=request["cwd"]}else{payload["text"]=request["text"]}
        let response=try await guestExchange(payload)
        guard response["guest_instance"] as? String==guest else{throw failure("guest_generation_changed","Guest bridge changed before mutation")}
        guard response["ok"] as? Bool==true else{throw failure("guest_bridge_rejected","Guest rejected the generation-bound operation")}
        var result=response["result"] as? [String:Any] ?? [:];result["guest_instance"]=guest
        if op=="type_text"{
            // Keep bridgeBusy through paste/consumption; no input or lifecycle
            // interleaving between staging the guest clipboard and its chord.
            result.merge(try await input(["key":"cmd+v"])){_,new in new}
            try? await Task.sleep(nanoseconds:200_000_000);result["text_entry"]="guest-clipboard";result["verified"]=false
        }
        return result
    }
    func capture(_ request:[String:Any]) async throws->[String:Any] {
        guard let output=request["output"] as? String,output.hasPrefix("/") else{throw failure("invalid_output","An absolute output path is required")}
        guard panel != nil,!panel.isKeyWindow,!panel.isMainWindow,!NSScreen.screens.contains(where:{$0.frame.intersects(panel.frame)}) else{throw failure("window_isolation_lost","VM window is not confined offscreen")}
        let content=try await SCShareableContent.currentProcess
        guard let target=content.windows.first(where:{$0.windowID==CGWindowID(panel.windowNumber)}) else{throw failure("owned_window_missing","Exact owned VM window is unavailable")}
        let config=SCStreamConfiguration();config.width=1024;config.height=768;config.showsCursor=false;config.capturesAudio=false;config.ignoreShadowsSingleWindow=true;config.minimumFrameInterval=CMTime(value:1,timescale:15)
        let collector=FrameCollector();let stream=SCStream(filter:SCContentFilter(desktopIndependentWindow:target),configuration:config,delegate:collector)
        try stream.addStreamOutput(collector,type:.screen,sampleHandlerQueue:DispatchQueue(label:"owned.vm.capture"));try await stream.startCapture()
        var image:CGImage?;var reason:String?
        for _ in 0..<70 {try await Task.sleep(nanoseconds:100_000_000);(image,reason)=collector.read();if image != nil || reason != nil{break}}
        try? await stream.stopCapture();guard let image else{throw failure("capture_timeout",reason ?? "No complete VM frame in 7 seconds")}
        let data=NSMutableData();guard let destination=CGImageDestinationCreateWithData(data,UTType.png.identifier as CFString,1,nil) else{throw failure("png_failed","PNG destination failed")};CGImageDestinationAddImage(destination,image,nil);guard CGImageDestinationFinalize(destination) else{throw failure("png_failed","PNG encoding failed")}
        let fd=open(output,O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW,0o600);guard fd>=0 else{throw failure("output_exists_or_invalid","Output must be a new file in an existing directory")};defer{close(fd)}
        let bytes=data as Data;let written=bytes.withUnsafeBytes{Darwin.write(fd,$0.baseAddress,$0.count)};guard written==bytes.count else{throw failure("write_failed","Incomplete PNG write")}
        captures+=1;return ["path":output,"width":image.width,"height":image.height,"captured_at":Date().timeIntervalSince1970,"window_id":target.windowID,"only_owned_guest_view":true]
    }
    func input(_ request:[String:Any]) async throws->[String:Any] {
        guard phase=="running",machine?.state == .running else{throw failure("guest_not_running","Guest must be running")}
        guard panel != nil,!panel.isKeyWindow,!panel.isMainWindow,!NSScreen.screens.contains(where:{$0.frame.intersects(panel.frame)}) else{throw failure("window_isolation_lost","VM window is not confined offscreen")}
        var sent=0
        let began=ProcessInfo.processInfo.systemUptime
        var hold=0
        if let value=request["hold_ms"] {
            guard let number=value as? NSNumber,CFGetTypeID(number) != CFBooleanGetTypeID(),
                number.doubleValue.isFinite,number.doubleValue.rounded()==number.doubleValue,
                (0...5000).contains(number.doubleValue) else{throw failure("invalid_input","hold_ms must be an integer from 0–5000")}
            hold=number.intValue
        }
        guard (0...5000).contains(hold),hold==0 || request["key"] is String else{throw failure("invalid_input","A bounded hold requires a key")}
        if let text=request["text"] as? String {
            guard text.utf16.count<=128 else{throw failure("text_too_long","US-key bootstrap input is limited to 128 UTF16 units; use a live guest bridge for longer text")}
            guard text.allSatisfy({keyCode(String($0)) != nil}) else{throw failure("unsupported_text","Text contains unsupported US-keyboard characters; no events sent")}
            for char in text {let s=String(char);guard let code=keyCode(s) else{throw failure("unsupported_text","Only US keyboard characters supported by this input path")};let shift=s.rangeOfCharacter(from:CharacterSet.uppercaseLetters) != nil || "~!@#$%^&*()_+{}|:\"<>?".contains(s);try await sendKey(code:code,characters:s,modifiers:shift ? .shift:[]);sent+=1}
        } else if let key=request["key"] as? String {
            let pieces=key.lowercased().split(separator:"+",omittingEmptySubsequences:false).map(String.init);var flags:NSEvent.ModifierFlags=[]
            for modifier in pieces.dropLast(){switch modifier{case "cmd","command","meta":flags.insert(.command);case "ctrl","control":flags.insert(.control);case "alt","option":flags.insert(.option);case "shift":flags.insert(.shift);default:throw failure("invalid_key","Unknown modifier")}}
            let last=pieces.last ?? "";let named:[String:UInt16] = ["enter":36,"return":36,"tab":48,"space":49,"escape":53,"esc":53,"backspace":51,"delete":117,"up":126,"down":125,"left":123,"right":124,"home":115,"end":119,"pageup":116,"pagedown":121,"cmd":55,"command":55,"meta":55,"shift":56,"alt":58,"option":58,"ctrl":59,"control":59]
            guard let code=named[last] ?? keyCode(last) else{throw failure("invalid_key","Unsupported key")};try await sendKey(code:code,characters:last.count==1 ? last:"",modifiers:flags,holdMS:hold);sent=1
        } else if request["drag"] != nil {
            sent=try guestDrag(request,windowNumber:panel.windowNumber){e in
                switch e.type {
                case .leftMouseDown:view.mouseDown(with:e)
                case .leftMouseDragged:view.mouseDragged(with:e)
                case .leftMouseUp:view.mouseUp(with:e)
                case .rightMouseDown:view.rightMouseDown(with:e)
                case .rightMouseDragged:view.rightMouseDragged(with:e)
                case .rightMouseUp:view.rightMouseUp(with:e)
                case .otherMouseDown:view.otherMouseDown(with:e)
                case .otherMouseDragged:view.otherMouseDragged(with:e)
                case .otherMouseUp:view.otherMouseUp(with:e)
                default:break
                }
            }
        } else if let xy=(request["click"] ?? request["move"]) as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}),xy[0]>=0,xy[0]<1024,xy[1]>=0,xy[1]<768 {
            let location=NSPoint(x:xy[0],y:768-xy[1]);let click=request["click"] != nil;let button=request["button"] as? Int ?? 1
            if click {let down:NSEvent.EventType=button==3 ? .rightMouseDown:button==2 ? .otherMouseDown:.leftMouseDown;let up:NSEvent.EventType=button==3 ? .rightMouseUp:button==2 ? .otherMouseUp:.leftMouseUp
                for type in [down,up] {guard let e=NSEvent.mouseEvent(with:type,location:location,modifierFlags:[],timestamp:ProcessInfo.processInfo.systemUptime,windowNumber:panel.windowNumber,context:nil,eventNumber:0,clickCount:1,pressure:type==down ? 1:0) else{throw failure("event_failed","Could not build mouse event")};if button==3 {type==down ? view.rightMouseDown(with:e):view.rightMouseUp(with:e)}else if button==2{type==down ? view.otherMouseDown(with:e):view.otherMouseUp(with:e)}else{type==down ? view.mouseDown(with:e):view.mouseUp(with:e)}}
            }else if let e=NSEvent.mouseEvent(with:.mouseMoved,location:location,modifierFlags:[],timestamp:ProcessInfo.processInfo.systemUptime,windowNumber:panel.windowNumber,context:nil,eventNumber:0,clickCount:0,pressure:0){view.mouseMoved(with:e)};sent=1
        }else{throw failure("invalid_input","Provide text, key, or bounded click/move/drag coordinates")}
        lastInputAt=Date().timeIntervalSince1970;var result:[String:Any] = ["events_submitted":sent,"destination":"owned VZVirtualMachineView","host_global_events":false,"guest_effect_requires_capture_verification":true]
        if request["drag"] != nil{result["released"]=true}
        if hold>0{result["heldMs"]=hold;result["elapsedMs"]=Int(ceil((ProcessInfo.processInfo.systemUptime-began)*1000));result["released"]=true}
        return result
    }
    func sendKey(code:UInt16,characters:String,modifiers:NSEvent.ModifierFlags,holdMS:Int=0) async throws {
        try await guestKey(code:code,characters:characters,modifiers:modifiers,holdMS:holdMS,windowNumber:panel.windowNumber){event in
            switch event.type{case .flagsChanged:view.flagsChanged(with:event);case .keyDown:view.keyDown(with:event);case .keyUp:view.keyUp(with:event);default:break}
        }
    }
    func keyCode(_ character:String)->UInt16? {
        let keys:[String:UInt16] = ["a":0,"s":1,"d":2,"f":3,"h":4,"g":5,"z":6,"x":7,"c":8,"v":9,"b":11,"q":12,"w":13,"e":14,"r":15,"y":16,"t":17,"1":18,"2":19,"3":20,"4":21,"6":22,"5":23,"=":24,"9":25,"7":26,"-":27,"8":28,"0":29,
        "]":30,"o":31,"u":32,"[":33,"i":34,"p":35,"\n":36,"l":37,"j":38,"'":39,"k":40,";":41,"\\":42,",":43,"/":44,"n":45,"m":46,".":47,"\t":48," ":49,"`":50]
        let shifted=Array("~!@#$%^&*()_+{}|:\"<>?");let base=Array("`1234567890-=[]\\;',./")
        if let i=shifted.firstIndex(of:character.first ?? "\0"),character.count==1{return keys[String(base[i])]};return keys[character.lowercased()]
    }
    func applicationWillTerminate(_ notification:Notification){timer?.invalidate();panel?.orderOut(nil);if listener>=0{close(listener);unlink(file("control.sock").path)};if lockFD>=0{close(lockFD)}}
}
@main struct Main {
    @MainActor static func main(){let args=CommandLine.arguments;guard let state=args.firstIndex(of:"--state"),state+1<args.count,let name=args.firstIndex(of:"--id"),name+1<args.count else{exit(2)}
        signal(SIGPIPE,SIG_IGN)
        let app=NSApplication.shared;let delegate=VMHost(root:URL(fileURLWithPath:args[state+1]),id:args[name+1],install:args.contains("--install"));app.delegate=delegate;withExtendedLifetime(delegate){app.run()}}
}

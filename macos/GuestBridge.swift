import Foundation
import AppKit
import Darwin
import CoreAudio
import Metal
import ApplicationServices

struct GuestTargetError: Error, CustomStringConvertible {
 let description:String
 init(_ message:String){description=message}
}

// References are confined to this virtualized bridge instance. Never resolve a
// mutation by title, app name, window index, or an unobserved/recycled PID.
@MainActor final class GuestTargets {
 struct ProcessTarget {let pid:pid_t;let birth:String;let created:Date}
 struct WindowTarget {let element:AXUIElement;let process:ProcessTarget;let created:Date}
 var processes=[String:ProcessTarget]();var windows=[Int:WindowTarget]()
 var ownerGeneration=""
 func bind(_ owner:String) {
  if owner != ownerGeneration {processes.removeAll();windows.removeAll();ownerGeneration=owner}
 }
 func identity(_ pid:pid_t)throws->ProcessTarget {
  var info=proc_bsdinfo();let size=Int32(MemoryLayout<proc_bsdinfo>.size)
  guard pid>1,proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&info,size)==size else{throw GuestTargetError("Process no longer exists")}
  guard info.pbi_uid==getuid(),pid != getpid() else{throw GuestTargetError("Target must be another process owned by the guest user")}
  return ProcessTarget(pid:pid,birth:"\(info.pbi_start_tvsec):\(info.pbi_start_tvusec)",created:Date())
 }
 func validate(_ target:ProcessTarget)throws {
  guard Date().timeIntervalSince(target.created)<300,try identity(target.pid).birth==target.birth else{throw GuestTargetError("Target expired or PID identity changed; list again")}
 }
 func arguments(_ pid:pid_t)->[String] {
  var mib:[Int32]=[CTL_KERN,KERN_PROCARGS2,pid];var size=65536;var bytes=[UInt8](repeating:0,count:size)
  guard sysctl(&mib,3,&bytes,&size,nil,0)==0,size>4 else{return []}
  let count=bytes.withUnsafeBytes{$0.loadUnaligned(as:Int32.self)}
  guard count>0,count<=4096 else{return []}
  var i=4;while i<size && bytes[i] != 0{i+=1};while i<size && bytes[i]==0{i+=1}
  var result=[String]()
  for _ in 0..<count {guard i<size else{break};let start=i;while i<size && bytes[i] != 0{i+=1};result.append(String(decoding:bytes[start..<i],as:UTF8.self));i+=1}
  return result // No environment variables, and no shell interpolation.
 }
 func listProcesses()->[[String:Any]] {
  processes=processes.filter{Date().timeIntervalSince($0.value.created)<300}
  let count=proc_listallpids(nil,0);guard count>0,count<100000 else{return []}
  var pids=[pid_t](repeating:0,count:Int(count)+128)
  let found=proc_listallpids(&pids,Int32(pids.count*MemoryLayout<pid_t>.size))
  var rows=[[String:Any]]()
  for pid in pids.prefix(max(0,min(Int(found),pids.count))).sorted() {
   guard let target=try? identity(pid) else{continue}
   var path=[CChar](repeating:0,count:4096);let n=proc_pidpath(pid,&path,UInt32(path.count))
   let executable=n>0 ? String(cString:path):"";let argv=arguments(pid)
   guard (try? identity(pid).birth)==target.birth else{continue}
   let token=UUID().uuidString;processes[token]=target
   rows.append(["pid":pid,"name":URL(fileURLWithPath:executable).lastPathComponent,"executable":executable,"argv":argv,"cmd":argv.joined(separator:" "),"target":token,"birth":target.birth])
  }
  return rows
 }
 func attribute(_ element:AXUIElement,_ name:String)->CFTypeRef? {
  var value:CFTypeRef?;guard AXUIElementCopyAttributeValue(element,name as CFString,&value) == .success else{return nil};return value
 }
 func listWindows()throws->[[String:Any]] {
  guard AXIsProcessTrusted() else{throw GuestTargetError("Guest Accessibility permission required for GuestBridge; no prompt or host fallback")}
  windows=windows.filter{Date().timeIntervalSince($0.value.created)<300}
  var rows=[[String:Any]]()
  for app in NSWorkspace.shared.runningApplications {
   guard let target=try? identity(app.processIdentifier) else{continue}
   let application=AXUIElementCreateApplication(app.processIdentifier);AXUIElementSetMessagingTimeout(application,0.3)
   guard let elements=attribute(application,kAXWindowsAttribute) as? [AXUIElement] else{continue}
   for element in elements {
    AXUIElementSetMessagingTimeout(element,0.3)
    let token=Int.random(in:1...Int(Int32.max))
    guard windows[token]==nil else{continue}
    windows[token]=WindowTarget(element:element,process:target,created:Date())
    rows.append(["id":token,"pid":target.pid,"app":app.localizedName ?? "","title":attribute(element,kAXTitleAttribute) as? String ?? "","minimized":attribute(element,kAXMinimizedAttribute) as? Bool ?? false])
   }
  }
  return rows
 }
 func perform(_ request:[String:Any])throws->[String:Any] {
  let op=request["op"] as? String;let action=request["action"] as? String ?? "list"
  if op=="processes",action=="list" {return ["processes":listProcesses(),"scope":"guest-user","target_ttl_seconds":300]}
  if op=="windows",action=="list" {return ["windows":try listWindows(),"target_ttl_seconds":300]}
  if op=="windows" {
   guard AXIsProcessTrusted(),let id=request["window_id"] as? Int,let target=windows[id],Date().timeIntervalSince(target.created)<300 else{throw GuestTargetError("Unknown/expired window or guest Accessibility permission missing; list again")}
   try validate(target.process)
   var pid:pid_t=0;guard AXUIElementGetPid(target.element,&pid) == .success,pid==target.process.pid,attribute(target.element,kAXRoleAttribute) as? String==kAXWindowRole else{throw GuestTargetError("Window identity is no longer valid")}
   let app=AXUIElementCreateApplication(pid)
   guard let current=attribute(app,kAXWindowsAttribute) as? [AXUIElement],current.contains(where:{CFEqual($0,target.element)}) else{throw GuestTargetError("Exact window is no longer present")}
   if action=="close" {
    guard let value=attribute(target.element,kAXCloseButtonAttribute),CFGetTypeID(value)==AXUIElementGetTypeID() else{throw GuestTargetError("Window has no close button")}
    let button=unsafeBitCast(value,to:AXUIElement.self)
    guard AXUIElementPerformAction(button,kAXPressAction as CFString) == .success else{throw GuestTargetError("Exact window close was refused")}
   } else if action=="focus" {
    guard AXUIElementSetAttributeValue(target.element,kAXMinimizedAttribute as CFString,kCFBooleanFalse) == .success,AXUIElementPerformAction(target.element,kAXRaiseAction as CFString) == .success,let running=NSRunningApplication(processIdentifier:pid),running.activate(options:[]) else{throw GuestTargetError("Exact window focus was not confirmed")}
   } else{throw GuestTargetError("Only list, focus and close are supported")}
   return ["action":action,"window":id,"pid":pid,"requested":true,"completion_verified":false]
  }
  guard op=="processes",let token=request["target"] as? String,let target=processes[token],let pid=request["pid"] as? Int,pid==Int(target.pid) else{throw GuestTargetError("Exact PID and target token from a recent process list required")}
  try validate(target)
  if action=="quit" {
   guard let app=NSRunningApplication(processIdentifier:target.pid),app.terminate() else{throw GuestTargetError("Graceful app quit refused; no force quit was sent")}
  } else if action=="terminate" {
   guard kill(target.pid,SIGTERM)==0 else{throw GuestTargetError("SIGTERM refused")}
  } else{throw GuestTargetError("Only list, quit and terminate are supported")}
  processes.removeValue(forKey:token)
  return ["action":action,"pid":pid,"requested":true,"completion_verified":false]
 }
}

func json(_ value:[String:Any])->Data{(try? JSONSerialization.data(withJSONObject:value,options:.sortedKeys)) ?? Data("{}".utf8)}
@MainActor @main struct GuestBridge {
 static func main() async {
  // Never run host workloads, even if someone launches the transfer binary locally.
  var virtualized:Int32=0;var length=MemoryLayout<Int32>.size
  guard sysctlbyname("kern.hv_vmm_present",&virtualized,&length,nil,0)==0,virtualized==1,getuid()>=500 else{exit(2)}
  guard let session=CGSessionCopyCurrentDictionary() as? [String:Any],session[kCGSessionOnConsoleKey as String] as? Bool==true else{exit(3)}
  let root=URL(fileURLWithPath:"/Volumes/My Shared Files")
  guard let identity=try? String(contentsOf:root.appendingPathComponent("bridge-id"),encoding:.utf8),UUID(uuidString:identity.trimmingCharacters(in:.whitespacesAndNewlines)) != nil else{exit(4)}
  let ownerLock=open((NSHomeDirectory()+"/Library/Application Support/Deskhelper/bridge.lock"),O_CREAT|O_RDWR|O_NOFOLLOW,0o600)
  guard ownerLock>=0,flock(ownerLock,LOCK_EX|LOCK_NB)==0 else{exit(5)}
  NSApplication.shared.setActivationPolicy(.prohibited)
  var audioAddress=AudioObjectPropertyAddress(mSelector:kAudioHardwarePropertyDevices,mScope:kAudioObjectPropertyScopeGlobal,mElement:kAudioObjectPropertyElementMain)
  var audioSize:UInt32=0;let audioStatus=AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject),&audioAddress,0,nil,&audioSize)
  var outputAddress=AudioObjectPropertyAddress(mSelector:kAudioHardwarePropertyDefaultOutputDevice,mScope:kAudioObjectPropertyScopeGlobal,mElement:kAudioObjectPropertyElementMain)
  var outputDevice:AudioDeviceID=0;var outputSize=UInt32(MemoryLayout<AudioDeviceID>.size)
  let outputStatus=AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject),&outputAddress,0,nil,&outputSize,&outputDevice)
  let metalDevice=MTLCreateSystemDefaultDevice()?.name ?? "unavailable"
  let ownInstance=UUID().uuidString;var owned=[String:Process]();let fm=FileManager.default;let targets=GuestTargets()
  while true {
   let vmOwner=(try? String(contentsOf:root.appendingPathComponent("owner-instance"),encoding:.utf8)) ?? ""
   targets.bind(vmOwner)
   let heartbeat:[String:Any] = ["instance":ownInstance,"vm_owner_instance":vmOwner,"bridge_id":identity.trimmingCharacters(in:.whitespacesAndNewlines),"pid":getpid(),"uid":getuid(),"virtualized":true,"graphical_session":true,"audio_device_query_status":audioStatus,"audio_device_count":audioSize/UInt32(MemoryLayout<AudioDeviceID>.size),"default_output_query_status":outputStatus,"default_output_device":outputDevice,"metal_device":metalDevice,"metal_execution_tested":false,"heartbeat_at":Date().timeIntervalSince1970,"os_version":ProcessInfo.processInfo.operatingSystemVersionString,"frontmost_bundle":NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "","owned_process_count":owned.values.filter{$0.isRunning}.count]
   var liveHeartbeat=heartbeat;liveHeartbeat["guest_targets"]=true;liveHeartbeat["window_control"]=AXIsProcessTrusted()
   try? json(liveHeartbeat).write(to:root.appendingPathComponent("guest-status.json"),options:.atomic)
   if let files=try? fm.contentsOfDirectory(at:root,includingPropertiesForKeys:nil){
    for file in files where file.lastPathComponent.hasSuffix(".request.json") {
     let name=String(file.lastPathComponent.dropLast(".request.json".count));guard UUID(uuidString:name) != nil else{continue}
     guard let data=try? Data(contentsOf:file),data.count<=1048576,let request=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] else{continue}
     do{try fm.removeItem(at:file)}catch{continue}
     var response:[String:Any] = ["ok":false,"guest_instance":ownInstance,"request_id":name]
     do {
      guard request["bridge_id"] as? String==identity.trimmingCharacters(in:.whitespacesAndNewlines) else{throw NSError(domain:"Bridge",code:1,userInfo:[NSLocalizedDescriptionKey:"Bridge identity mismatch"])}
      if request["op"] as? String != "status",request["vm_owner_instance"] as? String != vmOwner {throw NSError(domain:"Bridge",code:7,userInfo:[NSLocalizedDescriptionKey:"VM owner generation changed; refusing replacement guest mutation"])}
      if request["op"] as? String != "status",request["guest_instance"] as? String != ownInstance {throw NSError(domain:"Bridge",code:6,userInfo:[NSLocalizedDescriptionKey:"Guest bridge instance changed; old requests are never replayed"])}
      switch request["op"] as? String {
      case "windows","processes":
       response["result"]=try targets.perform(request);response["ok"]=true
      case "exec":
       guard let argv=request["argv"] as? [String],let program=argv.first,program.hasPrefix("/"),argv.count<=4096 else{throw NSError(domain:"Bridge",code:2,userInfo:[NSLocalizedDescriptionKey:"Absolute executable and argv required"])}
       let process=Process();process.executableURL=URL(fileURLWithPath:program);process.arguments=Array(argv.dropFirst());if let cwd=request["cwd"] as? String{process.currentDirectoryURL=URL(fileURLWithPath:cwd)}
       process.standardInput=FileHandle.nullDevice;process.standardOutput=FileHandle.nullDevice;process.standardError=FileHandle.nullDevice;try process.run();owned[name]=process
       response["ok"]=true;response["result"]=["pid":process.processIdentifier,"guest_instance":ownInstance,"launched_in_guest":true,"argv_preserved":true]
      case "clipboard":
       guard let text=request["text"] as? String,text.utf8.count<=262144 else{throw NSError(domain:"Bridge",code:3)}
       NSPasteboard.general.clearContents();guard NSPasteboard.general.setString(text,forType:.string) else{throw NSError(domain:"Bridge",code:4)}
       response["ok"]=true;response["result"]=["guest_clipboard_set":true,"utf8_bytes":text.utf8.count]
      case "status":response["ok"]=true;response["result"]=liveHeartbeat
      default:throw NSError(domain:"Bridge",code:5,userInfo:[NSLocalizedDescriptionKey:"Unsupported bridge operation"])
      }
     } catch{response["error"]=["code":"guest_bridge_error","message":String(describing:error)]}
     if json(response).count>900000 {response=["ok":false,"guest_instance":ownInstance,"request_id":name,"error":["code":"response_too_large","message":"Guest response exceeds bounded transport"]]}
     try? json(response).write(to:root.appendingPathComponent(name+".response.json"),options:.atomic)
    }
   }
   try? await Task.sleep(nanoseconds:100_000_000)
  }
 }
}

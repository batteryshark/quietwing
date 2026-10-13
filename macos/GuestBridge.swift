import Foundation
import AppKit
import Darwin
import CoreAudio
import Metal

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
  let ownInstance=UUID().uuidString;var owned=[String:Process]();let fm=FileManager.default
  while true {
   let vmOwner=(try? String(contentsOf:root.appendingPathComponent("owner-instance"),encoding:.utf8)) ?? ""
   let heartbeat:[String:Any] = ["instance":ownInstance,"vm_owner_instance":vmOwner,"bridge_id":identity.trimmingCharacters(in:.whitespacesAndNewlines),"pid":getpid(),"uid":getuid(),"virtualized":true,"graphical_session":true,"audio_device_query_status":audioStatus,"audio_device_count":audioSize/UInt32(MemoryLayout<AudioDeviceID>.size),"default_output_query_status":outputStatus,"default_output_device":outputDevice,"metal_device":metalDevice,"metal_execution_tested":false,"heartbeat_at":Date().timeIntervalSince1970,"os_version":ProcessInfo.processInfo.operatingSystemVersionString,"frontmost_bundle":NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "","owned_process_count":owned.values.filter{$0.isRunning}.count]
   try? json(heartbeat).write(to:root.appendingPathComponent("guest-status.json"),options:.atomic)
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
      case "exec":
       guard let argv=request["argv"] as? [String],let program=argv.first,program.hasPrefix("/"),argv.count<=4096 else{throw NSError(domain:"Bridge",code:2,userInfo:[NSLocalizedDescriptionKey:"Absolute executable and argv required"])}
       let process=Process();process.executableURL=URL(fileURLWithPath:program);process.arguments=Array(argv.dropFirst());if let cwd=request["cwd"] as? String{process.currentDirectoryURL=URL(fileURLWithPath:cwd)}
       process.standardInput=FileHandle.nullDevice;process.standardOutput=FileHandle.nullDevice;process.standardError=FileHandle.nullDevice;try process.run();owned[name]=process
       response["ok"]=true;response["result"]=["pid":process.processIdentifier,"guest_instance":ownInstance,"launched_in_guest":true,"argv_preserved":true]
      case "clipboard":
       guard let text=request["text"] as? String,text.utf8.count<=262144 else{throw NSError(domain:"Bridge",code:3)}
       NSPasteboard.general.clearContents();guard NSPasteboard.general.setString(text,forType:.string) else{throw NSError(domain:"Bridge",code:4)}
       response["ok"]=true;response["result"]=["guest_clipboard_set":true,"utf8_bytes":text.utf8.count]
      case "status":response["ok"]=true;response["result"]=heartbeat
      default:throw NSError(domain:"Bridge",code:5,userInfo:[NSLocalizedDescriptionKey:"Unsupported bridge operation"])
      }
     } catch{response["error"]=["code":"guest_bridge_error","message":String(describing:error)]}
     try? json(response).write(to:root.appendingPathComponent(name+".response.json"),options:.atomic)
    }
   }
   try? await Task.sleep(nanoseconds:100_000_000)
  }
 }
}

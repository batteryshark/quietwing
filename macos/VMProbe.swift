import Foundation
import Virtualization

@main struct Probe {
    static func main() async {
        #if arch(arm64)
        let architecture="arm64"
        #else
        let architecture="unsupported"
        #endif
        var result:[String:Any] = ["probe":"read-only Virtualization capability and restore metadata",
            "virtualization_supported":VZVirtualMachine.isSupported,
            "host_architecture":architecture,"vm_created":false,"vm_booted":false,"image_downloaded":false,
            "guest_disk_allocated":false,"audio_devices_default":VZVirtualMachineConfiguration().audioDevices.count,
            "minimum_allowed_cpu_count":VZVirtualMachineConfiguration.minimumAllowedCPUCount,
            "maximum_allowed_cpu_count":VZVirtualMachineConfiguration.maximumAllowedCPUCount]
        if let fs=try? FileManager.default.attributesOfFileSystem(forPath:NSHomeDirectory()),let bytes=fs[.systemFreeSize] as? NSNumber {result["host_free_bytes"]=bytes}
        if CommandLine.arguments.contains("--latest-metadata") {
            do {
                let image=try await VZMacOSRestoreImage.latestSupported
                let version=image.operatingSystemVersion
                var metadata:[String:Any] = ["version":"\(version.majorVersion).\(version.minorVersion).\(version.patchVersion)",
                    "build":image.buildVersion,"restore_url":image.url.absoluteString,"supported":image.isSupported]
                if let req=image.mostFeaturefulSupportedConfiguration {
                    metadata["minimum_supported_cpu_count"]=req.minimumSupportedCPUCount
                    metadata["minimum_supported_memory_bytes"]=req.minimumSupportedMemorySize
                    metadata["hardware_model_supported"]=req.hardwareModel.isSupported
                }
                result["latest_restore_metadata"]=metadata
                result["ok"]=true
            } catch {result["ok"]=false;result["error"]=String(describing:error)}
        } else {result["ok"]=true}
        let data=try! JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys])
        print(String(data:data,encoding:.utf8)!)
    }
}

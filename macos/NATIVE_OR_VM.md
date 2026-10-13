# Mac backend choice and measured result

The selected backend is now a working dedicated macOS VM. The earlier read-only probe is historical; the VM has since been downloaded, installed and controlled on this Apple Silicon Mac. The current starting budget is the measured Apple restore minimum: **2 vCPU / 4 GiB RAM**, with a **64 GiB sparse disk**. It uses Apple's built-in framework and a locally ad-hoc-signed helper, with no VM manager, admin password, host user/Sharing/TCC/firewall change or host reboot.

| Aspect | Native separate-user GUI | Implemented macOS VM |
| --- | --- | --- |
| Setup | Dedicated standard account, restricted Screen Sharing, different-user authentication/initial login and worker permissions still required | Installed `minimal` is ready. New VM requires compatible Apple restore image and guest Setup Assistant/account; no Apple Account is needed |
| Control | Generic native worker, audio and same-Mac loopback acceptance remain incomplete | Real TextEdit control, direct guest USB keyboard/mouse, exact Unicode save/readback and capture passed |
| Capture privacy | Native Screen Recording depends on worker/session permission | `SCShareableContent.currentProcess` captures only the owning VM app window without TCC consent; measured while preflight=false |
| Audio | A separate login does not establish separate output; native exec/input remain gated | `audioDevices=[]`; live guest has zero CoreAudio devices and default output device0 |
| Lifetime | Screen Sharing/remote GUI lifetime and worker bootstrap still need acceptance | Persistent owner survives CLI exit; save/stop/start resumes the same unsaved document and guest bridge without login |
| Resources | Lower extra OS overhead | 4 GiB reserved guest RAM while running; sparse disk actual use grows, 29.45 GiB at final cleanup; restore download about 24.8 GiB cache was removed; snapshot about 1.44 GiB in the measured run |
| Graphics | Native host GPU access possible; isolated-session path untested | Apple Paravirtual Metal device rendered/read back24/24 distinct frames correctly. No game, broad GPU-feature or performance compatibility claim |

The guest shares only its private helper transfer directory. NAT supports guest connectivity without opening a host TCP listener or forwarding ports. Shared CPU/GPU resources and network access are not a hostile-code security boundary. There is no automatic bidirectional clipboard synchronization; Unicode explicitly sets only the guest clipboard. A guest-only LaunchAgent supplies generic exec through nonce/generation-bound file IPC. Host Accessibility/Screen Recording was not requested.

The current installed instance is reusable, but new-instance provisioning is explicit rather than an unattended installer/account wizard. Saved state is tied to this host and compatible VM configuration. Snapshot restore after host/OS changes, long-term unattended use, multiple VMs, guest reboot recovery and arbitrary games are untested.

Native separate-user remains a plausible lower-overhead future option. Apple documents concurrent different-account remote virtual displays. Apple also documents stereo audio in High Performance Screen Sharing and physical display blanking for a same-user connection; this does not establish isolated audio for a different user. Same-Mac loopback and safe native audio have not been proved. No host account/Sharing provisioning was performed for that route.

Primary sources:

- [Apple macOS VM sample](https://developer.apple.com/documentation/virtualization/running-macos-in-a-virtual-machine-on-apple-silicon), [installation](https://developer.apple.com/documentation/virtualization/installing-macos-on-a-virtual-machine) and [virtualization entitlement](https://developer.apple.com/documentation/virtualization/adding-the-virtualization-entitlement-to-your-project).
- [Apple VM view](https://developer.apple.com/documentation/virtualization/vzvirtualmachineview) forwards view input to configured guest devices; this project's offscreen event/capture behavior is measured separately.
- [Apple current-process shareable content](https://developer.apple.com/documentation/screencapturekit/scshareablecontent/getcurrentprocessshareablecontent(completionhandler:)); installed SCShareableContent.h explicitly states own-process redacted content is available without TCC user consent (macOS14.4+).
- [Apple audio configuration](https://developer.apple.com/documentation/virtualization/vzvirtualmachineconfiguration/audiodevices): empty by default.
- [Apple WWDC22 VM graphics](https://developer.apple.com/videos/play/wwdc2022/10002/) describes macOS virtual graphics Metal support.
- [Apple directory sharing](https://developer.apple.com/documentation/virtualization/vzvirtiofilesystemdeviceconfiguration) and [macOS automount tag](https://developer.apple.com/documentation/virtualization/vzvirtiofilesystemdeviceconfiguration/macosguestautomounttag).
- [Apple separate-account remote display](https://support.apple.com/guide/remote-desktop/choose-how-to-control-and-observe-apd4f46319e/mac) and [High Performance Screen Sharing](https://support.apple.com/guide/remote-desktop/use-high-performance-screen-sharing-apdf8e09f5a9/mac).

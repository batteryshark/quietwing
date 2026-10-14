# macOS: isolated macOS VM

The default backend is a real macOS guest on Apple's Virtualization.framework. The locally provisioned `minimal` test instance is reusable; the package does not include a VM image. This instance runs with 2 virtual CPUs, 4 GiB RAM and a 64 GiB sparse disk. No VM manager is installed. Its owned view stays completely offscreen; capture and input target only that view. Host focus/cursor/Sharing/TCC settings are untouched. Audio devices are absent, verified in both VM configuration and the running guest.

Validated host/build environment: Apple Silicon, macOS 27.0.1, SDK 27 and Swift 6.4. Older macOS/toolchain combinations have not been accepted; see [provisioning prerequisites](PROVISIONING.md) for the API lower bounds and build-target limitation.

From this project's root:

```sh
python3 deskhelper.py start --id minimal
python3 deskhelper.py status --id minimal
python3 deskhelper.py exec --id minimal -- /usr/bin/open -a TextEdit
python3 deskhelper.py input --id minimal --type 'Hello — café 日本語 👋'
python3 deskhelper.py capture --id minimal --output /absolute/new-file.png
python3 deskhelper.py stop --id minimal
```

Wait for `session.phase: running` after start. `status` and `attach` use a live owner socket; verified `exec`/Unicode capabilities additionally require a fresh nonce response from the guest bridge. There is no fallback to the host desktop. Capture paths must be new files. Mouse buttons are 1 left, 2 middle, 3 right. Key syntax includes `cmd+a`, `cmd+shift+g`, `ctrl+c`, `enter`, `escape`, arrows and navigation keys. ASCII uses US physical keyboard codes; Unicode uses only the guest clipboard followed by guest Cmd+V. TextEdit/app editing preferences may transform text normally.

`stop` pauses and saves the entire owned VM memory/session, then exits its owner. `start` restores the same desktop without login; this was measured with an unsaved TextEdit document and the same guest bridge process/instance. Controller exit alone leaves the guest running. Stop retains the disk and encrypted, host-bound snapshot; it does not uninstall the guest. RAM is released while stopped. A crash cannot promise unsaved work: cold boot presents guest login, using the separate guest-local account. Snapshots are consumed before resuming disk mutation, never replayed automatically after a failed resume.

State is private under `~/.local/state/deskhelper/macos-vm/minimal` (or `DESKHELPER_STATE_ROOT/macos-vm/NAME`). It holds disk/platform files, socket/lock, snapshot, generated guest-local credential and a single helper transfer directory. Credentials are never source/evidence/command arguments. The verified IPSW installation cache has been removed; ordinary boot/restore does not need it. Retained disk allocation is about 29.45 GiB plus a 1.44 GiB saved session. No host home/project directory is shared. Guest NAT is enabled, with no inbound listener/port-forward. The guest bridge's LaunchAgent exists **inside the guest only**; no host autostart is installed.

`deskhelper build` (or source `python3 macos/build_vm.py`) compiles and ad-hoc signs the VM owner/probe and builds GuestBridge using existing Apple command-line tools. Assets and the Swift module cache go to `DESKHELPER_BUILD_ROOT/macos`, default `~/Library/Caches/desktop-session-helper/macos`; the build never writes installed package resources. Save/stop owned VMs before rebuilding. It does not download or provision. New instance setup is explicit: select Apple's supported restore metadata, download and verify its IPSW, install to fresh private disk/platform files, complete guest Setup Assistant with a guest-only account, stage the bridge binary/bootstrap/bridge ID in that instance's helper directory and run `guest_bootstrap.sh` inside the guest. `start` is not an unattended new-guest account/setup wizard. Do not copy the installed minimal guest's identity files to make another instance.

See [PROVISIONING.md](PROVISIONING.md) for reproducible setup commands and [NATIVE_OR_VM.md](NATIVE_OR_VM.md) for the native-session tradeoff. Machine-specific `VM_RESULTS.md` evidence, when present in a development checkout, is not shipped in the package. The optional `--backend native` path remains guarded and incomplete: it rejects the host console user and blocks native exec/input until real audio/session isolation is available. It is not the default.

Consumers can pin `status`, `capture`, `input`, `exec` and `stop` to `--expect-generation TOKEN`, using `session.generation` from a live response. The owner rejects a mismatch with `generation_changed` before performing the action, including bridge mutations. An unpinned status can discover a replacement; a pinned action never automatically retargets it. Saved/stopped responses have a null generation. Calls without this option retain their existing behavior.

Capabilities are explicit booleans: capture, input, keyboard, pointer, exec, audio_capture, audio_silent, browser and accessibility. The VM supplies pixels and native guest input, generic process launch and silent audio (no audio device). It does not supply audio recording, browser DOM or accessibility-tree APIs. Exec/Unicode readiness requires a fresh guest nonce bound to the current owner.

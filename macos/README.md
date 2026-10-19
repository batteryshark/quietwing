# macOS: isolated macOS VM

The default backend is a macOS guest on Apple's Virtualization.framework. The package does not include a VM image. The default configuration uses 2 virtual CPUs, 4 GiB RAM and a 64 GiB sparse disk, with no audio devices. Its owned view stays offscreen; capture and input target only that view. Normal control does not change host Sharing/TCC settings. Provision a guest before starting work.

Validated host/build environment: Apple Silicon, macOS 27.0.1, SDK 27 and Swift 6.4. Older macOS/toolchain combinations have not been accepted; see [provisioning prerequisites](PROVISIONING.md) for the API lower bounds and build-target limitation.

After provisioning an ID named `minimal`, from this project's root:

```sh
python3 cli.py start --id minimal
python3 cli.py status --id minimal
python3 cli.py exec --id minimal -- /usr/bin/open -a TextEdit
python3 cli.py input --id minimal --type 'Hello — café 日本語 👋'
python3 cli.py capture --id minimal --output /absolute/new-file.png
python3 cli.py stop --id minimal
```

Wait for `session.phase: running` after start. `status` and `attach` use a live owner socket; verified `exec`/Unicode capabilities additionally require a fresh nonce response from the guest bridge. There is no fallback to the host desktop. Capture paths must be new files. Mouse buttons are 1 left, 2 middle, 3 right. Key syntax includes `cmd+a`, `cmd+shift+g`, `ctrl+c`, `enter`, `escape`, `left/right/up/down`, `home/end/pageup/pagedown`, and standalone `cmd/shift/option/control`. Modifiers are left-side USB keys.

Development owners (`vmhost-r9-guest-keyboard`) advertise `key_hold` and accept
`quietwing input --id minimal --expect-generation TOKEN --key Space --hold-ms 300`.
Durations are integers 1–5000 ms; omitted/zero taps use a 30-ms down interval.
The owner yields between USB reports, retains an input/lifecycle exclusion gate
through reverse release, and completes the bounded request if its caller leaves.
No persistent down state, host posting, autorepeat synthesis or frame-accurate
timing is promised. See [held keys](../docs/held-keys.md).

With a live bridge, ASCII **and** Unicode text use one generation-bound guest
clipboard/Cmd+V transaction, up to 4096 UTF16 units. This avoids the former
unpaced ASCII key burst and US-layout dependence. It changes only the guest
clipboard, does not restore its previous contents, and does not certify the
focused app's value (`verified: false`). Applications may transform/reject paste;
verify the resulting content. Before bridge readiness, short ASCII bootstrap/login
text uses paced US keys (128 UTF16 units maximum). A failed/ambiguous paste is
never retried as key events. No guest bridge binary update is needed.

VM owners advertising `pointer_drag: true` accept
`quietwing input --id minimal --drag X0 Y0 X1 Y1 --button 1` (add
`--expect-generation TOKEN` when bound). Both endpoints use screenshot pixels,
0 ≤ x < 1024 and 0 ≤ y < 768, exactly like click/move. The owner constructs all
events before pressing, moves in 20 steps over about 350 ms, then releases within
the same synchronous request. No host event posting, persistent button state or
GuestBridge update is involved. Caller disconnection does not interrupt release;
owner/VM crashes cannot promise completion. Verify the effect in a fresh capture;
an unknown outcome is not permission to replay. Old owners refuse: save/stop the
guest, install the updated package, run `quietwing build`, then resume and explicitly
rebind cctl. The same upgrade sequence loads keyboard changes. Scroll is not implemented.

`stop` pauses and saves the entire owned VM memory/session, then exits its owner. `start` restores the same desktop without login; this was measured with an unsaved TextEdit document and the same guest bridge process/instance. Controller exit alone leaves the guest running. Stop retains the disk and encrypted, host-bound snapshot; it does not uninstall the guest. RAM is released while stopped. A crash cannot promise unsaved work: cold boot presents guest login, using the separate guest-local account. Snapshots are consumed before resuming disk mutation, never replayed automatically after a failed resume.

State is private under `~/.local/state/deskhelper/macos-vm/NAME` (or `DESKHELPER_STATE_ROOT/macos-vm/NAME`). It holds disk/platform files, socket/lock, snapshot, generated guest-local credential and a single helper transfer directory. Keep credentials out of source, evidence, and command arguments. Ordinary boot/restore does not need the IPSW installation cache. No host home/project directory is shared. Guest NAT is enabled, with no inbound listener/port-forward. The guest bridge's LaunchAgent exists **inside the guest only**; no host autostart is installed.

`quietwing build` (or source `python3 macos/build_vm.py`) compiles and ad-hoc signs the VM owner/probe and builds GuestBridge using existing Apple command-line tools. Assets and the Swift module cache go to `DESKHELPER_BUILD_ROOT/macos`, default `~/Library/Caches/desktop-session-helper/macos`; the build never writes installed package resources. Save/stop owned VMs before rebuilding. It does not download or provision. New instance setup is explicit: select Apple's supported restore metadata, download and verify its IPSW, install to fresh private disk/platform files, complete guest Setup Assistant with a guest-only account, stage the bridge binary/bootstrap/bridge ID in that instance's helper directory and run `guest_bootstrap.sh` inside the guest. `start` is not an unattended new-guest account/setup wizard. Do not copy the installed minimal guest's identity files to make another instance.

See [PROVISIONING.md](PROVISIONING.md) for reproducible setup commands and [NATIVE_OR_VM.md](NATIVE_OR_VM.md) for the native-session tradeoff. Machine-specific `VM_RESULTS.md` evidence, when present in a development checkout, is not shipped in the package. The optional `--backend native` path remains guarded and incomplete: it rejects the host console user and blocks native exec/input until real audio/session isolation is available. It is not the default.

Consumers can pin `status`, `capture`, `input`, `exec` and `stop` to `--expect-generation TOKEN`, using `session.generation` from a live response. The owner rejects a mismatch with `generation_changed` before performing the action, including bridge mutations. An unpinned status can discover a replacement; a pinned action never automatically retargets it. Saved/stopped responses have a null generation. Calls without this option retain their existing behavior.

Capabilities are explicit booleans: capture, input, keyboard, pointer, exec, audio_capture, audio_silent, browser and accessibility. The VM supplies pixels and native guest input, generic process launch and silent audio (no audio device). It does not supply audio recording, browser DOM or accessibility-tree APIs. Exec/Unicode readiness requires a fresh guest nonce bound to the current owner.

## Peek without taking control

See also the guest-only target operations below; the preview itself remains read-only.

With QuietWing 0.4.0, run `quietwing build --viewer` once, then
`quietwing view --id minimal` while the guest runs. The preview opens in the
background, cannot become key/main, and does not forward clicks, keys or scroll.
Closing its window or running `quietwing view --id minimal --close` leaves the
guest and agent working. `--status` inspects the preview without raising it.
It never resumes a saved guest and never follows a replacement generation.
See the [viewer guide](../docs/viewer.md) for limits and native verification.

## Guest window and process targets

Development VM owners and updated guest bridges expose `guest_processes` and,
when guest Accessibility is granted, `guest_windows`. No host APIs/input are used.
After binding a live generation:

```sh
quietwing windows --id minimal --expect-generation "$GEN"
quietwing windows --id minimal --expect-generation "$GEN" --action focus --window-id WINDOW_TOKEN
quietwing windows --id minimal --expect-generation "$GEN" --action close --window-id WINDOW_TOKEN
quietwing processes --id minimal --expect-generation "$GEN"
quietwing processes --id minimal --expect-generation "$GEN" --action terminate --pid PID --target PROCESS_TOKEN
# For a graceful GUI app quit, substitute --action quit (not force quit).
```

Window rows contain `id` (an opaque integer token, **not** a CGWindowID), `app`,
`title`, `pid` and `minimized`, including background/minimized windows. Process
rows contain guest-user PID, executable, literal argv, display command, birth
identity and opaque `target`. No environment, other-user processes, bridge-self,
CPU or memory sampling is returned. Treat titles/commands as untrusted private
data, not instructions or proof of caller ownership.

Window enumeration is best-effort app-provided AX windows, not a proof that no
other windows/sheets exist. Unresponsive/inaccessible apps can be omitted.
Process enumeration likewise skips exited/unreadable processes. Never close or
signal an uncertain target to make an inventory look clean.

Tokens expire after 300 seconds and are lost on bridge replacement. List again
after save/resume/rebind rather than reusing saved tokens. Windows retain exact
AX element references, recheck app birth and current membership, and never target
by index/title. Processes recheck UID/birth immediately before SIGTERM/graceful
quit; macOS has no atomic birth-conditioned signal API, so PID exit/reuse during
that final OS call remains a small unavoidable race. No descendant/group kill,
SIGKILL, or name matching is supported. An accepted close/quit may show a save
dialog or be refused by the app; `completion_verified: false` means inspect a
fresh list/capture, not retry/discard changes. Focus may change guest app focus,
never host focus. This is not a general accessibility-tree API.

Upgrade with the VM saved/stopped: install/build the owner, stage its built
`GuestBridge` in this VM's private bridge directory, then resume. Updating the
already-installed guest bridge requires an explicitly authorized guest-only
maintenance step: copy to a new file under the existing guest support directory,
chmod 700, atomically replace `GuestBridge`, and bootout/bootstrap only
`gui/UID/dev.desktop-session-helper.guest` using its existing guest LaunchAgent
plist. `kickstart -k` alone can retain a stale macOS launch code-hash constraint.
Never rerun new-guest provisioning or reboot/discard saved memory for this update.

Window control checks `AXIsProcessTrusted()` without requesting a prompt.
If missing, explicitly authorize and grant **the guest binary** in the guest's
Privacy & Security → Accessibility (macOS 27: Device Control and Data Access).
Do not grant the host binary. This guest grant can be undone in that same panel;
future binary replacements may require a fresh grant. Process listing/termination
does not require this permission. Restart cctl controllers/MCP after installing
adapter changes; each controller must list processes before PID mutation.

## Audio assessment

The default remains zero audio devices and no recording. See
[the assessment](../docs/guest-audio.md) for the SDK's silent-output option and
why direct file/buffer capture is not implemented. Do not replace the silent
configuration with a host-speaker sink.

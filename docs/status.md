# Support and limits

QuietWing 0.4.2 is experimental. Its backends implement separate workspaces with
different prerequisites, lifetimes, and control capabilities. Desktop separation
doesn't establish safe execution of arbitrary untrusted programs; read the
[security model](../SECURITY.md).

## Platform support

- Mac uses a provisioned macOS VM on Apple Silicon. The recorded host/toolchain
  is macOS 27.0.1, SDK 27, Swift 6.4. Older combinations remain unvalidated; API
  lower bounds in the [provisioning guide](../macos/PROVISIONING.md) aren't a
  compatibility promise. The VM has no audio devices or host home/project share.
  The optional native-user backend is guarded and incomplete.
- Linux uses Xvfb with private HOME/XDG, D-Bus, and default audio routing under
  the same UID. The recorded target is Debian 13 with llvmpipe software rendering.
  Applications retain filesystem/device access permitted to that user.
- Windows requires a signed-in ParaDesk child session and a connected,
  non-minimized viewer. Attach may hide the viewer; stop/crash/rollback preserve
  its visibility and the existing login. Lock, secure desktop, disconnect, or
  provider loss requires operator attention. There is no automatic sign-in or
  reconnect. The setup guide covers the tested x64 Windows 11 environment and
  [pinned provider prerequisites](../windows/SETUP.md).

The package ships native source for local compilation. VM images, credentials,
runtime state, and compiled binaries are excluded. Fresh-machine setup and
arbitrary OS/toolchain combinations need their own validation.

## Capabilities

The [descriptor](../session.schema.json) reports live boolean capabilities.
Capture, native keyboard/pointer input, and generic app launch are the common
surface once the backend is ready. Mac exec/Unicode readiness also needs
its guest bridge. Generation preconditions refuse replaced instances before an
action; they don't constrain the authority of a program launched inside one.

Windows and development Mac VM `key_hold` support bounded 1–5000 ms key/chord holds only when the live
worker advertises it. Linux and older workers refuse holds. Save owned
work before explicit reattachment to load new worker code. Timing includes
delivery overhead; no frame-accurate game input or general game/GPU compatibility
is promised. See [held keys](held-keys.md).

Development Mac VM owners advertising `pointer_drag` support bounded guest-only
press/move/release through computer-ctrl's `drag`, with the same screenshot/zoom
coordinate mapping as click. Save/stop, rebuild and resume to load the new owner;
older owners and other platforms refuse. Scroll remains unsupported. Native
validation for this development change is recorded below; no cross-platform or
game compatibility follows from it.

Development Mac bridges add guest-only window list/focus/close and guest-user
process list/targeted SIGTERM/graceful quit through computer-ctrl. See
[Mac targets](../macos/README.md#guest-window-and-process-targets) for permissions,
300-second tokens and dispatch-only receipts. Other backends/old bridges refuse.
The adapter still lacks accessibility trees, DOM/CDP, general window geometry,
scroll, and audio/video tools. Linux applications can record the private
null monitor through `exec`, but QuietWing has no dedicated recording command.
Application singleton IPC and explicit device routes need their own checks.

The [Mac preview](viewer.md) is read-only for local guests and remote
Linux/Windows targets over SSH. Follow mode waits across remote attachment
generations; it never acquires a session. Linux/Windows have no native preview
window, common takeover control, or agent pause panel.

## Lifetimes and persistence

Closing a caller leaves the work instance alive. Mac stop saves VM memory and
releases RAM; a cold boot/crash can require guest login. It retains disk,
identity, bridge, and host-bound snapshot, with no automatic idle save policy.

Linux defaults to a fixed 30-minute TTL, adjustable at acquisition up to 86400
seconds. Activity and preview frames don't extend it. Stop/expiry ends owned apps
and removes runtime sockets/authority material; session files remain. Recreating
a stopped ID makes a new desktop, without restoring running applications.

Windows closes owned apps/workers after 30 minutes without activity other than
preview frames. Stop preserves the native login/provider and current viewer
visibility. Uninstalling the package doesn't sign out that child. Save documents
before stop or expiry. [Daily use](daily-use.md) explains recovery; commands
aren't automatically replayed after a timeout.

## Development Mac drag validation — 2026-10-19

Portable checks passed (133 tests, three Windows-native skips on Mac), as did
local NSEvent tests for left/middle/right event sequences, interpolation, endpoint
bounds and release. Native sources built successfully; fresh wheel/source archives
passed audit and the installed-package check passed. Consumer coverage includes
frame scaling/zoom, generation refusal, old-worker refusal and release receipts.

The installed cctl direct-MCP adapter's left-button drag moved a disposable TextEdit window using a
half-size screenshot's coordinates and visibly selected text in the existing Mac
guest. Both actions confirmed release. The owned test window closed and the VM
saved/stopped, with its owner exited. The VM stayed offscreen/nonkey/nonmain and
reported no host input. Its idle-locked resume required an explicitly authorized
guest-local unlock; idle lock can require that again. No host settings changed.
Middle/right button identity is covered by local event tests, not live guest gestures.
Scroll is deferred. These are bounded native/scripted MCP checks, not new
autonomous Codex/OpenCode workflows; those two-harness reruns remain deferred.

## Development Mac keyboard validation — 2026-10-19

`vmhost-r9-guest-keyboard` adds bounded held keys, proper device-specific modifier
reports, and asynchronous USB pacing behind an input/lifecycle exclusion gate.
The former ASCII path submitted an entire unpaced key burst; live-bridge text now
uses the existing guest-only clipboard and one owner-guarded paste transaction,
for ASCII and Unicode alike (4096 UTF16 units). Bridge-less US-key bootstrap text
is paced and limited to 128 units. There is no host clipboard/input path, silent
hold downgrade, paste replay or general focused-field read-back claim.

Installed cctl CLI checks in the existing saved Mac guest observed 300-ms Space,
all four arrows, all four modifiers and Shift+Left in a disposable native app
polling guest HID key state across multiple ticks; all keys were released.
Cmd+N created new Terminal and TextEdit windows. A 1,000-character mixed ASCII
payload typed through cctl into a new plain TextEdit document was saved and read
back exactly, including punctuation and literal shell metacharacters. A stale
generation hold refused before delivery. Test windows closed; protected apps/data
remained and the VM saved/stopped. Host load retained headroom; the owner stayed
offscreen/nonkey/nonmain and reported no host input or activation.

Portable tests, local NSEvent tests and native build/package checks cover the
new paths. These are bounded native/CLI checks, not two new autonomous harness
workflows; those reruns remain deferred. The disposable Safari local-page check
showed a blank body, so no browser/game compatibility is claimed. Scroll remains
deferred. No Linux/Windows behavior change or cross-platform native claim follows.

## Development Mac guest targets — 2026-10-19

The guest bridge lists guest-user executable/argv/PID/birth identities and AX
windows (app/title/PID), retaining expiring exact element references and process
tokens. The owner pins all reads/actions to both owner and guest generations.
Guest Accessibility is checked without prompting; it was explicitly granted
inside the available guest for native validation. No host permission/input path
was used. Audio remains disabled; the [audio assessment](guest-audio.md) documents
the public nil/discard sink and the lack of a supported host PCM capture sink.

Portable checks passed (139 tests, three Windows-native skips). A local compiled
synthetic target-ledger test also verified owner-generation invalidation, exact
PID and expiry without invoking desktop/process APIs. Installed cctl
adapter calls in the existing guest listed windows/processes, focused an exact
Terminal window and a disposable TextEdit file, closed that exact file window,
and terminated an identified disposable sleep process. Graceful quit requested a
save review in a separately launched TextEdit instance restoring prior documents;
it was cancelled, then only that newly created instance was terminated. The
pre-existing TextEdit instance and documents remained. This illustrates why quit
receipts are not completion claims and app launch is not document ownership.
Unknown targets and stale owner generation refused; no host fallback/replay.
The guest saved/stopped with its owner exited; its owner reported offscreen,
nonkey/nonmain operation and no host input/activation. These are bounded native
adapter checks, not two new autonomous harness workflows; those reruns remain
deferred. No Linux/Windows native behavior claim follows.

## Guest Safari rendering diagnosis — 2026-10-20

On the available macOS 27.0.1/Apple Paravirtual Metal guest, synthetic plain HTML,
CSS animation, canvas and WebGL content were missing from both QuietWing capture
and independent guest `screencapture`; silent video remained visible. Fresh Safari
processes with **GPU Process: DOM Rendering** enabled restored the content in both
methods. An ON/OFF/ON comparison reproduced the dependency. Reloading the original
process was insufficient. See the [guest-only workaround](../macos/README.md#safari-loads-a-page-but-its-body-is-blank),
including how to preserve another caller's Safari windows. The native preview
displayed the same working frames but shares QuietWing's capture pipeline; it is
not a third independent rendering test. No capture implementation change was made.

The temporary guest Screen Recording grant was revoked, task-owned windows,
processes and preview were closed, and the guest saved with protected state
retained. No host settings/input or new browser installation was used; audio
devices remained absent. This is synthetic-page diagnosis, not application/game
acceptance or two new autonomous harness workflows. Other guest/OS versions and
WebKit's underlying defect remain unvalidated.

## Release history (published)

[v0.4.2](https://github.com/batteryshark/quietwing/releases/tag/v0.4.2) adds SSH
preview follow mode and Windows held keys. Earlier releases added the Mac viewer
and live Windows provider-readiness checks. Published release notes and
[tagged CI](https://github.com/batteryshark/quietwing/actions/workflows/ci.yml)
describe their historical checks. CI covers portable/package behavior; it
doesn't provision a guest or authenticate a native child. A portable test pass
doesn't establish cross-platform native acceptance.

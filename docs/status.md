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

Windows `key_hold` supports bounded 1–5000 ms key/chord holds only when the live
worker advertises it. Other backends and older workers refuse holds. Save owned
work before explicit reattachment to load new worker code. Timing includes
delivery overhead; no frame-accurate game input or general game/GPU compatibility
is promised. See [held keys](held-keys.md).

The computer-ctrl adapter lacks accessibility, DOM/CDP, window management,
drag/scroll, and audio/video tools. Linux applications can record the private
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

## Release history

[v0.4.2](https://github.com/batteryshark/quietwing/releases/tag/v0.4.2) adds SSH
preview follow mode and Windows held keys. Earlier releases added the Mac viewer
and live Windows provider-readiness checks. Published release notes and
[tagged CI](https://github.com/batteryshark/quietwing/actions/workflows/ci.yml)
describe their historical checks. CI covers portable/package behavior; it
doesn't provision a guest or authenticate a native child. A portable test pass
doesn't establish cross-platform native acceptance.

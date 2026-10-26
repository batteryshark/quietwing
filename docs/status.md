# Support and limits

QuietWing 0.4.2 is experimental. Desktop separation does not make arbitrary
untrusted programs safe; see the [security model](../SECURITY.md).

## Platform support

- **Mac:** a provisioned macOS VM on Apple Silicon. The validated host/toolchain
  is macOS 27.0.1, SDK 27, Swift 6.4. Older combinations remain unvalidated;
  [API lower bounds](../macos/PROVISIONING.md) are not a compatibility promise.
  The VM has no audio devices or host home/project share. The optional native-user
  backend is guarded and incomplete.
- **Linux:** Xvfb, private HOME/XDG, D-Bus and default audio routing under the
  same UID. Validation used Debian 13 with llvmpipe software rendering.
  Applications retain that user's filesystem and device permissions.
- **Windows:** a signed-in ParaDesk child with a connected, non-minimized viewer.
  Stop, crash and rollback preserve the login and viewer visibility. Lock, secure
  desktop, disconnect or provider loss require operator attention; there is no
  automatic sign-in or reconnect. See [setup and provider pins](../windows/SETUP.md).

Native source is compiled locally. Packages exclude VM images, credentials,
runtime state and compiled binaries. Fresh-machine setup needs validation.

## Capabilities

The live [descriptor](../session.schema.json) reports capabilities. Capture,
keyboard/pointer input and app launch are common once a backend is ready. Mac
exec and Unicode text require its guest bridge. Generation checks reject replaced
instances but do not restrict a launched program's authority.

- Windows and development Mac VM workers advertising `key_hold` support bounded
  1–5000 ms holds; Linux and older workers refuse. Timing is not frame-accurate.
  See [held keys](held-keys.md) for worker upgrades.
- Development Mac owners advertising `pointer_drag` support bounded guest-only
  drag. Other platforms and older owners refuse it. Middle/right button sequences
  have local event-test coverage, not live guest gesture validation.
- Mac bridge text uses one guest-only clipboard/paste transaction, limited to
  4096 UTF16 units. Bridge-less bootstrap supports 128 paced US-key units.
  Neither path promises application-level read-back verification.
- Development Mac bridges support guest window and process targets with
  permissions, expiring tokens and dispatch-only receipts. See
  [Mac targets](../macos/README.md#guest-window-and-process-targets).
- General accessibility trees, DOM/CDP, window geometry, scroll and audio/video
  tools remain unsupported. Linux apps can record the private null monitor through
  `exec`. Singleton IPC and explicit device routing need separate checks.
- The [Mac preview](viewer.md) is read-only and never acquires a session. There
  is no native Linux/Windows preview window, common takeover or agent pause panel.

Development Mac drag, keyboard and target operations have bounded native/adapter
checks; new two-harness autonomous acceptance runs remain outstanding. These
checks do not establish game or cross-platform compatibility. Safari on the
validated guest may require the [guest-only rendering workaround](../macos/README.md#safari-loads-a-page-but-its-body-is-blank).
Other guest/OS versions remain unvalidated. See the [audio assessment](guest-audio.md)
for the silent guest's limitations.

## Lifetimes and persistence

- Mac stop saves memory and releases RAM, retaining disk, identity, bridge and
  host-bound snapshot. Cold boot, crash or idle lock can require guest login.
  There is no automatic idle-save policy.
- Linux has a fixed 30-minute TTL, adjustable at acquisition up to 86400 seconds.
  Activity does not extend it. Stop/expiry ends owned apps and removes runtime
  sockets and authority material; files remain. Recreating an ID starts a new desktop.
- Windows closes owned apps/workers after 30 minutes without activity other than
  preview frames. Stop and uninstall preserve the external login and viewer state.

Caller exit leaves the instance alive within these limits. Save documents before
stopping. [Daily use](daily-use.md) covers recovery; interrupted mutations are not
automatically replayed.

## Releases and validation

[v0.4.2](https://github.com/batteryshark/quietwing/releases/tag/v0.4.2) adds SSH
preview follow mode and Windows held keys. See the [changelog](../CHANGELOG.md)
and [CI](https://github.com/batteryshark/quietwing/actions/workflows/ci.yml).
CI verifies portable/package behavior; it neither provisions a guest nor
authenticates a native child, and does not establish native platform acceptance.

# Current status

Updated 2026-10-15. [QuietWing 0.3.0](https://github.com/batteryshark/quietwing/releases/tag/v0.3.0)
is the first experimental MIT-licensed GitHub release. The package, import, and
sole executable are `quietwing`. Computer-ctrl's integration is
[merged](https://github.com/batteryshark/computer-ctrl/pull/1).

## Release validation

| Check | Result |
| --- | --- |
| Hosted QuietWing CI | Linux, macOS, Windows; Python 3.11 and 3.14 portable checks, clean wheel install, source rebuild/distribution audit passed. See [CI](https://github.com/batteryshark/quietwing/actions/workflows/ci.yml). |
| Hosted computer-ctrl CI | Linux, macOS, Windows; Python 3.11 and 3.13 regression and package jobs passed. 141 regression tests per run. |
| Portable companion checks on Mac | 34 passed: 15 dispatcher/distribution, 11 Windows fake transport, 8 Mac fake generation cases. |
| Native source comparison | 17 runtime/native source files identical to the historically validated 0.2 backend. |
| Mac, updated cctl and installed QuietWing | Saved guest resumed, fresh capture visually inspected, provider identity verified, guest saved/stopped again. Host pointer/focus unchanged, no audio devices; no input sent in this smoke check. |
| Linux, installed QuietWing | Two separate SSH stages passed ordinary Mousepad/Xmessage input, exact Unicode/metacharacter saved text, native click, fresh capture, private audio, generation refusal, reconnect, TTL expiry, and owned cleanup. 167 unchanged host metadata samples; only the original X display remained. |
| Windows, installed QuietWing and private consumer environment | Clean install/entry point, native C# compilation without launching the worker, pure transport tests, and refusal without an active child passed. Provider state file and installed resources unchanged. No input, capture, scheduled task, sign-in, reconnect, or main-desktop controller changes. |
| Windows current live-GUI scope | The existing ParaDesk child was disconnected. It remained unavailable after the host became available; a new 0.3 live GUI rerun was not attempted without authentication. Historical 0.2 native/two-harness results below remain the evidence for unchanged GUI backend behavior. |

A window interruption was reported during Windows headless validation. Final
inspection found no remaining release-test process or QuietWing window; the source
of the interruption was not identified. This run does not establish foreground
noninterference for every setup or diagnostic path.

Release archives include source, license, guides, and native build resources;
private evidence, credentials, VM disks/snapshots, compiled binaries, and runtime
state are excluded. Release assets and SHA256SUMS are built by the reviewed-tag
workflow. Native images/inventories remain private.

## Historical native evidence

Version 0.2 acceptance on 2026-10-13 exercised installed wheels, ordinary native
apps, input/capture, reconnect/save-resume, stale refusal, and owned cleanup on all
three platforms. Actual Codex CLI and OpenCode editor workflows passed on each.
Saved Unicode, successful tool calls, screenshots, and host pointer/focus metadata
were checked independently. [VALIDATION.md](../VALIDATION.md) and its platform
reports preserve exact source/package identities; they are not new-name reruns.

## Current limits

- No unified live viewer, takeover control, or agent pause/resume panel.
- Windows requires an authenticated, connected, non-minimized ParaDesk viewer;
  no automatic sign-in/reconnect. The 0.3 release's Windows live GUI rerun remains
  pending an available authenticated child.
- Windows owned apps close after 30 minutes without requests. Linux defaults to
  a fixed 30-minute TTL. Mac has no idle-save policy.
- Linux uses llvmpipe software rendering on the tested host. No gaming claim.
- Mac was tested on Apple Silicon, macOS 27.0.1, SDK 27, Swift 6.4; older
  hosts/toolchains are unvalidated. Guest provisioning is explicit.
- The computer-ctrl adapter lacks accessibility, browser DOM/CDP, window
  management, drag/scroll, and audio/video tools.
- Windows/Linux share the user's filesystem/device access. Application-specific
  device routes and singleton IPC need their own checks.

## Next measured work

1. Make lifetimes explicit for long tasks, with visible expiry and a safe policy.
2. Add a read-only viewer that opens/closes without disturbing session identity
   or agent input. Keep takeover a separate explicit action.
3. Run new-name Windows native acceptance when its child desktop is available.
4. Expand computer-ctrl capabilities only with per-platform evidence.

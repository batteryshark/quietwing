# Current status

Updated 2026-10-15. [QuietWing 0.3.0](https://github.com/batteryshark/quietwing/releases/tag/v0.3.0)
is the first experimental MIT-licensed GitHub release. The package, import, and
sole executable are `quietwing`. Computer-ctrl's integration is
[merged](https://github.com/batteryshark/computer-ctrl/pull/1).

## [0.3.1 viewer cleanup patch](https://github.com/batteryshark/quietwing/releases/tag/v0.3.1)

Version 0.3.1 removes the explicit show-window operation from the Windows viewer
observer's cleanup. Stop, worker exit (including idle exit/crash), and attach
rollback preserve the current viewer visibility. A viewer hidden for control stays
hidden; the external provider and native login are not stopped or reconnected.
Explicitly visible viewers remain visible. No cleanup operation reveals a viewer.

The portable regression failed against 0.3.0's hide-plus-show calls and passes with
the cleanup show removed. Windows CI additionally compiles the actual worker with
only its viewer OS calls faked, then executes 12 stop/crash/rollback cases across
visible/hidden and hide/observe modes. A negative control reinserts the old show operation and must fail. These tests
do not use a real desktop.

**Fresh Windows native and Codex/OpenCode acceptance was not run for 0.3.1.** The
operator kept the Windows machine reserved for another workload and requested
static validation. No Windows connection, install, input, capture, sign-in or
provider operation is performed for this patch. The 0.3.0 live evidence below is
historical and does not prove the changed cleanup behavior on a native desktop.
Mac/Linux native implementations are unchanged. Existing 0.3.0 attachments still
use their old cleanup code until finished and replaced during a safe work window.

## 0.3.0 release validation

| Check | Result |
| --- | --- |
| Hosted QuietWing CI | Linux, macOS, Windows; Python 3.11 and 3.14 portable checks, clean wheel install, source rebuild/distribution audit passed. See [CI](https://github.com/batteryshark/quietwing/actions/workflows/ci.yml). |
| Hosted computer-ctrl CI | Linux, macOS, Windows; Python 3.11 and 3.13 regression and package jobs passed. 141 regression tests per run. |
| Portable companion checks on Mac | 34 passed: 15 dispatcher/distribution, 11 Windows fake transport, 8 Mac fake generation cases. |
| Native source comparison | 17 runtime/native source files identical to the historically validated 0.2 backend. |
| Mac, updated cctl and installed QuietWing | Saved guest resumed, fresh capture visually inspected, provider identity verified, guest saved/stopped again. Host pointer/focus unchanged, no audio devices; no input sent in this smoke check. |
| Linux, installed QuietWing | Two separate SSH stages passed ordinary Mousepad/Xmessage input, exact Unicode/metacharacter saved text, native click, fresh capture, private audio, generation refusal, reconnect, TTL expiry, and owned cleanup. 167 unchanged host metadata samples; only the original X display remained. |
| Windows, official 0.3 wheel and private consumer environment, follow-up on 2026-10-15 | Installed CLI passed native text/click/capture, ordinary cmd application, runtime silent-output checks, stale refusal and cleanup. Two SSH connections reused the same controller/generation. Reattachment rejected old generations, including direct worker stop. |
| Windows, fresh actual Codex and OpenCode workflows | Both saved exact Unicode in an ordinary PowerShell ISE document through isolated MCP calls. Independent file/event/session/capture/cleanup checks passed. The same authenticated child/provider survived all tests; 1,849 parent metadata samples showed unchanged pointer/focus and a hidden, non-minimized connected viewer during control. |

Windows live GUI acceptance was missing at initial publication; earlier wording
that the Windows checks were finished overstated that coverage. The authorized
follow-up above now exercises the **published 0.3.0 wheel**. No runtime sources or
release assets were replaced. Private captures and failed harness-startup attempts
are retained locally, excluded from Git. These tests establish ordinary-app
behavior under the measured conditions, not game/GPU or arbitrary startup-path
noninterference.

A parallel main-desktop workload stopped at 14:37 EDT after its capture guard
reported an obstruction without recording the blocking window. Its visible
application list matched its baseline. The QuietWing installation checks started
around 14:40; the earlier overlapping QuietWing operation was a read-only SSH
inventory. The shared host driver had already logged accessibility timeouts.
Replaying the headless QuietWing checks while the workload ran produced no new
visible windows or foreground changes across 284 metadata samples. The original
obstruction remains unidentified; no fix for that historical event is claimed.
With explicit authorization, the workload's launcher was made consistently headless,
and its unchanged obstruction guard now reports blocking process/window metadata.
Command-generation checks and Windows diagnostic compilation passed. This is a
separate runner correction, not identification of the historical obstruction.
This evidence does not establish noninterference for every setup or diagnostic path.

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
  no automatic sign-in/reconnect. From 0.3.1, cleanup preserves current viewer
  visibility; a hidden viewer stays hidden. Old running workers retain old behavior.
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
3. Measure nonintrusive viewer/setup behavior and game rendering separately.
4. Expand computer-ctrl capabilities only with per-platform evidence.

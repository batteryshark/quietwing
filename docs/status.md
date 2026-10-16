# Current status

Updated 2026-10-15. [QuietWing 0.3.0](https://github.com/batteryshark/quietwing/releases/tag/v0.3.0)
is the first experimental MIT-licensed GitHub release. The package, import, and
sole executable are `quietwing`. Computer-ctrl's integration is
[merged](https://github.com/batteryshark/computer-ctrl/pull/1).

## 0.4.0.dev1: Linux viewing on Mac over SSH

The same read-only Mac window can display an existing isolated Linux desktop.
Use `view --host user@linux-machine --id NAME` and the Linux helper's executable
and state-root options as needed. Matching development builds are required;
see the [viewer guide](viewer.md). Windows remains unchanged and unsupported by
this preview; a native Linux viewer window is not implemented.

- Installed-wheel acceptance on Debian 13: actual Codex and OpenCode each saved
  exact Unicode in ordinary Mousepad documents through six successful isolated
  MCP calls. Saved files, tool events, generation and final screenshots were
  independently checked. Across 183 Mac viewer-state samples, the panel stayed
  nonkey/nonmain and never became foreground; frames advanced 70->101 and
  101->114 during the two workflows. No human Linux desktop capture or input.
- Live duplicate open, stale open/close, closing without stopping/extending the
  Linux session, an eight-second busy action lock, explicit stop/replacement and
  five-second TTL cleanup passed. Busy capture cleared and recovered on the same
  generation. A fixed helper returning exit 255 cleared its image and required
  explicit reopen; this simulated helper/SSH-style failure is not a tested
  physical network outage. No automatic session creation or rebind occurred.
- Native Mac panel regression passed 12 local input dispatches, nonactivation,
  unchanged foreground/cursor during its controlled interval, invalid-image
  clearing, waiting/recovery and ended/close cleanup. It displayed a real Linux
  capture for visual QA. Portable checks: 70 passed, one Windows-only fake-OS
  case skipped locally. Wheel/source audit, independent source rebuild and fresh
  install passed; all 34 bundled runtime resources matched reviewed source.
- Extra ordinary-app Mac VM reruns stopped at black captures before typing;
  waking only the guest revealed its lock screen. Those two attempts are not
  acceptance passes. Fresh Mac VM ordinary-app reruns are deferred until the
  guest is unlocked; no login/power settings or credentials were changed. The
  older 0.4.0.dev0 Mac VM evidence below remains historical. VM native source
  is unchanged; the current native panel and Linux workflows passed above.
- Automatic approval review rejected a proposed Linux main-desktop pointer/focus
  monitor; it was omitted. No such host-activity monitoring or unchanged Linux
  host cursor/focus claim is made for this run. Private evidence stays ignored
  under evidence/linux-viewer-2026-10-15. Personal Windows was not contacted.

## 0.4 development: Mac read-only viewer

The installed 0.4.0.dev0 wheel passed live Mac viewer acceptance on 2026-10-15.
`quietwing view --id NAME` displays guest pixels without taking keyboard focus
or forwarding input. `--close` closes only the preview. Windows/Linux viewing
remain unsupported. See the [viewer guide](viewer.md).

- Native AppKit fixture: image display, 12 locally dispatched input events,
  refusal to become key/main, unchanged foreground/cursor, stale-image clearing,
  and frame removal at close passed. This fixture posts no global input.
- Live guest: duplicate open reused the same window; stale open/close refused;
  close retained the running owner and input timestamp. Explicit save/resume
  retained the guest login, cleared the old preview, refused automatic rebind,
  and allowed an explicitly reopened preview on the new generation.
- Actual Codex and OpenCode each saved exact Unicode through seven isolated MCP
  calls while preview frames advanced. Files, tool events, final screenshots and
  pinned generation were checked independently. Across 151 metadata samples, the
  preview/VM stayed nonkey/nonmain, the VM stayed offscreen, and neither became
  foreground or posted host input. The human continued moving the pointer and
  switching applications; unchanged pointer/focus is claimed only for the native
  fixture's controlled interval, not the whole agent workflow.
- Local portable checks: 51 passed, one Windows-only simulated case skipped.
  Clean wheel/source audit, independent source rebuild and fresh installed
  command passed; all 33 bundled runtime resources matched reviewed source.
  Hosted CI additionally compiles the installed viewer on Mac without launching it.
- Dedicated acceptance controller and harness/server processes were removed.
  The Mac guest and preview were retained for inspection. No personal Windows
  connection, install, capture, input or settings change was performed.

## [0.3.1 viewer cleanup patch](https://github.com/batteryshark/quietwing/releases/tag/v0.3.1)

[Exact-tag CI](https://github.com/batteryshark/quietwing/actions/runs/38805831649)
and the [release workflow](https://github.com/batteryshark/quietwing/actions/runs/38805847684)
passed. Official archives were checksum-verified, fresh installed, and rebuilt
from the source download with all 29 runtime resources matching.

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

- The 0.4 development build has a read-only Mac window for Mac VMs and Linux over
  SSH; see [viewer](viewer.md).
  No cross-platform viewer, takeover control, or agent pause/resume panel.
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
2. Add viewer windows on Linux itself and Windows with separate native acceptance.
   Keep takeover a separate explicit action.
3. Measure nonintrusive viewer/setup behavior and game rendering separately.
4. Expand computer-ctrl capabilities only with per-platform evidence.

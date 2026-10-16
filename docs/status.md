# Current status

Updated 2026-10-16. [QuietWing 0.3.0](https://github.com/batteryshark/quietwing/releases/tag/v0.3.0)
is the first experimental MIT-licensed GitHub release. The package, import, and
sole executable are `quietwing`. Computer-ctrl's integration is
[merged](https://github.com/batteryshark/computer-ctrl/pull/1).

## Development SSH preview follow mode — 2026-10-16

0.4.2.dev0 adds opt-in Mac `view --host HOST --follow` for the same verified
Linux/Windows target. The image-only window waits across missing attachments,
transport loss and generation replacement. It issues only status and pinned
frames; session acquisition, authentication and control bindings remain explicit.
Default pinned and local Mac VM previews retain their existing behavior.

Portable checks: 120 tests, 118 pass/two Windows-native skips on Mac. The real
Mac native UI fixture passed synthetic rendering, local event consumption,
nonkey/nonmain behavior, unchanged foreground/cursor and stale-image clearing.
The installed candidate's real panel also survived controlled Linux/Windows
attachment and transport replacement in the same window, clearing pixels while
waiting and stopping requests on close. These lifecycle/transport replies are
local synthetic fixtures, not native Windows or Linux reconnect tests.
Fresh wheel/source audits and independent source rebuild/install passed.
A separate real Windows peek uses only existing read-only status/frame operations;
the Mac preview is left open in follow mode. No native RDP reconnect, worker
reattachment, remote installation or session/settings change was exercised while
DreamStudio works. Private receipts: evidence/viewer-follow-2026-10-16.

## 0.4.1 release validation — 2026-10-16

[Published experimental v0.4.1](https://github.com/batteryshark/quietwing/releases/tag/v0.4.1)
at `a0f5d13` promotes the accepted live-provider fix from `9652314`. The executable
backend resources are unchanged from the development build that passed native
Windows and actual Codex/OpenCode acceptance below. Release work is local and
on GitHub; the occupied Windows machine is not accessed for release validation
or installation. No fresh native Windows acceptance is claimed for the version
promotion. Native RDP disconnect/relogin remains outside the tested scope.

The release includes the Windows readiness fix and retains the existing native
session, generation, secure-desktop, audio and hidden-viewer guards. The ParaDesk
writer bug remains upstream; QuietWing's live authority is its verified IPC
response. Existing loaded workers get the new guard on their next explicit attach.
[Release-commit CI](https://github.com/batteryshark/quietwing/actions/runs/38928179239)
and [exact-tag CI](https://github.com/batteryshark/quietwing/actions/runs/38928182076)
passed all seven jobs each; the [draft build](https://github.com/batteryshark/quietwing/actions/runs/38928182600)
passed. Reviewed draft/public checksums and anonymous downloads, independent source
rebuild, and fresh wheel/source installs passed. All 35 runtime resources match
the tag; all 23 executable backend resources match the accepted fix. No old tag
or asset was replaced. Receipts: evidence/release-0.4.1.

## Development Windows live-provider fix — 2026-10-16

0.4.1.dev0 queries ParaDesk's existing local status pipe instead of trusting cached
child/connection metadata. The actual pipe server PID/birth is verified; readiness
and every bound action fail closed on missing/unavailable status or changed live
identity. Native WTS, generation, secure-desktop, audio and hidden-viewer checks
remain. No provider launch/reconnect, state-file repair or settings toggle.
The upstream ParaDesk file-writer race itself is unchanged.

The deterministic stale-cache test failed with the original authentication error
before the fix and passes afterward. Native desktop-free pipe tests cover login
registration timing, repeated status connections, disconnect/new connection and
child replacement, wrong server PID/birth, malformed/oversized replies and timeout.
Viewer stop/crash/rollback regression also passes. Portable checks ran 100 tests
(98 passed; two Windows-native tests skipped on Mac and passed on Windows).
Fresh wheel/source installs and independent rebuild passed; all 35 runtime
resources match reviewed source and the accepted executable resources.

An installed native red/green test used a separate stale-cache fixture pointing
to the existing provider: unchanged 0.4.0 refused it; the candidate passed doctor,
native WTS attach, Unicode input and capture. A fresh SSH connection retained the
same worker/generation/child; eight independent live-status connections, exact
input/capture, stale-generation refusal and owned stop passed. The real provider
state/settings and stale fixture bytes stayed unchanged. All 192 parent samples
kept cursor/foreground unchanged and the viewer hidden/unminimized, including stop.

Actual Codex and OpenCode normal-MCP editor workflows each passed seven tools,
independently checked exact Unicode/files, native identities and fresh captures.
All 1,568 parent observations kept the viewer hidden/unminimized. The first
OpenCode attempt correctly refused a stale controller generation; explicit rebind
preceded the successful new-generation rerun. Earlier fixture runner failures
(transient file replacement and select-all expectations) are retained and are not
passes. Owned editors, workers, observers, tasks and private controller were cleaned;
the original provider, authenticated child and other worker were retained.

Live reconnect coverage is SSH/status-pipe transport against a retained native
connection. Provider disconnect/new connection/child replacement were tested in
headless fixtures. An RDP disconnect/relogin was not forced because it can require
an interactive sign-in. No main-desktop capture/input, games, system-policy change
or new authentication was used.
Official 0.4.0 assets/tag remain unchanged. The tested development artifact was
not a published release; its fix is promoted in 0.4.1 above. Private evidence: evidence/windows-live-provider-2026-10-16.

## 0.4.0 release validation

[Published experimental v0.4.0](https://github.com/batteryshark/quietwing/releases/tag/v0.4.0)
at release commit `33c6a90`. [Exact-tag CI](https://github.com/batteryshark/quietwing/actions/runs/38834328744)
passed all seven jobs, including both fresh Mac viewer compilations; the
[draft build](https://github.com/batteryshark/quietwing/actions/runs/38834328177)
also passed. Public wheel/source downloads and SHA256SUMS were verified without
authentication, independently rebuilt and fresh installed. All 34 runtime
resources match reviewed source and the live-tested Mac candidate. No release
assets or historical tags were replaced.

The installed 0.4.0 release candidate passed fresh Mac acceptance on 2026-10-15.
Codex and OpenCode each saved exact Unicode in TextEdit through six verified
isolated MCP calls. Files, tool events, pinned generation and final images were
checked independently. Across 220 preview observations, the window stayed visible,
nonkey/nonmain and never became foreground; frames advanced 27->60 and 69->88.
The VM stayed offscreen and posted no host input; human activity remained allowed.

Duplicate/stale open-close, closing without changing owner/input timestamp,
save/stop image clearing, guest login/document retention after resume, stale
capture refusal, and explicit close/reopen on the new generation all passed.
The native AppKit fixture passed all 12 local input handlers, controlled unchanged
foreground/cursor, invalid/waiting/ended frame clearing and close cleanup. Only
owned guest input was used; the user explicitly authorized guest credential use
for the one-time unlock. No login/power/credential policy or host setting changed.

The native and transport executable sources are byte-identical to accepted
0.4.0.dev2. Windows native lifecycle and both actual harnesses, plus both Linux
shared-transport harnesses, passed on that development build as detailed below.
At initial publication those remote workflows had not yet been rerun against
the version-only 0.4.0 package; initial publication did not access Windows. The
official-package follow-up below supersedes that deferral. The Mac checks close
the development guest-lock deferrals; those earlier failures remain historical.

Local portable checks: 93 passed and one Windows-only simulated case skipped.
Clean release archives passed auditing, independent source rebuild and fresh
wheel/source installs; all 34 runtime resources match the live-tested candidate
and reviewed source. Exact-tag hosted CI and reviewed public asset checks passed, as linked above. Private evidence stays under evidence/release-0.4.0.

## Official 0.4.0 Windows/Linux follow-up — 2026-10-15

The unchanged public wheel is installed in dedicated Windows and Linux
QuietWing environments. Its checksum and all 34 installed runtime resources
match the official release. Native Windows input/capture/stop/crash/rollback and
stale checks passed against this installed package. This follow-up also closes
the normal-MCP editor deferral recorded in the earlier rollout notes.

After an operator reboot and local ParaDesk sign-in, actual Windows Codex and
OpenCode passed through the normal persistent computer-ctrl MCP controller:
seven and thirteen verified tools, exact saved Unicode, checked final images
and verified native editor/session identities. Across 594 Mac preview samples
the panel stayed nonactivating. All 1,983 Windows parent observations kept
ParaDesk hidden and unminimized. Default CLI rebind, windowless controller,
stop/stale-frame/generation refusal and cleanup passed with 88 additional
hidden-parent samples. The same post-reboot native child/login stayed connected;
owned test editors/workers/controller/tasks were removed.

Fresh Linux Codex and OpenCode normal-MCP Mousepad workflows passed six verified
tools each, exact saved Unicode, the same persistent controller and checked final
captures. Owned editor identities, private X display and private PulseAudio
routing were verified; all 261 Mac preview samples stayed nonactivating. Owned
session/editors/controller were cleaned. Default CLI automatic acquisition,
stop/restart, stale refusal and controller cleanup passed separately. No human
Linux desktop capture, input or pointer/focus monitor was used. Earlier Linux
agent evidence used direct MCP; the previous wording calling those runs
persistent was incorrect. The fresh runs above close that gap.

Normal Windows MCP bootstrap had exposed a separate
[computer-ctrl logging/state-directory ACL bug, now fixed](https://github.com/batteryshark/computer-ctrl/commit/ce9671c).
Its native desktop-free regression failed before and passed after the fix;
141 portable tests and hosted CI passed. The consumer reuses its existing
private-directory factory for new paths; it changes no existing ACL or system
policy. Dedicated consumers use the fix. QuietWing runtime code/assets are unchanged.

One extra Linux default-MCP attempt failed before tools with `AF_UNIX path too
long`: its socket path was 112 bytes. Shortening only the private test cache path
to 89 bytes passed; keep Unix cache paths short because this OS limit remains.
Windows capture after an external helper stop currently returns `ADAPTER_ERROR`
with a missing-binding detail; explicit cctl start/rebind passed. Explicit cctl
stop then refuses input as `session_stopped`. Neither error targets the host.
The first lifecycle assertion expected a different missing-binding code; its
narrow expectation was corrected and all lifecycle checks were rerun successfully.
Failed startup/SSH/expectation attempts remain recorded, not counted as GUI passes.

Owned acceptance preview panels/brokers were closed; the authenticated Windows
child is retained. No system settings, credential/firewall/RDP policy, global cctl,
release tag or asset changes were made in this follow-up. No gaming/GPU or
universal noninterference claim follows from these checks. Private evidence is
retained under evidence/official-0.4.0-rollout-2026-10-15.

## ParaDesk readiness snapshot follow-up — 2026-10-16

A live ParaDesk 1.1 reconnect left its saved snapshot connected with no child,
while fresh provider IPC status and a native WTS console probe agreed on the
real authenticated child. Original doctor failed; a provider-owned refresh
reapplying its existing view-only value corrected the snapshot. Settings bytes,
provider/connection identity and native login were unchanged.

Public doctor, native attach/status, fresh child-only capture and owned stop then
passed with the original guards. The viewer stayed hidden after cleanup; no
input, apps/games, reconnect or system policies changed. This was an operational
recovery on the unchanged official 0.4.0 runtime, not a permanent race fix or a
new two-harness acceptance claim. See the
[bounded operator recovery](../windows/README.md#connected-provider-with-a-stale-child-snapshot).
Private evidence: evidence/windows-provider-readiness-2026-10-16.

## Development acceptance history

The following sections identify their tested development builds and historical
deferrals; the 0.4.0 results above supersede the Mac guest-lock deferrals.

## 0.4.0.dev2: Windows viewing on Mac over SSH

The optional Mac preview can now show an already attached Windows child with
`view --host user@windows-machine --remote-platform windows --id NAME`. Matching
0.4.0.dev2 builds are installed in dedicated Mac/Windows/Linux environments.
The existing ParaDesk child stayed signed in and hidden; no reconnect, login,
firewall, credential policy, RDP port, service or global computer-ctrl change.
See the [viewer guide](viewer.md#windows-over-ssh).

- Exact installed wheel passed Windows native input/capture, normal stop, owned
  worker crash, attach rollback and stale-generation checks. Cleanup kept
  ParaDesk hidden and retained the same authenticated native child throughout.
- Actual Codex and OpenCode each saved exact Unicode through seven verified
  isolated MCP calls. Saved files, native editor/worker identity, generation and
  final captures were independently checked. Across 282 Mac preview samples,
  the panel stayed nonkey/nonmain and never became foreground; frames advanced
  18->54 and 1->19. All 1,203 Windows parent samples kept ParaDesk hidden and
  unminimized. Human cursor/focus activity was allowed, not required to stay fixed.
- Duplicate/stale open-close, closing without stopping the worker, explicit
  reopen and old-helper failure passed. Stop cleared the old image; replacement
  was refused until explicit close/reopen. An old helper ended/cleared its own
  separate preview without fallback. No physical network outage, Windows lock or
  provider disconnect was induced during this follow-up.
- Later, the retained preview ended/cleared after 301 frames with an empty SSH
  failure (`remote_unavailable`). A new read-only status succeeded; the same
  Windows worker/provider/child were still healthy. Explicit preview close/reopen
  on that same generation restored frames. The transient failure's origin was
  not established; manual reopen after SSH failure is the current behavior.
- Six frames did not keep a worker copy alive with its timeout shortened to five
  seconds. It exited naturally in 6.89 s, left ParaDesk hidden and cleaned up.
  Only that private copy's duration changed; installed 30-minute timeout was not
  changed or waited out. Preview frames do not reset that inactivity timer.
- Shared-transport Linux regression passed actual Codex/OpenCode: six verified
  tools and exact saved Unicode each; 209 nonactivating Mac preview samples,
  frames 55->89 and 147->163, same private Linux generation/TTL. No Linux human
  desktop capture, input or pointer/focus monitor. Mac VM ordinary-app reruns
  remain deferred until its guest is unlocked; VM native source is unchanged.
- Current native Mac panel passed all 12 local input handlers, nonactivation,
  controlled unchanged foreground/cursor, invalid/waiting/ended image clearing
  and close cleanup, with synthetic pixels and a real isolated Windows frame.
- Portable checks: 93 passed, one Windows-only fake-OS case skipped locally.
  Clean archives, source rebuild/fresh install and all 34 runtime resources
  matched the reviewed source. Windows hosted CI runs the fake-OS C# cases.
- Only the new Windows demo attachment/editor and normal private Linux session
  are retained; transient acceptance workers/tasks and dedicated direct MCP
  processes ended. Native login remains alive. Raw evidence is ignored under
  evidence/windows-viewer-2026-10-15. Published 0.3.1 assets are unchanged.

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

The later 2026-10-15 live follow-up passed against the unchanged official 0.3.1
wheel (SHA-256 `468e0e45947a59a7b7055aa89ec10bf60f80c4be62a8de3cdb830ca390d6a5a0`).
Native installed input/capture, normal stop, owned-worker crash, attach rollback,
stale-generation refusal and actual Codex/OpenCode ordinary ISE workflows passed.
The harnesses used seven and eleven successful isolated tool calls respectively,
with independently verified exact Unicode and final images. All 1,708 parent
samples kept ParaDesk hidden/unminimized; cleanup preserved the same signed-in
child. This closes the native-testing deferral recorded at publication below.

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

- QuietWing 0.4.0 has a read-only Mac window for Mac VMs and Linux/Windows over
  SSH; see [viewer](viewer.md).
  No viewer window running on Linux/Windows, takeover control, or agent pause/resume panel.
- Windows requires an authenticated, connected, non-minimized ParaDesk viewer;
  no automatic sign-in/reconnect. From 0.3.1, cleanup preserves current viewer
  visibility; a hidden viewer stays hidden. Old running workers retain old behavior.
- Windows owned apps close after 30 minutes without activity other than preview frames. Linux defaults to
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

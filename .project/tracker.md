# QuietWing tracker

Updated: 2026-10-15

## 0.4.0 release (2026-10-15, publication preparation)

- User authorized remaining Mac checks, CI and publication. After automatic review
  required specific guest-credential approval, user explicitly authorized private
  retrieval/unlock; one guest-only submission succeeded, without secret output.
- Installed 0.4.0 candidate passed actual Codex/OpenCode TextEdit workflows: six
  verified isolated tools each, exact saved Unicode and final images, 220 preview
  samples (27->60 and 69->88 frames), nonactivating panel/offscreen VM/no host input.
- Native panel passed 12 local handlers, controlled focus/cursor and clearing.
  Duplicate/stale open-close, retained owner/input timestamp, save/stop clearing,
  resume retaining guest login/documents, stale capture and explicit preview reopen
  passed. This closes the earlier Mac guest-lock acceptance deferrals.
- Native/transport executable resources match accepted dev2 byte-for-byte; only
  version constants/guides differ. Windows/Linux dev2 evidence below is retained;
  no fresh remote native run or Windows access claimed for this version-only release.
- Portable 93 passed/one Windows-only simulated skip. Clean archives, independent
  source rebuild/fresh wheel/source installs passed; all 34 resources match source
  and the live-tested candidate. Exact-tag CI/draft asset review remain release gates.
- Private evidence: evidence/release-0.4.0. Same signed-in guest and read-only
  preview retained; no host settings, guest disks/identity or policy changes.

## Windows read-only viewer and 0.3.1 follow-up (0.4.0.dev2, 2026-10-15)

- User freed Windows and explicitly chose preview plus deferred checks. Existing
  child was connected/authenticated; no sign-in, reconnect, settings/policy/RDP/
  firewall/service change or global cctl modification. Work uses separate venvs.
- Official unchanged 0.3.1 wheel passed native installed input/capture, normal
  stop/crash/rollback, stale refusal and actual Codex/OpenCode ISE workflows:
  seven/eleven verified tools, exact saved Unicode and final images, 1,708 parent
  samples with ParaDesk hidden. Same provider/login retained; test workers removed.
- Development Windows `view --frame --expect-generation` returns a bounded PNG
  only through the bound child's guard; no standalone PNG or native viewer UI.
  Mac `--remote-platform windows` uses literal encoded PowerShell over existing
  SSH, optional existing-key selection, shared bounded transport and image panel.
  Linux target identity and behavior retained; no input forwarding or auto-acquire.
- Exact installed dev2 wheel passed native input/capture/stop/crash/rollback and
  two actual Windows harnesses: seven tools each, exact files/images/generation,
  282 nonactivating preview samples (18->54, 1->19 frames); 1,203 parent samples
  kept ParaDesk hidden. Human pointer/focus activity allowed. Duplicate/stale/
  close-retention/replacement/old-helper failure passed, with no automatic rebind.
- A private worker copy with five-second idle threshold exited naturally despite
  six frames (6.89 s); installed 30-minute timeout unchanged. Native panel fixture
  passed 12 local event handlers, focus/clearing/close and real Windows pixels.
- Shared Linux transport passed both actual harnesses: six tools each, exact
  Unicode, 209 nonactivating preview samples, same generation/TTL. No Linux host
  monitor. Mac VM ordinary-app reruns still deferred while guest idle-locked;
  native VM source unchanged. No lock/disconnect/physical outage induced on Windows.
- Portable 93 passed/one Windows-only simulated case skipped; clean wheel/source,
  rebuild/fresh install and all 34 runtime resources matched. PR #3:
  https://github.com/batteryshark/quietwing/pull/3 merged as 66f444c after explicit
  user authorization. Tested code 1bc2107; approved review head 9364dfd. Main now
  provides development 0.4.0.dev2. Default published release remains 0.3.1;
  its notes now include the completed native follow-up, with tag/assets unchanged.
- Late preview SSH failure after 301 frames cleared/ended as designed; origin
  unestablished. Read-only status confirmed the same healthy worker/provider/child;
  explicit Mac preview close/reopen restored frames without native reconnect.
  Final review-head PR/push CI (38831834832/38831829718) and consumer CI
  38831468234 passed all seven jobs each, including both fresh Mac compilations.
  Post-merge main CI evidence is retained privately with the acceptance evidence.
- Private evidence: evidence/windows-viewer-2026-10-15. Only Windows demo worker/
  saved editor and preview retained; same native child/login. Dedicated direct
  MCPs ended, other test bindings/tasks removed; Linux demo/preview retained.

## Linux read-only viewer over SSH (0.4.0.dev1, 2026-10-15)

- PR #2 merged as 6586ff8 after explicit user authorization:
  https://github.com/batteryshark/quietwing/pull/2. Tested runtime head 52063ff;
  final review head 07094c8 passed all seven PR CI jobs (38827975171), including
  fresh Mac viewer compilation; its push CI also passed (38827968121).
  Published 0.3.1 remains unchanged; main provides development 0.4.0.dev1.
- User chose a Mac window for the Linux desktop over existing SSH. Windows is
  reserved for DreamStudio and was not contacted. No host settings, credential
  policy, listener or global installation changed; tests use private venvs.
- `view --host HOST --id NAME [--remote-command PATH] [--remote-state-root PATH]`
  reuses the image-only Mac panel. Linux `view --frame --expect-generation TOKEN`
  verifies the private display/PID identities under existing lifetime locks and
  returns one bounded PNG in JSON; no remote image file. Mac checks generation,
  dimensions, SHA256 and provenance. SSH is noninteractive with no forwarding or
  persistent master. Endpoint-specific state cannot collide with Mac VM viewers.
- Busy capture clears/waits and retries only the pinned generation. Stop/expiry,
  replacement or helper/SSH error clear/end refresh; explicit reopen required.
  Closing does not stop work or refresh Linux TTL. Strengthened private path checks.
- Installed wheel passed actual Codex/OpenCode Linux Mousepad workflows: six
  verified isolated calls each, exact Unicode, final images and 183 viewer-state
  samples, frames 70->101 and 101->114. Mac window never activated/keyed.
- Live duplicate/stale open-close, session retention, eight-second busy lock,
  simulated helper exit255/reopen, generation replacement and TTL cleanup passed.
  Native panel passed all 12 local events, controlled focus/cursor invariants,
  invalid image, waiting/recovery, end/close and real Linux pixel rendering.
- Portable: 70 passed, one Windows-only simulated case skipped. Clean wheel/source
  audit, independent rebuild/fresh install, all 34 bundled resources match. Own
  Mac and dedicated Linux venv use tested 0.4.0.dev1 wheel; official assets unchanged.
- Extra Mac VM Codex/OpenCode attempts encountered black frames and performed no
  click/type/save. Guest-only Escape revealed idle lock screen. Not counted as
  passes; ordinary-app rerun deferred until unlocked. Native VM source unchanged;
  no credential read or login/power setting change. Mac guest remains running.
- Automatic review rejected a proposed Linux human-desktop metadata monitor;
  omitted, without alternative host observation. No unchanged Linux host-pointer/
  focus claim. Private evidence: evidence/linux-viewer-2026-10-15. Dedicated MCP
  sessions ended; test TTL session cleaned; current Linux demo and preview retained.

## Mac read-only viewer (0.4 development, 2026-10-15)

- User requested a Mac-first read-only peek; personal Windows is reserved for
  DreamStudio and was not contacted. No host settings or credentials changed.
- `view --id NAME [--status | --close]` uses a separate nonactivating image panel
  plus a generation/PID-pinned capture broker. No VM socket/input code in the
  window; broker uses existing owned capture. No automatic resume/rebind, audio,
  host capture or listener. `build --viewer` compiles only the preview, safe with
  a running VM. Existing VMHost/capture and Windows/Linux native sources unchanged.
- Native fixture passed image display, all 12 local event handlers, nonkey/main,
  controlled unchanged foreground/cursor, stale-image clear and close cleanup.
  Live duplicate/stale open-close, unchanged guest input timestamp, saved guest
  retention and explicit generation transition passed. Preview clears on stop.
- Final installed wheel passed actual Codex + OpenCode editor workflows: seven
  verified isolated MCP events each, exact Unicode readback, final images, 151
  viewer/owner metadata samples; preview frames 33->86 and 87->105. Neither agent
  window became foreground or posted host input; human activity remained allowed.
- Portable: 51 passed, one Windows-only simulated case skipped. Wheel/source audit,
  independent source rebuild and fresh installed entry points passed; all 33
  bundled resources match source/rebuild. Native UI fixture retained in tests;
  hosted Mac CI now compiles the installed viewer without launch.
- PR #1 merged as c79b8b5 after the user explicitly authorized the merge:
  https://github.com/batteryshark/quietwing/pull/1. Final feature head 7a61c69
  passed all seven PR CI jobs (38810403518), including fresh Mac compilation;
  its push CI also passed (38810395981). Published 0.3.1 remains the default
  release; this viewer is available on main as development 0.4.0.dev0.
- Own private venv uses development 0.4.0.dev0; official 0.3.1 assets unchanged.
  Private evidence: evidence/mac-viewer-2026-10-15. Acceptance controller and
  harness/server processes removed; authenticated Mac guest and preview retained.

## 0.3.1 viewer cleanup (2026-10-15, released)

- User requested quiet stop with the child signed in, then explicitly reserved
  the Windows machine for another workload: static verification only, no Windows
  host access/install/input/capture or native/two-harness rerun for this patch.
- Root cause is the explicit ShowWindowAsync(hwnd, 4) in the viewer finally path.
  Portable regression ran red on 0.3.0 (hide plus show), green after removal.
  Stop, worker exit and attach rollback now preserve current visibility; hidden
  viewers remain hidden. Observer result reports restored=false. Provider/session
  lifecycle and Mac/Linux native code unchanged. Historical popup still unattributed.
- Added 12 actual C# cleanup-path cases with viewer OS calls faked for Windows CI;
  no real desktop/provider. Updated native acceptance assertions for later use.
- Existing live 0.3.0 attachments cannot be rewritten by a package upgrade; finish
  them during a safe work window, retain the provider/login, then use new workers.
- Local portable checks: 35 passed, one Windows-only simulated test skipped.
  Clean wheel/source build, archive audit, fresh installed entry points and source
  rebuild passed; all 29 runtime resources match. Exact-tag CI 38805831649 and
  draft workflow 38805847684 passed at 3678a5a. Both Windows matrices passed the
  12 fake-OS C# cases and failing old-behavior control.
- Published experimental v0.3.1: https://github.com/batteryshark/quietwing/releases/tag/v0.3.1.
  Official wheel/source/SHA256SUMS independently audited, installed and source
  rebuilt; reviewed runtime sources match. Own Mac venv updated to 0.3.1. Personal
  Windows provider/login left untouched; fix is not installed on that machine.

## Windows follow-up (2026-10-15, acceptance complete)

- Initial completion wording overstated Windows coverage. Fresh acceptance now
  passes against the published 0.3 wheel (SHA256 852ea015…3675e4), with no runtime
  or asset replacement: native CLI text/click/capture, ordinary app, silent output
  routes, stale-generation refusal, reattachment, two-SSH reconnect, owned cleanup.
- Actual Codex and OpenCode saved exact Unicode in separate ordinary ISE documents.
  Independently verified files, native tool events, child identity, fresh captures
  and cleanup. 1,849 parent samples: pointer/focus unchanged, connected viewer
  hidden and not minimized. Same provider/authenticated child retained; all owned
  workers/apps, temporary tasks and the private consumer controller removed.
- User authorized one manual ParaDesk sign-in while the separate main workload
  was paused. No host capture/input, firewall, credential-policy, RDP or service
  changes. Private evidence and unsuccessful harness-startup attempts stay ignored
  under evidence/windows-live-0.3.0-2026-10-15.
- Separate workload runner patch applied with permission: all shell helpers use
  its existing headless launcher, obstruction guard retains refusal and adds
  blocker identity. Command checks/Windows compile passed; synced copy hash matches.
  Lead notified of completion and PC release. Historical 14:37 occluder remains
  unknown: install checks began later; headless replay had 284 stable samples.
- Fixed acceptance-runner readiness: required Codex MCP startup now waits up to
  60 s, avoiding the optional one-second catalog grace. Private MCP pywin32 missing
  dependency fixed only in the test environment. Successful runs verified afterward.
- Checkout moved to ~/Projects/workstack/quietwing; private venv recreated and Mac
  cctl configuration points directly there. No alias. Saved guest/state/cache kept.
- Historical 0.3.0 visibility behavior: stop restored the viewer and could cover
  another window; 0.3.1 corrects that. Hidden/connected control passed; minimized,
  disconnected and automatic reconnect remain unsupported. No game/GPU claim.

## Release 0.3.0

- Public MIT repository: https://github.com/batteryshark/quietwing. Sole package,
  import, and command: quietwing, no aliases. Native state identities retained.
- Computer-ctrl integration merged in PR #1 (442768ad); hosted CI passed on
  Windows/Mac/Linux with Python 3.11/3.13, 141 tests per run and package build.
- QuietWing hosted CI passed on Windows/Mac/Linux with Python 3.11/3.14 plus
  distribution audit. Windows install-probe scripts-directory assumption fixed.
- Published experimental v0.3.0: https://github.com/batteryshark/quietwing/releases/tag/v0.3.0.
  Tag 8d22d1a; exact-tag CI 38788369705 and draft workflow 38788370243 passed.
  Official wheel/source checksums, fresh installs, source rebuild, and all 29
  runtime resources independently verified. Public downloads checked without auth.
- Mac updated integration resume/capture/save passed. Linux fresh installed
  acceptance stages passed native input/Unicode/click/audio, SSH reconnect,
  stale refusal, TTL, and cleanup; 167 stable host samples, original X display only.
- Windows separate release venv passed install/import, native compile without
  launching worker, transport tests, and missing-child refusal. Provider file and
  installed resources unchanged; no main-desktop input/capture/controller changes.
  Existing child remained disconnected after the host became available; fresh
  live GUI acceptance was deferred at publication; the follow-up above now passed.
  Operator reported a window interruption
  during headless validation; final inventory found no release-test process/window,
  and its origin was not established. Existing provider/authentication retained.
- 17 native sources match the historical 0.2 acceptance; actual Codex/OpenCode
  workflows passed then on all three platforms. Preserve that distinction.
- Raw release evidence is ignored under evidence/release-0.3.0; no credentials,
  guest disks/snapshots, machine inventory, or captures enter Git or release assets.

## Next action

Finish reviewed 0.4.0 archive validation and exact-tag CI, then publish the authorized
GitHub release and verify its public assets. Retain the signed-in Mac guest/preview.
Native viewer windows on Linux/Windows and game/GPU validation remain future work.

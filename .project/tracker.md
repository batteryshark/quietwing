# QuietWing tracker

Updated: 2026-10-16

## 0.4.2 release (2026-10-16, published)

- Published experimental MIT https://github.com/batteryshark/quietwing/releases/tag/v0.4.2
  at dd638e1. User-authorized PR #4 merged as 7d49521, #5 as bf3a3f1 and consumer
  PR #2 as 84124c7. The stacked #5 rebase preserved the entire accepted tree;
  seven fresh jobs 38963532399 passed before merge.
- Release-commit CI 38963912167 and exact-tag CI 38964091707 passed all seven jobs;
  draft workflow 38964115932 passed. Consumer merge CI 38963490737 passed seven.
  Local portable: 126 tests, 123 pass/three Windows-native Mac skips. Fresh wheel/
  source audit, anonymous public assets/checksums, clean installs and independent
  rebuild passed. All 37 resources match tag/rebuild; 24 executable backend
  resources match the native-tested dev1 candidate. Prior native/two-harness
  acceptance applies; no fresh Windows native rerun is claimed.
- Public wheel SHA256 24a6f92a3d04f51cdb7bf57b9de4ed3536d9f3110e3c58125d6c7e1ac339b5e3.
  No Windows access, installation, lifecycle/viewer/input/settings change during
  release while DreamStudio tests. Existing dev1 installation/worker work retained;
  no automatic package/controller/worker update, PyPI upload or older-tag change.
- Private receipts: evidence/release-0.4.2. Next: normal isolated use; coordinate
  any future Windows package update with its owner after current work is saved.
  Original-game compatibility remains DreamStudio's separate controls pilot.

## Bounded Windows held keys (0.4.2.dev1, 2026-10-16)

- Public input `--key KEY --hold-ms MS`, integer 1–5000 ms. Physical scan-code
  chord, reverse release, periodic unchanged generation/provider/session/audio
  guards, already-down refusal and explicit KEY_RELEASE_UNCONFIRMED on unsafe
  cleanup. No persistent key-down state, action replay or host fallback.
- `key_hold` capability and ready-file check prevent old workers silently tapping;
  explicit owner-coordinated reattach required. computer-ctrl adds hold_ms,
  repeat=1 and strict release receipts; unsupported direct-host/providers refuse.
- Portable: 126 tests, 123 pass/three Windows-native skips on Mac; all seven
  feature CI jobs 38958683602 passed, including actual C# fake-OS handler cases.
  Consumer 152 tests and initial seven-job CI 38958688203 passed. Fresh packages,
  source rebuild/install and 37 runtime resources match the native-tested wheel.
- Lead-approved 20-minute helper window finished 16:18 EDT. Native 250 ms request
  measured ~274 ms; CLI-client termination during 900 ms still released, same
  worker survived; stale generation refused. Actual Codex/OpenCode normal MCP
  editor workflows passed exact saved Unicode, native ~241/~249 ms for 220 ms
  and release. All 693 parent samples kept pointer/focus and hidden viewer fixed.
- Initial runner path error preceded input and cleaned up; initial OpenCode free
  provider refused before tools, then authenticated OpenAI run passed. Raw
  controller kill returned access denied after partial cleanup; fresh scoped
  inventories confirmed no owned processes/listeners/tasks remain. No fail counted
  as a pass. Guard/capture/input behavior did not fail in the accepted runs.
- Tested wheel installed into the existing Windows QuietWing venv (0.4.1.dev0 →
  0.4.2.dev1); all 37 installed resources match. Provider/login retained, no main
  input/capture, original game/debugger, reconnect, settings or DreamStudio/guard
  edits. Main-desktop cctl install untouched; staged consumer tested separately.
- DreamStudio lead notified ready with fresh-attach syntax and honest timing/
  cleanup limits. Its ordinary-controls pilot/legacy-debugger hold remains its
  gate. No further Windows work planned. Candidate later promoted to 0.4.2 above.
- Reviews: QuietWing PR #5 (stacked on #4), consumer PR #2. Private receipts:
  evidence/held-keys-2026-10-16. PRs merged and promoted to 0.4.2 above; original-game pilot
  remains outside this helper acceptance.

## SSH viewer follow mode (0.4.2.dev0, 2026-10-16)

- Opt-in Mac SSH `view --follow` discovers only an existing verified attachment
  at the same host/executable/state/key/ID. New frames remain generation-pinned;
  availability errors clear pixels and back off 1–30 seconds. Protocol/capture/
  boundary errors end refresh. No remote lifecycle/input calls or relaxed guards.
  Default/local-VM pinned mode and computer-ctrl bindings remain unchanged.
- Portable: 120 tests, 118 pass/two Windows-native skips on Mac. Native Mac
  synthetic UI and installed Linux/Windows transport/lifecycle fixtures pass
  same-window recovery, nonactivation, busy capture and close cancellation.
  Native Windows/RDP and Linux desktop lifecycles were not changed or rerun.
  Fresh package audits, wheel install and independent source rebuild/install pass.
- Installed tested development wheel only in the existing Mac environment;
  replaced only its old Mac preview with follow mode. Real existing Windows
  status/frames display normally, same generation retained, never key/main/frontmost.
  Windows provider/worker/login/install/settings and DreamStudio work untouched.
- Future cross-platform worker pools recorded in docs/future-work.md; evaluate
  a separate scheduler/leases project later, no implementation now. README positions
  QuietWing for existing personal machines; VM pools are the default future scaling
  direction, with RDS only if measured density benefits justify it.
- Actual Codex/OpenCode each ran installed Linux and Windows fixtures: all four
  passed, 387 nonactivating window observations. Initial OpenCode runner expired
  after Linux passed while waiting for inference; resumed only Windows, which
  passed. No assertion failure or native desktop lifecycle claimed.
- Feature CI 38932163143 passed all seven jobs, including fresh Mac viewer builds;
  archive audit now requires the new source tests. No new official release.
  Private receipts: evidence/viewer-follow-2026-10-16. PR #4 merged;
  the feature is included in official 0.4.2 above.

## 0.4.1 release (2026-10-16, published)

- Published experimental MIT https://github.com/batteryshark/quietwing/releases/tag/v0.4.1
  at `a0f5d13`. Executable backend resources are byte-identical to accepted `9652314`;
  its native Windows and two-harness evidence applies. No new native Windows
  acceptance or install; DreamStudio's occupied machine/session was left unchanged.
- Portable: 100 tests (98 passed/two Windows-native skips on Mac; those cases pass
  on Windows CI). Release-commit CI 38928179239 and exact-tag CI 38928182076 passed
  all seven jobs each; draft workflow 38928182600 passed. Reviewed notes/assets,
  authenticated draft and anonymous public checksums/downloads, independent source
  rebuild and fresh wheel/source installs passed. All 35 runtime resources match
  the tagged source; 23 executable resources match the live-tested fix.
- Public wheel SHA256 d2300d8dcc6785c06602c50f7091d6cfac4415634d830b13945e55323c3eb222.
  Prior tags/assets unchanged; no PyPI or automatic machine update. Existing workers
  get the new guard on their next explicit attach after their owned work is saved.
- Separate requested read-only Mac peek found a stopped Windows attachment; no
  session acquisition/restart/input. Preview needs an already live worker.
- Private release receipts: evidence/release-0.4.1. Next: normal isolated use;
  defer the occupied Windows package update until its work is finished.

## Live ParaDesk readiness fix (0.4.1.dev0, 2026-10-16)

- Replaced cached child/connection authority with bounded read-only status IPC for
  readiness and every bound action. Pin actual pipe-server PID/birth and live
  connection at attach; retain native WTS, generation, desktop, audio and viewer
  guards. No launch/reconnect, settings toggle, state-file repair or cached fallback.
  The upstream writer race remains, but cannot serve as QuietWing live authority.
- Deterministic original-auth-error regression ran red/green. Native pipe fixture
  covers login timing, reconnect/replacement/refusal, wrong PID/birth, malformed/
  oversized status and timeout; actual viewer fake-OS cleanup cases passed.
  Portable: 100 tests, 98 pass/two Windows-only skips on Mac; native cases passed
  on Windows. Clean installs/source rebuild and all 35 runtime resources match.
- Installed native old-vs-fixed test with a separate stale-cache fixture passed
  doctor, WTS attach, Unicode input/capture, same worker across SSH reconnect,
  eight status connections, stale-generation refusal and stop. Real provider and
  fixture/settings bytes unchanged; 192 unchanged parent cursor/focus observations.
- Actual normal-MCP Codex/OpenCode each passed seven tools, exact Unicode, native
  identity/images and cleanup. All 1,568 parent samples kept viewer hidden. Initial
  OpenCode stale-controller attempt correctly refused; explicit rebind/new generation
  passed. Fixture runner transient-file/select-all failures retained, not counted.
- Owned test editors/workers/observers/tasks/controller removed; other worker and
  native provider/login retained. No main input/capture, games or system settings.
  Live reconnects cover SSH/status pipes; native RDP reauthentication was not forced.
- Runtime fix is development, not a new public release; 0.4.0 assets/tag unchanged.
  Private receipts (including hosted CI): evidence/windows-live-provider-2026-10-16.
  Next: update consumers through the CLI; existing workers load new code on their
  next explicit attachment. Native reconnect/relogin remains an operator action.

## ParaDesk 1.1 snapshot recovery (2026-10-16)

- Live mismatch reproduced: saved connected/no-child metadata, but fresh provider
  IPC status and native WTS parent probe agreed on the authenticated child.
  Original doctor failed. Upstream writes state at connection and does not
  refresh it after login completion; status returns a fresh snapshot separately.
- Bounded operator recovery reapplied the exact existing view-only value,
  causing the provider itself to publish a fresh snapshot. Settings bytes,
  provider identity and connection stayed unchanged; no direct state-file edit.
- Public doctor passed afterward. Owned attach/status/child-only capture/stop
  passed native relationship guards, retained login, left viewer hidden and
  removed the worker. No apps/games/input, reconnect or system-policy changes.
- Official 0.4.0 runtime/guards unchanged. The provider race can recur; documented
  operator recovery is a workaround, not a permanent code fix. Private evidence:
  evidence/windows-provider-readiness-2026-10-16. Next: consumer retries ordinary
  doctor/attach; evaluate a provider-side post-login refresh in separate work.

## Official 0.4.0 remote rollout (2026-10-15, live acceptance complete)

- Dedicated Windows/Linux environments use the checksum-verified public wheel;
  all 34 runtime resources match. No release assets/tag or native code changed.
- After user reboot/local sign-in, actual Windows Codex/OpenCode normal persistent
  MCP workflows passed 7/13 tools, exact Unicode, independently checked images
  and native identities. All 594 Mac preview samples stayed nonactivating;
  1,983 parent samples kept ParaDesk hidden/unminimized. Default CLI rebind,
  windowless controller, stop/stale refusal and cleanup passed with 88 more
  hidden-parent samples. Same post-reboot child/login retained; workers/editors,
  controller and one-shot tasks removed. Owned test previews/brokers closed.
- Fresh Linux Codex/OpenCode default-MCP workflows passed six tools each, exact
  Unicode/images, same persistent controller and private display/audio/editor
  routing; 261 nonactivating Mac preview samples. Owned session/editors/controller
  cleaned. Earlier Linux agent runs used direct MCP: previous persistent-MCP
  wording was incorrect; fresh runs close that gap. Persistent CLI was separately
  verified. No Linux human-display capture/input/activity monitor or stability claim.
- Consumer logging fix ce9671c uses its existing private-directory factory for
  Windows 3.13 Limited-token compatibility. Native regression ran red/green;
  141 portable tests and seven-job CI 38839516195/38839780348 passed. Dedicated
  consumers use it; no global cctl or existing ACL/policy changes.
- Extra Linux normal-MCP attempt failed before tools at the Unix socket path
  limit (112 bytes); shortening its private test cache to 89 bytes passed. Limit
  remains. Windows external-stop missing-binding refusal is ADAPTER_ERROR, while
  explicit cctl stop refuses input as session_stopped. Both rebind paths passed.
- My bare-exe operator instruction was wrong: guarded ParaDesk requires explicit
  --minimized then --start. Corrected manual launch requested auth once, user
  signed in locally; no setup/policy change. Earlier failed attempts retained.
- Earlier docs CI 38839573592/38839784302 passed seven jobs each. Private evidence:
  evidence/official-0.4.0-rollout-2026-10-15. Next: normal isolated use with manual
  cold-boot auth, short Unix cache paths and explicit preview reopen on failure.

## 0.4.0 release (2026-10-15, published)

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
  and the live-tested candidate. Main release CI 38834233351 and exact-tag CI
  38834328744 passed all seven jobs; draft workflow 38834328177 passed.
- Published experimental https://github.com/batteryshark/quietwing/releases/tag/v0.4.0
  at 33c6a90. Public unauthenticated downloads/checksums, source rebuild and fresh
  installs passed; all 34 resources match. Own Mac venv uses the official wheel.
  Wheel SHA256 df5e72e61a4109c585641892965a2f89e93711897f351263cf8564bceebeafb0.
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

0.4.0 is published and verified. Retain final main/consumer documentation CI in the
private release evidence and the signed-in Mac guest/preview for inspection.
Native viewer windows on Linux/Windows, explicit lifetimes and game/GPU validation
remain future work. The original historical Windows obstruction is unidentified.

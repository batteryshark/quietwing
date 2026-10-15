# QuietWing tracker

Updated: 2026-10-15

## 0.3.1 viewer cleanup (2026-10-15, release preparation)

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
  rebuild passed; all 29 runtime resources match. Hosted CI and exact-tag draft/
  archive verification remain release gates. Keep native deferral explicit.

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
- Remaining Windows visibility limit: stop restores original viewer visibility,
  which may cover another window. Hidden/connected control passed; minimized,
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

Finish 0.3.1 static/package/CI release gates, then prioritize explicit lifetimes
and a read-only viewer. Repeat native Windows/two-harness acceptance when available. Measure setup and game/GPU behavior separately; the historical obstruction is still unidentified. docs/status.md is
the current capability/validation summary.

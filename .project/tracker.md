# QuietWing tracker

Updated: 2026-10-15

## Windows interruption investigation (2026-10-15, active)

- Corrected completion wording: 0.3 Windows live GUI acceptance was not done.
  Current provider has no native child. New sign-in is needed for that acceptance;
  none requested on the desktop. No login, settings, input, or host capture used.
- Original parallel-workload stop: 14:37 EDT, obstruction guard with no saved
  blocker identity and the same visible application set. QuietWing install checks
  began about 14:40; only a read-only inventory overlapped before the stop. Shared
  host UIA timeouts predate the inventory. Historical occluder remains unknown.
- Exact headless replay passed with a windowless console-session monitor: 284
  samples, no new visible windows, foreground remained the running workload.
- Service-session console probes did not reproduce a popup; no speculative
  QuietWing runtime change. Prepared a separate workload runner patch for consistent
  headless launches and blocker metadata; its command checks and Windows C# compile
  pass. Applying/messaging that active project awaits explicit user authorization.
- User requests moving the checkout to ~/Projects/workstack/quietwing when ready;
  update its venv and private cctl path directly, with no aliases.

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
  live GUI acceptance remains deferred. Operator reported a window interruption
  during headless validation; final inventory found no release-test process/window,
  and its origin was not established. Existing provider/authentication retained.
- 17 native sources match the historical 0.2 acceptance; actual Codex/OpenCode
  workflows passed then on all three platforms. Preserve that distinction.
- Raw release evidence is ignored under evidence/release-0.3.0; no credentials,
  guest disks/snapshots, machine inventory, or captures enter Git or release assets.

## Next action

Prioritize explicit lifetimes and a read-only viewer. Repeat Windows native
acceptance when an authenticated child is available; investigate diagnostic/setup
foreground interference without assuming the reported interruption was resolved
at source. docs/status.md is the current capability/validation summary.

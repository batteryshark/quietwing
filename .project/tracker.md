# QuietWing tracker

Updated: 2026-10-15

## Release 0.3.0

- Public MIT repository: https://github.com/batteryshark/quietwing. Sole package,
  import, and command: quietwing, no aliases. Native state identities retained.
- Computer-ctrl integration merged in PR #1 (442768ad); hosted CI passed on
  Windows/Mac/Linux with Python 3.11/3.13, 141 tests per run and package build.
- QuietWing hosted CI passed on Windows/Mac/Linux with Python 3.11/3.14 plus
  distribution audit. Windows install-probe scripts-directory assumption fixed.
- Release workflow builds audited wheel/source/SHA256SUMS from v0.3.0; publish
  only after the exact release head is green and assets are independently checked.
- Mac updated integration resume/capture/save passed. Linux fresh installed
  acceptance stages passed native input/Unicode/click/audio, SSH reconnect,
  stale refusal, TTL, and cleanup; 167 stable host samples, original X display only.
- Windows separate release venv passed install/import, native compile without
  launching worker, transport tests, and missing-child refusal. Provider file and
  installed resources unchanged; no main-desktop input/capture/controller changes.
  Existing child was disconnected; fresh live GUI acceptance remains deferred.
- 17 native sources match the historical 0.2 acceptance; actual Codex/OpenCode
  workflows passed then on all three platforms. Preserve that distinction.
- Raw release evidence is ignored under evidence/release-0.3.0; no credentials,
  guest disks/snapshots, machine inventory, or captures enter Git or release assets.

## Next action

Complete publication/asset verification for v0.3.0, then prioritize explicit
lifetimes and a read-only viewer. Repeat Windows native acceptance when the child
is available. docs/status.md is the current capability/validation summary.

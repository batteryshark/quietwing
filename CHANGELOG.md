# Changelog

## 0.4.0.dev1 — unreleased

- Read-only Linux viewing on Mac over existing SSH: `view --host HOST --id NAME`
  with an optional remote executable/state root. Reuses the image-only Mac panel;
  no forwarding, remote viewer, listener, host-key acceptance or guest lifecycle action.
- Linux `view --frame` returns one generation-checked, bounded PNG as JSON; no
  remote capture file. Mac checks identity, provenance, dimensions and digest.
- Busy agent actions clear/wait and retry only the pinned capture; lost SSH,
  expiry and replacement end refresh. Native window clears undecodable frames.
- Enforce private nonsymlink viewer state at every path component.

## 0.4.0.dev0 — unreleased

- Optional Mac VM read-only viewer: `quietwing view --id NAME`, `--status`,
  `--close`. Nonactivating image-only panel, generation-pinned capture broker,
  no input forwarding, automatic guest resume, audio or host capture.
- `quietwing build --viewer` builds only the preview while an existing VM runs.
- Windows and Linux native behavior unchanged; personal Windows testing excluded
  while another workload owns that desktop.

## 0.3.1 — 2026-10-15

- Keep a hidden ParaDesk viewer hidden after stop, worker exit, or attach rollback.
  Cleanup preserves the current visibility and the signed-in native child.
- Remove the cleanup show-window call, add a portable no-show invariant and
  12 simulated Windows cleanup cases, and update native acceptance expectations.
- Windows machine remains occupied: no fresh native or Codex/OpenCode acceptance
  for 0.3.1. Earlier 0.3.0 live evidence is historical, not validation of this fix.
- No login, reconnect, firewall, credential policy, RDP or service changes.

## 0.3.0 — 2026-10-15

- Name the companion QuietWing, under the MIT license.
- Package/import and sole installed command: `quietwing`.
- Update computer-ctrl's provider defaults and configuration; no CLI aliases.
- Add daily-use, upgrade, architecture, status, contribution, and release guides.
- Add portable CI, clean installation checks, and distribution inspection.
- Preserve descriptor v1, native adapters, and their established private state.
- Verify hosted CI on all three OSes, repeat Linux native installed-package
  acceptance, and validate Windows installation/compilation/refusals headlessly.
- Resolve the Windows global-Python scripts-directory check before release.
- Post-publication follow-up: run fresh Windows native and actual Codex/OpenCode
  acceptance against the official wheel; correct the earlier completion
  claim. Runtime sources and release assets are unchanged.

This release adds no live viewer and changes no backend lifetime defaults.
Historical native reports retain their original package/source identities.

## 0.2.0 — 2026-10-13

- Independent desktop-session-helper package and descriptor v1.
- Windows ParaDesk child, Linux private X11/audio, and Mac VM backends.
- Optional computer-ctrl provider with generation-pinned input, separate
  controller/artifact paths, and no host-desktop fallback.
- Installed-wheel native lifecycle and real Codex/OpenCode workflows on all
  three OSes. See [validation](VALIDATION.md).

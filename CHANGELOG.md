# Changelog

## 0.4.0 — 2026-10-15

- Optional read-only Mac window for a local Mac VM or an existing isolated
  Linux/Windows desktop over SSH: `view --id NAME`, `--status`, `--close`.
  Use `--remote-platform windows` for Windows; Linux remains the remote default.
- Image-only, nonactivating preview: no keyboard focus, input/audio forwarding,
  host capture, automatic session creation/resume/reconnect or generation rebind.
  Closing leaves the existing desktop and agent work running.
- Generation/PID/connection/display guards, bounded PNG/JSON transport, verified
  dimensions/digest/provenance, private state and image clearing on failure.
  Linux busy capture waits only for the pinned generation; other failures require
  explicit preview close/reopen. Frames do not extend Linux TTL or Windows idle.
- Existing SSH trust/authentication, literal arguments/encoded PowerShell, optional
  existing-key selection; no forwarding, listener, credential-policy/firewall/RDP
  changes or saved credentials. Preview window currently runs on Mac only.
- `build --viewer` compiles just the Mac preview while a VM runs. Native owner and
  guest bridge sources are unchanged from the earlier accepted VM implementation.
- Includes the 0.3.1 Windows cleanup fix: hidden ParaDesk stays hidden after stop,
  worker crash and attach rollback, preserving the native connection and login.

- Later official-package follow-up passed native Windows lifecycle checks and
  actual Codex/OpenCode normal-MCP editor workflows on Windows and Linux.
  Same Windows login retained and hidden; private Linux display/audio verified.
  See [current validation](docs/status.md) for counts, limits and consumer fixes.

## 0.3.1 — 2026-10-15

- Keep a hidden ParaDesk viewer hidden after stop, worker exit, or attach rollback.
  Cleanup preserves the current visibility and the signed-in native child.
- Remove the cleanup show-window call, add a portable no-show invariant and
  12 simulated Windows cleanup cases, and update native acceptance expectations.
- Windows machine remains occupied: no fresh native or Codex/OpenCode acceptance
  for 0.3.1. Earlier 0.3.0 live evidence is historical, not validation of this fix.
- Later 2026-10-15 follow-up against the unchanged official wheel passed native
  input/capture/stop/crash/rollback and actual Codex/OpenCode editor workflows.
  The authenticated child stayed connected and hidden; publication deferral closed.
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

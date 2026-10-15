# QuietWing tracker

Updated: 2026-10-15

## Current work

- Repository preparation for QuietWing 0.3.0, MIT. User selected the name and
  requested one command without aliases; computer-ctrl is updated directly.
- Separate package/import/CLI `quietwing`; descriptor v1 and native adapters
  retained. Native state/cache/ownership names are deliberately unchanged.
- Added CI, draft release tooling, distribution/installation checks, examples,
  and usage/upgrade/security/contribution guides.
- Local preparation complete: 34 portable tests; wheel/source audit, source
  rebuild, and fresh installs passed; workflow lint passed. No GitHub publication.
- Windows machine is occupied; no Windows connection, desktop tests, installs,
  configuration or settings changes are part of this session.

## Evidence and limits

- Historical native installed-wheel and two-harness acceptance: 0.2, 2026-10-13,
  all three platforms. `VALIDATION.md` and platform integration reports preserve
  exact source/package provenance. This is not a fresh 0.3 native claim.
- Current consumer regression: 141 passed in 22.53s. Companion: 15 dispatcher/
  distribution, 11 Windows fake transport, 8 Mac fake generation checks passed.
- 17 native source files byte-identical to 0.2. Updated cctl/installed QuietWing
  resumed the saved Mac guest, captured its desktop, and saved/stopped it again;
  no host focus/pointer change, no guest audio devices, no input sent.
- Sole installed/imported command/package is quietwing. Local folder renamed;
  private Mac cctl target now selects its new executable. Native state retained.
- Current limits and next capability work: `docs/status.md`. Live viewing and
  lifetime policies remain explicit follow-up work.

## Next action

Create/push the GitHub repository when authorized, inspect hosted CI, and review
the draft release. Repeat new-command native rollout on Linux and Windows when
available. Follow-up viewer/lifetime work is scoped in docs/status.md.

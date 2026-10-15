# Current status

Updated 2026-10-15. QuietWing is experimental software with usable native backends.
It succeeds desktop-session-helper with a separate package and MIT license.

## Proven behavior

The 2026-10-13 version 0.2 acceptance exercised installed wheels, ordinary native
apps, screenshots, native input, reconnect/save-resume, stale-generation refusal,
and owned cleanup on Linux, Mac, and Windows. Codex CLI and OpenCode each
completed actual editor workflows on all three. Saved Unicode, tool calls,
screenshots, and host pointer/focus metadata were checked independently.
See [validation](../VALIDATION.md) and its platform reports.

Version 0.3 changes project/package/CLI naming and repository tooling. Native
backend implementation and state conventions are retained. Portable tests and
clean-package checks are separate from that historical native acceptance.
GitHub CI is not evidence of a real GUI workflow. The repository-polish session
does not run or modify the occupied Windows machine.

## QuietWing 0.3 local release checks

| Check | Result |
| --- | --- |
| Portable dispatcher/distribution, Windows fake transport, Mac fake generation tests | 34 passed on the Mac. |
| Updated computer-ctrl regression | 141 passed. |
| Clean wheel installation and sole command/import | Passed; only `quietwing`, no old command alias. |
| Source archive inspection, rebuild, and fresh install | Passed; required resources/license/guides present, private/generated content excluded. |
| GitHub workflow lint | Passed with actionlint 1.7.12; Actions revisions pinned to reviewed commits. |
| Native source comparison | 17 runtime/native source files identical to 0.2. |
| Updated cctl → installed QuietWing → Mac guest | Resume, fresh visually inspected capture, provider identity, and save/stop passed. Host pointer/focus unchanged; guest has no audio devices. No input was sent. |
| New-name Windows/Linux native rollout | Deferred. Historical backend acceptance remains valid evidence for those unchanged sources, not a new installation claim. |
| Remote GitHub CI and release publication | Pending repository creation/push. Local lint does not establish hosted CI success. |

## Current limits

- No unified live viewer, takeover control, or agent pause/resume panel.
- Windows requires an authenticated, connected, non-minimized ParaDesk viewer.
  No automatic sign-in or reconnect.
- Windows owned apps close after 30 minutes without requests. Linux defaults to
  a fixed 30-minute TTL. Mac has no idle-save policy.
- Linux uses llvmpipe software rendering on the tested host. No gaming claim.
- Mac was tested on Apple Silicon, macOS 27.0.1, SDK 27, Swift 6.4. Older
  hosts/toolchains are unvalidated; guest provisioning is explicit.
- The computer-ctrl adapter lacks accessibility, browser DOM/CDP, window
  management, drag/scroll, and audio/video tools.
- Windows/Linux share the user's filesystem/device access. Application-specific
  device routes and singleton IPC need their own checks.

## Next measured work

1. Make lifetimes explicit for long tasks, with visible expiry and a safe policy.
2. Add a read-only viewer that opens/closes without disturbing session identity
   or agent input. Keep takeover a separate explicit action.
3. Repeat native installed-package acceptance under the QuietWing command on
   Windows when available, and on Linux.
4. Expand computer-ctrl capabilities only with per-platform evidence.

These are follow-up features, not features shipped in 0.3.

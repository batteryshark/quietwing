# QuietWing contract

This project owns the creation/attachment, lifetime and control boundary of isolated OS work sessions. It is separate from computer-ctrl. Package version: 0.4.1; JSON envelope schemaVersion: 1. The helper runs on its target OS; SSH is an optional outer transport, not an additional listener.

## Commands

- `doctor`: read-only prerequisite and capability checks; no permission prompts or setup changes. Windows may compile a windowless status probe into its private cache; the provider and desktop remain read-only.
- `start --id NAME`: create only an owned isolated session when supported and prerequisites are met. Otherwise return a specific setup/authentication error. Do not silently attach to the host desktop.
- `attach --id NAME`: adopt a verified existing isolated session with an explicit identity. Never log off or replace a pre-existing session on stop.
- `status --id NAME`: report live state and verified capabilities; revalidate process/session identity, not just a saved state file.
- `exec --id NAME -- PROGRAM ARG...`: launch a generic application inside that session. Preserve arguments without shell interpolation. Record only owned resources for cleanup.
- `capture --id NAME --output PATH`: capture only that session and return the image path, dimensions and capture time. Errors must not fall back to a parent screenshot.
- `input --id NAME --type TEXT | --key KEY | --click X Y [--button N] | --move X Y`: deliver native input only to the verified isolated session. Text is data, including leading hyphens and shell metacharacters. Input must fail closed when session identity, ownership or permission checks fail.
- `view --id NAME [--status | --close]`: optional Mac read-only preview of a local Mac VM or an isolated Linux or Windows desktop over SSH (`--remote-platform windows` for Windows). Open pins the existing live generation; it never starts/resumes a guest or forwards input. Status/close touch only preview files/processes. A failed capture clears the image; no automatic rebind. A busy Linux action may delay capture; only read-only captures retry against the same generation. Linux/Windows `view --frame --expect-generation TOKEN` returns one base64 PNG within the JSON envelope, without a remote viewer or standalone PNG. Windows frames do not reset its worker inactivity timer. See [viewer](docs/viewer.md).
- `stop --id NAME`: stop only helper-owned resources. Do not log off a pre-existing Windows/Mac user session, stop a human app, or change global settings.

Adapters may add necessary OS options. Every command must be documented by its adapter. Normal stdout is exactly one JSON object: `{ "ok": true|false, "platform": "linux"|"windows"|"macos", "session": {...}, "result": {...}, "error": {"code": "...", "message": "..."} }`. Optional fields may be omitted. The common entry point adds `schemaVersion`. A failed operation returns a nonzero exit status. Diagnostic logs go to stderr and must not contain credentials or authority cookies.

## Isolation and completion requirements

For every backend, completion requires a reusable helper controlling a generic native application in a separate instance, with fresh capture and real keyboard/mouse delivery, while the host user can continue working. A fixture, compiler success or permission preflight alone is insufficient. Reconnect/lifetime behavior must be explicit and verified. Audio must not leak into the human session; any unverified audio state must be reported and cannot support an overall isolation claim.

Hardware rendering, input isolation, capture, audio, viewer visibility and connection lifetime are separate capabilities. Do not infer GPU acceleration from device inventory or a software-rendered virtual desktop. An unavailable prerequisite must produce an actionable error rather than success or a substitution with the host desktop.

Normal control commands do not prompt for login or change host credentials, firewall, credential policies, RDP ports, reboot state or startup. Explicitly authorized Mac guest provisioning created a separate guest-local account and guest-only bridge LaunchAgent; its private mode-0600 credential is retained outside source and evidence, never a host credential. Clean save/resume does not require login. Shared CPU/GPU resources and same-user filesystem access are not isolated by a separate display.

`DESKHELPER_STATE_ROOT` selects a private state directory for adapters that use one. Validate names, permissions, PID birth identity and resource ownership before reuse or cleanup. Capture artifacts can be retained; private authentication material must never enter source/evidence files.

## Descriptor v1 and generation preconditions

`describe --id NAME` is the read-only versioned status interface. Successful session responses include `descriptor`, validated by `session.schema.json`: session ID, platform, generation, lifecycle state, boolean capabilities, local CLI connection protocol version and acquire/release behavior. A stopped session has null generation and no live control capabilities. Native details remain under `session` and are not the portable connection contract.

Bind a client to the returned generation, then pass `--expect-generation TOKEN` to status, capture, input, exec and stop. A mismatch returns `generation_changed` before delivering the operation; it never causes an implicit rebind. The backend enforces the check within its lifetime/dispatch protection, not merely before issuing another independently targeted command. Old clients may omit the precondition, but computer-ctrl always supplies it after binding. Create/attach is an explicit new binding decision; start does not accept a stale generation as permission to recreate anything.

`exec` starts an application and reports launch metadata; it does not promise synchronous stdout or completion. Caller exit preserves the work instance. Windows stop detaches only owned workers/apps and retains the external login and current viewer visibility. A viewer hidden with `--hide-viewer` stays hidden after stop, worker exit, or attach rollback; cleanup never shows/minimizes/disconnects it. Linux stops its owned private desktop; Mac saves and stops its guest. Interrupted mutations are not automatically replayed. New Mac guest provisioning remains explicit and separate from routine control.

Distribution: `quietwing` is the installed CLI. Sources are packaged as resources; native builds go to user state/cache, never into the installed package. `quietwing build` builds the Mac native helper without starting a VM. No computer-ctrl import/dependency is required.

# Integration acceptance status

The 0.2 companion and optional computer-ctrl provider passed the defined cross-platform integration gates. Native session management stays in this independent project. Acceptance covers the tools and conditions below; it does not establish full computer-ctrl capability parity.

| Evidence | Linux | macOS | Windows |
| --- | --- | --- | --- |
| Installed wheel and unchanged package resources | Pass | Pass, including independent native build cache | Pass, native compile in private state |
| Ordinary native app, fresh capture, native input | Pass | Pass | Pass |
| Reconnect or save/resume | Pass | Pass, saved guest retained | Pass, authenticated child retained |
| Generation/stale-operation refusal and owned cleanup | Pass | Pass | Pass |
| Real Codex GUI workflow | Pass | Pass | Pass |
| Real second-harness GUI workflow | OpenCode/GLM-5.3 pass | OpenCode/OpenAI pass | OpenCode/OpenAI pass |

The installed package tested was `desktop_session_helper-0.2.0-py3-none-any.whl`, SHA256 `8ad1b90f7a5523c64d22cdfda1e376d53825fb6e18a1e612f03c02cfef5c88b5`. The final wheel is `19f7497ada868ad2dad34cab40767ff5faf667fad9f3edc0edc7acef05e877fb`. Intermediate wheel `0e66a327d4b88ffa4d19238b46dd3202f1bb8022b7e8015fb1a30fb7d31a591b` added setup documentation and changed only dispatcher trailing whitespace. A byte comparison from that intermediate to the final wheel found only the two Mac prerequisite documents and archive RECORD changed; every runtime resource is identical. Native source identities are recorded separately. The wheel contains no credentials, disks, snapshots or machine-specific evidence.

The dispatcher has 11 passing contract tests. Computer-ctrl's full regression passed 141 tests, including 23 isolated-provider cases and the final repeated-stop cleanup fixes. These tests use a subprocess provider and do not substitute for native app acceptance.

Detailed portable reports: [Linux](linux/INTEGRATION.md), [macOS](macos/INTEGRATION_RESULTS.md), [Windows](windows/INTEGRATION.md). Scripts and platform setup instructions are versioned; raw machine inventories, screenshots and private state are intentionally ignored.

Each real harness pass requires successful isolated MCP calls, exact independently read saved text, an inspected fresh screenshot and host/session metadata. Model exit status alone is insufficient. Preserved unsuccessful attempts include a host process-creation failure and provider billing/free-tier/usage-limit failures before desktop actions.

The native lifecycle suites cover stale generation checks, reconnect/resume and cleanup. The model harness workflows separately prove that actual agents can launch and edit ordinary apps through the optional computer-ctrl interface. Reports state the scope of each observation and the actual source provenance; an on-disk hash is not proof of a previously imported controller module.

## Completion audit

| Requirement | Inspected evidence |
| --- | --- |
| Independent repository and installable package | Own Git repository, `pyproject.toml`, installed entry points on all three OSes, explicit wheel resources and source manifest; archives exclude credentials, images, snapshots and runtime inventories. |
| Versioned session interface | `CONTRACT.md`, `session.schema.json`, descriptor v1 and 11 dispatcher tests; native generation preconditions validated on each platform. |
| Optional cctl routing | `cctl --session NAME`, CLI/MCP provider selection and actual native workflows; host-default selection retained by regression. OS provisioning remains in this companion. |
| Target separation and fail-closed behavior | Target-hashed controller/artifact paths, generation-bound frames, private HOME/guest/browser profiles, unsupported-tool refusal and no host-engine construction in isolated regression. Same-user filesystem/device access is not a security sandbox. |
| Cross-platform two-harness acceptance | Codex plus OpenCode on each platform; exact independently read saved text, actual native tool calls, inspected screenshots and host pointer/focus metadata. Reconnect/resume, stale refusal and cleanup have separate native lifecycle evidence. |
| Clear capability and recovery limits | Platform setup guides, `CONTRACT.md`, and consumer `docs/isolated-sessions.md`. Windows retains an authenticated connected viewer; Mac saves its guest; Linux releases owned resources. |

The final consumer regression passed 141 tests in 22.46 seconds. OpenCode v2 needed an isolated runtime registration workaround and an actual `tools/list` readiness check; a connected status or model exit 0 alone did not establish usable tools. The passing Windows retry recorded all eleven tool definitions before inference, seven successful calls, exact saved content, 368 stable host samples and complete owned-controller cleanup. All local harness/server process groups were empty afterward. The earlier Linux-relay proposal was not used; local OpenCode required no additional login.

Acceptance does not include browser DOM/CDP, accessibility trees, audio/video recording, general application singleton behavior, gaming/performance, older untested OS versions, or Windows viewer minimize/disconnect support. These remain explicit capability limits, not hidden fallbacks.

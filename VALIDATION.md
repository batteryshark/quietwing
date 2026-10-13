# Integration acceptance status

This release candidate separates native session management from computer-ctrl. Completion remains pending the final Mac and Windows second-harness checks; package installation and basic companion control do not establish full computer-ctrl parity.

| Evidence | Linux | macOS | Windows |
| --- | --- | --- | --- |
| Installed wheel and unchanged package resources | Pass | Pass, including independent native build cache | Pass, native compile in private state |
| Ordinary native app, fresh capture, native input | Pass | Pass | Pass |
| Reconnect or save/resume | Pass | Pass, saved guest retained | Pass, authenticated child retained |
| Generation/stale-operation refusal and owned cleanup | Pass | Pass | Pass |
| Real Codex GUI workflow | Pass | Pass | In progress |
| Real second-harness GUI workflow | OpenCode/GLM-5.3 pass | Pending approved transport or usable local provider | Pending |

The installed package tested was `desktop_session_helper-0.2.0-py3-none-any.whl`, SHA256 `8ad1b90f7a5523c64d22cdfda1e376d53825fb6e18a1e612f03c02cfef5c88b5`. Later packaging revisions may add setup documentation; native source identities are recorded separately. The wheel contains no credentials, disks, snapshots or machine-specific evidence.

The dispatcher has 11 passing contract tests. Computer-ctrl's full regression passed 141 tests, including 23 isolated-provider cases and the final repeated-stop cleanup fixes. These tests use a subprocess provider and do not substitute for native app acceptance.

Detailed portable reports: [Linux](linux/INTEGRATION.md), [macOS](macos/INTEGRATION_RESULTS.md). Windows raw native/installed/reconnect evidence is retained locally while its portable harness report is completed. Scripts and platform setup instructions are versioned; raw machine inventories, screenshots and private state are intentionally ignored.

Each real harness pass requires successful isolated MCP calls, exact independently read saved text, an inspected fresh screenshot and host/session metadata. Model exit status alone is insufficient. Preserved unsuccessful attempts include a host process-creation failure and provider billing/free-tier/usage-limit failures before desktop actions.

The native lifecycle suites cover stale generation checks, reconnect/resume and cleanup. The model harness workflows separately prove that actual agents can launch and edit ordinary apps through the optional computer-ctrl interface. Reports state the scope of each observation and the actual source provenance; an on-disk hash is not proof of a previously imported controller module.

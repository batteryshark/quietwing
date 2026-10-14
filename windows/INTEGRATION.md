# Windows companion integration acceptance

The independent Windows companion and the optional computer-ctrl consumer passed native acceptance and two real model harnesses, Codex CLI and OpenCode. Both harnesses controlled an ordinary PowerShell ISE document inside an existing authenticated ParaDesk child. They used the installed companion wheel through the same SSH/MCP transport. No host-desktop fallback, provider reconnect, credential saving, or system provisioning was used.

## Tested components and artifacts

- ParaDesk 1.1.0, pinned source `c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435`; existing connected Windows 11 x64 child session.
- Desktop Session Helper 0.2.0 installed offline in a private Python 3.11 venv; the optional cctl controller used a separate existing Python 3.13 environment.
- Codex CLI 0.162.1, configured model `gpt-6.1-sol`.
- OpenCode 2.0.23, model `openai/gpt-6.1-sol`, with a temporary authenticated local server and explicit isolated MCP registration.

| Wheel SHA-256 | Validation |
| --- | --- |
| `8ad1b90f7a5523c64d22cdfda1e376d53825fb6e18a1e612f03c02cfef5c88b5` | Fresh private install, external worker compilation, native input/capture/exec, generic command window, generation refusal, and Codex GUI acceptance. |
| `0e66a327d4b88ffa4d19238b46dd3202f1bb8022b7e8015fb1a30fb7d31a591b` | OpenCode GUI acceptance. Windows adapter/C# resources match the preceding live-tested wheel; root dispatcher difference is trailing whitespace only, plus documentation changes. |
| `19f7497ada868ad2dad34cab40767ff5faf667fad9f3edc0edc7acef05e877fb` | Final distribution. Only Mac prerequisite documentation and wheel RECORD changed from the preceding wheel. Offline update of the idle private Windows venv, installed `--version`, and read-only `doctor` passed after cleanup. |

No native replay was needed for the final documentation-only wheel. The worker compiled into the configured state cache, outside site-packages. The installed-resource content hashes remained unchanged during runtime acceptance, and no executable was written into the package directory.

## Results and independent checks

| Check | Result |
| --- | --- |
| Native public companion CLI | Owned fixture and generic native process launch, real mouse/keyboard input, Unicode text, screen capture, literal argv preservation, generation refusal, and owned process-tree cleanup passed. |
| Native public cctl CLI | Configured isolated target passed native input/capture/launch, unsupported-tool refusal, stopped-target input refusal, generation change after reattach, and rejection of stale screenshot frames. |
| Separate SSH reconnect | Controller PID/birth and attachment generation remained the same. A frame obtained before SSH disconnect still targeted the correct attachment afterward; new native input and capture passed. |
| Codex | Seven successful MCP operations: editor launch, screenshot, click, select all, text entry, save, screenshot. Exact saved Unicode content matched the requested marker; runtime 55.6 seconds. |
| OpenCode | Same seven-operation editor workflow passed; runtime 31.54 seconds. Actual `tools/list` delivery was recorded before inference. Exact saved Unicode content matched the distinct requested marker. |
| Host noninterference | All 728 Codex and 368 successful OpenCode observation samples retained their respective initial host cursor and foreground window, with the connected viewer hidden and not minimized. |
| Final cleanup | Owned editors, helper worker, viewer observer, temporary task registrations, isolated consumer controller/interpreter shim, and local harness process groups were absent. The stale private controller port record was removed. Native child authentication, provider identity/connection timestamp, and original viewer visibility were preserved. |

Acceptance did not rely on a model's DONE or its exit code. The independent verifier decoded the saved file according to its BOM and required exact equality, with no whitespace stripping. It checked the real editor process's native session, the live generation, target-specific tool events, final image, host observer samples, application/worker exit, and unchanged provider identity. No script was executed in ISE; the document contained only a comment marker.

An earlier OpenCode attempt exited successfully after claiming tools were unavailable. Its file stayed blank and it emitted zero desktop tool calls, so it was recorded as a failure. A connected MCP status alone was insufficient readiness evidence. The shared runner now waits for the actual tool-list response forwarded through that OpenCode connection. The Windows diagnostic observed all 11 isolated tools before the successful retry. A startup race is a plausible explanation, not a proven root cause.

## Reproduce the tests

Complete the separately controlled provider setup in [SETUP.md](SETUP.md) first. The companion attaches only to an already authenticated child; `start` intentionally does not provision or authenticate Windows sessions. Install the wheel in a private venv with `pip install --no-index --no-deps <wheel>` and configure the provider/state directories described there.

For cctl, use a checkout or installation containing its optional isolated-session consumer. A private `CCTL_CONFIG` target selects the installed `deskhelper.exe`, its logical helper ID, `acquire="attach"`, `acquire_args=["--hide-viewer"]`, and `DESKHELPER_PARADESK_DATA`/`DESKHELPER_STATE_ROOT` in that target's environment. Give the consumer separate private state/cache roots. Set `CCTL_SESSION` to the same configured target. The companion remains usable without cctl.

The acceptance helpers run on Windows in the cctl Python environment, using configuration and arguments rather than a baked-in host or native session ID:

```powershell
python windows\test_adapter.py
python windows\harness_prepare.py prepare --target work --output C:\test-artifacts\codex
python windows\harness_prepare.py attach --target work --output C:\test-artifacts\codex
```

`prepare` creates a new owned UTF-16 blank-line file and performs a read-only provider check. `attach` refuses an existing helper binding and records its new generation and ownership metadata. The logical name `work` above is an example configured target, not a Windows native session number.

Run the consumer's `acceptance/isolated_harness.py` from the model host with an MCP command array that invokes only the configured target, optionally through SSH. Supply the ISE launch arguments `-NoProfile <prepared document>`, a distinct comment marker, `--replace-existing`, and `--save-key ctrl+s`. The successful OpenCode invocation additionally uses `--opencode-mode standalone --opencode-owned-server --model openai/gpt-6.1-sol`. The runner creates temporary per-run configuration, proves catalog readiness, and cleans its owned server; it does not edit global harness configuration.

After the harness exits, independently verify on Windows and stop only its helper-owned app/job:

```powershell
python windows\harness_verify.py --target work --output C:\test-artifacts\codex --marker '# chosen exact Unicode marker'
```

Use a fresh output directory and marker for the second harness. After the last run, stop the verified isolated consumer controller too:

```powershell
python windows\cleanup_test_controller.py --target work --output C:\test-artifacts\controller-cleanup.json
```

The cleanup script requires the target-private port, actual listener PID/birth, exact launcher path, matching configuration/session environment, and optional interpreter-shim relationship. It refuses an active helper binding. It verifies the observer/worker and exact task registrations have ended, without stopping the native provider. The private config and venv remain ready for a later ordinary auto-start.

ISE treats a BOM-only UTF-8 empty file as legacy encoding on the tested installation, prompting when Unicode is added. Preparing a UTF-16 blank line and selecting all before typing avoids that ambiguity; the final verifier still expects exactly the requested marker. A legacy single-line WinForms fixture used for lower-level tests does not implement Ctrl+A selection, so its key-event trace and HOME/SHIFT+END were used for that fixture; ordinary ISE Ctrl+A passed.

## Boundaries

The Windows lane requires an already authenticated, connected, non-minimized ParaDesk child. Hiding uses SW_HIDE while preserving the connection. Locking, secure desktops, disconnection, changed provider identity, or unavailable workers fail closed; there is no automatic sign-in or reconnect. Stop ends only helper-owned processes and restores viewer visibility, leaving the native child alive.

Before every exec/input, the child must expose no active/default Core Audio render endpoint and zero WaveOut devices. This was measured without emitting sound. It establishes absence of normal output routes at those measurements; it is not a driver/security sandbox, network-audio guarantee, or audio-capture implementation.

Browser automation, accessibility automation, and audio capture are unsupported capabilities. Singleton applications need their own profile/instance flags. Same-user files and machine CPU/GPU resources are shared. No claim is made about arbitrary games, fullscreen rendering, every graphics API, clean-machine provisioning, or unattended recovery after authentication is lost. The separate earlier D3D11 experiment is not a substitute for application-specific acceptance.

Raw screenshots, transcripts, native identities, private paths, and failures are deliberately kept in ignored local evidence directories. This portable report records the acceptance conditions without publishing machine identities or credentials.

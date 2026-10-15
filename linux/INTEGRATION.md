# Linux integration validation

This is the historical 0.2 acceptance report. Package names and hashes below
identify that tested build. For QuietWing 0.3 commands and setup, use the
[upgrade guide](../docs/upgrading.md) and this platform's README.

Validated on Debian 13/X11 on 2026-10-13. The companion provides an independent authenticated Xvfb display, optional xfwm4, private HOME/XDG/D-Bus, and private PulseAudio null output. Tests used ordinary Mousepad (GTK) and Xmessage (Xaw), with no viewer attached. The physical display received no input or screenshots; only pointer/focus metadata was sampled. The existing installed computer-ctrl remained unchanged: integration used a separate source checkout with its existing Python dependencies.

## Companion and consumer checks

| Check | Result |
| --- | --- |
| Generic native apps | Public helper `exec`, `capture`, keyboard and pointer input passed in both app types. Mousepad saved exact leading-hyphen, multiword, punctuation and Unicode input, then a newline/suffix after SSH reconnect. |
| Literal argument boundary | Exec arguments including `input --type`, spaces, shell punctuation and `--help` were preserved. Oversized input refused before delivery. |
| Audio routing | Private topology verified before playback: one null sink and its monitor, no physical device module. Captured 111,904 mono samples at 48 kHz, RMS 2,708.31 and peak 6,000. Host route/mute/volume/port metadata stayed unchanged. |
| Generation and lifetime | Replacing a cleaned stopped instance changed its UUID. Old-generation status/capture/input/exec/stop refused before action. Replacement while live refused. A 400-character native input crossing TTL completed before cleanup acquired the lifetime lock. |
| Public cctl tools | Session start/doctor, apps launch, screenshot, frame-based click, Unicode type, save key and zoom passed. Unsupported browser/run returned explicit errors. |
| Reconnect/controller restart | Separate SSH connections retained the app and generation. Restarting only the test controller adopted the same live instance. |
| Replacement and rebind | A stale controller refused type/click/capture/stop. Explicit start rebound to the replacement and invalidated old frames. Stopped descriptors cleared generation/capabilities; further input refused. |
| Host metadata | 142 samples in the generic helper suite and 81 in the cctl core suite were unchanged with no read errors. |
| Cleanup | Generic suite audited 15 saved current instances: terminal, no owned live supervisors/processes/runtime directories, only the original X socket. Core integration stopped its helper and both owned controllers with identity/birth checks. |

The Xvfb GLX renderer was **llvmpipe**, accelerated=false and hardware_rendering=false. The earlier successful AMD offscreen EGL experiment does not turn this Xvfb desktop into a hardware-accelerated display. Host PulseAudio exposed only a null sink, so audio evidence establishes private routing and captured signal, not physical-speaker audibility. This is default-route/session separation within one user, not a filesystem/device security sandbox. Browser, accessibility, Wayland and games are outside this validation; the isolated cctl backend does not expose audio/video tools yet.

## Real harness attempts

| Harness | Outcome |
| --- | --- |
| Codex CLI 0.162.1, gpt-6.1-sol | Passed: six successful tagged MCP calls (apps, screenshot twice, click, type_text, key), exact independently read saved text `ISO-CODEX-20261013 café Ω 世界`, and a visually inspected final capture. Exit 0 in 40.75 seconds. |
| OpenCode 2.0.23, inherited default model | Failed before tool calls: HTTP 402 `billing_not_configured`. Retained as an unsuccessful attempt; no account/configuration changes. |
| OpenCode 1.18.35 on Linux, `zai/glm-5.3` | Passed: eight successful tagged MCP calls (apps, screenshot twice, OCR twice, click, type_text, key), exact saved text `ISO-OPENCODE-20261013 café Ω 世界`, independently inspected final capture. Exit 0 in 55.99 seconds. |

Codex's host observer started after the app-launch event but before all native input actions. Its 245-sample initial verification supports input noninterference; app-launch noninterference is covered by the separate scripted suite. Harness success requires exact saved content, successful required tool events, and actual capture inspection; a model's DONE response is insufficient. The successful OpenCode run had all events covered by 457 unchanged host pointer/focus samples, with no read errors. Both harnesses used only isolated MCP tools. Their process groups had no remaining children. Both generation-pinned helper stops completed; exact-config cctl controllers were terminated with process-birth checks, owned observers stopped, private runtime/socket/authority state removed, and only the original X socket remained.

## Source identity and reproducibility

SHA256 identifies the actual sources used, rather than implying that later changes received a full rerun:

| Component | SHA256 |
| --- | --- |
| Companion Linux adapter (all final suites) | `61287f81a930dabaee8d8fb182781ee615cd70e16f1911870320f30e24079f74` |
| cctl isolated provider (scripted core) | `5c2058d9dec64c4b87aa0b67073725d3038cc4a5f600f8802cc2bbe8b212f25a` |
| cctl CLI (scripted core) | `61db2a0cb8084723d556daf83edf1beed8d20539f7e5e5ca8dedb4a73d2d16b8` |
| cctl config (core and harnesses) | `fde07e217927958f2c1a7f0d47df815056138963e5adc13e0b87300849e2074c` |
| Companion dispatcher (scripted core) | `70a94d48a85ef0ab582317ba75a743998f72e7cb6265d06772fc37c84fd57bc0` |
| cctl isolated provider (harness controller baseline) | `d0f9b976151c4f9d6ef8ff2c5a0fef7e893de297ff166070820a264f5e53c556` |
| cctl CLI (harnesses) | `024af2b53ad530fd47ca2539f9e7d39a987ee63ad97efa530a13ce38164b2975` |
| cctl private_paths (harnesses) | `590ef9781755847236fd048521049ddd2d5e6a32c152f12582823bd659c8ae19` |

The acceptance sources retained with their corresponding runs have these SHA256 values:

| Test source | SHA256 |
| --- | --- |
| Generic generation-aware native suite, tested snapshot | `94e3e1fd363c31105d99ddf4eae268d11098f9b580a53b787a61c4b570caccad` |
| Public cctl core suite, tested snapshot | `16a68a065ae450936fd2825899518f2f67f23ebfbbeb91892574f732a4a1e198` |
| Installed-wheel native suite | `d5e219785d0a0b0de8cf9ff0ad4f11c03f68cf3d8c90d7dcd96cfed2cc606f83` |
| Successful remote OpenCode runner snapshot | `9e1905cab663e7e018e2ca8adff2017c8bb1b3eee731ab03424cfbbc6fb124ca` |

OpenCode reused the private controller created by its earlier failed provider attempt. That controller imported the provider before the final stop-before-acquire guard was staged. The OpenCode verification JSON therefore records a later **on-disk** provider hash (`b8f3d25263c4868974a640d3eb6bb6a2bca77a35b60203ae3137560622137ffa`), while the controller's startup baseline was `d0f9b…` above. This is not proof that the final guard ran in that harness. The final guard has separate unit coverage; raw JSON is preserved with a source-provenance clarification.

[README](README.md) documents prerequisites and the public companion acceptance commands. [integration_acceptance.py](integration_acceptance.py) runs the two public cctl stages against a caller-prepared private config/launcher; its `CCTL_INTEGRATION_*` and `DESKHELPER_DISPATCHER` overrides avoid machine-specific paths. Prepare a fresh run and ID, then execute `stage1` and `stage2` through separate SSH connections. Do not rerun into historical evidence. Source portability edits after the successful run only changed acceptance environment defaults; the exact tested versions remain in local evidence.

The consumer's `acceptance/isolated_harness.py` runs each real harness with a per-run MCP config and an owned empty document. Provide the configured SSH command ending in `mcp`, app launch arguments and a unique marker. Independently inspect the saved document/events/captures afterward, then stop only the configured owned session/controller. No credentials, Xauthority cookies or operational private state belong in evidence exports.

Optional local evidence (ignored, not required by the package): `evidence/GENERATION_RESULTS.md`, `evidence/INTEGRATION_RESULTS.md`, `evidence/generation-manifest.json`, `evidence/cctl-integration-001/`, and `evidence/harness-001/`. These contain detailed JSON, exact documents, PNGs, source/artifact hashes and preserved failed attempts. One early scripted attempt used the nonexistent `browser` tool name; correcting the test to `browser_open` produced the recorded core pass.

## Installed wheel acceptance

The wheel `desktop_session_helper-0.2.0-py3-none-any.whl`, SHA256 `8ad1b90f7a5523c64d22cdfda1e376d53825fb6e18a1e612f03c02cfef5c88b5`, was installed with `pip --no-index --no-deps` into a fresh disposable remote venv. No system package or existing cctl install was replaced. The installed `deskhelper` entry point passed both native acceptance stages over separate SSH connections. Its supervisor resource was a persistent real file at `site-packages/desktop_session_helper/linux/adapter.py`, with the adapter hash listed above.

The wheel run repeated exact Unicode/metacharacter input and save, Xmessage native click, fresh captures, literal exec argv, stale identity refusal, reconnect, TTL expiry and stop cleanup. Audio capture had 124,493 mono samples at 48 kHz, RMS 2,567.73 and peak 6,000 after verified private topology. All 150 host pointer/focus samples were unchanged; audio routing metadata stayed unchanged. The final capture was visually inspected. An initial test invocation incorrectly supplied `--platform`; the dispatcher correctly rejected it before any session started. The corrected installed command is simply `deskhelper doctor`.

For the successful remote OpenCode route, use its installed Node bin directory on PATH and a fresh per-run working directory. Set PWD and OPENCODE_CONFIG to that directory, configure only the intended isolated MCP command, and run `opencode run --pure --auto --format json --model zai/glm-5.3 PROMPT` with stdin closed. OpenCode 1.18.35 documents `--pure` as “run without external plugins”; no shared-server `--attach` was used. Existing authentication was used without reading/copying credentials or changing billing/provider configuration. Newer OpenCode versions may require the runner's `standalone` mode instead. Availability and authentication must be checked on the target; model listing alone is not an inference pass.

## Final distribution update

The final wheel SHA256 `19f7497ada868ad2dad34cab40767ff5faf667fad9f3edc0edc7acef05e877fb` was subsequently installed offline (`--no-index --no-deps --force-reinstall`) into the same idle disposable Linux venv. Its installed `deskhelper --version` returned 0.2.0 and `doctor` succeeded. The installed Linux adapter remained byte-identical to the native-tested `61287f81…` source above; dispatcher SHA256 was `0535202c5ab37ac56561602a7d174a2f92e6e777708ee1a9be30e72787f94d93`. This final check did not repeat the earlier native GUI suite or start a desktop/model. A read-only cleanup audit checked 17 saved Linux instances: all terminal, no matching live owned processes or harness controllers, and only the original X display socket. The host cctl installation was untouched. Optional raw evidence: `evidence/package-final-001/verification.json` and `install.txt`.

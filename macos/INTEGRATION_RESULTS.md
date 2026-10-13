# macOS companion integration acceptance

Tested on Apple Silicon with the existing dedicated 2 vCPU / 4 GiB macOS VM. This record covers the installable companion boundary and cctl integration; it does not repeat the earlier VM installation/Metal investigation.

## Completed

- Build outputs and Swift module caches live outside installed resources, under a private configurable cache. The VM owner/probe compile and sign successfully; Python source checks and eight focused generation-boundary tests pass.
- The installed 0.2.0 wheel independently built into a second private cache. Every bundled Mac resource matched the wheel afterward; the provisioning guide was present and machine evidence absent. Its own newly built owner resumed the existing guest, captured TextEdit without TCC consent, survived four disconnected status clients, refused stale input before its timestamp changed, then saved/stopped with null generation. The owner executable path was verified to belong to the separate cache.
- Public status/capture/input/exec/stop accept an expected generation. All five stale operations were refused before an image, input, process or stop occurred. A controller retains its expected target across the status/action boundary. Guest mutations run through the checked owner and carry both owner and guest generations. Saved sessions expose no live generation.
- The scripted public cctl workflow launched TextEdit, captured a frame, clicked using that frame, typed Unicode, saved it, and independently read back the exact string `CCTL companion — café 日本語 👋 token-Mac-46`.
- Save/stop/start retained an unsaved TextEdit edit and the same guest bridge process, while creating a new VM owner generation. Old frames were refused; a fresh frame showed the resumed edit. Each controller process exited independently of VM lifetime.
- A real Codex CLI run using its installed default model completed apps → screenshot → click → type_text → key(save) → screenshot through only the isolated MCP server. Independent UTF-8 file readback exactly matched `MAC-CODEX-73 café 日本語 4821`; all six recorded calls succeeded on one generation, and the final screenshot was inspected.
- During that run the owned VM view remained offscreen/nonkey/nonmain; sampled host cursor and foreground process remained unchanged. No host input was posted. Both VM configuration and guest CoreAudio reported zero audio devices. Stop saved the session and confirmed owner exit; the harness process group was empty.

## Preserved failures and remaining acceptance

The first Codex attempt encountered host process exhaustion before its apps call could complete. Its exit code was zero because the harness reported the failure normally; the empty output file and failed event were retained, and it was not counted as acceptance. A subsequent serialized retry passed.

The real OpenCode executable with explicitly selected `opencode/ling-3.1-flash-free` exited before any tool call: its provider returned HTTP403 (`FreeTierError`). The document remained empty and the VM stayed saved. The existing Claude Code login also connected to isolated MCP, but its default model was rejected before tools by the provider’s five-hour usage limit (HTTP429). Both test documents remained empty and no harness process group remained. Neither rejected run is a passing second harness. A working, authorized provider route or another real harness is still required before claiming the required two-harness acceptance.

Runtime capabilities remain deliberately limited: guest screenshots, native guest keyboard/pointer, generic exec and silent audio; no audio recording, browser DOM or accessibility tree. New-VM provisioning is documented in [PROVISIONING.md](PROVISIONING.md) but was not repeated during this phase. No host account, Sharing, TCC, firewall or login changes were made. Raw local evidence is retained in the ignored VM evidence directory; credentials and VM state are not source artifacts.

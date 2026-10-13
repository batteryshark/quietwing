# Completion gates

The goal is a usable helper on Windows, macOS and Linux that controls a separate work instance while the human continues using the host. This document records what would prove that result; current evidence may cover only some gates. A passing earlier spike does not by itself validate the reusable helper.

Each platform must pass its public adapter and the common entry point where applicable:

1. Discover prerequisites without opening a window or permission prompt. Missing setup returns an actionable error.
2. Create or attach to an explicitly identified isolated instance. Record live OS session/display identity, helper ownership and process creation identity. The host desktop is never an alternative target.
3. Launch a normal native application through the public exec command, alongside an owned diagnostic fixture when useful. Verify that it is in the intended instance and that it does not redirect its window into the host session. Use private app profiles where shared profile locks would otherwise select the human's app.
4. Use the public input command for native pointer and keyboard events, including text with spaces, Unicode, leading hyphens and shell metacharacters. Verify intended app state and fresh capture independently of an input-call success flag.
5. Capture the isolated desktop before and after multiple changes. Match returned capture dimensions and identity. No host screenshot or human window contents are needed for this test.
6. Observe host pointer and focus metadata during launch, input and capture. All automation windows remain inside the work instance; helpers must not activate a host-side viewer or steal focus.
7. Verify a silent or isolated default audio path before producing any test tone. For a backend with an output device, confirm that a tone reaches the owned virtual output/capture while host output routing remains untouched. For an intentionally silent backend, verify the absence of live output devices; do not add an audio device merely to run a tone test. Document any untested bypasses or explicit-device limitations rather than claiming arbitrary process containment.
8. Reuse the same instance after the controlling CLI or SSH connection exits, without another login. Exercise input and fresh capture again. Record unsupported states such as minimize/detach/session loss separately.
9. Verify safe failure on stale/lost session identity and stop only helper-owned resources. A pre-existing login/session remains intact. Do not kill by a broad process name, trust PID alone, or delete an unrelated display/socket.
10. Record the installed dependencies, source used, public commands, output/capture evidence, cleanup and limitations in the platform's evidence folder. Generic GPU/game support is a separate measured capability; do not infer it from a small renderer probe.

No-completion conditions include: a compile-only Mac adapter, a fixture with no generic launch/control path, an unverified audio route, a viewer that must steal host focus, a hidden window that cannot accept native input, or a session that requires repeated user sign-in for routine commands. A setup prerequisite that only the owner can satisfy remains pending; it is not a successful platform result.

## Installable companion and computer-ctrl integration

The 0.2 integration adds these gates to the native requirements above:

1. Build and install the wheel in a separate environment on each target OS. Resolve native resources from the installed package, compile only in private cache/state, and verify live operations through the installed entry point. Inspect distribution contents to exclude credentials, machine state, images and snapshots.
2. Validate descriptor version, target identity, generation, capabilities, connection and lifecycle through the public CLI. Pin every operation after acquisition, reject stale requests before delivery, and invalidate old screenshot frames after replacement/rebind.
3. Keep host-control behavior available. Target controllers, artifacts and default browser profiles must be separated; unsupported tools fail without selecting a host engine.
4. Complete an ordinary app launch, fresh capture, native mouse/keyboard and exact saved-content workflow using at least two real agent harnesses on each platform. A scripted replay, successful model exit, failed provider connection or compile alone does not satisfy this gate. Inspect actual tool calls, saved files and host/session observations independently.
5. Verify reconnect/resume where supported and owned cleanup. Preserve the external Windows login and save the Mac guest. Document limitations for unsupported viewer, graphics, browser, accessibility and audio/video states.

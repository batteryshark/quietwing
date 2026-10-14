# Desktop Session Helper

A standalone companion that creates or attaches to a separate desktop for agent work while a human uses the host. It owns the platform session, native capture/input and lifecycle. The optional computer-ctrl integration consumes its versioned CLI; neither project depends on the other's source tree.

| Backend | Work instance | Lifecycle and limitations |
| --- | --- | --- |
| Windows | Existing authenticated ParaDesk child session | Attach to a hidden, connected viewer; detach owned workers/apps on stop. Minimized or disconnected viewers are unsupported. No automatic sign-in. |
| Linux | Private Xvfb display, HOME/XDG, D-Bus and PulseAudio null sink | Start a bounded owned session; reconnect over SSH; stop only its resources. Tested GLX renderer is software llvmpipe. |
| Apple Silicon macOS | macOS guest using Apple's Virtualization.framework | Resume an explicitly provisioned guest; save and stop to release RAM. Tested with 2 vCPU, 4 GiB RAM and no audio devices. |

## Install separately

Python 3.11 or later is required; the companion has no Python runtime dependencies. From a checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/deskhelper --version
.venv/bin/deskhelper doctor
```

On Windows use `.venv\Scripts\python.exe` and `.venv\Scripts\deskhelper.exe` instead. `uv tool install .` is an alternative when uv is already available. To build a portable wheel, use `python -m pip wheel --no-deps --wheel-dir dist .`; install that wheel on each target OS in a separate environment. The wheel includes native source resources; the target's existing compiler builds them into private state/cache. It does not include compiled executables, credentials, a VM disk or snapshots.

Package installation does not install OS prerequisites, change host policies, create accounts or provision a guest. Follow [Linux setup](linux/README.md), [Windows setup](windows/README.md), or [Mac provisioning](macos/PROVISIONING.md). Mac first-instance setup requires a guest-local account; routine clean save/resume does not require repeated login. `deskhelper build` builds the Mac helper without booting or downloading a guest.

## Use the CLI

Run on the controlled machine, optionally through existing SSH:

```sh
deskhelper doctor
deskhelper start --id work
deskhelper describe --id work
deskhelper exec --id work -- PROGRAM ARGUMENTS
deskhelper capture --id work --output /absolute/new-capture.png
deskhelper input --id work --click 100 100
deskhelper input --id work --type 'Hello — café 日本語'
deskhelper input --id work --key Return
deskhelper stop --id work
```

Windows uses `attach --id work --hide-viewer` instead of start and requires `DESKHELPER_PARADESK_DATA`. Mac uses an already provisioned ID. Linux can reuse a fully stopped ID with `start --replace-stopped`. Platform docs define key syntax, text limits and state paths.

`describe` returns descriptor version 1: identity, generation, capabilities, connection and lifecycle. Bind subsequent status/capture/input/exec/stop commands with `--expect-generation TOKEN`; a replaced instance is rejected before delivery. Failed commands return nonzero with a JSON error. A timeout can have an unknown outcome: inspect state before retrying a mutation. There is no human-desktop fallback. See [the contract](CONTRACT.md) and [descriptor schema](session.schema.json).

## Optional computer-ctrl integration

Install both projects on the controlled machine. Add an explicit target to a private cctl configuration:

```toml
[sessions.work]
command = ["/absolute/path/to/deskhelper"]
id = "work"
acquire = "start"
```

Use `cctl --session work mcp` for a harness, or `cctl --session work screenshot` for CLI use. Windows selects `acquire = "attach"`; its data-directory environment and hidden viewer option belong to that target's configuration. Computer-ctrl's `docs/isolated-sessions.md` covers those examples, remote SSH use, supported tools and recovery. Omitting session selection retains ordinary host control.

Each target has separate controller state, artifacts and browser-profile defaults. Accessibility trees, window management, browser/CDP, audio/video recording and game compatibility are not implied by basic capture/input. Same-user Windows/Linux sessions still share filesystem and hardware access; applications with custom device routes or singleton IPC need their own compatibility checks. Windows refuses execution/input when its normal audio output routes are not demonstrably absent; Linux uses a private null sink; the Mac VM has no audio device.

## Verification

[ACCEPTANCE.md](ACCEPTANCE.md) defines completion gates. The dispatcher contract tests run with `python -m unittest discover -s tests -p 'test_*.py'`. Platform acceptance scripts exercise actual applications, generation replacement, stale refusal, reconnect and owned cleanup. The integration adds real agent-harness workflows whose saved content and native evidence are checked independently of model completion messages.

The installed companion and optional computer-ctrl provider passed native lifecycle acceptance on all three platforms, plus ordinary-app workflows through both Codex and OpenCode. See [VALIDATION.md](VALIDATION.md) and its platform reports for exact coverage, source identities, preserved failures and limitations. Machine-specific raw evidence, screenshots and private inventories are retained locally and ignored by Git and package builds. Fresh checkouts contain portable source, setup instructions and curated results only.

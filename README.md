# QuietWing

**Separate desktops for agents. Keep using your computer.**

QuietWing gives a computer-use agent somewhere else to open applications, click,
type, and take screenshots. The agent works in a separate desktop while you keep
your own pointer, focus, and audio.

It is an independent companion to
[computer-ctrl](https://github.com/batteryshark/computer-ctrl). QuietWing owns
desktop lifetime and native capture/input. Computer-ctrl supplies the agent's
MCP tools, images, and automation workflow. QuietWing also works directly from
the command line, without computer-ctrl or a particular agent harness.

**Status: experimental. Latest release: 0.3.1; development: 0.4.0.dev0.** The native backends passed ordinary-app
and lifecycle acceptance in 0.2, including actual Codex and OpenCode workflows
on all three operating systems. Version 0.3 introduces the QuietWing name,
package, and repository tooling. The published 0.3.0 wheel also passed fresh Windows
native and actual Codex/OpenCode acceptance on 2026-10-15. [Current status](docs/status.md)
distinguishes that follow-up from initial release checks and historical evidence.
Version 0.3.1 prevents Windows cleanup from revealing the hidden viewer. Its
regression uses static checks and simulated OS calls in CI; fresh native Windows
and two-harness acceptance were unavailable for this patch.

The 0.4 development build adds an optional [read-only Mac preview](docs/viewer.md):
`quietwing view --id minimal`. It opens without taking keyboard focus and never
forwards viewer input to the guest. Windows and Linux viewing are unchanged.

## Pick your desktop

| Host | Agent desktop | Everyday behavior |
| --- | --- | --- |
| Apple Silicon Mac | macOS VM using Apple's Virtualization.framework | Resume a provisioned guest; save memory and release RAM on stop. Tested with 2 vCPU, 4 GiB RAM, no audio devices. |
| Linux | Private Xvfb with its own HOME/XDG, D-Bus, and PulseAudio null sink | Start/adopt an owned desktop; stop its apps when finished. Software rendering on the tested host. |
| Windows | Existing authenticated ParaDesk child session | Attach and hide its connected viewer. Stop owned apps/workers while preserving the Windows login. |

Windows needs an already signed-in child. Minimized/disconnected viewers are
unsupported. Mac needs explicit guest provisioning first. Package installation
alone does not prepare either desktop.

## Install

Python 3.11+ is required; there are no Python runtime dependencies.
Download the wheel and SHA256SUMS from the [v0.3.1 release](https://github.com/batteryshark/quietwing/releases/tag/v0.3.1).
For a private environment on Mac/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install https://github.com/batteryshark/quietwing/releases/download/v0.3.1/quietwing-0.3.1-py3-none-any.whl
.venv/bin/quietwing --version
.venv/bin/quietwing doctor
```

Windows uses `.venv\Scripts\python.exe` and `.venv\Scripts\quietwing.exe`.
Alternatively, install a reviewed wheel with
`python -m pip install /path/to/quietwing-VERSION-py3-none-any.whl`, or use
`uv tool install .` from a checkout. To develop from a checkout, install with `python -m pip install .`.
This setup does not require a PyPI release.

Native tools are separate prerequisites:

- [Mac setup and guest provisioning](macos/PROVISIONING.md)
- [Linux prerequisites and private desktop](linux/README.md)
- [Windows setup and ParaDesk](windows/SETUP.md)

The wheel includes native source; existing compilers build into a private cache.
It contains no VM disk, credentials, snapshots, or machine state. Installation
does not change host firewall, login policy, RDP ports, Sharing, accounts, or startup.

## First use

Run on the controlled machine, directly or through SSH. Use a provisioned Mac ID;
Linux can create a fresh ID.

```sh
quietwing doctor
quietwing start --id work
quietwing describe --id work
quietwing exec --id work -- PROGRAM ARGUMENTS
quietwing capture --id work --output /absolute/new-capture.png
quietwing input --id work --type 'Hello — café 日本語'
quietwing stop --id work
```

Windows uses `quietwing attach --id work --hide-viewer` instead of start, with
`DESKHELPER_PARADESK_DATA` set to its prepared ParaDesk directory. There is one
command, `quietwing`. No `deskhelper` alias is installed. See the
[upgrade guide](docs/upgrading.md) for an existing 0.2 setup.

Scripts should bind capture, input, exec, status, and stop to acquisition's
generation using `--expect-generation TOKEN`. Replaced sessions are refused
before delivery. Normal output is JSON; errors exit nonzero. The
[versioned interface](CONTRACT.md) is the source of truth.

## Connect computer-ctrl

Install both projects on the controlled machine. Use a computer-ctrl build
containing [the merged QuietWing integration](https://github.com/batteryshark/computer-ctrl/pull/1).
In a private cctl configuration:

```toml
[sessions.work]
command = ["/absolute/path/to/quietwing"]
id = "work"
acquire = "start"
```

Launch the agent's MCP server with `cctl --session work mcp`. Its first ordinary
control action acquires the target. Windows uses `acquire = "attach"`. The
[examples](examples/) cover each backend. [Daily use](docs/daily-use.md) explains
automatic acquisition, lifetimes, stopping, SSH, and progress viewing.

## Peek at the agent

Ask for a fresh screenshot, run `cctl --session work screenshot`, or use
`quietwing capture`. These capture the isolated desktop. A common live viewer and
show/hide command are not implemented yet. Mac stays offscreen; Linux has no
viewer by default; Windows retains ParaDesk's active connection.

## Scope

QuietWing provides session identity, lifecycle, app launch, pixels, and native
input. Accessibility trees, browser DOM/CDP, window management, audio/video,
and game compatibility are separate work. The computer-ctrl adapter supports a
subset of its normal tools. See [status and limitations](docs/status.md).

Windows/Linux apps retain their user's file/device permissions: separate desktops
are not a security sandbox. Mac uses a separate guest with no host home/project
folder shared. Read the [security model](SECURITY.md) before granting access.

## Develop

```sh
python scripts/check.py
python -m pip install build
python -m build
python scripts/check_distribution.py dist
```

Default checks never start a desktop or request permissions. See
[contributing](CONTRIBUTING.md), [architecture](docs/architecture.md),
[releases](docs/releases.md), and [validation evidence](VALIDATION.md).

MIT licensed. External tools and operating systems retain their own terms;
see [third-party dependencies](THIRD_PARTY.md).

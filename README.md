# QuietWing

<img src="assets/workstack-mark.png" alt="QuietWing comic mascot" width="256">

Some agent work needs the machine you've already set up: its installed software
and dependencies, connected hardware, or local data. Moving that work into a VM
can mean rebuilding the environment, and maintaining more VMs adds work as you
take on more tasks. Giving an agent access to your everyday machine carries
risk, but sometimes the convenience is worth it. You still need to get your own
work done without the agent tying up your pointer and keyboard focus.

QuietWing gives a computer-use agent a separate desktop on a machine you own,
so it can open applications, click, type, and take screenshots while you keep
using your own desktop. The agent's windows and input stay in its work instance;
you can check progress through status and screenshots, or the optional read-only
Mac viewer, and stop the instance when you're done. QuietWing is experimental;
the current release is [0.4.2](https://github.com/batteryshark/quietwing/releases/tag/v0.4.2).

Linux uses Xvfb under your existing user; Windows uses an authenticated ParaDesk
child session in the existing OS. Neither needs a separate VM for each task.
The current Mac backend uses an actual macOS VM on Apple's
Virtualization.framework. That guest needs provisioning, and the host's hardware
and software may not be available inside it.

QuietWing handles the desktop underneath the agent:

- Separate application windows and input let you keep working without sharing
  the agent's pointer and keyboard focus.
- Work survives the controlling CLI or SSH connection closing. Mac guests can
  save and resume their running applications; Linux and Windows have explicit
  expiry and cleanup rules.
- Generation-bound commands refuse a replaced desktop, so a stale controller
  can't send input to a new instance with the same name.
- An optional read-only Mac preview lets you watch a local Mac guest or a remote
  Linux/Windows target without forwarding clicks, keys, or audio.
- A versioned JSON CLI works with your own scripts or with
  [computer-ctrl](https://github.com/batteryshark/computer-ctrl), which supplies
  CLI and MCP tools for the agent. QuietWing doesn't require a particular harness.

## What a separate desktop means

The backends use different OS facilities and have different requirements:

| Target | Agent's workspace | Setup and lifetime |
| --- | --- | --- |
| Apple Silicon Mac | A macOS VM on Apple's Virtualization.framework, with a separate guest account/disk and an offscreen view. No audio devices or host home/project share. | Provision the guest first. Stop saves VM memory and releases RAM; start resumes it. |
| Linux | A private Xvfb display, HOME/XDG directories, D-Bus session, and PulseAudio null sink under your existing user. | Install the native tools first. Stop or fixed TTL expiry ends owned apps; session files remain. |
| Windows | An existing authenticated ParaDesk child session, with its connected viewer hidden during control. | Sign in locally first. Attach verifies the child; stop ends owned apps/workers and preserves the login and viewer visibility. |

Linux and Windows retain the user's filesystem and device permissions. Their
desktop separation is not a security sandbox for untrusted programs. The Mac
guest has a separate OS boundary, a private helper transfer directory, and NAT
networking. Shared machine resources still need consideration. Read the
[security model](SECURITY.md) before granting an agent access.

## Install and prepare a target

QuietWing needs Python 3.11+ and has no Python runtime dependencies. Download
the wheel and `SHA256SUMS` from the
[v0.4.2 release](https://github.com/batteryshark/quietwing/releases/tag/v0.4.2)
and verify the checksum before installing. On Mac/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install /path/to/quietwing-0.4.2-py3-none-any.whl
```

Windows uses `.venv\Scripts\python.exe` and `.venv\Scripts\quietwing.exe`.
For source installation, use `python -m pip install .` from a reviewed checkout;
pip may fetch build requirements. Native tools are separate prerequisites:

- [Mac setup and guest provisioning](macos/PROVISIONING.md) requires Apple
  Silicon, Apple's Swift tools, space for the guest, and an explicitly completed
  guest Setup Assistant and bridge bootstrap.
- [Linux setup](linux/README.md) requires Xvfb/X11, xauth, xdotool, D-Bus,
  PulseAudio, FFmpeg, and Mesa; xfwm4 is an optional window manager.
- [Windows setup](windows/SETUP.md) requires a supported Windows edition,
  .NET Framework tools, and a separately installed ParaDesk provider with an
  authenticated, connected, non-minimized child viewer.

The wheel includes native source, built with existing compilers into private
cache/state directories. It includes no VM image or credentials. Installing the
package doesn't provision a guest, create a Windows login, or grant desktop
permissions. Use the platform guide before running lifecycle commands.

## Use the desktop

Run QuietWing on the controlled machine, directly or over existing SSH. Put the
installed executable on your PATH, or use its full path. For a prepared Mac guest
named `work`, or a new Linux ID:

```sh
quietwing doctor
quietwing start --id work
quietwing describe --id work
```

On Windows, set `DESKHELPER_PARADESK_DATA` to the prepared provider data directory
and acquire with `quietwing attach --id work --hide-viewer` instead of `start`.
QuietWing won't sign in or reconnect a disconnected viewer for you.

Acquisition returns a generation token. Pass that same token to subsequent
commands; replace `TOKEN` below with the returned `session.generation`:

```sh
quietwing exec --id work --expect-generation TOKEN -- PROGRAM ARGUMENTS
quietwing capture --id work --expect-generation TOKEN --output /absolute/new-capture.png
quietwing input --id work --expect-generation TOKEN --type 'Hello from the agent desktop'
quietwing stop --id work --expect-generation TOKEN
```

Choose a program installed in the target environment and a new capture filename
in an existing writable directory. `exec` launches asynchronously; a successful
launch doesn't mean the application's task has finished. Normal output is JSON;
failures exit nonzero. The [CLI contract](CONTRACT.md) and
[daily-use guide](docs/daily-use.md) cover binding, recovery, and cleanup.

Save Linux/Windows documents before stopping. Linux's default 30-minute TTL runs
from creation even during activity. Windows workers close owned apps after
30 minutes without activity other than preview frames. Mac has no automatic idle
stop; a clean stop saves guest memory, while crash recovery can require login.

## Connect an agent through computer-ctrl

Install [computer-ctrl](https://github.com/batteryshark/computer-ctrl) and
QuietWing on the controlled machine. In a private cctl configuration:

```toml
[sessions.work]
command = ["/absolute/path/to/quietwing"]
id = "work"
acquire = "start"
```

Configure the agent's MCP command as `cctl --session work mcp`, with `CCTL_CONFIG`
pointing to that file. The first control action acquires the target and pins its
generation. Windows uses `acquire = "attach"` and provider settings; the
[platform examples](examples/) include those options. Remote use is
`cctl --host user@machine --session work mcp`, with configuration on that machine.
QuietWing adds no network listener.

Closing the agent or MCP connection leaves the work instance alive within its
lifetime limits. Use `cctl --session work session stop` when finished. See
[daily use](docs/daily-use.md) for explicit restart/rebind and residual state.

## Watch progress and understand the limits

On Mac, build the optional preview once with `quietwing build --viewer`, then
run `quietwing view --id work` for an already running local guest. It also shows
isolated Linux/Windows desktops over SSH. Closing the preview leaves the agent
working; viewing never starts or reconnects a desktop. The
[viewer guide](docs/viewer.md) covers remote options and follow mode.

There is no native preview window on Linux or Windows, common takeover button,
or agent pause panel. Screenshots and native mouse/keyboard input are the core
control surface. The computer-ctrl adapter lacks accessibility trees, browser
DOM/CDP, window management, drag/scroll, and audio/video tools. Windows
[held keys](docs/held-keys.md) require a live worker advertising `key_hold`;
installing 0.4.2 alone doesn't replace an older running worker. Support and
platform-specific limits are in [status](docs/status.md).

## Reference and development

Start with [daily use](docs/daily-use.md), the [CLI contract](CONTRACT.md), and
the [descriptor schema](session.schema.json). For implementation and packaging,
see [architecture](docs/architecture.md), [contributing](CONTRIBUTING.md), and
[releases](docs/releases.md). Portable checks are `python scripts/check.py`;
native acceptance requires a separately authorized target and the
[acceptance plan](ACCEPTANCE.md).

Owned source and documentation are [MIT licensed](LICENSE). The comic artwork
is AI-generated and offered under MIT to the extent applicable, without an
exclusive-copyright claim. See [rights](RIGHTS.md) and
[third-party terms](THIRD_PARTY.md) for the scope and external prerequisites.

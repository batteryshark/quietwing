# Linux adapter

`adapter.py` creates a separate X11 instance for ordinary native applications. It uses installed Xvfb, private X authority, an independent D-Bus session, private HOME/XDG directories, and a private PulseAudio server with only a null sink and its monitor. An installed xfwm4 is used as the session's window manager. No viewer, TCP listener, login switch, system service, or autostart is needed.

## Prerequisites

On the tested Debian 13 target, `dpkg-query -S` mapped the required `doctor` binaries to these packages. For a fresh Debian installation, first inspect the package plan, then install the same list if appropriate for that host:

```sh
sudo apt-get --simulate --no-install-recommends install python3 python3-venv xvfb xauth x11-utils xdotool ffmpeg mesa-utils dbus-daemon dbus-bin pulseaudio pulseaudio-utils
sudo apt-get --no-install-recommends install python3 python3-venv xvfb xauth x11-utils xdotool ffmpeg mesa-utils dbus-daemon dbus-bin pulseaudio pulseaudio-utils
# Optional window manager, plus the GTK app used by acceptance:
sudo apt-get --no-install-recommends install xfwm4 mousepad
```

The adapter itself does not install packages or change system services. Review proposed conflicts/replacements, especially on a host using PipeWire as its audio server; it requires the PulseAudio executable and modules for its own private daemon. No host audio-service replacement is needed by the adapter. Other distributions must resolve equivalent packages rather than reuse Debian names.

| Package | Tools used |
| --- | --- |
| `xvfb`, `xauth`, `xdotool` | `Xvfb`, `xauth`, `xdotool` |
| `x11-utils` | `xprop`, `xdpyinfo`; acceptance also uses `xmessage`, `xwininfo` |
| `ffmpeg`, `mesa-utils` | `ffmpeg`, `glxinfo` |
| `dbus-daemon`, `dbus-bin` | `dbus-daemon`, `dbus-send` |
| `pulseaudio`, `pulseaudio-utils` | `pulseaudio`, `pactl`; acceptance also uses `paplay` |
| `xfwm4`, `mousepad` | Optional window manager and native editor acceptance app |

The companion wheel has no Python runtime dependencies beyond Python 3.11 or newer. `python3-venv` supports the documented private installation. After installing the wheel, run `quietwing doctor`; successful session start additionally verifies the private audio module topology.

## Commands

Run on the target Linux host, directly or over SSH:

```sh
python3 adapter.py doctor
python3 adapter.py start --id work-001 --width 1024 --height 768 --ttl 1800
python3 adapter.py exec --id work-001 -- mousepad --disable-server
python3 adapter.py input --id work-001 --type 'Hello from the private display'
python3 adapter.py input --id work-001 --key ctrl+s
python3 adapter.py capture --id work-001 --output /tmp/work-001.png
python3 adapter.py status --id work-001
python3 adapter.py stop --id work-001
```

The supervisor survives the creating SSH command's exit. Every public operation emits one JSON envelope; failures have a nonzero exit status and an error code. `COMMAND --help` returns JSON help. `exec` is asynchronous: it returns an owned PID and stdout/stderr log paths, and passes arguments after `--` without shell interpolation. Finished app leaders are reaped and exit results are recorded in the private session directory.

`input` supports exactly one of `--type TEXT`, `--key KEY`, `--click X Y [--button 1]`, or `--move X Y`. Coordinates are absolute pixels in the isolated display. Keys use xdotool names, such as `ctrl+a`, `Return`, and `alt+F4`. Input uses native XTEST without the XSendEvent window-target fallback. Text includes literal spaces, leading hyphens and shell metacharacters; type at most **1024 characters per call**, splitting longer text. Newlines and tabs become native Return and Tab keys; CRLF/CR are normalized to LF, and other ASCII control characters are rejected. Native typing uses 25 ms key spacing: the earlier 1 ms setting lost a final CJK character in Mousepad. This tested spacing improves delivery but cannot verify arbitrary applications' semantic acceptance of each event. Delivery has a bounded timeout below the common dispatcher's 90-second limit.

The session defaults to 1024×768 and a 30-minute TTL. Width must be 320–4096, height 240–2160, and TTL 5–86400 seconds. Status can briefly report `stopping` during bounded cleanup before `stopped` or `failed`; input/capture/exec reject a session that is no longer running. TTL teardown waits for an already-running bounded operation to finish, then removes the owned resources. Completed session evidence/home files are retained, while private runtime sockets, authority cookies, and owned processes are removed. `attach` explicitly rejects unowned sessions.

## Stable instance identity

Each new instance returns `session.id` and a public UUID in `session.generation`. Pass `--expect-generation UUID` to `status`, `capture`, `input`, `exec` and `stop` to bind a command to that exact instance. Put the flag before `--` for `exec`. A stale value returns error code `generation_changed` before output creation, app execution, native input or cleanup. Calls that omit the flag remain compatible, but select the current instance at execution time.

Generation comparison, ownership verification and the operation occur under the same root replacement lock and per-instance lifetime lock. The supervisor takes the lifetime lock before teardown, so expiry cannot recycle the display midway through an action. `stop` releases the lifetime lock for cleanup while retaining the replacement lock. This is an operation-level guarantee; a caller needing consistency across multiple operations must pass the same expected generation to each one.

Default `start` still rejects an existing ID. `start --id NAME --replace-stopped` can archive a fully cleaned terminal instance under the private state root's `.history` directory and create a new generation with that ID. It refuses running instances, live supervisors, remaining owned processes, surviving runtime directories or incomplete cleanup evidence. It never stops an existing instance as a side effect of replacement.

The capability map explicitly includes `capture`, `input`, `keyboard`, `pointer`, `exec`, `audio_capture`, `audio_silent`, `browser` and `accessibility`. The first seven are true for a successfully initialized session; browser and accessibility automation are false. `audio_capture` means apps launched by `exec` can record the private null monitor; there is no dedicated audio recording command. Ordinary browser apps inherit private HOME/XDG defaults, but no browser protocol/controller or arbitrary browser compatibility is asserted.

State defaults to `~/.local/state/desktop-session-helper`. Override it with `DESKHELPER_STATE_ROOT`; the root must belong to the current UID and have mode 0700. State and authentication material must not be published or copied into evidence. Public responses omit tokens/cookies. Each operation validates PID birth identity, the private runtime ownership marker, and the X server's session property. Stale identities fail closed; there is no fallback to `:0`. Cleanup targets the exact session environment token and rechecks ownership before signalling. A failed or expired backend triggers cleanup.

## Audio and rendering

Start succeeds only after the private PulseAudio server reports exactly its null sink, monitor source, and the two expected modules. Ordinary PulseAudio clients use this private socket; default ALSA playback is configured as null, and the environment prevents accidental connection to the host PipeWire socket. There are no hardware detection/output modules. The null monitor can be recorded by launching FFmpeg through `exec` if the agent needs app audio. The helper never needs to play through human speakers.

This is **same-user session separation, not a security sandbox**. An explicitly configured application can still access files or open hardware devices permitted to that UID; shared CPU/GPU/memory limits and denial of raw device access are outside this adapter. It does not make a GPU-backed desktop: capabilities preserve the actual GLX renderer and explicit `Accelerated` field, with unknown acceleration left unknown. The tested Xvfb session uses llvmpipe software rendering.

## Validation

`acceptance.py stage1` and `stage2` exercise public adapter commands pinned to the returned generation. Run them in separate SSH invocations, setting the same fresh `DESKHELPER_TEST_ID` and `DESKHELPER_TEST_RUN` for both. Stage 1 leaves a bounded owned session for stage 2; failures still have a TTL. The tests use Mousepad and Xmessage, known test strings, owned screenshots, a generated tone through verified private audio, and host pointer/focus/routing metadata only. They never capture human windows. `generation_acceptance.py` independently exercises ID replacement, refusal of all stale operations and an actual native input operation overlapping TTL expiry. See `evidence/RESULTS.md` and `evidence/GENERATION_RESULTS.md` for measured runs and limits.

The runtime adapter is one standard-library Python file plus its installed external tool dependencies (`doctor` lists them). It locates its supervisor through `Path(__file__).resolve()` and starts it with the current Python executable. Installed packaging must preserve the adapter as a real on-disk Python resource, rather than an ephemeral extraction that disappears after a command. Private state is stored outside package resources. Acceptance scripts and screenshots are development evidence, not runtime dependencies.

Acceptance observers default to host display `:0`, the current user's `~/.Xauthority`, and `unix:/run/user/<uid>/pulse/native`. Override these explicitly with `CCTL_TEST_HOST_DISPLAY`, `CCTL_TEST_HOST_XAUTHORITY` and `CCTL_TEST_HOST_PULSE` when appropriate; they read host metadata only. `integration_acceptance.py` defaults to `~/Experiments/cctl-isolated/run-001` and `~/Experiments/quietwing/cli.py`. Configure another test setup through `CCTL_INTEGRATION_ROOT`, `CCTL_INTEGRATION_RUN`, `CCTL_INTEGRATION_LAUNCHER`, `CCTL_INTEGRATION_ID` and `DESKHELPER_DISPATCHER`. These test configuration variables do not affect the production adapter.

For installed-package acceptance, `DESKHELPER_TEST_COMMAND_JSON` can name the installed entry point (a JSON string array), `DESKHELPER_TEST_ADAPTER` supplies its on-disk adapter resource for the source hash, and `DESKHELPER_TEST_EVIDENCE_ROOT` places artifacts outside the installed package. For example, set the command to `["/path/to/venv/bin/quietwing"]` and run the same two stages. The test source defaults still invoke the adjacent adapter directly.

See [INTEGRATION.md](INTEGRATION.md) for the portable current validation summary, including actual Codex/OpenCode MCP runs, installed-wheel acceptance, source provenance and cleanup. Detailed raw evidence is optional and ignored by the package repository.

## Peek from a Mac

QuietWing 0.4.0 on both ends can show this isolated desktop in QuietWing's
nonactivating, read-only Mac window over existing SSH. On Mac, run
`quietwing view --host user@linux-machine --id work --remote-command /absolute/path/to/quietwing`
and include `--remote-state-root` if this Linux session uses a custom state root.
No Linux viewer, VNC service, firewall change or X11 forwarding is required.
Closing the preview leaves the session running; its fixed TTL is unchanged.
See the [viewer guide](../docs/viewer.md).

The Linux transport operation is `quietwing view --frame --id work
--expect-generation UUID`. It returns one base64 PNG in the usual JSON envelope
after generation, process and display verification under the lifetime lock.
It writes no image on Linux and cannot start a desktop or deliver input.

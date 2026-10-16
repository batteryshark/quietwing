# Read-only viewer on Mac

Available in QuietWing 0.4.0, for a local Mac VM or an already running
isolated Linux or Windows desktop over SSH. The preview window opens on your Mac.
Use the QuietWing executable from the same environment that computer-ctrl uses.
The viewer is optional; computer-ctrl's MCP interface and configuration do not change.

```sh
quietwing build --viewer                 # one explicit build using Apple CLI tools
quietwing view --id minimal              # peek at a running guest
quietwing view --id minimal --status     # inspect the preview without raising it
quietwing view --id minimal --close      # close preview; guest keeps running
```

The window shows a guest screenshot about once a second. It opens in the
background and cannot become the key or main window. Resize or move it normally,
or use its close button. Clicks and scrolling in the image are ignored and never sent to the guest.
Typing stays with your active Mac application; the preview never takes keyboard focus. There is no takeover control or audio.
Opening it again reuses the same window without raising it.

The viewer never starts or resumes a guest. If computer-ctrl has not yet acquired
the session, run its normal isolated workflow first, or explicitly use
`quietwing start --id minimal` and wait for `status` to report `running`.
Do not rebuild the VM owner while it runs: `build --viewer` builds only the
separate preview application and is safe with an existing guest.

By default, each preview pins one VM generation and owner PID. On a stopped, replaced or
unavailable session, it clears its image and reports that the session is
unavailable. Close and reopen explicitly after a new session starts. Automation
can additionally pass `--expect-generation TOKEN` to open or close; a mismatch
is refused. `view --status` reports viewer metadata, not live guest status.

The image app receives only private files from a capture broker; it has no VM
connection, event injection or input forwarding. The broker reuses the existing
owned-guest capture operation. It cannot capture the human desktop. No listener,
login item, permission prompt or host settings change is added.

Only the current PNG is retained, under the private state root at
`viewers/macos-vm/NAME/TOKEN`; closing removes it. Small diagnostic metadata is
retained for troubleshooting. A crashed broker's window clears a stale image
after three seconds and exits after fifteen seconds without a heartbeat.
Frames can pause during capture or guest work; this is a preview, not a video
stream. CPU, memory and screen space are still shared with the host.
The preview window currently runs on Mac; a native viewer window on Linux or Windows is not implemented.

## Leave an SSH preview open across agent attachments

Development 0.4.2 adds opt-in `--follow` for Linux and Windows SSH targets:

```sh
quietwing view --host user@windows-machine --remote-platform windows --id work --follow \
  --remote-command 'C:\private\venv\Scripts\quietwing.exe' \
  --remote-state-root 'C:\private\helper-state'
```

The same Mac window waits when the attachment disappears, clears old pixels,
and resumes after an agent explicitly attaches a verified replacement. It can
also open before an attachment exists. It never starts, resumes, attaches,
reconnects RDP, signs in, or changes visibility on the remote machine. The host,
remote executable, state root, SSH identity and logical ID stay fixed. Only the
read-only preview follows; computer-ctrl never silently changes its control binding.

Every new generation must pass the existing status/descriptor checks, and every
frame is pinned to that generation and checked for isolated-image provenance.
A replacement between status and capture clears and retries. Availability errors
retry after 1, 2, 4, 8, 16, then at most 30 seconds; heartbeat updates continue
while waiting. Invalid protocol, unsafe state, boundary/ownership failures and
invalid images end refresh and require inspection. No input or operation is replayed.
Healthy viewing sends frames only. Rediscovery uses ordinary status, which may
extend a Windows worker's idle timer once it is found; frames do not. Linux's
fixed TTL is unchanged.

Use the same target options without `--follow` for `--status` or `--close`.
Status reports `follow`, the current verified `generation` (null while
rediscovering), and waiting/error information. Close affects only the Mac
preview and cancels further retries; an already in-flight read-only request may
finish within its existing bounded deadline. Closing never starts a new window.
Changing an open preview between pinned and follow modes requires closing that
Mac preview first. `--follow` cannot be combined with `--expect-generation`, and
a following window cannot be closed with a generation precondition. Local Mac VM
viewing remains generation-pinned. Published 0.4.1 does not yet include `--follow`.

## Linux over SSH

Use QuietWing 0.4.0 or later on Mac and Linux. Existing Linux prerequisite
packages and an already trusted, noninteractive SSH login are required. The viewer
does not install software or request login, change SSH configuration or accept
new host keys. First start the Linux isolated session through its normal
computer-ctrl workflow or explicit QuietWing start; viewing never acquires it.

```sh
quietwing view --host user@linux-machine --id work \
  --remote-command /home/user/quietwing/venv/bin/quietwing
# Use the same target options with --status or --close.
```

If the Linux target uses a nondefault `DESKHELPER_STATE_ROOT`, also pass
`--remote-state-root /absolute/private/state`. The host, executable, state root
and ID identify a separate preview. Mac VM and different Linux targets cannot
reuse each other's preview. Standard SSH host aliases resolve through existing
SSH config; command/path arguments are quoted literally. No X11/agent/port
forwarding, persistent SSH master or new listener is created.

Linux `view --frame --id work --expect-generation TOKEN` is the read-only
transport leaf. It checks the same generation, process birth identities, private
runtime and X server ownership as normal capture, under the existing lifetime
locks. It returns one bounded PNG in a versioned JSON envelope with dimensions,
time and SHA-256; it writes no remote frame file. The Mac verifies the envelope,
generation, dimensions and digest before displaying it. Remote clock skew cannot
make an old connection appear fresh: preview age is timed locally per completed
capture. SSH carries only status/frame requests from the viewer; the image app
has no network or input code.

A long agent action can hold the Linux capture lock. The preview then clears and
waits, retrying only read-only capture against the same generation. Stop, expiry,
identity changes, invalid frames or lost SSH clear a pinned preview and end refresh;
close and explicitly reopen after recovery. No input is replayed, session is
restarted, or replacement generation followed. Viewing does not extend Linux's
fixed TTL. Closing disconnects the preview and leaves Linux work running.
The current frame is private on Mac under `viewers/linux-ssh/TARGET_HASH/NAME/TOKEN`
and removed on close; small diagnostic metadata remains. Cadence depends on SSH
and capture latency, roughly one frame per second on the accepted setup. This
is not a video or remote-control client.


## Windows over SSH

Use QuietWing 0.4.0 or later on Mac and Windows. The
existing ParaDesk child must already be authenticated, connected and unminimized,
and QuietWing must already be attached with `--hide-viewer`. Viewing never starts,
attaches, hides, reconnects or signs in to ParaDesk. It requires no extra firewall,
credential-policy, RDP-port or service configuration.

```sh
quietwing view --host user@windows-machine --remote-platform windows --id work \
  --remote-command 'C:\private\venv\Scripts\quietwing.exe' \
  --remote-state-root 'C:\private\helper-state'
# Use the exact same target options with --status or --close.
```

`--remote-platform windows` selects a fixed noninteractive PowerShell command over
existing SSH. Executable, state path, ID and generation are passed as literal
single-quoted values in an encoded script; no local/remote command evaluation,
forwarding or persistent SSH master is added. Existing SSH aliases and trust
still apply. If the existing key is not a default SSH identity, pass
`--ssh-identity /absolute/path/to/existing/key` on Mac. This selects an existing
key for this connection without changing SSH configuration or copying the key.
Use the same option for status/close. The provider directory does not need to be passed to the viewer:
the attached worker retains and revalidates its original provider identity.

Windows `view --frame --id work --expect-generation TOKEN` only requests an
in-memory PNG from that exact worker. The worker checks the non-console child,
active connection, provider PID/birth and ordinary input desktop before capture.
The bounded reply includes dimensions, generation, SHA-256 and isolated-image
provenance. It creates no standalone Windows PNG; the normal private transient
IPC response is deleted after reading. Frames do not reset the worker's existing
30-minute inactivity timer. Agent actions and ordinary status requests retain
existing lifetime behavior.

The Mac uses the same image-only, nonactivating window as Linux and local VMs.
Closing it removes the Mac PNG and leaves the attachment, its applications and
the authenticated child running. A worker stop/crash, lost SSH, lock, disconnect
or generation replacement clears the image and ends refresh; recovery requires
explicit close/reopen in the default pinned mode; `--follow` above can wait for a verified replacement. The preview never reveals the hidden ParaDesk window or
forwards keyboard, pointer, clipboard or audio. Remote capture latency determines
refresh rate; it is a screenshot preview, not a video/game streaming client.
Windows and Linux target state have separate private namespaces even with the
same host, executable and logical ID. Windows helper cleanup continues to leave
ParaDesk's current visibility unchanged.

## Native UI regression

Run the portable checks first. On an explicitly available Mac, the native fixture
creates only its own panel and synthetic pixels. It dispatches local events
without posting host input, checks nonactivation and stale-image removal, then
closes. It can optionally render a supplied isolated-guest PNG for visual review.

```sh
mkdir -m 700 /tmp/quietwing-viewer-ui-test
xcrun swiftc -D VIEWER_TEST -parse-as-library macos/Viewer.swift tests/native_viewer.swift -o /tmp/quietwing-viewer-ui-test/check
/tmp/quietwing-viewer-ui-test/check /tmp/quietwing-viewer-ui-test
```

Use a fresh private output directory for each invocation. The fixture is not a
substitute for live guest and actual agent acceptance; see [status](status.md).

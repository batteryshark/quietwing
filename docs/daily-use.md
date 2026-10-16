# Daily use

Install QuietWing and computer-ctrl on the machine that owns the isolated
desktop. Start with an [example configuration](../examples/) in a private file.

## Automatic acquisition

Configure the agent's MCP command as `cctl --session work mcp`, setting
`CCTL_CONFIG` to the private target configuration when necessary. Its first
screenshot, input, or app launch acquires that target. `doctor` and `session
status` inspect without acquiring a desktop.

Mac starts or resumes a provisioned guest. A clean saved snapshot resumes
without another login. Linux creates a private desktop or adopts its live owned
instance. Windows attaches to an existing signed-in ParaDesk child; it does not
create a login or reconnect a disconnected viewer.

Closing an agent or MCP connection preserves the work instance, subject to the
lifetime limits below. An explicitly stopped controller requires `session start`
before more work.

```sh
cctl --session work session status
cctl --session work session start
cctl --session work screenshot
cctl --session work session stop
```

Remote use is `cctl --host user@machine --session work mcp` or the corresponding
CLI command. The target configuration resolves on the remote machine. Existing
SSH carries the traffic; QuietWing adds no network listener.

## View progress

Ask the agent to display a fresh isolated screenshot, or run
`cctl --session work screenshot` and open the returned `path`. Standalone:
`quietwing capture --id work --output /absolute/new-file.png`. Standalone capture
paths must be new files.

The 0.4 development build adds a [read-only Mac viewer](viewer.md):
run `quietwing build --viewer` once, then `quietwing view --id work` while the
provisioned guest runs. For Linux, use `view --host user@linux-machine --id work`
and the remote executable/state-root options from the viewer guide. The window
opens on Mac over existing SSH; viewing does not extend Linux TTL.
Closing the viewer leaves the agent working. It does not
start a guest, take keyboard focus or forward input. The ID must match the
QuietWing ID in your target configuration, which can differ from the cctl name.

There is no common takeover button or agent pause command. Linux has no viewer
by default. Windows
has ParaDesk's viewer, but the helper has no supported show/hide toggle during
work. Keep it connected and unminimized. Use screenshots to inspect without
competing with the agent's input. A hidden Windows viewer stays hidden after stop
or worker exit; reveal it only deliberately through ParaDesk's own UI.

## Save and finish

| Backend | Meaning of stop | Current lifetime default |
| --- | --- | --- |
| Mac | Save the whole VM session, stop its owner, release RAM. Guest apps remain in saved memory. | No automatic idle save/stop. |
| Linux | End owned apps and release display/audio resources. Keep retained session files. | Fixed 30-minute TTL from creation, even while active. `--ttl` can set a longer bounded run, up to 86400 seconds. |
| Windows | End owned apps/workers without showing the viewer. Keep its current visibility and the authenticated child alive. | Worker exits and closes owned apps after 30 minutes without requests; not configurable yet. |

Save Linux and Windows documents before stopping or going idle. Linux's TTL is
not refreshed by activity. Its cctl `acquire_args` can set `--ttl` and
`--replace-stopped`; see the Linux example. Reusing a stopped ID creates a new
desktop rather than restoring running applications.

## Recovery

Inspect `session status` after a timeout; a mutation may already have completed.
Commands are never replayed automatically. If generation changed, `session start`
explicitly rebinds and discards old frames. An old controller cannot silently
target a replacement desktop.

A Mac crash/cold boot can require guest login; routine clean save/resume does
not. A Windows lock, secure desktop, provider reconnect, or disconnected viewer
requires operator attention. Follow the platform guide rather than changing host
login or credential policy as a recovery shortcut.

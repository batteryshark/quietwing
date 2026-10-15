# Windows adapter

Run this adapter on Windows with Python 3.11 or newer. It uses the installed .NET Framework C# compiler, Windows PowerShell, Task Scheduler, and an already authenticated ParaDesk child session. SSH can be an outer transport; no host address, SSH identity, password, listener, or credential persistence is built in.

Set `DESKHELPER_PARADESK_DATA` to the existing ParaDesk directory containing `state.json` and `settings.json`. `DESKHELPER_STATE_ROOT` optionally selects helper state; default is `%LOCALAPPDATA%\DesktopSessionHelper`. The instance directory receives a user-and-SYSTEM-only ACL. Packaged `Worker.cs` and `NativeSupport.cs` are read-only resources. A worker executable is compiled under `%DESKHELPER_STATE_ROOT%\cache\windows\<source hash>` (or the default state root), outside the installed package. No write access to installed sources is required.

```powershell
$env:DESKHELPER_PARADESK_DATA = 'C:\Users\YOURNAME\Experiments\paradesk-spike\data'
python windows\adapter.py doctor
python windows\adapter.py attach --id work --hide-viewer
python windows\adapter.py exec --id work -- C:\Windows\System32\cmd.exe /d /q /k
python windows\adapter.py input --id work --type 'echo Hello from the child desktop'
python windows\adapter.py input --id work --key ENTER
python windows\adapter.py capture --id work --output C:\Temp\child.png
python windows\adapter.py status --id work
python windows\adapter.py stop --id work
```

Every session command requires `--id`. `start` returns `EXISTING_SESSION_REQUIRED`: this backend never creates/reconnects a native session or triggers sign-in. `attach` verifies the actual WTS parent-child relationship, active non-console child, viewer PID/birth, and usable desktop. The caller must already have permission to launch a Limited Interactive task in these existing sessions. No elevation prompt or password is requested.

`--hide-viewer` uses SW_HIDE only, keeping the RDP connection active. Stop, worker exit, and attach rollback leave the viewer's current visibility alone. A hidden viewer stays hidden; cleanup never reveals it. The viewer observer still records state and exits when the exact worker PID/birth disappears. The stop result reports `restored: false`. The adapter rejects a minimized viewer; it never minimizes, detaches, reconnects, restarts, or logs off ParaDesk. Locks, secure desktops, changed provider connection identity, missing workers, and disconnected sessions fail closed.

`exec -- PROGRAM ARG...` uses native CreateProcess with literal Windows argument quoting. It creates the process suspended, verifies its real session, assigns an owned kill-on-close Job Object, then resumes it. Stop or worker exit terminates launched process trees belonging to that job. This includes unsaved work in those helper-launched applications; save it before stopping. Human processes outside the job are untouched. Worker inactivity for 30 minutes also ends the worker/job. Task registrations have no triggers and are removed by stop. After unexpected worker exit, call stop to clean remaining registrations before attaching again.

Use independently launchable native applications. Browser or other singleton applications must use a separate application profile/instance option; a program can otherwise delegate work through its own IPC to a pre-existing process outside the job. This helper does not sandbox arbitrary applications, user files, drivers, CPU, or GPU resources. Same-user file access remains shared. Process launches that cannot join the job fail while still suspended.

Input options are `--type TEXT`, `--key CTRL+A` (plus ENTER, ESCAPE, TAB, arrows, HOME/END, PAGEUP/PAGEDOWN, DELETE, BACKSPACE, SPACE, F1–F24), `--move X Y`, or `--click X Y --button N`. Buttons are 1 left, 2 middle, 3 right. Coordinates use the child virtual screen. Native input is subject to Windows privilege restrictions; the worker does not bypass UAC or secure desktops. Capture uses the child's composed screen and never falls back to the console.

Before **every exec and input**, the child enumerates Core Audio active render endpoints, all three default render roles, and WaveOut devices. Only zero active endpoints, no default render device for every role, and zero WaveOut devices permit the operation. Otherwise `AUDIO_ROUTE_UNVERIFIED` blocks exec/input; status/capture remain diagnostic. This measures absence of normal output routes without emitting sound. It is not a guarantee against special drivers, device APIs, deliberate configuration changes by launched programs, or network audio. Audio capture is not provided.

Each attachment uses a fresh random IPC generation. Requests are private transient files, deleted after reply or timeout, and never replayed into a later attachment. Full exec arguments are not retained in operational responses. Capture files are retained at the caller's requested path. `status` validates worker birth identity and reports live runtime audio; saved profile mute alone is never treated as proof.

The bounded `python windows\acceptance.py` test requires `DESKHELPER_STATE_ROOT` and an existing authenticated child. It uses only owned apps, exercises the public adapter, deliberately crashes only its own worker, verifies the viewer stays hidden through crash/stop and same-ID generation isolation, then removes its tasks. Evidence contains public test nonces, not user input.

Every live attachment response includes `session.id`, immutable `session.generation`, and explicit `session.capabilities` for capture, input, keyboard, pointer, exec, audio_capture, audio_silent, browser, and accessibility. The last three unsupported interfaces (audio capture, browser, accessibility) are false; `audio_silent` reflects a current child endpoint measurement. Lifecycle metadata states that native-session ownership and reconnect are false and stop preserves the native child.

Optional `--expect-generation TOKEN` is accepted by status, capture, input, exec, and stop. Use the token returned by attach/status to bind subsequent calls. The worker compares it immediately before dispatch, including stop, and returns `generation_changed` without acting on a mismatch. Each reattachment gets a fresh token; old callers without the option remain supported. Attach and stop serialize per ID so delayed cleanup cannot remove a replacement binding. Example: `python windows\adapter.py input --id work --expect-generation TOKEN --type "Hello"`.

`windows/test_viewer.py` enforces a portable no-show invariant. On Windows CI it
compiles the actual worker with viewer OS calls replaced by in-memory fakes and
executes 12 stop/crash/rollback visibility cases. It uses no provider, real window,
capture or input and does not replace native acceptance on a signed-in child.

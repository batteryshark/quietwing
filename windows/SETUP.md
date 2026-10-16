# Portable Windows setup

This backend attaches to an already authenticated ParaDesk child session. It does not provision Remote Desktop, create users, save passwords, reconnect, or log off a native session. A fresh machine therefore has a one-time operator setup step before `quietwing attach` can work.

The tested provider is ParaDesk 1.1.0, source commit `c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435`. The live experiment used its portable release ZIP, SHA-256 `60c0e6502c799de434870647c77e736401e9c18841ee996fd54ab5d0b5b76122`, with the thin launcher below. The source pin is recorded in that experiment; its provider directory contains the release, not a Git checkout. The source-build recipe below is reviewed against that pin, but a clean-machine source rebuild and provisioning have not been tested here.

## Prerequisites and the configuration boundary

Use Windows 10 1903+ or Windows 11 Pro, Enterprise, or Education, with .NET Framework 4.8; this implementation was tested on x64 Windows 11. Python 3.11+ runs the companion. Building ParaDesk requires Git and a .NET SDK; restoring its declared NuGet dependencies needs access to their package source. Arm64 and Windows Home are outside this acceptance.

**Do not run upstream `--setup`, its first-run Configure/Repair action, or a bulk installer/Undo command for this minimal setup.** Upstream setup changes the RDP listener, firewall rules, credential delegation/password-prompt policy, service startup, and per-user integration. The companion does not require permission for that bundle merely because child sessions are wanted. Do not use `build.ps1 -Run` or `-Force` against a running provider.

Before enabling anything, run the pinned provider's read-only `--probe --json` and record the result. Its transport prerequisites include a running Terminal Services service, an available RDP listener/client ActiveX component, and child-session support. On the tested machine the listener and service already existed. The only feature change separately approved for that experiment was `WTSEnableChildSessions(true)`; port, policy, firewall configuration, and service settings were left alone. It became usable without a reboot on that machine. That result does not establish that every fresh Windows install will be ready.

If child sessions are disabled, an administrator can separately approve enabling **only that feature**. The relevant public calls are `WTSIsChildSessionsEnabled(out BOOL)` to record the old state and `WTSEnableChildSessions(BOOL)` to change it. Do not execute the change automatically as an attach fallback. If other prerequisites are missing or transport still fails afterward, stop and review those exact requirements with the operator; do not silently open a port, alter policy, restart services, or reboot. [Microsoft child-session API](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsenablechildsessions), [pinned readiness check](https://github.com/sinpoce/ParaDesk/blob/c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435/src/ParaDesk.App/Core/SystemStatus.cs).

## Build into a private directory

Run these manually in a new directory, using existing tools. They do not install a service or configure Windows:

```powershell
$root = Join-Path $env:USERPROFILE 'Experiments\desktop-provider'
New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
git clone https://github.com/sinpoce/ParaDesk.git "$root\source"
git -C "$root\source" checkout --detach c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435
git -C "$root\source" rev-parse HEAD
$env:NUGET_PACKAGES = "$root\nuget"
& "$root\source\build.ps1" -Release
if ($LASTEXITCODE -ne 0) { throw 'Provider build failed' }
New-Item -ItemType Directory "$root\portable", "$root\data" | Out-Null
Copy-Item "$root\source\src\ParaDesk.App\bin\Release\net48\*.exe" "$root\portable"
Copy-Item "$root\source\src\ParaDesk.App\bin\Release\net48\*.dll" "$root\portable"
Copy-Item "$root\source\src\ParaDesk.App\bin\Release\net48\*.config" "$root\portable"
```

[The pinned build script](https://github.com/sinpoce/ParaDesk/blob/c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435/build.ps1) builds without launching unless `-Run` is supplied. Keep this checkout separate from any running provider. The upstream portable release is an alternative; verify its hash and provenance before extracting it into `portable`.

ParaDesk has no public data-directory switch at this version. To reproduce the experiment's private data directory, save this as `$root\PortableLauncher.cs` and compile it below. It redirects the pinned private `_dataDir` field before upstream initialization; it needs re-review for another version. The guard rejects broad setup/child-agent CLI verbs and refuses tray startup when the transport is unready. It is not a security sandbox for upstream UI actions: do not select Configure/Repair/Undo in the UI. Upstream startup may also repair pre-existing ParaDesk startup registrations, so an existing installation needs separate review.

```csharp
using System;
using System.IO;
using System.Reflection;
internal static class PortableLauncher {
 [STAThread] private static int Main(string[] args) {
  string dir=Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
  string root=Directory.GetParent(dir).FullName;
  try {
   string verb=args.Length==0 ? "" : args[0].ToLowerInvariant();
   string[] allowed={"--minimized","--status","--start","--view-only",
                     "--screenshot","--probe","--version","--help","--quit"};
   if(Array.IndexOf(allowed,verb)<0) throw new InvalidOperationException("Unsupported portable command");
   Assembly app=Assembly.LoadFrom(Path.Combine(dir,"ParaDesk.exe"));
   BindingFlags flags=BindingFlags.NonPublic|BindingFlags.Static;
   app.GetType("ParaDesk.Core.AppInfo",true).GetField("_dataDir",flags)
      .SetValue(null,Path.Combine(root,"data"));
   if(verb=="--minimized") {
    if(System.Diagnostics.Process.GetCurrentProcess().SessionId==0)
      throw new InvalidOperationException("Start viewer from the logged-in console");
    object report=app.GetType("ParaDesk.Core.SystemStatus",true)
      .GetMethod("Check").Invoke(null,null);
    if(!(bool)report.GetType().GetProperty("ReadyToStart").GetValue(report,null))
      throw new InvalidOperationException("Transport not ready; setup is not automatic");
   }
   return (int)app.GetType("ParaDesk.Program",true).GetMethod("Main",flags)
      .Invoke(null,new object[]{args});
  } catch(Exception ex) {
   File.AppendAllText(Path.Combine(root,"launcher-errors.log"),ex+Environment.NewLine);
   return 1;
  }
 }
}
```

```powershell
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe "/out:$root\portable\ParaDesk.Portable.exe" "$root\PortableLauncher.cs"
if ($LASTEXITCODE -ne 0) { throw 'Launcher build failed' }
Copy-Item "$root\portable\ParaDesk.exe.config" "$root\portable\ParaDesk.Portable.exe.config"
& "$root\portable\ParaDesk.Portable.exe" --probe --json | Out-String
```

## First sign-in and the connected viewer

After readiness is established, launch the viewer **from the user's existing interactive console**, not an SSH session/service:

```powershell
Start-Process "$root\portable\ParaDesk.Portable.exe" -ArgumentList '--minimized'
```

Open its tray UI and configure a windowed profile before starting a child: fixed 1280×720 is the tested size; audio **Mute** (`desktopAudio=2`), clipboard Off, automatic start/reattach Off, keep-awake Off, startup command empty, updates Off, and global hotkeys Off. Leave Windows startup registration off. These are application preferences in the private data directory. Audio changes apply on the next connection, so choose Mute before first sign-in. Do not edit an active user's profile or reconnect it to apply changes without their permission. [Pinned settings fields](https://github.com/sinpoce/ParaDesk/blob/c01b5fa1c434fac74b5cd3ddf8adb0cd3b08d435/src/ParaDesk.App/Core/Settings.cs).

From that same console, start the child and complete any Windows Security prompt **locally**:

```powershell
& "$root\portable\ParaDesk.Portable.exe" --start --wait --json | Out-String
& "$root\portable\ParaDesk.Portable.exe" --status --json | Out-String
```

No password goes into a script, chat, command line, or helper state. This recipe does not save credentials or promise future connections without authentication. A bounded CLI wait may time out while the local prompt remains open; inspect the existing viewer instead of repeatedly restarting it. Same-user startup programs can create their own UAC dialogs in the child. The human must dismiss or handle those locally; the helper refuses a secure/locked desktop.

Keep the viewer **connected and not minimized**. `quietwing attach --hide-viewer` uses `SW_HIDE` while retaining the connection. Closing/detaching/minimizing the RDP viewer made native screen capture/input unavailable in the experiment. Hiding the connected window is a different operation. Native input/capture and a modest D3D11 fixture passed while hidden on this host; this is not a game/performance guarantee.

## Install and use the companion independently

Use the supplied companion wheel in its own venv; no cctl installation is required:

```powershell
python -m venv "$root\helper-venv"
& "$root\helper-venv\Scripts\python.exe" -m pip install --no-index --no-deps C:\path\quietwing-0.4.1-py3-none-any.whl
$helper = "$root\helper-venv\Scripts\quietwing.exe"
$env:DESKHELPER_PARADESK_DATA = "$root\data"
$env:DESKHELPER_STATE_ROOT = "$root\helper-state"
& $helper doctor
$attached = & $helper attach --id work --hide-viewer | ConvertFrom-Json
$generation = $attached.session.generation
& $helper status --id work --expect-generation $generation
& $helper exec --id work --expect-generation $generation -- C:\Windows\System32\cmd.exe /d /q /k
& $helper input --id work --expect-generation $generation --type 'echo hello'
& $helper input --id work --expect-generation $generation --key ENTER
& $helper capture --id work --expect-generation $generation --output "$root\child.png"
& $helper stop --id work --expect-generation $generation
```

The caller needs permission to register Limited Interactive tasks for the already logged-in account. Attach validates the actual console-child relationship; a stale JSON state file alone is insufficient. Runtime worker builds go under the private state cache, outside site-packages. Capture output must be writable by that same user in the child. Browser/singleton apps need a distinct profile/instance so their own IPC cannot reuse a human window.

`status` reports actual child audio endpoints. Exec/input are allowed only while there are zero active/default Core Audio render endpoints and zero WaveOut output devices. No test tone is played. If an output route appears, those actions fail; a saved Mute preference alone never proves silence.

## Cleanup and recovery

Normal `quietwing stop` ends only the helper worker and its job-owned apps, removes its temporary tasks, and leaves the viewer's current visibility unchanged. A viewer hidden by `--hide-viewer` remains hidden. Save work in those apps before stop. The native child and its existing authentication remain alive. A worker crash also closes its owned job and leaves the viewer hidden; follow with stop to clean registrations. If generation changes, obtain a new descriptor explicitly rather than retrying an old action against a replacement.

If the provider locks/disconnects/exits, the companion fails closed and never reconnects. Leave the native session alone until the human is available to restore it and authenticate if needed. Do not guess credentials or repeatedly trigger prompts. `--quit` exits the provider and loses the connection even though the native child may remain; it is not routine helper cleanup.

Full provider teardown is separate and requires the human to save all native-child work and explicitly sign that child out. Only then quit its viewer. If child support was previously disabled and restoring it is explicitly requested, restore the recorded value with `WTSEnableChildSessions(false)`; do not use upstream bulk Undo. A venv/state directory can be deleted after its helpers are stopped, but native-child teardown is not implied by uninstalling this Python package.

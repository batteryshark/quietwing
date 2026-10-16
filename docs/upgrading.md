# Upgrade to 0.4.0

Version 0.3 is QuietWing. The package, Python import, and sole installed command
are `quietwing`. There is no `deskhelper` command alias.

Finish current agent work first. Save/stop owned Mac guests before rebuilding
native helpers. Save Windows/Linux documents before stopping workers. Preserve
the authenticated ParaDesk child; a package upgrade does not require sign-out.

Install the reviewed wheel in a new private environment:

```sh
python3 -m venv /absolute/path/to/quietwing-env
/absolute/path/to/quietwing-env/bin/python -m pip install /path/to/quietwing-0.4.0-py3-none-any.whl
/absolute/path/to/quietwing-env/bin/quietwing --version
```

Change each private cctl target's `command` array to that executable. On Windows
it is `quietwing-env\Scripts\quietwing.exe`. Update imports from
`desktop_session_helper` to `quietwing`, and source invocations of `deskhelper.py`
to `cli.py`. The [examples](../examples/) use the new command only.

Native `DESKHELPER_*` environment names, state/cache paths, ownership markers,
and saved-state files retain their existing names. Leave them in place. Never
clone VM identity files or credentials to make a new guest. IDs and descriptor
schema v1 are unchanged.

Computer-ctrl must include the QuietWing update: the target command default is
now `quietwing`. A changed configuration gets its own controller paths. Retire
old controllers after work is finished, then explicitly start the configured
target. Check status and fresh capture before input.

Version 0.3.1 keeps a hidden Windows viewer hidden during cleanup. The change
applies to newly compiled workers/observers; upgrading the package cannot rewrite
an attachment already running 0.3.0 code. Finish those attachments during a safe
work window before upgrading. Their old cleanup still restores visibility. Keep
the ParaDesk provider and authenticated child running; no sign-out is required.


Version 0.4.0 adds the optional [read-only Mac preview](viewer.md) for Mac VMs and
isolated Linux/Windows desktops over SSH. Install 0.4.0 at both ends for remote
viewing; old helpers fail closed on the frame operation. Existing Windows workers
keep their compiled code until explicitly replaced: save their owned documents,
stop only the helper attachment, upgrade, and attach again with `--hide-viewer`.
Keep the external ParaDesk connection and signed-in child alive. Upgrade never
requires a native sign-out, system settings change or host-control fallback.

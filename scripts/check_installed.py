#!/usr/bin/env python3
"""Check an installed wheel in a fresh cwd, without acquiring a desktop."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PROBE = r'''
import configparser, importlib.metadata, importlib.resources, json, pathlib, subprocess, sys
import quietwing
dist = importlib.metadata.distribution('quietwing')
assert dist.version == quietwing.__version__
assert not dist.requires
entrypoints = {ep.name:ep.value for ep in dist.entry_points if ep.group == 'console_scripts'}
assert entrypoints == {'quietwing':'quietwing.cli:entrypoint'}, entrypoints
root = importlib.resources.files('quietwing')
for name in ['cli.py','CONTRACT.md','session.schema.json','linux/adapter.py','windows/adapter.py','windows/Worker.cs','macos/VMHost.swift','macos/build_vm.py','macos/GuestBridge.swift']:
    assert root.joinpath(name).is_file(), name
command = pathlib.Path(sys.executable).parent / ('quietwing.exe' if sys.platform == 'win32' else 'quietwing')
version = subprocess.run([str(command),'--version'],capture_output=True,text=True,check=True)
value = json.loads(version.stdout)
assert value['ok'] and value['version'] == quietwing.__version__
help = subprocess.run([str(command),'--help'],capture_output=True,text=True,check=True)
assert 'QuietWing' in help.stdout and 'Usage: quietwing' in help.stdout
assert not (command.parent / ('deskhelper.exe' if sys.platform == 'win32' else 'deskhelper')).exists(), 'Unexpected old executable in clean environment'
print(json.dumps({'ok':True,'version':dist.version,'installed_package':str(root),'command':str(command),'native_session_started':False}))
'''


def main():
    # Do not resolve the venv executable symlink: it selects the environment.
    python = str(Path(sys.argv[1]).absolute()) if len(sys.argv) > 1 else sys.executable
    with tempfile.TemporaryDirectory(prefix="quietwing-installed-") as directory:
        result = subprocess.run([python, "-I", "-c", PROBE], cwd=directory, capture_output=True, text=True)
    if result.stderr:
        sys.stderr.write(result.stderr)
    print(result.stdout, end="")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

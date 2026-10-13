#!/usr/bin/env python3
"""Compile only; never launch/install a worker or request permissions."""
import os
import subprocess
from pathlib import Path
import sys
sys.dont_write_bytecode = True
try:
    from .runtime_paths import build_root
except ImportError:
    from runtime_paths import build_root

root = Path(__file__).resolve().parent
build = build_root(create=True)
build.mkdir(exist_ok=True)
cache = build / 'module-cache'
command = ['xcrun', 'swiftc', '-parse-as-library', '-module-cache-path', str(cache),
           *(str(root / p) for p in ('SessionGuard.swift', 'NativeSession.swift', 'Worker.swift')),
           '-o', str(build / 'deskhelper-macos-worker')]
subprocess.run(command, check=True)
print(build / 'deskhelper-macos-worker')

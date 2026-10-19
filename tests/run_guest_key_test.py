#!/usr/bin/env python3
"""Explicit Mac NSEvent-only test: no desktop, VM, or event posting."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'macos/VMHost.swift').read_text()
with tempfile.TemporaryDirectory(prefix='quietwing-keys-') as folder:
    folder = Path(folder)
    swift = folder / 'Keys.swift'
    swift.write_text('import AppKit\nimport Darwin\n'
                     + source[source.index('struct VMFailure:'):source.index('final class QuietPanel:')]
                     + (root / 'tests/native_guest_key.swift').read_text())
    binary = folder / 'key-test'
    subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-module-cache-path', str(folder / 'modules'),
                    str(swift), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

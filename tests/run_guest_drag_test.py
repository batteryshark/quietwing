#!/usr/bin/env python3
"""Explicit Mac source-level NSEvent test. Never launches a VM or posts input."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "macos/VMHost.swift").read_text()
start = source.index("struct VMFailure:")
end = source.index("final class QuietPanel:")
with tempfile.TemporaryDirectory(prefix="quietwing-drag-") as folder:
    folder = Path(folder)
    swift = folder / "Drag.swift"
    swift.write_text("import AppKit\nimport Darwin\n" + source[start:end]
                     + (root / "tests/native_guest_drag.swift").read_text())
    binary = folder / "drag-test"
    subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-module-cache-path", str(folder / "modules"),
                    str(swift), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

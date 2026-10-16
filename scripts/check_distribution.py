#!/usr/bin/env python3
"""Audit release archives for runtime resources, metadata, and private files."""
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import zipfile

REQUIRED_RUNTIME = {
    "__init__.py", "cli.py", "CONTRACT.md", "session.schema.json", "docs/viewer.md",
    "linux/adapter.py", "windows/adapter.py", "windows/Worker.cs", "windows/NativeSupport.cs", "windows/ProviderStatus.cs",
    "macos/adapter.py", "macos/vm_adapter.py", "macos/runtime_paths.py", "macos/build.py",
    "macos/build_vm.py", "macos/viewer.py", "macos/ssh_remote.py", "macos/build_viewer.py", "macos/Viewer.swift", "macos/VMHost.swift", "macos/VMCapture.swift", "macos/GuestBridge.swift",
    "macos/SessionGuard.swift", "macos/Worker.swift", "macos/NativeSession.swift",
    "macos/VMProbe.swift", "macos/VMProbe.entitlements", "macos/guest_bootstrap.sh",
}
PRIVATE_PARTS = {".git", ".venv", "state", "evidence", "VM_EVIDENCE", "__pycache__"}
PRIVATE_SUFFIXES = {".pyc", ".pyo", ".ipsw", ".img", ".qcow2", ".vzstate", ".vhd", ".vhdx", ".vmdk", ".hdd", ".pvm", ".sock", ".png", ".jpg", ".jpeg", ".wav", ".mp4", ".exe", ".dll"}
PRIVATE_FILES = {"guest-credential.json", "VERIFICATION.json", "RESULTS.md", "VM_RESULTS.md", ".env"}
SECRETS = [re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"), re.compile(rb"sk-[A-Za-z0-9_-]{24,}"), re.compile(rb"-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----")]


def safe_member(name, data):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe archive path: {name}")
    if (PRIVATE_PARTS.intersection(path.parts) or path.name in PRIVATE_FILES
            or path.name.startswith(".env") or any(part.startswith(".venv") for part in path.parts)
            or path.suffix.lower() in PRIVATE_SUFFIXES):
        raise ValueError(f"Private/generated archive entry: {name}")
    if len(data) > 2 * 1024 * 1024:
        raise ValueError(f"Unexpected large archive entry: {name}")
    if any(pattern.search(data) for pattern in SECRETS):
        raise ValueError(f"Credential pattern in archive entry: {name}")


def contents(path):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate wheel entries")
            return {name: archive.read(name) for name in names if not name.endswith("/")}
    with tarfile.open(path, "r:gz") as archive:
        entries = {}
        for member in archive:
            if member.isdir():
                continue
            if not member.isfile() or member.name in entries:
                raise ValueError(f"Unexpected or duplicate source member: {member.name}")
            entries[member.name] = archive.extractfile(member).read()
        return entries


def audit(path):
    entries = contents(path)
    if sum(map(len, entries.values())) > 10 * 1024 * 1024:
        raise ValueError("Unexpected distribution size")
    for name, data in entries.items():
        safe_member(name, data)
    if path.suffix == ".whl":
        required = {"quietwing/" + name for name in REQUIRED_RUNTIME}
        assert required <= entries.keys(), f"Missing wheel resources: {sorted(required - entries.keys())}"
        assert not any(name.startswith("desktop_session_helper/") for name in entries)
        meta_name = next(name for name in entries if name.endswith(".dist-info/METADATA"))
        metadata = BytesParser().parsebytes(entries[meta_name])
        assert metadata["Name"] == "quietwing"
        assert metadata["License-Expression"] == "MIT"
        assert not metadata.get_all("Requires-Dist"), "Unexpected runtime dependency"
        ep_name = next(name for name in entries if name.endswith(".dist-info/entry_points.txt"))
        import configparser
        parser = configparser.ConfigParser()
        parser.read_string(entries[ep_name].decode())
        assert dict(parser["console_scripts"]) == {"quietwing": "quietwing.cli:entrypoint"}, "Only quietwing may be installed"
        assert any(name.endswith("/LICENSE") for name in entries), "Missing license"
    else:
        prefixes = {name.split("/", 1)[0] for name in entries}
        assert len(prefixes) == 1
        prefix = next(iter(prefixes)) + "/"
        expected = {"README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "THIRD_PARTY.md", "docs/daily-use.md", "docs/upgrading.md", "docs/releases.md", "docs/status.md", "examples/macos.toml", "examples/linux.toml", "examples/windows.toml", "scripts/check.py", "scripts/check_distribution.py", "scripts/check_installed.py", "tests/test_dispatcher.py", "windows/test_adapter.py", "windows/test_provider.py", "windows/test_viewer.py", "macos/test_generation.py", "macos/test_viewer.py", "macos/test_remote_viewer.py", "macos/test_viewer_follow.py", "tests/viewer_follow_acceptance.py", "docs/future-work.md", "linux/test_readonly_frames.py", "tests/native_viewer.swift", "docs/viewer.md"}
        assert {prefix + name for name in expected} <= entries.keys(), "Incomplete source distribution"
        assert prefix + "deskhelper.py" not in entries, "Old command source in release"
    return {"file": path.name, "entries": len(entries), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    paths = sorted([*directory.glob("*.whl"), *directory.glob("*.tar.gz")])
    assert len(paths) == 2 and sum(p.suffix == ".whl" for p in paths) == 1, "Use a fresh directory containing one wheel and one sdist"
    reports = [audit(path) for path in paths]
    (directory / "SHA256SUMS").write_text("".join(f"{item['sha256']}  {item['file']}\n" for item in reports))
    print(json.dumps({"ok": True, "archives": reports}, indent=2))


if __name__ == "__main__":
    main()

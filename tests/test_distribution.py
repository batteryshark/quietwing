"""Reject unsafe release content, using synthetic archives and payloads."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("distribution_audit", Path(__file__).resolve().parents[1] / "scripts/check_distribution.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class DistributionSafety(unittest.TestCase):
    def test_reject_private_files_and_traversal(self):
        for name in ["quietwing/evidence/capture.json", "quietwing/VM_EVIDENCE/run.txt", "quietwing/guest-credential.json", "quietwing/session.vzstate", "quietwing/screen.png", "quietwing/.env.local", "quietwing/.venv-test/config", "../outside.py", "/absolute.py"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                audit.safe_member(name, b"test")

    def test_reject_private_key(self):
        with self.assertRaises(ValueError):
            audit.safe_member("quietwing/settings.txt", b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----")

    def test_permit_native_source(self):
        audit.safe_member("quietwing/windows/Worker.cs", b"// native source")
        audit.safe_member("quietwing/macos/VMHost.swift", b"// native source")

    def test_incomplete_wheel_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quietwing-0.3.0-py3-none-any.whl"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("quietwing/__init__.py", "")
            with self.assertRaises(AssertionError):
                audit.audit(path)

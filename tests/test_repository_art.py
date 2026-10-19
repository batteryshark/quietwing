"""Pure repository-art policy checks; no adapter imports or native operations."""
import ast
import fnmatch
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ART = {
    "assets/workstack-mark.png",
    "assets/workstack-mark-full.png",
    "assets/workstack-mark-32.png",
}


def definitions(path, names, namespace):
    """Load only named policy definitions, without executing a module's imports."""
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if (
        isinstance(node, ast.FunctionDef) and node.name in names
    ) or (
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)
    )]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)


class RepositoryArtwork(unittest.TestCase):
    def setUp(self):
        self.archive = {"PurePosixPath": PurePosixPath, "re": re}
        definitions(ROOT / "scripts/check_distribution.py", {
            "PRIVATE_PARTS", "PRIVATE_SUFFIXES", "PRIVATE_FILES", "SECRETS", "safe_member",
        }, self.archive)
        self.repository = {}
        definitions(ROOT / "scripts/check.py", {
            "REPOSITORY_ART", "repository_member",
        }, self.repository)
        module = types.ModuleType("check_distribution")
        module.safe_member = self.archive["safe_member"]
        self.modules = patch.dict(sys.modules, {"check_distribution": module})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_exact_repository_art_only(self):
        self.assertEqual(self.repository["REPOSITORY_ART"], ART)
        for name in ART:
            self.repository["repository_member"](name, (ROOT / name).read_bytes())
        for name in ["assets/other.png", "private.png", "assets/nested/workstack-mark.png",
                     "assets/../assets/workstack-mark.png"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.repository["repository_member"](name, b"image")

    def test_archive_guards_unchanged(self):
        for name, data in [
            *((name, b"image") for name in ART),
            ("quietwing/evidence/private.json", b"{}"),
            ("quietwing/large.txt", b"x" * (2 * 1024 * 1024 + 1)),
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.archive["safe_member"](name, data)
        self.archive["safe_member"]("quietwing/windows/Worker.cs", b"// source")

    def test_art_excluded_from_package_inputs(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        setup = project["tool"]["setuptools"]
        self.assertIs(setup["include-package-data"], False)
        for patterns in setup["package-data"].values():
            for pattern in patterns:
                self.assertFalse(any(fnmatch.fnmatchcase(name, pattern) for name in ART))
        lines = (ROOT / "MANIFEST.in").read_text().splitlines()
        self.assertIn("prune assets", lines)
        for line in lines:
            words = line.split()
            if not words or words[0].startswith("#"):
                continue
            if words[0] in {"include", "global-include"}:
                for pattern in words[1:]:
                    self.assertFalse(any(fnmatch.fnmatchcase(name, pattern) for name in ART))
            if words[0] in {"graft", "recursive-include"}:
                self.assertNotIn(words[1].rstrip("/"), {".", "*", "assets"})
                self.assertFalse(fnmatch.fnmatchcase("assets", words[1]))

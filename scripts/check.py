#!/usr/bin/env python3
"""Portable repository checks. Never acquire or control a desktop."""
import ast
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"Missing {name} in {path.name}")


def repository_checks():
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text())
    project = meta["project"]
    assert project["name"] == "quietwing"
    assert project["scripts"] == {"quietwing": "quietwing.cli:entrypoint"}, "Exactly one CLI; no aliases"
    assert project["version"] == constant(ROOT / "__init__.py", "__version__") == constant(ROOT / "cli.py", "VERSION")
    assert not project.get("dependencies"), "Runtime package must remain dependency-free"
    if (ROOT / ".git").exists():
        from check_distribution import safe_member
        files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
        for name in filter(None, files):
            path = ROOT / name
            if path.is_file():
                safe_member(name, path.read_bytes())
    for path in (ROOT / "examples").glob("*.toml"):
        data = tomllib.loads(path.read_text())
        for target in data["sessions"].values():
            assert Path(target["command"][0].replace("\\", "/")).name in ("quietwing", "quietwing.exe")
    docs = [ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "THIRD_PARTY.md")]
    docs += list((ROOT / "docs").glob("*.md"))
    for path in docs:
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", path.read_text(encoding="utf-8")):
            if ":" in target or target.startswith("#"):
                continue
            file = unquote(target.split("#", 1)[0])
            assert (path.parent / file).exists(), f"Broken local link: {path.relative_to(ROOT)} -> {file}"
    print("Repository metadata, canonical CLI, example configs, and guide links passed.", flush=True)


def main():
    repository_checks()
    suites = [("tests", "test_*.py"), ("windows", "test_*.py")]
    if sys.platform != "win32":
        suites.extend([("macos", "test_generation.py"), ("macos", "test_viewer.py")])
    for directory, pattern in suites:
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", directory, "-p", pattern], cwd=ROOT, check=True)
    print("Portable checks passed; no native session was started.")


if __name__ == "__main__":
    main()

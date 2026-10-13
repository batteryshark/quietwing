"""Writable macOS assets live in a user cache, never installed package resources."""
import os
import stat
from pathlib import Path


def build_root(create=False):
    base = Path(os.environ.get('DESKHELPER_BUILD_ROOT', str(Path.home() / 'Library/Caches/desktop-session-helper'))).expanduser()
    if not base.is_absolute():
        raise ValueError('DESKHELPER_BUILD_ROOT must be an absolute path')
    path = base / 'macos'
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError('Mac build cache must be private, user-owned and not a symlink')
    return path

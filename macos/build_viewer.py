"""Build only the read-only window; never rebuild or launch a VM owner."""
import plistlib, shutil, subprocess, uuid
from pathlib import Path
try:
    from .viewer import app_path, private_dir, build_root, lock
except ImportError:
    from viewer import app_path, private_dir, build_root, lock

def build():
    cache = build_root(create=True)
    with lock(cache / 'viewer-build.lock'):
        return build_locked()

def build_locked():
    target = app_path()
    if target.is_dir(): return target
    private_dir(target.parent, True)
    temporary = target.with_name('Viewer-' + uuid.uuid4().hex + '.app')
    binary = temporary / 'Contents/MacOS/QuietWingViewer'
    binary.parent.mkdir(parents=True, mode=0o700)
    try:
        subprocess.run(['xcrun', 'swiftc', '-parse-as-library', '-module-cache-path', str(target.parents[2] / 'module-cache'),
            str(Path(__file__).with_name('Viewer.swift')), '-o', str(binary)], check=True)
        info = {'CFBundleIdentifier': 'org.quietwing.viewer', 'CFBundleName': 'QuietWing Viewer',
            'CFBundleExecutable': 'QuietWingViewer', 'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1',
            'LSUIElement': True, 'NSHighResolutionCapable': True, 'LSMultipleInstancesProhibited': False}
        with (temporary / 'Contents/Info.plist').open('wb') as stream: plistlib.dump(info, stream)
        subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(temporary)], check=True)
        try: temporary.rename(target)
        except FileExistsError:
            shutil.rmtree(temporary)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
    return target

if __name__ == '__main__': print(build())

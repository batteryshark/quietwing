#!/usr/bin/env python3
"""Build/sign owned VM components. No download, install, launch or host settings."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
try:
    from .runtime_paths import build_root
except ImportError:
    from runtime_paths import build_root
import subprocess,plistlib,os,fcntl
root=Path(__file__).resolve().parent
state=Path(os.environ.get('DESKHELPER_STATE_ROOT',str(Path.home()/'.local/state/deskhelper')))/'macos-vm'
# Refuse to overwrite a signed executable belonging to any live VM owner.
for lock in state.glob('*/owner.lock'):
    fd=os.open(lock,os.O_RDWR|os.O_NOFOLLOW)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Save/stop the owned VM before rebuilding its app.')
    finally:os.close(fd)
build=build_root(create=True);app=build/'DeskhelperVM.app';contents=app/'Contents';binary=contents/'MacOS'/'DeskhelperVM'
binary.parent.mkdir(parents=True,exist_ok=True)
for source,target in [('VMHost.swift',binary),('VMCapture.swift',build/'vm-capture'),('GuestBridge.swift',build/'GuestBridge'),('VMProbe.swift',build/'vm-probe')]:
    subprocess.run(['xcrun','swiftc','-parse-as-library','-module-cache-path',str(build/'module-cache'),str(root/source),'-o',str(target)],check=True)
info={'CFBundleIdentifier':'dev.desktop-session-helper.vm','CFBundleName':'Deskhelper VM','CFBundleExecutable':'DeskhelperVM','CFBundlePackageType':'APPL','CFBundleVersion':'1','LSUIElement':True,'NSHighResolutionCapable':True,'LSMultipleInstancesProhibited':False}
with (contents/'Info.plist').open('wb') as f:plistlib.dump(info,f)
for target in [app,build/'vm-probe']:
    subprocess.run(['/usr/bin/codesign','--force','--sign','-','--entitlements',str(root/'VMProbe.entitlements'),str(target)],check=True)
print(app)

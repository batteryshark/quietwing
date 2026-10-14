# Provision a new macOS VM

This one-time workflow requires Apple Silicon and Apple's existing command-line tools. The validated host is macOS 27.0.1 with SDK 27 and Swift 6.4. Earlier hosts/toolchains are untested. The source uses current-process ScreenCaptureKit capture (an API introduced in macOS 14.4) and VM save/restore (macOS 14.0); those API versions are necessary lower bounds, not a claim that this package has been built or accepted on those releases. The build uses the installed compiler's default deployment target. It creates user-owned VM files and a guest-local account/LaunchAgent. It does not create host accounts, enable Sharing, request host TCC, change firewall policy, or reboot the host. The default is 2 vCPU, 4 GiB RAM and a sparse 64 GiB disk. Allow space for the Apple restore download (about 25 GiB for the tested version) plus the guest disk.

Activate the Python environment where the companion is installed. These commands use its `deskhelper` and `python3`. Select a **new** ID, not an existing installed guest:

```sh
export DESKHELPER_VM_ID=mac-agent
# Optional absolute parent directories, before building/provisioning:
# export DESKHELPER_BUILD_ROOT=/your/private/build-cache
# export DESKHELPER_STATE_ROOT=/your/private/state
deskhelper build
deskhelper doctor
```

Build uses `xcrun swiftc` and ad-hoc `codesign`, with no VM manager or admin password. Assets go to `DESKHELPER_BUILD_ROOT/macos`, default `~/Library/Caches/desktop-session-helper/macos`, never installed package resources. Save/stop existing VMs before rebuilding.

## 1. Pin supported Apple metadata and stage the private bridge

This only fetches metadata and copies helper-owned files. It does not download an image or allocate a guest disk. It refuses an existing VM platform; repeating before installation retains the pinned metadata.

```sh
python3 - <<'PY'
import json, os, platform, shutil, subprocess, uuid
from pathlib import Path
from importlib.resources import files
from desktop_session_helper.macos import vm_adapter
from desktop_session_helper.macos.runtime_paths import build_root
os.umask(0o077)
assert platform.machine() == 'arm64', 'Apple Silicon is required'
state = vm_adapter.directory(os.environ['DESKHELPER_VM_ID'], create=True)
assert not (state/'HardwareModel.bin').exists(), 'Existing VM: use normal start/status'
build = build_root()
metadata_path = state/'restore-metadata.json'
if not metadata_path.exists():
    data = json.loads(subprocess.check_output([str(build/'vm-probe'), '--latest-metadata'], text=True))
    assert data['ok'] and data['virtualization_supported']
    metadata_path.write_text(json.dumps(data, indent=2))
restore = json.loads(metadata_path.read_text())['latest_restore_metadata']
assert restore['supported'] and restore['hardware_model_supported']
assert restore['minimum_supported_cpu_count'] <= 2
assert restore['minimum_supported_memory_bytes'] <= 4*1024**3
bridge = state/'bridge'; bridge.mkdir(mode=0o700, exist_ok=True)
if not (bridge/'bridge-id').exists():
    (bridge/'bridge-id').write_text(str(uuid.uuid4()))
shutil.copy2(build/'GuestBridge', bridge/'GuestBridge')
(bridge/'GuestBridge').chmod(0o700)
source = Path(str(files('desktop_session_helper').joinpath('macos')))
shutil.copy2(source/'guest_bootstrap.sh', bridge/'bootstrap.sh')
(bridge/'bootstrap.sh').chmod(0o700)
print(json.dumps({'state':str(state), 'restore':restore}, indent=2))
PY
```

If a future image requires more than 2 vCPU/4 GiB, stop and review the fixed VM configuration. Do not change installed/snapshotted VM hardware casually.

## 2. Download/resume and verify the official image

This accepts only an HTTPS Apple CDN URL supplied by Apple's framework, pins the official CDN SHA256 and length, then resumes/downloads the image. It fails closed if the metadata changes or the checksum header is unavailable. The currently used official header is `x-amz-meta-digest-sha256`.

The download runs in the foreground. If interrupted, ensure that process ended, then rerun this block: curl resumes the existing file. Do not start a second download merely because a controller stopped waiting. A checksum mismatch never creates the verification marker.

```sh
python3 - <<'PY'
import hashlib, json, os, re, shutil, subprocess, time
from urllib.parse import urlparse
from desktop_session_helper.macos import vm_adapter
os.umask(0o077)
state = vm_adapter.directory(os.environ['DESKHELPER_VM_ID'])
assert not (state/'installed.json').exists(), 'Already installed'
url = json.loads((state/'restore-metadata.json').read_text())['latest_restore_metadata']['restore_url']
parsed = urlparse(url)
assert parsed.scheme == 'https' and (parsed.hostname or '').endswith('.cdn-apple.com')
head = subprocess.check_output(['/usr/bin/curl','--fail','--silent','--show-error','--head','--location','--proto','=https','--proto-redir','=https',url], text=True)
headers = {}
for line in head.splitlines():
    if ':' in line:
        key,value = line.split(':',1); headers[key.lower()] = value.strip()
expected = headers.get('x-amz-meta-digest-sha256','').lower()
assert re.fullmatch(r'[0-9a-f]{64}', expected), 'No official SHA256; stop for review'
length = int(headers['content-length'])
pinned = {'url':url,'sha256':expected,'content_length':length}
pin = state/'download.json'
if pin.exists():
    old = json.loads(pin.read_text())
    assert all(old.get(k)==v for k,v in pinned.items()), 'Pinned download metadata differs'
else:
    pin.write_text(json.dumps(pinned,indent=2))
image = state/'Restore.ipsw'
current = image.stat().st_size if image.exists() else 0
assert current <= length
assert shutil.disk_usage(state).free >= (length-current)+64*1024**3, 'Insufficient headroom'
if current < length:
    subprocess.run(['/usr/bin/curl','--fail','--location','--proto','=https','--proto-redir','=https','--continue-at','-','--output',str(image),url], check=True)
image.chmod(0o600)
digest = hashlib.sha256()
with image.open('rb') as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
assert image.stat().st_size == length and digest.hexdigest() == expected, 'Image verification failed'
(state/'restore-verified.json').write_text(json.dumps({'verified':True,'bytes':length,'sha256':expected,'verified_at':time.time()},indent=2))
print('Official restore size and SHA256 verified')
PY
```

## 3. Install and complete guest Setup Assistant

```sh
deskhelper start --id "$DESKHELPER_VM_ID"
deskhelper status --id "$DESKHELPER_VM_ID"
```

First start creates compatible Mac hardware/identifier/auxiliary files, the sparse disk and a persistent owner, then runs Apple's installer. Status exposes `install_fraction`; wait for `phase: running`. Do not relaunch because a command returned while installation continues. The owner lock prevents duplicate disk owners. `installed.json` distinguishes installation from boot/resume. Do not delete partial platform files or force-stop the installer.

The view is intentionally offscreen. Complete Setup Assistant by inspecting **owned guest screenshots** and sending guest-only input. Until the bridge is installed, use the companion directly; cctl waits for generic exec readiness.

```sh
deskhelper capture --id "$DESKHELPER_VM_ID" --output /private/tmp/mac-agent-setup-001.png
# Open the PNG normally. Use a new capture filename each time.
deskhelper input --id "$DESKHELPER_VM_ID" --click 500 600
deskhelper input --id "$DESKHELPER_VM_ID" --type 'Guest account name'
deskhelper input --id "$DESKHELPER_VM_ID" --key enter
```

Coordinates illustrate syntax, not universal targets; use the current image. Choose a US keyboard for bootstrap, create a **guest-local** account, and skip Apple Account/iCloud and host data migration. No existing host/Apple password is needed. Do not put a password in `--type`, shell history or saved source. After focusing the guest password field, use this private stdin path; repeat for its confirmation field:

```sh
python3 - <<'PY'
import getpass, os
from desktop_session_helper.macos import vm_adapter
name = os.environ['DESKHELPER_VM_ID']
status = vm_adapter.request(name, {'op':'status'})
assert status['ok'] and status['session']['phase']=='running'
secret = getpass.getpass('New guest-only password for the focused guest field: ')
result = vm_adapter.request(name, {'op':'input','instance':status['session']['instance'],'text':secret})
secret = None
assert result['ok'], result.get('error',{}).get('code')
print('Submitted to guest field; no credential saved or printed')
PY
```

Before bridge installation, text uses US physical key codes; choose a password representable by that mapping. Guest reboot/crash recovery still presents its own login; this is not an unattended login service. The tested initial baseline did not enable guest FileVault.

## 4. Bootstrap generic exec inside the guest

After reaching Finder, use guest Spotlight to open Terminal. Inspect fresh screenshots at transitions rather than typing into an unready window:

```sh
deskhelper input --id "$DESKHELPER_VM_ID" --key cmd+space
deskhelper input --id "$DESKHELPER_VM_ID" --type Terminal
deskhelper input --id "$DESKHELPER_VM_ID" --key enter
# Once the guest Terminal prompt is visible:
deskhelper input --id "$DESKHELPER_VM_ID" --type "/bin/zsh '/Volumes/My Shared Files/bootstrap.sh'"
deskhelper input --id "$DESKHELPER_VM_ID" --key enter
deskhelper status --id "$DESKHELPER_VM_ID"
```

The script refuses a nonvirtualized context, installs under the **guest** account's `~/Library/Application Support/Deskhelper`, and registers only a **guest** LaunchAgent. Do not execute it on the host. The only share is this VM's private bridge, never home/projects. Fresh guest/owner generations must match before `exec` and `unicode_text` advertise true.

```sh
deskhelper exec --id "$DESKHELPER_VM_ID" -- /usr/bin/open -a TextEdit
deskhelper stop --id "$DESKHELPER_VM_ID"
deskhelper start --id "$DESKHELPER_VM_ID"
```

Verify the same desktop resumes without login, with a new owner `session.generation`. Controller exit leaves the guest running; stop saves memory and exits the owner. After successful install and save/resume acceptance, remove only `Restore.ipsw` to reclaim download space; keep verification metadata, disk, hardware, auxiliary storage, network MAC, bridge and snapshot. The snapshot is encrypted and host/configuration-bound. There are no audio devices, no host clipboard synchronization, and NAT has no forwarded ports.

Apple references: [installation](https://developer.apple.com/documentation/virtualization/installing-macos-on-a-virtual-machine), [macOS VM sample](https://developer.apple.com/documentation/virtualization/running-macos-in-a-virtual-machine-on-apple-silicon), [entitlement](https://developer.apple.com/documentation/virtualization/adding-the-virtualization-entitlement-to-your-project), [guest automount](https://developer.apple.com/documentation/virtualization/vzvirtiofilesystemdeviceconfiguration/macosguestautomounttag).

"""Generation-pinned capture broker; the native window receives image files only."""
from __future__ import annotations
import fcntl, hashlib, json, os, re, stat, subprocess, sys, time, uuid
from contextlib import contextmanager
from pathlib import Path
try:
    from . import vm_adapter as vm, linux_remote
    from .runtime_paths import build_root
except ImportError:
    import vm_adapter as vm
    import linux_remote
    from runtime_paths import build_root

HERE = Path(__file__).resolve().parent
MAX_IMAGE = 16 * 1024 * 1024

class ViewerError(vm.VMError):
    def __init__(self, code, message): self.code, self.message = code, message; super().__init__(message)

def app_path():
    digest = hashlib.sha256((HERE / 'Viewer.swift').read_bytes()).hexdigest()
    return build_root() / 'viewer' / digest / 'QuietWingViewer.app'

def private_dir(path, create=False):
    if create: path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ViewerError('unsafe_viewer_state', 'Viewer state must be private, owned and not a symlink')
    return path

def state_root(name, create=False, source=None):
    pattern = r'[A-Za-z0-9][A-Za-z0-9_.-]{0,47}' if source else vm.NAME.pattern
    if not re.fullmatch(pattern, name): raise ViewerError('invalid_id', 'Invalid session ID')
    base = Path(os.environ.get('DESKHELPER_STATE_ROOT', str(Path.home() / '.local/state/deskhelper')))
    if not base.is_absolute(): raise ViewerError('unsafe_viewer_state', 'State root must be absolute')
    if not create and not base.exists(): return None
    if create: base.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = base.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o022:
        raise ViewerError('unsafe_viewer_state', 'State parent must be owned, not a symlink or writable by others')
    parts=['viewers','macos-vm',name]
    if source:
        linux_remote.validate(source)
        digest=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
        parts=['viewers','linux-ssh',digest,name]
    for part in parts:
        base = base / part
        if not create and not base.exists(): return None
        private_dir(base, create)
    return base

def read_file(path, limit=65536):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > limit:
            raise ViewerError('unsafe_viewer_state', 'Viewer file must be a bounded private owned regular file')
        data = stream.read(limit + 1)
        if len(data) > limit: raise ViewerError('unsafe_viewer_state', 'Viewer file exceeds its limit')
        return data

def read_json(path): return json.loads(read_file(path))

def write_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream: json.dump(value, stream)
        temporary.replace(path)
    finally: temporary.unlink(missing_ok=True)

@contextmanager
def lock(path, blocking=True):
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ViewerError('unsafe_viewer_state', 'Unsafe viewer lock')
        fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield
    finally: os.close(fd)

def binding(root):
    try: value = read_json(root / 'active.json')
    except FileNotFoundError: return None
    token = value.get('token', '')
    if not re.fullmatch('[a-f0-9]{32}', token) or value.get('id') != root.name:
        raise ViewerError('unsafe_viewer_state', 'Invalid viewer binding')
    run = private_dir(root / token)
    return value, run

def alive(run):
    try:
        with lock(run / 'broker.lock', False): return False
    except BlockingIOError: return True

def snapshot(root):
    item = binding(root)
    if item is None: return {'state': 'closed', 'readOnly': True}
    info, run = item
    try: value = read_json(run / 'state.json')
    except FileNotFoundError: value = {'state': 'starting'}
    value.update(id=info['id'], generation=info['generation'], readOnly=True, viewerRun=str(run), brokerAlive=alive(run))
    try: value['window'] = read_json(run / 'window.json')
    except FileNotFoundError: pass
    if not value['brokerAlive']: value['state'] = 'closed'
    if (run / 'window-closed.json').exists() and 'window' in value:
        value['window'].update(visible=False, imageAvailable=False, closed=True)
    return value

def require_generation(response, info):
    s = response.get('session', {})
    if not response.get('ok'):
        error = response.get('error', {})
        raise ViewerError('generation_changed' if error.get('code') == 'instance_changed' else error.get('code', 'viewer_capture_failed'), error.get('message', 'Session unavailable'))
    if not isinstance(info['generation'], str) or not info['generation'] or not isinstance(info['ownerPid'], int) or info['ownerPid'] <= 0:
        raise ViewerError('session_unavailable', 'No live VM generation is available; start it explicitly first')
    if s.get('instance') != info['generation'] or s.get('pid') != info['ownerPid']:
        raise ViewerError('generation_changed', 'Session identity changed; close and reopen the viewer')
    if s.get('phase') != 'running' or not s.get('window_offscreen') or s.get('window_key') or s.get('window_main'):
        raise ViewerError('session_unavailable', 'The isolated VM view is not running offscreen')
    return response

def capture_frame(info, run):
    incoming = run / ('incoming-' + uuid.uuid4().hex + '.png')
    try:
        if info.get('source'):
            data,details=linux_remote.frame(info['source'],info['id'],info['generation'])
            fd=os.open(incoming,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(data)
            incoming.replace(run/'frame.png')
            return details
        response = require_generation(vm.request(info['id'], {'op': 'capture', 'instance': info['generation'], 'output': str(incoming)}, timeout=10), info)
        result = response.get('result', {})
        if result.get('path') != str(incoming) or result.get('only_owned_guest_view') is not True:
            raise ViewerError('invalid_capture', 'Capture did not identify the isolated guest image')
        data = read_file(incoming, MAX_IMAGE)
        if not data.startswith(b'\x89PNG\r\n\x1a\n'): raise ViewerError('invalid_capture', 'Capture is not a PNG')
        incoming.replace(run / 'frame.png')
        return {'capturedAt': result['captured_at'], 'width': result['width'], 'height': result['height']}
    except Exception:
        (run / 'frame.png').unlink(missing_ok=True)
        raise
    finally: incoming.unlink(missing_ok=True)

def close_viewer(root, expected=None):
    item = binding(root)
    if item is None: return {'state': 'closed', 'readOnly': True}
    info, run = item
    if expected is not None and info['generation'] != expected:
        raise ViewerError('generation_changed', 'Viewer belongs to a different generation')
    write_json(run / 'close.json', {'close': True})
    deadline = time.monotonic() + 12
    def pending():
        return alive(run) or ((run / 'window.json').exists() and not (run / 'window-closed.json').exists())
    while pending() and time.monotonic() < deadline: time.sleep(.1)
    if pending(): raise ViewerError('viewer_close_pending', 'Viewer is closing; guest is unaffected. Inspect viewer status.')
    # Retain only metadata, never a last guest image after closing.
    (run / 'frame.png').unlink(missing_ok=True)
    return snapshot(root)

def open_viewer(root, name, expected=None, source=None):
    if source:
        current=linux_remote.call(source,'status',name,expected)
        info={'id':name,'generation':current['session']['generation'],'source':source}
        return launch_viewer(root,info)

    payload = {'op': 'status'}
    if expected is not None: payload['instance'] = expected
    current = vm.request(name, payload)
    if not current.get('ok'):
        error = current.get('error', {})
        raise ViewerError(error.get('code', 'session_unavailable'), error.get('message', 'Session unavailable'))
    session = current['session']
    info = {'id': name, 'generation': session.get('instance'), 'ownerPid': session.get('pid')}
    require_generation(current, info)
    return launch_viewer(root,info)

def launch_viewer(root,info):
    name=info['id']
    existing = binding(root)
    if existing and alive(existing[1]):
        if existing[0]['generation'] != info['generation']:
            raise ViewerError('viewer_generation_changed', 'Close the previous viewer before viewing the replacement session')
        return snapshot(root)
    app = app_path()
    if not app.is_dir(): raise ViewerError('viewer_not_built', 'Run quietwing build --viewer once; viewing never builds or starts a VM')
    info['token'] = uuid.uuid4().hex
    run = private_dir(root / info['token'], True)
    write_json(root / 'active.json', info)
    write_json(run / 'label.json', {'id': name + (' @ ' + info['source']['host'] if info.get('source') else '')})
    fd = os.open(run / 'broker.log', os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'ab') as log:
        process = subprocess.Popen([sys.executable, str(HERE / 'viewer.py'), '--broker-root', str(root), info['token']],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if (run / 'window.json').exists():
            value = snapshot(root)
            if value['brokerAlive']: return value
        if process.poll() is not None: break
        time.sleep(.1)
    write_json(run / 'close.json', {'close': True})
    raise ViewerError('viewer_launch_failed', 'Read-only viewer did not become ready; guest was not changed. Inspect viewer status.')

def command(args):
    if args.backend != 'vm': raise ViewerError('viewer_unsupported', 'Viewer currently supports the Mac VM backend only')
    source = linux_remote.target(args.host,args.remote_command,args.remote_state_root) if args.host else None
    root = state_root(args.id, not (args.viewer_status or args.close_viewer), source)
    if root is None: value = {'state': 'closed', 'readOnly': True}
    else:
        with lock(root / 'lifecycle.lock'):
            if args.viewer_status: value = snapshot(root)
            elif args.close_viewer: value = close_viewer(root, args.expect_generation)
            else: value = open_viewer(root, args.id, args.expect_generation, source)
    return {'ok': True, 'platform': 'macos', 'result': {'viewer': value}}

def broker(name, token, root=None):
    root = private_dir(root) if root is not None else state_root(name)
    item = binding(root)
    if item is None or item[0]['token'] != token: raise ViewerError('viewer_changed', 'Viewer launch binding changed')
    info, run = item
    with lock(run / 'broker.lock', False):
        state = {'state': 'starting', 'frames': 0, 'readOnly': True, 'heartbeat': time.time()}
        def publish():
            state['heartbeat'] = time.time();write_json(run / 'state.json', state)
        publish()
        try:
            subprocess.run(['/usr/bin/open', '-g', '-n', str(app_path()), '--args', '--run-root', str(run)],
                capture_output=True, check=True, timeout=10)
            while not (run / 'close.json').exists():
                began = time.monotonic()
                if state['state'] in ('starting', 'watching', 'waiting'):
                    try:
                        state.update(capture_frame(info, run), state='watching', frames=state['frames'] + 1)
                        state.pop('errorCode',None);state.pop('message',None)
                    except (OSError, vm.VMError, ValueError, KeyError) as error:
                        (run / 'frame.png').unlink(missing_ok=True)
                        code=getattr(error,'code','session_unavailable')
                        state.update(state='waiting' if code=='SESSION_BUSY' else 'ended',
                            message='Waiting for the pinned session' if code=='SESSION_BUSY' else 'Session ended or unavailable. Close and reopen to view it again.', errorCode=code)
                publish()
                while time.monotonic() - began < 1 and not (run / 'close.json').exists(): time.sleep(.1)
        finally:
            write_json(run / 'close.json', {'close': True})
            (run / 'frame.png').unlink(missing_ok=True)
            state.update(state='closed');publish()

if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] != '--broker-root': raise SystemExit(2)
    try: broker(Path(sys.argv[2]).name, sys.argv[3], Path(sys.argv[2]))
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr);raise SystemExit(1)

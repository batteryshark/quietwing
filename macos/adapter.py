#!/usr/bin/env python3
"""Mac CLI adapter. Never redirects operations to the host's console desktop."""
import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
import sys
sys.dont_write_bytecode = True
try:
    from .runtime_paths import build_root
except ImportError:
    from runtime_paths import build_root

ROOT = Path(__file__).resolve().parent
WORKER = build_root() / 'deskhelper-macos-worker'
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')


class Failure(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Failure('invalid_arguments', message)


def run_worker(request):
    if not WORKER.is_file():
        raise Failure('worker_not_built', 'Run python3 macos/build.py once; doctor never builds or installs automatically.')
    try:
        result = subprocess.run([str(WORKER)], input=json.dumps(request) + '\n',
                                capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        raise Failure('worker_timeout', 'Worker timed out; no host-desktop fallback was attempted.')
    if result.returncode:
        raise Failure('worker_failed', 'Native worker exited unsuccessfully; no success inferred.')
    try:
        response = json.loads(result.stdout)
    except ValueError:
        raise Failure('invalid_worker_response', 'Native worker did not return one JSON object.')
    if not isinstance(response, dict) or type(response.get('ok')) is not bool or response.get('platform') != 'macos':
        raise Failure('invalid_worker_response', 'Native worker returned an invalid envelope.')
    return response


def state_root(create=False):
    root = Path(os.environ.get('DESKHELPER_STATE_ROOT', str(Path.home() / '.local/state/deskhelper'))) / 'macos'
    if create:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.exists():
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise Failure('unsafe_state_directory', 'Mac state must be a private, owned directory without symlinks.')
    return root


def read_binding(name):
    path = state_root() / (name + '.json')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        raise Failure('not_attached', 'No binding exists. Attach explicitly from the dedicated non-console GUI context.')
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise Failure('unsafe_binding', 'Binding must be an owned private regular file.')
        value = json.load(stream)
    if (value.get('id') != name or value.get('uid') != os.getuid()
            or type(value.get('session_id')) is not int or value['session_id'] <= 0):
        raise Failure('invalid_binding', 'Binding identity is invalid for this caller.')
    return value, path


def save_binding(name, uid, session_id):
    path = state_root(create=True) / (name + '.json')
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise Failure('already_attached', 'Binding already exists; inspect status or detach it before reattaching.')
    with os.fdopen(fd, 'w') as stream:
        json.dump({'id': name, 'uid': uid, 'session_id': session_id, 'owns_os_login': False}, stream)


def parse(argv):
    parser = Parser(description='Guarded Mac separate-user adapter; setup and live acceptance are incomplete.')
    parser.add_argument('command', choices=['doctor', 'start', 'attach', 'status', 'exec', 'capture', 'input', 'stop', 'view'])
    parser.add_argument('--id')
    parser.add_argument('--expect-generation', help='Require the exact live VM owner generation; never retarget a replacement')
    parser.add_argument('--backend', choices=['vm','native'], default='vm')
    parser.add_argument('--uid', type=int, help='Explicit dedicated UID for attach; never the console UID')
    parser.add_argument('--session-id', type=int, help='Explicit graphical security session ID for attach')
    parser.add_argument('--output')
    parser.add_argument('--window-id', type=int)
    parser.add_argument('--display-id', type=int)
    parser.add_argument('--cwd')
    parser.add_argument('--host', help='Show an isolated Linux or Windows desktop over existing SSH')
    parser.add_argument('--ssh-identity', help='Absolute path to an existing local SSH key; no configuration change')
    parser.add_argument('--remote-platform', choices=['linux','windows'], default='linux', help='Remote OS; default linux for existing commands')
    parser.add_argument('--remote-command', default='quietwing', help='One remote QuietWing executable path')
    parser.add_argument('--remote-state-root', help='Private remote session state root')
    viewer = parser.add_mutually_exclusive_group()
    viewer.add_argument('--close', dest='close_viewer', action='store_true', help='Close only the read-only viewer')
    viewer.add_argument('--status', dest='viewer_status', action='store_true', help='Inspect only viewer state')
    viewer.add_argument('--follow', action='store_true', help='Wait for and follow verified attachments on the same SSH target; never acquire a session')
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--type', dest='text')
    inputs.add_argument('--key')
    parser.add_argument('--hold-ms', type=int, default=0, help='Bounded guest key/chord hold, 1–5000 ms; zero is a tap')
    inputs.add_argument('--click', nargs=2, type=float)
    inputs.add_argument('--move', nargs=2, type=float)
    inputs.add_argument('--drag', nargs=4, type=float, metavar=('X0', 'Y0', 'X1', 'Y1'), help='Guest-only bounded press, move and release (VM backend)')
    parser.add_argument('--button', type=int, choices=[1, 2, 3], default=1)
    normalized = list(argv)
    executable = []
    if normalized and normalized[0] == 'exec' and '--' in normalized:
        i = normalized.index('--')
        executable, normalized = normalized[i + 1:], normalized[:i]
    # argparse can treat a literal "--" specially even after --type= on some
    # bundled Python versions. Parse a harmless placeholder and restore the data.
    literal_text = None
    has_literal_text = False
    if normalized and normalized[0] == 'input':
        i = 1
        while i < len(normalized):
            if normalized[i] == '--type':
                if i + 1 >= len(normalized):
                    raise Failure('invalid_arguments', '--type requires a value')
                literal_text, has_literal_text = normalized[i + 1], True
                normalized[i:i + 2] = ['--type=DESKHELPER_LITERAL']
            elif normalized[i].startswith('--type='):
                literal_text, has_literal_text = normalized[i][7:], True
                normalized[i] = '--type=DESKHELPER_LITERAL'
            i += 1
    args = parser.parse_args(normalized)
    if has_literal_text:
        args.text = literal_text
    args.argv = executable
    if not 0 <= args.hold_ms <= 5000 or (args.hold_ms and (args.command != 'input' or args.backend != 'vm' or args.key is None)):
        raise Failure('invalid_arguments', '--hold-ms requires a VM input key and 0–5000 ms')
    if args.drag is not None and (args.command != 'input' or args.backend != 'vm'):
        raise Failure('invalid_arguments', '--drag requires input with the VM backend')
    if args.command != 'view' and (args.close_viewer or args.viewer_status or args.follow or args.host or args.remote_command != 'quietwing' or args.remote_state_root or args.remote_platform != 'linux' or args.ssh_identity):
        raise Failure('invalid_arguments', '--close/--status/--follow are view options only')
    if not args.host and (args.remote_command != 'quietwing' or args.remote_state_root or args.remote_platform != 'linux' or args.ssh_identity):
        raise Failure('invalid_arguments', 'Remote options require view --host')
    if args.follow and (not args.host or args.expect_generation is not None):
        raise Failure('invalid_arguments', '--follow requires view --host and cannot be combined with --expect-generation')
    if args.command == 'view' and args.backend != 'vm':
        raise Failure('viewer_unsupported', 'Read-only viewing supports only the Mac VM backend')
    if args.command != 'doctor' and (not args.id or not (re.fullmatch(r'[A-Za-z0-9_-]{1,64}' if args.remote_platform=='windows' else r'[A-Za-z0-9][A-Za-z0-9_.-]{0,47}',args.id) if args.host else NAME.fullmatch(args.id))):
        raise Failure('invalid_id', 'Use a 1–64 character session ID containing letters, digits, underscore or hyphen.')
    if args.expect_generation is not None:
        if args.command in ('doctor','start') or not args.expect_generation or len(args.expect_generation)>256:
            raise Failure('invalid_arguments', '--expect-generation requires a nonempty token on a session operation other than start')
        if args.backend != 'vm':
            raise Failure('generation_unsupported', 'Native backend has no verified process generation; use the VM backend')
    return args


def main(argv):
    try:
        args = parse(argv)
        if sys.platform != 'darwin':
            raise Failure('unsupported_platform', 'This adapter requires macOS.')
        if args.backend == 'vm':
            if __package__:
                from . import vm_adapter
            else:
                import vm_adapter
            try:
                if args.command == 'view':
                    if __package__:
                        from . import viewer
                    else:
                        import viewer
                    response = viewer.command(args)
                else:
                    response = vm_adapter.command(args)
            except (vm_adapter.VMError, OSError, ValueError, subprocess.SubprocessError) as exc:
                raise Failure(getattr(exc, 'code', 'vm_backend_error'), str(exc))
        elif args.command == 'doctor':
            response = run_worker({'op': 'doctor'})
            response['result']['native_setup_document'] = str(ROOT / 'SETUP.md')
            response['result']['vm_tradeoff_document'] = str(ROOT / 'NATIVE_OR_VM.md')
        elif args.command == 'start':
            response = run_worker({'op': 'start'})
        elif args.command == 'attach':
            if args.uid is None or args.session_id is None or not 500 <= args.uid <= 4294967295 or not 0 < args.session_id <= 4294967295:
                raise Failure('explicit_session_binding_required', 'Attach needs --uid and --session-id from doctor in the dedicated GUI context.')
            response = run_worker({'op': 'attach', 'expected_uid': args.uid, 'expected_session_id': args.session_id})
            if response['ok']:
                save_binding(args.id, args.uid, args.session_id)
                response['result']['id'] = args.id
        else:
            binding, path = read_binding(args.id)
            request = {'op': args.command, 'expected_uid': binding['uid'], 'expected_session_id': binding['session_id']}
            if args.command == 'stop':
                # Stateless adapter has never launched children: stop detaches only this binding.
                path.unlink()
                response = {'ok': True, 'platform': 'macos', 'result': {'binding_removed': args.id, 'os_login_retained': True, 'processes_stopped': []}}
            else:
                if args.command == 'exec':
                    if not args.argv:
                        raise Failure('invalid_arguments', 'exec needs -- PROGRAM ARG...')
                    request.update(argv=args.argv, cwd=args.cwd)
                elif args.command == 'capture':
                    if not args.output:
                        raise Failure('invalid_arguments', 'capture needs --output PATH')
                    request['output'] = str(Path(args.output).absolute())
                    if args.window_id is not None:
                        request['window_id'] = args.window_id
                    if args.display_id is not None:
                        request['display_id'] = args.display_id
                elif args.command == 'input':
                    if all(getattr(args, k) is None for k in ('text', 'key', 'click', 'move')):
                        raise Failure('invalid_arguments', 'input needs --type, --key, --click or --move')
                    request.update({k: getattr(args, k) for k in ('text', 'key', 'click', 'move') if getattr(args, k) is not None})
                    request['button'] = args.button
                response = run_worker(request)
        if args.id and isinstance(response.get('session'), dict):
            response['session']['id'] = args.id
        print(json.dumps(response, ensure_ascii=False))
        return 0 if response['ok'] else 1
    except Failure as exc:
        print(json.dumps({'ok': False, 'platform': 'macos', 'error': {'code': exc.code, 'message': exc.message}}))
        return 1
    except (OSError, ValueError) as exc:
        print(json.dumps({'ok': False, 'platform': 'macos', 'error': {'code': 'adapter_error', 'message': str(exc)}}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

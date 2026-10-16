#!/usr/bin/env python3
"""Dispatch to an OS-local session adapter; never fall back to the host desktop."""
import json
import os
import subprocess
import sys
from pathlib import Path

VERSION = '0.4.1.dev0'
PLATFORMS = {'linux': 'linux', 'win32': 'windows', 'darwin': 'macos'}
COMMANDS = {'doctor', 'start', 'attach', 'status', 'exec', 'capture', 'input', 'stop', 'describe', 'build', 'view'}


def fail(platform, code, message, exit_code=2):
    print(json.dumps({'schemaVersion': 1, 'ok': False, 'platform': platform,
                      'error': {'code': code, 'message': message}}))
    return exit_code


def descriptor(response):
    session = response.get('session')
    if not response.get('ok') or not isinstance(session, dict) or not session.get('id'):
        return None
    platform = response['platform']
    state = session.get('phase', session.get('state', 'unknown'))
    generation = session.get('generation') if state in ('running', 'attached', 'starting') else None
    caps = {k: v for k, v in session.get('capabilities', {}).items() if type(v) is bool}
    if state not in ('running', 'attached'):
        caps = {k: False for k in caps}
    return {'schemaVersion': 1, 'id': session['id'], 'platform': platform,
            'generation': generation, 'state': state,
            'capabilities': caps, 'connection': {'kind': 'local-cli', 'protocolVersion': 1},
            'lifecycle': {'acquire': 'attach' if platform == 'windows' else 'start',
                          'release': {'windows': 'detach-owned', 'linux': 'stop-owned', 'macos': 'save-and-stop'}[platform]}}


def entrypoint():
    raise SystemExit(main(sys.argv[1:]))


def main(argv):
    platform = PLATFORMS.get(sys.platform)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if argv == ['--version']:
        print(json.dumps({'schemaVersion': 1, 'ok': True, 'version': VERSION, 'platform': platform}))
        return 0
    if not argv or argv in (['-h'], ['--help']):
        print('QuietWing ' + VERSION + '\n'
              'Usage: quietwing COMMAND [OPTIONS]\n\n'
              'Commands: doctor, describe, start, attach, status, exec, capture, input, stop, view, build\n'
              'Session commands use --id NAME. Run COMMAND --help for adapter options.\n'
              'Run this helper on the target OS, directly or through SSH.\n'
              'Only verified isolated sessions are controllable; there is no host-desktop fallback.')
        return 0
    if not platform:
        return fail(None, 'unsupported_platform', 'This OS has no session adapter.')
    if argv[0] not in COMMANDS:
        return fail(platform, 'unknown_command', 'Unknown command: ' + argv[0])
    root = Path(__file__).resolve().parent
    if argv in (['build'], ['build', '--viewer']):
        if platform != 'macos':
            return fail(platform, 'unsupported_operation', 'Explicit build is macOS-only; other backends report prerequisites through doctor.')
        try:
            p = subprocess.run([sys.executable, str(root / 'macos' / ('build_viewer.py' if '--viewer' in argv else 'build_vm.py'))],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=240)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return fail(platform, 'build_failed', str(exc))
        if p.stderr:
            sys.stderr.write(p.stderr)
        if p.returncode:
            return fail(platform, 'build_failed', 'Native build failed; see stderr.')
        print(json.dumps({'schemaVersion': 1, 'ok': True, 'platform': platform,
                          'result': {'built': True, 'output': p.stdout.strip()}}))
        return 0
    adapter_argv = ['status', *argv[1:]] if argv[0] == 'describe' else argv
    adapter = root / platform / 'adapter.py'
    if not adapter.is_file():
        return fail(platform, 'adapter_unavailable', 'The ' + platform + ' adapter is not installed.')
    kwargs = {}
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    try:
        completed = subprocess.run([sys.executable, str(adapter), *adapter_argv],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                   env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=90, **kwargs)
    except subprocess.TimeoutExpired:
        return fail(platform, 'adapter_timeout', 'Adapter did not respond within 90 seconds. Inspect status before retrying a mutation.')
    except OSError as exc:
        return fail(platform, 'adapter_launch_failed', str(exc))
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    try:
        response = json.loads(completed.stdout)
    except (ValueError, TypeError):
        # Only the documented standalone help form permits non-JSON output.
        # Values such as input --type --help are always treated as data.
        if argv[1:] in (['-h'], ['--help']) and completed.returncode == 0:
            sys.stdout.write(completed.stdout)
            return 0
        return fail(platform, 'invalid_adapter_response', 'Adapter did not return one JSON object; no success was inferred.')
    if not isinstance(response, dict) or type(response.get('ok')) is not bool or response.get('platform') != platform:
        return fail(platform, 'invalid_adapter_response', 'Adapter response lacks a valid ok/platform envelope.')
    if response['ok'] and completed.returncode != 0:
        return fail(platform, 'adapter_exit_mismatch', 'Adapter claimed success but exited with an error.')
    response['schemaVersion'] = 1
    desc = descriptor(response)
    if desc is not None:
        response['descriptor'] = desc
    print(json.dumps(response, ensure_ascii=False))
    return 0 if response['ok'] else (completed.returncode or 1)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

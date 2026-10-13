#!/usr/bin/env python3
"""Read-only console rejection checks. No successful capture/input/exec is attempted."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import sys
sys.dont_write_bytecode = True
try:
    from .runtime_paths import build_root
except ImportError:
    from runtime_paths import build_root

root = Path(__file__).resolve().parent
worker = build_root() / 'deskhelper-macos-worker'
checks = []

def record(name, passed, detail=None):
    item = {'name': name, 'passed': bool(passed)}
    if detail is not None:
        item['detail'] = detail
    checks.append(item)

def call(req):
    proc = subprocess.run([str(worker)], input=json.dumps(req) + '\n', capture_output=True, text=True, timeout=10)
    if proc.returncode:
        raise RuntimeError('Worker process failed')
    return json.loads(proc.stdout)

pure = json.loads(subprocess.check_output([str(worker), '--self-test'], text=True))
record('pure_session_policy_matrix', pure['ok'], pure['tests'])
preflight = call({'op': 'doctor'})
identity = preflight.get('session', {}).get('identity', {})
record('read_only_doctor', preflight.get('ok') is True and preflight.get('result', {}).get('permission_prompts') is False)
if not (identity.get('uid') == identity.get('consoleUID') or identity.get('onConsole') is True):
    raise SystemExit('These rejection-only live tests require the known console context; refusing on another session.')
with tempfile.TemporaryDirectory(prefix='deskhelper-rejection-') as folder:
    marker = Path(folder) / 'must-not-exist'
    expected = {'expected_uid': identity['uid'], 'expected_session_id': identity.get('securitySessionID', 1)}
    requests = [dict(op='attach'), dict(op='capture', output=str(marker)),
                dict(op='input', click=[0.0, 0.0]),
                dict(op='exec', argv=['/usr/bin/touch', str(marker)])]
    for req in requests:
        result = call(dict(req, **expected))
        record('console_refused_' + req['op'], result.get('ok') is False and result.get('error', {}).get('code') in ('worker_is_console_user', 'console_gui_forbidden'), result.get('error'))
    record('no_capture_or_exec_artifact', not marker.exists())
    env = dict(os.environ, DESKHELPER_STATE_ROOT=str(Path(folder) / 'state'), PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run([sys.executable, str(root / 'adapter.py'), 'attach', '--backend', 'native', '--id', 'guard-test', '--uid', str(identity['uid']), '--session-id', str(identity.get('securitySessionID', 1))], env=env, capture_output=True, text=True)
    result = json.loads(proc.stdout)
    record('adapter_refuses_before_state_write', proc.returncode != 0 and not result['ok'] and not (Path(folder) / 'state').exists())
spec = importlib.util.spec_from_file_location('mac_adapter', root / 'adapter.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parsed = module.parse(['input', '--id', 'test', '--type', '--hello;$(data)'])
record('leading_hyphen_text_is_data', parsed.text == '--hello;$(data)')
parsed = module.parse(['input', '--id', 'test', '--type', '--'])
record('double_hyphen_text_is_data', parsed.text == '--')
parsed = module.parse(['exec', '--id', 'test', '--', '/bin/echo', '--type', '--hello;$(data)'])
record('exec_argv_preserved', parsed.argv == ['/bin/echo', '--type', '--hello;$(data)'])
result = {'ok': all(c['passed'] for c in checks), 'platform': 'macos', 'tests': checks,
          'live_separate_session_acceptance': False, 'host_control_performed': False}
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['ok'] else 1)

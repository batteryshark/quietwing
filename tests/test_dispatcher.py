"""Contract boundary tests, independent of native desktop availability."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = {'darwin': 'macos', 'linux': 'linux', 'win32': 'windows'}[sys.platform]


class DispatcherContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='quietwing-dispatch-')
        self.root = Path(self.tmp.name)
        shutil.copyfile(ROOT / 'cli.py', self.root / 'cli.py')
        (self.root / PLATFORM).mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def adapter(self, body):
        (self.root / PLATFORM / 'adapter.py').write_text(body)

    def call(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'cli.py'), *args],
                              capture_output=True, text=True, timeout=10)

    def session_adapter(self, state, generation, capabilities):
        session = {"id": "work", "phase": state, "generation": generation,
                   "capabilities": capabilities}
        body = 'import json,sys\nprint(json.dumps(' + repr({
            "ok": True, "platform": PLATFORM, "session": session,
        }) + ' | {"result":{"argv":sys.argv[1:]}}))\n'
        self.adapter(body)

    def test_describe_returns_versioned_live_descriptor_and_uses_status(self):
        self.session_adapter('running', 'live-123', {'capture': True, 'input': True, 'exec': True})
        r = self.call('describe', '--id', 'work')
        self.assertEqual(r.returncode, 0, r.stderr)
        value = json.loads(r.stdout)
        self.assertEqual(value['result']['argv'], ['status', '--id', 'work'])
        d = value['descriptor']
        self.assertEqual((d['schemaVersion'], d['id'], d['platform'], d['generation']),
                         (1, 'work', PLATFORM, 'live-123'))
        self.assertEqual(d['connection'], {'kind': 'local-cli', 'protocolVersion': 1})
        self.assertEqual(d['lifecycle']['acquire'], 'attach' if PLATFORM == 'windows' else 'start')
        self.assertEqual(d['lifecycle']['release'], {
            'windows': 'detach-owned', 'linux': 'stop-owned', 'macos': 'save-and-stop'}[PLATFORM])
        self.assertTrue(d['capabilities']['capture'])

    def test_terminal_descriptors_cannot_advertise_live_control(self):
        for state in ('stopped', 'saved', 'lost', 'failed'):
            with self.subTest(state=state):
                self.session_adapter(state, 'old-generation', {'capture': True, 'input': True, 'exec': True})
                r = self.call('describe', '--id', 'work')
                self.assertEqual(r.returncode, 0, r.stderr)
                d = json.loads(r.stdout)['descriptor']
                self.assertIsNone(d['generation'])
                self.assertFalse(any(d['capabilities'].values()))

    def test_starting_descriptor_pins_owner_without_claiming_control(self):
        self.session_adapter('starting', 'starting-123', {'capture': True, 'input': True})
        r = self.call('start', '--id', 'work')
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)['descriptor']
        self.assertEqual(d['generation'], 'starting-123')
        self.assertFalse(any(d['capabilities'].values()))

    def test_view_dispatch_preserves_generation_flags(self):
        self.adapter('import json,sys\nprint(json.dumps({"ok":True,"platform":' + repr(PLATFORM) + ',"result":{"argv":sys.argv[1:]}}))\n')
        args = ['view', '--id', 'work', '--expect-generation', 'live-123', *(['--status'] if PLATFORM=='macos' else ['--frame'])]
        response = self.call(*args)
        value = json.loads(response.stdout)
        self.assertEqual(response.returncode, 0)
        self.assertEqual(value['result']['argv'], args)

    def test_viewer_build_does_not_invoke_vm_builder_or_adapter(self):
        if PLATFORM == 'macos':
            (self.root / PLATFORM / 'build_viewer.py').write_text('print("preview-only")\n')
        response = self.call('build', '--viewer')
        value = json.loads(response.stdout)
        if PLATFORM == 'macos':
            self.assertEqual(response.returncode, 0)
            self.assertEqual(value['result']['output'], 'preview-only')
        else:
            self.assertNotEqual(response.returncode, 0)
            self.assertEqual(value['error']['code'], 'unsupported_operation')

    def test_missing_adapter_is_an_error(self):
        r = self.call('doctor')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['error']['code'], 'adapter_unavailable')

    def test_exec_arguments_are_data_including_help_and_shell_syntax(self):
        self.adapter('import json,sys\nprint(json.dumps({"ok":True,"platform":' + repr(PLATFORM) + ',"result":{"argv":sys.argv[1:]}}))\n')
        marker = self.root / 'must-not-be-created'
        args = ['exec', '--id', 'test', '--', 'app', '--help', '-again', 'two words',
                "apostrophe's", 'line1\nline2', '$(touch ' + str(marker) + ')', '`touch ' + str(marker) + '`']
        r = self.call(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout)
        self.assertEqual(result['result']['argv'], args)
        self.assertEqual(result['schemaVersion'], 1)
        self.assertFalse(marker.exists())

    def test_help_literal_still_validates_and_decorates_json(self):
        self.adapter('import json,sys\nprint(json.dumps({"ok":True,"platform":' + repr(PLATFORM) + ',"result":{"argv":sys.argv[1:]}}))\n')
        args = ['input', '--id', 'test', '--type', '--help']
        r = self.call(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        value = json.loads(r.stdout)
        self.assertEqual(value['schemaVersion'], 1)
        self.assertEqual(value['result']['argv'], args)
        self.adapter('print("not JSON")\n')
        r = self.call(*args)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['error']['code'], 'invalid_adapter_response')

    def test_standalone_adapter_help_allows_text(self):
        self.adapter('print("Usage: isolated adapter")\n')
        r = self.call('input', '--help')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, 'Usage: isolated adapter\n')

    def test_malformed_response_cannot_be_success(self):
        self.adapter('print("not JSON")\n')
        r = self.call('capture', '--id', 'test', '--output', 'image.png')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['error']['code'], 'invalid_adapter_response')

    def test_wrong_platform_cannot_be_success(self):
        self.adapter('import json\nprint(json.dumps({"ok":True,"platform":"other"}))\n')
        r = self.call('input', '--id', 'test', '--type', 'a')
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(json.loads(r.stdout)['ok'])

    def test_nonzero_adapter_exit_overrides_success_claim(self):
        self.adapter('import json,sys\nprint(json.dumps({"ok":True,"platform":' + repr(PLATFORM) + '}))\nsys.exit(3)\n')
        r = self.call('start', '--id', 'test')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['error']['code'], 'adapter_exit_mismatch')

    def test_error_envelope_cannot_return_success_exit(self):
        self.adapter('import json\nprint(json.dumps({"ok":False,"platform":' + repr(PLATFORM) + ',"error":{"code":"session_lost","message":"session gone"}}))\n')
        r = self.call('status', '--id', 'test')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['error']['code'], 'session_lost')


if __name__ == '__main__':
    unittest.main()

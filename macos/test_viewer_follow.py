"""Following is opt-in, image-only, and never acquires a remote desktop."""
import json, os, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
import adapter, viewer, ssh_remote as remote
from test_remote_viewer import PNG

class FollowViewer(unittest.TestCase):
    platform = 'linux'
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, DESKHELPER_STATE_ROOT=self.temp.name); self.env.start()
        self.source = remote.target('fixture.invalid', platform=self.platform)
        self.root = viewer.state_root('work', True, self.source)
        self.token = 'f'*32
        self.run = viewer.private_dir(self.root/self.token, True)
        self.info = dict(id='work', generation=None, source=self.source, token=self.token, follow=True)
        viewer.write_json(self.root/'active.json', self.info)
    def tearDown(self): self.env.stop(); self.temp.cleanup()
    def run_broker(self, status, frame, stop):
        states=[]; queries=[]; clock=[0.0]; original=viewer.write_json
        def record(path, value):
            if path.name == 'state.json':
                states.append(json.loads(json.dumps(value)))
                if stop(value): original(self.run/'close.json', {'close':True})
            original(path, value)
        def query(source, operation, name, generation=None):
            self.assertEqual((source, operation, name, generation), (self.source, 'status', 'work', None))
            queries.append(clock[0]); return status(len(queries))
        def pixels(source, name, generation):
            self.assertEqual((source, name), (self.source, 'work')); self.assertIsInstance(generation, str)
            return frame(generation)
        with patch.object(viewer.subprocess, 'run') as ui, patch.object(remote, 'call', side_effect=query), \
             patch.object(remote, 'frame', side_effect=pixels), patch.object(viewer.vm, 'request') as vm, \
             patch.object(viewer, 'write_json', side_effect=record), \
             patch.object(viewer.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(viewer.time, 'sleep', side_effect=lambda delay: clock.__setitem__(0, clock[0]+delay)):
            viewer.broker('work', self.token, self.root)
        ui.assert_called_once(); vm.assert_not_called()
        self.assertFalse((self.run/'frame.png').exists())
        self.assertEqual(viewer.read_json(self.root/'active.json'), self.info)
        return states, queries
    def test_follow_can_open_while_absent_without_contacting_or_acquiring_target(self):
        with patch.object(remote, 'call') as ssh, patch.object(viewer.vm, 'request') as vm, \
             patch.object(viewer, 'launch_viewer', return_value={}) as launch:
            viewer.open_viewer(self.root, 'work', source=self.source, follow=True)
        ssh.assert_not_called(); vm.assert_not_called()
        self.assertEqual(launch.call_args.args[1], dict(id='work', generation=None, source=self.source, follow=True))
    def test_waits_then_rebinds_in_same_broker_and_reports_current_generation(self):
        frames=[]
        def status(n):
            if n == 1: raise remote.RemoteError('session_unavailable', 'absent')
            return {'session': {'generation': 'one' if n == 2 else 'two'}}
        def frame(generation):
            frames.append(generation)
            if len(frames) == 2: raise remote.RemoteError('generation_changed', 'replaced')
            return PNG, dict(capturedAt=time.time(), width=320, height=240)
        states, queries = self.run_broker(status, frame, lambda s: s['frames'] == 3)
        self.assertEqual(frames, ['one', 'one', 'two', 'two'])
        self.assertEqual(len(queries), 3)  # Healthy frames never poll unpinned status.
        self.assertEqual([s['generation'] for s in states if s['state']=='watching'], ['one', 'two', 'two'])
        with patch.object(viewer, 'alive', return_value=True):
            self.assertEqual(viewer.snapshot(self.root)['generation'], 'two')
        for state in states:
            if state.get('errorCode') == 'generation_changed':
                self.assertIsNone(state['generation']); self.assertNotIn('capturedAt', state)
    def test_status_to_frame_replacement_race_revalidates_before_showing_pixels(self):
        frames=[]
        def frame(generation):
            frames.append(generation)
            if generation=='one': raise remote.RemoteError('generation_changed', 'changed after status')
            return PNG, dict(capturedAt=time.time())
        states, _ = self.run_broker(lambda n: {'session':{'generation':'one' if n==1 else 'two'}}, frame, lambda s: s['frames']==1)
        self.assertEqual(frames, ['one','two'])
        self.assertEqual([s['generation'] for s in states if s['state']=='watching'], ['two'])
    def test_retry_backoff_is_bounded_and_keeps_heartbeat_alive(self):
        def absent(n): raise remote.RemoteError('remote_timeout', 'offline')
        states, queries = self.run_broker(absent, lambda _: self.fail('No capture without verified status'), lambda s: s.get('retryIn')==30)
        # Stop on first capped retry; no real sleeping or network.
        self.assertEqual(len(queries), 6)
        self.assertTrue(all(b-a >= delay-.001 for a,b,delay in zip(queries,queries[1:],[1,2,4,8,16])))
        self.assertEqual(max(s.get('retryIn',0) for s in states),30)
        self.assertGreater(len(states),len(queries))
    def test_protocol_and_capture_errors_end_refresh_without_rediscovery(self):
        for code in ['remote_protocol','invalid_capture','remote_reply_too_large','unsafe_viewer_state','BOUNDARY','OWNERSHIP_MISMATCH']:
            with self.subTest(code=code):
                (self.run/'close.json').unlink(missing_ok=True)
                def bad(_): raise remote.RemoteError(code, 'rejected')
                states, queries = self.run_broker(lambda n: {'session':{'generation':'one'}}, bad, lambda s: s['state']=='ended')
                self.assertEqual(len(queries),1)
                self.assertEqual(states[-2]['state'],'ended')
    def test_close_during_discovery_never_requests_a_frame(self):
        def status(_):
            viewer.write_json(self.run/'close.json', {'close':True})
            return {'session':{'generation':'one'}}
        states, _ = self.run_broker(status, lambda _: self.fail('Close must win'), lambda s: False)
        self.assertFalse(any(s['state']=='watching' for s in states))
    def test_close_during_capture_never_publishes_replacement_pixels(self):
        def frame(_):
            viewer.write_json(self.run/'close.json', {'close':True})
            return PNG, dict(capturedAt=time.time())
        states, _ = self.run_broker(lambda n: {'session':{'generation':'one'}}, frame, lambda s: False)
        self.assertFalse(any(s['state']=='watching' for s in states))
    def test_reopen_reuses_follow_window_without_rediscovery_or_launch(self):
        viewer.write_json(self.run/'state.json', dict(state='watching', generation='two', frames=4))
        with patch.object(viewer, 'alive', return_value=True), patch.object(viewer.subprocess, 'Popen') as ui, patch.object(remote,'call') as ssh:
            result = viewer.open_viewer(self.root, 'work', source=self.source, follow=True)
        self.assertEqual(result['generation'],'two'); self.assertTrue(result['follow'])
        ui.assert_not_called(); ssh.assert_not_called()
    def test_changing_modes_and_generation_pinned_close_are_explicit(self):
        with patch.object(viewer,'alive',return_value=True), self.assertRaises(viewer.ViewerError):
            viewer.launch_viewer(self.root, dict(id='work', generation='two', source=self.source))
        with self.assertRaises(viewer.ViewerError): viewer.close_viewer(self.root,'two')
        self.assertFalse((self.run/'close.json').exists())
    def test_follow_flags_cannot_weaken_control_generation_checks(self):
        self.assertTrue(adapter.parse(['view','--id','work','--host','fixture.invalid','--follow']).follow)
        for args in [ ['view','--id','work','--follow'],
                      ['view','--id','work','--host','fixture.invalid','--follow','--expect-generation','one'],
                      ['view','--id','work','--host','fixture.invalid','--follow','--close'],
                      ['input','--id','work','--type','x','--follow'],
                      ['stop','--id','work','--follow'] ]:
            with self.subTest(args=args), self.assertRaises(adapter.Failure): adapter.parse(args)

class WindowsFollowViewer(FollowViewer): platform='windows'
if __name__=='__main__': unittest.main()

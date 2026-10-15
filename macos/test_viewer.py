"""Read-only viewer interface tests with fake VM transports and no desktop."""
import json, os, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
import adapter, viewer, build_viewer

PNG = b'\x89PNG\r\n\x1a\nsynthetic-test-image'

class ReadOnlyViewer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, DESKHELPER_STATE_ROOT=self.temp.name)
        self.environment.start()
        self.root = viewer.state_root('test', True)
        self.info = {'id': 'test', 'generation': 'bound-generation', 'ownerPid': 123, 'token': 'a'*32}
        self.run = viewer.private_dir(self.root / self.info['token'], True)
        viewer.write_json(self.root / 'active.json', self.info)
    def tearDown(self):
        self.environment.stop(); self.temp.cleanup()
    def response(self, **changes):
        session = {'instance': self.info['generation'], 'pid': 123, 'phase': 'running',
                   'window_offscreen': True, 'window_key': False, 'window_main': False}
        session.update(changes)
        return {'ok': True, 'platform': 'macos', 'session': session, 'result': {}}
    def args(self, *options): return adapter.parse(['view', '--id', 'test', *options])
    def capture(self, name, payload, **kwargs):
        self.assertEqual(name, 'test'); self.assertEqual(payload['op'], 'capture')
        self.assertEqual(payload['instance'], 'bound-generation')
        p = Path(payload['output']);p.write_bytes(PNG);p.chmod(0o600)
        value = self.response();value['result'] = {'path': str(p), 'only_owned_guest_view': True,
            'captured_at': time.time(), 'width': 2, 'height': 2}
        return value
    def test_fresh_viewer_build_creates_a_private_cache_before_hash_lookup(self):
        cache=Path(self.temp.name)/'new-cache'
        def fake_tool(argv, **kwargs):
            if argv[0]=='xcrun': Path(argv[-1]).touch()
        with patch.dict(os.environ, DESKHELPER_BUILD_ROOT=str(cache)),patch.object(build_viewer.subprocess,'run',side_effect=fake_tool) as tool:
            app=build_viewer.build()
            self.assertTrue(app.is_dir())
            self.assertEqual(viewer.app_path(), app)
            self.assertEqual((cache/'macos').stat().st_mode & 0o777,0o700)
            self.assertEqual(tool.call_count,2)
            self.assertEqual(build_viewer.build(), app)
            self.assertEqual(tool.call_count,2)

    def test_capture_is_generation_pinned_and_keeps_one_private_frame(self):
        with patch.object(viewer.vm, 'request', side_effect=self.capture) as request:
            for _ in range(3): viewer.capture_frame(self.info, self.run)
        self.assertEqual(request.call_count, 3)
        self.assertEqual((self.run/'frame.png').read_bytes(), PNG)
        self.assertEqual(list(self.run.glob('*.png')), [self.run/'frame.png'])
        self.assertEqual((self.run/'frame.png').stat().st_mode & 0o777, 0o600)
    def test_replacement_owner_and_generation_cannot_publish_frames(self):
        for change in [{'instance':'replacement'}, {'pid':999}, {'phase':'saved'},
                       {'window_offscreen':False}, {'window_key':True}]:
            with self.subTest(change=change):
                (self.run/'frame.png').write_bytes(PNG)
                with patch.object(viewer.vm,'request',return_value=self.response(**change)):
                    with self.assertRaises(viewer.ViewerError):viewer.capture_frame(self.info,self.run)
                self.assertFalse((self.run/'frame.png').exists())
    def test_wrong_capture_provenance_is_refused(self):
        value = self.response(); value['result'] = {'path':'/unrelated','only_owned_guest_view':False}
        with patch.object(viewer.vm,'request',return_value=value):
            with self.assertRaises(viewer.ViewerError):viewer.capture_frame(self.info,self.run)
        self.assertFalse((self.run/'frame.png').exists())
    def test_stale_owner_error_stops_before_image_access(self):
        value={'ok':False,'error':{'code':'instance_changed','message':'changed'}}
        with patch.object(viewer.vm,'request',return_value=value):
            with self.assertRaises(viewer.ViewerError) as e:viewer.capture_frame(self.info,self.run)
        self.assertEqual(e.exception.code,'generation_changed')
    def test_stopped_guest_is_never_started(self):
        with patch.object(viewer.vm,'request',return_value=self.response(phase='saved',instance=None,pid=None)) as request,patch.object(viewer.subprocess,'Popen') as launch:
            with self.assertRaises(viewer.ViewerError):viewer.command(self.args())
        self.assertEqual([c.args[1]['op'] for c in request.call_args_list],['status']);launch.assert_not_called()
    def test_status_and_close_never_contact_vm_or_launch_apps(self):
        with patch.object(viewer.vm,'request') as request,patch.object(viewer.subprocess,'Popen') as launch:
            self.assertEqual(viewer.command(self.args('--status'))['result']['viewer']['state'],'closed')
            self.assertEqual(viewer.command(self.args('--close'))['result']['viewer']['state'],'closed')
        request.assert_not_called();launch.assert_not_called();self.assertTrue((self.run/'close.json').exists())
    def test_close_generation_mismatch_cannot_close_another_viewer(self):
        with self.assertRaises(viewer.ViewerError):viewer.command(self.args('--close','--expect-generation','other'))
        self.assertFalse((self.run/'close.json').exists())
    def test_reopening_existing_viewer_does_not_raise_or_duplicate_window(self):
        viewer.write_json(self.run/'state.json',{'state':'watching','frames':1})
        with patch.object(viewer.vm,'request',return_value=self.response()),patch.object(viewer,'alive',return_value=True),patch.object(viewer.subprocess,'Popen') as launch:
            value=viewer.command(self.args())
        self.assertEqual(value['result']['viewer']['generation'],'bound-generation');launch.assert_not_called()
    def test_open_does_not_follow_replacement_while_old_viewer_is_open(self):
        with patch.object(viewer.vm,'request',return_value=self.response(instance='new')),patch.object(viewer,'alive',return_value=True),patch.object(viewer.subprocess,'Popen') as launch:
            with self.assertRaises(viewer.ViewerError) as e:viewer.command(self.args())
        self.assertEqual(e.exception.code,'viewer_generation_changed');launch.assert_not_called()
    def test_symlinks_and_public_files_are_rejected(self):
        p=self.run/'unsafe';p.symlink_to('/etc/hosts')
        with self.assertRaises(OSError):viewer.read_file(p)
        p.unlink();p.write_text('{}');p.chmod(0o644)
        with self.assertRaises(viewer.ViewerError):viewer.read_file(p)
    def test_broker_closes_own_window_and_frames_without_vm_mutations(self):
        requests=[]
        def capture(name,payload,**kwargs):
            requests.append(payload);value=self.capture(name,payload,**kwargs)
            viewer.write_json(self.run/'close.json',{'close':True});return value
        with patch.object(viewer.vm,'request',side_effect=capture),patch.object(viewer.subprocess,'run') as ui:
            viewer.broker('test',self.info['token'])
        self.assertEqual([p['op'] for p in requests],['capture'])
        self.assertEqual(ui.call_args.args[0][:3],['/usr/bin/open','-g','-n'])
        self.assertEqual(viewer.read_json(self.run/'state.json')['state'],'closed')
        self.assertFalse((self.run/'frame.png').exists())
    def test_native_window_contains_no_guest_input_or_control_transport(self):
        source=(Path(__file__).parent/'Viewer.swift').read_text()
        for forbidden in ['import Virtualization','VZVirtualMachineView','CGEventPost','control.sock','keyDown(with: event)','super.mouseDown']:
            self.assertNotIn(forbidden,source)
        self.assertIn('override var canBecomeKey: Bool { false }',source)
        self.assertIn('override var canBecomeMain: Bool { false }',source)
    def test_view_flags_are_not_silently_applied_to_session_commands(self):
        for args in [['input','--id','test','--type','x','--close'],['view','--id','test','--backend','native'],['view','--id','test','--close','--status']]:
            with self.assertRaises(adapter.Failure):adapter.parse(args)

if __name__ == '__main__': unittest.main()

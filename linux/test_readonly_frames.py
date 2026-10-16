"""Read-only Linux frame leaf: no X server or host GUI is acquired by tests."""
import base64, contextlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('linux_adapter',Path(__file__).with_name('adapter.py'))
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
PNG=b'\x89PNG\r\n\x1a\n' + b'fake bounded fixture'

class ReadOnlyFrames(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.folder=self.root/'work';self.folder.mkdir()
        self.meta={'id':'work','generation':'one','state':'running','directory':str(self.folder),'width':1024,'height':768,'display':':77','capabilities':{'capture':True,'private_display':True}}
    def tearDown(self):self.temp.cleanup()
    def invoke(self,*options):
        with patch.object(adapter,'state_root',return_value=self.root),patch.object(adapter,'load_session',return_value=self.meta),patch.object(adapter,'verify',return_value={'DISPLAY':':77'}) as verify,patch.object(adapter,'run',return_value=PNG) as capture,patch.object(adapter,'reply') as reply:
            adapter.main(['view','--id','work','--frame',*options])
        return verify,capture,reply
    def test_frame_leaf_uses_verified_isolated_display_and_stdout_only(self):
        verify,capture,reply=self.invoke('--expect-generation','one')
        verify.assert_called_once_with(self.meta)
        argv=capture.call_args.args[0]
        self.assertEqual(argv[0],'ffmpeg');self.assertEqual(argv[argv.index('-i')+1],':77')
        self.assertEqual(argv[-1],'pipe:1');self.assertEqual(capture.call_args.args[1],{'DISPLAY':':77'})
        self.assertEqual(capture.call_args.kwargs['timeout'],8)
        image=reply.call_args.args[2]['image']
        self.assertEqual(base64.b64decode(image['data']),PNG);self.assertTrue(image['only_owned_guest_view'])
        self.assertEqual(list(self.folder.iterdir()),[self.folder/'.lifetime.lock'])
    def test_stale_or_missing_generation_refuses_before_capture(self):
        for options in [[],['--expect-generation','replacement']]:
            with self.subTest(options=options),patch.object(adapter,'verify') as verify,patch.object(adapter,'run') as run:
                # Use the same real parser/locking path; never reach X verification.
                with patch.object(adapter,'state_root',return_value=self.root),patch.object(adapter,'load_session',return_value=self.meta):
                    with self.assertRaises(adapter.Failure):adapter.main(['view','--id','work','--frame',*options])
                verify.assert_not_called();run.assert_not_called()
    def test_plain_view_is_not_a_gui_or_lifecycle_operation(self):
        with patch.object(adapter,'state_root') as state:
            with self.assertRaises(adapter.Failure):adapter.main(['view','--id','work'])
        state.assert_not_called()
    def test_bad_image_fails_without_a_success_reply(self):
        with patch.object(adapter,'state_root',return_value=self.root),patch.object(adapter,'load_session',return_value=self.meta),patch.object(adapter,'verify',return_value={}),patch.object(adapter,'run',return_value=b'bad'),patch.object(adapter,'reply') as reply:
            with self.assertRaises(adapter.Failure):adapter.main(['view','--id','work','--frame','--expect-generation','one'])
        reply.assert_not_called()

if __name__=='__main__':unittest.main()

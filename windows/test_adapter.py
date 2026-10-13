"""Pure CLI/binding tests; no desktop, scheduler, provider, or process operations."""
import contextlib, importlib.util, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('windows_adapter',Path(__file__).with_name('adapter.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class GenerationTests(unittest.TestCase):
    def run_command(self, arguments):
        payloads=[]
        def request(folder,payload):
            payloads.append(payload)
            return {'ok':True,'session':{'id':'test','generation':'a'*32},'result':{}}
        meta={'audio':{},'connectedAt':'test'}
        # Only os.name is needed for dispatch; keep host pathlib behavior intact.
        with patch.object(a,'os',types.SimpleNamespace(name='nt')),patch.object(a,'bound',return_value=(Path('/fake'),meta)),patch.object(a,'request',side_effect=request):
            result=a.main(arguments)
        return payloads,result
    def test_transient_response_read_does_not_resubmit(self):
        response={'ok':True}
        with patch.object(a,'read',side_effect=[PermissionError('sharing'),response]),patch.object(a.time,'sleep'):
            self.assertIs(a.wait_file(Path('/fake')),response)
    def test_transient_response_cleanup_only_retries_unlink(self):
        from unittest.mock import Mock
        path=Mock();path.unlink.side_effect=[PermissionError('sharing'),None]
        with patch.object(a.time,'sleep'):a.remove_transient(path)
        self.assertEqual(path.unlink.call_count,2)
    def test_forward_guard_every_worker_command(self):
        for command,args in [('status',[]),('capture',['--output','capture.png']),('input',['--type','test']),('exec',['--','app','--type','--help'])]:
            with self.subTest(command=command):
                payloads,_=self.run_command([command,'--id','test','--expect-generation','token',*args])
                self.assertEqual(payloads[0]['expectGeneration'],'token')
    def test_no_guard_remains_compatible(self):
        payloads,_=self.run_command(['input','--id','test','--type','--help'])
        self.assertNotIn('expectGeneration',payloads[0]);self.assertEqual(payloads[0]['text'],'--help')
    def test_exec_literal_generation_option_preserved(self):
        argv=['app','--expect-generation','literal','--type','--help','two words\\']
        payloads,_=self.run_command(['exec','--id','test','--expect-generation','token','--',*argv])
        self.assertEqual(payloads[0]['argv'],argv)
    def test_invalid_missing_id_json_failure(self):
        with self.assertRaises(a.Failure) as e:a.main(['status','--expect-generation','token'])
        self.assertEqual(e.exception.code,'INVALID_ARGUMENT')
    def test_generation_not_accepted_on_attach(self):
        with self.assertRaises(a.Failure) as e:a.main(['attach','--id','test','--expect-generation','token'])
        self.assertEqual(e.exception.code,'INVALID_ARGUMENT')
    def test_corrupt_generation_binding_rejected(self):
        with self.assertRaises(a.Failure) as e:a.generation({'ipc':'/runs/'+'a'*32,'generation':'b'*32})
        self.assertEqual(e.exception.code,'OWNERSHIP_MISMATCH')
    def test_stale_stop_rejected_before_process_or_cleanup(self):
        with patch.object(a,'load_binding',return_value=(Path('/fake'),{'ipc':'/runs/'+'a'*32})),patch.object(a,'process') as process:
            with self.assertRaises(a.Failure) as e:a.stop('test','b'*32)
        self.assertEqual(e.exception.code,'generation_changed');process.assert_not_called()
    def test_old_worker_guard_fails_before_request_write(self):
        with patch.object(a,'read',return_value={'session':{}}),patch.object(a,'save') as save:
            with self.assertRaises(a.Failure) as e:a.request(Path('/runs/'+'a'*32),{'action':'input','expectGeneration':'a'*32})
        self.assertEqual(e.exception.code,'REATTACH_REQUIRED');save.assert_not_called()
    def test_rejected_worker_stop_does_not_wait_or_cleanup(self):
        meta={'ipc':'/runs/'+'a'*32,'workerPid':1,'workerBirthTicks':2,'childSessionId':3,'exe':'worker.exe'}
        response={'ok':False,'error':{'code':'generation_changed'}}
        with patch.object(a,'load_binding',return_value=(Path('/fake'),meta)),patch.object(a,'process',return_value={'birthTicks':2,'session':3,'path':'worker.exe'}),patch.object(a,'request',return_value=response),patch.object(a,'wait_file') as wait:
            self.assertIs(a.stop('test','a'*32),response)
        wait.assert_not_called()

if __name__=='__main__':unittest.main()

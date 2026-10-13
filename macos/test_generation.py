#!/usr/bin/env python3
"""Generation boundary tests with fake transports; never control a desktop."""
import tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
import adapter,vm_adapter,runtime_paths

class GenerationBoundary(unittest.TestCase):
    def args(self,verb,*rest):return adapter.parse([verb,'--id','test','--expect-generation','fixed-owner',*rest])
    def response(self,ok=True):
        value={'ok':ok,'platform':'macos','session':{'id':'test','instance':'replacement' if not ok else 'fixed-owner','phase':'running','pid':123,'capabilities':{}},'result':{}}
        if not ok:value['error']={'code':'instance_changed','message':'changed'}
        return value
    def test_every_stale_operation_stops_before_action(self):
        for verb,rest in [('status',[]),('capture',['--output','/tmp/no-image']),('input',['--type','ignored']),('exec',['--','/bin/echo','ignored']),('stop',[])]:
            with self.subTest(verb=verb),patch.object(vm_adapter,'request',return_value=self.response(False)) as request,patch.object(vm_adapter,'bridge_exchange') as bridge:
                result=vm_adapter.command(self.args(verb,*rest))
                self.assertFalse(result['ok']);self.assertEqual(result['error']['code'],'generation_changed')
                self.assertEqual(request.call_count,1);self.assertEqual(request.call_args.args[1]['instance'],'fixed-owner');bridge.assert_not_called()
    def test_race_never_retargets_to_new_status_generation(self):
        for verb,rest in [('capture',['--output','/tmp/no-image']),('input',['--key','enter']),('exec',['--','/bin/echo','ok']),('stop',[])]:
            with self.subTest(verb=verb),patch.object(vm_adapter,'request',side_effect=[self.response(),self.response(False)]) as request:
                result=vm_adapter.command(self.args(verb,*rest))
                self.assertFalse(result['ok']);self.assertEqual(request.call_args.args[1]['instance'],'fixed-owner')
                if verb=='exec':self.assertEqual(request.call_args.args[1]['op'],'bridge')
    def test_unicode_mutation_is_owner_guarded(self):
        with patch.object(vm_adapter,'request',side_effect=[self.response(),self.response(False)]) as request,patch.object(vm_adapter,'live_bridge') as old_route:
            result=vm_adapter.command(self.args('input','--type','café 日本語'))
            self.assertFalse(result['ok']);self.assertEqual(request.call_args.args[1],{'op':'bridge','bridge_op':'clipboard','text':'café 日本語','instance':'fixed-owner'});old_route.assert_not_called()
    def test_saved_expected_generation_refused(self):
        with patch.object(vm_adapter,'request',side_effect=vm_adapter.VMError('VM control socket does not exist')),patch.object(vm_adapter,'directory') as directory:
            with self.assertRaises(vm_adapter.GenerationMismatch):vm_adapter.command(self.args('status'))
            directory.assert_not_called()
    def test_completed_stop_has_no_live_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'owner.lock').touch(mode=0o600)
            stopped=self.response();stopped['session']['phase']='terminating';stopped['result']={'guest_state_saved':True}
            with patch.object(vm_adapter,'request',side_effect=[self.response(),stopped]),patch.object(vm_adapter,'directory',return_value=Path(folder)),patch.object(vm_adapter,'bridge_exchange') as bridge:
                result=vm_adapter.command(self.args('stop'))
                self.assertTrue(result['result']['owner_exited']);self.assertIsNone(result['session']['generation']);self.assertEqual(result['session']['phase'],'saved');bridge.assert_not_called()
    def test_exec_arguments_are_data(self):
        args=self.args('exec','--','/bin/echo','--expect-generation','application-data')
        self.assertEqual(args.expect_generation,'fixed-owner');self.assertEqual(args.argv,['/bin/echo','--expect-generation','application-data'])
    def test_build_cache_outside_resource_source(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,DESKHELPER_BUILD_ROOT=folder):
            target=runtime_paths.build_root(create=True);self.assertEqual(target,Path(folder)/'macos');self.assertEqual(target.stat().st_mode&0o777,0o700)
    def test_unsupported_binding_not_silently_ignored(self):
        for argv in [['doctor','--expect-generation','old'],['start','--id','test','--expect-generation','old'],['status','--id','test','--backend','native','--expect-generation','old']]:
            with self.assertRaises(adapter.Failure):adapter.parse(argv)

if __name__=='__main__':unittest.main()

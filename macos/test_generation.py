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
        for verb,rest in [('windows',[]),('processes',[]),('windows',['--action','close','--window-id','123']),('processes',['--action','terminate','--pid','234','--target','token']),('status',[]),('capture',['--output','/tmp/no-image']),('input',['--type','ignored']),('exec',['--','/bin/echo','ignored']),('stop',[])]:
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

    def test_drag_is_one_pinned_request_without_bridge_mutation(self):
        ready=self.response();ready['session']['capabilities']['pointer_drag']=True
        done=self.response();done['session']['phase']='stopped';done['result']={'released':True}
        with patch.object(vm_adapter,'request',side_effect=[ready,done]) as request,patch.object(vm_adapter,'bridge_exchange') as bridge:
            result=vm_adapter.command(self.args('input','--drag','0','0','1023','767','--button','3'))
            self.assertTrue(result['result']['released'])
            self.assertEqual(request.call_count,2)
            self.assertEqual(request.call_args.args[1],{'op':'input','instance':'fixed-owner','drag':[0,0,1023,767],'button':3})
            bridge.assert_not_called()

    def test_old_owner_refuses_drag_before_delivery(self):
        with patch.object(vm_adapter,'request',return_value=self.response()) as request:
            with self.assertRaisesRegex(vm_adapter.VMError,'does not support pointer_drag'):
                vm_adapter.command(self.args('input','--drag','1','2','3','4'))
            self.assertEqual(request.call_count,1)

    def test_stale_drag_and_race_refuse_without_retargeting(self):
        ready=self.response();ready['session']['capabilities']['pointer_drag']=True
        for replies in ([self.response(False)],[ready,self.response(False)]):
            with patch.object(vm_adapter,'request',side_effect=replies) as request:
                result=vm_adapter.command(self.args('input','--drag','1','2','3','4'))
                self.assertEqual(result['error']['code'],'generation_changed')
                self.assertEqual(request.call_count,len(replies))
                self.assertEqual(request.call_args.args[1]['instance'],'fixed-owner')

    def test_hold_capability_and_generation(self):
        ready=self.response();ready['session']['capabilities']['key_hold']=True
        for replies in ([self.response(False)],[ready,self.response(False)]):
            with patch.object(vm_adapter,'request',side_effect=replies) as request:
                result=vm_adapter.command(self.args('input','--key','shift+left','--hold-ms','300'))
                self.assertEqual(result['error']['code'],'generation_changed')
                self.assertEqual(request.call_count,len(replies))
                self.assertEqual(request.call_args.args[1]['instance'],'fixed-owner')
        done=self.response();done['session']['phase']='stopped';done['result']={'released':True,'heldMs':300}
        with patch.object(vm_adapter,'request',side_effect=[ready,done]) as request:
            self.assertTrue(vm_adapter.command(self.args('input','--key','Space','--hold-ms','300'))['ok'])
            self.assertEqual(request.call_args.args[1],dict(op='input',instance='fixed-owner',key='Space',hold_ms=300,button=1))
        with patch.object(vm_adapter,'request',return_value=self.response()) as request:
            with self.assertRaisesRegex(vm_adapter.VMError,'does not support key_hold'):
                vm_adapter.command(self.args('input','--key','Space','--hold-ms','300'))
            self.assertEqual(request.call_count,1)

    def test_paste_is_one_owner_guarded_transaction_and_never_replayed(self):
        ready=self.response();ready['session']['capabilities']['text_paste']=True
        for text in ('a'*1000, '--help ; $(literal) café 日本語'):
            with patch.object(vm_adapter,'request',side_effect=[ready,self.response(False)]) as request,patch.object(vm_adapter,'live_bridge',return_value='guest'):
                result=vm_adapter.command(self.args('input','--type',text))
                self.assertFalse(result['ok']);self.assertEqual(request.call_count,2)
                self.assertEqual(request.call_args.args[1],dict(op='bridge',bridge_op='type_text',text=text,instance='fixed-owner'))
        with patch.object(vm_adapter,'request',return_value=ready) as request:
            with self.assertRaisesRegex(vm_adapter.VMError,'4096'):
                vm_adapter.command(self.args('input','--type','x'*4097))
            self.assertEqual(request.call_count,1)

    def test_invalid_hold_cli_never_reaches_transport(self):
        for rest in (['--key','Space','--hold-ms','-1'],['--key','a','--hold-ms','5001'],
                     ['--type','a','--hold-ms','300'],['--key','a','--hold-ms','1.5'],
                     ['--key','a','--hold-ms','300','--backend','native']):
            with self.subTest(rest=rest),self.assertRaises(adapter.Failure):self.args('input',*rest)

    def test_bootstrap_fallback_only_before_paste_and_without_live_bridge(self):
        ready=self.response();ready['session']['capabilities']['text_paste']=True
        done=self.response();done['session']['phase']='stopped'
        for unavailable in (vm_adapter.VMError('No live verified guest GUI bridge'),FileNotFoundError('bridge-id')):
            with patch.object(vm_adapter,'request',side_effect=[ready,done]) as request,patch.object(vm_adapter,'live_bridge',side_effect=unavailable):
                result=vm_adapter.command(self.args('input','--type','Bootstrap'))
                self.assertTrue(result['ok']);self.assertEqual(request.call_args.args[1]['text'],'Bootstrap')
                self.assertEqual(request.call_args.args[1]['op'],'input')
        with patch.object(vm_adapter,'request',side_effect=[ready,vm_adapter.VMError('unknown paste outcome')]) as request,patch.object(vm_adapter,'live_bridge',return_value='guest'):
            with self.assertRaisesRegex(vm_adapter.VMError,'unknown paste outcome'):
                vm_adapter.command(self.args('input','--type','never replay'))
            self.assertEqual(request.call_count,2)

    def test_drag_cli_refuses_ambiguous_or_native_requests(self):
        for rest in (['--drag','1','2','3'],['--drag','1','2','3','4','--click','5','6'],
                     ['--drag','1','2','3','4','--backend','native'],['--drag','1','2','3','4','--button','4']):
            with self.subTest(rest=rest),self.assertRaises(adapter.Failure):self.args('input',*rest)

    def test_guest_targets_are_one_owner_guarded_bridge_request(self):
        for verb,rest in [('windows',['--action','focus','--window-id','123']),('processes',['--action','terminate','--pid','234','--target','literal-token'])]:
            with patch.object(vm_adapter,'request',side_effect=[self.response(),self.response(False)]) as request:
                result=vm_adapter.command(self.args(verb,*rest))
                self.assertFalse(result['ok']);self.assertEqual(request.call_count,2)
                payload=request.call_args.args[1]
                self.assertEqual(payload['op'],'bridge');self.assertEqual(payload['bridge_op'],verb)
                self.assertEqual(payload['instance'],'fixed-owner')
                if verb=='processes':self.assertEqual(payload['target'],'literal-token')

    def test_guest_target_cli_refuses_unidentified_or_native_mutations(self):
        for verb,rest in [('windows',['--action','close']),('windows',['--action','quit','--pid','10']),('processes',['--action','terminate','--pid','10']),('processes',['--action','terminate','--pid','1','--target','t']),('windows',['--backend','native']),('processes',['--backend','native'])]:
            with self.subTest(verb=verb,rest=rest),self.assertRaises(adapter.Failure):self.args(verb,*rest)

if __name__=='__main__':unittest.main()

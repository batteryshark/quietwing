"""Remote viewer transport and lifecycle tests; all SSH and GUI effects faked."""
import base64,hashlib,json,os,shlex,subprocess,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import adapter,linux_remote as remote,viewer
PNG=b'\x89PNG\r\n\x1a\n'+b'\0\0\0\rIHDR'+(320).to_bytes(4,'big')+(240).to_bytes(4,'big')+b'test'

class RemoteViewer(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,DESKHELPER_STATE_ROOT=self.temp.name);self.env.start()
        self.source=remote.target('user@linux','/test/quietwing','/test/private-state')
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def response(self,generation='one'):
        return {'schemaVersion':1,'ok':True,'platform':'linux','session':{'id':'work','generation':generation,'state':'running','width':320,'height':240,'capabilities':{'private_display':True}},'descriptor':{'schemaVersion':1,'id':'work','platform':'linux','generation':generation,'state':'running','capabilities':{'capture':True}},'result':{'image':{'encoding':'base64','mimeType':'image/png','only_owned_guest_view':True,'data':base64.b64encode(PNG).decode(),'sha256':hashlib.sha256(PNG).hexdigest(),'width':320,'height':240,'captured_at':1.0}}}
    def call(self,value=None,code=0):
        # Write fake SSH output to the actual anonymous bounded output file.
        class Process:
            returncode=code
            def poll(self):return code
        def spawn(argv,**kwargs):
            kwargs['stdout'].write(json.dumps(value if value is not None else self.response()).encode());kwargs['stdout'].flush()
            self.assertEqual(kwargs['stdin'],subprocess.DEVNULL)
            return Process()
        with patch.object(remote.subprocess,'Popen',side_effect=spawn):return remote.call(self.source,'frame','work','one')
    def test_ssh_arguments_are_literal_and_have_no_forwards_or_prompts(self):
        source=remote.target('user@linux',"/test/a space'$(false);quietwing",'/state/two words')
        argv=remote.ssh_argv(source,'frame','work','one')
        self.assertEqual(shlex.split(argv[-1]),['env','DESKHELPER_STATE_ROOT=/state/two words',source['command'],'view','--id','work','--frame','--expect-generation','one'])
        for option in ['BatchMode=yes','StrictHostKeyChecking=yes','ForwardX11=no','ForwardAgent=no','ClearAllForwardings=yes','ControlPath=none']:self.assertIn(option,argv)
    def test_only_readonly_operations_and_valid_hosts_are_allowed(self):
        for name in ['input','exec','start','stop']:
            with self.assertRaises(remote.RemoteError):remote.ssh_argv(self.source,name,'work')
        for host in ['-oProxyCommand=bad','host;touch nope','host\nother']:
            with self.assertRaises(remote.RemoteError):remote.target(host)
    def test_reply_requires_matching_linux_session_and_capture_descriptor(self):
        self.assertEqual(self.call()['session']['generation'],'one')
        for change in ['platform','schemaVersion','generation','private','descriptor','exit']:
            value=self.response()
            if change=='platform':value['platform']='macos'
            if change=='schemaVersion':value['schemaVersion']=99
            if change=='generation':value=self.response('new')
            if change=='private':value['session']['capabilities']['private_display']=False
            if change=='descriptor':value['descriptor']=[]
            with self.subTest(change=change),self.assertRaises(remote.RemoteError):self.call(value,1 if change=='exit' else 0)
    def test_noisy_reply_is_bounded(self):
        with patch.object(remote,'MAX_REPLY',32),self.assertRaises(remote.RemoteError) as error:self.call()
        self.assertEqual(error.exception.code,'remote_reply_too_large')
    def test_ssh_timeout_terminates_only_the_owned_client(self):
        class Hung:
            returncode=None
            terminated=False
            def poll(self):return self.returncode
            def terminate(self):self.terminated=True;self.returncode=-15
            def wait(self,timeout=None):return self.returncode
        process=Hung()
        with patch.object(remote.subprocess,'Popen',return_value=process),patch.object(remote.time,'monotonic',side_effect=[0,11]),self.assertRaises(remote.RemoteError) as error:
            remote.call(self.source,'frame','work','one')
        self.assertEqual(error.exception.code,'remote_timeout');self.assertTrue(process.terminated)

    def test_remote_clock_skew_does_not_make_fresh_frames_stale(self):
        with patch.object(remote,'call',return_value=self.response()):data,meta=remote.frame(self.source,'work','one')
        self.assertEqual(data,PNG);self.assertLess(abs(meta['capturedAt']-time.time()),1);self.assertEqual(meta['remoteCapturedAt'],1.0)
    def test_corrupt_or_host_frames_are_rejected(self):
        for field,value in [('only_owned_guest_view',False),('data','not base64'),('sha256','bad'),('width',999),('captured_at',float('nan'))]:
            reply=self.response();reply['result']['image'][field]=value
            with self.subTest(field=field),patch.object(remote,'call',return_value=reply),self.assertRaises(remote.RemoteError):remote.frame(self.source,'work','one')
    def test_host_command_and_state_namespaces_cannot_collide_with_mac(self):
        paths=[viewer.state_root('work',True),viewer.state_root('work',True,self.source),viewer.state_root('work',True,remote.target('other')),viewer.state_root('work',True,remote.target('user@linux','/other'))]
        self.assertEqual(len(set(paths)),4)
        for path in paths:self.assertEqual(path.stat().st_mode & 0o777,0o700)
    def test_symlink_state_component_is_rejected(self):
        (Path(self.temp.name)/'viewers').symlink_to(Path(self.temp.name))
        with self.assertRaises(viewer.ViewerError):viewer.state_root('work',True,self.source)
    def test_status_close_do_not_make_ssh_calls(self):
        args=adapter.parse(['view','--id','work','--host','user@linux','--status'])
        with patch.object(remote,'call') as ssh,patch.object(viewer.subprocess,'Popen') as app:
            self.assertEqual(viewer.command(args)['result']['viewer']['state'],'closed')
            args=adapter.parse(['view','--id','work','--host','user@linux','--close']);viewer.command(args)
        ssh.assert_not_called();app.assert_not_called()
    def test_remote_capture_failure_removes_current_image(self):
        root=viewer.state_root('work',True,self.source);run=viewer.private_dir(root/'token',True);(run/'frame.png').write_bytes(PNG)
        info={'id':'work','generation':'one','source':self.source}
        with patch.object(remote,'frame',side_effect=remote.RemoteError('generation_changed','changed')),self.assertRaises(remote.RemoteError):viewer.capture_frame(info,run)
        self.assertFalse((run/'frame.png').exists())
    def test_remote_open_pins_generation_without_vm_or_lifecycle_calls(self):
        root=viewer.state_root('work',True,self.source)
        with patch.object(remote,'call',return_value=self.response()) as ssh,patch.object(viewer,'launch_viewer',return_value={}) as launch,patch.object(viewer.vm,'request') as vm:
            viewer.open_viewer(root,'work','one',self.source)
        ssh.assert_called_once_with(self.source,'status','work','one');vm.assert_not_called()
        self.assertEqual(launch.call_args.args[1],{'id':'work','generation':'one','source':self.source})
    def test_busy_capture_retries_only_the_same_generation(self):
        root=viewer.state_root('work',True,self.source);token='a'*32
        run=viewer.private_dir(root/token,True)
        info={'id':'work','generation':'one','source':self.source,'token':token}
        viewer.write_json(root/'active.json',info)
        calls=[]
        def capture(source,name,generation):
            calls.append((name,generation))
            if len(calls)==1:raise remote.RemoteError('SESSION_BUSY','busy')
            viewer.write_json(run/'close.json',{'close':True})
            return PNG,{'capturedAt':time.time(),'width':320,'height':240}
        states=[];original=viewer.write_json
        def record(path,value):
            if path.name=='state.json':states.append(value['state'])
            original(path,value)
        with patch.object(remote,'frame',side_effect=capture),patch.object(viewer.subprocess,'run'),patch.object(viewer,'write_json',side_effect=record):
            viewer.broker('work',token,root)
        self.assertEqual(calls,[('work','one'),('work','one')]);self.assertIn('waiting',states);self.assertIn('watching',states)
        self.assertFalse((run/'frame.png').exists())
    def test_remote_session_names_can_include_linux_dots(self):
        args=adapter.parse(['view','--id','work.name','--host','user@linux'])
        self.assertEqual(args.id,'work.name')

    def test_remote_options_never_apply_to_mutation_commands(self):
        for args in [['input','--id','work','--type','x','--host','user@linux'],['view','--id','work','--remote-command','/other']]:
            with self.assertRaises(adapter.Failure):adapter.parse(args)

if __name__=='__main__':unittest.main()

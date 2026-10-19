#!/usr/bin/env python3
"""Private Unix-socket controller for the owned Apple Virtualization guest."""
import json,os,socket,stat,time,subprocess,re,fcntl,uuid
from pathlib import Path
import sys
sys.dont_write_bytecode = True
try:
    from .runtime_paths import build_root
except ImportError:
    from runtime_paths import build_root
ROOT=Path(__file__).resolve().parent
BUILD=build_root()
APP=BUILD/'DeskhelperVM.app'
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')
class VMError(Exception):pass
class GenerationMismatch(VMError):
    code="generation_changed"

def directory(name,create=False):
    if not NAME.fullmatch(name):raise VMError('Invalid VM name')
    root=Path(os.environ.get('DESKHELPER_STATE_ROOT',str(Path.home()/'.local/state/deskhelper')))/'macos-vm'/name
    if create:root.mkdir(parents=True,exist_ok=True,mode=0o700)
    if not root.exists():raise VMError('VM state does not exist')
    s=root.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)&0o077:raise VMError('VM state must be private, owned and not a symlink')
    return root

def request(name,payload,timeout=20):
    root=directory(name); path=root/'control.sock'
    try:s=path.lstat()
    except FileNotFoundError:raise VMError('VM control socket does not exist')
    if not stat.S_ISSOCK(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)&0o077:raise VMError('VM control socket is not private and owned')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(timeout);client.connect(str(path));peer_pid=client.getsockopt(0,2);client.sendall(json.dumps(payload,ensure_ascii=False).encode());client.shutdown(socket.SHUT_WR)
        data=b''
        while len(data)<1048576:
            chunk=client.recv(65536)
            if not chunk:break
            data+=chunk
    value=json.loads(data)
    if value.get('session',{}).get('pid') != peer_pid:raise VMError('VM server PID does not match Unix peer identity')
    if type(value.get('ok')) is not bool or value.get('platform')!='macos' or value.get('session',{}).get('id')!=name:raise VMError('Invalid VM response')
    return value

def launch(name,install=False):
    root=directory(name,create=True)
    try:
        current=request(name,{'op':'status'})
        if current.get('session',{}).get('phase')=='stopped':return request(name,{'op':'start','instance':current['session']['instance']})
        return current
    except (OSError,VMError) as unavailable:
        # Never launch another owner because a running server is temporarily busy.
        lock=os.open(root/'owner.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise VMError('Existing VM owner is live but status is unavailable; refusing a duplicate launch')
            finally:os.close(lock)
        except OSError as exc:raise VMError('Cannot verify exclusive VM ownership: '+str(exc))
    if not APP.is_dir():raise VMError('Build VM host with macos/build_vm.py')
    if not install and not (root/'installed.json').is_file():raise VMError('Guest is not installed')
    if install and not (root/'Restore.ipsw').is_file():raise VMError('Verified restore image is required before installation')
    if install:
        metadata=json.loads((root/'restore-verified.json').read_text())
        if not metadata.get('verified') or metadata.get('bytes')!=(root/'Restore.ipsw').stat().st_size:raise VMError('Restore verification is missing or stale')
    command=['/usr/bin/open','-g','-n',str(APP),'--args','--state',str(root),'--id',name]
    if install:command+=['--install']
    subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,check=True)
    for _ in range(50):
        time.sleep(.1)
        try:return request(name,{'op':'status'})
        except (OSError,VMError):pass
    raise VMError('VM host did not become available; inspect launch-error.json')

if __name__=='__main__':
    import sys
    try:
        cmd,name=sys.argv[1:3]
        if cmd in ('start','install'):result=launch(name,cmd=='install')
        else:
            payload=json.loads(sys.stdin.read()) if cmd=='request' else {'op':cmd}
            result=request(name,payload)
        print(json.dumps(result));sys.exit(0 if result['ok'] else 1)
    except Exception as e:print(json.dumps({'ok':False,'platform':'macos','error':{'code':'vm_controller_error','message':str(e)}}));sys.exit(1)


def bridge_exchange(name,payload,guest_instance=None,timeout=15):
    bridge=directory(name)/'bridge'
    info=bridge.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise VMError('Unsafe guest bridge directory')
    identity=(bridge/'bridge-id').read_text().strip();uuid.UUID(identity)
    request_id=str(uuid.uuid4());request_path=bridge/(request_id+'.request.json');response_path=bridge/(request_id+'.response.json')
    value=dict(payload,bridge_id=identity)
    if guest_instance is not None:value['guest_instance']=guest_instance
    temporary=bridge/(request_id+'.pending')
    fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False)
    os.rename(temporary,request_path)
    try:
        for _ in range(max(1,int(timeout*10))):
            if response_path.exists():
                fd=os.open(response_path,os.O_RDONLY|os.O_NOFOLLOW)
                with os.fdopen(fd) as f:
                    info=os.fstat(f.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size>1048576:raise VMError('Invalid guest response file')
                    response=json.load(f)
                if response.get('request_id')!=request_id or type(response.get('ok')) is not bool:raise VMError('Invalid guest response identity')
                if guest_instance is not None and response.get('guest_instance')!=guest_instance:raise VMError('Guest bridge instance changed')
                return response
            time.sleep(.1)
        raise VMError('Guest bridge did not acknowledge this nonce; operation outcome is unknown and is not automatically retried')
    finally:
        request_path.unlink(missing_ok=True);response_path.unlink(missing_ok=True)

def live_bridge(name,owner_instance):
    response=bridge_exchange(name,{'op':'status'})
    if not response.get('ok') or not response.get('result',{}).get('virtualized') or not response.get('result',{}).get('graphical_session'):raise VMError('No live verified guest GUI bridge')
    if response['result'].get('vm_owner_instance')!=owner_instance:raise VMError('VM owner generation changed before guest mutation')
    return response['guest_instance']

def _command(args):
    """Common CLI entry point. The VM owner survives this function's process."""
    if args.command=='doctor':
        probe=BUILD/'vm-probe'
        if not probe.is_file():raise VMError('VM capability probe is not built')
        p=subprocess.run([str(probe)],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10,check=True)
        capabilities=json.loads(p.stdout)
        return {'ok':True,'platform':'macos','result':{'selected_backend':'apple-virtualization','virtualization':capabilities,'host_built':APP.is_dir(),'build_root':str(BUILD),'setup_document':str(ROOT/'NATIVE_OR_VM.md'),**({'acceptance_evidence':str(ROOT/'VM_RESULTS.md')} if (ROOT/'VM_RESULTS.md').is_file() else {}),'audio_policy':'no virtual audio devices; guest cannot play to host output'}}
    if args.command=='start':
        root=directory(args.id,create=True)
        return launch(args.id,not (root/'installed.json').is_file())
    if args.command in ('status','attach'):
        try:return request(args.id,dict(op='status',**({'instance':args.expect_generation} if args.expect_generation is not None else {})))
        except (OSError,VMError) as unavailable:
            absent=isinstance(unavailable,ConnectionRefusedError) or isinstance(unavailable,FileNotFoundError) or str(unavailable)=='VM control socket does not exist'
            if not absent:raise
            if args.expect_generation is not None:raise GenerationMismatch('Expected live generation is absent; session is saved/stopped')
            root=directory(args.id);fd=os.open(root/'owner.lock',os.O_RDWR|os.O_NOFOLLOW)
            try:
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:raise VMError('VM owner is live but temporarily unavailable; no saved-state status is inferred')
            finally:os.close(fd)
            snapshot=root/'SavedState.vzstate'
            saved=snapshot.is_file() and not snapshot.is_symlink()
            if args.command=='attach':raise VMError('VM is saved/stopped; use start to resume the owned guest')
            session={'id':args.id,'backend':'apple-virtualization','phase':'saved' if saved else 'stopped','owner_lock_free':True,'snapshot_present':saved,'audio_devices':0,'audio_isolated':True,'capabilities':{'capture':False,'input':False,'keyboard':False,'pointer':False,'audio':False,'audio_silent':True}}
            return {'ok':True,'platform':'macos','session':session,'result':dict(session)}
    before=request(args.id,dict(op='status',**({'instance':args.expect_generation} if args.expect_generation is not None else {})))
    if not before['ok']:return before
    session=before['session'];generation=args.expect_generation if args.expect_generation is not None else session['instance'];payload={'op':args.command,'instance':generation}
    if args.command=='capture':
        if not args.output:raise VMError('capture requires --output PATH')
        payload['output']=str(Path(args.output).absolute())
        return request(args.id,payload)
    if args.command=='input':
        if all(getattr(args,k,None) is None for k in ('text','key','click','move','drag')):raise VMError('input requires text, key, click, move or drag')
        if getattr(args,'drag',None) is not None and session.get('capabilities',{}).get('pointer_drag') is not True:raise VMError('VM owner does not support pointer_drag; save/stop, build and resume with the updated owner')
        payload.update({k:getattr(args,k) for k in ('text','key','click','move','drag') if getattr(args,k,None) is not None});payload['button']=args.button
        hold=getattr(args,'hold_ms',0)
        if hold:
            if session.get('capabilities',{}).get('key_hold') is not True:raise VMError('VM owner does not support key_hold; save/stop, build and resume with the updated owner')
            payload['hold_ms']=hold
        if args.text is not None and session.get('capabilities',{}).get('text_paste') is True:
            if len(args.text.encode('utf-16-le'))>8192:raise VMError('Text exceeds 4096 UTF16 units')
            # Bootstrap/login can lack a live bridge. Only this pre-mutation case
            # permits paced US keys; an ambiguous paste is never retried.
            try:live_bridge(args.id,generation)
            except (OSError,VMError,ValueError):
                if any(ord(c)>127 for c in args.text):raise
            else:return request(args.id,{'op':'bridge','bridge_op':'type_text','text':args.text,'instance':generation})
        elif args.text is not None and any(ord(c)>127 for c in args.text):
            if len(args.text.encode('utf-16-le'))>8192:raise VMError('Text exceeds 4096 UTF16 units')
            pasted=request(args.id,{'op':'bridge','bridge_op':'clipboard','text':args.text,'instance':generation})
            if not pasted['ok']:return dict(pasted,platform='macos',session=session)
            payload={'op':'input','instance':generation,'key':'cmd+v'}
    elif args.command=='exec':
        if not args.argv:raise VMError('exec requires -- PROGRAM ARG...')
        return request(args.id,{'op':'bridge','bridge_op':'exec','argv':args.argv,'cwd':args.cwd,'instance':generation})
    elif args.command in ('windows','processes'):
        return request(args.id,{'op':'bridge','bridge_op':args.command,'action':args.action,'window_id':args.window_id,'pid':args.pid,'target':args.target,'instance':generation})
    response=request(args.id,payload,timeout=75 if args.command=='stop' else 20)
    if args.command=='stop' and response.get('ok'):
        lock_path=directory(args.id)/'owner.lock'
        for _ in range(100):
            fd=os.open(lock_path,os.O_RDWR|os.O_NOFOLLOW);released=False
            try:
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);released=True
                except BlockingIOError:pass
            finally:os.close(fd)
            if released:
                response.setdefault('result',{})['owner_exited']=True
                departed=response.get('session',{})
                departed.update(phase='saved' if response['result'].get('guest_state_saved') else 'stopped',instance=None,generation=None,pid=None,owner_lock_free=True)
                break
            time.sleep(.1)
        else:raise VMError('Stop accepted but owner exit is not yet confirmed; do not restart blindly')
    return response


def command(args):
    response=_command(args)
    session=response.get('session')
    if not isinstance(session,dict):return response
    session['generation']=session.get('instance')
    if response.get('error',{}).get('code')=='instance_changed':response['error']['code']='generation_changed'
    capabilities=session.setdefault('capabilities',{})
    capabilities.update(audio_capture=False,browser=False,accessibility=False)
    capabilities.update(exec=False,unicode_text=False,guest_bridge_live=False)
    capabilities.update(guest_processes=False,guest_windows=False)
    if response.get('ok') and session.get('phase')=='running':
        try:
            bridge=bridge_exchange(args.id,{'op':'status'},timeout=2)
            state=bridge.get('result',{})
            live=bridge.get('ok') and state.get('virtualized') and state.get('graphical_session') and state.get('vm_owner_instance')==session.get('instance')
            if live:
                capabilities.update(exec=True,unicode_text=True,guest_bridge_live=True)
                capabilities.update(guest_processes=state.get('guest_targets') is True,guest_windows=state.get('guest_targets') is True and state.get('window_control') is True)
                session['guest']={k:state[k] for k in ('instance','pid','uid','os_version','metal_device','audio_device_count','default_output_device','vm_owner_instance') if k in state}
        except (OSError,VMError,ValueError):pass
    if (ROOT/'VM_RESULTS.md').is_file():session['acceptance_evidence']=str(ROOT/'VM_RESULTS.md')
    if session.get('instance') is not None and response.get('result',{}).get('instance')==session['instance']:response['result']=dict(session)
    return response

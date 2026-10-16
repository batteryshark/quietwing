#!/usr/bin/env python3
"""Linux desktop-session adapter. Standard library only; installed X11/Pulse tools.

This separates default GUI/session/audio routing, not the same user's OS rights.
"""
import argparse
import base64
import contextlib
import ctypes
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess as sp
import sys
import tempfile
import time
import traceback
import uuid

PLATFORM='linux'
REQUIRED=('Xvfb','xauth','xprop','xdpyinfo','xdotool','ffmpeg','glxinfo','dbus-daemon','dbus-send','pulseaudio','pactl')
class Failure(Exception):
    def __init__(self,code,message):self.code=code;super().__init__(message)
def fail(code,message):raise Failure(code,message)
def timestamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def write_json(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.'+secrets.token_hex(4)+'.tmp')
    with os.fdopen(os.open(tmp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as f:json.dump(value,f,indent=2);f.write('\n')
    os.replace(tmp,path)
def read_json(path):return json.loads(Path(path).read_text())
@contextlib.contextmanager
def lifetime_lock(directory,timeout=5):
    # The supervisor shares this lock with public actions. A verified private
    # display cannot be torn down/reallocated in the middle of an operation.
    with (Path(directory)/'.lifetime.lock').open('a') as lock:
        deadline=None if timeout is None else time.monotonic()+timeout
        while True:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if deadline is not None and time.monotonic()>=deadline:fail('SESSION_BUSY','Session lifetime is locked; retry shortly')
                time.sleep(.05)
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
def expect_generation(meta,expected):
    if expected is not None and meta.get('generation')!=expected:
        fail('generation_changed','Session instance changed; resolve its current descriptor before retrying')
def state_root():
    p=Path(os.environ.get('DESKHELPER_STATE_ROOT',str(Path.home()/'.local/state/desktop-session-helper'))).expanduser().absolute()
    if p.is_symlink():fail('UNSAFE_STATE_ROOT','State root must not be a symlink')
    p.mkdir(mode=0o700,parents=True,exist_ok=True)
    s=p.stat()
    if s.st_uid!=os.getuid() or s.st_mode&0o077:fail('UNSAFE_STATE_ROOT','State root must belong to this UID and have mode 0700')
    return p
def valid_id(name):
    if not name or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,47}',name):fail('INVALID_ID','Use 1–48 letters, digits, dot, underscore or hyphen, starting with a letter/digit')
    return name
def birth(pid):
    try:
        p=Path('/proc',str(pid));fields=(p/'stat').read_text().rsplit(')',1)[1].split()
        if p.stat().st_uid!=os.getuid() or fields[0]=='Z':return None
        return fields[19]
    except (FileNotFoundError,ProcessLookupError):return None
def identity(pid):return {'pid':pid,'start_time':birth(pid)}
def alive(record):return bool(record and record.get('start_time') and birth(record['pid'])==record['start_time'])
def has_token(pid,token):
    try:return b'DESKHELPER_SESSION_TOKEN='+token.encode() in Path('/proc',str(pid),'environ').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):return False
def run(argv,env=None,timeout=8):
    p=sp.run(argv,env=env,stdin=sp.DEVNULL,capture_output=True,timeout=timeout)
    if p.returncode:fail('BACKEND_COMMAND_FAILED',Path(argv[0]).name+' failed: '+p.stderr.decode(errors='replace')[-1000:])
    return p.stdout
def public(meta):
    keys=('id','generation','state','created_at','expires_at','width','height','display','capabilities','error','stopped_at','cleanup','window_manager')
    out={k:meta[k] for k in keys if k in meta}
    out['state_path']=str(Path(meta['directory'])/'session.json')
    return out
def reply(ok,session=None,result=None,error=None):
    d={'ok':ok,'platform':PLATFORM,'session':session or {'id':None,'state':'unavailable'}}
    if result is not None:d['result']=result
    if error is not None:d['error']=error
    print(json.dumps(d),flush=True)
def prerequisites():
    deps={n:shutil.which(n) for n in REQUIRED}
    return {'ready':all(deps.values()),'dependencies':deps,'optional_window_manager':shutil.which('xfwm4'),
            'audio':'private PulseAudio null sink verified per session; no hardware modules',
            'renderer':'measured per session; Xvfb commonly reports software rendering',
            'security_boundary':False,'same_uid_resource_and_filesystem_access_shared':True}
def load_session(root,name):
    path=root/valid_id(name)/'session.json'
    if not path.is_file():fail('SESSION_NOT_FOUND','No helper-owned session with this ID')
    meta=read_json(path)
    if meta.get('id')!=name or meta.get('uid')!=os.getuid() or meta.get('directory')!=str(path.parent):fail('SESSION_IDENTITY_MISMATCH','Saved session identity does not match this user/path')
    return meta
def environment(meta):
    p=Path(meta['directory']);r=Path(meta['runtime'])
    env={'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin'),'LANG':os.environ.get('LANG','C.UTF-8'),
         'USER':os.environ.get('USER',''),'LOGNAME':os.environ.get('LOGNAME',''),'HOME':str(p/'home'),
         'XDG_CONFIG_HOME':str(p/'home/config'),'XDG_CACHE_HOME':str(p/'home/cache'),'XDG_DATA_HOME':str(p/'home/data'),
         'XDG_STATE_HOME':str(p/'home/state'),'XDG_RUNTIME_DIR':str(r),'TMPDIR':str(r/'tmp'),
         'DISPLAY':meta['display'],'XAUTHORITY':str(r/'Xauthority'),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(r/'bus'),
         'GDK_BACKEND':'x11','QT_QPA_PLATFORM':'xcb','SDL_VIDEODRIVER':'x11','XDG_SESSION_TYPE':'x11',
         'DESKTOP_SESSION':'deskhelper','DESKHELPER_SESSION_TOKEN':meta['token'],
         'PULSE_SERVER':'unix:'+str(r/'pulse.sock'),'PULSE_SINK':'isolated','PULSE_SOURCE':'isolated.monitor',
         'PULSE_COOKIE':str(r/'pulse-cookie'),'PULSE_CLIENTCONFIG':str(r/'pulse-client.conf'),
         'PULSE_RUNTIME_PATH':str(r/'pulse-runtime'),'PULSE_STATE_PATH':str(r/'pulse-state'),
         'ALSA_CONFIG_PATH':str(r/'asound.conf'),'PIPEWIRE_RUNTIME_DIR':str(r),'PIPEWIRE_REMOTE':'deskhelper-no-host-pipewire',
         'NO_AT_BRIDGE':'0'}
    return env
def verify(meta,check_servers=True):
    if meta['state']!='running':fail('SESSION_NOT_RUNNING','Session state is '+meta['state'])
    r=Path(meta['runtime'])
    if not r.is_dir() or r.is_symlink() or r.stat().st_uid!=os.getuid() or r.stat().st_mode&0o077:fail('SESSION_STALE','Private runtime directory identity failed')
    if not (r/'owner.json').is_file() or read_json(r/'owner.json').get('token')!=meta['token']:fail('SESSION_STALE','Runtime ownership marker failed')
    for role in ('supervisor','xvfb','dbus','audio'):
        rec=meta.get('processes',{}).get(role)
        if not alive(rec):fail('SESSION_STALE',role+' PID birth identity no longer matches')
        if role!='supervisor' and not has_token(rec['pid'],meta['token']):fail('SESSION_STALE',role+' environment ownership failed')
    if check_servers:
        data=run(['xprop','-root','_DESKHELPER_SESSION'],environment(meta)).decode()
        if '= "'+meta['token']+'"' not in data:fail('DISPLAY_IDENTITY_MISMATCH','X server ownership property changed; refusing input/capture')
    return environment(meta)
def pdeath():
    # Backend/app leaders cannot survive unexpected supervisor death.
    ctypes.CDLL(None).prctl(1,signal.SIGTERM,0,0,0)
def spawn(argv,env,logdir,label):
    out=Path(logdir)/(label+'.stdout.log');err=Path(logdir)/(label+'.stderr.log')
    with out.open('ab') as a,err.open('ab') as b:
        p=sp.Popen(argv,env=env,stdin=sp.DEVNULL,stdout=a,stderr=b,preexec_fn=pdeath)
    return p,{'process':identity(p.pid),'stdout':str(out),'stderr':str(err)}
def tcp_owned(pids):
    inodes=set()
    for pid in pids:
        for fd in Path('/proc',str(pid),'fd').glob('*'):
            try:
                m=re.fullmatch(r'socket:\[(\d+)\]',os.readlink(fd))
                if m:inodes.add(m[1])
            except FileNotFoundError:pass
    hits=[]
    for family in ('tcp','tcp6'):
        for line in Path('/proc/net',family).read_text().splitlines()[1:]:
            fields=line.split()
            if fields[3]=='0A' and fields[9] in inodes:hits.append(fields[1])
    return hits
def owned_members(meta):
    found=[]
    for p in Path('/proc').glob('[0-9]*'):
        try:
            if p.stat().st_uid==os.getuid() and has_token(int(p.name),meta['token']):
                rec=identity(int(p.name))
                if rec['start_time']:found.append(rec)
        except (FileNotFoundError,ProcessLookupError):pass
    return found
def cleanup(meta):
    token=meta['token'];r=Path(meta['runtime'])
    killed=[]
    for sig in (signal.SIGTERM,signal.SIGKILL):
        members=owned_members(meta)
        for rec in members:
            if alive(rec) and has_token(rec['pid'],token):
                try:os.kill(rec['pid'],sig);killed.append(rec['pid'])
                except ProcessLookupError:pass
        deadline=time.monotonic()+(2 if sig==signal.SIGTERM else 1)
        while time.monotonic()<deadline and owned_members(meta):time.sleep(.05)
    # Reap direct child zombies, which cannot retain a display/audio server.
    while True:
        try:
            pid,_=os.waitpid(-1,os.WNOHANG)
            if not pid:break
        except ChildProcessError:break
    remaining=owned_members(meta)
    if r.is_dir() and not r.is_symlink() and (r/'owner.json').is_file() and read_json(r/'owner.json').get('token')==token:
        shutil.rmtree(r)
    number=meta['display'][1:]
    return {'remaining_owned_processes':remaining,'terminated_pids':sorted(set(killed)),
            'runtime_removed':not r.exists(),'display_socket_removed':not Path('/tmp/.X11-unix',f'X{number}').exists(),
            'display_lock_removed':not Path('/tmp',f'.X{number}-lock').exists()}
def wait_for(action,seconds=10):
    until=time.monotonic()+seconds;last=None
    while time.monotonic()<until:
        try:return action()
        except (Failure,FileNotFoundError,ConnectionRefusedError) as exc:last=exc;time.sleep(.1)
    raise last or Failure('START_TIMEOUT','Backend did not become ready')

def supervise(directory):
    p=Path(directory);meta=read_json(p/'session.json');r=Path(meta['runtime']);env=environment(meta)
    children=[];applications=[];control=None;stop_requested=False
    def stopping(*_):
        nonlocal stop_requested
        stop_requested=True
    signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
    meta['processes']={'supervisor':identity(os.getpid())};write_json(p/'session.json',meta)
    try:
        for directory in ('tmp','pulse-runtime','pulse-state'): (r/directory).mkdir(mode=0o700)
        for directory in ('home','home/config','home/cache','home/data','home/state','logs'): (p/directory).mkdir(mode=0o700,parents=True,exist_ok=True)
        (r/'Xauthority').touch(mode=0o600)
        cookie=secrets.token_hex(16)
        a=sp.run(['xauth','-f',str(r/'Xauthority')],input=f'add {meta["display"]} . {cookie}\n'.encode(),capture_output=True)
        if a.returncode:fail('AUTH_SETUP_FAILED','Private X authority setup failed')
        del cookie
        xvfb,_=spawn(['Xvfb',meta['display'],'-screen','0',f'{meta["width"]}x{meta["height"]}x24','-nolisten','tcp','-auth',str(r/'Xauthority'),'-noreset'],env,p/'logs','xvfb');children.append(xvfb)
        meta['processes']['xvfb']=identity(xvfb.pid)
        wait_for(lambda:run(['xdpyinfo'],env))
        run(['xprop','-root','-f','_DESKHELPER_SESSION','8s','-set','_DESKHELPER_SESSION',meta['token']],env)
        dbus,_=spawn(['dbus-daemon','--session','--nofork','--nopidfile','--address=unix:path='+str(r/'bus')],env,p/'logs','dbus');children.append(dbus)
        meta['processes']['dbus']=identity(dbus.pid)
        wait_for(lambda:run(['dbus-send','--session','--print-reply','--dest=org.freedesktop.DBus','/','org.freedesktop.DBus.GetId'],env))
        with os.fdopen(os.open(r/'pulse-cookie',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(secrets.token_bytes(256))
        (r/'pulse-client.conf').write_text(f'autospawn = no\ndefault-server = unix:{r}/pulse.sock\ncookie-file = {r}/pulse-cookie\n')
        # Route ordinary ALSA defaults to silence; direct device opens remain same-UID rights.
        (r/'asound.conf').write_text('pcm.!default { type null }\nctl.!default { type hw card -1 }\n')
        (r/'pulse.pa').write_text(f'load-module module-native-protocol-unix socket={r}/pulse.sock auth-cookie={r}/pulse-cookie auth-anonymous=0\nload-module module-null-sink sink_name=isolated rate=48000 channels=2\nset-default-sink isolated\nset-default-source isolated.monitor\n')
        pa,_=spawn(['pulseaudio','--daemonize=no','--use-pid-file=no','--exit-idle-time=-1','--disallow-exit','--disallow-module-loading','--log-target=stderr','-nF',str(r/'pulse.pa')],env,p/'logs','pulse');children.append(pa)
        meta['processes']['audio']=identity(pa.pid)
        sinks=wait_for(lambda:json.loads(run(['pactl','-f','json','list','sinks'],env)))
        sources=json.loads(run(['pactl','-f','json','list','sources'],env))
        modules=json.loads(run(['pactl','-f','json','list','modules'],env))
        if [x['name'] for x in sinks]!=['isolated'] or [x['name'] for x in sources]!=['isolated.monitor'] or set(x['name'] for x in modules)!={'module-native-protocol-unix','module-null-sink'}:
            fail('AUDIO_ISOLATION_FAILED','Private server must contain only a null sink, its monitor, and Unix protocol')
        gl=run(['glxinfo','-B'],env,timeout=12).decode(errors='replace');(p/'logs/glxinfo.txt').write_text(gl)
        renderer=next((line.split(':',1)[1].strip() for line in gl.splitlines() if line.startswith('OpenGL renderer string:')),None)
        acceleration=re.search(r'^\s*Accelerated:\s*(yes|no)',gl,re.MULTILINE|re.IGNORECASE)
        accelerated=(acceleration.group(1).lower()=='yes') if acceleration else None
        software=bool(renderer and any(s in renderer.lower() for s in ('llvmpipe','softpipe','software','swrast')))
        meta['capabilities']={'native_input':True,'capture':True,'input':True,'keyboard':True,'pointer':True,'exec':True,
                              'audio_capture':True,'audio_silent':True,'browser':False,'accessibility':False,
                              'private_display':True,'private_dbus':True,'private_home_xdg':True,
                              'audio_isolation':{'verified':True,'method':'private-pulseaudio-null','sinks':['isolated'],'sources':['isolated.monitor'],'hardware_modules':False},
                              'gl_renderer':renderer,'glx_accelerated':accelerated,'hardware_rendering':False if software else accelerated,
                              'security_sandbox':False,'viewer_required':False}
        if shutil.which('xfwm4'):
            wm,_=spawn(['xfwm4','--replace','--compositor=off'],env,p/'logs','wm');children.append(wm)
            time.sleep(.3)
            if wm.poll() is not None:fail('WINDOW_MANAGER_FAILED','Private xfwm4 exited; see session log')
            meta['processes']['wm']=identity(wm.pid);meta['window_manager']='xfwm4'
        else:meta['window_manager']=None
        if tcp_owned([c.pid for c in children]):fail('UNEXPECTED_LISTENER','Backend opened a TCP listener')
        control=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);control.bind(str(r/'control'));os.chmod(r/'control',0o600);control.listen(4);control.settimeout(.2)
        meta['state']='running';write_json(p/'session.json',meta)
        while not stop_requested and time.time()<meta['expires_epoch']:
            for app,label in list(applications):
                code=app.poll()
                if code is not None:
                    with (p/'apps-exits.jsonl').open('a') as f:f.write(json.dumps({'id':label,'pid':app.pid,'exit_code':code,'exited_at':timestamp()})+'\n')
                    applications.remove((app,label))
            if (p/'stop.request').exists() and read_json(p/'stop.request').get('token')==meta['token']:break
            if any(c.poll() is not None for c in children):fail('BACKEND_EXITED','A session backend exited unexpectedly')
            try:conn,_=control.accept()
            except socket.timeout:continue
            with conn:
                conn.settimeout(3)
                try:
                    raw=bytearray()
                    while not raw.endswith(b'\n') and len(raw)<65536:
                        part=conn.recv(4096)
                        if not part:break
                        raw.extend(part)
                    req=json.loads(raw)
                    argv=req.get('argv')
                    if req.get('token')!=meta['token'] or not isinstance(argv,list) or not argv or not all(isinstance(a,str) and '\0' not in a for a in argv):fail('INVALID_EXEC','Invalid owned-session exec request')
                    label='app-'+secrets.token_hex(6)
                    proc,details=spawn(argv,env,p/'logs',label)
                    applications.append((proc,label))
                    details.update(id=label,pid=proc.pid,launched_at=timestamp())
                    with (p/'apps.jsonl').open('a') as f:f.write(json.dumps(details)+'\n')
                    conn.sendall(json.dumps({'ok':True,'result':details}).encode()+b'\n')
                except Exception as exc:conn.sendall(json.dumps({'ok':False,'error':str(exc)}).encode()+b'\n')
    except Exception as exc:
        meta['error']={'code':getattr(exc,'code','START_FAILED'),'message':str(exc)}
        (p/'logs').mkdir(exist_ok=True)
        (p/'logs/supervisor-error.txt').write_text(traceback.format_exc())
    finally:
        with lifetime_lock(p,timeout=None):
            meta['state']='stopping';write_json(p/'session.json',meta)
            if control:control.close()
            meta['cleanup']=cleanup(meta);meta['state']='failed' if 'error' in meta else 'stopped';meta['stopped_at']=timestamp()
            write_json(p/'session.json',meta)

class Parser(argparse.ArgumentParser):
    def error(self,message):fail('INVALID_ARGUMENT',message)
def parser():
    p=Parser(add_help=False);subs=p.add_subparsers(dest='command',required=True)
    subs.add_parser('doctor',add_help=False)
    for name in ('start','attach','status','exec','capture','input','stop','view'):
        s=subs.add_parser(name,add_help=False);s.add_argument('--id',required=True)
        if name in ('status','exec','capture','input','stop','view'):s.add_argument('--expect-generation')
        if name=='start':
            s.add_argument('--width',type=int,default=1024);s.add_argument('--height',type=int,default=768);s.add_argument('--ttl',type=int,default=1800)
            s.add_argument('--replace-stopped',action='store_true')
        if name=='exec':s.add_argument('argv',nargs=argparse.REMAINDER)
        if name=='capture':s.add_argument('--output',required=True)
        if name=='view':s.add_argument('--frame',action='store_true',required=True)
        if name=='input':
            g=s.add_mutually_exclusive_group(required=True);g.add_argument('--type');g.add_argument('--key');g.add_argument('--click',nargs=2,type=int);g.add_argument('--move',nargs=2,type=int);s.add_argument('--button',type=int,default=1)
    return p
def main(argv):
    # Keep leading hyphens in text as data rather than argparse options.
    if argv[:1]==['input']:
        for opt in ('--type','--key'):
            if opt in argv:
                i=argv.index(opt)
                if i+1<len(argv):argv=argv[:i]+[opt+'='+argv[i+1]]+argv[i+2:]
    help_tokens=argv[:argv.index('--')] if '--' in argv else argv
    if '--help' in help_tokens or '-h' in help_tokens:
        reply(True,result={'usage':{'doctor':'doctor','start':'start --id NAME [--width 1024 --height 768 --ttl 1800] [--replace-stopped]',
              'status':'status --id NAME [--expect-generation UUID]','exec':'exec --id NAME [--expect-generation UUID] -- PROGRAM ARG...',
              'view':'view --frame --id NAME --expect-generation UUID (one isolated PNG in a JSON envelope)',
              'capture':'capture --id NAME [--expect-generation UUID] --output /absolute/image.png',
              'input':'input --id NAME [--expect-generation UUID] --type TEXT | --key KEY | --click X Y [--button 1] | --move X Y',
              'stop':'stop --id NAME [--expect-generation UUID]','attach':'unsupported: this adapter creates only owned isolated displays'},
              'notes':['DESKHELPER_STATE_ROOT must be private (0700).','exec is asynchronous and returns PID/stdout/stderr paths.',
                       'Use a fresh ID; stopped session evidence is retained.','Native keys use xdotool names, e.g. ctrl+s or Return.',
                       'TTL 5–86400 seconds; private resources removed at stop/expiry.','Same-UID access is not a security sandbox.']});return
    args=parser().parse_args(argv);meta=None
    if args.command=='doctor':
        d=prerequisites()
        if not d['ready']:fail('MISSING_DEPENDENCIES',', '.join(n for n,v in d['dependencies'].items() if not v))
        reply(True,result=d);return
    root=state_root();name=valid_id(args.id)
    with contextlib.ExitStack() as locks:
        lock=locks.enter_context((root/'.lock').open('a'))
        lock_deadline=time.monotonic()+5
        while True:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()>=lock_deadline:fail('SESSION_BUSY','Another helper command holds the state lock; retry shortly')
                time.sleep(.05)
        if args.command=='attach':fail('UNSUPPORTED_ATTACH','Linux only controls displays created and identity-verified by this helper')
        if args.command=='start':
            if not 320<=args.width<=4096 or not 240<=args.height<=2160 or not 5<=args.ttl<=86400:fail('INVALID_ARGUMENT','Width 320–4096, height 240–2160, TTL 5–86400 seconds')
            if not prerequisites()['ready']:fail('MISSING_DEPENDENCIES','Run doctor; required installed tools are missing')
            folder=root/name
            if folder.exists():
                if not args.replace_stopped:fail('SESSION_EXISTS','Use a new ID or --replace-stopped; existing evidence is preserved')
                with lifetime_lock(folder):
                    old=load_session(root,name)
                    until=time.monotonic()+1
                    while alive(old.get('processes',{}).get('supervisor')) and time.monotonic()<until:time.sleep(.05)
                    cleaned=old.get('cleanup',{})
                    if old['state'] not in ('stopped','failed') or alive(old.get('processes',{}).get('supervisor')) or Path(old['runtime']).exists() or owned_members(old) or cleaned.get('remaining_owned_processes')!=[] or not all(cleaned.get(k) for k in ('runtime_removed','display_socket_removed','display_lock_removed')):
                        fail('SESSION_NOT_CLEAN','Replacement requires a stopped instance with complete owned-resource cleanup')
                    archive=root/'.history'/name
                    archive.mkdir(mode=0o700,parents=True,exist_ok=True)
                    folder.rename(archive/str(uuid.uuid4()))
            folder.mkdir(mode=0o700);(folder/'logs').mkdir(mode=0o700)
            display=next((f':{n}' for n in range(70,200) if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
            if display is None:fail('NO_DISPLAY_AVAILABLE','No unused private display number')
            runtime=Path(tempfile.mkdtemp(prefix=f'deskhelper-{os.getuid()}-',dir='/tmp'));runtime.chmod(0o700)
            token=secrets.token_hex(24)
            meta={'id':name,'generation':str(uuid.uuid4()),'uid':os.getuid(),'state':'starting','directory':str(folder),'runtime':str(runtime),'token':token,
                  'created_at':timestamp(),'expires_epoch':time.time()+args.ttl,'expires_at':dt.datetime.fromtimestamp(time.time()+args.ttl,dt.timezone.utc).isoformat(),
                  'width':args.width,'height':args.height,'display':display}
            write_json(runtime/'owner.json',{'token':token,'uid':os.getuid()});write_json(folder/'session.json',meta)
            with (folder/'logs/supervisor.log').open('ab') as log:
                sp.Popen([sys.executable,str(Path(__file__).resolve()),'_supervise',str(folder)],stdin=sp.DEVNULL,stdout=log,stderr=log,start_new_session=True)
            until=time.monotonic()+40
            while time.monotonic()<until:
                meta=read_json(folder/'session.json')
                if meta['state']=='running':verify(meta);reply(True,public(meta));return
                if meta['state']=='failed':fail(meta['error']['code'],meta['error']['message'])
                time.sleep(.1)
            write_json(folder/'stop.request',{'token':token});fail('START_TIMEOUT','Session startup timed out; stop requested')
        meta=load_session(root,name)
        instance_locks=locks.enter_context(contextlib.ExitStack())
        instance_locks.enter_context(lifetime_lock(meta['directory']))
        meta=load_session(root,name)
        expect_generation(meta,args.expect_generation)
        if args.command=='status':
            if meta['state']=='running':
                try:verify(meta)
                except Failure:
                    current=load_session(root,name)
                    if current['state'] not in ('stopping','stopped','failed'):raise
                    meta=current
            elif meta['state']=='starting':fail('SESSION_NOT_READY','Session is still starting')
            if meta['state']=='stopping' and not alive(meta.get('processes',{}).get('supervisor')):fail('SESSION_STALE','Cleanup supervisor PID birth identity no longer matches')
            reply(True,public(meta));return
        if args.command=='stop' and meta['state'] in ('stopped','failed'):
            reply(True,public(meta));return
        if args.command=='stop':
            if meta['state']=='stopping':
                if not alive(meta.get('processes',{}).get('supervisor')):fail('SESSION_STALE','Cleanup supervisor PID birth identity no longer matches')
            else:
                verify(meta)
                write_json(Path(meta['directory'])/'stop.request',{'token':meta['token']})
            # Keep the root/replacement lock, but let the supervisor tear down.
            instance_locks.close()
            until=time.monotonic()+10
            while time.monotonic()<until:
                current=read_json(Path(meta['directory'])/'session.json')
                if current['state'] in ('stopped','failed'):
                    reply(True,public(current));return
                time.sleep(.1)
            fail('STOP_TIMEOUT','Owned supervisor has not confirmed cleanup')
        if args.command=='view' and args.expect_generation is None:
            fail('generation_required','Read-only frames require an explicit expected generation')
        env=verify(meta)
        if args.command=='view':
            image=run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-f','x11grab','-video_size',f'{meta["width"]}x{meta["height"]}',
                       '-draw_mouse','0','-i',meta['display'],'-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','pipe:1'],env,timeout=8)
            if len(image)>16*1024*1024 or not image.startswith(b'\x89PNG\r\n\x1a\n'):fail('INVALID_CAPTURE','Expected one bounded isolated PNG')
            reply(True,public(meta),{'image':{'encoding':'base64','mimeType':'image/png','only_owned_guest_view':True,
                'width':meta['width'],'height':meta['height'],'captured_at':time.time(),'sha256':hashlib.sha256(image).hexdigest(),
                'data':base64.b64encode(image).decode('ascii')}});return
        if args.command=='exec':
            if args.argv[:1]!=['--']:fail('INVALID_EXEC','Use -- before the executable to preserve application arguments')
            command=args.argv[1:] if args.argv[:1]==['--'] else args.argv
            if not command:fail('INVALID_EXEC','Provide an executable and arguments after --')
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                client.settimeout(8);client.connect(str(Path(meta['runtime'])/'control'))
                client.sendall(json.dumps({'token':meta['token'],'argv':command}).encode()+b'\n')
                data=bytearray()
                while not data.endswith(b'\n'):
                    chunk=client.recv(4096)
                    if not chunk:fail('EXEC_CONNECTION_CLOSED','Owned supervisor closed the exec connection')
                    data.extend(chunk)
            response=json.loads(data)
            if not response['ok']:fail('EXEC_FAILED',response['error'])
            reply(True,public(meta),response['result']);return
        if args.command=='capture':
            output=Path(args.output).expanduser().absolute()
            if output.suffix.lower()!='.png':fail('INVALID_OUTPUT','Capture output must have .png extension')
            output.parent.mkdir(parents=True,exist_ok=True)
            run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','x11grab','-video_size',f'{meta["width"]}x{meta["height"]}','-draw_mouse','0','-i',meta['display'],'-frames:v','1',str(output)],env,timeout=15)
            reply(True,public(meta),{'path':str(output),'width':meta['width'],'height':meta['height'],'captured_at':timestamp(),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()});return
        if args.command=='input':
            command=['xdotool']
            if args.type is not None:
                if len(args.type)>1024:fail('TEXT_TOO_LONG','Type at most 1024 characters per call; split longer text')
                if any(ord(c)<32 and c not in '\r\n\t' for c in args.type):fail('UNSUPPORTED_TEXT_CONTROL','Only tab and newline text control characters are supported')
                # xdotool type silently drops some control characters. Deliver those
                # as native Return/Tab keys and keep printable text literal.
                normalized=args.type.replace('\r\n','\n').replace('\r','\n')
                deadline=time.monotonic()+max(15,len(args.type)*.05+10)
                for part in re.findall(r'[^\n\t]+|[\n\t]',normalized):
                    command=['xdotool','key','--clearmodifiers','--','Return' if part=='\n' else 'Tab'] if part in ('\n','\t') else ['xdotool','type','--clearmodifiers','--delay','25','--',part]
                    remaining=deadline-time.monotonic()
                    if remaining<=0:fail('INPUT_TIMEOUT','Text exceeded its bounded delivery time')
                    run(command,env,timeout=remaining)
                reply(True,public(meta),{'delivered_at':timestamp(),'method':'XTEST','target_display':meta['display']});return
            elif args.key is not None:command+=['key','--clearmodifiers','--',args.key]
            else:
                x,y=args.click or args.move
                if not 0<=x<meta['width'] or not 0<=y<meta['height'] or not 1<=args.button<=9:fail('INVALID_COORDINATES','Input must stay inside the isolated display; buttons 1–9')
                command+=['mousemove',str(x),str(y)]
                if args.click:command+=['click',str(args.button)]
            run(command,env,timeout=max(15,len(args.type or '')*.05+10));reply(True,public(meta),{'delivered_at':timestamp(),'method':'XTEST','target_display':meta['display']});return

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='_supervise':
        supervise(sys.argv[2]);sys.exit(0)
    try:main(sys.argv[1:])
    except Exception as exc:
        reply(False,error={'code':getattr(exc,'code','INTERNAL_ERROR'),'message':str(exc)});sys.exit(1)

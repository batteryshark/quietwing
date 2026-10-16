"""Native Windows adapter. SSH, if desired, is an outer transport."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, os, re, subprocess, sys, time, uuid
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
class JsonParser(argparse.ArgumentParser):
    def error(self, message): raise Failure("INVALID_ARGUMENT", message)

class Failure(Exception):
    def __init__(self, code, message): self.code, self.message = code, message

def ps(script):
    import base64
    cmd = ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-OutputFormat', 'Text', '-EncodedCommand', base64.b64encode(("$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';" + script).encode('utf-16le')).decode()]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode: raise Failure('WINDOWS_OPERATION_FAILED', p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()

def quote(s): return "'" + str(s).replace("'", "''") + "'"
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path, value):
    tmp = Path(str(path)+'.writing'); tmp.write_text(json.dumps(value), encoding='utf-8'); tmp.replace(path)
def wait_file(path, seconds=12):
    end = time.monotonic()+seconds
    while time.monotonic()<end:
        try:return read(path)
        except (FileNotFoundError,PermissionError,json.JSONDecodeError):pass
        time.sleep(.06)
    raise Failure('TIMEOUT', f'Timed out waiting for owned worker output: {path.name}; no command retried')

def remove_transient(path, seconds=2):
    # A renamed Windows response can be visible before the writer closes its
    # handle. Retry cleanup only; the submitted action is never replayed.
    end=time.monotonic()+seconds
    while True:
        try:path.unlink(missing_ok=True);return
        except PermissionError:
            if time.monotonic()>=end:raise
            time.sleep(.02)

def native_state(session):
    from ctypes import wintypes
    dll=ctypes.WinDLL('wtsapi32',use_last_error=True)
    dll.WTSQuerySessionInformationW.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.c_int,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.DWORD)]
    dll.WTSFreeMemory.argtypes=[ctypes.c_void_p]
    p=ctypes.c_void_p(); n=wintypes.DWORD()
    if not dll.WTSQuerySessionInformationW(None,session,8,ctypes.byref(p),ctypes.byref(n)): return -1
    try:return ctypes.cast(p,ctypes.POINTER(ctypes.c_int)).contents.value
    finally:dll.WTSFreeMemory(p)

def console_id(): return ctypes.windll.kernel32.WTSGetActiveConsoleSessionId()
def process(pid):
    data=ps(f"$p=Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue;if($p){{@{{pid=$p.Id;session=$p.SessionId;birthTicks=$p.StartTime.ToUniversalTime().Ticks;path=$p.Path}}|ConvertTo-Json -Compress}};exit 0")
    return json.loads(data) if data else None

def provider():
    env=os.environ.get('DESKHELPER_PARADESK_DATA')
    if not env: raise Failure('PROVIDER_REQUIRED','Set DESKHELPER_PARADESK_DATA to the existing ParaDesk data directory. Authenticate manually once; this helper never opens a login prompt.')
    path=Path(env).resolve(); s=read(path/'state.json'); settings=read(path/'settings.json')
    profiles=[p for p in settings.get('profiles',[]) if p.get('name')==s.get('profile')]
    audio={'configuredMode':profiles[0].get('desktopAudio') if profiles else None,'configuredMuted':bool(profiles and profiles[0].get('desktopAudio')==2),'runtimeVerified':False,'isolationVerified':False,'detail':'ParaDesk maps profile mode 2 to RDP mute; saved settings alone do not prove the active connection or arbitrary endpoint playback is silent.'}
    return path,s,audio

def live_provider(viewer):
    # Windowless, bounded status-only IPC. The native probe pins the actual pipe
    # server PID and birth; the provider's saved child/connection fields are unused.
    import tempfile
    directory=state_root().parent/'cache'/'windows'/'provider-status'
    directory.mkdir(parents=True,exist_ok=True);restrict_directory(directory)
    exe=compile_worker()
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        output=Path(temporary)/'status.json'
        try:
            result=subprocess.run([str(exe),'--provider-status',str(output),str(viewer['pid']),str(viewer['birthTicks'])],capture_output=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
            response=read(output)
        except (OSError,ValueError,subprocess.TimeoutExpired):
            raise Failure('PROVIDER_UNAVAILABLE','Live ParaDesk status could not be verified; no cached fallback or reconnect attempted') from None
        if result.returncode or not response.get('ok'):
            raise Failure('PROVIDER_UNAVAILABLE','Live ParaDesk status could not be verified; no cached fallback or reconnect attempted')
        return response['snapshot']

def require_provider():
    path,cached,audio=provider();parent=console_id()
    # The selected data directory discovers only the existing PID. Even connected
    # cached state is never sufficient evidence for readiness or a connection ID.
    pid=cached.get('pid')
    if type(pid) is not int or pid<=0:raise Failure('PROVIDER_UNAVAILABLE','No existing provider PID is available; no provider launched')
    p=process(pid)
    if not p or p['session']!=parent:raise Failure('PARENT_MISMATCH','ParaDesk viewer is not in the active console session')
    s=live_provider(p);child=s.get('childSessionId',-1)
    if s.get('pid')!=pid:raise Failure('PARENT_MISMATCH','Live ParaDesk status does not match the selected provider PID')
    if s.get('running') is not True or s.get('attached') is not True or not s.get('connectedAt') or s.get('desktopState')!='connected' or s.get('childSessionExists') is not True or type(child) is not int or child in (-1,0,parent) or child<0 or native_state(child)!=0:
        raise Failure('AUTHENTICATED_SESSION_REQUIRED','No connected active non-console ParaDesk child exists. Existing authentication is required; no reconnect or sign-in attempted.')
    return path,s,audio,p

def state_root(): return Path(os.environ.get('DESKHELPER_STATE_ROOT',str(Path(os.environ['LOCALAPPDATA'])/'DesktopSessionHelper'))).resolve()/'windows'
def instance(name):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name):raise Failure('INVALID_ID','Use 1–64 ASCII letters, digits, underscores, or hyphens')
    return state_root()/name

@contextmanager
def instance_lock(name):
    # Serialize lifecycle mutations so stop cannot clean a later attachment.
    import msvcrt
    base=instance(name);base.mkdir(parents=True,exist_ok=True)
    with (base/'lifecycle.lock').open('a+b') as lock:
        lock.seek(0,2)
        if not lock.tell():lock.write(b'0');lock.flush()
        deadline=time.monotonic()+25
        while True:
            try:
                lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:
                if time.monotonic()>=deadline:raise Failure('BUSY','Another lifecycle operation owns this instance; no action performed')
                time.sleep(.05)
        try:yield
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

def generation(meta):
    # Pre-generation bindings also used a unique immutable IPC directory.
    actual=Path(meta['ipc']).name
    if meta.get('generation',actual)!=actual:raise Failure('OWNERSHIP_MISMATCH','Saved generation does not match its IPC directory')
    return actual

def expect_generation(meta, expected):
    if expected is not None and expected!=generation(meta):
        raise Failure('generation_changed','The requested attachment generation is no longer current; no action performed')

def restrict_directory(path):
    """Set only the owned directory DACL; do not request SACL/SeSecurityPrivilege."""
    from ctypes import wintypes
    advapi=ctypes.WinDLL('advapi32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.LocalFree.argtypes=[ctypes.c_void_p]
    advapi.OpenProcessToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]
    advapi.GetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes=[ctypes.c_void_p,ctypes.POINTER(wintypes.LPWSTR)]
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.DWORD)]
    advapi.GetSecurityDescriptorDacl.argtypes=[ctypes.c_void_p,ctypes.POINTER(wintypes.BOOL),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.BOOL)]
    advapi.SetNamedSecurityInfoW.argtypes=[wintypes.LPWSTR,ctypes.c_int,wintypes.DWORD,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
    advapi.SetNamedSecurityInfoW.restype=wintypes.DWORD
    token=wintypes.HANDLE();sid_text=wintypes.LPWSTR();descriptor=ctypes.c_void_p()
    try:
        if not advapi.OpenProcessToken(kernel.GetCurrentProcess(),8,ctypes.byref(token)):raise ctypes.WinError(ctypes.get_last_error())
        size=wintypes.DWORD();advapi.GetTokenInformation(token,1,None,0,ctypes.byref(size))
        info=ctypes.create_string_buffer(size.value)
        if not advapi.GetTokenInformation(token,1,info,size,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        sid=ctypes.cast(info,ctypes.POINTER(ctypes.c_void_p))[0]
        if not advapi.ConvertSidToStringSidW(sid,ctypes.byref(sid_text)):raise ctypes.WinError(ctypes.get_last_error())
        sddl='D:P(A;OICI;FA;;;'+sid_text.value+')(A;OICI;FA;;;SY)'
        if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,ctypes.byref(descriptor),None):raise ctypes.WinError(ctypes.get_last_error())
        present=wintypes.BOOL();defaulted=wintypes.BOOL();dacl=ctypes.c_void_p()
        if not advapi.GetSecurityDescriptorDacl(descriptor,ctypes.byref(present),ctypes.byref(dacl),ctypes.byref(defaulted)) or not present.value:raise ctypes.WinError(ctypes.get_last_error())
        error=advapi.SetNamedSecurityInfoW(str(path),1,0x80000004,None,None,dacl,None)
        if error:raise ctypes.WinError(error)
    finally:
        if descriptor:kernel.LocalFree(descriptor)
        if sid_text:kernel.LocalFree(sid_text)
        if token:kernel.CloseHandle(token)

def compile_worker():
    digest=hashlib.sha256(b''.join((HERE/name).read_bytes() for name in ('Worker.cs','NativeSupport.cs','ProviderStatus.cs','KeyHold.cs'))).hexdigest(); dest=state_root().parent/'cache'/'windows'/digest; exe=dest/'Worker.exe'
    if not exe.exists():
        dest.mkdir(parents=True,exist_ok=True)
        compiler=Path(os.environ['WINDIR'])/'Microsoft.NET'/'Framework64'/'v4.0.30319'/'csc.exe'
        temporary=dest/('Worker-'+uuid.uuid4().hex+'.exe')
        p=subprocess.run([str(compiler),'/nologo','/target:winexe',f'/out:{temporary}','/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Web.Extensions.dll',str(HERE/'Worker.cs'),str(HERE/'NativeSupport.cs'),str(HERE/'ProviderStatus.cs'),str(HERE/'KeyHold.cs')],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode:
            temporary.unlink(missing_ok=True);raise Failure('BUILD_FAILED',p.stdout+p.stderr)
        try:
            if not exe.exists():temporary.replace(exe)
        finally:temporary.unlink(missing_ok=True)
    return exe

def task(name,exe,argv,session):
    # No triggers, passwords, elevated token, or session lifecycle operations.
    arguments=subprocess.list2cmdline([str(a) for a in argv])
    script=f"""$svc=New-Object -ComObject Schedule.Service;$svc.Connect();$f=$svc.GetFolder('\\');$d=$svc.NewTask(0);$u=[Security.Principal.WindowsIdentity]::GetCurrent().Name;$d.RegistrationInfo.Description='Owned Desktop Session Helper task';$d.Principal.UserId=$u;$d.Principal.LogonType=3;$d.Principal.RunLevel=0;$d.Settings.ExecutionTimeLimit='PT0S';$d.Settings.DisallowStartIfOnBatteries=$false;$d.Settings.StopIfGoingOnBatteries=$false;$a=$d.Actions.Create(0);$a.Path={quote(exe)};$a.Arguments={quote(arguments)};$a.WorkingDirectory={quote(exe.parent)};$t=$f.RegisterTaskDefinition({quote(name)},$d,6,$u,$null,3,$null);$null=$t.RunEx($null,4,{int(session)},$null)"""
    ps(script)

def delete_tasks(meta):
    for name in meta.get('tasks',[]):
        if not name.startswith('DesktopSessionHelper-'+meta['token']+'-'):raise Failure('OWNERSHIP_MISMATCH','Task name does not match helper ownership token')
        ps(f"$s=New-Object -ComObject Schedule.Service;$s.Connect();$f=$s.GetFolder('\\');try{{$t=$f.GetTask({quote(name)})}}catch{{$t=$null}};if($t){{if($t.GetInstances(0).Count -gt 0){{throw 'Owned task is still running; not forcibly ending it'}};$f.DeleteTask({quote(name)},0)}}")

def load_binding(name):
    base=instance(name);meta=read(base/'binding.json');folder=Path(meta['ipc'])
    if meta.get('id')!=name or meta.get('root')!=str(base) or folder.parent!=base/'runs' or not re.fullmatch(r'[a-f0-9]{32}',folder.name):raise Failure('OWNERSHIP_MISMATCH','Saved helper identity does not match requested instance')
    generation(meta)
    return folder,meta

def bound(name):
    folder,meta=load_binding(name)
    p=process(meta['workerPid'])
    if not p or p['birthTicks']!=meta['workerBirthTicks'] or p['session']!=meta['childSessionId'] or Path(p['path']).resolve()!=Path(meta['exe']).resolve():raise Failure('WORKER_UNAVAILABLE','Bound worker no longer exists with its recorded birth identity; no fallback to another session')
    if read(folder/'ready.json').get('session',{}).get('generation')!=generation(meta):raise Failure('REATTACH_REQUIRED','This worker predates generation-bound commands; stop it and attach again')
    return folder,meta

def request(folder, payload):
    if 'expectGeneration' in payload and read(folder/'ready.json').get('session',{}).get('generation')!=folder.name:
        raise Failure('REATTACH_REQUIRED','This worker cannot enforce generation-bound commands; no request sent')
    token=uuid.uuid4().hex; save(folder/'requests'/f'{token}.json',payload)
    path=folder/'responses'/f'{token}.json'
    try:
        data=wait_file(path);remove_transient(path);return data
    finally:
        remove_transient(folder/'requests'/f'{token}.json')

def attach(name,hide):
    base=instance(name)
    if (base/'binding.json').exists():
        root,meta=bound(name)
        if hide and not meta.get('hideViewer'):raise Failure('ALREADY_ATTACHED','Existing attachment did not own viewer hiding. Stop it before attaching with --hide-viewer.')
        return request(root,{'action':'status'})
    path,s,audio,p=require_provider();exe=compile_worker();folder=base/'runs'/uuid.uuid4().hex;folder.mkdir(parents=True,exist_ok=True)
    # Restrict the newly-created IPC directory to its current user and SYSTEM.
    restrict_directory(base)
    for f in ['parent.json','ready.json','stopped.json','viewer-ready.json','viewer-stopped.json','viewer-stop.flag']:
        (folder/f).unlink(missing_ok=True)
    token=uuid.uuid4().hex; names=[f'DesktopSessionHelper-{token}-{part}' for part in ['inspect','worker','viewer']]
    pending={'id':name,'root':str(folder),'token':token,'tasks':names,'exe':str(exe)}
    save(folder/'attach-pending.json',pending)
    try:
        task(names[0],exe,['--inspect',folder/'parent.json',s['pid']],p['session']); parent=wait_file(folder/'parent.json')
        if not parent['childQuerySucceeded'] or parent['childSessionId']!=s['childSessionId'] or parent['childState']!=0 or parent['parentSessionId']!=parent['consoleSessionId'] or parent['viewerBirthTicks']!=p['birthTicks'] or not parent['viewerHwnd'] or parent['viewerMinimized']:
            raise Failure('RELATIONSHIP_MISMATCH','Native WTS parent/child relationship or usable viewer state could not be verified')
        task(names[1],exe,[folder,path,name,s['childSessionId'],p['session'],s['pid'],s['connectedAt'],p['birthTicks']],s['childSessionId']); ready=wait_file(folder/'ready.json')
        if not ready['ok']:raise Failure(ready['error']['code'],ready['error']['message'])
        meta={'id':name,'generation':folder.name,'root':str(base),'ipc':str(folder),'token':token,'tasks':names,'exe':str(exe),'provider':str(path),'parentSessionId':p['session'],'childSessionId':s['childSessionId'],'viewerPid':s['pid'],'viewerBirthTicks':p['birthTicks'],'workerPid':ready['session']['workerPid'],'workerBirthTicks':ready['session']['workerBirthTicks'],'connectedAt':s.get('connectedAt'),'hideViewer':hide,'audio':audio}
        save(base/'binding.json',meta);save(folder/'binding.json',meta)
        task(names[2],exe,['--viewer',folder,s['pid'],s['childSessionId'],'hide' if hide else 'observe'],p['session']); view=wait_file(folder/'viewer-ready.json')
        ready['result']={'attachedExisting':True,'ownsNativeSession':False,'viewer':view,'audio':audio,'capabilities':{'nativeInput':True,'desktopCapture':True,'genericExec':True,'audioIsolationVerified':False},'bindingPath':str(base/'binding.json')}
        (folder/'attach-pending.json').unlink(missing_ok=True)
        return ready
    except Exception as original:
        # Scope cleanup to this attempt's random task names and verified worker birth.
        cleanup_errors=[]
        try:
            ready=read(folder/'ready.json')
            p=process(ready['session']['workerPid'])
            if p and p['birthTicks']==ready['session']['workerBirthTicks'] and Path(p['path']).resolve()==exe.resolve():
                request(folder,{'action':'stop'});wait_file(folder/'stopped.json',3)
        except Exception as error:
            if (folder/'ready.json').exists() and read(folder/'ready.json').get('ok'):cleanup_errors.append(str(error))
        (folder/'viewer-stop.flag').write_text('attach rollback',encoding='utf-8')
        if (folder/'viewer-ready.json').exists():
            try:wait_file(folder/'viewer-stopped.json',3)
            except Exception as error:cleanup_errors.append(str(error))
        time.sleep(.3)
        try:delete_tasks(pending)
        except Exception as error:cleanup_errors.append(str(error))
        (base/'binding.json').unlink(missing_ok=True)
        if cleanup_errors:raise Failure('ATTACH_ROLLBACK_INCOMPLETE','Attach failed; owned cleanup needs attention: '+'; '.join(cleanup_errors)) from original
        (folder/'attach-pending.json').unlink(missing_ok=True)
        raise

def stop(name, expected_generation=None):
    folder,meta=load_binding(name)
    # Needed for cleanup when the worker is already absent. The lifecycle lock
    # protects this binding until cleanup completes; live stop checks again in-worker.
    expect_generation(meta,expected_generation)
    p=process(meta['workerPid'])
    if p and p['birthTicks']==meta['workerBirthTicks'] and p['session']==meta['childSessionId'] and Path(p['path']).resolve()==Path(meta['exe']).resolve():
        guard={'expectGeneration':expected_generation} if expected_generation is not None else {}
        data=request(folder,{'action':'stop',**guard})
        if not data['ok']:return data
        wait_file(folder/'stopped.json')
    else:
        data={'ok':True,'platform':'windows','session':{'id':name,'generation':generation(meta),'capabilities':{'capture':False,'input':False,'keyboard':False,'key_hold':False,'pointer':False,'exec':False,'audio_capture':False,'audio_silent':False,'browser':False,'accessibility':False}},'result':{'workerAlreadyAbsent':True,'childPreserved':True}}
        (folder/'viewer-stop.flag').write_text('stop stale attachment',encoding='utf-8')
    wait_file(folder/'viewer-stopped.json');time.sleep(.25);delete_tasks(meta)
    (Path(meta['root'])/'binding.json').replace(Path(meta['root'])/'stopped-binding.json')
    data['session']['state']='stopped';data['session']['generation']=generation(meta)
    data['session'].setdefault('capabilities',{'audio_capture':False,'audio_silent':False,'browser':False,'accessibility':False})
    for capability in ('capture','input','keyboard','key_hold','pointer','exec'):data['session']['capabilities'][capability]=False
    data['result']['viewer']=read(folder/'viewer-stopped.json');return data

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    app=[]
    if args and args[0]=='exec' and '--' in args:
        i=args.index('--');app=args[i+1:];args=args[:i]
    # Only normalize the input command; application argv is already separate.
    if args and args[0]=='input' and '--type' in args:
        i=args.index('--type')
        if i+1<len(args):args[i:i+2]=['--type='+args[i+1]]
    parser=JsonParser();parser.add_argument('command',choices=['doctor','start','attach','status','exec','capture','input','stop','view']);parser.add_argument('--id');parser.add_argument('--expect-generation');parser.add_argument('--hide-viewer',action='store_true');parser.add_argument('--frame',action='store_true');parser.add_argument('--output');parser.add_argument('--type');parser.add_argument('--key');parser.add_argument('--hold-ms',type=int,help='Hold a key/chord for 1-5000 ms and release in the same worker request; 0 keeps tap behavior');parser.add_argument('--click',nargs=2,type=int);parser.add_argument('--move',nargs=2,type=int);parser.add_argument('--button',type=int,choices=[1,2,3],default=1)
    a=parser.parse_args(args)
    if a.command!='doctor' and not a.id:raise Failure('INVALID_ARGUMENT','An explicit --id is required for session commands')
    if a.expect_generation is not None and a.command not in ('status','capture','input','exec','stop','view'):raise Failure('INVALID_ARGUMENT','--expect-generation is supported for status, capture, input, exec, and stop')
    if a.frame and a.command!='view':raise Failure('INVALID_ARGUMENT','--frame is a view option only')
    if a.command=='view' and (not a.frame or not a.expect_generation):raise Failure('INVALID_ARGUMENT','Windows view requires --frame and --expect-generation; it never opens a local window or attaches')
    if a.hold_ms is not None and (a.command!='input' or a.key is None or not 0<=a.hold_ms<=5000 or any(v is not None for v in (a.type,a.click,a.move))):raise Failure('INVALID_ARGUMENT','--hold-ms requires input --key and an integer from 0 to 5000')
    if os.name!='nt':raise Failure('WRONG_PLATFORM','This adapter must run on Windows; use SSH as an outer transport if needed')
    if a.command=='doctor':
        path,s,audio,p=require_provider()
        return {'ok':True,'platform':'windows','session':{'id':a.id,'state':'available','nativeSessionId':s['childSessionId'],'parentSessionId':p['session']},'result':{'providerData':str(path),'nativeRelationshipVerified':False,'relationshipCheck':'Verified with WTSGetChildSessionId during attach','audio':audio,'requiresAuthenticatedExistingChild':True,'autoReconnect':False,'createsSession':False,'compilerAvailable':(Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe').exists()}}
    if a.command=='start':raise Failure('EXISTING_SESSION_REQUIRED','Windows backend does not create or authenticate sessions. Use attach for an already authenticated ParaDesk child; no sign-in triggered.')
    if a.command=='attach':
        with instance_lock(a.id):return attach(a.id,a.hide_viewer)
    if a.command=='stop':
        with instance_lock(a.id):return stop(a.id,a.expect_generation)
    folder,meta=bound(a.id)
    # The worker enforces this token at the action boundary in its immutable IPC generation.
    guard={'expectGeneration':a.expect_generation} if a.expect_generation is not None else {}
    if a.command=='view':return request(folder,{'action':'frame',**guard})
    if a.command=='status':
        data=request(folder,{'action':'status',**guard})
        if data['ok']:
            audio=dict(meta['audio']);runtime=data['result'].get('audioRuntime',{});audio.update({'runtimeVerified':'error' not in runtime,'silentDefaultOutput':runtime.get('silentDefaultOutput',False),'detail':'Current child endpoint measurement is reported in audioRuntime; each exec/input rechecks it. No playback or driver/security sandbox guarantee.'})
            data['result'].update({'audio':audio,'connectedAt':meta['connectedAt'],'ownsNativeSession':False})
        return data
    if a.command=='exec':
        if not app:raise Failure('INVALID_ARGUMENT','exec requires -- PROGRAM ARG...')
        return request(folder,{'action':'exec','argv':app,**guard})
    if a.command=='capture':
        if not a.output:raise Failure('INVALID_ARGUMENT','capture requires --output PATH')
        output=Path(a.output).resolve();data=request(folder,{'action':'capture','output':str(output),**guard})
        if data['ok']:data['result']['capturedAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        return data
    if sum(v is not None for v in [a.type,a.key,a.click,a.move])!=1:raise Failure('INVALID_ARGUMENT','input needs exactly one of --type, --key, --click, --move')
    if a.type is not None:payload={'kind':'type','text':a.type}
    elif a.key is not None:
        payload={'kind':'key','key':a.key}
        if a.hold_ms is not None:
            if a.hold_ms and read(folder/'ready.json').get('session',{}).get('capabilities',{}).get('key_hold') is not True:raise Failure('REATTACH_REQUIRED','Existing worker does not support key_hold; save owned work and explicitly stop/attach with the updated helper')
            payload['holdMs']=a.hold_ms
    else:
        x,y=a.click if a.click else a.move;payload={'kind':'click' if a.click else 'move','x':x,'y':y,'button':a.button}
    return request(folder,{'action':'input',**payload,**guard})

if __name__=='__main__':
    try: response=main()
    except Failure as e:response={'ok':False,'platform':'windows','session':{'state':'unavailable'},'error':{'code':e.code,'message':e.message}}
    except Exception as e:response={'ok':False,'platform':'windows','session':{'state':'unavailable'},'error':{'code':'ADAPTER_ERROR','message':str(e)}}
    print(json.dumps(response,separators=(',',':')));sys.exit(0 if response['ok'] else 1)

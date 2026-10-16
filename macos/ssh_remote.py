"""Read-only isolated-desktop frame transport over the user's existing SSH authentication."""
from __future__ import annotations
import base64, hashlib, json, math, os, re, shlex, subprocess, time
from pathlib import Path
try:
    from . import vm_adapter as vm
except ImportError:
    import vm_adapter as vm

MAX_IMAGE = 16 * 1024 * 1024
MAX_REPLY = 24 * 1024 * 1024

class RemoteError(vm.VMError):
    def __init__(self, code, message): self.code=code;super().__init__(message)

def target(host, command='quietwing', state=None, platform='linux', identity=None):
    if platform not in ('linux','windows'):raise RemoteError('invalid_remote_target','Remote platform must be linux or windows')
    if not isinstance(host,str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.@:-]{0,254}',host):
        raise RemoteError('invalid_remote_target','Use a plain SSH host or user@host; options belong in your SSH config')
    if not isinstance(command,str) or not command or len(command)>4096 or any(ord(c)<32 for c in command) or command.startswith('-'):
        raise RemoteError('invalid_remote_target','Remote command must be one executable name/path')
    absolute = (lambda path: path.startswith('/')) if platform=='linux' else (lambda path: re.match(r'^[A-Za-z]:[\\/]',path))
    if state is not None and (not isinstance(state,str) or not absolute(state) or len(state)>4096 or any(ord(c)<32 for c in state)):
        raise RemoteError('invalid_remote_target','Remote state root must be an absolute '+platform+' path')
    result={'kind':platform+'-ssh','host':host,'command':command,'stateRoot':state}
    if identity is not None:
        if not isinstance(identity,str) or not identity.startswith('/') or len(identity)>4096 or any(ord(c)<32 for c in identity):
            raise RemoteError('invalid_remote_target','SSH identity must be an absolute local key-file path')
        result['identityFile']=identity
    return result

def validate(source):
    if not isinstance(source,dict) or source.get('kind') not in ('linux-ssh','windows-ssh'):
        raise RemoteError('invalid_remote_target','Invalid stored remote target')
    if source != target(source.get('host'),source.get('command'),source.get('stateRoot'),source['kind'].removesuffix('-ssh'),source.get('identityFile')):
        raise RemoteError('invalid_remote_target','Invalid stored remote target')
    return source

def ssh_argv(source, operation, name, generation=None):
    validate(source)
    platform=source['kind'].removesuffix('-ssh')
    pattern=r'[A-Za-z0-9][A-Za-z0-9_.-]{0,47}' if platform=='linux' else r'[A-Za-z0-9_-]{1,64}'
    if not re.fullmatch(pattern,name):raise RemoteError('invalid_id','Invalid '+platform+' session ID')
    if operation not in ('status','frame'):raise RemoteError('readonly_transport','Only status and isolated frames are supported')
    argv=[source['command'],'status' if operation=='status' else 'view','--id',name]
    if operation=='frame':argv+=['--frame']
    if generation is not None:argv+=['--expect-generation',generation]
    if platform=='windows':
        # Windows OpenSSH may use cmd.exe or PowerShell. Only a fixed executable
        # and a base64 UTF-16 script cross that outer shell; all values are single
        # quoted inside the decoded script, never interpolated or evaluated.
        quote=lambda value: "'"+value.replace("'","''")+"'"
        script="$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        if source['stateRoot'] is not None:script+='$env:DESKHELPER_STATE_ROOT='+quote(source['stateRoot'])+';'
        script+='& '+' '.join(map(quote,argv))+';exit $LASTEXITCODE'
        remote_command='powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand '+base64.b64encode(script.encode('utf-16le')).decode()
    else:
        if source['stateRoot'] is not None:argv=['env','DESKHELPER_STATE_ROOT='+source['stateRoot'],*argv]
        remote_command=shlex.join(argv)
    # No interactive prompts, forwarding or persistent SSH client.
    return ['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','ServerAliveInterval=5',
            '-o','ServerAliveCountMax=1','-o','ClearAllForwardings=yes','-o','ForwardX11=no',
            '-o','ForwardAgent=no','-o','PermitLocalCommand=no','-o','RemoteCommand=none','-o','ControlMaster=no','-o','ControlPath=none','-o','StrictHostKeyChecking=yes',
            *(['-o','IdentitiesOnly=yes','-i',source['identityFile']] if source.get('identityFile') else []),source['host'],remote_command]

def call(source, operation, name, generation=None):
    import tempfile
    # Bound output even for a noisy/misconfigured remote executable. Temporary
    # files are private and anonymous; no frame history is retained.
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
        proc=subprocess.Popen(ssh_argv(source,operation,name,generation),stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        deadline=time.monotonic()+10
        try:
            while proc.poll() is None:
                if os.fstat(out.fileno()).st_size>MAX_REPLY or os.fstat(err.fileno()).st_size>65536:
                    raise RemoteError('remote_reply_too_large','Remote output exceeded the bounded viewer protocol')
                if time.monotonic()>deadline:raise RemoteError('remote_timeout','SSH frame request timed out; close and reopen the viewer')
                time.sleep(.02)
            out.seek(0);raw=out.read(MAX_REPLY+1)
            if len(raw)>MAX_REPLY or os.fstat(err.fileno()).st_size>65536:
                raise RemoteError('remote_reply_too_large','Remote output exceeded the bounded viewer protocol')
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=1)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
    if proc.returncode and not raw:raise RemoteError('remote_unavailable','SSH/helper unavailable; verify the existing noninteractive SSH login and remote command')
    try:value=json.loads(raw)
    except (ValueError,UnicodeError):raise RemoteError('remote_protocol','Remote helper did not return one JSON envelope') from None
    platform=source['kind'].removesuffix('-ssh')
    if not isinstance(value,dict) or value.get('schemaVersion')!=1 or type(value.get('ok')) is not bool or value.get('platform')!=platform:
        raise RemoteError('remote_protocol','Expected matching QuietWing '+platform+' protocol version 1')
    if not value['ok']:
        error=value.get('error',{})
        code=error.get('code','remote_unavailable') if isinstance(error,dict) else 'remote_protocol'
        if operation=='frame' and code in ('INVALID_ARGUMENT','unsupported_operation','unknown_command'):
            raise RemoteError('remote_viewer_unsupported','Install a matching QuietWing development build on '+platform+' for view --frame')
        raise RemoteError(code,'Remote session unavailable; inspect its status and explicitly reopen when ready')
    if proc.returncode:raise RemoteError('remote_protocol','Remote helper claimed success but exited unsuccessfully')
    s=value.get('session',{});d=value.get('descriptor',{})
    if not isinstance(s,dict) or not isinstance(d,dict) or not isinstance(s.get('capabilities'),dict) or not isinstance(d.get('capabilities'),dict):
        raise RemoteError('remote_protocol','Invalid session/descriptor objects')
    actual=s.get('generation')
    if s.get('id')!=name or d.get('id')!=name or d.get('platform')!=platform or d.get('schemaVersion')!=1:
        raise RemoteError('remote_protocol','Remote session/descriptor identity does not match the requested target')
    if generation is not None and actual!=generation:raise RemoteError('generation_changed','Remote session generation changed')
    state='running' if platform=='linux' else 'attached'
    isolated=(s['capabilities'].get('private_display') is True) if platform=='linux' else (type(s.get('nativeSessionId')) is int and type(s.get('parentSessionId')) is int and s['nativeSessionId']>0 and s['parentSessionId']>0 and s['nativeSessionId']!=s['parentSessionId'])
    capture=d['capabilities'].get('capture') is True and (platform=='linux' or s['capabilities'].get('capture') is True)
    if s.get('state')!=state or d.get('state')!=state or not isinstance(actual,str) or not actual or not isolated or not capture:
        raise RemoteError('session_unavailable','No verified live isolated '+platform+' desktop; acquire it explicitly first')
    if d.get('generation')!=actual:raise RemoteError('remote_protocol','Running descriptor generation does not match session')
    return value

def frame(source,name,generation):
    value=call(source,'frame',name,generation)
    result=value.get('result',{})
    if not isinstance(result,dict):raise RemoteError('invalid_capture','Invalid frame result')
    image=result.get('image',{})
    if not isinstance(image,dict):raise RemoteError('invalid_capture','Invalid image envelope')
    if image.get('encoding')!='base64' or image.get('mimeType')!='image/png' or image.get('only_owned_guest_view') is not True:
        raise RemoteError('invalid_capture','Remote frame lacks isolated-image provenance')
    try:data=base64.b64decode(image['data'],validate=True)
    except (KeyError,ValueError,TypeError):raise RemoteError('invalid_capture','Invalid encoded frame') from None
    if len(data)>MAX_IMAGE or len(data)<24 or data[:8]!=b'\x89PNG\r\n\x1a\n' or data[12:16]!=b'IHDR':
        raise RemoteError('invalid_capture','Expected a bounded PNG frame')
    width=int.from_bytes(data[16:20],'big');height=int.from_bytes(data[20:24],'big')
    s=value['session'];at=image.get('captured_at')
    if (width,height)!=(image.get('width'),image.get('height')) or (width,height)!=(s.get('width'),s.get('height')) or not 320<=width<=4096 or not 240<=height<=2160 or hashlib.sha256(data).hexdigest()!=image.get('sha256'):
        raise RemoteError('invalid_capture','Frame dimensions or digest did not match the isolated session')
    if not isinstance(at,(float,int)) or not math.isfinite(at):raise RemoteError('invalid_capture','Invalid frame timestamp')
    # Freshness is measured locally after each successful synchronous capture;
    # Remote and Mac wall clocks need not agree.
    return data,{'capturedAt':time.time(),'remoteCapturedAt':at,'width':width,'height':height}

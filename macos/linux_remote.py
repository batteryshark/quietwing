"""Read-only Linux frame transport over the user's existing SSH authentication."""
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

def target(host, command='quietwing', state=None):
    if not isinstance(host,str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.@:-]{0,254}',host):
        raise RemoteError('invalid_remote_target','Use a plain SSH host or user@host; options belong in your SSH config')
    if not isinstance(command,str) or not command or len(command)>4096 or any(ord(c)<32 for c in command) or command.startswith('-'):
        raise RemoteError('invalid_remote_target','Remote command must be one executable name/path')
    if state is not None and (not state.startswith('/') or len(state)>4096 or any(ord(c)<32 for c in state)):
        raise RemoteError('invalid_remote_target','Remote state root must be an absolute Linux path')
    return {'kind':'linux-ssh','host':host,'command':command,'stateRoot':state}

def validate(source):
    if source != target(source.get('host'),source.get('command'),source.get('stateRoot')):
        raise RemoteError('invalid_remote_target','Invalid stored remote target')
    return source

def ssh_argv(source, operation, name, generation=None):
    validate(source)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,47}',name):raise RemoteError('invalid_id','Invalid Linux session ID')
    if operation not in ('status','frame'):raise RemoteError('readonly_transport','Only status and isolated frames are supported')
    argv=[source['command'],'status' if operation=='status' else 'view','--id',name]
    if operation=='frame':argv+=['--frame']
    if generation is not None:argv+=['--expect-generation',generation]
    if source['stateRoot'] is not None:argv=['env','DESKHELPER_STATE_ROOT='+source['stateRoot'],*argv]
    # SSH invokes a remote shell; quote every literal argument as a single command.
    return ['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','ServerAliveInterval=5',
            '-o','ServerAliveCountMax=1','-o','ClearAllForwardings=yes','-o','ForwardX11=no',
            '-o','ForwardAgent=no','-o','PermitLocalCommand=no','-o','RemoteCommand=none','-o','ControlMaster=no','-o','ControlPath=none','-o','StrictHostKeyChecking=yes',
            source['host'],shlex.join(argv)]

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
    if not isinstance(value,dict) or value.get('schemaVersion')!=1 or type(value.get('ok')) is not bool or value.get('platform')!='linux':
        raise RemoteError('remote_protocol','Expected QuietWing Linux protocol version 1')
    if not value['ok']:
        error=value.get('error',{})
        code=error.get('code','remote_unavailable') if isinstance(error,dict) else 'remote_protocol'
        if operation=='frame' and code in ('INVALID_ARGUMENT','unsupported_operation','unknown_command'):
            raise RemoteError('remote_viewer_unsupported','Install a matching QuietWing development build on Linux for view --frame')
        raise RemoteError(code,'Linux session unavailable; inspect its status and explicitly reopen when ready')
    if proc.returncode:raise RemoteError('remote_protocol','Remote helper claimed success but exited unsuccessfully')
    s=value.get('session',{});d=value.get('descriptor',{})
    if not isinstance(s,dict) or not isinstance(d,dict) or not isinstance(s.get('capabilities'),dict) or not isinstance(d.get('capabilities'),dict):
        raise RemoteError('remote_protocol','Invalid session/descriptor objects')
    actual=s.get('generation')
    if s.get('id')!=name or d.get('id')!=name or d.get('platform')!='linux' or d.get('schemaVersion')!=1:
        raise RemoteError('remote_protocol','Remote session/descriptor identity does not match the requested target')
    if generation is not None and actual!=generation:raise RemoteError('generation_changed','Remote session generation changed')
    if s.get('state')!='running' or d.get('state')!='running' or not isinstance(actual,str) or not actual or s.get('capabilities',{}).get('private_display') is not True or d.get('capabilities',{}).get('capture') is not True:
        raise RemoteError('session_unavailable','No verified running isolated Linux desktop; start it explicitly first')
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
    # Linux and Mac wall clocks need not agree.
    return data,{'capturedAt':time.time(),'remoteCapturedAt':at,'width':width,'height':height}

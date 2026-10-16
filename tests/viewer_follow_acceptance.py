#!/usr/bin/env python3
"""Mac native preview acceptance with a local fake SSH executable, never a host desktop.

Run with an installed candidate: python tests/viewer_follow_acceptance.py
  --command /private/candidate/bin/quietwing --output /private/fresh-output
  --platform windows|linux
Only the preview is real. Desktop/transport lifecycle is synthetic and local.
"""
import argparse, base64, hashlib, json, os, re, shlex, struct, subprocess, sys, time, zlib
from pathlib import Path


def write(path, value):
    temporary=path.with_suffix('.pending')
    temporary.write_text(json.dumps(value)); temporary.chmod(0o600); temporary.replace(path)


def read(path):
    try: return json.loads(path.read_text())
    except FileNotFoundError: return {}


def png():
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',320,240,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x30\x80\xc0'*320)*240))+chunk(b'IEND',b'')


def fake_ssh(argv):
    root=Path(os.environ['QUIETWING_FOLLOW_FIXTURE'])
    fixture=read(root/'fixture.json'); platform=fixture['platform']
    assert argv[-2]=='fixture.invalid', 'Fixture must never reach a real SSH target'
    command=argv[-1]
    if platform=='windows':
        prefix='powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand '
        assert command.startswith(prefix)
        script=base64.b64decode(command[len(prefix):]).decode('utf-16le')
        assert "& 'quietwing' '" in script
        operation='frame' if "'view' '--id' 'follow-fixture' '--frame'" in script else 'status'
        assert operation=='frame' or "'status' '--id' 'follow-fixture'" in script
        match=re.search(r"'--expect-generation' '([^']+)'",script)
        expected=match.group(1) if match else None
    else:
        parts=shlex.split(command)
        assert parts[:1]==['quietwing'] and parts[2:4]==['--id','follow-fixture']
        assert parts[1] in ('view','status')
        operation='frame' if parts[1]=='view' else 'status'
        expected=parts[parts.index('--expect-generation')+1] if '--expect-generation' in parts else None
    assert operation!='frame' or expected, 'Every frame must be pinned'
    record=dict(operation=operation, expected=expected, phase=fixture['phase'], at=time.time())
    with (root/'requests.jsonl').open('a') as stream: stream.write(json.dumps(record)+'\n')
    (root/'requests.jsonl').chmod(0o600)
    phase=fixture['phase']
    if phase=='offline': raise SystemExit(255)
    code='AUTHENTICATED_SESSION_REQUIRED' if platform=='windows' else 'SESSION_NOT_FOUND'
    if phase=='absent' or (phase=='busy' and operation=='frame'):
        print(json.dumps(dict(schemaVersion=1,ok=False,platform=platform,error=dict(code='SESSION_BUSY' if phase=='busy' else code,message='Controlled fixture unavailable'))))
        raise SystemExit(1)
    generation='one' if phase=='busy' else phase
    capabilities={'capture':True} if platform=='windows' else {'private_display':True}
    state='attached' if platform=='windows' else 'running'
    session=dict(id='follow-fixture',generation=generation,state=state,width=320,height=240,capabilities=capabilities)
    if platform=='windows': session.update(nativeSessionId=4,parentSessionId=1)
    descriptor=dict(schemaVersion=1,id='follow-fixture',platform=platform,generation=generation,state=state,capabilities=dict(capture=True))
    image=png()
    result={'image':dict(encoding='base64',mimeType='image/png',only_owned_guest_view=True,data=base64.b64encode(image).decode(),sha256=hashlib.sha256(image).hexdigest(),width=320,height=240,captured_at=time.time())} if operation=='frame' else {}
    print(json.dumps(dict(schemaVersion=1,ok=True,platform=platform,session=session,descriptor=descriptor,result=result)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--command',required=True); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platform',choices=['windows','linux'],required=True)
    args=p.parse_args(); root=args.output.absolute(); root.mkdir(mode=0o700)
    bin_dir=root/'bin'; bin_dir.mkdir(mode=0o700)
    script=Path(__file__).resolve()
    ssh=bin_dir/'ssh'
    ssh.write_text('#!'+sys.executable+'\nimport runpy,sys\nsys.argv=['+repr(str(script))+',"--ssh",*sys.argv[1:]]\nrunpy.run_path('+repr(str(script))+',run_name="__main__")\n'); ssh.chmod(0o700)
    env=dict(os.environ,PATH=str(bin_dir)+os.pathsep+os.environ['PATH'],DESKHELPER_STATE_ROOT=str(root/'state'),QUIETWING_FOLLOW_FIXTURE=str(root))
    def phase(value): write(root/'fixture.json',dict(phase=value,platform=args.platform))
    def requests():
        path=root/'requests.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    command=[args.command,'view','--host','fixture.invalid','--remote-platform',args.platform,'--id','follow-fixture']
    def cli(*flags):
        proc=subprocess.run([*command,*flags],env=env,text=True,capture_output=True,timeout=20)
        value=json.loads(proc.stdout); assert proc.returncode==0 and value['ok'],value
        return value['result']['viewer']
    def wait(predicate):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            value=predicate()
            if value: return value
            time.sleep(.1)
        raise AssertionError('Timed out waiting for controlled native preview; inspect '+str(root))
    phase('absent'); run=None
    try:
        result=cli('--follow'); run=Path(result['viewerRun'])
        observations=[]
        def observe():
            state=read(run/'state.json'); window=read(run/'window.json')
            if window:
                assert not window['key'] and not window['main'] and not window['becameFrontmost'],window
                observations.append(window)
            return state,window
        wait(lambda: requests())
        wait(lambda: (lambda pair: pair[0].get('state')=='waiting' and not pair[1].get('imageAvailable'))(observe()))
        first_pid=read(run/'window.json')['pid']
        def watching(generation):
            state,window=observe()
            return state.get('state')=='watching' and state.get('generation')==generation and window.get('imageAvailable') and window.get('displayedFrames')==state['frames']
        phase('one'); wait(lambda: watching('one'))
        before=len([r for r in requests() if r['operation']=='status'])
        phase('busy'); wait(lambda: (lambda pair: pair[0].get('errorCode')=='SESSION_BUSY' and not pair[1].get('imageAvailable'))(observe()))
        phase('one'); wait(lambda: watching('one'))
        assert before==len([r for r in requests() if r['operation']=='status']), 'Busy/healthy capture must not rediscover'
        phase('two'); wait(lambda: watching('two'))
        assert read(run/'window.json')['pid']==first_pid
        assert cli('--follow')['viewerRun']==str(run), 'Reopen must reuse the window'
        phase('offline'); wait(lambda: (lambda pair: pair[0].get('errorCode')=='remote_unavailable' and not pair[1].get('imageAvailable'))(observe()))
        phase('three'); wait(lambda: watching('three'))
        assert read(run/'window.json')['pid']==first_pid
        phase('absent'); wait(lambda: (lambda pair: pair[0].get('state')=='waiting' and not pair[1].get('imageAvailable'))(observe()))
        closed=cli('--close'); assert closed['state']=='closed'
        count=len(requests()); phase('four'); time.sleep(2)
        assert len(requests())==count, 'Closed viewer must stop querying'
        assert not (run/'frame.png').exists()
        assert read(run/'window-closed.json').get('closed')
        assert {w['pid'] for w in observations}=={first_pid}
        req=requests(); assert {r['operation'] for r in req}=={'status','frame'}
        receipt=dict(ok=True,platform=args.platform,observations=len(observations),windowPid=first_pid,sameWindow=True,nonactivating=True,framesPinned=True,requests=len(req),desktopLifecycle='synthetic only',remoteMachineAccess=False)
        write(root/'verification.json',receipt); print(json.dumps(receipt))
    finally:
        if run is not None and not (run/'window-closed.json').exists(): cli('--close')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--ssh': fake_ssh(sys.argv[2:])
    else: main()

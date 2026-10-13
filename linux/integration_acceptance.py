#!/usr/bin/env python3
"""Two separate SSH stages exercising staged cctl's public CLI, no host engine."""
import datetime,hashlib,json,os,pathlib,shutil,signal,subprocess,sys,threading,time
BASE=pathlib.Path(os.environ.get('CCTL_INTEGRATION_ROOT',str(pathlib.Path.home()/'Experiments/cctl-isolated')))
RUN=BASE/os.environ.get('CCTL_INTEGRATION_RUN','run-001');RUN.mkdir(mode=0o700,exist_ok=True)
ART=RUN/'evidence';ART.mkdir(mode=0o700,exist_ok=True)
LAUNCHER=pathlib.Path(os.environ.get('CCTL_INTEGRATION_LAUNCHER',str(BASE/'cctl-integration')))
COMPANION=pathlib.Path(os.environ.get('DESKHELPER_DISPATCHER',str(pathlib.Path.home()/'Experiments/desktop-session-helper/deskhelper.py')))
CONFIG=RUN/'config.toml';HELPER_ENV=dict(os.environ,DESKHELPER_STATE_ROOT=str(RUN/'helper-state'))
ID=os.environ.get('CCTL_INTEGRATION_ID','cctl-integration-001')
def dump(name,value):(ART/name).write_text(json.dumps(value,indent=2)+'\n')
def cli(tool,args=None,error=None):
    argv=[str(LAUNCHER),*(['session',args] if tool=='session' else [tool,json.dumps(args or {},ensure_ascii=False)])]
    p=subprocess.run(argv,capture_output=True,text=True,timeout=110)
    try:r=json.loads(p.stdout)
    except ValueError:raise AssertionError((argv,p.returncode,p.stdout,p.stderr))
    with (ART/'commands.jsonl').open('a') as f:f.write(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'exit':p.returncode,'response':r})+'\n')
    assert (p.returncode==0)==(error is None),(argv,r,p.stderr)
    if error:assert r['error']==error,r
    return r
def helper(*argv):
    p=subprocess.run([sys.executable,str(COMPANION),*map(str,argv)],env=HELPER_ENV,capture_output=True,text=True,timeout=100)
    r=json.loads(p.stdout);assert p.returncode==0 and r['ok'],r
    with (ART/'companion-commands.jsonl').open('a') as f:f.write(json.dumps({'argv':argv,'response':r})+'\n')
    return r
def shot(name):
    result=cli('screenshot');shutil.copy2(result['path'],ART/name);return result
def await_text(path,text):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if path.exists() and path.read_text()==text:return
        time.sleep(.05)
    raise AssertionError((str(path),path.read_text() if path.exists() else None,text))
def birth(pid):
    try:
        fields=pathlib.Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        return fields[19] if fields[0]!='Z' else None
    except FileNotFoundError:return None
def stop_own_daemon():
    found=[]
    for proc in pathlib.Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid!=os.getuid():continue
            env=(proc/'environ').read_bytes().split(b'\0');cmd=(proc/'cmdline').read_bytes()
            if b'CCTL_CONFIG='+str(CONFIG).encode() in env and b'cctl.cli\0serve\0' in cmd:
                pid=int(proc.name);start=birth(pid)
                if start and birth(pid)==start:os.kill(pid,signal.SIGTERM);found.append((pid,start))
        except (FileNotFoundError,PermissionError,ProcessLookupError):pass
    deadline=time.monotonic()+5
    while any(birth(pid)==start for pid,start in found) and time.monotonic()<deadline:time.sleep(.05)
    assert not any(birth(pid)==start for pid,start in found)
    # The staged service leaves a stale Unix socket on SIGTERM. Only its private
    # configured sockets are removed after all matching owned PIDs have exited.
    for socket in (RUN/'cache').glob('sessions/*/cctl.sock'):socket.unlink(missing_ok=True)
    return [pid for pid,_ in found]
HOST=dict(os.environ,DISPLAY=os.environ.get('CCTL_TEST_HOST_DISPLAY',':0'),
          XAUTHORITY=os.environ.get('CCTL_TEST_HOST_XAUTHORITY',str(pathlib.Path.home()/'.Xauthority')))
samples=[];ending=threading.Event()
def observe():
    while not ending.is_set():
        a=subprocess.run(['xdotool','getmouselocation','--shell'],env=HOST,capture_output=True,text=True,timeout=3)
        b=subprocess.run(['xdotool','getwindowfocus'],env=HOST,capture_output=True,text=True,timeout=3)
        point=dict(line.split('=',1) for line in a.stdout.splitlines() if '=' in line)
        samples.append({'x':int(point['X']),'y':int(point['Y']),'focus':int(b.stdout),'errors':a.stderr+b.stderr})
        ending.wait(.1)
observer=threading.Thread(target=observe,daemon=True);observer.start()
stage=sys.argv[1]
summary={'stage':stage,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'source_sha256':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/'src/cctl').glob('*.py'))},
         'companion_sha256':hashlib.sha256(COMPANION.read_bytes()).hexdigest(),
         'linux_adapter_sha256':hashlib.sha256((COMPANION.parent/'linux/adapter.py').read_bytes()).hexdigest()}
try:
    document=ART/'native-document.txt'
    if stage=='stage1':
        start=cli('session','start');summary['start']=start;generation=start['session']['generation']
        summary['doctor']=cli('doctor');document.write_text('')
        summary['app']=cli('apps',{'action':'launch','name':'mousepad','args':['--disable-server',str(document)]});time.sleep(.7)
        before=shot('before.png')
        cli('click',{'x':150,'y':100,'frame':before['frame']})
        text='-cctl two words ; $(literal) café Ω 世界'
        cli('type_text',{'text':text});cli('key',{'keys':'ctrl+s'});await_text(document,text)
        after=shot('after.png');assert (ART/'before.png').read_bytes()!=(ART/'after.png').read_bytes()
        zoom=cli('zoom',{'region':[0,50,600,200],'frame':after['frame'],'max_dim':900});shutil.copy2(zoom['path'],ART/'zoom.png')
        cli('browser_open',{'url':'about:blank'},error='unsupported_capability')
        cli('run',{'command':'printf should-not-run'},error='unsupported_capability')
        summary['native_text']=document.read_text();summary['frame']=after['frame'];summary['generation']=generation
        summary['awaiting_separate_ssh']=True
    elif stage=='stage2':
        previous=json.loads((ART/'result-stage1.json').read_text());ga=previous['generation']
        status=cli('session','status');assert status['descriptor']['generation']==ga;summary['reconnected_status']=status
        cli('key',{'keys':'ctrl+End'});cli('type_text',{'text':'\nreconnected through cctl'});cli('key',{'keys':'ctrl+s'})
        await_text(document,previous['native_text']+'\nreconnected through cctl');summary['reconnect_text']=document.read_text()
        shot('after-reconnect.png')
        summary['restarted_owned_daemon_pids']=stop_own_daemon()
        adopted=shot('after-daemon-restart.png');assert adopted['session']['generation']==ga
        summary['daemon_restart_preserved_generation']=True
        helper('stop','--id',ID,'--expect-generation',ga)
        replacement=helper('start','--id',ID,'--replace-stopped','--ttl','120');gb=replacement['descriptor']['generation'];assert gb!=ga
        cli('type_text',{'text':'STALE SHOULD NEVER ARRIVE'},error='generation_changed')
        cli('click',{'x':100,'y':100,'frame':adopted['frame']},error='generation_changed')
        cli('screenshot',error='generation_changed')
        cli('session','stop',error='generation_changed')
        assert helper('describe','--id',ID,'--expect-generation',gb)['descriptor']['state']=='running'
        rebound=cli('session','start');assert rebound['session']['generation']==gb
        cli('click',{'x':100,'y':100,'frame':adopted['frame']},error='bad_arguments')
        summary['stale_generation_and_frame_refused']=True
        summary['explicit_rebind']=rebound;shot('replacement.png')
        summary['stop']=cli('session','stop')
        assert summary['stop']['descriptor']['generation'] is None
        cli('type_text',{'text':'must not fall back'},error='session_stopped')
        summary['final_owned_daemon_pids']=stop_own_daemon()
    else:raise AssertionError('Unknown stage')
    summary['passed']=True
except Exception as exc:
    summary['passed']=False;summary['error']=repr(exc);raise
finally:
    ending.set();observer.join(timeout=5)
    dump('host-metadata-'+stage+'.json',samples)
    summary['host_samples']=len(samples);summary['host_positions']=sorted(set((s['x'],s['y']) for s in samples));summary['host_focus']=sorted(set(s['focus'] for s in samples));summary['host_errors']=[s['errors'] for s in samples if s['errors']]
    summary['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump('result-'+stage+'.json',summary);print(json.dumps(summary,indent=2))

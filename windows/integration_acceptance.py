"""Public cctl CLI acceptance against the separate Windows companion experiment."""
import datetime,json,os,shutil,subprocess,sys,time,tomllib
from pathlib import Path
import adapter
CFG=Path(os.environ['CCTL_CONFIG']);config=tomllib.loads(CFG.read_text());target=config['sessions']['integration']
os.environ.update(target['env']);os.environ['PYTHONDONTWRITEBYTECODE']='1'
OUT=Path(os.environ['DESKHELPER_ACCEPTANCE_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
BASE=adapter.instance(target['id']);calls=[];owned=[];active=None

def save(path,value):Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def call(tool,args=None,ok=True):
    argv=[sys.executable,'-m','cctl.cli','--session','integration',tool]
    argv+=(args if tool=='session' else [json.dumps(args or {})])
    p=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=125)
    try:data=json.loads(p.stdout)
    except Exception:raise AssertionError((argv,p.returncode,p.stdout,p.stderr))
    calls.append({'tool':tool,'args':args,'returncode':p.returncode,'data':data})
    assert (p.returncode==0)==ok,(tool,data,p.stderr)
    return data

def wait_for(path,predicate):
    end=time.monotonic()+6
    while time.monotonic()<end:
        try:
            value=read(path)
            if predicate(value):return value
        except (FileNotFoundError,json.JSONDecodeError,PermissionError):pass
        time.sleep(.05)
    raise AssertionError('Owned fixture failed to reach expected state')

def acquire():
    data=call('session',['start']);meta=read(BASE/'binding.json');owned.append(meta)
    gen=data['session']['generation'];assert gen==meta['generation']
    assert data['session']['platform']=='windows' and data['session']['capabilities']['audio_silent']
    return gen,meta

before=adapter.provider()[1]
try:
    active,first=acquire()
    initial=call('session',['status']);assert initial['descriptor']['generation']==active
    call('apps',{'action':'launch','name':first['exe'],'args':['--fixture',str(OUT/'fixture.json')]})
    wait_for(OUT/'fixture.json',lambda d: d['sessionId']==before['childSessionId'])
    frame=call('screenshot');shutil.copyfile(frame['path'],OUT/'before.png')
    call('click',{'x':155,'y':210,'frame':frame['frame']})
    nonce='CCTL_NATIVE_CHILD_42'
    call('type_text',{'text':nonce})
    wait_for(OUT/'fixture.json',lambda d:d['text']==nonce)
    call('key',{'keys':'CTRL+A'})
    wait_for(OUT/'fixture.json',lambda d:'A, Control' in d.get('keys',[]))
    # This legacy single-line TextBox does not implement Ctrl+A selection.
    # Verify real modifier delivery above; select with its native editing keys.
    call('key',{'keys':'HOME'})
    call('key',{'keys':'SHIFT+END'})
    call('type_text',{'text':'CCTL_REPLACED_43'})
    wait_for(OUT/'fixture.json',lambda d:d['text']=='CCTL_REPLACED_43')
    call('click',{'x':175,'y':262,'frame':frame['frame']})
    wait_for(OUT/'fixture.json',lambda d:d['clicks']==1)
    shot=call('screenshot');shutil.copyfile(shot['path'],OUT/'fixture.png')
    call('apps',{'action':'launch','name':str(Path(os.environ['WINDIR'])/'System32/cmd.exe'),'args':['/d','/q','/k','title','DesktopSessionHelperCctlIntegration']})
    time.sleep(.6)
    call('type_text',{'text':'echo CCTL_GENERIC_CHILD_ACCEPTANCE'})
    call('key',{'keys':'ENTER'})
    time.sleep(.3)
    generic=call('screenshot');shutil.copyfile(generic['path'],OUT/'generic.png')
    unsupported=call('browser_snapshot',{},ok=False);assert unsupported['error']=='unsupported_capability'
    forbidden=call('run',{'command':'echo SHOULD_NOT_EXECUTE'},ok=False);assert forbidden['error']=='unsupported_capability'
    stopped=call('session',['stop']);active=None
    assert stopped['session']['state']=='stopped'
    blocked=call('click',{'x':155,'y':210,'frame':frame['frame']},ok=False);assert blocked['error']=='session_stopped'
    active,second=acquire();assert first['generation']!=active
    stale=call('click',{'x':155,'y':210,'frame':frame['frame']},ok=False);assert stale['error']=='bad_arguments'
    assert call('session',['status'])['descriptor']['generation']==active
    call('session',['stop']);active=None
    after=adapter.provider()[1];fields=['pid','childSessionId','connectedAt','desktopState']
    assert all(before.get(k)==after.get(k) for k in fields)
    for meta in owned:
        ip=Path(meta['ipc']);original=read(ip/'parent.json');restored=read(ip/'viewer-stopped.json')
        assert restored['visible']==original['viewerVisible'] and not restored['minimized']
        assert adapter.process(meta['workerPid']) is None
        for name in ['binding.json','parent.json','parent-observations.jsonl','viewer-stopped.json']:
            shutil.copyfile(ip/name,OUT/(meta['generation']+'-'+name))
    result={'ok':True,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'firstGeneration':first['generation'],'secondGeneration':second['generation'],'providerBefore':{k:before.get(k) for k in fields},'providerAfter':{k:after.get(k) for k in fields},'childActive':adapter.native_state(after['childSessionId'])==0,'fixture':read(OUT/'fixture.json'),'genericCapture':str(OUT/'generic.png'),'hostFallbackForUnsupported':False,'bindingsRemoved':not (BASE/'binding.json').exists(),'workersGone':True}
    save(OUT/'result.json',result);print(json.dumps(result))
finally:
    if active and (BASE/'binding.json').exists() and read(BASE/'binding.json').get('generation')==active:
        try:
            diagnostic=call('screenshot');shutil.copyfile(diagnostic['path'],OUT/'failure.png')
        except Exception:pass
        try:call('session',['stop'])
        except Exception:pass
    save(OUT/'calls.json',calls)

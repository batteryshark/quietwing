"""Bounded public-CLI generation acceptance; preserves the existing native child."""
import datetime, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
import adapter
HERE=Path(__file__).resolve().parent
OUT=Path(os.environ['DESKHELPER_ACCEPTANCE_OUTPUT']).resolve();OUT.mkdir(parents=True,exist_ok=True)
NAME='generation-smoke';BASE=adapter.instance(NAME)
calls=[];attachments=[];passed=False

def save(path,value):Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def wait_for(path,predicate):
    end=time.monotonic()+5
    while time.monotonic()<end:
        try:
            data=read(path)
            if predicate(data):return data
        except (FileNotFoundError,json.JSONDecodeError):pass
        time.sleep(.05)
    raise AssertionError('Owned fixture did not reach expected state')
def call(*args,ok=True):
    process=subprocess.run([sys.executable,str(HERE/'adapter.py'),*args],capture_output=True,text=True,encoding='utf-8',timeout=40)
    data=json.loads(process.stdout);calls.append({'args':list(args),'returncode':process.returncode,'response':data})
    assert data['ok']==ok and (process.returncode==0)==ok,(args,data,process.stderr)
    return data

def status(generation=None):
    args=['status','--id',NAME]
    if generation:args+=['--expect-generation',generation]
    return call(*args)

def rejected(command,generation,*args):
    data=call(command,'--id',NAME,'--expect-generation',generation,*args,ok=False)
    assert data['error']['code']=='generation_changed',data
    return data

def attach():
    data=call('attach','--id',NAME,'--hide-viewer');meta=read(BASE/'binding.json');attachments.append(meta)
    gen=data['session']['generation'];assert gen==meta['generation']==Path(meta['ipc']).name
    assert data['session']['id']==NAME
    expected={'capture':True,'input':True,'keyboard':True,'pointer':True,'exec':True,'audio_capture':False,'audio_silent':True,'browser':False,'accessibility':False}
    assert data['session']['capabilities']==expected,data
    assert Path(meta['exe']).is_relative_to(Path(os.environ['DESKHELPER_STATE_ROOT'])/'cache'),meta['exe']
    return gen,meta

before=adapter.provider()[1]
try:
    call('doctor')
    gen,meta=attach();folder=Path(meta['ipc']);assert status(gen)['session']['generation']==gen
    fixture=OUT/'fixture.json'
    call('exec','--id',NAME,'--expect-generation',gen,'--',meta['exe'],'--fixture',str(fixture));time.sleep(.4)
    call('input','--id',NAME,'--expect-generation',gen,'--click','155','185')
    nonce='GENERATION_BOUND_INPUT_42'
    call('input','--id',NAME,'--expect-generation',gen,'--type',nonce)
    wait_for(fixture,lambda value:value['text']==nonce)
    bad='stale-'+gen
    for command,args in [('status',[]),('capture',['--output',str(OUT/'rejected.png')]),('input',['--type','MUST_NOT_TYPE']),('exec',['--',sys.executable,'-c','import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("bad")',str(OUT/'rejected-exec.txt')]),('stop',[])]:
        rejected(command,bad,*args)
    # Prove the worker itself rejects stop, not just the adapter's metadata check.
    raw=adapter.request(folder,{'action':'stop','expectGeneration':bad});save(OUT/'worker-stale-stop.json',raw)
    assert not raw['ok'] and raw['error']['code']=='generation_changed'
    assert read(fixture)['text']==nonce and not (OUT/'rejected.png').exists() and not (OUT/'rejected-exec.txt').exists()
    # Legacy callers still target this immutable attachment without the optional flag.
    assert status()['session']['generation']==gen
    call('capture','--id',NAME,'--expect-generation',gen,'--output',str(OUT/'fixture.png'))
    argv=['--expect-generation','literal','--type','--help','two words\\']
    call('exec','--id',NAME,'--expect-generation',gen,'--',sys.executable,'-c','import pathlib,json,sys;pathlib.Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))',str(OUT/'argv.json'),*argv)
    wait_for(OUT/'argv.json',lambda value:value==argv)
    call('stop','--id',NAME,'--expect-generation',gen)
    new,second=attach();assert new!=gen
    rejected('input',gen,'--type','MUST_NOT_REPLAY')
    rejected('stop',gen)
    assert status(new)['session']['generation']==new
    call('stop','--id',NAME,'--expect-generation',new)
    after=adapter.provider()[1]
    same_fields=['pid','childSessionId','connectedAt','desktopState']
    assert all(before.get(k)==after.get(k) for k in same_fields),(before,after)
    assert adapter.native_state(after['childSessionId'])==0
    for meta in attachments:
        assert adapter.process(meta['workerPid']) is None
        ip=Path(meta['ipc']);initial=read(ip/'parent.json');final=read(ip/'viewer-stopped.json')
        assert initial['viewerVisible']==final['visible'] and not final['minimized'],(initial,final)
        for file in ['parent.json','parent-observations.jsonl','viewer-stopped.json','binding.json']:
            shutil.copyfile(ip/file,OUT/(meta['generation']+'-'+file))
    hashes={file:hashlib.sha256((HERE/file).read_bytes()).hexdigest() for file in ['adapter.py','Worker.cs','NativeSupport.cs','generation_acceptance.py','test_adapter.py']}
    summary={'ok':True,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'firstGeneration':gen,'secondGeneration':new,'providerBefore':{k:before.get(k) for k in same_fields},'providerAfter':{k:after.get(k) for k in same_fields},'childActive':True,'bindingsRemoved':not (BASE/'binding.json').exists(),'workersGone':True,'sourceHashes':hashes,'workerPath':attachments[-1]['exe'],'workerHash':hashlib.sha256(Path(attachments[-1]['exe']).read_bytes()).hexdigest()}
    save(OUT/'result.json',summary);print(json.dumps(summary));passed=True
finally:
    if (BASE/'binding.json').exists():
        binding=read(BASE/'binding.json')
        # Scope cleanup to an attachment created by this test; never act on replacements.
        if any(m['generation']==binding.get('generation') for m in attachments):
            call('stop','--id',NAME,'--expect-generation',binding['generation'])
    save(OUT/'calls.json',calls)

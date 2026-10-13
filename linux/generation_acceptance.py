#!/usr/bin/env python3
"""Bounded generation replacement/refusal and TTL-overlapping native input proof."""
import datetime,hashlib,json,os,pathlib,subprocess,sys,time,uuid
BASE=pathlib.Path(__file__).resolve().parent
ADAPTER=BASE/'adapter.py'
RUN=BASE/'evidence'/os.environ.get('DESKHELPER_TEST_RUN','generation-acceptance-001')
RUN.mkdir(mode=0o700,parents=True,exist_ok=True)
STATE=RUN/'private-state';ENV=dict(os.environ,DESKHELPER_STATE_ROOT=str(STATE))
SESSION='generation-proof';owned={}
def api(command,*args,expect=None,error=None):
    argv=[command,*map(str,args)]
    if expect is not None:
        at=argv.index('--') if '--' in argv else len(argv);argv[at:at]=['--expect-generation',expect]
    started=time.time()
    p=subprocess.run([sys.executable,str(ADAPTER),*argv],env=ENV,capture_output=True,text=True,timeout=85)
    r=json.loads(p.stdout)
    with (RUN/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':argv,'started_epoch':started,'ended_epoch':time.time(),'exit':p.returncode,'response':r})+'\n')
    assert bool(r['ok'])==(error is None) and (p.returncode==0)==(error is None),(argv,r,p.stderr)
    if error:assert r['error']['code']==error,r
    if command=='start' and not error:owned[r['session']['id']]=r['session']['generation']
    return r
summary={'source_sha256':hashlib.sha256(ADAPTER.read_bytes()).hexdigest(),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    a=api('start','--id',SESSION,'--ttl',120)['session'];ga=a['generation'];uuid.UUID(ga)
    api('start','--id',SESSION,'--replace-stopped',error='SESSION_NOT_CLEAN')
    api('stop','--id',SESSION,expect=ga)
    b=api('start','--id',SESSION,'--replace-stopped','--ttl',120)['session'];gb=b['generation'];uuid.UUID(gb)
    assert ga!=gb and b['id']==a['id']
    summary['generations']={'old':ga,'replacement':gb}
    assert api('status','--id',SESSION)['session']['generation']==gb
    document=RUN/'replacement-document.txt';document.write_text('')
    api('exec','--id',SESSION,'--','mousepad','--disable-server',document,expect=gb);time.sleep(.6)
    api('input','--id',SESSION,'--type','replacement alive',expect=gb)
    api('input','--id',SESSION,'--key','ctrl+s',expect=gb);time.sleep(.15)
    assert document.read_text()=='replacement alive'
    old_image=RUN/'stale-output'/'must-not-exist.png';marker=RUN/'must-not-execute.txt'
    api('status','--id',SESSION,expect=ga,error='generation_changed')
    api('capture','--id',SESSION,'--output',old_image,expect=ga,error='generation_changed')
    api('input','--id',SESSION,'--type','STALE MUST NOT ARRIVE',expect=ga,error='generation_changed')
    api('input','--id',SESSION,'--click',10,10,expect=ga,error='generation_changed')
    api('exec','--id',SESSION,'--',sys.executable,'-c','import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("wrong")',marker,expect=ga,error='generation_changed')
    api('stop','--id',SESSION,expect=ga,error='generation_changed')
    assert not old_image.parent.exists() and not marker.exists()
    assert api('status','--id',SESSION,expect=gb)['session']['state']=='running'
    api('input','--id',SESSION,'--key','ctrl+s',expect=gb);time.sleep(.15)
    assert document.read_text()=='replacement alive'
    api('capture','--id',SESSION,'--output',RUN/'replacement-after-refusals.png',expect=gb)
    summary['stale_actions_rejected_before_effects']=True
    summary['archive_count']=len(list((STATE/'.history'/SESSION).iterdir()));assert summary['archive_count']==1
    summary['replacement_stop']=api('stop','--id',SESSION,expect=gb)
    # Keep a native input action in flight while the bounded instance TTL passes.
    short=api('start','--id','lifetime-proof','--ttl',5)['session'];gl=short['generation']
    api('exec','--id','lifetime-proof','--','mousepad','--disable-server',RUN/'lifetime-document.txt',expect=gl);time.sleep(.6)
    began=time.time();delivery=api('input','--id','lifetime-proof','--type','x'*400,expect=gl);ended=time.time()
    expires=datetime.datetime.fromisoformat(short['expires_at']).timestamp()
    assert began<expires<ended,(began,expires,ended)
    deadline=time.monotonic()+10
    while True:
        stopped=api('status','--id','lifetime-proof',expect=gl)
        if stopped['session']['state']=='stopped':break
        assert time.monotonic()<deadline
        time.sleep(.1)
    assert datetime.datetime.fromisoformat(stopped['session']['stopped_at']).timestamp()>=ended-.05
    summary['ttl_overlap']={'input_started_epoch':began,'input_completed_epoch':ended,'expiry_epoch':expires,'delivery':delivery,'cleanup':stopped['session']['cleanup']}
    summary['passed']=True
finally:
    # Exact owned generation only; never stop a replacement discovered later.
    for name,generation in owned.items():
        try:api('stop','--id',name,expect=generation)
        except Exception as exc:summary.setdefault('cleanup_errors',[]).append(str(exc))
    summary['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (RUN/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

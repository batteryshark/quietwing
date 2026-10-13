"""Bounded Windows acceptance against an already-authenticated ParaDesk child."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'evidence'/'acceptance-final';OUT.mkdir(parents=True,exist_ok=True)
NAME='lifecycle-acceptance';ROOT=Path(os.environ['DESKHELPER_STATE_ROOT'])/'windows'/NAME
calls=[]
def call(*args,ok=True):
 p=subprocess.run([sys.executable,str(HERE/'adapter.py'),*args],capture_output=True,text=True,encoding='utf-8')
 d=json.loads(p.stdout);calls.append({'args':list(args),'returncode':p.returncode,'response':d})
 assert d['ok']==ok and (p.returncode==0)==ok,(args,d,p.stderr)
 return d
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def wait(p):
 end=time.monotonic()+8
 while not p.exists() and time.monotonic()<end:time.sleep(.05)
 assert p.exists(),p
 return read(p)
def save(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8')
try:
 call('attach','--id',NAME,'--hide-viewer');b=read(ROOT/'binding.json');old=Path(b['ipc'])
 status=call('status','--id',NAME);assert status['result']['audioRuntime']['silentDefaultOutput']
 fixture=call('exec','--id',NAME,'--',b['exe'],'--fixture',str(OUT/'fixture.json'))['result'];time.sleep(.3)
 call('input','--id',NAME,'--click','155','185');literal='--literal $ & ; unicode café'
 call('input','--id',NAME,'--type',literal);call('input','--id',NAME,'--click','175','255')
 state=read(OUT/'fixture.json');assert state['text']==literal and state['clicks']==1,state
 call('capture','--id',NAME,'--output',str(OUT/'fixture.png'))
 argv=['--type','literal $ & ;','--help','two words\\']
 call('exec','--id',NAME,'--',sys.executable,'-c','import json,pathlib,sys;pathlib.Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))',str(OUT/'argv.json'),*argv)
 assert wait(OUT/'argv.json')==argv
 app=call('exec','--id',NAME,'--',str(Path(os.environ['WINDIR'])/'System32'/'cmd.exe'),'/d','/q','/k','title','DesktopSessionHelperFinalAcceptance')['result']
 call('input','--id',NAME,'--type','echo NATIVE_AUDIO_GATED_CHILD_ACCEPTANCE');call('input','--id',NAME,'--key','ENTER')
 call('input','--id',NAME,'--move','450','300');call('capture','--id',NAME,'--output',str(OUT/'generic.png'))
 call('input','--id',NAME,'--click','-1','-1',ok=False);call('status',ok=False)
 original=read(ROOT/'binding.json');tampered=dict(original);tampered['workerBirthTicks']+=1;save(ROOT/'binding.json',tampered)
 try:call('status','--id',NAME,ok=False)
 finally:save(ROOT/'binding.json',original)
 # Simulate only the owned worker crashing; its job must close and guardian restore.
 script=f"$p=Get-Process -Id {b['workerPid']};if($p.StartTime.ToUniversalTime().Ticks -ne {b['workerBirthTicks']}){{throw 'birth mismatch'}};Stop-Process -Id $p.Id"
 subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],check=True,capture_output=True)
 restored=wait(old/'viewer-stopped.json');assert restored['visible'] and not restored['minimized'],restored
 time.sleep(.4)
 # A harmless stale capture request must never enter the next attachment generation.
 stale=OUT/'must-not-exist.png';stale.unlink(missing_ok=True)
 save(old/'requests'/'stale.json',{'action':'capture','output':str(stale)})
 call('stop','--id',NAME)
 call('attach','--id',NAME,'--hide-viewer');new=read(ROOT/'binding.json');assert new['ipc']!=str(old)
 call('status','--id',NAME);time.sleep(.25);assert not stale.exists()
 call('stop','--id',NAME)
 result={'ok':True,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':state,'argv':argv,'genericApp':app,'oldIpc':str(old),'newIpc':new['ipc'],'crashRestore':restored,'staleCaptureReplayed':stale.exists()}
 save(OUT/'result.json',result)
 for label,path in [('first',old),('second',Path(new['ipc']))]:
  for name in ['parent.json','parent-observations.jsonl','viewer-stopped.json','binding.json']:
   (OUT/(label+'-'+name)).write_bytes((path/name).read_bytes())
 print(json.dumps(result))
finally:
 save(OUT/'calls.json',calls)
 if (ROOT/'binding.json').exists():
  try:call('stop','--id',NAME)
  except Exception:pass

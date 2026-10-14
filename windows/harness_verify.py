"""Independently check an ordinary editor artifact and clean only its helper job."""
import argparse,datetime,json,os,shutil,subprocess,sys,time,tomllib
from pathlib import Path
import adapter
from cctl.config import load
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--marker',required=True)
parser.add_argument('--target',default=os.environ.get('CCTL_SESSION','integration'))
args=parser.parse_args();target=args.target
cfg=tomllib.loads(Path(os.environ['CCTL_CONFIG']).read_text());os.environ.update(cfg['sessions'][target]['env']);os.environ['CCTL_SESSION']=target
OUT=args.output;expected=args.marker;prior=adapter.read(OUT/'prepared.json');calls=[]
def save(p,v):Path(p).write_text(json.dumps(v,indent=2),encoding='utf-8')
def call(tool,args=None):
 p=subprocess.run([sys.executable,'-m','cctl.cli','--session',target,tool]+(args if tool=='session' else [json.dumps(args or {})]),capture_output=True,text=True,encoding='utf-8',timeout=120)
 v=json.loads(p.stdout);calls.append({'tool':tool,'args':args,'returncode':p.returncode,'data':v});assert p.returncode==0,(v,p.stderr);return v
status=call('session',['status']);assert status['descriptor']['generation']==prior['generation'] and not status['requires_rebind']
assert status['descriptor']['capabilities']['audio_silent']
doc=Path(prior['document']);raw=doc.read_bytes();actual=raw.decode('utf-16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-8-sig');assert actual==expected,repr(actual)
apps=json.loads(adapter.ps("@(Get-CimInstance Win32_Process -Filter \"Name='powershell_ise.exe'\" | Where-Object {$_.CommandLine -like "+adapter.quote('*'+str(doc)+'*')+"} | Select-Object ProcessId,SessionId,CommandLine)|ConvertTo-Json -Compress"))
if isinstance(apps,dict):apps=[apps]
assert len(apps)==1 and apps[0]['SessionId']==status['session']['nativeSessionId'],apps
app_pid=apps[0]['ProcessId'];app_birth=adapter.process(app_pid)['birthTicks']
frame=call('screenshot');assert frame['session']['generation']==prior['generation'];shutil.copyfile(frame['path'],OUT/'verified.png')
events=[json.loads(s) for s in (load().state_dir/'events.jsonl').read_text().splitlines() if s.strip()];events=[e for e in events if e.get('generation')==prior['generation']]
assert {'apps','screenshot','click','type_text','key'}<={e['tool'] for e in events if e['ok']}
assert all(e['target']==target for e in events)
call('session',['stop'])
ip=Path(prior['ipc']);original=adapter.read(ip/'parent.json');restored=adapter.read(ip/'viewer-stopped.json');assert original['viewerVisible']==restored['visible'] and not restored['minimized']
assert adapter.process(app_pid) is None and adapter.process(prior['workerPid']) is None
provider=adapter.provider()[1];assert all(provider.get(k)==v for k,v in prior['providerBefore'].items()) and adapter.native_state(provider['childSessionId'])==0
for n in ['parent.json','parent-observations.jsonl','viewer-stopped.json']:shutil.copyfile(ip/n,OUT/n)
obs=[json.loads(s) for s in (ip/'parent-observations.jsonl').read_text().splitlines() if s.strip()]
summary={'samples':len(obs),'cursors':list({(r['x'],r['y']) for r in obs}),'foregrounds':list({r['foreground'] for r in obs}),'viewerVisible':list({r['viewerVisible'] for r in obs}),'viewerMinimized':list({r['viewerMinimized'] for r in obs})}
result={'ok':True,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'generation':prior['generation'],'expectedText':expected,'actualText':actual,'bytesHex':raw.hex(),'appPid':app_pid,'appBirthTicks':app_birth,'nativeSessionId':apps[0]['SessionId'],'eventTools':[e['tool'] for e in events],'observation':summary,'viewer':restored,'providerBefore':prior['providerBefore'],'providerAfter':{k:provider.get(k) for k in prior['providerBefore']},'appGone':True,'workerGone':True,'childActive':True}
save(OUT/'verification.json',result);save(OUT/'events.json',events);save(OUT/'verification-calls.json',calls);print(json.dumps(result))

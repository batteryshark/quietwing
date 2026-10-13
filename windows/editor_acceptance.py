"""Prepare/check an ordinary, owned ISE document through public cctl calls."""
import json,os,shutil,subprocess,sys,time,tomllib
from pathlib import Path
import adapter
cfg=tomllib.loads(Path(os.environ['CCTL_CONFIG']).read_text());os.environ.update(cfg['sessions']['integration']['env']);os.environ['CCTL_SESSION']='integration'
OUT=Path(os.environ['DESKHELPER_ACCEPTANCE_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True);adapter.restrict_directory(OUT)
calls=[];NAME=cfg['sessions']['integration']['id'];BASE=adapter.instance(NAME)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):Path(p).write_text(json.dumps(d,indent=2),encoding='utf-8')
def call(tool,args=None):
 argv=[sys.executable,'-m','cctl.cli','--session','integration',tool]+(args if tool=='session' else [json.dumps(args or {})])
 p=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=120);v=json.loads(p.stdout);calls.append({'tool':tool,'args':args,'returncode':p.returncode,'data':v});assert p.returncode==0,(v,p.stderr);return v
phase=sys.argv[1]
try:
 if phase=='prepare':
  doc=OUT/'owned-editor.ps1';assert not doc.exists();doc.write_text('\n',encoding='utf-16')
  desc=call('session',['start'])['session'];b=read(BASE/'binding.json')
  app=call('apps',{'action':'launch','name':str(Path(os.environ['WINDIR'])/'System32/WindowsPowerShell/v1.0/powershell_ise.exe'),'args':['-NoProfile',str(doc)]})
  assert app['sessionId']==b['childSessionId'];time.sleep(2)
  frame=call('screenshot');shutil.copyfile(frame['path'],OUT/'before.png')
  save(OUT/'prepared.json',{'generation':desc['generation'],'frame':frame,'ipc':b['ipc'],'workerPid':b['workerPid'],'appPid':app['pid'],'document':str(doc)})
  print(json.dumps({'generation':desc['generation'],'frame':frame['frame'],'appPid':app['pid'],'document':str(doc)}))
 elif phase=='finish':
  prior=read(OUT/'prepared.json');frame=call('screenshot')
  call('click',{'x':int(sys.argv[2]),'y':int(sys.argv[3]),'frame':frame['frame']})
  call('key',{'keys':'CTRL+A'});call('type_text',{'text':'# WINDOWS_INSTALLED_EDITOR café Ω'})
  call('key',{'keys':'CTRL+S'});time.sleep(.4)
  raw=Path(prior['document']).read_bytes()
  actual=raw.decode('utf-16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-8-sig');assert actual=='# WINDOWS_INSTALLED_EDITOR café Ω',repr(actual)
  frame=call('screenshot');shutil.copyfile(frame['path'],OUT/'after.png');call('session',['stop'])
  ip=Path(prior['ipc'])
  for n in ['parent.json','parent-observations.jsonl','viewer-stopped.json']:shutil.copyfile(ip/n,OUT/n)
  result={'ok':True,'generation':prior['generation'],'actualText':actual,'bytesHex':raw.hex(),'appGone':adapter.process(prior['appPid']) is None,'workerGone':adapter.process(prior['workerPid']) is None,'viewer':read(ip/'viewer-stopped.json'),'childActive':adapter.native_state(adapter.provider()[1]['childSessionId'])==0}
  save(OUT/'result.json',result);print(json.dumps(result))
 else:raise ValueError(phase)
finally:save(OUT/(phase+'-calls.json'),calls)

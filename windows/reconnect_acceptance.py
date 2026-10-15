"""Run prepare and resume in separate SSH connections; use only public cctl GUI calls."""
import json,os,shutil,subprocess,sys,time,tomllib
from pathlib import Path
import psutil
import adapter
from cctl.config import load
from cctl.daemon import socket_path
os.environ['CCTL_SESSION']='integration'
config=tomllib.loads(Path(os.environ['CCTL_CONFIG']).read_text());target=config['sessions']['integration'];os.environ.update(target['env'])
OUT=Path(os.environ['DESKHELPER_ACCEPTANCE_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True);adapter.restrict_directory(OUT)
BASE=adapter.instance(target['id']);calls=[]
def read(p):
 end=time.monotonic()+3
 while True:
  try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
  except (FileNotFoundError,PermissionError,json.JSONDecodeError):
   if time.monotonic()>=end:raise
   time.sleep(.02)
def save(p,v):Path(p).write_text(json.dumps(v,indent=2),encoding='utf-8')
def call(tool,args=None):
 argv=[sys.executable,'-m','cctl.cli','--session','integration',tool]+(args if tool=='session' else [json.dumps(args or {})])
 p=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=100);v=json.loads(p.stdout);calls.append({'tool':tool,'args':args,'returncode':p.returncode,'data':v});assert p.returncode==0,(v,p.stderr);return v
phase=sys.argv[1]
try:
 if phase=='prepare':
  desc=call('session',['start'])['session'];b=read(BASE/'binding.json')
  call('apps',{'action':'launch','name':b['exe'],'args':['--fixture',str(OUT/'fixture.json')]})
  end=time.monotonic()+6
  while not (OUT/'fixture.json').exists() and time.monotonic()<end:time.sleep(.05)
  assert (OUT/'fixture.json').exists(),'fixture did not write initial state'
  frame=call('screenshot');shutil.copyfile(frame['path'],OUT/'before.png')
  port=read(socket_path(load()))['port'];listener=next(c for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==port)
  p=psutil.Process(listener.pid)
  save(OUT/'prepared.json',{'generation':desc['generation'],'frame':frame,'binding':b,'controllerPid':p.pid,'controllerBirth':p.create_time()})
  print(json.dumps({'prepared':True,'generation':desc['generation'],'frame':frame['frame'],'controllerPid':p.pid}))
 elif phase=='resume':
  prior=read(OUT/'prepared.json');p=psutil.Process(prior['controllerPid']);assert p.create_time()==prior['controllerBirth']
  status=call('session',['status']);assert status['descriptor']['generation']==prior['generation'] and not status['requires_rebind']
  call('click',{'x':155,'y':210,'frame':prior['frame']['frame']})
  call('type_text',{'text':'SSH_RECONNECTED_57'})
  end=time.monotonic()+5
  while time.monotonic()<end:
   if read(OUT/'fixture.json')['text']=='SSH_RECONNECTED_57':break
   time.sleep(.05)
  assert read(OUT/'fixture.json')['text']=='SSH_RECONNECTED_57'
  frame=call('screenshot');shutil.copyfile(frame['path'],OUT/'after.png');call('session',['stop'])
  ip=Path(prior['binding']['ipc'])
  viewer=read(ip/'viewer-stopped.json');assert not viewer['restored'] and not viewer['visible'] and not viewer['minimized']
  for name in ['parent.json','parent-observations.jsonl','viewer-stopped.json']:shutil.copyfile(ip/name,OUT/name)
  result={'ok':True,'sameControllerPid':p.pid,'sameGeneration':prior['generation'],'priorFrameAccepted':prior['frame']['frame'],'fixture':read(OUT/'fixture.json'),'viewer':read(ip/'viewer-stopped.json'),'workerGone':adapter.process(prior['binding']['workerPid']) is None,'childActive':adapter.native_state(prior['binding']['childSessionId'])==0}
  save(OUT/'result.json',result);print(json.dumps(result))
 else:raise ValueError('phase must be prepare or resume')
finally:save(OUT/(phase+'-calls.json'),calls)

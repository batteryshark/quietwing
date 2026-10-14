"""Stop only the verified private isolated test controller after helper stop.

Run in the same Python environment and CCTL_CONFIG/CCTL_SESSION as the test.
Requires psutil from that cctl environment; never installs or stops host tools.
"""
import argparse,hashlib,json,os,time
from pathlib import Path
import psutil
import adapter
from cctl.config import load
from cctl.daemon import socket_path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--target',default=os.environ.get('CCTL_SESSION','integration'))
args=parser.parse_args();os.environ['CCTL_SESSION']=args.target
cfg=load();assert cfg.session==args.target and cfg.session_options
os.environ.update(cfg.session_options['env'])
base=adapter.instance(cfg.session_options['id'])
assert not (base/'binding.json').exists(),'Stop this test helper before controller cleanup'
before=adapter.require_provider()[1];provider_fields=['pid','childSessionId','connectedAt','desktopState']
launcher=(cfg.state_dir/'controller-launch.py').resolve();config=Path(os.environ['CCTL_CONFIG']).resolve()
assert cfg.state_dir.parent.name=='sessions' and cfg.cache_dir.parent.name=='sessions','Refuse a non-target state/cache path'
assert launcher.exists() and str(config) in launcher.read_text(encoding='utf-8').replace('\\\\','\\')
portfile=socket_path(cfg);port_data=adapter.read(portfile)
listeners=[c for c in psutil.net_connections(kind='tcp') if c.status=='LISTEN' and c.laddr.port==port_data['port'] and c.laddr.ip in ('127.0.0.1','::1')]
assert len({c.pid for c in listeners})==1,'Expected one private target controller listener'
listener_pid=listeners[0].pid
listener=psutil.Process(listener_pid);listener_parent=listener.ppid();env=listener.environ()
assert Path(env['CCTL_CONFIG']).resolve()==config and env['CCTL_SESSION']==args.target
owned=[]
for proc in psutil.process_iter(['pid','cmdline','create_time']):
 try:
  argv=proc.info['cmdline'] or []
  if str(launcher).lower() not in [a.lower() for a in argv]:continue
  assert proc.pid in (listener_pid,listener_parent),'Unexpected process shares the private launcher'
  owned.append({'pid':proc.pid,'birth':proc.create_time(),'path':proc.exe(),'argv':argv})
 except psutil.NoSuchProcess:pass
assert listener_pid in {p['pid'] for p in owned},'Listener does not belong to the selected launcher/config'
# Terminate listener first. An interpreter shim may exit when its runtime does.
owned.sort(key=lambda p:p['pid']!=listener_pid)
for meta in owned:
 try:
  proc=psutil.Process(meta['pid']);assert proc.create_time()==meta['birth'] and proc.cmdline()==meta['argv'];proc.terminate()
 except psutil.NoSuchProcess:pass
end=time.monotonic()+5
while time.monotonic()<end:
 remaining=[]
 for meta in owned:
  try:
   proc=psutil.Process(meta['pid'])
   if proc.create_time()==meta['birth']:remaining.append(meta['pid'])
  except psutil.NoSuchProcess:pass
 if not remaining:break
 time.sleep(.05)
assert not remaining,remaining
# Delete only the same stale private port record, after its verified owner exited.
assert adapter.read(portfile)==port_data;portfile.unlink()
meta=adapter.read(base/'stopped-binding.json')
assert adapter.generation(meta)==Path(meta['ipc']).name
worker=adapter.process(meta['workerPid']);assert worker is None or worker['birthTicks']!=meta['workerBirthTicks']
observer=adapter.read(Path(meta['ipc'])/'viewer-ready.json');observer_process=adapter.process(observer['pid'])
assert observer_process is None or observer_process['birthTicks']!=observer['birthTicks']
names=meta['tasks']+['cctl-isolated-'+hashlib.sha256(str(cfg.state_dir).encode()).hexdigest()[:16]]
script='@('+','.join(adapter.quote(n) for n in names)+')|ForEach-Object {Get-ScheduledTask -TaskName $_ -ErrorAction SilentlyContinue}|Select-Object -ExpandProperty TaskName'
assert not adapter.ps(script),'Owned test registrations remain; inspect before deleting'
after=adapter.require_provider()[1];assert all(before.get(k)==after.get(k) for k in provider_fields)
result={'ok':True,'target':args.target,'controllerProcesses':owned,'controllerGone':True,'privatePortRecordRemoved':True,'ownedTasksRemaining':0,'workerGone':True,'observerGone':True,'observerIdentity':observer,'providerBefore':{k:before.get(k) for k in provider_fields},'providerAfter':{k:after.get(k) for k in provider_fields},'childActive':adapter.native_state(after['childSessionId'])==0,'keptConfig':str(config),'keptLauncher':str(launcher)}
args.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

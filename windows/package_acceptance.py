"""Exercise only the installed public entry point; no host GUI or native-session lifecycle."""
import datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
import quietwing
PACKAGE=Path(quietwing.__file__).parent
spec=importlib.util.spec_from_file_location('installed_adapter',PACKAGE/'windows/adapter.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
EXE=Path(sys.executable).with_name('quietwing.exe');NAME='package-smoke';BASE=adapter.instance(NAME)
OUT=Path(os.environ['DESKHELPER_ACCEPTANCE_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True);adapter.restrict_directory(OUT)
calls=[];meta=None;active=False

def save(p,v):Path(p).write_text(json.dumps(v,indent=2),encoding='utf-8')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def wait_for(p,predicate):
 end=time.monotonic()+6
 while time.monotonic()<end:
  try:
   v=read(p)
   if predicate(v):return v
  except (FileNotFoundError,PermissionError,json.JSONDecodeError):pass
  time.sleep(.03)
 raise AssertionError('fixture deadline')
def call(*args,ok=True):
 p=subprocess.run([str(EXE),*args],capture_output=True,text=True,encoding='utf-8',timeout=60)
 v=json.loads(p.stdout);calls.append({'args':list(args),'returncode':p.returncode,'response':v});assert v['ok']==ok and (p.returncode==0)==ok,(v,p.stderr);return v
def hashes():return {str(p.relative_to(PACKAGE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
initial_hashes=hashes();before=adapter.provider()[1]
try:
 call('doctor');attached=call('attach','--id',NAME,'--hide-viewer');active=True;meta=read(BASE/'binding.json');gen=attached['session']['generation'];assert gen==meta['generation']
 guard=['--id',NAME,'--expect-generation',gen]
 assert Path(meta['exe']).is_relative_to(Path(os.environ['DESKHELPER_STATE_ROOT'])/'cache')
 assert not Path(meta['exe']).is_relative_to(PACKAGE)
 assert call('status',*guard)['session']['capabilities']['audio_silent']
 call('exec',*guard,'--',meta['exe'],'--fixture',str(OUT/'fixture.json'))
 wait_for(OUT/'fixture.json',lambda v:v['sessionId']==meta['childSessionId'])
 call('input',*guard,'--click','155','210');call('input',*guard,'--type','INSTALLED_WHEEL_CHILD_71')
 wait_for(OUT/'fixture.json',lambda v:v['text']=='INSTALLED_WHEEL_CHILD_71')
 call('input',*guard,'--click','175','262');wait_for(OUT/'fixture.json',lambda v:v['clicks']==1)
 call('capture',*guard,'--output',str(OUT/'installed-fixture.png'))
 call('exec',*guard,'--',str(Path(os.environ['WINDIR'])/'System32/cmd.exe'),'/d','/q','/k','title','InstalledCompanionAcceptance')
 time.sleep(.5);call('input',*guard,'--type','echo INSTALLED_GENERIC_CHILD_72');call('input',*guard,'--key','ENTER');time.sleep(.2)
 call('capture',*guard,'--output',str(OUT/'installed-generic.png'))
 rejected=call('input','--id',NAME,'--expect-generation','stale-'+gen,'--type','MUST_NOT_TYPE',ok=False);assert rejected['error']['code']=='generation_changed'
 call('stop',*guard);active=False
 after=adapter.provider()[1];fields=['pid','childSessionId','connectedAt','desktopState'];assert all(before.get(k)==after.get(k) for k in fields)
 assert adapter.native_state(after['childSessionId'])==0 and adapter.process(meta['workerPid']) is None
 ip=Path(meta['ipc']);parent=read(ip/'parent.json');restored=read(ip/'viewer-stopped.json');assert not restored['restored'] and not restored['visible'] and not restored['minimized']
 for name in ['parent.json','parent-observations.jsonl','viewer-stopped.json']:shutil.copyfile(ip/name,OUT/name)
 assert hashes()==initial_hashes,'Installed resource contents changed'
 executables=[str(p.relative_to(PACKAGE)) for p in PACKAGE.rglob('*.exe')];assert not executables,executables
 result={'ok':True,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entryPoint':str(EXE),'packagePath':str(PACKAGE),'generation':gen,'workerPath':meta['exe'],'workerHash':hashlib.sha256(Path(meta['exe']).read_bytes()).hexdigest(),'installedResourceHashes':initial_hashes,'installedResourcesUnchanged':True,'noExecutablesInPackage':True,'providerBefore':{k:before.get(k) for k in fields},'providerAfter':{k:after.get(k) for k in fields},'fixture':read(OUT/'fixture.json'),'viewer':restored,'workerGone':True,'childActive':True,'bindingRemoved':not (BASE/'binding.json').exists()}
 save(OUT/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='installedResourceHashes'}))
finally:
 if active and meta and (BASE/'binding.json').exists() and read(BASE/'binding.json').get('generation')==meta['generation']:call('stop','--id',NAME,'--expect-generation',meta['generation'])
 save(OUT/'calls.json',calls)

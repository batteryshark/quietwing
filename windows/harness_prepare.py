"""Prepare a blank owned ISE document, then attach before a real MCP harness run.

Requires CCTL_CONFIG and a cctl installation in this Python environment. The
configured target must use the Windows companion and an existing ParaDesk child.
"""
import argparse,json,os,subprocess,sys,tomllib
from pathlib import Path
import adapter

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('phase',choices=['prepare','attach'])
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--target',default=os.environ.get('CCTL_SESSION','integration'))
args=parser.parse_args();target=args.target;out=args.output.resolve()
cfg=tomllib.loads(Path(os.environ['CCTL_CONFIG']).read_text());options=cfg['sessions'][target]
os.environ.update(options['env']);os.environ['CCTL_SESSION']=target
if args.phase=='prepare':
 adapter.require_provider()
 out.mkdir(parents=True,exist_ok=False);adapter.restrict_directory(out)
 (out/'owned-editor.ps1').write_text('\n',encoding='utf-16')
 print(json.dumps({'ok':True,'document':str(out/'owned-editor.ps1'),'attached':False}))
else:
 doc=out/'owned-editor.ps1'
 assert doc.read_text(encoding='utf-16')=='\n','Document must still be the prepared blank line'
 assert not (out/'prepared.json').exists(),'Evidence already has an attachment'
 base=adapter.instance(options['id']);assert not (base/'binding.json').exists(),'Target already has an attachment; clean the prior test first'
 before=adapter.require_provider()[1]
 p=subprocess.run([sys.executable,'-m','cctl.cli','--session',target,'session','start'],capture_output=True,text=True,encoding='utf-8',timeout=120)
 value=json.loads(p.stdout);assert p.returncode==0,(value,p.stderr)
 binding=adapter.read(base/'binding.json');assert value['session']['generation']==binding['generation']
 fields=['pid','childSessionId','connectedAt','desktopState']
 prepared={'generation':binding['generation'],'ipc':binding['ipc'],'workerPid':binding['workerPid'],'workerBirthTicks':binding['workerBirthTicks'],'document':str(doc),'providerBefore':{k:before.get(k) for k in fields},'descriptor':value['session']}
 (out/'prepared.json').write_text(json.dumps(prepared,indent=2),encoding='utf-8')
 print(json.dumps(prepared))

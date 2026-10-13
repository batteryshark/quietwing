#!/usr/bin/env python3
"""Public adapter acceptance only. Run stage1 and stage2 over separate SSH calls."""
import array,datetime,hashlib,json,math,os,pathlib,re,subprocess,sys,threading,time,wave
BASE=pathlib.Path(__file__).resolve().parent
ADAPTER=pathlib.Path(os.environ.get('DESKHELPER_TEST_ADAPTER',str(BASE/'adapter.py'))).resolve()
COMMAND=json.loads(os.environ['DESKHELPER_TEST_COMMAND_JSON']) if 'DESKHELPER_TEST_COMMAND_JSON' in os.environ else [sys.executable,str(ADAPTER)]
if not isinstance(COMMAND,list) or not COMMAND or not all(isinstance(x,str) for x in COMMAND):
    raise ValueError('DESKHELPER_TEST_COMMAND_JSON must be a nonempty string array')
ROOT=pathlib.Path(os.environ.get('DESKHELPER_TEST_EVIDENCE_ROOT',str(BASE/'evidence'))).resolve()
STATE=ROOT/'state'
RUN=ROOT/os.environ.get('DESKHELPER_TEST_RUN','public-acceptance-final')
RUN.mkdir(mode=0o700,parents=True,exist_ok=True)
ENV=dict(os.environ,DESKHELPER_STATE_ROOT=str(STATE))
SESSION=os.environ.get('DESKHELPER_TEST_ID','public-final2')
GENERATION_FILE=RUN/'generations.json'
GENERATIONS=json.loads(GENERATION_FILE.read_text()) if GENERATION_FILE.exists() else {}
def dump(name,data):(RUN/name).write_text(json.dumps(data,indent=2)+'\n')
def api(*args,ok=True):
    args=tuple(map(str,args))
    if args[0] in ('status','exec','capture','input','stop') and '--id' in args:
        generation=GENERATIONS.get(args[args.index('--id')+1])
        if generation:
            boundary=args.index('--') if '--' in args else len(args)
            args=args[:boundary]+('--expect-generation',generation)+args[boundary:]
    p=subprocess.run([*COMMAND,*map(str,args)],env=ENV,capture_output=True,text=True,timeout=50)
    response=json.loads(p.stdout)
    with (RUN/'commands.jsonl').open('a') as f:f.write(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':args,'exit':p.returncode,'response':response})+'\n')
    assert response['ok']==ok and (p.returncode==0)==ok,(args,response,p.stderr)
    if args[0]=='start' and response['ok']:
        GENERATIONS[response['session']['id']]=response['session']['generation'];dump('generations.json',GENERATIONS)
    return response
def execute(*argv):return api('exec','--id',SESSION,'--',*argv)['result']
def wait_until(fn,seconds=5):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        try:
            answer=fn()
            if answer:return answer
        except (FileNotFoundError,json.JSONDecodeError,ValueError):pass
        time.sleep(.05)
    raise AssertionError('Timeout waiting for owned app result')
def text_log(result):return wait_until(lambda:pathlib.Path(result['stdout']).read_text())
HOST=dict(os.environ,DISPLAY=os.environ.get('CCTL_TEST_HOST_DISPLAY',':0'),
          XAUTHORITY=os.environ.get('CCTL_TEST_HOST_XAUTHORITY',str(pathlib.Path.home()/'.Xauthority')),
          PULSE_SERVER=os.environ.get('CCTL_TEST_HOST_PULSE',f'unix:/run/user/{os.getuid()}/pulse/native'))
samples=[];ending=threading.Event()
def host_monitor():
    while not ending.is_set():
        a=subprocess.run(['xdotool','getmouselocation','--shell'],env=HOST,capture_output=True,text=True,timeout=3)
        b=subprocess.run(['xdotool','getwindowfocus'],env=HOST,capture_output=True,text=True,timeout=3)
        d=dict(line.split('=',1) for line in a.stdout.splitlines() if '=' in line)
        samples.append({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'x':int(d['X']),'y':int(d['Y']),'focus':int(b.stdout),'errors':a.stderr+b.stderr})
        ending.wait(.1)
def host_audio():
    def read(*args):return json.loads(subprocess.run(['pactl','-f','json',*args],env=HOST,capture_output=True,text=True,check=True).stdout)
    info=read('info');sinks=read('list','sinks');sources=read('list','sources')
    return {'default_sink':info.get('default_sink_name'),'default_source':info.get('default_source_name'),
            'sinks':[{'name':x['name'],'active_port':x.get('active_port'),'mute':x['mute'],'volume':x['volume']} for x in sinks],
            'sources':[{'name':x['name'],'active_port':x.get('active_port'),'mute':x['mute']} for x in sources]}
observer=threading.Thread(target=host_monitor,daemon=True);observer.start()
stage=sys.argv[1]
summary={'stage':stage,'source_sha256':hashlib.sha256(ADAPTER.read_bytes()).hexdigest(),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    if stage=='stage1':
        api('doctor');api('input','--help')
        summary['start']=api('start','--id',SESSION,'--width',1024,'--height',768,'--ttl',600)
        api('status','--id',SESSION)
        oversized=api('input','--id',SESSION,'--type','x'*1025,ok=False)
        assert oversized['error']['code']=='TEXT_TOO_LONG'
        # Every application is launched by the public exec endpoint.
        args=['input','--type','value with spaces ; $(notexecuted)','--help']
        script='import json,pathlib,sys; (pathlib.Path.home()/"argv-proof.json").write_text(json.dumps(sys.argv[1:])); print(json.dumps(sys.argv[1:]),flush=True)'
        rec=execute('python3','-c',script,*args)
        summary['exec_argv_preserved']=json.loads(text_log(rec))==args
        assert summary['exec_argv_preserved']
        topology={}
        for kind in ('sinks','sources','modules'):
            topology[kind]=json.loads(text_log(execute('pactl','-f','json','list',kind)))
        assert [x['name'] for x in topology['sinks']]==['isolated']
        assert [x['name'] for x in topology['sources']]==['isolated.monitor']
        assert set(x['name'] for x in topology['modules'])=={'module-null-sink','module-native-protocol-unix'}
        # Redact module arguments: they contain private cookie PATHS, not contents, but aren't needed as evidence.
        dump('private-audio-topology.json',{k:[{'name':x['name'],'driver':x.get('driver'),'ports':x.get('ports')} for x in v] for k,v in topology.items()})
        summary['audio_topology_verified_before_tone']=True
        summary['host_audio_before']=host_audio()
        document=RUN/'mousepad.txt';document.write_text('')
        app=execute('mousepad','--disable-server',str(document));summary['mousepad']=app
        time.sleep(1)
        api('capture','--id',SESSION,'--output',RUN/'mousepad-before.png')
        text='-leading two words ; $(ignored) café Ω 世界'
        api('input','--id',SESSION,'--type',text)
        api('input','--id',SESSION,'--key','ctrl+s')
        wait_until(lambda:document.read_text()==text)
        summary['mousepad_exact_unicode_metachar_text']=document.read_text()
        api('capture','--id',SESSION,'--output',RUN/'mousepad-after.png')
        assert (RUN/'mousepad-before.png').read_bytes()!=(RUN/'mousepad-after.png').read_bytes()
        message=execute('xmessage','-title','Deskhelper-xmessage-proof','-geometry','420x150+100+100','-buttons','Accept:0,Reject:1','-print','Owned native Xaw button proof')
        time.sleep(.4)
        ids=text_log(execute('xdotool','search','--onlyvisible','--name','^Deskhelper-xmessage-proof$')).split()
        geometry=text_log(execute('xwininfo','-id',ids[0]))
        g={'X':int(re.search(r'Absolute upper-left X:\s*(\d+)',geometry).group(1)),
           'Y':int(re.search(r'Absolute upper-left Y:\s*(\d+)',geometry).group(1)),
           'HEIGHT':int(re.search(r'Height:\s*(\d+)',geometry).group(1))}
        api('capture','--id',SESSION,'--output',RUN/'xmessage-before-click.png')
        api('input','--id',SESSION,'--move',int(g['X'])+30,int(g['Y'])+int(g['HEIGHT'])-15)
        api('input','--id',SESSION,'--click',int(g['X'])+30,int(g['Y'])+int(g['HEIGHT'])-15)
        chosen=text_log(message).strip();assert chosen=='Accept',chosen
        summary['xmessage_native_click']=chosen
        api('capture','--id',SESSION,'--output',RUN/'xmessage-after-click.png')
        # Only now generate/play a tone, through the verified private null sink.
        tone=RUN/'tone.wav'
        with wave.open(str(tone),'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
            f.writeframes(array.array('h',[round(6000*math.sin(2*math.pi*660*i/48000)) for i in range(48000)]).tobytes())
        recorded=RUN/'private-audio.wav'
        recording=execute('ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','pulse','-i','isolated.monitor','-t','3','-ac','1','-ar','48000',str(recorded))
        time.sleep(.6)
        execute('paplay',str(tone))
        def recording_finished():
            p=pathlib.Path('/proc',str(recording['pid']),'stat')
            return not p.exists() or p.read_text().rsplit(')',1)[1].split()[0]=='Z'
        wait_until(recording_finished,seconds=12)
        with wave.open(str(recorded),'rb') as f:
            rate=f.getframerate();values=array.array('h',f.readframes(f.getnframes()))
        rms=math.sqrt(sum(x*x for x in values)/len(values));peak=max(abs(x) for x in values)
        assert rms>500 and peak>2000,(rms,peak)
        summary['private_audio_capture']={'rate':rate,'samples':len(values),'rms':rms,'peak':peak,'tone_hz':660}
        summary['host_audio_after']=host_audio()
        assert summary['host_audio_before']==summary['host_audio_after']
        # Fail closed on a stale saved PID birth identity; no actual server/process is changed.
        state_path=pathlib.Path(summary['start']['session']['state_path']);original=state_path.read_text();bad=json.loads(original)
        bad['processes']['xvfb']['start_time']='0';state_path.write_text(json.dumps(bad))
        try:
            rejected=api('input','--id',SESSION,'--move',10,10,ok=False)
            rejected_stop=api('stop','--id',SESSION,ok=False)
            assert rejected['error']['code']=='SESSION_STALE' and rejected_stop['error']['code']=='SESSION_STALE'
            summary['stale_identity_fail_closed']=True
        finally:state_path.write_text(original)
        summary['running_after_checks']=api('status','--id',SESSION)
        summary['awaiting_separate_ssh_stage2']=True
    elif stage=='stage2':
        summary['reconnected_status']=api('status','--id',SESSION)
        doc=RUN/'mousepad.txt';before=doc.read_text()
        api('input','--id',SESSION,'--key','ctrl+End')
        api('input','--id',SESSION,'--type','\nreconnected native session')
        api('input','--id',SESSION,'--key','ctrl+s')
        wait_until(lambda:doc.read_text()==before+'\nreconnected native session')
        summary['reconnect_native_text']=doc.read_text()
        api('capture','--id',SESSION,'--output',RUN/'mousepad-after-reconnect.png')
        ttl_id=SESSION+'-ttl'
        summary['ttl_session']=api('start','--id',ttl_id,'--width',640,'--height',480,'--ttl',5)
        def ttl_stopped():
            response=api('status','--id',ttl_id)
            return response if response['session']['state']=='stopped' else None
        expired=wait_until(ttl_stopped,seconds=12);summary['ttl_expiry']=expired
        summary['stop']=api('stop','--id',SESSION)
        assert summary['stop']['session']['state']=='stopped'
        assert not summary['stop']['session']['cleanup']['remaining_owned_processes']
        assert all(summary['stop']['session']['cleanup'][k] for k in ('runtime_removed','display_socket_removed','display_lock_removed'))
        api('input','--id',SESSION,'--type','must not reach host',ok=False)
        api('capture','--id',SESSION,'--output',RUN/'must-not-exist.png',ok=False)
        assert not (RUN/'must-not-exist.png').exists()
        summary['closed_session_fail_closed']=True
    else:raise AssertionError('Unknown stage')
    summary['passed']=True
except Exception as exc:
    summary['passed']=False;summary['error']=repr(exc)
    raise
finally:
    ending.set();observer.join(timeout=5)
    dump('host-metadata-'+stage+'.json',samples)
    summary['host_metadata_samples']=len(samples)
    summary['host_positions']=sorted(set((s['x'],s['y']) for s in samples))
    summary['host_focus']=sorted(set(s['focus'] for s in samples))
    summary['host_errors']=[s['errors'] for s in samples if s['errors']]
    summary['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump('result-'+stage+'.json',summary)
    print(json.dumps(summary,indent=2))

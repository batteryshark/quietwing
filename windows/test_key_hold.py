"""Bounded key-hold regressions. Native calls are replaced before Windows compilation."""
import os, subprocess, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROBE=r'''
using System;using System.Collections.Generic;using System.Diagnostics;using System.Reflection;
static class KeyHoldProbe {
 public static HashSet<int> Down=new HashSet<int>();
 public static List<string> Events=new List<string>();
 public static int Guards,FailGuard,PartialCalls; public static bool CleanupBlocked,FailRelease;
 public static uint Scan(uint key){switch(key){case 13:return 0x1C;case 17:return 0x1D;case 37:return 0xE04B;case 65:return 0x1E;default:return 0;}}
 public static int Virtual(ushort scan){switch(scan){case 0x1C:return 13;case 0x1D:return 17;case 0x4B:return 37;case 0x1E:return 65;default:return 0;}}
 public static void Guard(){Guards++;if((FailGuard>0&&Guards==FailGuard)||(CleanupBlocked&&Guards>1))throw new Exception("SESSION_UNAVAILABLE: fixture boundary unavailable");}
 public static void Check(bool ok,string text){if(!ok)throw new Exception(text);}
 static MethodInfo Method(string name){return typeof(Worker).GetMethod(name,BindingFlags.Static|BindingFlags.NonPublic);}
 static object Hold(string chord,int ms){try{return Method("HoldKeys").Invoke(null,new object[]{chord,ms});}catch(TargetInvocationException e){throw e.InnerException;}}
 static void Reset(){Down.Clear();Events.Clear();Guards=FailGuard=PartialCalls=0;CleanupBlocked=FailRelease=false;}
 static void Error(Action run,string code){try{run();throw new Exception("Expected "+code);}catch(Exception e){Check(e.Message.StartsWith(code+":"),"Wrong error: "+e.Message);}}
 public static int Main(){try{
  Reset();var sw=Stopwatch.StartNew();var result=Hold("CTRL+LEFT",35);Check(sw.ElapsedMilliseconds>=35,"no hold interval");Check(Down.Count==0,"keys stuck");Check(Events.Count==4,"event count");Check(Events[0]=="down:17:8"&&Events[1]=="down:37:9"&&Events[2]=="up:37:11"&&Events[3]=="up:17:10","physical/reverse-order events: "+string.Join(",",Events));Check((bool)result.GetType().GetProperty("released").GetValue(result,null),"missing release receipt");
  foreach(int ms in new[]{-1,0,5001}){Reset();Error(()=>Hold("ENTER",ms),"INVALID_ARGUMENT");Check(Events.Count==0,"invalid duration injected");}
  foreach(string chord in new[]{"CTRL+CONTROL","A+A","NO_SUCH_KEY","é"}){Reset();Error(()=>Hold(chord,20),"INVALID_ARGUMENT");Check(Events.Count==0,"invalid chord injected");}
  Reset();Down.Add(13);Error(()=>Hold("ENTER",20),"KEY_ALREADY_DOWN");Check(Events.Count==0&&Down.Contains(13),"adopted preexisting key");
  Reset();FailGuard=1;Error(()=>Hold("ENTER",20),"SESSION_UNAVAILABLE");Check(Events.Count==0,"initial failed guard injected");
  Reset();FailGuard=2;Error(()=>Hold("ENTER",20),"SESSION_UNAVAILABLE");Check(Down.Count==0&&Events.Count==2,"recoverable guard failure did not release");
  Reset();PartialCalls=1;Error(()=>Hold("CTRL+LEFT",20),"INPUT_REJECTED");Check(Down.Count==0&&Events.Count==3,"partial press was not released");
  Reset();FailRelease=true;Error(()=>Hold("ENTER",20),"KEY_RELEASE_UNCONFIRMED");Check(Events.Count==1,"failed release silently replayed input");
  Reset();CleanupBlocked=true;Error(()=>Hold("ENTER",20),"KEY_RELEASE_UNCONFIRMED");Check(Events.Count==1,"cleanup bypassed changed boundary");
  Console.WriteLine("Held-key worker passed physical chords, bounds, ownership, partial input, failure cleanup and boundary refusal; all OS calls faked.");return 0;
 }catch(Exception e){Console.Error.WriteLine(e);return 1;}}
}
'''
class HeldKeys(unittest.TestCase):
    def test_public_hold_path_keeps_existing_guards_and_worker_owned_release(self):
        s=(HERE/'Worker.cs').read_text();h=(HERE/'KeyHold.cs').read_text()
        self.assertIn('key_hold=true',s);self.assertIn('KeyHold.Run(milliseconds,',s)
        self.assertIn('GetAsyncKeyState(k)&0x8000',s)
        self.assertIn('AudioProbe.EnsureSilent()',s);self.assertIn('ProviderStatus.RequireConnection',s)
        self.assertIn('finally {',h);self.assertIn('guard(); release();',h)
        self.assertIn('KEY_RELEASE_UNCONFIRMED',h)
    @unittest.skipUnless(os.name=='nt','Actual C# worker tests execute with fake OS calls on Windows CI')
    def test_actual_worker_with_fake_keyboard_and_session_apis(self):
        s=(HERE/'Worker.cs').read_text()
        start=s.index(' static void Guard(){');end=s.index('\n static ',start+1)
        s=s[:start]+' static void Guard(){KeyHoldProbe.Guard();}'+s[end:]
        replacements={
          '[DllImport("user32.dll")]static extern short GetAsyncKeyState(int key);':'static short GetAsyncKeyState(int key){return (short)(KeyHoldProbe.Down.Contains(key)?-32768:0);}',
          '[DllImport("user32.dll",EntryPoint="MapVirtualKeyW")]static extern uint MapVirtualKey(uint code,uint mode);':'static uint MapVirtualKey(uint code,uint mode){return KeyHoldProbe.Scan(code);}',
          '[DllImport("user32.dll")]static extern uint SendInput(uint count,INPUT[] inputs,int size);':'''static uint SendInput(uint count,INPUT[] inputs,int size){bool up=(inputs[0].u.ki.flags&2)!=0;if(up&&KeyHoldProbe.FailRelease)return 0;int limit=KeyHoldProbe.PartialCalls>0?1:(int)count;bool partial=KeyHoldProbe.PartialCalls>0;if(partial)KeyHoldProbe.PartialCalls--;for(int i=0;i<limit;i++){var k=inputs[i].u.ki;int vk=KeyHoldProbe.Virtual(k.scan);bool released=(k.flags&2)!=0;KeyHoldProbe.Events.Add((released?"up:":"down:")+vk+":"+k.flags);if(released)KeyHoldProbe.Down.Remove(vk);else KeyHoldProbe.Down.Add(vk);}return partial?0:count;}'''
        }
        for declaration,fake in replacements.items():
            self.assertEqual(s.count(declaration),1);s=s.replace(declaration,fake)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);worker=root/'Worker.cs';worker.write_text(s);probe=root/'Probe.cs';probe.write_text(PROBE)
            exe=root/'check.exe';compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            result=subprocess.run([str(compiler),'/nologo','/target:exe','/main:KeyHoldProbe','/out:'+str(exe),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Web.Extensions.dll',str(worker),str(HERE/'NativeSupport.cs'),str(HERE/'ProviderStatus.cs'),str(HERE/'KeyHold.cs'),str(probe)],capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())
if __name__=='__main__':unittest.main()

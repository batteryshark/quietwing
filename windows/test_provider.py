"""Readiness regression: cached pre-login state must not override live status."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('readiness_adapter', Path(__file__).with_name('adapter.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class ProviderReadiness(unittest.TestCase):
    def setUp(self):
        self.cached = dict(pid=123, desktopState='connected', childSessionExists=False,
                           childSessionId=-1, connectedAt='connection-1')
        self.live = dict(self.cached, running=True, attached=True,
                         childSessionExists=True, childSessionId=4)
        self.parent = dict(pid=123, session=1, birthTicks=456, path='provider.exe')

    def require(self, live=None, parent=None):
        with patch.object(a, 'provider', return_value=(Path('provider'), self.cached, {})), \
             patch.object(a, 'console_id', return_value=1), \
             patch.object(a, 'process', return_value=self.parent if parent is None else parent), \
             patch.object(a, 'native_state', return_value=0), \
             patch.object(a, 'live_provider', create=True, return_value=self.live if live is None else live) as query:
            result = a.require_provider()
            query.assert_called_once_with(self.parent)
            return result

    def test_stale_prelogin_cache_uses_fresh_child(self):
        self.assertEqual(self.require()[1]['childSessionId'], 4)
        self.assertEqual(self.cached['childSessionId'], -1, 'Provider file must not be repaired or rewritten')

    def test_live_disconnected_refuses_even_when_cache_says_connected(self):
        self.cached.update(childSessionId=4, childSessionExists=True)
        with self.assertRaises(a.Failure) as error:
            self.require(dict(self.live, desktopState='idle', attached=False))
        self.assertEqual(error.exception.code, 'AUTHENTICATED_SESSION_REQUIRED')

    def test_live_absent_or_console_child_refused(self):
        for child in [-1, 0, 1]:
            with self.subTest(child=child), self.assertRaises(a.Failure) as error:
                self.require(dict(self.live, childSessionId=child))
            self.assertEqual(error.exception.code, 'AUTHENTICATED_SESSION_REQUIRED')

    def test_live_wrong_provider_or_missing_connection_refused(self):
        for changes in [dict(pid=124), dict(connectedAt=None), dict(running=False), dict(attached=False)]:
            with self.subTest(changes=changes), self.assertRaises(a.Failure):
                self.require(dict(self.live, **changes))

    def test_viewer_outside_console_refused_without_query(self):
        with patch.object(a, 'provider', return_value=(Path('provider'), self.cached, {})), \
             patch.object(a, 'console_id', return_value=1), \
             patch.object(a, 'process', return_value=dict(self.parent, session=2)), \
             patch.object(a, 'live_provider', create=True) as query, self.assertRaises(a.Failure) as error:
            a.require_provider()
        self.assertEqual(error.exception.code, 'PARENT_MISMATCH')
        query.assert_not_called()

NATIVE_PROBE = r'''
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
static class StatusProbe {
 static JavaScriptSerializer Json = new JavaScriptSerializer();
 static Process Self = Process.GetCurrentProcess();
 static int Pid = Self.Id;
 static long Birth = Self.StartTime.ToUniversalTime().Ticks;
 static int Cases;
 static void Check(bool ok, string message) { if (!ok) throw new Exception(message); }
 static Dictionary<string, object> Snapshot(int child, string connection) {
  return new Dictionary<string, object> { {"pid", Pid}, {"running", true}, {"attached", true},
   {"desktopState", "connected"}, {"childSessionExists", child > 0},
   {"childSessionId", child}, {"connectedAt", connection} };
 }
 static string Reply(Dictionary<string, object> state) {
  return Json.Serialize(new {ok=true, exitCode=0, json=Json.Serialize(state)});
 }
 static Dictionary<string, object> Query(string reply, int pid, long birth, bool hangs, bool expectsRequest) {
  string name = "QuietWing-Status-Test-" + Guid.NewGuid().ToString("N");
  Exception serverError = null;
  using (var server = new NamedPipeServerStream(name, PipeDirection.InOut, 1,
      PipeTransmissionMode.Byte, PipeOptions.Asynchronous)) {
   var thread = new Thread(delegate() {
    try {
     server.WaitForConnection();
     string request = new StreamReader(server, Encoding.UTF8).ReadLine();
     if (expectsRequest) Check(request == "{\"cmd\":\"status\",\"args\":[]}", "Only status with no arguments is allowed");
     else { Check(request == null, "Sent a request to an unverified server"); return; }
     if (hangs) { Thread.Sleep(500); return; }
     byte[] data = Encoding.UTF8.GetBytes(reply + "\n");
     server.Write(data, 0, data.Length);
     server.Flush();
     server.WaitForPipeDrain();
    } catch (Exception error) { serverError=error; }
   });
   thread.IsBackground=true;thread.Start();
   try { return ProviderStatus.ReadFrom(name, pid, birth, hangs ? 200 : 3000); }
   finally {
    Check(thread.Join(5000), "Fixture server did not exit");
    if (serverError!=null) throw serverError;
   }
  }
 }
 static void Reject(Action action, string detail) {
  bool refused=false;
  try {action();} catch(Exception error) {
   refused=error.Message.StartsWith("PROVIDER_UNAVAILABLE:") || error.Message.StartsWith("SESSION_UNAVAILABLE:");
  }
  Check(refused, "Accepted unsafe live status: " + detail);Cases++;
 }
 public static int Main(string[] args) {
  try {
   // Replay the connection/login race and independent status-pipe reconnects.
   string cached = Reply(Snapshot(-1, "first"));
   File.WriteAllText(args[0], cached);
   var live=Query(Reply(Snapshot(4, "first")), Pid, Birth, false, true);
   ProviderStatus.RequireConnection(live, Pid, 4, "first");Cases++;
   Check(File.ReadAllText(args[0]) == cached, "Status must never refresh or repair provider state");Cases++;
   for (int i=0;i<5;i++) {
    live=Query(Reply(Snapshot(4, "first")), Pid, Birth, false, true);
    ProviderStatus.RequireConnection(live, Pid, 4, "first");Cases++;
   }
   var absent=Query(Reply(Snapshot(-1, "first")), Pid, Birth, false, true);
   Reject(()=>ProviderStatus.RequireConnection(absent, Pid, 4, "first"), "no registered child yet");
   var next=Query(Reply(Snapshot(4, "next")), Pid, Birth, false, true);
   Reject(()=>ProviderStatus.RequireConnection(next, Pid, 4, "first"), "new connection in same session");
   ProviderStatus.RequireConnection(next, Pid, 4, "next");Cases++;
   var different=Query(Reply(Snapshot(5, "next")), Pid, Birth, false, true);
   Reject(()=>ProviderStatus.RequireConnection(different, Pid, 4, "next"), "replacement child");
   foreach(string field in new[]{"pid","running","attached","desktopState","childSessionExists","childSessionId","connectedAt"}) {
    var changed=Snapshot(4,"first");changed.Remove(field);
    Reject(()=>ProviderStatus.RequireConnection(changed, Pid, 4, "first"), "missing " + field);
   }
   var disconnected=Snapshot(4,"first");disconnected["desktopState"]="idle";
   Reject(()=>ProviderStatus.RequireConnection(disconnected, Pid, 4, "first"), "disconnect");
   var stopped=Snapshot(4,"first");stopped["running"]=false;
   Reject(()=>ProviderStatus.RequireConnection(stopped, Pid, 4, "first"), "provider stopping");
   Reject(()=>Query(Reply(Snapshot(4,"first")), int.MaxValue, Birth, false, false), "wrong native pipe PID");
   Reject(()=>Query(Reply(Snapshot(4,"first")), Pid, Birth+1, false, false), "PID reuse/birth mismatch");
   var wrongPid=Snapshot(4,"first");wrongPid["pid"]=Pid+1;
   Reject(()=>Query(Reply(wrongPid), Pid, Birth, false, true), "snapshot PID mismatch");
   Reject(()=>Query("{\"ok\":false,\"message\":\"private provider detail\"}", Pid, Birth, false, true), "provider error");
   Reject(()=>Query("garbled", Pid, Birth, false, true), "malformed envelope");
   Reject(()=>Query(new string('x',65537), Pid, Birth, false, true), "oversized envelope");
   var clock=Stopwatch.StartNew();
   Reject(()=>Query("", Pid, Birth, true, true), "hung provider");
   Check(clock.ElapsedMilliseconds<2000,"Read-only query exceeded its deadline");Cases++;
   Console.WriteLine(Cases + " live status/race/identity/refusal cases passed without a desktop.");
   return 0;
  } catch (Exception error) { Console.Error.WriteLine(error);return 1; }
 }
}
'''


class NativeProviderProtocol(unittest.TestCase):
    @unittest.skipUnless(__import__('os').name == 'nt', 'Native named-pipe regression runs on Windows without a desktop')
    def test_live_protocol_race_and_reconnect_refusals(self):
        import os
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe = root / 'StatusProbe.cs'
            probe.write_text(NATIVE_PROBE, encoding='utf-8')
            exe = root / 'StatusProbe.exe'
            compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
            build = subprocess.run([str(compiler), '/nologo', '/target:exe', '/out:' + str(exe),
                '/r:System.Web.Extensions.dll', str(Path(__file__).with_name('ProviderStatus.cs')), str(probe)],
                capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe), str(root / 'cached.json')], capture_output=True, text=True,
                timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('live status/race/identity/refusal cases passed without a desktop', run.stdout)


if __name__ == '__main__':
    unittest.main()

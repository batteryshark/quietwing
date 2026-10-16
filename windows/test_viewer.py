"""Viewer cleanup regression: no real provider, windows, capture or input.

The Windows-only case compiles the actual worker with its viewer OS calls replaced
by in-memory fakes, then runs its real timer/finally paths. Other worker code is
compiled unchanged but is never invoked. The portable invariant also catches an
accidental native show/restore call without requiring a Windows machine.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent

PROBE = r'''
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Web.Script.Serialization;

static class ViewerProbe {
 public static bool Visible;
 public static List<int> Commands = new List<int>();
 static void Check(bool condition, string message) {
  if (!condition) throw new Exception(message);
 }
 static void Case(string root, string name, bool visible, bool hide, string exit) {
  string folder = Path.Combine(root, name);
  Directory.CreateDirectory(folder);
  Visible = visible;
  Commands.Clear();
  var self = Process.GetCurrentProcess();
  var json = new JavaScriptSerializer();
  File.WriteAllText(Path.Combine(folder, "parent.json"), json.Serialize(new {
   viewerBirthTicks = self.StartTime.ToUniversalTime().Ticks,
   viewerHwnd = 1L, viewerVisible = visible, viewerMinimized = false
  }));
  File.WriteAllText(Path.Combine(folder, "ready.json"), json.Serialize(new {
   session = new { workerPid = exit == "crash" ? int.MaxValue : self.Id,
    workerBirthTicks = self.StartTime.ToUniversalTime().Ticks }
  }));
  if (exit == "stop") File.WriteAllText(Path.Combine(folder, "stopped.json"), "{}");
  if (exit == "rollback") File.WriteAllText(Path.Combine(folder, "viewer-stop.flag"), "rollback");
  typeof(Worker).GetMethod("Viewer", BindingFlags.Static | BindingFlags.NonPublic)
   .Invoke(null, new object[] {folder, self.Id, self.SessionId, hide});
  bool expected = hide ? false : visible;
  Check(Visible == expected, name + ": cleanup revealed the viewer");
  Check(Commands.Count == (hide && visible ? 1 : 0), name + ": cleanup changed visibility");
  foreach (int command in Commands) Check(command == 0, name + ": non-hide window command");
  var result = json.Deserialize<Dictionary<string, object>>(
   File.ReadAllText(Path.Combine(folder, "viewer-stopped.json")));
  Check(!(bool)result["restored"], name + ": result falsely reports viewer restoration");
  Check((bool)result["visible"] == expected, name + ": incorrect visibility result");
  Check(!(bool)result["minimized"], name + ": viewer minimized");
 }
 [STAThread] public static int Main(string[] args) {
  try {
  foreach (string exit in new[] {"stop", "crash", "rollback"}) {
   Case(args[0], exit + "-visible-hide", true, true, exit);
   Case(args[0], exit + "-hidden-hide", false, true, exit);
   Case(args[0], exit + "-visible-observe", true, false, exit);
   Case(args[0], exit + "-hidden-observe", false, false, exit);
  }
  Console.WriteLine("12 actual viewer cleanup paths passed with fake OS calls.");
  return 0;
  } catch (Exception error) {
   Console.Error.WriteLine(error.Message);
   return 1;
  }
 }
}
'''


class ViewerCleanup(unittest.TestCase):
    def test_worker_cannot_show_or_restore_viewer(self):
        source = (HERE / "Worker.cs").read_text()
        calls = re.findall(r"ShowWindowAsync\(hwnd,\s*([^)]*)\)", source)
        self.assertTrue(calls, "The explicit attach hide operation must remain")
        self.assertEqual(calls, ["0"], "Only explicit SW_HIDE is allowed; cleanup must never show the viewer")

    @unittest.skipUnless(os.name == "nt", "C# regression runs on Windows CI with fake OS calls")
    def test_real_viewer_stop_crash_and_rollback_preserve_visibility(self):
        source = (HERE / "Worker.cs").read_text()
        replacements = {
            '[DllImport("kernel32.dll")]static extern uint WTSGetActiveConsoleSessionId();':
                'static uint WTSGetActiveConsoleSessionId(){return (uint)Process.GetCurrentProcess().SessionId;}',
            '[DllImport("wtsapi32.dll",SetLastError=true)]static extern bool WTSGetChildSessionId(out uint session);':
                'static bool WTSGetChildSessionId(out uint session){session=(uint)Process.GetCurrentProcess().SessionId;return true;}',
            '[DllImport("user32.dll")]static extern bool GetCursorPos(out POINT point);':
                'static bool GetCursorPos(out POINT point){point=new POINT{X=11,Y=22};return true;}',
            '[DllImport("user32.dll")]static extern IntPtr GetForegroundWindow();':
                'static IntPtr GetForegroundWindow(){return new IntPtr(777);}',
            '[DllImport("user32.dll")]static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);':
                'static uint GetWindowThreadProcessId(IntPtr h,out uint pid){pid=(uint)Process.GetCurrentProcess().Id;return 1;}',
            '[DllImport("user32.dll")]static extern bool IsWindowVisible(IntPtr h);':
                'static bool IsWindowVisible(IntPtr h){return ViewerProbe.Visible;}',
            '[DllImport("user32.dll")]static extern bool IsIconic(IntPtr h);':
                'static bool IsIconic(IntPtr h){return false;}',
            '[DllImport("user32.dll")]static extern bool ShowWindowAsync(IntPtr h,int cmd);':
                'static bool ShowWindowAsync(IntPtr h,int cmd){ViewerProbe.Commands.Add(cmd);ViewerProbe.Visible=cmd!=0;return true;}',
        }
        for declaration, fake in replacements.items():
            self.assertEqual(source.count(declaration), 1, "Update fake boundary after native declaration changes")
            source = source.replace(declaration, fake)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            worker = root / "Worker.cs"
            worker.write_text(source, encoding="utf-8")
            probe = root / "ViewerProbe.cs"
            probe.write_text(PROBE, encoding="utf-8")
            exe = root / "ViewerProbe.exe"
            compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
            build = subprocess.run([str(compiler), "/nologo", "/target:exe", "/main:ViewerProbe",
                "/out:" + str(exe), "/r:System.Windows.Forms.dll", "/r:System.Drawing.dll",
                "/r:System.Web.Extensions.dll", str(worker), str(HERE / "NativeSupport.cs"), str(HERE / "ProviderStatus.cs"), str(HERE / "KeyHold.cs"), str(probe)],
                capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe), str(root / "cases")], capture_output=True, text=True,
                timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("12 actual viewer cleanup paths passed", run.stdout)
            old_cleanup = "if(valid()&&hide&&visible)ShowWindowAsync(hwnd,4);"
            anchor = "timer.Stop();timer.Dispose();"
            self.assertEqual(source.count(anchor), 1)
            worker.write_text(source.replace(anchor, anchor + old_cleanup), encoding="utf-8")
            rebuild = subprocess.run(build.args, capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)
            negative = subprocess.run([str(exe), str(root / "old-cases")], capture_output=True,
                text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertNotEqual(negative.returncode, 0, "Regression must reject the old restore operation")
            self.assertIn("cleanup revealed the viewer", negative.stderr)


if __name__ == "__main__":
    unittest.main()

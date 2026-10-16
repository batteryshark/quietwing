// ParaDesk 1.1 publishes a pre-login file snapshot. Ask its existing owner for
// live status only; never launch it, refresh settings, or repair its state file.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;
using System.Threading.Tasks;

static class ProviderStatus {
 const string PipeName = "ParaDesk.Activate.v1";
 const int TimeoutMs = 5000;
 const int MaxReplyBytes = 65536;
 [DllImport("kernel32.dll", SetLastError=true)]
 static extern bool GetNamedPipeServerProcessId(Microsoft.Win32.SafeHandles.SafePipeHandle pipe, out uint pid);
 static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
 static Exception Unavailable() { return new Exception("PROVIDER_UNAVAILABLE: Live ParaDesk status could not be verified; no cached fallback or reconnect attempted"); }
 static void Identity(NamedPipeClientStream pipe, int pid, long birth) {
  uint actual;
  if (!GetNamedPipeServerProcessId(pipe.SafePipeHandle, out actual) || actual != pid) throw Unavailable();
  using (var process = Process.GetProcessById(pid))
   if (process.StartTime.ToUniversalTime().Ticks != birth || process.HasExited) throw Unavailable();
 }
 static int Remaining(Stopwatch clock, int timeout) {
  int left = timeout - (int)clock.ElapsedMilliseconds;
  if (left <= 0) throw Unavailable();
  return left;
 }
 static void Await(Task operation, Stopwatch clock, int timeout) {
  // Dispose cancels pending pipe IO on timeout. Observe its eventual fault without
  // closing an overlapped wait handle that the Windows completion callback owns.
  operation.ContinueWith(done => { var ignored = done.Exception; },
      TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously);
  if (!operation.Wait(Remaining(clock, timeout))) throw Unavailable();
 }
 internal static Dictionary<string, object> Read(int pid, long birth) { return ReadFrom(PipeName, pid, birth, TimeoutMs); }
 // The alternate name/timeout is used only by the desktop-free native regression.
 internal static Dictionary<string, object> ReadFrom(string name, int pid, long birth, int timeout) {
  try {
   var clock = Stopwatch.StartNew();
   using (var pipe = new NamedPipeClientStream(".", name, PipeDirection.InOut,
       PipeOptions.Asynchronous, TokenImpersonationLevel.Identification)) {
    pipe.Connect(Remaining(clock, timeout));
    Identity(pipe, pid, birth); // Verify the actual pipe server before sending anything.
    byte[] request = Encoding.UTF8.GetBytes("{\"cmd\":\"status\",\"args\":[]}\n");
    Await(pipe.WriteAsync(request, 0, request.Length), clock, timeout);
    using (var reply = new MemoryStream()) {
     byte[] buffer = new byte[4096];
     while (true) {
      Task<int> read = pipe.ReadAsync(buffer, 0, buffer.Length);
      Await(read, clock, timeout);
      int count = read.Result;
      if (count == 0) throw Unavailable();
      int newline = Array.IndexOf(buffer, (byte)'\n', 0, count);
      int length = newline < 0 ? count : newline;
      if (reply.Length + length > MaxReplyBytes) throw Unavailable();
      reply.Write(buffer, 0, length);
      if (newline < 0) continue;
      Identity(pipe, pid, birth);
      var envelope = Json.Deserialize<Dictionary<string, object>>(Encoding.UTF8.GetString(reply.ToArray()));
      if (envelope == null || !envelope.ContainsKey("ok") || !(envelope["ok"] is bool) || !(bool)envelope["ok"] ||
          !envelope.ContainsKey("exitCode") || !Equals(envelope["exitCode"], 0) ||
          !envelope.ContainsKey("json") || !(envelope["json"] is string)) throw Unavailable();
      var snapshot = Json.Deserialize<Dictionary<string, object>>((string)envelope["json"]);
      if (snapshot == null || !snapshot.ContainsKey("pid") || !Equals(snapshot["pid"], pid)) throw Unavailable();
      return snapshot;
     }
    }
   }
  } catch { throw Unavailable(); } // Do not expose provider text or protocol payloads.
 }
 internal static void RequireConnection(Dictionary<string, object> state, int pid, int child, string connection) {
  object value;
  if (!state.TryGetValue("pid", out value) || !Equals(value, pid) ||
      !state.TryGetValue("running", out value) || !Equals(value, true) ||
      !state.TryGetValue("attached", out value) || !Equals(value, true) ||
      !state.TryGetValue("desktopState", out value) || !Equals(value, "connected") ||
      !state.TryGetValue("childSessionExists", out value) || !Equals(value, true) ||
      !state.TryGetValue("childSessionId", out value) || !Equals(value, child) ||
      string.IsNullOrEmpty(connection) ||
      !state.TryGetValue("connectedAt", out value) || !Equals(value, connection))
   throw new Exception("SESSION_UNAVAILABLE: Provider no longer reports the bound live connection and child; explicit reattach required");
 }
}

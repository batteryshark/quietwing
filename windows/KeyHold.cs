using System;
using System.Diagnostics;
using System.Runtime.ExceptionServices;
using System.Threading;

// One bounded lease in the worker, independent of the caller's connection.
// Never retain key-down state between requests or replay a failed press.
static class KeyHold {
 internal const int MaxMilliseconds = 5000;
 internal static long Run(int milliseconds, Action preflight, Action press,
                          Action release, Action guard) {
  if(milliseconds < 1 || milliseconds > MaxMilliseconds)
   throw new Exception("INVALID_ARGUMENT: hold duration must be 1-5000 ms");
  guard();
  preflight(); // An already-down key is not ours to release.
  var elapsed = Stopwatch.StartNew();
  Exception failure = null;
  try {
   // Even a partially rejected SendInput may have pressed some keys. Cleanup
   // covers the whole preflighted chord before propagating any press error.
   press();
   while(elapsed.ElapsedMilliseconds < milliseconds) {
    guard();
    int remaining = milliseconds - (int)elapsed.ElapsedMilliseconds;
    if(remaining > 0) Thread.Sleep(Math.Min(10, remaining));
   }
  } catch(Exception error) { failure = error; }
  finally {
   try { guard(); release(); }
   catch(Exception error) {
    // Safety takes precedence over cleanup: never send key-up into a changed
    // console/provider/secure desktop, and never pretend release succeeded.
    throw new Exception("KEY_RELEASE_UNCONFIRMED: held-key cleanup could not be verified; no input was retargeted. " + error.Message, failure ?? error);
   }
  }
  if(failure != null) ExceptionDispatchInfo.Capture(failure).Throw();
  return elapsed.ElapsedMilliseconds;
 }
}

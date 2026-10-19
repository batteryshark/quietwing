#!/usr/bin/env python3
"""Compile the actual target ledger with synthetic data, never a guest/desktop.

Explicit macOS developer check, not part of portable checks. The extracted class
is tested without calling any AX, libproc, signal, application or clipboard API.
The production GuestBridge startup/virtualization guard is not included/run.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'macos/GuestBridge.swift').read_text().split('\nfunc json(', 1)[0]
test = r'''
@MainActor @main struct LedgerTest {
 static func main() throws {
  let ledger=GuestTargets()
  ledger.bind("owner-one")
  let target=GuestTargets.ProcessTarget(pid:42,birth:"synthetic-birth",created:Date())
  ledger.processes["observed"]=target
  ledger.bind("owner-one")
  precondition(ledger.processes["observed"] != nil)
  ledger.bind("owner-two")
  precondition(ledger.processes.isEmpty && ledger.windows.isEmpty)
  do {
   _=try ledger.perform(["op":"processes","action":"terminate","pid":42,"target":"observed"])
   fatalError("stale owner token accepted")
  } catch is GuestTargetError {}
  ledger.processes["current"]=target
  do {
   _=try ledger.perform(["op":"processes","action":"terminate","pid":43,"target":"current"])
   fatalError("mismatched PID accepted")
  } catch is GuestTargetError {}
  let expired=GuestTargets.ProcessTarget(pid:42,birth:"synthetic-birth",created:Date(timeIntervalSinceNow:-301))
  do {
   try ledger.validate(expired)
   fatalError("expired target accepted")
  } catch is GuestTargetError {}
  print("Guest target ledger: owner reset, exact PID and expiry passed; no desktop/process APIs called")
 }
}
'''
with tempfile.TemporaryDirectory(prefix='quietwing-target-ledger-') as directory:
    path = Path(directory)
    swift = path / 'LedgerTest.swift'
    swift.write_text(source + test)
    subprocess.run(['xcrun', 'swiftc', '-parse-as-library', str(swift), '-o', str(path/'test')], check=True)
    subprocess.run([str(path/'test')], check=True)

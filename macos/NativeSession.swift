import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
import Security
import Darwin

func currentFacts() -> SessionFacts {
    let dict=CGSessionCopyCurrentDictionary() as? [String:Any]
    var sid: SecuritySessionId=0
    var attrs: SessionAttributeBits=[]
    let status=SessionGetInfo(callerSecuritySession,&sid,&attrs)
    var console=stat()
    let hasConsole=stat("/dev/console",&console)==0
    return SessionFacts(uid:getuid(),euid:geteuid(),consoleUID:hasConsole ? console.st_uid : nil,
        cgUID:(dict?[kCGSessionUserIDKey as String] as? NSNumber)?.uint32Value,
        onConsole:dict?[kCGSessionOnConsoleKey as String] as? Bool,
        loginDone:dict?[kCGSessionLoginDoneKey as String] as? Bool,
        securitySessionID:status==0 ? sid : nil,
        graphicAccess:attrs.contains(.sessionHasGraphicAccess),remoteAttribute:attrs.contains(.sessionIsRemote),securityStatus:status)
}
func permissions() -> [String:Bool] {
    ["screen_capture":CGPreflightScreenCaptureAccess(),
     "accessibility":AXIsProcessTrustedWithOptions([kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String:false] as CFDictionary),
     "post_event":CGPreflightPostEventAccess(),"listen_event":CGPreflightListenEventAccess()]
}
func dictionary<T:Encodable>(_ value:T)->[String:Any] {
    (try? JSONSerialization.jsonObject(with:JSONEncoder().encode(value))) as? [String:Any] ?? [:]
}

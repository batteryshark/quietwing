import Foundation

struct SessionFacts: Codable {
    var uid: UInt32
    var euid: UInt32
    var consoleUID: UInt32?
    var cgUID: UInt32?
    var onConsole: Bool?
    var loginDone: Bool?
    var securitySessionID: UInt32?
    var graphicAccess: Bool
    var remoteAttribute: Bool
    var securityStatus: Int32

    func denial(expectedUID: UInt32?, expectedSession: UInt32?, requireBinding: Bool) -> String? {
        if uid < 500 || euid != uid { return "invalid_worker_identity" }
        guard let consoleUID else { return "console_identity_unknown" }
        if consoleUID == uid { return "worker_is_console_user" }
        guard cgUID == uid else { return "gui_user_mismatch" }
        guard onConsole == false else { return "console_gui_forbidden" }
        guard loginDone == true else { return "gui_login_incomplete" }
        guard securityStatus == 0, graphicAccess, let sid = securitySessionID, sid != 0 else { return "not_graphical_security_session" }
        if requireBinding && (expectedUID == nil || expectedSession == nil) { return "explicit_session_binding_required" }
        if let expectedUID, expectedUID != uid { return "expected_user_mismatch" }
        if let expectedSession, expectedSession != sid { return "expected_session_mismatch" }
        return nil
    }
}

func guardSelfTest() -> [String: Any] {
    let good = SessionFacts(uid: 502, euid: 502, consoleUID: 501, cgUID: 502, onConsole: false,
        loginDone: true, securitySessionID: 9001, graphicAccess: true, remoteAttribute: true, securityStatus: 0)
    var checks = [[String: Any]]()
    func check(_ name: String, _ state: SessionFacts, _ expected: String?, _ uid: UInt32? = 502, _ sid: UInt32? = 9001) {
        let actual = state.denial(expectedUID: uid, expectedSession: sid, requireBinding: true)
        checks.append(["name": name, "passed": actual == expected, "actual": actual ?? "allowed"])
    }
    check("separate_graphical_user_bound", good, nil)
    var s=good;s.consoleUID=502;check("console_user_even_if_flag_false",s,"worker_is_console_user")
    s=good;s.onConsole=true;check("console_flag",s,"console_gui_forbidden")
    s=good;s.onConsole=nil;check("unknown_console_flag",s,"console_gui_forbidden")
    s=good;s.consoleUID=nil;check("unknown_console_uid",s,"console_identity_unknown")
    s=good;s.cgUID=501;check("different_gui_uid",s,"gui_user_mismatch")
    s=good;s.loginDone=false;check("incomplete_login",s,"gui_login_incomplete")
    s=good;s.graphicAccess=false;check("ssh_without_graphical_session",s,"not_graphical_security_session")
    s=good;s.securityStatus = -60500;check("security_query_failure",s,"not_graphical_security_session")
    s=good;s.euid=0;check("root_asuser_without_setuid",s,"invalid_worker_identity")
    check("wrong_expected_user",good,"expected_user_mismatch",503)
    check("wrong_expected_session",good,"expected_session_mismatch",502,9002)
    check("missing_binding",good,"explicit_session_binding_required",nil,nil)
    return ["ok":checks.allSatisfy{$0["passed"] as? Bool == true},"tests":checks]
}

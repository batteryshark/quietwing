# Native macOS separate-user setup — proposal, not applied

This document covers only the optional `--backend native` adapter, a guarded worker/preflight implementation. The default VM backend is implemented; see [PROVISIONING.md](PROVISIONING.md). It currently refuses to create a GUI login and refuses execution/input because no audio-isolation provider has been verified. No account, Sharing, TCC, firewall, startup, or login-policy changes have been made.

## Current blockers (measured 2026-10-13)

Only ordinary local account UID501 exists; it owns the console GUI. Screen Sharing's launchd service is absent and TCP5900 has no listener. `sudo -n true` outside the tool execution sandbox returns “a password is required.” The proposed short name `deskhelper` did not exist at inspection. Capture preflight was true for the existing direct command-launch context, while Accessibility, post-event and listen-event preflights were false. These grants do not transfer to another account or differently launched worker.

## One owner setup visit

These are explicit user-local steps; no password should be sent to the agent, put in a command argument, saved in a script, or added to evidence.

1. In Users & Groups, create a **standard** local account with short name `deskhelper`, after checking the name remains free. Enter the account password privately in macOS UI. A sharing-only user cannot establish the required GUI. Administrator membership is unnecessary for normal app work.
2. In General → Sharing, enable **Screen Sharing**, select **Only these users**, and add only `deskhelper`. Do not enable “anyone may request permission” or legacy VNC-password access for this test. If Remote Management is already enabled at execution time, stop and review instead of silently changing it. Do not change firewall policy, enable Remote Login, or store connection credentials.
3. From another Mac's Apple Screen Sharing client, connect and authenticate as `deskhelper`; select the separate login/virtual-display choice rather than sharing the human's display. Start with Standard. Keep the human logged into the original console account. If the client does not offer a separate-user desktop, stop instead of switching the console user.
4. Finish any first-login setup **inside the remote `deskhelper` desktop**, leaving Apple Account/iCloud sign-in optional. Run the helper's `doctor` from this graphical context and record its UID/security-session ID. Only an explicit different-user, non-console graphical session is attachable.
5. If required, the owner grants Screen Recording and Accessibility to the stable worker identity in this dedicated account's privacy settings. The adapter never calls permission-request APIs. Grant/launch attribution must be verified; compiling a binary is not a permission grant.
6. Stop at capture/identity acceptance until audio output has a measured isolated/silent route. Native capture is implemented, but generic exec and input are deliberately disabled by a non-bypassable audio gate. A different login alone does not establish silent output.

This is one planned setup visit, not a guarantee of one authorization click: macOS may separately require account administration, remote login authentication, first-login setup, and privacy grants. Same-Mac loopback is **unverified**, so these steps currently require an Apple client on another Mac for the documented reference route. No new-user provisioning script is supplied because there is no approved password-handling or owner-authentication flow.

## Worker launch and transport

Run `python3 macos/build.py` to compile only. `python3 deskhelper.py doctor --backend native` performs read-only API preflight; it does not automatically build, install a service, prompt, or start a viewer.

The JSONL worker is `~/Library/Caches/desktop-session-helper/macos/deskhelper-macos-worker --stdio` (or `DESKHELPER_BUILD_ROOT/macos/deskhelper-macos-worker --stdio`). It can be launched in the already established dedicated Aqua login. A production transport/bootstrap has not yet been installed or live-validated. No TCP listener, LaunchAgent, LaunchDaemon, login item, or automatic startup is created here.

Apple's installed `launchctl(1)` documents that `asuser UID` adopts bootstrap/audit context but does **not** change Unix credentials or the environment. Running `sudo launchctl asuser UID ...` while remaining root is insufficient; the worker rejects it. A later approved bootstrap must enter both the correct GUI bootstrap/security session and the dedicated real/effective UID. An Aqua LaunchAgent is a suitable supported mechanism, but installation and controller transport need a separate reviewed implementation. Do not create a fake graphical security session with `SessionCreate` or use a background SSH session as evidence of a GUI login.

From the dedicated GUI context, an explicit binding is:

```text
python3 deskhelper.py attach --backend native --id mac-agent --uid DEDICATED_UID --session-id GRAPHICAL_SECURITY_SESSION_ID
python3 deskhelper.py status --backend native --id mac-agent
python3 deskhelper.py capture --backend native --id mac-agent --output /absolute/new-capture.png
python3 deskhelper.py stop --backend native --id mac-agent
```

Attach retains an external OS login; stop removes only the adapter's private binding. It never logs off that user, disables Sharing, or terminates human applications. The stateless CLI currently owns no launched applications. The staged persistent worker retains direct child objects, but generic execution is disabled and descendant cleanup is not claimed.

## Required acceptance before claiming parity

Use a generic native application in the separate GUI, not just a custom fixture. Prove fresh capture and real keyboard/mouse delivery while a host-side sentinel records the human cursor/focus unchanged; verify no host audio leakage, viewer visibility, disconnect/reconnect, session-switch rejection, owned-process cleanup, and absence of unrelated effects. Revalidate UID, graphical security-session ID, console status and TCC before every capture/input operation. GPU capability and input/session/audio isolation are separate results.

## Primary references

- [Apple Remote Desktop separate-user virtual display](https://support.apple.com/guide/remote-desktop/choose-how-to-control-and-observe-apd4f46319e/mac): explicitly describes using the authenticated account's desktop while another local user continues working. It does not establish same-Mac loopback.
- [Apple Screen Sharing setup](https://support.apple.com/guide/mac-help/turn-screen-sharing-on-or-off-mh11848/mac): selected-user access and mutual exclusion with Remote Management.
- [Apple users and groups](https://support.apple.com/en-sg/guide/mac-help/-mchl3e281fc9/mac): standard versus sharing-only users.
- [Apple launchd user agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html): per-user agents execute in logged-in user contexts and end on logout. Installed `launchctl(1)` supplies the finer `gui/<uid>`, `login/<asid>` and `asuser` semantics.
- [Apple current-login event tap](https://developer.apple.com/documentation/coregraphics/cgeventtaplocation/cgsessioneventtap): login-session event boundary. Actual separate-user event delivery still requires acceptance.
- [Apple process-audio taps](https://developer.apple.com/documentation/coreaudio/capturing-system-audio-with-core-audio-taps): individual process playback can be muted through a tap. Whole-session coverage, permissions, process birth/race handling and cleanup remain unimplemented/unverified here.

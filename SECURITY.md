# Security model and reporting

QuietWing separates display, native input, normal audio routing, and owned
process lifetime from the human desktop. Identity, PID birth, ownership, and
generation checks prevent accidental retargeting. They do not make an untrusted
agent safe to run arbitrary programs.

Windows/Linux apps retain the host user's filesystem and device permissions.
Custom routing, singleton IPC, explicit audio devices, and resource exhaustion
need separate controls. Mac uses a separate guest account/disk, no audio devices,
and no host home/project folder shared; guest networking uses NAT.

QuietWing exposes no network listener. Existing SSH can carry CLI/MCP traffic;
the Mac bridge uses private local transport. Computer-ctrl's Windows controller
has its separately documented authenticated loopback transport.

Normal commands do not alter host firewall, credentials, RDP ports, Sharing,
accounts, startup, or global permissions. Provisioning is explicit and separate.
Captures/app output can contain sensitive data; keep them private and redact
evidence before sharing.

## Report a vulnerability

Use this repository's GitHub private vulnerability reporting when enabled. If
unavailable, request a private contact in an issue without exploit details or
sensitive material. Never attach credentials, authority cookies, guest identity
files, snapshots, or human-desktop captures.

Reports are assessed against the current development branch. No response-time
SLA or supported-version maintenance matrix is promised for this experimental
project.

# Future work: cross-platform worker pools

Recorded 2026-10-16 at the maintainer's request. This is a research idea, not
implemented functionality or a commitment to build it now.

Explore running several agents concurrently across Mac, Linux and Windows, with
an exclusive lease per isolated desktop and read-only previews from one machine.
Keep QuietWing responsible for verified session lifetime and capture/input. A
separate orchestration companion could own scheduling, queues, machine inventory,
resource budgets and worker account/VM pools. Decide the project boundary before
building a scheduler; avoid adding orchestration to computer-ctrl's tool contract.

Potential backends to evaluate:

- Windows Server Remote Desktop Services: multiple user sessions on one server,
  with a dedicated worker account/session for each lease. The current ParaDesk
  child adapter permits only one active connected child system-wide and would
  need a separate RDS implementation. RDS Session Host deployment and appropriate
  licensing are prerequisites; installing Server alone does not change our adapter.
- Linux: multiple helper-owned private displays, each with separate runtime,
  HOME/XDG, audio and process ownership. Measure capacity and contention.
- Mac: a pool of independently provisioned guests. Measure VM resource costs,
  concurrency and applicable platform/licensing constraints before designing it.

Questions for a later feasibility pass: lease expiry and crash recovery;
per-worker generation/credential ownership; resource quotas; per-session audio
and input isolation; app/game compatibility and GPU sharing; preview selection;
and when a shared OS session is sufficient versus a dedicated VM. Multiple
sessions share one OS and hardware, so do not claim VM-level separation.

Microsoft documents the [system-wide child-session limit](https://learn.microsoft.com/en-us/windows/win32/termserv/child-sessions),
[RDS multi-session architecture](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/overview),
and [session-host licensing](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/rds-license-session-hosts).
This note adds no installation, account/policy changes, RDS backend or pooling implementation.

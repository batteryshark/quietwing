# Desktop Session Helper

An independent local CLI for controlling isolated desktop sessions. Python 3.11+; no Python runtime dependencies. Install with `python -m pip install .`, or build a wheel with `python -m pip wheel --no-deps .`. The `deskhelper` command works without computer-ctrl.

Backends: Windows attaches to an already authenticated ParaDesk child; Linux starts an authenticated private Xvfb desktop and private PulseAudio sink; Apple Silicon macOS resumes an explicitly provisioned macOS VM. Installation alone does not install native prerequisites, create OS accounts, enable Sharing/RDP, or provision a VM.

`deskhelper doctor` reports local prerequisites. `deskhelper describe --id work` returns a versioned descriptor. Use `start` (Linux/macOS), `attach` (Windows), `exec`, `capture`, `input`, and `stop`. Mutating commands accept `--expect-generation TOKEN` to refuse a replaced session before delivery. Successful stop only releases helper-owned resources; Windows retains the authenticated child and macOS saves the guest for resume.

A descriptor reports the current generation and supported capabilities. Unsupported operations fail; there is no host-desktop fallback. Normal CLI calls do not open login prompts. Credentials, VM images/snapshots, build products, and runtime evidence live outside the installed package.

See the source repository's platform READMEs for native prerequisites and setup/recovery instructions. Host builds use native compilers already available on the target. The Mac build entry point is `deskhelper build`; it compiles/signs the VM owner into the user cache without starting it. Mac first-instance provisioning remains an explicit restore/install/guest-account workflow.

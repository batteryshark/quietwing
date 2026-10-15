# External software

QuietWing's original source is MIT licensed. External software retains its own
licenses/terms and is installed separately. The wheel bundles no upstream
binaries, OS images, disks, or credentials.

| Backend | Prerequisites |
| --- | --- |
| Linux | Xvfb/X11, xauth, xdotool, D-Bus, PulseAudio, FFmpeg, Mesa; optional xfwm4. Resolve packages through the distribution. |
| Windows | Windows child-session APIs, .NET Framework compiler, and a separately installed [ParaDesk](https://github.com/sinpoce/ParaDesk) provider. |
| macOS | Apple Virtualization.framework, ScreenCaptureKit, Swift tools, and an explicitly provisioned licensed macOS guest. |

Windows setup records the tested ParaDesk source pin and release hash. Re-review
its private-data launcher and provider behavior before upgrading. Upstream broad
repair/undo actions are not part of QuietWing attach. ParaDesk is not vendored.

There are no Python runtime dependencies. Build/development tools and GitHub
Actions are declared in project files/workflows and excluded from the wheel.

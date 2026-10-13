#!/bin/zsh
set -eu
[[ "$(/usr/sbin/sysctl -n kern.hv_vmm_present)" == "1" ]] || exit 2
[[ "$(/usr/bin/id -u)" -ge 500 ]] || exit 3
bridge_root="/Volumes/My Shared Files"
owned_root="$HOME/Library/Application Support/Deskhelper"
/bin/mkdir -p "$owned_root" "$HOME/Library/LaunchAgents"
/bin/cp "$bridge_root/GuestBridge" "$owned_root/GuestBridge"
/bin/chmod 700 "$owned_root" "$owned_root/GuestBridge"
/usr/bin/plutil -create xml1 "$HOME/Library/LaunchAgents/dev.desktop-session-helper.guest.plist"
/usr/bin/plutil -insert Label -string dev.desktop-session-helper.guest "$HOME/Library/LaunchAgents/dev.desktop-session-helper.guest.plist"
/usr/bin/plutil -insert ProgramArguments -json "[\"$owned_root/GuestBridge\"]" "$HOME/Library/LaunchAgents/dev.desktop-session-helper.guest.plist"
/usr/bin/plutil -insert RunAtLoad -bool YES "$HOME/Library/LaunchAgents/dev.desktop-session-helper.guest.plist"
/bin/launchctl bootstrap "gui/$(/usr/bin/id -u)" "$HOME/Library/LaunchAgents/dev.desktop-session-helper.guest.plist"

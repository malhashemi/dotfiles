#!/usr/bin/env bash
# Power actions for the Quickshell bar. Uses only system binaries.

lock_action()     { pidof hyprlock || hyprlock; }
suspend_action()  { systemctl suspend; }
logout_action()   { hyprctl dispatch exit; }
reboot_action()   { systemctl reboot; }
poweroff_action() { systemctl poweroff; }

# If hyprshutdown is installed, use its confirmation dialog.
if command -v hyprshutdown &>/dev/null; then
    logout_action()   { hyprshutdown; }
    reboot_action()   { hyprshutdown -t 'Restarting...' --post-cmd 'reboot'; }
    poweroff_action() { hyprshutdown -t 'Shutting down...' --post-cmd 'shutdown -P 0'; }
fi

case "$1" in
    -l|--lock)     lock_action ;;
    -s|--suspend)  suspend_action ;;
    -e|--logout)   logout_action ;;
    -r|--reboot)   reboot_action ;;
    -p|--poweroff) poweroff_action ;;
    *) echo "usage: $(basename "$0") -l|-s|-e|-r|-p" >&2; exit 1 ;;
esac

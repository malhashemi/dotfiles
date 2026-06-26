#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
    lock)
        exec hyprlock
        ;;
    exit)
        hyprctl dispatch 'hl.dsp.exit()'
        ;;
    reboot)
        systemctl reboot
        ;;
    shutdown|poweroff)
        systemctl poweroff
        ;;
    suspend)
        systemctl suspend
        ;;
    hibernate)
        systemctl hibernate
        ;;
    *)
        printf 'usage: %s {lock|exit|reboot|shutdown|suspend|hibernate}\n' "$0" >&2
        exit 2
        ;;
esac

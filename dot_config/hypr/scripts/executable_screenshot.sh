#!/usr/bin/env bash
set -euo pipefail

if ! command -v flameshot >/dev/null 2>&1; then
    notify-send "Missing package" "Install flameshot for screenshots" >/dev/null 2>&1 || true
    printf 'flameshot is required for screenshots\n' >&2
    exit 127
fi

exec env XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_TYPE=wayland QT_QPA_PLATFORM=wayland flameshot gui

#!/usr/bin/env bash
set -euo pipefail

if ! command -v flameshot >/dev/null 2>&1; then
    notify-send "Missing package" "Install flameshot for screenshots" >/dev/null 2>&1 || true
    printf 'flameshot is required for screenshots\n' >&2
    exit 127
fi

# Run flameshot with the session's ambient environment — plain `flameshot gui`.
# Do NOT wrap it in `env XDG_CURRENT_DESKTOP=GNOME ...`: flameshot v14's GNOME
# clipboard path keeps the window alive waiting for Mutter to fetch the data
# (which never happens off GNOME), leaving the clipboard empty. The Hyprland
# session already exports native Wayland (XDG_SESSION_TYPE=wayland,
# QT_QPA_PLATFORM=wayland;xcb) and flameshot is built with KF6GuiAddons +
# Qt6WaylandClient, so bare `flameshot gui` captures via the xdg-desktop-portal
# and copies to the Wayland clipboard. (Verified: the GNOME-faked form failed to
# copy; bare `flameshot gui` works.)
exec flameshot gui

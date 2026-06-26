#!/usr/bin/env bash
# Interactive full system update — repo + AUR + flatpak. Run in a terminal (ghostty -e).
DIR="$(dirname "$(readlink -f "$0")")"
[ -f "$DIR/banner-updates.txt" ] && cat "$DIR/banner-updates.txt"

if command -v paru >/dev/null 2>&1; then
    paru
elif command -v yay >/dev/null 2>&1; then
    yay
else
    sudo pacman -Syu
fi

if command -v flatpak >/dev/null 2>&1; then
    printf '\n:: Updating Flatpak packages...\n'
    flatpak update
fi

printf '\nUpdates finished — press any key to close…'
read -rsn1 _

#!/usr/bin/env bash
# Update a single package (run in a terminal). Args: <name> [src: repo|aur|flatpak]
# NOTE: a single repo/AUR update is a "partial upgrade"; usually fine, but a full
# -Syu is the safe path on Arch if it pulls in newer dependencies.
pkg="$1"
src="$2"
if [ -z "$pkg" ]; then
    echo "No package specified."
    read -rsn1 _
    exit 1
fi

DIR="$(dirname "$(readlink -f "$0")")"
[ -f "$DIR/banner-update.txt" ] && cat "$DIR/banner-update.txt"
printf '   %s  (%s)\n\n' "$pkg" "${src:-repo}"

if [ "$src" = "flatpak" ]; then
    flatpak update "$pkg"
elif command -v paru >/dev/null 2>&1; then
    paru -S "$pkg"
elif command -v yay >/dev/null 2>&1; then
    yay -S "$pkg"
else
    sudo pacman -S "$pkg"
fi

printf '\nDone — press any key to close…'
read -rsn1 _

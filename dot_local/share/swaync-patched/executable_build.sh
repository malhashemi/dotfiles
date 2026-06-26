#!/usr/bin/env bash
# Build & install the locally-patched swaync (renders entity-encoded markup +
# <br> from clients like WhatsApp as bold/newlines instead of literal text).
#
# Safe to re-run anytime -- e.g. after an official swaync upgrade reverts the
# patch. Needs sudo for pacman (base-devel + makedepends + installing the pkg).
set -euo pipefail

dir="${HOME}/.local/share/swaync-patched"

# makepkg itself needs base-devel; makepkg -s pulls vala/sassc/blueprint-compiler.
echo ">> Ensuring base-devel is present..."
sudo pacman -S --needed --noconfirm base-devel

build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
cp "$dir/PKGBUILD" "$dir/swaync-br.patch" "$build/"

echo ">> Building patched swaync (downloads source, applies patch, compiles)..."
(cd "$build" && makepkg -si --noconfirm)

# swaync is started by Hyprland autostart (not systemd) -- restart it.
echo ">> Restarting swaync..."
pkill -x swaync 2>/dev/null || true
sleep 1
setsid swaync >/dev/null 2>&1 </dev/null &

echo ">> Done. Installed: $(pacman -Q swaync 2>/dev/null)"

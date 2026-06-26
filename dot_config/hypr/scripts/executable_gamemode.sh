#!/usr/bin/env bash
set -euo pipefail

flag="$HOME/.cache/gamemode"

if [[ -f "$flag" ]]; then
    rm -f "$flag"
    hyprctl reload
else
    mkdir -p "$(dirname "$flag")"
    touch "$flag"
    hyprctl eval "activate_gamemode()"
fi

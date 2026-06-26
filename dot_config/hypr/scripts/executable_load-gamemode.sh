#!/usr/bin/env bash
set -euo pipefail

if [[ -f "$HOME/.cache/gamemode" ]]; then
    hyprctl eval "activate_gamemode()"
fi

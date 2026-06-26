#!/usr/bin/env bash
# Full focused-window title (display elides; tooltip shows all)
hyprctl activewindow -j 2>/dev/null | jq -r '.title // .class // ""' 2>/dev/null

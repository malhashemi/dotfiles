#!/usr/bin/env bash
# Toggle Hyprland animations on/off (new Lua-parser compatible)
# Reads the live state via getoption (stateless, no cache file) and
# flips it with `hyprctl eval` since `hyprctl keyword` no longer works
# under the Lua config parser.
if [ "$(hyprctl getoption animations:enabled -j | grep -o '"bool": *true')" ]; then
    hyprctl eval 'hl.config({ animations = { enabled = false } })'
else
    hyprctl eval 'hl.config({ animations = { enabled = true } })'
fi

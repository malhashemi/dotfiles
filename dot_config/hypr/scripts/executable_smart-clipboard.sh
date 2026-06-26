#!/usr/bin/env bash
# Mac-style system-wide editing chords (ALT+{C,X,V,A,Z} and ALT+SHIFT+Z).
#
# Hyprland binds these globally and routes them here. Because the chords mean
# different things in a terminal, we translate per focused window:
#   - GUI apps  -> send the Ctrl-based equivalent
#                  (Ctrl+C/X/V copy/cut/paste, Ctrl+A select-all, Ctrl+Z undo,
#                  Ctrl+Shift+Z redo).
#   - Terminals -> copy/paste re-send the original ALT chord so the terminal's
#                  own keybind handles them (Ghostty maps alt+c/alt+v). The rest
#                  are NO-OPS on purpose: in a terminal Ctrl+C = SIGINT,
#                  Ctrl+A = start-of-line, Ctrl+Z = suspend (SIGTSTP), and
#                  select-all/undo/redo have no meaning -- so we must not forward
#                  Ctrl+* there.
#
# Delivery uses Hyprland's send_shortcut dispatcher via the Lua API
# (hl.dsp.send_shortcut). It sends the keys straight to the client (bypassing
# keybind matching, so there's no recursion) and is given an explicit target
# window ("activewindow") to avoid the stuck-modifier bug (hyprwm/Hyprland#14099).
set -euo pipefail

action="${1:-}"

# Send <mods>+<key> to the focused window via Hyprland's Lua dispatcher.
# <mods> may be space-separated, e.g. "CTRL SHIFT".
send() {
    hyprctl dispatch "hl.dsp.send_shortcut({mods=\"$1\",key=\"$2\",window=\"activewindow\"})" >/dev/null
}

# Window classes that are terminal emulators (they handle editing chords themselves).
is_terminal() {
    case "$1" in
    com.mitchellh.ghostty | *[Kk]itty | *[Aa]lacritty | *[Ff]oot* | org.wezfurlong.wezterm) return 0 ;;
    *) return 1 ;;
    esac
}

class="$(hyprctl activewindow -j 2>/dev/null | jq -r '.class // empty' 2>/dev/null || true)"
[ -z "$class" ] && exit 0

if is_terminal "$class"; then
    case "$action" in
    copy) send ALT c ;;
    paste) send ALT v ;;
    cut | selectall | undo | redo) : ;; # no-op in terminals (see header)
    esac
else
    case "$action" in
    copy) send CTRL c ;;
    cut) send CTRL x ;;
    paste) send CTRL v ;;
    selectall) send CTRL a ;;
    undo) send CTRL z ;;
    redo) send "CTRL SHIFT" z ;;
    esac
fi

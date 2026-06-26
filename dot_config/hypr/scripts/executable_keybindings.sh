#!/usr/bin/env bash
set -euo pipefail

format_binds() {
    hyprctl binds -j | jq -r '.[] | select(.description != null and .description != "") | [.modmask, (.key // .keycode // ""), .description] | @tsv' |
        while IFS=$'\t' read -r modmask key description; do
            local mods=()
            local combo=""
            key="${key^^}"

            ((modmask & 8)) && mods+=("ALT")
            ((modmask & 64)) && mods+=("SUPER")
            ((modmask & 4)) && mods+=("CTRL")
            ((modmask & 1)) && mods+=("SHIFT")

            for mod in "${mods[@]}"; do
                if [[ -n "$combo" ]]; then
                    combo+=" + "
                fi
                combo+="$mod"
            done

            if [[ -n "$combo" && -n "$key" ]]; then
                combo+=" + $key"
            elif [[ -n "$key" ]]; then
                combo="$key"
            fi

            printf '%-32s %s\n' "$combo" "$description"
        done
}

format_binds | walker --dmenu --placeholder "Keybindings" >/dev/null

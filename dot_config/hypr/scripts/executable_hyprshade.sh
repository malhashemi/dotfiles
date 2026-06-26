#!/usr/bin/env bash
set -euo pipefail

state_file="$HOME/.cache/hyprshade-filter"

select_filter() {
    local options choice
    options="$(hyprshade ls | sed 's/^[ *]*//')"
    choice="$(printf '%s\noff\n' "$options" | walker --dmenu --placeholder "Hyprshade")"
    [[ -n "$choice" ]] || exit 0
    printf '%s\n' "$choice" > "$state_file"
}

toggle_filter() {
    local filter
    filter="$(cat "$state_file" 2>/dev/null || printf 'blue-light-filter-50')"

    if [[ "$filter" == "off" ]]; then
        hyprshade off
        exit 0
    fi

    if [[ -n "$(hyprshade current)" ]]; then
        hyprshade off
    else
        hyprshade on "$filter"
    fi
}

case "${1:-toggle}" in
    select)
        select_filter
        ;;
    toggle)
        toggle_filter
        ;;
    off)
        hyprshade off
        ;;
    *)
        printf 'usage: %s [select|toggle|off]\n' "$0" >&2
        exit 2
        ;;
esac

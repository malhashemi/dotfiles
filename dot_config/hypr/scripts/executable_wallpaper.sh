#!/usr/bin/env bash
set -euo pipefail

manager="$HOME/.config/theme-system/scripts/wallpaper-manager.py"
cache_dir="$HOME/.cache/hyprland"
automation_flag="$cache_dir/wallpaper-automation"
automation_pid="$cache_dir/wallpaper-automation.pid"
automation_interval="${WALLPAPER_AUTOMATION_INTERVAL:-300}"

notify() {
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -a "wallpaper" "$1" "${2:-}" >/dev/null 2>&1 || true
    fi
}

require_manager() {
    if [[ ! -x "$manager" ]]; then
        printf 'theme-system wallpaper manager is not applied yet: %s\n' "$manager" >&2
        return 1
    fi
}

toggle_automation() {
    require_manager
    mkdir -p "$cache_dir"

    if [[ -f "$automation_flag" ]]; then
        if [[ -s "$automation_pid" ]]; then
            kill "$(cat "$automation_pid")" >/dev/null 2>&1 || true
        fi
        rm -f "$automation_flag" "$automation_pid"
        notify "Wallpaper automation stopped"
        return 0
    fi

    touch "$automation_flag"
    (
        while [[ -f "$automation_flag" ]]; do
            "$manager" random || true
            sleep "$automation_interval"
        done
    ) >/dev/null 2>&1 &
    printf '%s\n' "$!" > "$automation_pid"
    notify "Wallpaper automation started" "Changing every ${automation_interval}s"
}

case "${1:-random}" in
    random|--random)
        require_manager
        "$manager" random
        ;;
    automation|--automation)
        toggle_automation
        ;;
    restore|--restore)
        awww restore
        ;;
    set|--set)
        shift
        require_manager
        "$manager" set "$@"
        ;;
    *)
        require_manager
        "$manager" set "$1"
        ;;
esac

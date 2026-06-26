#!/usr/bin/env bash
set -euo pipefail

config="$HOME/.config/gtk-3.0/settings.ini"
if [[ ! -f "$config" ]]; then
    exit 0
fi

setting() {
    local key="$1"
    grep "^$key" "$config" | sed 's/.*= *//' | tail -n 1 || true
}

gnome_schema="org.gnome.desktop.interface"
gtk_theme="$(setting gtk-theme-name)"
icon_theme="$(setting gtk-icon-theme-name)"
cursor_theme="$(setting gtk-cursor-theme-name)"
cursor_size="$(setting gtk-cursor-theme-size)"
font_name="$(setting gtk-font-name)"
prefer_dark_theme="$(setting gtk-application-prefer-dark-theme)"

if [[ "$prefer_dark_theme" == "0" || "$prefer_dark_theme" == "false" ]]; then
    prefer_dark_theme_value="prefer-light"
else
    prefer_dark_theme_value="prefer-dark"
fi

[[ -n "$gtk_theme" ]] && gsettings set "$gnome_schema" gtk-theme "$gtk_theme"
[[ -n "$icon_theme" ]] && gsettings set "$gnome_schema" icon-theme "$icon_theme"
[[ -n "$cursor_theme" ]] && gsettings set "$gnome_schema" cursor-theme "$cursor_theme"
[[ -n "$font_name" ]] && gsettings set "$gnome_schema" font-name "$font_name"
gsettings set "$gnome_schema" color-scheme "$prefer_dark_theme_value"

if [[ -n "$cursor_theme" && -n "$cursor_size" ]]; then
    hyprctl setcursor "$cursor_theme" "$cursor_size"
fi

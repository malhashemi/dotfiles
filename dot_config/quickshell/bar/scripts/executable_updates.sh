#!/usr/bin/env bash
# Pending system updates for the Quickshell bar.
#   (no arg) -> "<total>|<repo> official · <aur> AUR · <flat> flatpak"  (badge count)
#   list     -> one line per package: "<name> <oldver> <newver> <repo|aur|flatpak>"
# Sources: checkupdates (official, no root) + AUR helper (paru/yay) + flatpak.
mode="${1:-count}"

repo_list=""
aur_list=""
flat_list=""
command -v checkupdates >/dev/null 2>&1 && repo_list=$(checkupdates 2>/dev/null)
for h in paru yay; do
    if command -v "$h" >/dev/null 2>&1; then
        aur_list=$("$h" -Qua 2>/dev/null)
        break
    fi
done
command -v flatpak >/dev/null 2>&1 && flat_list=$(flatpak remote-ls --updates --columns=application,version 2>/dev/null)

if [ "$mode" = "list" ]; then
    # checkupdates / -Qua line format: "name oldver -> newver"
    [ -n "$repo_list" ] && awk '{print $1, $2, $4, "repo"}' <<<"$repo_list"
    [ -n "$aur_list" ]  && awk '{print $1, $2, $4, "aur"}'  <<<"$aur_list"
    # flatpak remote-ls --updates: "app-id  version" (installed ver unknown -> "-")
    [ -n "$flat_list" ] && awk '{print $1, "-", ($2 == "" ? "-" : $2), "flatpak"}' <<<"$flat_list"
else
    repo=0; aur=0; flat=0
    [ -n "$repo_list" ] && repo=$(wc -l <<<"$repo_list")
    [ -n "$aur_list" ]  && aur=$(wc -l <<<"$aur_list")
    [ -n "$flat_list" ] && flat=$(wc -l <<<"$flat_list")
    printf '%s|%s official · %s AUR · %s flatpak\n' "$((repo + aur + flat))" "$repo" "$aur" "$flat"
fi

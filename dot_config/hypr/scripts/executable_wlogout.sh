#!/usr/bin/env bash
set -euo pipefail

read -r res_h scale < <(hyprctl -j monitors | jq -r '.[] | select(.focused == true) | "\(.height) \(.scale)"')

scale_int="${scale/./}"
if [[ -z "$res_h" || -z "$scale_int" || "$scale_int" == "0" ]]; then
    exec wlogout -b 5
fi

margin=$((res_h * 27 / scale_int))
exec wlogout -b 5 -T "$margin" -B "$margin"

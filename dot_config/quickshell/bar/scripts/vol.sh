#!/usr/bin/env bash
# "value|tooltip" — bar: volume %; tooltip: active device + level
v=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null) || { printf -- '--|No audio sink\n'; exit 0; }
name=$(wpctl inspect @DEFAULT_AUDIO_SINK@ 2>/dev/null | sed -n 's/.*node.description = "\(.*\)"/\1/p' | head -1)
if [[ $v == *MUTED* ]]; then
  # empty value → bar shows only the muted glyph (icon swap handled in QML)
  printf '|%s\nMuted\n' "${name:-Audio}"
else
  pct=$(awk '{printf "%.0f", $2*100}' <<<"$v")
  printf '%s%%|%s\nVolume  %s%%\n' "$pct" "${name:-Audio}" "$pct"
fi

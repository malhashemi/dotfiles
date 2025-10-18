#!/bin/sh

# Date widget - displays date in numeric format (e.g., 17/10)

sketchybar --set "$NAME" label="$(date '+%d/%m')"

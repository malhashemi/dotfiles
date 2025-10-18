#!/usr/bin/env bash

# Workspace indicator plugin for AeroSpace integration
# Shows pill background for active workspace
# Hides workspace 10 unless it's active

# Source theme colors
source "$CONFIG_DIR/colors-sketchybar.sh"

# $NAME is provided by sketchybar, $1 is the workspace ID passed from the script parameter
# $FOCUSED_WORKSPACE comes from the aerospace trigger

if [ "$1" = "$FOCUSED_WORKSPACE" ]; then
    # Active workspace: Show pill background with accent color and make visible
    sketchybar --set space.$1 \
               drawing=on \
               background.drawing=on \
               background.color="$ACCENT_COLOR" \
               label.color="$BACKGROUND"
else
    # Inactive workspace: Hide background, use accent color for text
    # Hide workspace 10 when not active
    if [ "$1" = "10" ]; then
        sketchybar --set space.$1 drawing=off
    else
        sketchybar --set space.$1 \
                   drawing=on \
                   background.drawing=off \
                   label.color="$ACCENT_COLOR"
    fi
fi

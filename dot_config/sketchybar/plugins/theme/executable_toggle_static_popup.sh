#!/bin/bash

# Set CONFIG_DIR if not already set
CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"

# Source theme colors for hover feedback
source "$CONFIG_DIR/colors-sketchybar.sh"

# Handle hover feedback
if [[ "$SENDER" == "mouse.entered" ]]; then
  sketchybar --set "$NAME" label.color="$ACCENT_COLOR"
  exit 0
elif [[ "$SENDER" == "mouse.exited" ]]; then
  sketchybar --set "$NAME" label.color="$LABEL_COLOR"
  exit 0
fi

# Only execute on mouse click
if [[ "$SENDER" == "mouse.clicked" ]]; then
  sketchybar --set theme.static popup.drawing=toggle
fi

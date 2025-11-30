#!/bin/bash

# Push theme to devbox via theme system

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
  # Show pushing indicator
  sketchybar --set "$NAME" label="Pushing..."
  
  # Run theme push
  if ~/.config/theme-system/scripts/theme-manager.py push >/dev/null 2>&1; then
    sketchybar --set "$NAME" label="✓ Pushed!"
    sleep 1
    sketchybar --set "$NAME" label="Push to Devbox"
  else
    sketchybar --set "$NAME" label="✗ Failed"
    sleep 1
    sketchybar --set "$NAME" label="Push to Devbox"
  fi
  
  # Close popup after action
  sketchybar --set theme_control popup.drawing=off
fi

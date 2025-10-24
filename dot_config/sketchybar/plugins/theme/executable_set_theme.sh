#!/bin/bash

# Ensure Homebrew and Cargo binaries are in PATH (SketchyBar runs in minimal environment)
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

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

# Arguments: $1 = theme type (dynamic/static), $2 = variant (mocha/latte/frappe/macchiato)
THEME_TYPE="$1"
VARIANT="$2"

# Only execute on mouse click
if [[ "$SENDER" != "mouse.clicked" ]]; then
  exit 0
fi

# Path to theme-manager.py
THEME_MANAGER="$HOME/.config/theme-system/scripts/theme-manager.py"

# Close all popups first
sketchybar --set theme_control popup.drawing=off
sketchybar --set theme.static popup.drawing=off

# Build command
if [[ "$THEME_TYPE" == "dynamic" ]]; then
  # Set dynamic theme (preserves current opacity and contrast)
  "$THEME_MANAGER" set dynamic
  
elif [[ "$THEME_TYPE" == "static" && -n "$VARIANT" ]]; then
  # Set static theme with variant (preserves current opacity)
  "$THEME_MANAGER" set static --variant "$VARIANT"
  
else
  echo "Invalid theme type or variant"
  exit 1
fi

# Trigger theme_changed event to update all subscribed widgets
sketchybar --trigger theme_changed

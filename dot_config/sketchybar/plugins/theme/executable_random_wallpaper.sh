#!/bin/bash

# Ensure Homebrew and Cargo binaries are in PATH (SketchyBar runs in minimal environment)
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

# Set CONFIG_DIR if not already set (fallback for manual testing)
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
if [[ "$SENDER" != "mouse.clicked" ]]; then
  exit 0
fi

# Path to wallpaper-manager.py
WALLPAPER_MANAGER="$HOME/.config/theme-system/scripts/wallpaper-manager.py"

# Visual feedback: Change icon color to green
sketchybar --set theme.wallpaper icon.color=0xff00ff00

# Execute wallpaper random command
"$WALLPAPER_MANAGER" random

# Check if dynamic theme is active
THEME_YAML="$HOME/.local/share/chezmoi/.chezmoidata/theme.yaml"
THEME_NAME=$(grep '^\s*name:' "$THEME_YAML" | awk '{print $2}' | tr -d '"' | tr -d "'")

# If dynamic theme, trigger event (theme colors changed)
if [[ "$THEME_NAME" == "dynamic" ]]; then
  sketchybar --trigger theme_changed
fi

# Restore icon color after 0.5 seconds
sleep 0.5
sketchybar --set theme.wallpaper icon.color="$ACCENT_COLOR"

#!/bin/bash

# Ensure Homebrew and Cargo binaries are in PATH (SketchyBar runs in minimal environment)
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

# Set CONFIG_DIR if not already set
CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"

# Source theme colors for hover feedback
source "$CONFIG_DIR/colors-sketchybar.sh"

# Path to theme-manager.py and theme.yaml
THEME_MANAGER="$HOME/.config/theme-system/scripts/theme-manager.py"
THEME_YAML="$HOME/.local/share/chezmoi/.chezmoidata/theme.yaml"

case "$SENDER" in
  "mouse.entered")
    # Hover feedback: label becomes accent color
    sketchybar --set "$NAME" label.color="$ACCENT_COLOR"
    ;;
    
  "mouse.exited")
    # Restore normal label color
    sketchybar --set "$NAME" label.color="$LABEL_COLOR"
    ;;
  
  "mouse.clicked")
    # Read current variant
    CURRENT_VARIANT=$(grep '^\s*variant:' "$THEME_YAML" | awk '{print $2}' | tr -d '"' | tr -d "'")
    
    # Default to dark if not found
    CURRENT_VARIANT=${CURRENT_VARIANT:-"dark"}
    
    # Toggle mode
    if [[ "$CURRENT_VARIANT" == "dark" ]]; then
      NEW_MODE="light"
    else
      NEW_MODE="dark"
    fi
    
    # Execute theme mode command
    "$THEME_MANAGER" mode "$NEW_MODE"
    
    # Trigger theme_changed event
    sketchybar --trigger theme_changed
    ;;
    
  "theme_changed")
    # Update icon and label based on current mode
    source "$CONFIG_DIR/colors-sketchybar.sh"
    VARIANT=$(grep '^\s*variant:' "$THEME_YAML" | awk '{print $2}' | tr -d '"' | tr -d "'")
    VARIANT=${VARIANT:-"dark"}
    
    if [[ "$VARIANT" == "dark" ]]; then
      MODE_ICON="󰖔"
      MODE_LABEL="Dark"
    else
      MODE_ICON="󰖨"
      MODE_LABEL="Light"
    fi
    
    sketchybar --set theme.mode icon="$MODE_ICON" label="$MODE_LABEL"
    ;;
esac

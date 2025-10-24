#!/bin/bash

# Set CONFIG_DIR if not already set (fallback for manual testing)
CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"

# Source theme colors
source "$CONFIG_DIR/colors-sketchybar.sh"

# Paths
THEME_YAML="$HOME/.local/share/chezmoi/.chezmoidata/theme.yaml"

# Read current theme state
THEME_NAME=$(grep '^\s*name:' "$THEME_YAML" | awk '{print $2}' | tr -d '"' | tr -d "'")
VARIANT=$(grep '^\s*variant:' "$THEME_YAML" | awk '{print $2}' | tr -d '"' | tr -d "'")
OPACITY=$(grep '^\s*opacity:' "$THEME_YAML" | awk '{print $2}')
CONTRAST=$(grep '^\s*contrast:' "$THEME_YAML" | awk '{print $2}')

# Default values if not found
THEME_NAME=${THEME_NAME:-"mocha"}
VARIANT=${VARIANT:-"dark"}
OPACITY=${OPACITY:-0}
CONTRAST=${CONTRAST:-0.0}

# Determine parent item display
if [[ "$THEME_NAME" == "dynamic" ]]; then
  PARENT_ICON="󰸘"
  PARENT_LABEL="Dynamic"
else
  PARENT_ICON="󰏘"
  # Capitalize first letter
  PARENT_LABEL="$(echo "$THEME_NAME" | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}')"
fi

# Update parent item
sketchybar --set theme_control \
  icon="$PARENT_ICON" \
  label="$PARENT_LABEL"

# Update mode toggle icon and label
if [[ "$VARIANT" == "dark" ]]; then
  MODE_ICON="󰖔"  # nf-md-weather_night
  MODE_LABEL="Dark"
else
  MODE_ICON="󰖨"  # nf-md-weather_sunny
  MODE_LABEL="Light"
fi

sketchybar --set theme.mode \
  icon="$MODE_ICON" \
  label="$MODE_LABEL"

# Update opacity slider and label
sketchybar --set theme.opacity.label \
  label="Opacity: ${OPACITY}%"

sketchybar --set theme.opacity \
  slider.percentage="$OPACITY"

# Update contrast slider and visibility
if [[ "$THEME_NAME" == "dynamic" ]]; then
  # Convert contrast from -1.0-1.0 to 0-100 for slider
  CONTRAST_PERCENT=$(echo "($CONTRAST + 1.0) * 50" | bc | awk '{print int($1)}')
  
  sketchybar --set theme.contrast.label \
    drawing=on \
    label="Contrast: ${CONTRAST_PERCENT}%"
  
  sketchybar --set theme.contrast \
    drawing=on \
    slider.percentage="$CONTRAST_PERCENT"
else
  # Hide contrast slider and label for static themes
  sketchybar --set theme.contrast.label drawing=off
  sketchybar --set theme.contrast drawing=off
fi

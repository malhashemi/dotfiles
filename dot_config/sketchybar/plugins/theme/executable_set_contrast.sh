#!/bin/bash

# Ensure Homebrew and Cargo binaries are in PATH (SketchyBar runs in minimal environment)
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

# Check if invoked by mouse click (slider drag/click)
if [[ "$SENDER" == "mouse.clicked" ]]; then
  # $PERCENTAGE is provided by SketchyBar (0-100)
  # Convert to -1.0 to 1.0 range for theme-manager.py
  CONTRAST=$(echo "scale=2; ($PERCENTAGE / 50) - 1.0" | bc)
  
  # Path to theme-manager.py
  THEME_MANAGER="$HOME/.config/theme-system/scripts/theme-manager.py"
  
  # Update dynamic theme with new contrast
  "$THEME_MANAGER" set dynamic -c "$CONTRAST"
  
  # Update slider and label immediately
  sketchybar --set theme.contrast.label \
    label="Contrast: ${PERCENTAGE}%"
  
  sketchybar --set theme.contrast \
    slider.percentage="$PERCENTAGE"
  
  # Trigger theme_changed event
  sketchybar --trigger theme_changed
fi

#!/bin/bash

# Ensure Homebrew and Cargo binaries are in PATH (SketchyBar runs in minimal environment)
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

# Check if invoked by mouse click (slider drag/click)
if [[ "$SENDER" == "mouse.clicked" ]]; then
  # $PERCENTAGE is provided by SketchyBar (0-100)
  NEW_OPACITY="$PERCENTAGE"
  
  # Path to theme-manager.py
  THEME_MANAGER="$HOME/.config/theme-system/scripts/theme-manager.py"
  
  # Update opacity (preserves current theme)
  "$THEME_MANAGER" opacity "$NEW_OPACITY"
  
  # Update slider and label immediately
  sketchybar --set theme.opacity.label \
    label="Opacity: ${NEW_OPACITY}%"
  
  sketchybar --set theme.opacity \
    slider.percentage="$NEW_OPACITY"
  
  # Trigger theme_changed event
  sketchybar --trigger theme_changed
fi

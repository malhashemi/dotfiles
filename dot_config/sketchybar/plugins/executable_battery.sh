#!/bin/sh

PERCENTAGE="$(pmset -g batt | grep -Eo "\d+%" | cut -d% -f1)"
CHARGING="$(pmset -g batt | grep 'AC Power')"

if [ "$PERCENTAGE" = "" ]; then
  exit 0
fi

# Using Nerd Font Material Design Icons (compatible with JetBrains Mono Nerd Font)
case "${PERCENTAGE}" in
  9[0-9]|100) ICON="󰁹"  # nf-md-battery (full)
  ;;
  [6-8][0-9]) ICON="󰂀"  # nf-md-battery_80
  ;;
  [3-5][0-9]) ICON="󰁾"  # nf-md-battery_50
  ;;
  [1-2][0-9]) ICON="󰁼"  # nf-md-battery_30
  ;;
  *) ICON="󰁺"  # nf-md-battery_10 (low)
esac

if [[ "$CHARGING" != "" ]]; then
  ICON="󰂄"  # nf-md-battery_charging (charging icon)
fi

# The item invoking this script (name $NAME) will get its icon and label
# updated with the current battery status
sketchybar --set "$NAME" icon="$ICON" label="${PERCENTAGE}%"

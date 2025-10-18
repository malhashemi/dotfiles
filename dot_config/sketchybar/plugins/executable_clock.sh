#!/bin/sh

# Clock widget - displays time only in HH:MM format

sketchybar --set "$NAME" label="$(date '+%H:%M')"


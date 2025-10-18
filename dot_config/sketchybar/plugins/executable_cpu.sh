#!/bin/sh

# CPU widget - displays CPU usage percentage (normalized to 0-100%)

# Get number of CPU cores
CORE_COUNT=$(sysctl -n hw.ncpu)

# Sum all process CPU usage
CPU_TOTAL=$(ps -A -o %cpu | awk '{s+=$1} END {print s}')

# Normalize to 0-100% by dividing by core count
CPU_PERCENT=$(echo "$CPU_TOTAL $CORE_COUNT" | awk '{printf "%.0f", $1/$2}')

sketchybar --set "$NAME" label="${CPU_PERCENT}%"

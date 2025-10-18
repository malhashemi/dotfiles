#!/bin/sh

# RAM widget - displays memory usage in GB

# Get memory stats using vm_stat
PAGES_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
PAGES_ACTIVE=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
PAGES_INACTIVE=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
PAGES_WIRED=$(vm_stat | grep "Pages wired down" | awk '{print $4}' | sed 's/\.//')

# Each page is 4096 bytes, calculate used memory in GB
USED_MEM=$(echo "scale=1; ($PAGES_ACTIVE + $PAGES_INACTIVE + $PAGES_WIRED) * 4096 / 1024 / 1024 / 1024" | bc)

sketchybar --set "$NAME" label="${USED_MEM}G"

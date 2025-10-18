#!/bin/sh

# Storage widget - displays free disk space

DISK_FREE=$(df -h / | awk 'NR==2 {print $4}')

sketchybar --set "$NAME" label="$DISK_FREE"

#!/usr/bin/env bash
# Free space on / (e.g. 867G)
df -h / | awk 'NR==2{print $4}'

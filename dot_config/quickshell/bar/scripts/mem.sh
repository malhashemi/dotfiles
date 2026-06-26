#!/usr/bin/env bash
# RAM usage %
read -r _ tot _ < <(grep -m1 MemTotal /proc/meminfo)
read -r _ av _  < <(grep -m1 MemAvailable /proc/meminfo)
printf '%d%%\n' "$(( (tot-av)*100/tot ))"

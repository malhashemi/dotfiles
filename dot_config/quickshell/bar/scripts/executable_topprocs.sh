#!/usr/bin/env bash
# Top processes for the procmon popup.
# Usage: topprocs.sh [cpu|mem]  (default: cpu)
sort="${1:-cpu}"
if [ "$sort" = "mem" ]; then
    ps -eo pid,pcpu,pmem,comm --sort=-pmem,-pcpu --no-headers | head -n 15
else
    ps -eo pid,pcpu,pmem,comm --sort=-pcpu,-pmem --no-headers | head -n 15
fi | while read -r pid cpu mem cmd; do
    printf '%s %s %s %s\n' "$pid" "$cpu" "$mem" "${cmd##*/}"
done

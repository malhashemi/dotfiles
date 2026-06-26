#!/usr/bin/env bash
# "value|tooltip" — bar: Wi-Fi signal %; tooltip: SSID (iface), signal, freq, IP, down/up rates
line=$(nmcli -t -f ACTIVE,SIGNAL,SSID,DEVICE,FREQ device wifi 2>/dev/null | awk -F: '$1=="yes"{print; exit}')
if [ -z "$line" ]; then
  printf 'off|Not connected to Wi-Fi\n'
  exit 0
fi
sig=$(awk -F:  '{print $2}' <<<"$line")
ssid=$(awk -F: '{print $3}' <<<"$line")
dev=$(awk -F:  '{print $4}' <<<"$line")
freq=$(awk -F: '{print $5}' <<<"$line")
ip=$(ip -4 -o addr show dev "$dev" 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)

sdir=/sys/class/net/$dev/statistics
rx1=$(<"$sdir/rx_bytes"); tx1=$(<"$sdir/tx_bytes")
sleep 1
rx2=$(<"$sdir/rx_bytes"); tx2=$(<"$sdir/tx_bytes")
h(){ numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"; }

printf '%s%%|%s  (%s)\nSignal   %s%%\nFreq     %s\nIP       %s\n↓ %s/s   ↑ %s/s\n' \
  "$sig" "${ssid:-Wi-Fi}" "$dev" "$sig" "${freq:-?}" "${ip:-?}" \
  "$(h $((rx2 - rx1)))" "$(h $((tx2 - tx1)))"

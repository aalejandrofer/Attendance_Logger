#!/bin/sh
# Keeps wlan0 usable. Run every minute by wifi-watchdog.timer.
#  - Turns wifi power saving off (a common cause of Pi 4 drop-outs).
#  - If the router has been unreachable for 3 checks in a row, restarts the
#    wifi connection. Never reboots: a reboot while offline would leave the
#    clock (no RTC) on its last saved time.
IFACE=wlan0
STATE=/run/wifi-watchdog.failures

/sbin/iw dev "$IFACE" set power_save off 2>/dev/null

GATEWAY=$(ip route show default dev "$IFACE" 2>/dev/null | awk '{print $3; exit}')
if [ -n "$GATEWAY" ] && ping -c 2 -W 3 "$GATEWAY" >/dev/null 2>&1; then
    rm -f "$STATE"
    exit 0
fi

FAILS=$(( $(cat "$STATE" 2>/dev/null || echo 0) + 1 ))
echo "$FAILS" > "$STATE"
echo "router unreachable (${GATEWAY:-no default route}), failure $FAILS"

if [ "$FAILS" -ge 3 ]; then
    echo "restarting $IFACE"
    /sbin/wpa_cli -i "$IFACE" reconfigure >/dev/null 2>&1
    ip link set "$IFACE" down
    sleep 2
    ip link set "$IFACE" up
    echo 0 > "$STATE"
fi

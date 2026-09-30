# Deployment

The Pi runs `main.py` under systemd as `attl.service`.

## Install / update the service unit

```bash
sudo cp deploy/attl.service /etc/systemd/system/attl.service
sudo systemctl daemon-reload
sudo systemctl enable --now attl.service
```

`/etc/systemd/system/` overrides any vendor copy in `/lib/systemd/system/`.

`Restart=always` means the service self-heals: if `main.py` crashes or exits,
systemd restarts it after `RestartSec`.

## Wifi watchdog

Turns wifi power saving off and restarts the wifi connection if the router has
been unreachable for 3 minutes. It never reboots the Pi.

```bash
sudo cp deploy/wifi-watchdog.service deploy/wifi-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wifi-watchdog.timer
journalctl -u wifi-watchdog.service   # only logs when something is wrong
```

## Deploy code

```bash
cd ~/Attendance_Logger
git pull --ff-only origin master
sudo systemctl restart attl.service
journalctl -u attl.service -f   # expect "Time checker started"
sudo python3 manage_cards.py status
```

The local database is `localstorage/attendance.db` (git-ignored). Back it up
with `sqlite3 localstorage/attendance.db ".backup attendance-backup.db"`.

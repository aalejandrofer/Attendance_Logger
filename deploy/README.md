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

## Deploy code

```bash
cd ~/Attendance_Logger
git pull --ff-only origin master
sudo systemctl restart attl.service
journalctl -u attl.service -f   # expect "Time checker started"
```

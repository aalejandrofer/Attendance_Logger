# Attendance_Logger (Using Clockify)
---
### Project using these products:
- Raspberry Pi 4 Model B 2Gb
- RFID HAT for Raspberry Pi (SB Components)
---
Tap an RFID card to clock in, tap again to clock out. Entries go to
[Clockify](https://api.clockify.me/api/v1).

- **Works offline.** Cards and time entries live in a local SQLite database
  (`localstorage/attendance.db`). Taps never wait on the network; anything
  Clockify hasn't received yet is queued and retried every 5 minutes, however
  long the outage lasts.
- **Optional online copy.** If `SUPABASE_URL`/`SUPABASE_KEY` are set, cards
  and entries are mirrored to Supabase so they can be checked online. The
  regular sync also keeps a free-tier project from pausing.
- **Forgotten tap-outs** are ended at `WORK_END_HOUR` (default 20:00) and
  tagged in Clockify.
- **Restarts are safe.** Local state is reconciled with Clockify, which also
  picks up timers started or stopped from the Clockify app.
- Entries created before the Pi's clock has synced (no RTC; e.g. a reboot
  while offline) are marked `(clock unverified)` in their description.

## Setup
Copy `.env.template` to `.env` and fill it in. See `deploy/README.md` for the
service and wifi watchdog.

## Cards
```bash
sudo python3 manage_cards.py list
sudo python3 manage_cards.py status          # clocked in, queued entries, errors
sudo systemctl stop attl                     # frees the reader for --tap
sudo python3 manage_cards.py add --name "Name" --like <existing-tag> --tap
sudo systemctl start attl
```
On first start with an empty database, cards are imported from Supabase.

## Tests
```bash
python3 -m unittest discover -s tests
```

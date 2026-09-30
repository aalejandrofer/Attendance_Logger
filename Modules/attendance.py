"""Attendance service: what a card tap and the background tick do.

Hardware-free (main.py owns the display and the reader) and network-tolerant:
every state change is written to the local DB first, then pushed. Nothing
here waits on, or fails because of, wifi, Clockify or Supabase.
"""
import json
import logging
import os
import threading
from datetime import datetime

import pytz

from Modules.reconcile import reconcile_sessions

CLOCK_SYNC_MARKER = '/run/systemd/timesync/synchronized'
UNVERIFIED_SUFFIX = ' (clock unverified)'


def _utc_now():
    return datetime.now(pytz.utc)


def _clock_synced():
    # systemd-timesyncd creates this once NTP has set the clock since boot.
    # Before that, the Pi (no RTC) runs on fake-hwclock's last saved time.
    return os.path.exists(CLOCK_SYNC_MARKER)


def _in_background(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def _iso(dt):
    return dt.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _parse(ts):
    # Tolerates Clockify's optional fractional seconds ("...:00.123Z").
    return pytz.utc.localize(datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S'))


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return '%dth' % n
    return '%d%s' % (n, {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


class Attendance:
    def __init__(self, db, syncer, clockify, tz_name, work_end_hour,
                 now=_utc_now, clock_trusted=_clock_synced, background=_in_background):
        self.db = db
        self.syncer = syncer
        self.clockify = clockify
        self.tz = pytz.timezone(tz_name)
        self.work_end_hour = work_end_hour
        self.now = now
        self.clock_trusted = clock_trusted
        self.background = background

    # ---- taps ------------------------------------------------------------

    def describe(self, when):
        t = when.astimezone(self.tz)
        return '%s %s at %s' % (t.strftime('%A'), _ordinal(t.day), t.strftime('%H:%M:%S'))

    def lookup(self, tag_uuid):
        return self.db.get_card(tag_uuid)

    def is_clocked_in(self, tag_uuid):
        return self.db.active_entry_for_tag(tag_uuid) is not None

    def active_count(self):
        return len(self.db.active_entries())

    def tap(self, tag_uuid):
        """Handle one card read. Returns ('in'|'out'|'unknown', name)."""
        card = self.lookup(tag_uuid)
        if not card:
            logging.warning("Unknown card: %r", (tag_uuid or '').strip())
            return 'unknown', None
        active = self.db.active_entry_for_tag(card['tag_uuid'])
        if active:
            self.db.end_entry(active['id'], _iso(self.now()))
            logging.info("Clocked out %s (entry %s)", card['name'], active['id'])
            self.background(self.syncer.push_entry, active['id'])
            return 'out', card['name']
        now = self.now()
        description = self.describe(now)
        if not self.clock_trusted():
            description += UNVERIFIED_SUFFIX
            logging.warning("Clock not NTP-synced; flagging entry for %s", card['name'])
        entry_id = self.db.start_entry(card, _iso(now), description)
        logging.info("Clocked in %s (entry %s)", card['name'], entry_id)
        self.background(self.syncer.push_entry, entry_id)
        return 'in', card['name']

    # ---- background tick -------------------------------------------------

    def end_overtime(self):
        """End sessions that ran past the end hour of the day they started.

        The entry ends exactly at the end hour, not whenever this runs, so a
        session left open over a power cut still gets a sensible end.
        """
        now = self.now()
        ended = 0
        for e in self.db.active_entries():
            start = _parse(e['start_time'])
            start_local = start.astimezone(self.tz)
            cutoff = self.tz.localize(datetime(
                start_local.year, start_local.month, start_local.day, self.work_end_hour))
            if now < cutoff:
                continue
            self.db.end_entry(e['id'], _iso(max(cutoff, start)), status='limit_reached')
            logging.info("Auto-ended %s at %s:00 (forgot to tap out)", e['name'], self.work_end_hour)
            self.background(self.syncer.push_entry, e['id'])
            ended += 1
        return ended

    def reconcile(self):
        """Line local sessions up with Clockify. Returns True if it ran."""
        if self.db.pending_clockify():
            return False  # Clockify can't be compared until the queue is empty
        cards = self.db.all_cards()
        if not cards:
            return False
        in_progress = []
        for ws in {c['workspace_id'] for c in cards}:
            fetched = self.clockify.get_in_progress(ws)
            if fetched is None:
                return False
            in_progress.extend(fetched)

        active = {e['tag_uuid']: e for e in self.db.active_entries()}
        to_add, to_remove = reconcile_sessions(cards, in_progress, active, self.db.known_clockify_ids())

        for tag, (card, e) in to_add.items():
            self.db.start_entry(
                card, e['timeInterval']['start'], e.get('description'),
                billable=e.get('billable', True),
                clockify_entry_id=e['id'], clockify_synced=True,
            )
            logging.info("Recovered running Clockify entry for %s", card['name'])
        for tag in to_remove:
            self.db.end_entry(active[tag]['id'], _iso(self.now()), push=False)
            logging.info("Closed %s locally: Clockify entry no longer running", active[tag]['name'])
        return True

    def tick(self):
        """One background cycle: overtime, push queue, reconcile."""
        if not self.db.all_cards():
            # First boot while offline: keep trying to fetch the card list.
            self.syncer.import_cards()
        self.end_overtime()
        self.syncer.run()
        self.reconcile()

    # ---- migration -------------------------------------------------------

    def import_legacy_state(self, path):
        """One-off import of active sessions from the old state.json."""
        if not os.path.exists(path):
            return 0
        try:
            with open(path) as f:
                sessions = (json.load(f) or {}).get('sessions') or {}
        except Exception as e:
            logging.error("Could not read legacy state %s: %s", path, e)
            sessions = {}
        imported = 0
        for tag, s in sessions.items():
            if self.is_clocked_in(tag):
                continue
            try:
                entry = s.get('entry') or {}
                card = dict(s.get('user_data') or {}, tag_uuid=tag)
                self.db.start_entry(
                    card, entry['start'], entry.get('description'),
                    billable=entry.get('billable', True),
                    clockify_entry_id=entry.get('clockify_entry_id'),
                    clockify_synced=bool(entry.get('clockify_entry_id')),
                )
                imported += 1
            except Exception as e:
                logging.error("Skipping unreadable legacy session for %s: %s", tag, e)
        os.rename(path, path + '.migrated')
        return imported

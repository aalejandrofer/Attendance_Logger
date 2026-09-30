"""Pushes the local queue to Clockify and mirrors it to Supabase.

The tap path calls `push_entry` right away; the background tick calls
`run` to retry anything that failed. A lock keeps the two from pushing the
same entry at once (which would create duplicate Clockify entries).
"""
import logging
import threading

import requests

from Modules.clockify import ClockifyError

CARD_COLUMNS = ('tag_uuid', 'name', 'user_id', 'project_id', 'workspace_id', 'task_id', 'updated_at')


def is_transient(error):
    """True if retrying other entries right now is pointless (network down)."""
    if isinstance(error, requests.RequestException):
        return True
    if isinstance(error, ClockifyError):
        return error.status == 429 or error.status >= 500
    return False


class Syncer:
    def __init__(self, db, clockify, mirror=None, time_limit_tag_id=None):
        self.db = db
        self.clockify = clockify
        self.mirror = mirror
        self.time_limit_tag_id = time_limit_tag_id
        self._lock = threading.Lock()
        self._supabase_ok = True  # log state changes, not every failure

    # ---- Clockify --------------------------------------------------------

    def _body(self, e):
        body = {
            'start': e['start_time'],
            'billable': bool(e['billable']),
            'description': e['description'],
            'projectId': e['project_id'],
            'taskId': e['task_id'],
        }
        if e['end_time']:
            body['end'] = e['end_time']
        if e['status'] == 'limit_reached' and self.time_limit_tag_id:
            body['tagIds'] = [self.time_limit_tag_id]
        return body

    def _push(self, entry_id):
        """Push one entry. Returns None on success, else the exception."""
        e = self.db.get_entry(entry_id)
        if not e or e['clockify_synced']:
            return None
        try:
            if e['clockify_entry_id']:
                result = self.clockify.update_entry(e['workspace_id'], e['clockify_entry_id'], self._body(e))
            else:
                result = self.clockify.create_entry(e['workspace_id'], self._body(e))
        except Exception as err:
            self.db.record_clockify_error(entry_id, err)
            logging.warning("Clockify push failed for %s (entry %s): %s", e['name'], entry_id, err)
            return err
        self.db.set_clockify_result(entry_id, result['id'], e['version'])
        return None

    def push_entry(self, entry_id):
        with self._lock:
            return self._push(entry_id) is None

    def push_clockify(self):
        """Retry every queued entry. Returns how many are still pending."""
        with self._lock:
            for e in self.db.pending_clockify():
                err = self._push(e['id'])
                if err is not None and is_transient(err):
                    break
                if err is None:
                    # The entry may have changed mid-push (tapped out while
                    # the start was in flight); push the new state too.
                    again = self.db.get_entry(e['id'])
                    if again and not again['clockify_synced']:
                        self._push(e['id'])
        return len(self.db.pending_clockify())

    # ---- Supabase --------------------------------------------------------

    def _entry_row(self, e):
        return {
            'clockify_entry_id': e['clockify_entry_id'],
            'project_id': e['project_id'],
            'start_time': e['start_time'],
            'end_time': e['end_time'],
            'description': e['description'],
            'status': e['status'],
            'updated_at': e['updated_at'],
        }

    def push_supabase(self):
        """Mirror unsynced cards and entries. Returns True if Supabase is reachable."""
        if not self.mirror:
            return False
        cards = self.db.unsynced_cards()
        entries = self.db.pending_supabase_entries()
        errors = []

        def attempt(fn):
            try:
                fn()
            except Exception as err:
                errors.append(err)

        def push_cards():
            self.mirror.upsert('projects', [{k: c[k] for k in CARD_COLUMNS} for c in cards], 'tag_uuid')
            for c in cards:
                self.db.mark_card_synced(c['tag_uuid'], c['version'])

        def push_entries():
            self.mirror.upsert('time_entries', [self._entry_row(e) for e in entries], 'clockify_entry_id')
            for e in entries:
                self.db.mark_entry_supabase_synced(e['id'], e['version'])

        # Independent: a rejected card write must not hold back entries.
        if entries:
            attempt(push_entries)
        if cards:
            attempt(push_cards)
        if not cards and not entries:
            attempt(self.mirror.ping)

        if errors:
            if self._supabase_ok:
                logging.warning("Supabase mirror unavailable, will retry: %s", errors[0])
            self._supabase_ok = False
            return False
        if not self._supabase_ok:
            logging.info("Supabase mirror reachable again")
        self._supabase_ok = True
        return True

    def import_cards(self):
        """Copy cards from Supabase into the local DB. Returns how many."""
        if not self.mirror:
            return 0
        try:
            rows = self.mirror.fetch_cards()
        except Exception as err:
            logging.warning("Could not import cards from Supabase: %s", err)
            return 0
        for row in rows:
            self.db.upsert_card(row, synced=True)
        return len(rows)

    def run(self):
        pending = self.push_clockify()
        self.push_supabase()
        return pending

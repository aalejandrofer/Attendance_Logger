"""Unit tests for Syncer (local queue -> Clockify / Supabase).

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import os
import sys
import tempfile
import unittest

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.local_db import LocalDB
from Modules.clockify import ClockifyError
from Modules.sync import Syncer

CARD = {
    'tag_uuid': 'tagA', 'name': 'Alice', 'user_id': 'u1',
    'project_id': 'projA', 'workspace_id': 'ws', 'task_id': 'taskA',
}
LIMIT_TAG = 'limit-tag'


class FakeClockify:
    def __init__(self):
        self.created = []
        self.updated = []
        self.fail = None  # exception to raise on the next calls
        self.on_call = None  # hook run mid-request
        self._n = 0

    def _maybe_fail(self):
        if self.on_call:
            self.on_call()
        if self.fail:
            raise self.fail

    def create_entry(self, workspace_id, body):
        self._maybe_fail()
        self._n += 1
        self.created.append((workspace_id, body))
        return {'id': 'c%d' % self._n}

    def update_entry(self, workspace_id, entry_id, body):
        self._maybe_fail()
        self.updated.append((workspace_id, entry_id, body))
        return {'id': entry_id}


class FakeMirror:
    def __init__(self, cards=None):
        self.upserts = []
        self.pings = 0
        self.fail = None
        self.cards = cards or []

    def upsert(self, table, rows, on_conflict):
        if self.fail:
            raise self.fail
        self.upserts.append((table, rows, on_conflict))

    def fetch_cards(self):
        if self.fail:
            raise self.fail
        return self.cards

    def ping(self):
        if self.fail:
            raise self.fail
        self.pings += 1


class SyncTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = LocalDB(os.path.join(self.dir.name, 'a.db'))
        self.db.upsert_card(CARD)
        self.clockify = FakeClockify()
        self.mirror = FakeMirror()
        self.sync = Syncer(self.db, self.clockify, self.mirror, time_limit_tag_id=LIMIT_TAG)

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()

    def start(self):
        return self.db.start_entry(CARD, '2026-09-30T08:00:00Z', 'Wednesday 30th at 09:00:00')


class ClockifyPushTest(SyncTestCase):
    def test_start_is_created_in_clockify(self):
        eid = self.start()
        self.assertTrue(self.sync.push_entry(eid))
        ws, body = self.clockify.created[0]
        self.assertEqual(ws, 'ws')
        self.assertEqual(body['start'], '2026-09-30T08:00:00Z')
        self.assertEqual(body['projectId'], 'projA')
        self.assertEqual(body['taskId'], 'taskA')
        self.assertTrue(body['billable'])
        self.assertNotIn('end', body)
        self.assertEqual(self.db.get_entry(eid)['clockify_entry_id'], 'c1')
        self.assertEqual(self.db.pending_clockify(), [])

    def test_end_updates_existing_entry(self):
        eid = self.start()
        self.sync.push_entry(eid)
        self.db.end_entry(eid, '2026-09-30T16:00:00Z')
        self.assertTrue(self.sync.push_entry(eid))
        ws, cid, body = self.clockify.updated[0]
        self.assertEqual(cid, 'c1')
        self.assertEqual(body['start'], '2026-09-30T08:00:00Z')
        self.assertEqual(body['end'], '2026-09-30T16:00:00Z')
        self.assertEqual(len(self.clockify.created), 1)

    def test_offline_start_and_end_become_one_complete_entry(self):
        eid = self.start()
        self.clockify.fail = requests.ConnectionError('no wifi')
        self.assertFalse(self.sync.push_entry(eid))
        self.db.end_entry(eid, '2026-09-30T16:00:00Z')
        self.clockify.fail = None
        self.sync.push_clockify()
        self.assertEqual(len(self.clockify.created), 1)
        body = self.clockify.created[0][1]
        self.assertEqual(body['end'], '2026-09-30T16:00:00Z')
        self.assertEqual(self.clockify.updated, [])
        self.assertEqual(self.db.pending_clockify(), [])

    def test_limit_reached_adds_tag(self):
        eid = self.start()
        self.db.end_entry(eid, '2026-09-30T19:00:00Z', status='limit_reached')
        self.sync.push_entry(eid)
        self.assertEqual(self.clockify.created[0][1]['tagIds'], [LIMIT_TAG])

    def test_failure_is_recorded_and_retried(self):
        eid = self.start()
        self.clockify.fail = ClockifyError(400, 'bad request')
        self.sync.push_entry(eid)
        e = self.db.get_entry(eid)
        self.assertEqual(e['attempts'], 1)
        self.assertIn('400', e['last_error'])
        self.clockify.fail = None
        self.sync.push_clockify()
        self.assertEqual(self.db.pending_clockify(), [])

    def test_network_down_stops_after_first_failure(self):
        a = self.start()
        b = self.db.start_entry(dict(CARD, tag_uuid='tagB'), '2026-09-30T08:05:00Z', 'd')
        self.clockify.fail = requests.ConnectionError('no wifi')
        self.sync.push_clockify()
        self.assertEqual(self.db.get_entry(a)['attempts'], 1)
        self.assertEqual(self.db.get_entry(b)['attempts'], 0)

    def test_client_error_does_not_block_other_entries(self):
        a = self.start()
        b = self.db.start_entry(dict(CARD, tag_uuid='tagB'), '2026-09-30T08:05:00Z', 'd')
        calls = {'n': 0}

        def first_call_fails():
            calls['n'] += 1
            self.clockify.fail = ClockifyError(400, 'bad') if calls['n'] == 1 else None

        self.clockify.on_call = first_call_fails
        self.sync.push_clockify()
        self.assertEqual(len(self.db.pending_clockify()), 1)
        self.assertIsNotNone(self.db.get_entry(b)['clockify_entry_id'])

    def test_end_during_start_push_is_not_lost(self):
        eid = self.start()
        # Card tapped out while the start POST is in flight.
        self.clockify.on_call = lambda: self.db.end_entry(eid, '2026-09-30T16:00:00Z')
        self.sync.push_entry(eid)
        self.clockify.on_call = None
        self.assertEqual(len(self.db.pending_clockify()), 1)
        self.sync.push_clockify()
        self.assertEqual(self.clockify.updated[0][2]['end'], '2026-09-30T16:00:00Z')
        self.assertEqual(self.db.pending_clockify(), [])

    def test_already_synced_entry_is_noop(self):
        eid = self.start()
        self.sync.push_entry(eid)
        self.sync.push_entry(eid)
        self.assertEqual(len(self.clockify.created), 1)


class SupabasePushTest(SyncTestCase):
    def test_cards_and_entries_are_mirrored(self):
        eid = self.start()
        self.sync.push_entry(eid)
        self.assertTrue(self.sync.push_supabase())
        tables = {t: (rows, key) for t, rows, key in self.mirror.upserts}
        cards, key = tables['projects']
        self.assertEqual(key, 'tag_uuid')
        self.assertEqual(cards[0]['tag_uuid'], 'tagA')
        self.assertEqual(cards[0]['name'], 'Alice')
        self.assertNotIn('version', cards[0])
        entries, key = tables['time_entries']
        self.assertEqual(key, 'clockify_entry_id')
        self.assertEqual(entries[0]['clockify_entry_id'], 'c1')
        self.assertEqual(entries[0]['project_id'], 'projA')
        self.assertEqual(entries[0]['status'], 'active')
        self.assertEqual(self.db.unsynced_cards(), [])
        self.assertEqual(self.db.pending_supabase_entries(), [])

    def test_entry_without_clockify_id_waits(self):
        self.start()
        self.sync.push_supabase()
        self.assertNotIn('time_entries', [t for t, _, _ in self.mirror.upserts])

    def test_nothing_to_push_still_pings(self):
        # Regular traffic keeps a free-tier project from pausing.
        self.sync.push_supabase()
        self.sync.push_supabase()
        self.assertGreaterEqual(self.mirror.pings, 1)

    def test_supabase_down_keeps_queue(self):
        self.mirror.fail = requests.ConnectionError('paused')
        self.assertFalse(self.sync.push_supabase())
        self.assertEqual(len(self.db.unsynced_cards()), 1)

    def test_card_push_rejected_does_not_block_entries(self):
        # e.g. RLS allows time_entries writes but not projects.
        eid = self.start()
        self.sync.push_entry(eid)
        real_upsert = self.mirror.upsert

        def upsert(table, rows, key):
            if table == 'projects':
                raise RuntimeError('Supabase HTTP 401: row-level security')
            real_upsert(table, rows, key)

        self.mirror.upsert = upsert
        self.assertFalse(self.sync.push_supabase())
        self.assertEqual(self.db.pending_supabase_entries(), [])
        self.assertEqual(len(self.db.unsynced_cards()), 1)

    def test_no_mirror_configured(self):
        sync = Syncer(self.db, self.clockify, None)
        self.assertFalse(sync.push_supabase())
        self.assertEqual(sync.import_cards(), 0)


class ImportCardsTest(SyncTestCase):
    def test_import_cards_marks_synced(self):
        self.mirror.cards = [dict(CARD, tag_uuid='tagZ', name='Zed', id='x')]
        self.assertEqual(self.sync.import_cards(), 1)
        self.assertEqual(self.db.get_card('tagZ')['name'], 'Zed')
        self.assertNotIn('tagZ', [c['tag_uuid'] for c in self.db.unsynced_cards()])

    def test_import_failure_returns_zero(self):
        self.mirror.fail = requests.ConnectionError('down')
        self.assertEqual(self.sync.import_cards(), 0)


if __name__ == '__main__':
    unittest.main()

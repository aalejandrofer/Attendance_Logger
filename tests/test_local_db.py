"""Unit tests for LocalDB (SQLite source of truth).

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.local_db import LocalDB


CARD = {
    'tag_uuid': 'tagA', 'name': 'Alice', 'user_id': 'u1',
    'project_id': 'projA', 'workspace_id': 'ws', 'task_id': 'taskA',
}


class LocalDBTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = LocalDB(os.path.join(self.dir.name, 'attendance.db'))

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()


class CardsTest(LocalDBTestCase):
    def test_missing_card_is_none(self):
        self.assertIsNone(self.db.get_card('nope'))

    def test_upsert_and_get(self):
        self.db.upsert_card(CARD)
        card = self.db.get_card('tagA')
        self.assertEqual(card['name'], 'Alice')
        self.assertEqual(card['project_id'], 'projA')

    def test_upsert_replaces(self):
        self.db.upsert_card(CARD)
        self.db.upsert_card(dict(CARD, name='Alice B'))
        self.assertEqual(len(self.db.all_cards()), 1)
        self.assertEqual(self.db.get_card('tagA')['name'], 'Alice B')

    def test_tag_is_trimmed(self):
        # Serial reads can carry stray whitespace/newlines.
        self.db.upsert_card(dict(CARD, tag_uuid=' tagA\n'))
        self.assertIsNotNone(self.db.get_card('tagA'))
        self.assertIsNotNone(self.db.get_card('tagA\r\n'))

    def test_remove(self):
        self.db.upsert_card(CARD)
        self.assertTrue(self.db.remove_card('tagA'))
        self.assertFalse(self.db.remove_card('tagA'))
        self.assertIsNone(self.db.get_card('tagA'))

    def test_new_card_needs_supabase_sync(self):
        self.db.upsert_card(CARD)
        self.assertEqual([c['tag_uuid'] for c in self.db.unsynced_cards()], ['tagA'])

    def test_imported_card_is_already_synced(self):
        self.db.upsert_card(CARD, synced=True)
        self.assertEqual(self.db.unsynced_cards(), [])

    def test_mark_card_synced_ignores_stale_version(self):
        self.db.upsert_card(CARD)
        seen = self.db.unsynced_cards()[0]
        self.db.upsert_card(dict(CARD, name='Changed'))  # edit during push
        self.db.mark_card_synced('tagA', seen['version'])
        self.assertEqual(len(self.db.unsynced_cards()), 1)


class EntriesTest(LocalDBTestCase):
    def setUp(self):
        super().setUp()
        self.db.upsert_card(CARD)

    def start(self, **kw):
        return self.db.start_entry(CARD, '2026-09-30T08:00:00Z', 'desc', **kw)

    def test_start_creates_active_pending_entry(self):
        eid = self.start()
        e = self.db.get_entry(eid)
        self.assertEqual(e['status'], 'active')
        self.assertIsNone(e['clockify_entry_id'])
        self.assertEqual(e['clockify_synced'], 0)
        self.assertEqual(self.db.active_entry_for_tag('tagA')['id'], eid)
        self.assertEqual([p['id'] for p in self.db.pending_clockify()], [eid])

    def test_start_with_known_clockify_entry_is_synced(self):
        eid = self.start(clockify_entry_id='c1', clockify_synced=True)
        self.assertEqual(self.db.pending_clockify(), [])
        self.assertEqual(self.db.known_clockify_ids(), {'c1'})
        self.assertEqual(self.db.get_entry(eid)['clockify_entry_id'], 'c1')

    def test_end_marks_pending_again(self):
        eid = self.start(clockify_entry_id='c1', clockify_synced=True)
        self.db.end_entry(eid, '2026-09-30T16:00:00Z')
        e = self.db.get_entry(eid)
        self.assertEqual(e['status'], 'completed')
        self.assertEqual(e['end_time'], '2026-09-30T16:00:00Z')
        self.assertEqual(e['clockify_synced'], 0)
        self.assertIsNone(self.db.active_entry_for_tag('tagA'))

    def test_end_without_push_keeps_synced(self):
        # Used when Clockify already ended the entry elsewhere.
        eid = self.start(clockify_entry_id='c1', clockify_synced=True)
        self.db.end_entry(eid, '2026-09-30T16:00:00Z', push=False)
        self.assertEqual(self.db.pending_clockify(), [])

    def test_limit_reached_status(self):
        eid = self.start()
        self.db.end_entry(eid, '2026-09-30T20:00:00Z', status='limit_reached')
        self.assertEqual(self.db.get_entry(eid)['status'], 'limit_reached')

    def test_clockify_result_stores_id_and_clears_pending(self):
        eid = self.start()
        v = self.db.get_entry(eid)['version']
        self.db.set_clockify_result(eid, 'c9', v)
        e = self.db.get_entry(eid)
        self.assertEqual(e['clockify_entry_id'], 'c9')
        self.assertEqual(e['clockify_synced'], 1)
        self.assertEqual(self.db.pending_clockify(), [])

    def test_clockify_result_keeps_pending_if_changed_meanwhile(self):
        # Card tapped out while the start POST was in flight: the id must
        # still be stored, but the end still needs pushing.
        eid = self.start()
        v = self.db.get_entry(eid)['version']
        self.db.end_entry(eid, '2026-09-30T16:00:00Z')
        self.db.set_clockify_result(eid, 'c9', v)
        e = self.db.get_entry(eid)
        self.assertEqual(e['clockify_entry_id'], 'c9')
        self.assertEqual(e['clockify_synced'], 0)

    def test_clockify_error_recorded(self):
        eid = self.start()
        self.db.record_clockify_error(eid, 'HTTP 400: bad')
        e = self.db.get_entry(eid)
        self.assertEqual(e['attempts'], 1)
        self.assertEqual(e['last_error'], 'HTTP 400: bad')
        self.assertEqual(len(self.db.pending_clockify()), 1)

    def test_supabase_queue_needs_clockify_id(self):
        eid = self.start()
        self.assertEqual(self.db.pending_supabase_entries(), [])
        self.db.set_clockify_result(eid, 'c1', self.db.get_entry(eid)['version'])
        pending = self.db.pending_supabase_entries()
        self.assertEqual([p['id'] for p in pending], [eid])
        self.db.mark_entry_supabase_synced(eid, pending[0]['version'])
        self.assertEqual(self.db.pending_supabase_entries(), [])

    def test_end_requeues_supabase(self):
        eid = self.start(clockify_entry_id='c1', clockify_synced=True)
        self.db.mark_entry_supabase_synced(eid, self.db.get_entry(eid)['version'])
        self.db.end_entry(eid, '2026-09-30T16:00:00Z', push=False)
        self.assertEqual(len(self.db.pending_supabase_entries()), 1)

    def test_persists_across_reopen(self):
        eid = self.start()
        path = self.db.path
        self.db.close()
        self.db = LocalDB(path)
        self.assertEqual(self.db.active_entry_for_tag('tagA')['id'], eid)
        self.assertEqual(self.db.get_card('tagA')['name'], 'Alice')


if __name__ == '__main__':
    unittest.main()

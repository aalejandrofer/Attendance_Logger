"""Unit tests for the pure reconciliation logic.

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.reconcile import reconcile_sessions


CARDS = [
    {'tag_uuid': 'tagA', 'name': 'Alice', 'user_id': 'u', 'project_id': 'projA',
     'workspace_id': 'ws', 'task_id': 'tA'},
    {'tag_uuid': 'tagB', 'name': 'Bob', 'user_id': 'u', 'project_id': 'projB',
     'workspace_id': 'ws', 'task_id': 'tB'},
]


def entry(eid, project_id):
    return {
        'id': eid,
        'projectId': project_id,
        'taskId': 'tX',
        'workspaceId': 'ws',
        'description': 'desc',
        'billable': True,
        'timeInterval': {'start': '2026-06-09T08:00:00Z'},
    }


def active(eid, synced=True):
    return {'clockify_entry_id': eid, 'clockify_synced': 1 if synced else 0}


class ReconcileTest(unittest.TestCase):
    def test_recovers_orphan_entry(self):
        # Clockify has projA running, local has nothing -> recover tagA.
        to_add, to_remove = reconcile_sessions(CARDS, [entry('e1', 'projA')], {})
        self.assertIn('tagA', to_add)
        card, e = to_add['tagA']
        self.assertEqual(card['name'], 'Alice')
        self.assertEqual(e['id'], 'e1')
        self.assertEqual(to_remove, [])

    def test_skips_already_tracked(self):
        to_add, to_remove = reconcile_sessions(
            CARDS, [entry('e1', 'projA')], {'tagA': active('e1')})
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, [])

    def test_removes_stale_session(self):
        # Local thinks tagB is active but nothing is running in Clockify.
        to_add, to_remove = reconcile_sessions(CARDS, [], {'tagB': active('gone')})
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, ['tagB'])

    def test_unmapped_project_ignored(self):
        to_add, to_remove = reconcile_sessions(CARDS, [entry('e9', 'unknownProj')], {})
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, [])

    def test_mixed_recover_and_remove(self):
        to_add, to_remove = reconcile_sessions(
            CARDS, [entry('e1', 'projA')], {'tagB': active('old')})
        self.assertEqual(set(to_add), {'tagA'})
        self.assertEqual(to_remove, ['tagB'])

    def test_unsynced_session_is_never_removed(self):
        # Started offline: Clockify doesn't know it yet, so it isn't running there.
        to_add, to_remove = reconcile_sessions(CARDS, [], {'tagA': active(None, synced=False)})
        self.assertEqual(to_remove, [])

    def test_session_with_pending_update_is_never_removed(self):
        to_add, to_remove = reconcile_sessions(CARDS, [], {'tagA': active('e1', synced=False)})
        self.assertEqual(to_remove, [])

    def test_known_entry_is_not_resurrected(self):
        # Ended locally but the end hasn't reached Clockify yet, so Clockify
        # still reports it running. It must not come back as a session.
        to_add, _ = reconcile_sessions(
            CARDS, [entry('e1', 'projA')], {}, known_entry_ids={'e1'})
        self.assertEqual(to_add, {})


if __name__ == '__main__':
    unittest.main()

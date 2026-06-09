"""Unit tests for the pure reconciliation logic.

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.reconcile import reconcile_sessions


PROJECTS = [
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


def session_for(eid):
    return {'entry': {'clockify_entry_id': eid}}


class ReconcileTest(unittest.TestCase):
    def test_recovers_orphan_entry(self):
        # Clockify has projA running, local has nothing -> recover tagA.
        to_add, to_remove = reconcile_sessions(PROJECTS, [entry('e1', 'projA')], {})
        self.assertIn('tagA', to_add)
        user_data, e = to_add['tagA']
        self.assertEqual(user_data['name'], 'Alice')
        self.assertEqual(e['clockify_entry_id'], 'e1')
        self.assertEqual(e['start'], '2026-06-09T08:00:00Z')
        self.assertEqual(to_remove, [])

    def test_skips_already_tracked(self):
        # tagA already tracked locally for the same running entry -> no action.
        active = {'tagA': session_for('e1')}
        to_add, to_remove = reconcile_sessions(PROJECTS, [entry('e1', 'projA')], active)
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, [])

    def test_removes_stale_session(self):
        # Local thinks tagB is active but nothing is running in Clockify.
        active = {'tagB': session_for('gone')}
        to_add, to_remove = reconcile_sessions(PROJECTS, [], active)
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, ['tagB'])

    def test_unmapped_project_ignored(self):
        # Running entry for a project not in Supabase -> can't map, skip.
        to_add, to_remove = reconcile_sessions(PROJECTS, [entry('e9', 'unknownProj')], {})
        self.assertEqual(to_add, {})
        self.assertEqual(to_remove, [])

    def test_mixed_recover_and_remove(self):
        # projA running (recover tagA); local tagB stale (remove).
        active = {'tagB': session_for('old')}
        to_add, to_remove = reconcile_sessions(PROJECTS, [entry('e1', 'projA')], active)
        self.assertEqual(set(to_add), {'tagA'})
        self.assertEqual(to_remove, ['tagB'])

    def test_entry_workspace_fallback(self):
        e = entry('e1', 'projA')
        del e['workspaceId']
        to_add, _ = reconcile_sessions(PROJECTS, [e], {})
        self.assertEqual(to_add['tagA'][1]['workspace_id'], 'ws')


if __name__ == '__main__':
    unittest.main()

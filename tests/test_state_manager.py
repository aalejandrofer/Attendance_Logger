"""Unit tests for StateManager (hardware-free core).

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import json
import os
import tempfile
import unittest

# config.py validates these at import time; provide dummies so importing
# StateManager doesn't require a real .env.
os.environ.setdefault('SUPABASE_URL', 'http://localhost')
os.environ.setdefault('SUPABASE_KEY', 'dummy')
os.environ.setdefault('CLOCKIFY_API_KEY', 'dummy')

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.state_manager import StateManager


def make_entry(eid):
    return {
        'clockify_entry_id': eid,
        'workspace_id': 'w',
        'projectId': 'p',
        'taskId': 't',
        'description': 'd',
        'start': '2026-06-09T10:00:00Z',
        'billable': True,
    }


class StateManagerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.tmp.close()
        self.path = self.tmp.name
        os.remove(self.path)  # let StateManager create it fresh
        self.sm = StateManager(state_file=self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_starts_empty(self):
        self.assertEqual(self.sm.get_active_sessions(), {})

    def test_start_and_get(self):
        self.sm.start_session('tagA', {'name': 'A', 'workspace_id': 'w'}, make_entry('e1'))
        self.assertTrue(self.sm.is_session_active('tagA'))
        s = self.sm.get_session('tagA')
        self.assertEqual(s['user_data']['name'], 'A')
        self.assertEqual(s['entry']['clockify_entry_id'], 'e1')

    def test_concurrent_sessions(self):
        self.sm.start_session('tagA', {'name': 'A', 'workspace_id': 'w'}, make_entry('e1'))
        self.sm.start_session('tagB', {'name': 'B', 'workspace_id': 'w'}, make_entry('e2'))
        self.assertEqual(set(self.sm.get_active_sessions()), {'tagA', 'tagB'})
        # Ending one must not touch the other.
        self.sm.end_session('tagA')
        self.assertFalse(self.sm.is_session_active('tagA'))
        self.assertTrue(self.sm.is_session_active('tagB'))
        self.assertEqual(self.sm.get_session('tagB')['entry']['clockify_entry_id'], 'e2')

    def test_end_unknown_tag_is_noop(self):
        self.sm.start_session('tagA', {'name': 'A', 'workspace_id': 'w'}, make_entry('e1'))
        self.sm.end_session('ghost')
        self.assertTrue(self.sm.is_session_active('tagA'))

    def test_persists_across_instances(self):
        self.sm.start_session('tagA', {'name': 'A', 'workspace_id': 'w'}, make_entry('e1'))
        other = StateManager(state_file=self.path)
        self.assertTrue(other.is_session_active('tagA'))

    def test_legacy_schema_migrates(self):
        # Old v2 schema without the 'sessions' key.
        with open(self.path, 'w') as f:
            json.dump({'active_session': None, 'current_entry': None}, f)
        sm = StateManager(state_file=self.path)
        self.assertEqual(sm.get_active_sessions(), {})

    def test_corrupt_file_recovers(self):
        with open(self.path, 'w') as f:
            f.write('}{ not json')
        sm = StateManager(state_file=self.path)
        self.assertEqual(sm.get_active_sessions(), {})


if __name__ == '__main__':
    unittest.main()

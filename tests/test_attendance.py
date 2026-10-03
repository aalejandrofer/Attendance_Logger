"""Unit tests for the Attendance service (tap, overtime, reconcile, tick).

Run from the repo root:
    python3 -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

import pytz
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Modules.attendance import Attendance
from Modules.local_db import LocalDB
from Modules.sync import Syncer
from test_sync import FakeClockify, FakeMirror

TZ = pytz.timezone('Europe/London')
CARD_A = {'tag_uuid': 'tagA', 'name': 'Alice', 'user_id': 'u', 'project_id': 'projA',
          'workspace_id': 'ws', 'task_id': 'tA'}
CARD_B = {'tag_uuid': 'tagB', 'name': 'Bob', 'user_id': 'u', 'project_id': 'projB',
          'workspace_id': 'ws', 'task_id': 'tB'}


def local(y, m, d, hh, mm=0):
    return TZ.localize(datetime(y, m, d, hh, mm)).astimezone(pytz.utc)


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class InProgressClockify(FakeClockify):
    def __init__(self):
        super().__init__()
        self.in_progress = []

    def get_in_progress(self, workspace_id):
        return None if self.fail else list(self.in_progress)


class AttendanceTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.dir.name, 'a.db')
        self.db = LocalDB(self.db_path)
        self.db.upsert_card(CARD_A)
        self.db.upsert_card(CARD_B)
        self.clockify = InProgressClockify()
        self.mirror = FakeMirror()
        self.clock = Clock(local(2026, 9, 30, 9))
        self.trusted = True
        self.app = self.make_app()

    def make_app(self):
        syncer = Syncer(self.db, self.clockify, self.mirror, time_limit_tag_id='limit')
        return Attendance(
            self.db, syncer, self.clockify, 'Europe/London', work_end_hour=20,
            now=self.clock, clock_trusted=lambda: self.trusted,
            background=lambda fn, *args: fn(*args),
        )

    def tearDown(self):
        self.db.close()
        self.dir.cleanup()


class TapTest(AttendanceTestCase):
    def test_unknown_card(self):
        self.assertEqual(self.app.tap('nope'), ('unknown', None))
        self.assertEqual(self.clockify.created, [])

    def test_tap_in_then_out(self):
        self.assertEqual(self.app.tap('tagA'), ('in', 'Alice'))
        self.assertTrue(self.app.is_clocked_in('tagA'))
        self.assertEqual(self.app.active_count(), 1)
        body = self.clockify.created[0][1]
        self.assertEqual(body['start'], '2026-09-30T08:00:00Z')
        self.assertEqual(body['description'], 'Wednesday 30th at 09:00:00')

        self.clock.t = local(2026, 9, 30, 13, 30)
        self.assertEqual(self.app.tap('tagA'), ('out', 'Alice'))
        self.assertFalse(self.app.is_clocked_in('tagA'))
        self.assertEqual(self.clockify.updated[0][2]['end'], '2026-09-30T12:30:00Z')

    def test_tap_works_with_clockify_down(self):
        self.clockify.fail = requests.ConnectionError('no wifi')
        self.assertEqual(self.app.tap('tagA'), ('in', 'Alice'))
        self.assertEqual(self.app.tap('tagA'), ('out', 'Alice'))
        self.assertEqual(len(self.db.pending_clockify()), 1)

    def test_tag_whitespace_ignored(self):
        self.assertEqual(self.app.tap('tagA\r\n'), ('in', 'Alice'))

    def test_two_people_at_once(self):
        self.app.tap('tagA')
        self.app.tap('tagB')
        self.assertEqual(self.app.active_count(), 2)
        self.app.tap('tagA')
        self.assertTrue(self.app.is_clocked_in('tagB'))

    def test_untrusted_clock_is_flagged(self):
        self.trusted = False
        self.app.tap('tagA')
        self.assertTrue(self.clockify.created[0][1]['description'].endswith('(clock unverified)'))


class DescriptionTest(AttendanceTestCase):
    def test_ordinal_suffixes(self):
        for day, want in [(1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'), (11, '11th'),
                          (12, '12th'), (13, '13th'), (21, '21st'), (22, '22nd'),
                          (23, '23rd'), (31, '31st')]:
            self.clock.t = local(2026, 8, day, 9)
            self.assertIn(' %s at ' % want, self.app.describe(self.clock.t))


class OvertimeTest(AttendanceTestCase):
    def test_nothing_before_end_hour(self):
        self.app.tap('tagA')
        self.clock.t = local(2026, 9, 30, 19, 59)
        self.assertEqual(self.app.end_overtime(), 0)

    def test_ends_at_end_hour_with_limit_tag(self):
        self.app.tap('tagA')
        self.clock.t = local(2026, 9, 30, 20, 4)
        self.assertEqual(self.app.end_overtime(), 1)
        self.assertFalse(self.app.is_clocked_in('tagA'))
        body = self.clockify.updated[0][2]
        self.assertEqual(body['end'], '2026-09-30T19:00:00Z')  # 20:00 BST
        self.assertEqual(body['tagIds'], ['limit'])

    def test_session_left_from_previous_day_ends_that_day(self):
        self.app.tap('tagA')
        self.clock.t = local(2026, 10, 1, 8)  # device was off overnight
        self.assertEqual(self.app.end_overtime(), 1)
        e = self.db.get_entry(1)
        self.assertEqual(e['end_time'], '2026-09-30T19:00:00Z')
        self.assertEqual(e['status'], 'limit_reached')


class ReconcileTest(AttendanceTestCase):
    def test_recovers_entry_started_elsewhere(self):
        self.clockify.in_progress = [{
            'id': 'x1', 'projectId': 'projA', 'taskId': 'tA', 'workspaceId': 'ws',
            'description': 'web', 'billable': True,
            'timeInterval': {'start': '2026-09-30T07:00:00Z'},
        }]
        self.assertTrue(self.app.reconcile())
        self.assertTrue(self.app.is_clocked_in('tagA'))
        self.assertEqual(self.db.pending_clockify(), [])
        # Tapping out now ends the recovered Clockify entry.
        self.app.tap('tagA')
        self.assertEqual(self.clockify.updated[0][1], 'x1')

    def test_closes_session_ended_elsewhere(self):
        self.app.tap('tagA')  # created as c1, synced
        self.clockify.in_progress = []
        self.app.reconcile()
        self.assertFalse(self.app.is_clocked_in('tagA'))
        self.assertEqual(self.db.pending_clockify(), [])  # no push back

    def test_recovered_entry_with_fractional_seconds_can_hit_overtime(self):
        self.clockify.in_progress = [{
            'id': 'x2', 'projectId': 'projB', 'taskId': 'tB', 'workspaceId': 'ws',
            'description': 'web', 'billable': True,
            'timeInterval': {'start': '2026-09-30T07:00:00.123Z'},
        }]
        self.app.reconcile()
        self.clock.t = local(2026, 9, 30, 21)
        self.assertEqual(self.app.end_overtime(), 1)

    def test_skipped_while_queue_pending(self):
        self.clockify.fail = requests.ConnectionError('down')
        self.app.tap('tagA')
        self.clockify.fail = None
        self.assertFalse(self.app.reconcile())
        self.assertTrue(self.app.is_clocked_in('tagA'))

    def test_skipped_when_clockify_unreachable(self):
        self.app.tap('tagA')
        self.clockify.fail = requests.ConnectionError('down')
        self.assertFalse(self.app.reconcile())
        self.assertTrue(self.app.is_clocked_in('tagA'))


class LongOutageTest(AttendanceTestCase):
    """The Sep 2026 incident: 13 days without wifi, then recovery."""

    def test_thirteen_days_offline_then_everything_syncs(self):
        self.clockify.fail = requests.ConnectionError('no wifi')
        self.mirror.fail = requests.ConnectionError('no wifi')
        day0 = datetime(2026, 9, 8)
        for i in range(13):
            d = day0 + timedelta(days=i)
            self.clock.t = local(d.year, d.month, d.day, 9)
            self.assertEqual(self.app.tap('tagA'), ('in', 'Alice'))
            self.app.tick()
            if i == 5:
                # Forgot to tap out: overtime must end it offline.
                self.clock.t = local(d.year, d.month, d.day, 20, 5)
                self.app.tick()
                self.assertFalse(self.app.is_clocked_in('tagA'))
                continue
            if i == 8:
                # Power cut mid-outage: device restarts with a fresh process.
                self.app = self.make_app()
            self.clock.t = local(d.year, d.month, d.day, 17)
            self.assertEqual(self.app.tap('tagA'), ('out', 'Alice'))
            self.app.tick()

        self.assertEqual(self.clockify.created, [])
        self.assertEqual(len(self.db.pending_clockify()), 13)

        # Wifi returns.
        self.clockify.fail = None
        self.mirror.fail = None
        self.app.tick()

        self.assertEqual(self.db.pending_clockify(), [])
        self.assertEqual(len(self.clockify.created), 13)  # one per day, no duplicates
        self.assertEqual(self.clockify.updated, [])
        for _, body in self.clockify.created:
            self.assertIn('end', body)
        overtime = [b for _, b in self.clockify.created if b.get('tagIds')]
        self.assertEqual(len(overtime), 1)
        mirrored = [r for t, rows, _ in self.mirror.upserts if t == 'time_entries' for r in rows]
        self.assertEqual(len(mirrored), 13)


class LegacyStateTest(AttendanceTestCase):
    def test_imports_state_json_sessions_once(self):
        path = os.path.join(self.dir.name, 'state.json')
        with open(path, 'w') as f:
            json.dump({'sessions': {'tagA': {
                'tag_uuid': 'tagA',
                'user_data': {k: CARD_A[k] for k in CARD_A if k != 'tag_uuid'},
                'entry': {'clockify_entry_id': 'old1', 'workspace_id': 'ws',
                          'projectId': 'projA', 'taskId': 'tA', 'description': 'd',
                          'start': '2026-09-30T07:00:00Z', 'billable': True},
            }}}, f)
        self.assertEqual(self.app.import_legacy_state(path), 1)
        self.assertTrue(self.app.is_clocked_in('tagA'))
        self.assertEqual(self.db.pending_clockify(), [])
        self.assertFalse(os.path.exists(path))
        self.assertEqual(self.app.import_legacy_state(path), 0)

    def test_bad_legacy_session_is_skipped(self):
        path = os.path.join(self.dir.name, 'state.json')
        with open(path, 'w') as f:
            json.dump({'sessions': {'tagA': {'user_data': {}, 'entry': {}}}}, f)
        self.assertEqual(self.app.import_legacy_state(path), 0)


if __name__ == '__main__':
    unittest.main()

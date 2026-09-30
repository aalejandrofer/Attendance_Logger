"""SQLite store on the device: the source of truth for cards and time entries.

Everything the device needs to work (which card belongs to whom, who is
clocked in) lives here, so a tap never depends on the network. Clockify and
Supabase are sync targets fed from the queues this module exposes.

Each row carries a `version` that bumps on every local change. Sync code marks
a row as pushed only if the version it pushed is still current, so an edit
made while a push is in flight is never lost.

Stdlib only; targets Python 3.7 / SQLite 3.27 (the Pi).
"""
import os
import sqlite3
import threading
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    tag_uuid        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    user_id         TEXT NOT NULL,
    project_id      TEXT NOT NULL,
    workspace_id    TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    supabase_synced INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entries (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_uuid          TEXT NOT NULL,
    name              TEXT NOT NULL,
    user_id           TEXT NOT NULL,
    project_id        TEXT NOT NULL,
    workspace_id      TEXT NOT NULL,
    task_id           TEXT NOT NULL,
    description       TEXT,
    billable          INTEGER NOT NULL DEFAULT 1,
    start_time        TEXT NOT NULL,
    end_time          TEXT,
    status            TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'completed', 'limit_reached')),
    clockify_entry_id TEXT UNIQUE,
    clockify_synced   INTEGER NOT NULL DEFAULT 0,
    supabase_synced   INTEGER NOT NULL DEFAULT 0,
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    version           INTEGER NOT NULL DEFAULT 1,
    updated_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entries_status ON entries(status);
CREATE INDEX IF NOT EXISTS idx_entries_tag ON entries(tag_uuid);
"""

CARD_FIELDS = ('tag_uuid', 'name', 'user_id', 'project_id', 'workspace_id', 'task_id')


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def normalize_tag(tag):
    return (tag or '').strip()


class LocalDB:
    def __init__(self, path):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        # One connection shared by the main loop and the background checker
        # thread; the lock serialises access.
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute('PRAGMA journal_mode=WAL')
            self._conn.execute('PRAGMA synchronous=FULL')  # survive power cuts
            self._conn.executescript(SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    def _exec(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params)

    def _one(self, sql, params=()):
        with self._lock:  # fetch under the lock too: the connection is shared
            row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def _all(self, sql, params=()):
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ---- cards -----------------------------------------------------------

    def upsert_card(self, card, synced=False):
        values = {f: card[f] for f in CARD_FIELDS}
        values['tag_uuid'] = normalize_tag(values['tag_uuid'])
        self._exec(
            """
            INSERT INTO cards (tag_uuid, name, user_id, project_id, workspace_id,
                               task_id, updated_at, supabase_synced)
            VALUES (:tag_uuid, :name, :user_id, :project_id, :workspace_id,
                    :task_id, :updated_at, :synced)
            ON CONFLICT(tag_uuid) DO UPDATE SET
                name = excluded.name,
                user_id = excluded.user_id,
                project_id = excluded.project_id,
                workspace_id = excluded.workspace_id,
                task_id = excluded.task_id,
                updated_at = excluded.updated_at,
                supabase_synced = excluded.supabase_synced,
                version = cards.version + 1
            """,
            dict(values, updated_at=_now(), synced=1 if synced else 0),
        )

    def get_card(self, tag_uuid):
        return self._one('SELECT * FROM cards WHERE tag_uuid = ?', (normalize_tag(tag_uuid),))

    def all_cards(self):
        return self._all('SELECT * FROM cards ORDER BY name')

    def remove_card(self, tag_uuid):
        cur = self._exec('DELETE FROM cards WHERE tag_uuid = ?', (normalize_tag(tag_uuid),))
        return cur.rowcount > 0

    def unsynced_cards(self):
        return self._all('SELECT * FROM cards WHERE supabase_synced = 0')

    def mark_card_synced(self, tag_uuid, version):
        self._exec(
            'UPDATE cards SET supabase_synced = 1 WHERE tag_uuid = ? AND version = ?',
            (tag_uuid, version),
        )

    # ---- entries ---------------------------------------------------------

    def start_entry(self, card, start_time, description, billable=True,
                    clockify_entry_id=None, clockify_synced=False):
        cur = self._exec(
            """
            INSERT INTO entries (tag_uuid, name, user_id, project_id, workspace_id,
                                 task_id, description, billable, start_time,
                                 clockify_entry_id, clockify_synced, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalize_tag(card['tag_uuid']), card['name'], card['user_id'],
                card['project_id'], card['workspace_id'], card['task_id'],
                description, 1 if billable else 0, start_time,
                clockify_entry_id, 1 if clockify_synced else 0, _now(),
            ),
        )
        return cur.lastrowid

    def end_entry(self, entry_id, end_time, status='completed', push=True):
        """Close an entry. `push=False` when Clockify already has the end."""
        self._exec(
            """
            UPDATE entries SET
                end_time = ?, status = ?,
                clockify_synced = CASE WHEN ? THEN 0 ELSE clockify_synced END,
                supabase_synced = 0, version = version + 1, updated_at = ?
            WHERE id = ?
            """,
            (end_time, status, 1 if push else 0, _now(), entry_id),
        )

    def get_entry(self, entry_id):
        return self._one('SELECT * FROM entries WHERE id = ?', (entry_id,))

    def active_entries(self):
        return self._all("SELECT * FROM entries WHERE status = 'active' ORDER BY id")

    def active_entry_for_tag(self, tag_uuid):
        return self._one(
            "SELECT * FROM entries WHERE status = 'active' AND tag_uuid = ? "
            "ORDER BY id DESC LIMIT 1",
            (normalize_tag(tag_uuid),),
        )

    def known_clockify_ids(self):
        rows = self._all('SELECT clockify_entry_id FROM entries WHERE clockify_entry_id IS NOT NULL')
        return {r['clockify_entry_id'] for r in rows}

    def pending_clockify(self):
        return self._all('SELECT * FROM entries WHERE clockify_synced = 0 ORDER BY id')

    def set_clockify_result(self, entry_id, clockify_entry_id, version):
        """Store the Clockify id; mark synced only if nothing changed since."""
        self._exec(
            """
            UPDATE entries SET
                clockify_entry_id = ?,
                clockify_synced = CASE WHEN version = ? THEN 1 ELSE 0 END,
                supabase_synced = 0, attempts = 0, last_error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (clockify_entry_id, version, _now(), entry_id),
        )

    def record_clockify_error(self, entry_id, error):
        self._exec(
            'UPDATE entries SET attempts = attempts + 1, last_error = ? WHERE id = ?',
            (str(error)[:500], entry_id),
        )

    def pending_supabase_entries(self):
        return self._all(
            'SELECT * FROM entries WHERE supabase_synced = 0 '
            'AND clockify_entry_id IS NOT NULL ORDER BY id'
        )

    def mark_entry_supabase_synced(self, entry_id, version):
        self._exec(
            'UPDATE entries SET supabase_synced = 1 WHERE id = ? AND version = ?',
            (entry_id, version),
        )

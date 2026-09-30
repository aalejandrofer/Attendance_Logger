"""Builds the object graph from config. Shared by main.py and manage_cards.py."""
from config import (
    CLOCKIFY_API_KEY, LOCAL_DB, REQUEST_TIMEOUT, SUPABASE_KEY, SUPABASE_URL,
    TIME_LIMIT_TAG_ID, TIMEZONE, WORK_END_HOUR,
)
from Modules.attendance import Attendance
from Modules.clockify import ClockifyClient
from Modules.local_db import LocalDB
from Modules.supabase_mirror import SupabaseMirror
from Modules.sync import Syncer


def build():
    db = LocalDB(LOCAL_DB)
    clockify = ClockifyClient(CLOCKIFY_API_KEY, timeout=REQUEST_TIMEOUT)
    mirror = None
    if SUPABASE_URL and SUPABASE_KEY:
        mirror = SupabaseMirror(SUPABASE_URL, SUPABASE_KEY, timeout=REQUEST_TIMEOUT)
    syncer = Syncer(db, clockify, mirror, time_limit_tag_id=TIME_LIMIT_TAG_ID)
    app = Attendance(db, syncer, clockify, TIMEZONE, WORK_END_HOUR)
    return app

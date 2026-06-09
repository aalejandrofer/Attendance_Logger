import json
import os
import logging
import fcntl
from datetime import datetime
from typing import Optional
from config import STATE_FILE

class StateManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.state_file = STATE_FILE
        storage_dir = os.path.dirname(STATE_FILE)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
        self._ensure_state_file()
    
    def _acquire_lock(self, file_obj):
        """Acquire exclusive lock on file"""
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
    
    def _release_lock(self, file_obj):
        """Release file lock"""
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    
    def _ensure_state_file(self):
        """Ensure state file exists with valid initial state"""
        initial_state = {
            'sessions': {}
        }

        try:
            if not os.path.exists(self.state_file):
                with open(self.state_file, 'w') as f:
                    self._acquire_lock(f)
                    json.dump(initial_state, f)
                    self._release_lock(f)
            else:
                # Validate and repair if needed
                with open(self.state_file, 'r+') as f:
                    self._acquire_lock(f)
                    try:
                        state = json.load(f)
                        if not isinstance(state, dict) or \
                           not all(key in state for key in initial_state):
                            f.seek(0)
                            json.dump(initial_state, f)
                            f.truncate()
                    except Exception:
                        f.seek(0)
                        json.dump(initial_state, f)
                        f.truncate()
                    finally:
                        self._release_lock(f)
        except Exception as e:
            logging.error(f"Error initializing state file: {e}")
            # Ensure we have a valid state file
            with open(self.state_file, 'w') as f:
                json.dump(initial_state, f)

    def _save_state(self, state):
        """Save state with file locking"""
        with open(self.state_file, 'w') as f:
            self._acquire_lock(f)
            try:
                json.dump(state, f)
            finally:
                self._release_lock(f)
    
    def _load_state(self):
        """Load state with file locking"""
        try:
            with open(self.state_file, 'r') as f:
                self._acquire_lock(f)
                try:
                    return json.load(f)
                finally:
                    self._release_lock(f)
        except Exception as e:
            logging.error(f"Error loading state: {e}")
            return {'sessions': {}}

    def _sessions(self, state) -> dict:
        """Return the sessions dict, tolerating legacy/corrupt state."""
        sessions = state.get('sessions')
        return sessions if isinstance(sessions, dict) else {}

    def start_session(self, tag_uuid: str, user_data: dict, entry: dict) -> None:
        """Start (or replace) a session for one RFID tag.

        `entry` holds the Clockify context needed to end this exact entry later
        (clockify_entry_id, workspace_id, start, billable, description, etc.).
        """
        state = self._load_state()
        sessions = self._sessions(state)
        sessions[tag_uuid] = {
            'tag_uuid': tag_uuid,
            'start_time': datetime.now().strftime("%d-%m-%Y %H:%M"),
            'user_data': user_data,
            'entry': entry,
        }
        state['sessions'] = sessions
        self._save_state(state)

    def end_session(self, tag_uuid: str) -> None:
        """End the session for one tag."""
        state = self._load_state()
        sessions = self._sessions(state)
        sessions.pop(tag_uuid, None)
        state['sessions'] = sessions
        self._save_state(state)

    def get_session(self, tag_uuid: str) -> Optional[dict]:
        """Get the active session for one tag, if any."""
        return self._sessions(self._load_state()).get(tag_uuid)

    def get_active_sessions(self) -> dict:
        """Get all active sessions keyed by tag_uuid."""
        return self._sessions(self._load_state())

    def is_session_active(self, tag_uuid: str) -> bool:
        """True if the given tag has an active session."""
        try:
            return tag_uuid in self._sessions(self._load_state())
        except Exception as e:
            logging.error(f"Error checking session status: {e}")
            return False

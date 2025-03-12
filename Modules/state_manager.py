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
            'active_session': None,
            'current_entry': None
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
            return {
                'active_session': None,
                'current_entry': None
            }
    
    def start_session(self, tag_uuid: str, user_data: dict) -> None:
        """Start a new session"""
        state = self._load_state()
        state['active_session'] = {
            'tag_uuid': tag_uuid,
            'start_time': datetime.now().strftime("%d-%m-%Y %H:%M"),
            'user_data': user_data
        }
        self._save_state(state)
        
    def end_session(self) -> None:
        """End the active session"""
        state = self._load_state()
        state['active_session'] = None
        self._save_state(state)
        
    def get_active_session(self) -> Optional[dict]:
        """Get active session if any"""
        return self._load_state()['active_session']
        
    def is_session_active(self, tag_uuid: str) -> bool:
        """Check if given tag has active session with safe access"""
        try:
            session = self._load_state().get('active_session')
            return session is not None and session.get('tag_uuid') == tag_uuid
        except Exception as e:
            logging.error(f"Error checking session status: {e}")
            return False
        
    def save_entry(self, entry_data: dict) -> None:
        """Save current Clockify entry data"""
        state = self._load_state()
        state['current_entry'] = entry_data
        self._save_state(state)
        
    def get_entry(self) -> Optional[dict]:
        """Get current Clockify entry data"""
        return self._load_state()['current_entry']

import threading
from datetime import datetime
import logging
import pytz
from typing import Optional
import requests

from config import TIMEZONE, WORK_END_HOUR, REQUEST_TIMEOUT
from Modules.state_manager import StateManager
import Modules.logger as logger
import Modules.display as display

TIMELIMIT_TAG_ID = "62c7a84f10ace715d5d553be"

class TimeChecker:
    def __init__(self, check_interval: int = 300):  # 5 minutes default
        self.timezone = pytz.timezone(TIMEZONE)
        self.check_interval = check_interval
        self.state_manager = StateManager(logger.ROOT_DIR)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the checker in a background thread"""
        if self._thread and self._thread.is_alive():
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_checker)
        self._thread.daemon = True  # Thread will exit when main program exits
        self._thread.start()
        logging.info("Time checker started")
        
    def stop(self):
        """Stop the checker thread"""
        if self._thread:
            self._stop_event.set()
            self._thread.join()
            logging.info("Time checker stopped")
            
    def _run_checker(self):
        """Main checker loop"""
        while not self._stop_event.is_set():
            try:
                self._check_active_sessions()
            except Exception as e:
                logging.error(f"Error in time checker: {e}")
            
            # Sleep until next check, but allow interruption
            self._stop_event.wait(self.check_interval)
                
    def _check_active_sessions(self):
        """End every active session once past work hours."""
        now = datetime.now(self.timezone)

        if now.hour < WORK_END_HOUR:
            return

        for tag_uuid, session in list(self.state_manager.get_active_sessions().items()):
            try:
                logging.info(f"Ending overtime session for {session['user_data']['name']}")
                endResponse = logger.terminateLog(tag_uuid)

                if endResponse and 'id' in endResponse:
                    # Add time limit tag to the entry
                    workspace_id = session["user_data"]["workspace_id"]
                    tag_url = f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/time-entries/{endResponse["id"]}'
                    logger.logger_instance.headers['Content-Type'] = 'application/json'
                    requests.put(
                        tag_url,
                        headers=logger.logger_instance.headers,
                        json={
                            **endResponse,
                            'tagIds': [TIMELIMIT_TAG_ID]
                        },
                        timeout=REQUEST_TIMEOUT
                    )

                self.state_manager.end_session(tag_uuid)
                logging.info(f"Successfully ended overtime session for {session['user_data']['name']}")
            except Exception as e:
                logging.error(f"Error ending overtime session: {e}")

    def check_startup_sessions(self):
        """Log any sessions left active from a previous run."""
        try:
            sessions = self.state_manager.get_active_sessions()
            for session in sessions.values():
                user_name = session['user_data'].get('name', 'Unknown')
                start_time = session['start_time']
                logging.info(f"Found active session for {user_name} started at {start_time}")
        except Exception as e:
            logging.error(f"Error checking startup session: {e}")

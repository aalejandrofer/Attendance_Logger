import requests
import json
from datetime import datetime
import pytz
import logging
from config import TIMEZONE, CLOCKIFY_API_KEY, ROOT_DIR, REQUEST_TIMEOUT
from Modules.db_manager import DatabaseManager
from Modules.state_manager import StateManager

CONTENT_TYPE = "application/json"

class ClockifyLogger:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'content-type': CONTENT_TYPE, 'X-Api-Key': api_key}
        self.db = DatabaseManager()
        self.tz = pytz.timezone(TIMEZONE)
        self.state = StateManager(ROOT_DIR)

    def startLog(self, user_id, project_id, workspace_id, task_id, tag_uuid):
        entry_data = {
            'user_id': user_id,
            'project_id': project_id,
            'workspace_id': workspace_id,
            'task_id': task_id
        }
        time, nameOfDay = self.getTime()
        return self.startEntry(time, nameOfDay, entry_data)

    def getTime(self):
        """Return (utc_timestamp, local_day_name).

        Clockify expects UTC timestamps with the 'Z' suffix. The day name is
        kept in the configured local timezone for the human-readable description.
        """
        utc_now = datetime.now(pytz.utc)
        format_time = utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        local_day = datetime.now(self.tz).strftime('%A')
        return format_time, local_day

    def formatDescription(self, nameOfDay):
        now = datetime.now(self.tz)
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(now.day % 20, 'th')
        return f"{nameOfDay} {now.day}{suffix} at {now.strftime('%H:%M:%S')}"

    def startEntry(self, time, nameOfDay, entry_data):
        description = self.formatDescription(nameOfDay)

        body = {
            "start": time,
            "billable": True,
            "description": description,
            "projectId": entry_data['project_id'],
            "taskId": entry_data['task_id']
        }

        response = requests.post(
            f'https://api.clockify.me/api/v1/workspaces/{entry_data["workspace_id"]}/time-entries',
            data=json.dumps(body),
            headers=self.headers,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 201:
            response_data = response.json()
            supabase_body = {
                'project_id': entry_data['project_id'],
                'start_time': time,
                'description': body['description'],
                'clockify_entry_id': response_data['id'],
                'status': 'active'
            }
            self.db.log_time_entry(supabase_body)

        return response

    def get_in_progress(self, workspace_id):
        """Clockify's in-progress entries for a workspace.

        Returns a list on success (possibly empty), or None if the fetch
        failed. Callers must distinguish: an empty list means "nothing
        running", None means "don't trust this — leave local state alone".
        """
        url = f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/time-entries/status/in-progress'
        try:
            resp = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                logging.error(f"Failed to fetch in-progress entries: {resp.text}")
                return None
            return resp.json() or []
        except Exception as e:
            logging.error(f"Error fetching in-progress entries: {e}")
            return None

    def endEntry(self, tag_uuid, time):
        """End the exact Clockify entry that this tag's session started.

        Uses the clockify_entry_id stored at start time, so concurrent users
        never end each other's entries.
        """
        session = self.state.get_session(tag_uuid)
        entry = session.get('entry') if session else None

        if not entry or not entry.get('clockify_entry_id'):
            logging.error(f"No stored Clockify entry for tag {tag_uuid}")
            return None

        try:
            end_url = (
                f'https://api.clockify.me/api/v1/workspaces/'
                f'{entry["workspace_id"]}/time-entries/{entry["clockify_entry_id"]}'
            )
            response = requests.put(
                end_url,
                headers=self.headers,
                json={
                    "start": entry["start"],
                    "end": time,
                    "billable": entry.get("billable", True),
                    "description": entry.get("description"),
                    "projectId": entry["projectId"],
                    "taskId": entry["taskId"]
                },
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                logging.error(f"Failed to end entry: {response.text}")
                return None

            response_data = response.json()

            self.db.update_time_entry(
                entry["clockify_entry_id"],
                {'end_time': time, 'status': 'completed'}
            )

            return response_data

        except Exception as e:
            logging.error(f"Error ending entry: {e}")
            return None

# Initialize logger with API key
logger_instance = ClockifyLogger(CLOCKIFY_API_KEY)

# Modify existing functions to use logger_instance
def startLog(user_id, project_id, workspace_id, task_id, tag_uuid):
    return logger_instance.startLog(user_id, project_id, workspace_id, task_id, tag_uuid)

def terminateLog(tag_uuid):
    time, _ = logger_instance.getTime()
    session = logger_instance.state.get_session(tag_uuid)

    if not session:
        logging.warning(f"No active session for tag: {tag_uuid}")
        return None

    return logger_instance.endEntry(tag_uuid, time)
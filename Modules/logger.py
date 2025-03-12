import requests
import json
from datetime import datetime
import pytz
import logging
from config import TIMEZONE, CLOCKIFY_API_KEY, ROOT_DIR
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
        self.state.save_entry(entry_data)  # No need for tag_uuid
        return self.startEntry(time, nameOfDay)

    def getTime(self):
        """Get timezone-aware timestamp"""
        now = datetime.now(self.tz)
        format_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        return format_time, now.strftime('%A')

    def formatDescription(self, nameOfDay):
        now = datetime.now(self.tz)
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(now.day % 20, 'th')
        return f"{nameOfDay} {now.day}{suffix} at {now.strftime('%H:%M:%S')}"

    def startEntry(self, time, nameOfDay):
        description = self.formatDescription(nameOfDay)
        entry_data = self.state.get_entry()

        body = {
            "start": time,
            "billable": "true",
            "description": description,
            "projectId": entry_data['project_id'],
            "taskId": entry_data['task_id']
        }

        response = requests.post(
            f'https://api.clockify.me/api/v1/workspaces/{entry_data["workspace_id"]}/time-entries',
            data=json.dumps(body),
            headers=self.headers
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

    def endEntry(self, time):
        entry_data = self.state.get_entry()
        session = self.state.get_active_session()
        
        if not entry_data or not session:
            logging.error("No active entry found")
            return None

        try:
            # Get current in-progress entry
            in_progress_url = f'https://api.clockify.me/api/v1/workspaces/{entry_data["workspace_id"]}/time-entries/status/in-progress'
            active_entry = requests.get(
                in_progress_url, 
                headers=self.headers
            )
            
            if active_entry.status_code != 200:
                logging.error(f"Failed to get active entry: {active_entry.text}")
                return None
                
            entries = active_entry.json()
            if not entries or len(entries) == 0:
                logging.error("No active time entries found")
                return None
            
            # Get the most recent entry
            entry_data = entries[0]
                
            # End the entry using PUT method
            end_url = f'https://api.clockify.me/api/v1/workspaces/{entry_data["workspaceId"]}/time-entries/{entry_data["id"]}'
            response = requests.put(
                end_url, 
                headers=self.headers,
                json={
                    "start": entry_data["timeInterval"]["start"],
                    "end": time,
                    "billable": entry_data["billable"],
                    "description": entry_data["description"],
                    "projectId": entry_data["projectId"],
                    "taskId": entry_data["taskId"]
                }
            )
            
            if response.status_code != 200:
                logging.error(f"Failed to end entry: {response.text}")
                return None
                
            response_data = response.json()
            
            # Update Supabase with both clockify_entry_id and end_time
            update_data = {
                'end_time': time,
                'status': 'completed'
            }
            self.db.update_time_entry(entry_data["id"], update_data)
            
            # Clear entry data
            self.state.save_entry(None)
            
            return response_data
            
        except Exception as e:
            logging.error(f"Error ending entry: {e}")
            return None

    def updateEntryOnLimit(self):
        self.current_entry['description'] = self.current_entry["description"] + ' // Limit Reached!'
        response = requests.put(f"https://api.clockify.me/api/v1/workspaces/{self.current_entry['workspace_id']}/time-entries/{self.current_entry['entry_id']}", data=json.dumps(self.current_entry), headers=self.headers)
        
        # Update Supabase entry
        self.db.update_time_entry(
            self.current_entry['entry_id'],
            {
                'status': 'limit_reached',
                'description': self.current_entry['description']
            }
        )
        
        return response

# Initialize logger with API key
logger_instance = ClockifyLogger(CLOCKIFY_API_KEY)

# Modify existing functions to use logger_instance
def startLog(user_id, project_id, workspace_id, task_id, tag_uuid):
    return logger_instance.startLog(user_id, project_id, workspace_id, task_id, tag_uuid)

def terminateLog(tag_uuid):
    time, nameOfDay = logger_instance.getTime()
    session = logger_instance.state.get_active_session()
    
    if not session or session.get('tag_uuid') != tag_uuid:
        logging.warning(f"Attempt to end session with wrong tag: {tag_uuid}")
        return None
        
    return logger_instance.endEntry(time)
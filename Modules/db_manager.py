from supabase import create_client
import sys
from functools import lru_cache
import logging
sys.path.append('..')
from config import SUPABASE_URL, SUPABASE_KEY

class DatabaseManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def get_user_by_tag(self, tag_id):
        """Get user and project details from tag ID - no caching"""
        try:
            response = self.supabase.table('projects').select(
                'id',
                'name',
                'user_id',
                'project_id',
                'workspace_id',
                'task_id'
            ).eq('tag_uuid', tag_id).execute()
            
            if not response.data:
                logging.warning(f"No user found for tag: {tag_id}")
                return None
                
            return response.data[0]
        except Exception as e:
            logging.error(f"Database error in get_user_by_tag: {e}")
            return None

    @lru_cache(maxsize=32)
    def get_project_details(self, project_id):
        """Get project details using string ID from Clockify"""
        try:
            response = self.supabase.table('projects').select(
                'project_id',
                'workspace_id',
                'task_id'
            ).eq('project_id', project_id).execute()
            
            if not response.data:
                logging.warning(f"No project found with ID: {project_id}")
                return None
                
            return response.data[0]
        except Exception as e:
            logging.error(f"Database error in get_project_details: {e}")
            return None

    def log_time_entry(self, entry_data):
        try:
            response = self.supabase.table('time_entries').insert({
                'project_id': entry_data['project_id'],
                'start_time': entry_data['start_time'],
                'description': entry_data.get('description'),
                'clockify_entry_id': entry_data.get('clockify_entry_id'),
                'status': entry_data.get('status', 'active')
            }).execute()
            
            if not response.data:
                logging.error("Failed to insert time entry")
                return None
                
            return response.data[0]
            
        except Exception as e:
            logging.error(f"Error logging time entry: {e}")
            return None

    def update_time_entry(self, clockify_entry_id, update_data):
        """Update existing time entry"""
        try:
            response = self.supabase.table('time_entries')\
                .update(update_data)\
                .eq('clockify_entry_id', clockify_entry_id)\
                .execute()
                
            if not response.data:
                logging.error(f"No time entry found with ID: {clockify_entry_id}")
                return None
                
            return response.data[0]
            
        except Exception as e:
            logging.error(f"Error updating time entry: {e}")
            return None

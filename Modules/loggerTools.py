import logging
from time import sleep
from config import ROOT_DIR
# Modules
import Modules.logger as logger
import Modules.display as display
from Modules.db_manager import DatabaseManager
from Modules.state_manager import StateManager

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests.

db = DatabaseManager()
state = StateManager(ROOT_DIR)

logging.basicConfig(
    filename='attendance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def checkRFData(data):
    user_data = db.get_user_by_tag(data)
    if user_data:
        display.createSound()
        return user_data, data  # Return tag_uuid also
    return None, None

def startTimer(user_data, tag_uuid):
    try:
        logging.info(f"Starting timer for user: {user_data}")
        
        startResponse = logger.startLog(
            user_id=user_data['user_id'],
            project_id=user_data['project_id'],
            workspace_id=user_data['workspace_id'],
            task_id=user_data['task_id'],
            tag_uuid=tag_uuid
        )
        
        if startResponse.status_code == 201:
            logging.info(f"Timer started for {user_data['name']}")
            display.displayRead(user_data['name'])
            state.start_session(tag_uuid, user_data)
            sleep(2)  # Show start message briefly
            display.displayTimer()  # Show timer immediately after start
            return True
            
        logging.error(f"Failed to start timer: {startResponse.text}")
        return False
            
    except Exception as e:
        logging.error(f"Error starting timer: {e}")
        return False

def endTimer(tag_uuid):
    try:
        session = state.get_active_session()
        if not session:
            logging.error("No active session found")
            return False
            
        if session['tag_uuid'] != tag_uuid:
            logging.warning(f"Wrong tag used to end session. Expected: {session['tag_uuid']}, Got: {tag_uuid}")
            return False
            
        endResponse = logger.terminateLog(tag_uuid)
        if endResponse:
            logging.info(f"Timer ended for {session['user_data']['name']}")
            display.displayEnd()
            state.end_session()
            return True
        else:
            logging.error("Failed to end timer - no active entry")
            return False
    except Exception as e:
        logging.error(f"Error ending timer: {e}")
        return False
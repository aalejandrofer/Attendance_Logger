from dotenv import load_dotenv
import os

# Directory settings
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env from the repo root regardless of the working directory
load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Configuration from environment variables
CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')
# Optional: without these the device runs fully local (no online mirror).
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/London')
WORK_END_HOUR = int(os.getenv('WORK_END_HOUR', 20))
# Clockify tag added to entries auto-ended at WORK_END_HOUR
TIME_LIMIT_TAG_ID = os.getenv('TIME_LIMIT_TAG_ID', '62c7a84f10ace715d5d553be')
# Seconds before any HTTP request gives up (prevents hung device)
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
# Seconds between background sync/overtime/reconcile runs
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 300))

STORAGE_DIR = os.path.join(ROOT_DIR, 'localstorage')
LOCAL_DB = os.getenv('LOCAL_DB', os.path.join(STORAGE_DIR, 'attendance.db'))
# Pre-SQLite session file, imported once on startup
STATE_FILE = os.path.join(STORAGE_DIR, 'state.json')

# Display settings
DISPLAY_FONT_SIZE = 11
GPIO_BUZZER_PIN = 17

if not CLOCKIFY_API_KEY:
    raise EnvironmentError("Missing required environment variable: CLOCKIFY_API_KEY")

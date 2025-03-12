from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
CLOCKIFY_API_KEY = os.getenv('CLOCKIFY_API_KEY')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/London')
WORK_END_HOUR = int(os.getenv('WORK_END_HOUR', 20))

# Directory settings
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(ROOT_DIR, 'localstorage', 'state.json')

# Display settings
DISPLAY_FONT_SIZE = 11
GPIO_BUZZER_PIN = 17

# Validate required environment variables
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'CLOCKIFY_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
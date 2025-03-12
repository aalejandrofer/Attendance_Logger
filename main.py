#!/usr/bin/python3
from operator import lt
from time import sleep
import os

# Modules
import Modules.display as display
import Modules.loggerTools as lT
from Modules.time_checker import TimeChecker

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests apscheduler

if __name__ == "__main__":
    # Ensure storage directory exists
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'localstorage')
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    display.welcomeUser()
    sleep(0.5)

    print("Starting Up ...\n")
    
    # Start time checker and check for leftover sessions
    time_checker = TimeChecker(check_interval=300)
    time_checker.check_startup_sessions() # Check for leftover sessions
    time_checker.start()
    
    try:
        # Main loop
        while True:
            if lT.state.get_active_session():
                display.displayTimer()
            else:
                display.waitingToRead()
            
            data = display.read_rfid.read_rfid()
            user_data, tag_uuid = lT.checkRFData(data)
            print(f"ID: {data}\n")

            if not user_data:
                sleep(1)
                continue

            if not lT.state.is_session_active(tag_uuid):
                lT.startTimer(user_data, tag_uuid)
            else:
                lT.endTimer(tag_uuid)
                sleep(2)  # Show end message briefly
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        time_checker.stop()




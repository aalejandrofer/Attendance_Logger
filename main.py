from time import sleep
from datetime import datetime
import Modules.logger as logger
#import Modules.display as display
#import Modules.serial as serial

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip install requests

# System set up
#status = serial.setUp()

# Startin the loop when program starts up



#TODO ACTIVATE API
ids = logger.getIDs()
startResponse = logger.startLog()
sleep(1)
endResponse = logger.terminateLog()

# Logging to txt file
with open("RFID.log", "a") as f:
  now = datetime.now().strftime("%d-%m-%Y %H:%M")
  f.write(f"{now} : {startResponse}\n")
  f.write(f"{now} : {endResponse}\n")
  f.close()

  

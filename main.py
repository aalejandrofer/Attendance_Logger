from time import sleep
from datetime import datetime

# Modules
import Modules.logger as logger
import Modules.display as display

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests

# False if start entry not entered
# True if timer is running
status = False

rfid = display.read_rfid()

if __name__ == "__main__":

  display.displayStart()
  
  # Startin the loop when program starts up
  while True:

    idRead = rfid.read_rfid()

    if idRead:

      if status == False:
        display.displayRead()

        ids = logger.getIDs()
        startResponse = logger.startLog()

        status = True

        # Logging to txt file
        with open("RFID.log", "a") as f:
          now = datetime.now().strftime("%d-%m-%Y %H:%M")
          f.write(f"{now} : {startResponse}\n")
          f.close()
          
        # Reset
        sleep(10)
        display.displayTimer()
        
      else:

        ids = logger.getIDs()
        endResponse = logger.terminateLog()

        display.displayEnd()

        # Logging to txt file
        with open("RFID.log", "a") as f:
          now = datetime.now().strftime("%d-%m-%Y %H:%M")
          #f.write(f"{now} : {startResponse}\n")
          f.write(f"{now} : {endResponse}\n")
          f.close()

        # Back to main stage
        status = False
        sleep(10)
        display.waitingToRead()




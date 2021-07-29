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
PATH = "./lastStatus.txt"
def checkStatus():
  try:
    status = open(PATH, "r+").readline().rstrip()
    if status != 'False' and status != 'True':
      f = open(PATH, "w+")
      f.write('False')
      f.close()
      status = open(PATH).readline().rstrip()
  except:
    f = open(PATH, "w+")
    f.write("False")
    f.close()
    status = open(PATH).readline().rstrip()
  
  if status == 'True':
    return True
  else:
    return False

def writeStatus(status):
  f = open(PATH, "w")
  f.write(f"{status}")
  f.close

def checkRFData(data):
  if data == ("02004819B2E1"): #TODO add card ID
    return True
  else:
    return False

if __name__ == "__main__":

  status = checkStatus()

  if status:
    display.displayRead()
  else:
    display.waitingToRead()

  # Startin the loop when program starts up
  while True:

    data = display.read_rfid().read_rfid()
    isRead = checkRFData(data)

    if isRead:

      if status == False:
        display.displayRead()

        ids = logger.getIDs()
        startResponse = logger.startLog()

        writeStatus(True)
        status = checkStatus()

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
        writeStatus(False)
        status = checkStatus()
        sleep(10)
        display.waitingToRead()




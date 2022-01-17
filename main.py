from time import sleep
from datetime import date, datetime, timedelta
import os

# Modules
import Modules.logger as logger
import Modules.display as display

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def writeStatus(status):
  PATH = ROOT_DIR + "/status.conf"
  with open(PATH, "w") as f:
    f.write(f"{status}")

def checkRFData(data):
  if data == ("02004819B2E1") or data == ("0D004EC21091"): #TODO add card ID
    display.createSound()
    return True
  else:
    return False

#Incase user forgets to logout
def check9hr():
  PATH = ROOT_DIR + "/login.conf"

  with open(PATH, "r") as f:
    startTime = f.readline()
    startTime = datetime.strptime(startTime,"%d-%m-%Y %H:%M")

    timeToStop = startTime + timedelta(hours=9)
    now = datetime.now()

    if timeToStop < now:
      print("Ended due to TimeLimit")
      endTimer()

# Create a timer
def startTimer():

  startResponse = logger.startLog()
  
  print("Starting Timer")
  display.displayRead()

  writeStatus(True)

  # Logging Start time
  PATH = ROOT_DIR + "/login.conf"
  with open(PATH, "w") as f:
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    f.write(now)
          
  sleep(2)

# End the timer
def endTimer():
  
  endResponse = logger.terminateLog()
  display.displayEnd()
  print("Ending Timer")

  writeStatus(False)

  sleep(3)

# False if timer not running
# True if timer is running
def checkStatus():
  PATH = ROOT_DIR + "/status.conf"

  with open(PATH, "r") as f:
    status = f.readline().rstrip()

    if status == "True":
      display.displayTimer(ROOT_DIR)
      #check9hr()
      return True

    if status == "False":
      display.waitingToRead()
      return False
    
    else:
      writeStatus(False)
      return False

if __name__ == "__main__":

  display.welcomeUser()
  sleep(0.5)

  # Startin the loop when program starts up
  while True:

    status = checkStatus()
    print(f"{status}")

    data = display.read_rfid.read_rfid()
    
    isRead = checkRFData(data)
    print(f"{data} + {isRead}")

    if isRead:
      if status == False:
        startTimer()

      elif status == True:
        endTimer()





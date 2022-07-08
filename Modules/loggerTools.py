from time import sleep
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler

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
      return True

    if status == "False":
      display.waitingToRead()
      return False
    
    else:
      writeStatus(False)
      return False
    
    
# Start the scheduler
def checkTimeJob():
  print("Checking If Timer Is Running ...")
  s = checkStatus()
  if s:
    endTimer()
    response = logger.updateEntryOnLimit()
    print(response)

# Creates the scheduler for the check time at 8pm daily
def createSchedulerForTimeLimit():
  scheduler = Scheduler(timezone="Europe/London")
  #scheduler.add_job(checkTimeJob, 'cron', hour="04", minute="40", id="timeLimitJob")
  scheduler.add_job(checkTimeJob, 'interval', seconds="5") # Testing purposes
  scheduler.start()

# Ensures status & config files are at least present (run once at startup)
def setUpApp():
  PATH1 = ROOT_DIR + "/status.conf"
  PATH2 = ROOT_DIR + "/login.conf"
  
  p1 = open(PATH1, "a+")
  p1.close()
  p2 = open(PATH2, "a+")
  p2.close()
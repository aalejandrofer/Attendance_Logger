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

# False if start entry not entered
# True if timer is running
def checkStatus():
  PATH = os.path.join(ROOT_DIR, 'status.conf')
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
    display.displayTimer(ROOT_DIR)
    return True
  else:
    display.waitingToRead()
    return False

def writeStatus(status):
  PATH = os.path.join(ROOT_DIR, 'status.conf')
  f = open(PATH, "w")
  f.write(f"{status}")
  f.close

def checkRFData(data):
  if data == ("02004819B2E1") or data == ("0D004EC21091"): #TODO add card ID
    display.createSound()
    return True
  else:
    return False

#Incase user forgets to logout
def check9hr():
  PATH = os.path.join(ROOT_DIR, 'login.conf')

  with open(PATH, "r") as f:
    startTime = f.readline()
    startTime = datetime.strptime(startTime,"%d-%m-%Y %H:%M")

    timeToStop = startTime + timedelta(hours=9)
    now = datetime.now()

    print(timeToStop)
    print(now)
    if timeToStop < now:
      endTimer()

# Create a timer
def startTimer():

  startResponse = logger.startLog()
  print("Starting Timer")
  display.displayRead()

  writeStatus(True)

  # Logging Start time
  PATH = os.path.join(ROOT_DIR, 'login.conf')
  with open(PATH, "w+") as f:
    now = datetime.now().strftime("%H")
    f.write(now)
    f.close()

  # Logging to txt file
  with open("RFID.log", "a") as f:
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    f.write(f"{now} : {startResponse}\n")
    f.close()
          
  # Reset
  sleep(10)
  display.displayTimer(ROOT_DIR)

# End the timer
def endTimer():
  
  endResponse = logger.terminateLog()
  print("Ending Timer")

  # Logging to txt file
  with open("RFID.log", "a") as f:
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    #f.write(f"{now} : {startResponse}\n")
    f.write(f"{now} : {endResponse}\n")
    f.close()

    # Back to main stage
    writeStatus(False)
  
    display.displayEnd()

    sleep(10)
    display.waitingToRead()

if __name__ == "__main__":

  display.welcomeUser()
  sleep(0.5)

  # Startin the loop when program starts up
  while True:

    status = checkStatus()

    data = display.read_rfid()
    isRead = checkRFData(data)

    if isRead:
      if status == False:
        startTimer()

      elif status == True:
        endTimer()
    
    if status:
      hour9 = check9hr()
      display.timeCounting()
      if hour9:
        endTimer()





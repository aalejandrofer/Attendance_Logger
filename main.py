from time import sleep
from datetime import date, datetime

# Modules
import Modules.logger as logger
import Modules.display as display

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests

# False if start entry not entered
# True if timer is running

def checkStatus():
  PATH = "./lastStatus.txt"
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
    display.displayTimer()
    return True
  else:
    display.waitingToRead()
    return False

def writeStatus(status):
  PATH = "./lastStatus.txt"
  f = open(PATH, "w")
  f.write(f"{status}")
  f.close

def checkRFData(data):
  if data == ("02004819B2E1") or data == ("02004819B2E1"): #TODO add card ID
    display.createSound()
    display.displayRead()
    return True
  else:
    return False

#Incase user forgets to logout
def check9hr():
  PATH = "./lastCheckIn.txt"

  with open(PATH, "r") as f:
    now = datetime.now().strftime("%H")
    startTime = f.readline().rstrip()

    difference = int(now) - int(startTime)

    if difference >= 9:
      endTimer()

# Create a timer
def startTimer():

  startResponse = logger.startLog()

  writeStatus(True)

  # Logging Start time
  PATH = "./lastCheckIn.txt"
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
  display.displayTimer()

# End the timer
def endTimer():
  
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
      if hour9:
        endTimer()





#!/usr/bin/python3

from operator import lt
from time import sleep

# Modules
import Modules.display as display
import Modules.loggerTools as lT

# Coded in Python 3.8
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install requests apscheduler

if __name__ == "__main__":

  display.welcomeUser()
  sleep(0.5)
  
  # Background Task to Check if Timer Still Running After Working Hours
  ## If Timer running after 8pm, it will stop the timer
  lT.createSchedulerForTimeLimit()
  
  lT.setUpApp() # Checks that config files exist

  # Startin the loop when program starts up
  while True:

    status = lT.checkStatus()
    print("Status: True(Running) False(Timer Not Running)")
    print(f"Waiting to Read : Current Status {status}\n")

    data = display.read_rfid.read_rfid()
    
    isRead = lT.checkRFData(data)
    print(f"{data} + {isRead}\n")

    if isRead:
      if status == False:
        print("Starting Timer")
        lT.startTimer()

      elif status == True:
        print("Ending Timer")
        lT.endTimer()




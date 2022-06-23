from telnetlib import STATUS
from time import sleep
import datetime

# Modules
import Modules.logger as logger
import Modules.redisDB.redisDB as redisDB
# import Modules.display as display #TODO only be run while connected to the PI

# Coded in Python 3.10
# Install Pip3 to get the requests dependancy
# Example: sudo apt-get -y install python3-pip python3 && pip3 install redis

# Checks for the RFID stags that are set for this project
def checkRFData(data):
  if data == ("02004819B2E1") or data == ("0D004EC21091"): #TODO add card ID
    # display.createSound() #TODO only be run while connected to the PI
    return True
  else:
    return False

if __name__ == "__main__":

  #display.welcomeUser() #TODO only be run while connected to the PI
  sleep(0.5)

  # Startin the loop when program starts up
  while True:

    #display.waitingToRead()

    time, lastStatus = logger.logger().readTimeEntry()

    if lastStatus == 1:
      x = redisDB.redisDB().read("hash", "config")
      print("Running")
      #display.displayTimer(x[b"lastStart"]) #TODO only be run while connected to the PI
    
    #data = display.read_rfid.read_rfid() #TODO only be run while connected to the PI
    
    #isRead = checkRFData(data)
    #print(f"{data} + {isRead}")

    isRead = True #TODO dev only

    if isRead:
      
      #display.displayRead()

      streamTime, lastStatus = logger.logger().readTimeEntry() # Represents the Last 2 time entries # If status True, then the last 2 entries match start and end

      # Create Tasks based on lastStatus
      # # 0 = Day is Done
      # # 1 = Day is not Done
      # # 2 = Error

      if lastStatus == 0:
        continue
      elif lastStatus == 1:
        continue
      elif lastStatus == 2:
        continue

      break #TODO dev only
    
    sleep(3) # Wait until it reads from device again
    
    

    





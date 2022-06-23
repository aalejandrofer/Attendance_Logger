from time import sleep

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

# In case of restart or power loss or wrong read, save current status
def checkStatus():
  # Status written on database
  lastStatus = redisDB.redis().read("hash", "config")
  return lastStatus[b'lastStatus']

if __name__ == "__main__":

  #display.welcomeUser() #TODO only be run while connected to the PI
  sleep(0.5)

  # Startin the loop when program starts up
  while True:

    #display.waitingToRead()

    lastStatus = checkStatus()

    if lastStatus == b"Running":
      x = redisDB.redis().read("hash", "config")
      print(x[b'lastStart'])
      #display.displayTimer(x[b'lastStart']) #TODO only be run while connected to the PI
    
    #data = display.read_rfid.read_rfid() #TODO only be run while connected to the PI
    
    #isRead = checkRFData(data)
    #print(f"{data} + {isRead}")

    isRead = True #TODO dev only

    if isRead:
      
      #display.displayRead()
      
      t = logger.logger().readTimeEntry() # Represents the Last 2 time entries # If status True, then the last 2 entries match start and end

      # if t["status"]:
      #   # Starting a new Day : Start New Day
      #   print("Day Completed")
      #   # Start Timer - create new start entry and set lastStatus to Running
      #   exit(0)
      
      # else:
      #   # Current Day is Running : End Day
      #   print("Day Running")
      #   # End Timer - create new end entry and set lastStatus to NotRunning
      #   exit(1)

    else:
      # incorrect read
      print("error reading, device not registered") #TODO implement simple logging system
      #display.displayWronRead()
    
    sleep(3) # Wait until it reads from device again
    
    

    





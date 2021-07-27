from time import sleep
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
sleep(120)
endResponse = logger.terminateLog()

print(startResponse)
print(endResponse)

  

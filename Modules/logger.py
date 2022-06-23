
import Modules.redisDB.redisDB as redisDB
from datetime import date, datetime
import json

class logger():
  
  def __init__(self):
    
    self.r = redisDB.redisDB()

  def startTimer(self, streamTime:dict):
    key = self.todayKey()
    
    return
  
  def endTimer(self, streamTime:dict):
    return
  
  # Creates a key in the format of %y %m %d (220623) from todays date
  def todayKey(self) -> str:    
    return datetime.now().strftime("%y%m%d")
  
  # Create a timestampt from given date
  def createTimestamp(self, date:datetime) -> int:
    return int(round(date.timestamp()))

  # Reads JSON frmo Redis database
  def readTimeEntry(self):
    stream = self.r.read("json", "entries")

    # Grabbing the last date entry
    dicLen = len(stream) - 3 # TODO Template Data grabbing status 1
    lastDate = list(stream.keys())[dicLen] # Grabs the last date
    status = stream[lastDate]["status"]

    # Status Codes
    # # 0 = Done e.g Last Day was Compelted start new timer
    # # 1 = Running e.g Missing end timer, add end timer and mark as done
    # # 2 = Error e.g Time entry exceeds max hours

    return stream, status
  
  
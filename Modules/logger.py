
import Modules.redisDB.redisDB as redisDB
from datetime import datetime
import json

class logger():
  
  def __init__(self):
    
    self.r = redisDB.redisDB()

  def startTimer(self, streamTime:dict):
    todayKey = self.todayKey()
    
    # Data
    starTime = self.createTimestamp(datetime.now())
    data = {"start":starTime, "end":0, "status":1} # status 1 as is not completed only start time added
    
    # Write to database
    self.r.write("json", "entries", todayKey, data)
  
  def endTimer(self, streamTime:dict):
    todayKey = self.todayKey()
    
    # Data
    endTime = self.createTimestamp(datetime.now())
    data = {"start":streamTime[todayKey]["start"] ,"end":endTime, "status":0} # status 0 as is completed

    # Writes JSON to Redis database
    self.r.write("json", "entries", todayKey, data)
  
  # Creates a key in the format of %y %m %d (220623) from todays date
  def todayKey(self) -> str:    
    return datetime.now().strftime("%y%m%d")
  
  # Create a timestampt from given date
  def createTimestamp(self, date:datetime) -> int:
    return int(round(date.timestamp()))

  # From timestamp to date
  def dateFromTimestamp(self, timestamp:int) -> datetime:
    return datetime.fromtimestamp(timestamp)

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
  
  

import Modules.redisDB.redisDB as redisDB
import datetime
import json

class logger():
  
  def __init__(self):
    
    self.r = redisDB.redisDB()

  def startTimer(self, streamTime:dict):
    return
  
  def endTimer(self, streamTime:dict):
    return
  
  def readTimeEntry(self):
    stream = self.r.read("json", "entries")
    print(stream)

    # Grabbing the last date entry
    dicLen = len(stream) - 2
    lastDate = list(stream.keys())[dicLen] # Grabs the last date
    status = stream[lastDate]["status"]

    # Status Codes
    # # 0 = Done e.g Last Day was Compelted start new timer
    # # 1 = Running e.g Missing end timer, add end timer and mark as done
    # # 2 = Error e.g Time entry exceeds max hours

    return stream, status

  
  
  
  
  

import Modules.redisDB.redisDB as redisDB
import time

class logger():
  
  def __init__(self):
    
    self.r = redisDB.redis()

  def startTimer(self):
    return
  
  def endTimer(self):
    return
  
  def readTimeEntry(self):
    stream = self.r.read("json", "entries")
    print(stream)



# THIS METHOD THE PROBLEM IS BECAUSE IS A TIME SET AND THE TIME IS DICTATED BT THE ID, WE CANT MODIFY THE ID THEREFORE WE CANT MODIFY TIMES IF WE NEEDED TO AND WE DO
    # try:
    #   if streamLast2[0][1][b'start'] == streamLast2[1][1][b'end']:
    #     intStart = int(streamLast2[0][0].decode("utf-8").split("-")[0])
    #     intEnd = int(streamLast2[1][0].decode("utf-8").split("-")[0])

    #     timeStart = time.localtime(intStart/1000.0)
    #     timeEnd = time.localtime(intEnd/1000.0)

    #     return {"key": streamLast2[0][1][b'start'], "status": True, "start": timeStart, "end": timeEnd}
        
    # except LookupError:
    #   if streamLast2[1][1][b'start']:

    #     intStart = int(streamLast2[1][0].decode("utf-8").split("-")[0])
    #     timeStart = time.localtime(intStart/1000.0)          
        
    #     return {"key": streamLast2[1][1][b'start'], "status": False, "start": timeStart, "end": "NotSet"}
        
    #   if streamLast2[0][1][b'start']:

    #     raise Exception("Redis DB is corrupted, Missing Data Entries Stuck on Dissagned Time")
    

  
  
  
  
  
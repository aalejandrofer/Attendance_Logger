
import Modules.redisDB.redisDB as redisDB
import time

class logger():
  
  def __init__(self):
    
    self.r = redisDB.redis()

  def start(self):
    stream = self.r.read("stream", "entries")
    print(stream)
    streamLast2 = stream[2:]
    print(streamLast2)

    if streamLast2[0][1][b'start'] == streamLast2[1][1][b'end']:
      intStart = int(streamLast2[0][0].decode("utf-8").split("-")[0])
      intEnd = int(streamLast2[1][0].decode("utf-8").split("-")[0])

      timeStart = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(intStart/1000.0))
      timeEnd = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(intEnd/1000.0))
                                                    

    print(timeStart)
    print(timeEnd)
    
  
  
  
  
  
  
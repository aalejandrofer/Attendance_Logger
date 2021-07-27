from time import sleep
import Modules.logger as logger
import Modules.display as display
import Modules.serial as serial

while True:

  logger.getIDs()

  time, nameOfDay = logger.getTime()
  startResponse = [logger.startEntry(time, nameOfDay), logger.body]
  print(startResponse)

  time, nameOfDay = logger.getTime()
  endResponse = [logger.endEntry(time), logger.body]
  print(endResponse)

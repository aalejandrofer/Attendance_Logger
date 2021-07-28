from oled_091 import SSD1306
from time import sleep
from os import path
import serial
import RPi.GPIO as GPIO

#########################################################
  # FIRST INSTALL
  
    # sudo raspi-config
    #   Now select Interfacing options.
    #   Now we need to select I2C option.
    #   Now select Yes and press enter and then ok.

    # To enable serial
      # select interfacing options.
      # Now we need to select serial.
      # select no to disable serial over login shell.
      # Now select yes to enable serial hardware port then ok.

      # After this step reboot raspberry by typing below command: sudo reboot

    # Install Required Libraries
      # sudo apt-get install python-smbus
      # sudo apt-get install i2c-tools
      # To verify the list of connected device on I2C interface, you can run : sudo i2cdetect -y 1

  ## SOURCE ##
  # https://github.com/sbcshop/SB-RFID-HAT #
#########################################################

## SOURCE of Part of the Code ##
# https://github.com/sbcshop/SB-RFID-HAT #

def setUp():

  status = False

  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup(17,GPIO.OUT)

  DIR_PATH = path.abspath(path.dirname(__file__))
  DefaultFont = path.join(DIR_PATH, "Fonts/GothamLight.ttf")

  class read_rfid:
    def read_rfid (self):
        ser = serial.Serial ("/dev/ttyS0")                           #Open named port 
        ser.baudrate = 9600                                            #Set baud rate to 9600
        data = ser.read(12)                                            #Read 12 characters from serial port to data
        if(data != " "):
            GPIO.output(17,GPIO.HIGH)
            sleep(.2)
            GPIO.output(17,GPIO.LOW)
        ser.close ()                                                   #Close port
        data=data.decode("utf-8")
        return data

  return status
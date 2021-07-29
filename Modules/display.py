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

## SOURCE Code ##
# https://github.com/sbcshop/SB-RFID-HAT #

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)

DIR_PATH = path.abspath(path.dirname(__file__))
DefaultFont = path.join(DIR_PATH, "Fonts/GothamLight.ttf")

display = SSD1306()

def read_rfid ():
   ser = serial.Serial ("/dev/ttyS0")
   ser.baudrate = 9600
   data = ser.read(12)
   ser.close ()

   if data.__sizeof__ != 0:
     return True

   return False

def white():
  display.WhiteDisplay()
        
        






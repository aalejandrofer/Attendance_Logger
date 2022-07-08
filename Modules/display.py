from time import sleep
from os import path
from datetime import datetime

try: 
  from Modules.oled_091 import SSD1306
except:
  from oled_091 import SSD1306

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

class read_rfid():
  def read_rfid():
    ser = serial.Serial ("/dev/ttyS0")
    ser.baudrate = 9600
    data = ser.read(12)
    ser.close ()
    data=data.decode("utf-8")
    return data

#Plays read sound
def createSound():
  GPIO.output(17,GPIO.HIGH)
  sleep(.2)
  GPIO.output(17,GPIO.LOW)

def welcomeUser():
  display.DrawRect()
  display.PrintText("Welcome!", cords=(5, 10), FontSize=13)
  display.ShowImage()
  sleep(1)
  display.DrawRect()
  display.PrintText("Loading...", cords=(5, 10), FontSize=13)
  display.ShowImage()

def waitingToRead():
  display.DrawRect()
  display.PrintText("Waiting To Read", cords=(5, 10), FontSize=11)
  display.ShowImage()
        
def displayRead():
  display.DrawRect()
  display.PrintText("ID Read, Starting...", cords=(5, 10), FontSize=11)
  display.ShowImage()

# Where startime is in H:M format (e.g. 08:00)
def displayTimer(startTime:str):
  display.DrawRect()
  display.PrintText("Logged In, Starting Timer", cords=(5, 10), FontSize=11)
  display.ShowImage()
  
  sleep(2)

  display.DrawRect()
  display.PrintText(f"Logged In, : {startTime} :", cords=(5, 10), FontSize=11)
  display.ShowImage()

def displayEnd():
  display.DrawRect()
  display.PrintText("Done, Goodbye!", cords=(5, 10), FontSize=11)
  display.ShowImage()

def displayWronRead():
  display.DrawRect()
  display.PrintText("Wrong Read ... Restarting", cords=(5, 10), FontSize=11)
  display.ShowImage()

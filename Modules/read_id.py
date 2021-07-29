import serial

# CODE FROM
# https://github.com/sbcshop/SB-RFID-HAT/blob/master/rfid.py

def read_rfid2 ():
   ser = serial.Serial ("/dev/ttyS0")                           #Open named port 
   ser.baudrate = 9600                                            #Set baud rate to 9600
   data = ser.read(12)                                            #Read 12 characters from serial port to data
   ser.close ()                                                   #Close port
   data=data.decode("utf-8")

   print(data)
   print(type(data))
   open("./id.txt", "+w").write(data)
   return data                                                    #Return data

id = read_rfid2 ()                                              #Function call   
# Attendance_Logger

Simple and Quick project, using these products:
- Raspberry Pi 4 Model B 2Gb
- RFID HAT for Raspberry Pi (SB Components)

Raspberry Pi OS will run the Pythong file on boot and connect Python with the RFID

Communicates with the https://api.clockify.me/api/v1 API to create a time stamp when it detects an RFI signal

> api_key.txt file needed so python can get the api_key from there, it will read the first line
  > api_key.txt in root folder
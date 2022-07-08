# Attendance_Logger v1 (Using Clockify)
---
### Project using these products:
- Raspberry Pi 4 Model B 2Gb
- RFID HAT for Raspberry Pi (SB Components)
---
Communicates with the https://api.clockify.me/api/v1 API to create a time stamp when it detects an RFI signal

Every 9hrs it will automatically end the timer, avoiding Human Error when forgetting to sign out

It creates a log file with the recent sign ins and sign outs

Program can be restarted mid-run, it makes the use of conf files to store the data

> Place api_key.conf file inside Modules folder.

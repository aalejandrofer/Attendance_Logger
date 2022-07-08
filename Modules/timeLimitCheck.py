import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler

import main

# Start the scheduler
def timeCheckJob():
    print("checking time")
    print(main.checkStatus())

def start():
    scheduler = Scheduler()
    scheduler.add_job(timeCheckJob, 'interval', hours=10, id="timeLimitJob")
    scheduler.start()
    
import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler


# Check Status


# If Status True (Running)

# Start the scheduler
def timeCheckJob():
    print("checking time")

def start():
    scheduler = Scheduler()
    scheduler.add_job(timeCheckJob, 'interval', hours=10, id="timeLimitJob")
    scheduler.start()
    
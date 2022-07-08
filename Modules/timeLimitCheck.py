import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler

# Start the scheduler
def timeCheckJob():
    print("checking time")

def start():
    scheduler = Scheduler()
    scheduler.add_job(timeCheckJob, 'interval', seconds=10, id="timeLimitJob")
    scheduler.start()
    
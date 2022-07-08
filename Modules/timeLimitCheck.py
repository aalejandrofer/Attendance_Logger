import datetime
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Start the scheduler
def timeCheckJob():
    PATH = ROOT_DIR + "/job.conf"
    with open(PATH, "w") as f:
        f.write(f"Yep")

def start():
    scheduler = Scheduler()
    scheduler.add_job(timeCheckJob, 'interval', seconds=5, id="timeLimitJob")
    scheduler.start()
    
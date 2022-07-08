<<<<<<< HEAD
from time import sleep
import requests
=======

import Modules.redisDB.redisDB as redisDB
from datetime import datetime
>>>>>>> e0014044cb5194aa2699cf4a1823661d848339ce
import json
from datetime import datetime, timedelta
import os

<<<<<<< HEAD
from requests.api import get

# Global Params
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
API_PATH = os.path.join(ROOT_DIR, 'api_key.conf')

with open(API_PATH) as f:
  API_KEY = f.readline().rstrip()

CONTENT_TYPE = "application/json"

# Global Variables
headers = {'content-type': CONTENT_TYPE, 'X-Api-Key': API_KEY}
body = {''}
user_name = ''
user_id = ''
workspace_id = ''
project_id = ''
task_id = ''
task_name = ''

## Converting json object to redeable format
def jprint(obj):
  text = json.dumps(obj, sort_keys=True, indent=4)
  print(text)

# Getting the necessary IDs from the API
def getIDs():
  global workspace_id, project_id, user_id, user_name, task_id, task_name

  response = requests.get(
    'https://api.clockify.me/api/v1/user', headers=headers
  )

  response = response.json()

  workspace_id = response['activeWorkspace']
  user_id = response['id']
  user_name = response['name']

  proID = requests.get(
    f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/projects', headers=headers
  )

  proID = proID.json()[0]
  project_id = proID['id']

  taskID = requests.get(
    f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/projects/{project_id}/tasks', headers=headers
  )

  taskID = taskID.json()[0]
  task_id = taskID['id']
  task_name = taskID['name']

  ids = {"workId": workspace_id, "userId":user_id, "username": user_name, "projectId": project_id, "taskId": task_id, "taskName": task_name}

  return ids

# Getting the time now and day of week
def getTime():
  
  #2021-07-27T08:00:00Z
  now = datetime.now()
  format_time = now.strftime(f"%Y-%m-%dT%H:%M:%SZ")
=======
class logger():
  
  def __init__(self):
    
    self.r = redisDB.redisDB()

  def startTimer(self, streamTime:dict):
    todayKey = self.todayKey()
    
    # Data
    starTime = self.createTimestamp(datetime.now())
    data = {"start":starTime, "end":0, "status":1} # status 1 as is not completed only start time added
    
    # Write to database
    self.r.write("json", "entries", todayKey, data)
  
  def endTimer(self, streamTime:dict):
    todayKey = self.todayKey()
    
    # Data
    endTime = self.createTimestamp(datetime.now())
    data = {"start":streamTime[todayKey]["start"] ,"end":endTime, "status":0} # status 0 as is completed

    # Writes JSON to Redis database
    self.r.write("json", "entries", todayKey, data)
>>>>>>> e0014044cb5194aa2699cf4a1823661d848339ce
  
  nameOfDay = datetime.now().strftime('%A')
  
  return format_time, nameOfDay

<<<<<<< HEAD
# Creating a new time entry
def startEntry(time, nameOfDay):
  global body
=======
  # From timestamp to date
  def dateFromTimestamp(self, timestamp:int) -> datetime:
    return datetime.fromtimestamp(timestamp)

  # Reads JSON frmo Redis database
  def readTimeEntry(self):
    stream = self.r.read("json", "entries")
>>>>>>> e0014044cb5194aa2699cf4a1823661d848339ce

  now = datetime.now()
  formatNow = now.strftime("%H:%M:%S")
  day = datetime.now().day

  if day == 1 or day == 21 or day == 31:
    day = f"{day}st"
  elif day == 2 or day == 22:
    day = f"{day}nd"
  elif day == 3 or day == 23:
    day = f"{day}rd"
  else:
    day = f"{day}"

  description = f"{nameOfDay} {day} at {formatNow}"

  body = {
    "start":time,
    "billable":"false",
    "description":description,
    "projectId":project_id,
    "taskId":task_id
  }

  response = requests.post(f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/time-entries', data=json.dumps(body), headers=headers)
  return response

# Ending the time entry
def endEntry(time):

  global body

  body = {
    "end":time,
  }

  response = requests.patch(f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user_id}/time-entries', data=json.dumps(body), headers=headers)
  return response

# Starts the entry logger
def startLog():
  ids = getIDs()
  time, nameOfDay = getTime()
  startResponse = [startEntry(time, nameOfDay), body]
  return startResponse

# Ends the entry logger
def terminateLog():
  ids = getIDs()
  time, nameOfDay = getTime()
  endResponse = [endEntry(time), body]
  return endResponse
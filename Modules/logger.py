from pydoc import describe
import requests
import json
from datetime import datetime, timedelta
import os

# Global Params
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
API_PATH = os.path.join(ROOT_DIR, 'api_key.conf')

with open(API_PATH) as f:
  API_KEY = f.readline().rstrip()

CONTENT_TYPE = "application/json"

# Global Variables
headers = {'content-type': CONTENT_TYPE, 'X-Api-Key': API_KEY}
body = {}
user_name = ''
user_id = ''
workspace_id = ''
project_id = ''
task_id = ''
task_name = ''
entry_id = ''

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
  
  nameOfDay = datetime.now().strftime('%A')
  
  return format_time, nameOfDay

# Creating a new time entry
def startEntry(time, nameOfDay):
  global body

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
    "billable":"true",
    "description":description,
    "projectId":project_id,
    "taskId":task_id
  }

  response = requests.post(f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/time-entries', data=json.dumps(body), headers=headers)
  
  return response

def updateEntryOnLimit():
  global body
  
  body = {
    "start":"2022-07-07T14:00:37Z",
    "billable":"true",
    "description":"lol",
    "projectId":project_id,
    "taskId":task_id,
    "end":body["end"]
  }
  
  body['description'] = body["description"] + ' // Limit Reached!'
  
  print(body)
  
  print(entry_id)
  
  # https://api.clockify.me/api/v1/workspaces/{{workspaceID}}/time-entries/{{testEntryID}}
  response = requests.put(f"https://api.clockify.me/api/v1/workspaces/{workspace_id}/time-entries/{id}", data=json.dumps(body), headers=headers)
  print(response)
  print(response.json())
  
  return response

# Ending the time entry
def endEntry(time):
  global body, entry_id

  localBody = {
    "end":time,
  }

  response = requests.patch(f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user_id}/time-entries', data=json.dumps(localBody), headers=headers)

  response = response.json()
  body["end"] = time
  
  entry_id = response['id']
  
  print(entry_id)
  
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
from time import sleep
import requests
import json
from datetime import date, datetime

from requests.models import Response

# Global Params
API_KEY = ''
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

# Getting the time now and day of week
def getTime():

  now = datetime.now()
  nameOfDay = datetime.now().strftime('%A')
  
  #2021-07-27T08:00:00Z
  hour = int(now.strftime("%H")) - 1
  format_time = now.strftime(f"%Y-%m-%dT{hour}:%M:%SZ")

  return format_time, nameOfDay

# Creating a new time entry
def startEntry(time, nameOfDay):
  global body

  now = datetime.now()
  formatNow = now.strftime("%H:%M:%S")

  description = f"{nameOfDay} {formatNow}"

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
def endEntry(time, nameOfDay):
  global body

  body = {
    "end":time,
  }

  response = requests.patch(f'https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user_id}/time-entries', data=json.dumps(body), headers=headers)
  return response

def main():

  getIDs()

  time, nameOfDay = getTime()
  startResponse = [startEntry(time, nameOfDay), body]
  print(startResponse)

  sleep(10)

  time, nameOfDay = getTime()
  endResponse = [endEntry(time, nameOfDay), body]
  print(endResponse)

main()
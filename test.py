from datetime import datetime

def check9hr():
  PATH = "./lastCheckIn.txt"

  with open("./lastCheckIn.txt", "w+") as f:
    now = datetime.now().strftime("%H")
    f.write(now)
    f.close()

  with open(PATH, "r") as f:
    now = datetime.now().strftime("%H")
    startTime = datetime.strftime(f.readline().rstrip(), "%H")

    difference = startTime - now

    print(difference)
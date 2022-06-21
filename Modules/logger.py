
import firebase.firestore as db

class logger():
  
  def __init__(self):
    
    data = db.firestore.readDb("config")
    
    print(data)
    
  
  
  
  
  
  
import string
from weakref import ref
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class firestore():
  
  def __init__(self):  
    # Use a service account
    self.cred = credentials.Certificate("./serviceAccount.json")
    firebase_admin.initialize_app(self.cred)

    self.db = firestore.client()
    self.ref = 1
  
  def readDb(self, colletion:string):
    db_ref = self.db.collection(colletion)
    data = db_ref.stream()

    return data
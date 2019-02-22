import os
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore

from firebase.config import config, firebase_adminsdk_file


base = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(base + firebase_adminsdk_file)
firebase_admin.initialize_app(cred, config)

db = firestore.client()

def get_last_id():
  refConfig = db.collection(u'config').document('global')
  doc = refConfig.get().to_dict()
  return doc['lastId']

def set_last_id(last_id):
  refConfig = db.collection(u'config').document('global')
  refConfig.update({ 'lastId': last_id })

def save_anime(id, data):
  db.collection(u'animes').document(str(id)).set(data) # autogenerate id
  set_last_id(id)

# doc['idsError'].append(current_id)
# refConfig.update({ 'idsError': doc['idsError'] })

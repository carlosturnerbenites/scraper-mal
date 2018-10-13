import requests
from bs4 import BeautifulSoup
from exceptions import MissingTagError, ParseError
from scraper import get_url_anime, get_anime_data
import json
import itertools

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

from firebase.config import config, firebase_adminsdk_file

cred = credentials.Certificate(os.getcwd() + firebase_adminsdk_file)
firebase_admin.initialize_app(cred, config)

# from firebase_admin import db????????

db = firestore.client()

refConfig = db.collection(u'config').document('global')
doc = refConfig.get().to_dict()
last_id = doc['lastId']

# for current_id in range(last_id, last_id + 10):
current_id = 1
try:
    url = get_url_anime(current_id)
    page = requests.get(url)
except requests.exceptions.HTTPError as err:
    code = err.response.status_code
    if code == 404:
        print("404 Error")
    else:
        print("Other HTTP Error")
else:
    soup = BeautifulSoup(page.content, 'html.parser')
    print(soup.prettify().encode('utf8'))
    try:
        data = get_anime_data(soup)
        data['id'] = current_id
        data['reviewed'] = False
        data['score'] = 0
        print(json.dumps(data, sort_keys=True, indent=4))
        # db.collection(u'animes').document(str(current_id)).set(data) # autogenerate id
        # refConfig.update({ 'lastId': current_id })
    except:
        # doc['idsError'].append(current_id)
        # refConfig.update({ 'idsError': doc['idsError'] })
        pass

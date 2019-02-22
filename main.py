import requests
from scraper.scraper import get_anime
import json

from firebase.client import get_last_id, save_anime

last_id = get_last_id()
print(last_id)

# current_id = 1
for current_id in range(last_id, last_id + 50):
    try:
        response = get_anime(current_id)
    except requests.exceptions.HTTPError as err:
        code = err.response.status_code
        if code == 404:
            print("404 Error")
        else:
            print("Other HTTP Error")
    else:
        data = response.data

        data['id'] = current_id
        # data['reviewed'] = False
        # data['score'] = 0

        print(json.dumps(data, sort_keys=True, indent=4))

        save_anime(current_id, data)


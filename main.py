from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

API_KEY = os.environ.get('API_KEY')

r = requests.get('https://api.utdnebula.com/section', headers={
    'x-api-key': API_KEY,
    'Accept': 'application/json',
}, params={
    'academic_session.name': '23F',
    'meetings.location.building': 'SCI',
    # 'instruction_mode': 'hybrid',
})

print(r.status_code)

obj = json.loads(r.text)

print(len(obj['data']))

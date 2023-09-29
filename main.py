from dotenv import load_dotenv
load_dotenv()

import os
import requests

API_KEY = os.environ.get('API_KEY')

r = requests.get('https://api.utdnebula.com/section', headers={
    'x-api-key': API_KEY,
    'Accept': 'application/json',
}, params={
    'meetings.location.building': 'SCI',
    # 'instruction_mode': 'hybrid',
})

print(r.status_code)
print(r.content)

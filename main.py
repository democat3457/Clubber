from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

API_KEY = os.environ.get('API_KEY')

def make_request(path: str, params: dict = {}):
    return requests.get(f'https://api.utdnebula.com/{path}', headers={
        'x-api-key': API_KEY,
        'Accept': 'application/json',
    }, params=params)

def find_by_id(type: str, id: str):
    return make_request(f'{type}/{id}')

def main():
    r = make_request('section', params={
        'academic_session.name': '23F',
        'meetings.location.building': 'SLC',
        'meetings.location.room': '1.102',
        'meetings.meeting_days': 'Monday',
        'meetings.start_time': '0000-01-01T10:00:00-05:50',
        # 'instruction_mode': 'hybrid',
    })

    print(r.status_code)

    obj = json.loads(r.text)

    print(obj['data'][0])

    print(len(obj['data']))

if __name__ == '__main__':
    main()

from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

API_ROOT = 'https://api.utdnebula.com'
# API_ROOT = 'http://localhost:8080'
API_KEY = os.environ.get('API_KEY')

def make_request(path: str, params: dict = {}):
    return requests.get(f'{API_ROOT}/{path}', headers={
        'x-api-key': API_KEY,
        'Accept': 'application/json',
    }, params=params)

def find_by_id(type: str, id: str):
    return make_request(f'{type}/{id}')

def main():
    c = make_request('course', params={
        'subject_prefix': 'MATH',
        'course_number': '2417',
        'catalog_year': '22',
    })

    obj = json.loads(c.text)['data']
    # print(obj)

    r = make_request('section', params={
        'academic_session.name': '22F',
        # 'section_number': '0H1',
        # 'course_reference': obj[0]['_id']
        'meetings.location.building': 'HH',
        'meetings.location.room': '2.402',
        'meetings.meeting_days': 'Tuesday',
        'meetings.start_time': '0000-01-01T16:00:00-05:50',
        # 'instruction_mode': 'hybrid',
    })

    print(r.status_code)

    obj = json.loads(r.text)

    print(obj['data'][0])

    print("Length:", len(obj['data']))

if __name__ == '__main__':
    main()

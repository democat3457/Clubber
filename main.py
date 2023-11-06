from typing import Optional
from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests

from tqdm import tqdm

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


def find_sections_of_course(prefix:str, number:str|int, year:str|int, semester:str):
    c = make_request('course', params={
        'subject_prefix': prefix,
        'course_number': str(number),
        'catalog_year': str(year),
    })
    course_id = json.loads(c.text)['data'][0]['_id']

    r = make_request('section', params={
        'academic_session.name': str(year)+semester,
        'course_reference': course_id,
    })

    return json.loads(r.text)['data']

def find_all_sections(session:Optional[str]=None, *,
                      building:Optional[str]=None,
                      room:Optional[str]=None,
                      meeting_days:Optional[str|list[str]]=None):
    base_params = {}
    if session is not None:
        base_params['academic_session.name'] = session
    if building is not None:
        base_params['meetings.location.building'] = building
    if room is not None:
        base_params['meetings.location.room'] = room
    if meeting_days is not None:
        base_params['meetings.meeting_days'] = str(meeting_days)
    
    sections = []

    t = tqdm()
    offset = 0
    while True:
        r = make_request('section', params=dict(offset=str(offset), **base_params))
        obj = json.loads(r.text)['data']
        if obj is None:
            break
        sections.extend(obj)
        offset += 20
        t.update(len(obj))
    return sections


def main():
    sections = []
    while True:
        s = input()
        if s == 'exit':
            break
        if s.startswith('query'):
            amnt = 0
            if ' ' in s:
                amnt = int(s.split(' ')[1])
            if amnt > 0:
                print(json.dumps(sections[:amnt], indent=2))
            else:
                print(json.dumps(sections, indent=2))
        else:
            params = {}
            for part in s.split():
                if '=' in part:
                    params[part.split('=')[0]] = part.split('=')[1]
            sections = find_all_sections(**params)
            print(f'Found {len(sections)} sections, enter "query" to show.')

    sections = find_all_sections(building='ECSS', room='2.102')
    print(len(sections))

    # r = make_request('section', params={
    #     'academic_session.name': '22F',
    #     # 'section_number': '0H1',
    #     # 'course_reference': obj[0]['_id']
    #     'meetings.location.building': 'HH',
    #     'meetings.location.room': '2.402',
    #     'meetings.meeting_days': 'Tuesday',
    #     'meetings.start_time': '0000-01-01T16:00:00-05:50',
    #     # 'instruction_mode': 'hybrid',
    # })

    # print(r.status_code)

    # obj = json.loads(r.text)

    # print(obj['data'][0])

    # print("Length:", len(obj['data']))

if __name__ == '__main__':
    main()

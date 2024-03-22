from typing import Any, Optional
from dotenv import load_dotenv
load_dotenv()

import os
import json
import pickle
import requests
from pathlib import Path
from datetime import datetime, time
from collections import defaultdict

from tqdm import tqdm

API_ROOT = 'https://api.utdnebula.com'
# API_ROOT = 'http://localhost:8080'
API_KEY = os.environ.get('NEBULA_API_KEY')

CACHE_FILE = Path(datetime.now().strftime('%Y%m%d-%H%m%s')+'.cache')
request_cache = {}

def make_request(path: str, params: dict = {}):
    p = (path, frozenset(params.items()))
    if p in request_cache:
        return request_cache[p]

    response = requests.get(f'{API_ROOT}/{path}', headers={
        'x-api-key': API_KEY,
        'Accept': 'application/json',
    }, params=params)
    data = json.loads(response.text)['data']

    if data == 'mongo: no documents in result':
        data = None

    request_cache[p] = data

    return data

def find_by_id(type: str, id: str):
    return make_request(f'{type}/{id}')

def from_go_datetime(dt: str):
    return datetime.fromisoformat(dt.replace('0000', '0001'))
def to_go_datetime(dt: datetime):
    return dt.isoformat()
def from_go_time(t: str):
    try:
        # v1 times : go format
        return from_go_datetime(t).time()
    except:
        # v2 times : standard format
        return datetime.strptime(t, '%I:%M%p').time()
def to_go_time(t: time):
    # return '0000-01-01T'+t.isoformat()+'-05:50'
    return t.strftime('%I:%M%p')


def get_course_from_section(section):
    r = find_by_id('course', section['course_reference'])
    data = r
    if data is None:
        print(f'ERROR: no course found for section {section["_id"]}: course ref {section["course_reference"]}')
        return None
    return data

def find_sections_of_course(prefix:str, number:str|int, year:str|int, semester:str):
    course_id = make_request('course', params={
        'subject_prefix': prefix,
        'course_number': str(number),
        'catalog_year': str(year),
    })[0]['_id']

    r = make_request('section', params={
        'academic_session.name': str(year)+semester,
        'course_reference': course_id,
    })

    return r

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
        obj = make_request('section', params=dict(offset=str(offset), **base_params))
        if obj is None:
            break
        sections.extend(obj)
        offset += 20
        t.update(len(obj))
    return sections

def save_cache():
    if len(request_cache):
        CACHE_FILE.write_bytes(pickle.dumps(request_cache))

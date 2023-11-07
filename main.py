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
API_KEY = os.environ.get('API_KEY')

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
    return from_go_datetime(t).time()
def to_go_time(t: time):
    return '0000-01-01T'+t.isoformat()+'-05:50'


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


def main():
    sections = []
    query = {}
    while True:
        try:
            s = input('::: ')
            if s == 'exit':
                break
            if s == 'help':
                print('UTD Clubber - Dev Dashboard')
                # print('You can also enter a command to take actions on the current query.')
                print()
                print('  query <params>   request sections from the API, using space-separated')
                print('                   key/value pairs to specify certain attributes.')
                print('                   possible keys: session, building, room, meeting_days')
                print('  show [n]         shows the current query results. if n is specified,')
                print('                   shows up to n queries. n can also be "length", which')
                print('                   shows the size of the query results.')
                print('  schedule [days]  lists the dates, times, and classes of the query')
                print('                   results. if days is specified (space-separated list),')
                print('                   only shows schedule for those days; otherwise, shows')
                print('                   entire week Mon-Sun.')
                print('  export           exports current query result to a json file.')
                print('  exit             exits the program.')
            elif s.startswith('show'):
                amnt = 0
                if 'length' in s:
                    print(f'Found {len(sections)} sections')
                    continue
                if ' ' in s:
                    amnt = int(s.split(' ')[1])
                if amnt > 0:
                    print(json.dumps(sections[:amnt], indent=2))
                else:
                    print(json.dumps(sections, indent=2))
            elif s == 'export':
                name = "query"
                values = []
                if not len(query):
                    values = ["All"]
                for key in ('session', 'building', 'room', 'meeting_days'):
                    if key in query:
                        value = query[key]
                        if isinstance(value, list):
                            value = ''.join(value)
                        values.append(value)
                name += '_'.join(values)
                name = name.replace('.', '-')
                Path(name+'.json').write_text(json.dumps(sections, indent=2))
            elif s.startswith('schedule'):
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                if ' ' in s:
                    days = s.split()[1:]
                day_sections: dict[str, list[tuple[time, Any, Any]]] = defaultdict(list)
                for section in sections:
                    if 'meetings' in section:
                        for meeting in section['meetings']:
                            for meeting_day in meeting['meeting_days']:
                                if meeting_day in days:
                                    day_sections[meeting_day].append((from_go_time(meeting['start_time']), section, meeting))
                for day in days:
                    sorted_sections = sorted(day_sections[day], key=lambda x: x[0])
                    for t, section, meeting in sorted_sections:
                        course = get_course_from_section(section)
                        if course is not None:
                            section_title = f"{course['subject_prefix']}{course['course_number']}.{section['section_number']}"
                        else:
                            section_title = f"???.{section['section_number']}"
                        print(day, f'{t.isoformat()}-{from_go_time(meeting["end_time"]).isoformat()}', section_title)
            elif s.startswith('query'):
                s = s.replace('query', '').strip()
                params = {}
                for part in s.split():
                    if '=' in part:
                        params[part.split('=')[0]] = part.split('=')[1]
                    else:
                        # invalid query
                        break
                else:
                    query = params
                    sections = find_all_sections(**params)
                    print(f'Found {len(sections)} sections.')
                    continue
                print('Malformed query!')
                continue
            else:
                if s:
                    print(f'clbr: command not found: {s.split()[0]}')
        except KeyboardInterrupt:
            pass
        except EOFError:
            break

    if len(request_cache):
        CACHE_FILE.write_bytes(pickle.dumps(request_cache))

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

if __name__ == '__main__':
    main()

from typing import Any
from dotenv import load_dotenv
load_dotenv()

import json
from pathlib import Path
from datetime import datetime, time
from collections import defaultdict

import simplekml

import nebula
import concept3d

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
                print('  draw             highlights current building or room and exports to')
                print('                   a kml file.')
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
                name += '.json'
                Path(name).write_text(json.dumps(sections, indent=2))
                print(f'Saved to {name}.')
            elif s.startswith('draw'):
                args = s.split()[1:]
                building_code = ''
                if not len(args) and 'building' in query:
                    building_code = query['building']
                elif len(args):
                    building_code = args[0]
                if not building_code:
                    print('No building in query found!')
                    continue
                interior = concept3d.get_building_interior(building_code)
                if interior is None:
                    print(f'Unable to find rooms for building {building_code}')
                    continue
                ground_floor = interior['level']
                def proc_room(room):
                    kml = concept3d.draw_kml(building_code, room=room)
                    kml_name = f'{building_code}{room}'.replace('.','_')
                    return kml, kml_name
                def proc_floor(floor):
                    kml = concept3d.draw_kml(building_code, floor=floor)
                    kml_name = f'{building_code}floor{floor}'
                    return kml, kml_name
                if not len(args):
                    if 'room' in query:
                        kml, kml_name = proc_room(query['room'])
                    else:
                        kml, kml_name = proc_floor(ground_floor)
                else:
                    if len(args) == 2:
                        if '.' in args[1]:
                            kml, kml_name = proc_room(args[1])
                        else:
                            kml, kml_name = proc_floor(args[1])
                    else:
                        kml, kml_name = proc_floor(ground_floor)
                kml_name += '.kml'
                kml.save(kml_name)
                print(f'Saved kml to {kml_name}')
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
                                    day_sections[meeting_day].append((nebula.from_go_time(meeting['start_time']), section, meeting))
                for day in days:
                    sorted_sections = sorted(day_sections[day], key=lambda x: x[0])
                    for t, section, meeting in sorted_sections:
                        course = nebula.get_course_from_section(section)
                        if course is not None:
                            section_title = f"{course['subject_prefix']}{course['course_number']}.{section['section_number']}"
                        else:
                            section_title = f"???.{section['section_number']}"
                        meeting_room = '' if 'room' in query and 'building' in query else f' {meeting["location"]["building"]} {meeting["location"]["room"]}'
                        print(f'{day}{meeting_room} {t.isoformat()}-{nebula.from_go_time(meeting["end_time"]).isoformat()} {section_title}')
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
                    sections = nebula.find_all_sections(**params)
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

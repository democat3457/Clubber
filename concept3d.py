from typing import Optional
from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests
import urllib.parse

import simplekml

API_ROOT = 'https://api.concept3d.com'
API_KEY = os.environ.get('MAP_API_KEY')
MAP_NUMBER = 1772
CATEGORY_INTERIOR = 52264

def make_request(path: str, params: dict = {}):
    params_dict = dict(
        map=MAP_NUMBER,
        key=API_KEY,
        **params
    )
    params_str = '&'.join(f'{k}={v}' if v is not None else str(k) for k,v in params_dict.items())
    response = requests.get(f'{API_ROOT}/{path}', params=params_str)
    data = json.loads(response.text)

    return data

def find_category(category_id: int, params: dict = {}) -> dict:
    return make_request(f'categories/{category_id}', params=dict(children=None, **params))

def find_location(location_id: int, params: dict = {}) -> dict:
    return make_request(f'locations/{location_id}', params=dict(children=None, **params))

def search(query: str, num: int|None = None) -> list[dict]:
    q = urllib.parse.quote(query)
    if num is None:
        o = make_request('search', params=dict(q=q, ppage=1))
        total_found = o['totalFound']
        return make_request('search', params=dict(q=q, ppage=total_found))['data']
    else:
        return make_request('search', params=dict(q=q, ppage=num))['data']

# TODO: wayfinding?
# https://api.concept3d.com/wayfinding/?map=1772&v2=true&toLat=32.99151664964702&toLng=-96.75121201281732&toLevel=-1&currentLevel=-1&stamp=MfWP0jYm&fromLevel=0&fromLat=32.9878185&fromLng=-96.7479817&key=0001085cc708b9cef47080f064612ca5

def get_building_interior(building_code: str):
    interiors = find_category(CATEGORY_INTERIOR)
    for category in interiors['children']['categories']:
        if f'({building_code})' in category['name']:
            return find_category(category['catId'])
    return None


def get_paths(room_dict: dict) -> list[tuple[float, float]]:
    if 'shape' in room_dict:
        shape = room_dict['shape']
        if shape['type'] == 'polygon':
            return [tuple(p) for p in shape['paths']]
        elif shape['type'] == 'rectangle':
            (boundY1, boundX1), (boundY2, boundX2) = shape['bounds']
            return [(boundY1, boundX1),
                    (boundY2, boundX1),
                    (boundY2, boundX2),
                    (boundY1, boundX2)]
    return []

def draw_kml(building_code: str, *, room: Optional[str]=None, floor: Optional[str|int]=None):
    highlight_query = f'{building_code} {room}' if room else ''  # room
    filter_query = f'{building_code} {room.split(".")[0] if room else floor}'  # floor
    interior = get_building_interior(building_code)
    if interior is None:
        return None
    else:
        kml = simplekml.Kml()
        normal_color = simplekml.Color.black
        highlight_color = simplekml.Color.hex('e87400')
        found_highlight = False
        for room in interior['children']['locations']:
            if filter_query in room['name']:
                highlight = False
                if highlight_query and highlight_query in room['name']:
                    found_highlight = True
                    highlight = True
                paths = get_paths(room)
                coords = [(lon, lat) for lat, lon in paths]
                coords.append(coords[0])
                line = kml.newlinestring(name=room['name'], coords=coords)
                line.linestyle.color = highlight_color if highlight else normal_color
                line.linestyle.width = 4 if highlight else 2
        if highlight_query and not found_highlight:
            print(f"Unable to find room {highlight_query}")
        return kml

from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests
import urllib.parse

API_ROOT = 'https://api.concept3d.com'
API_KEY = os.environ.get('MAP_API_KEY')
MAP_NUMBER = 1772

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

# todo: wayfinding?
# https://api.concept3d.com/wayfinding/?map=1772&v2=true&toLat=32.99151664964702&toLng=-96.75121201281732&toLevel=-1&currentLevel=-1&stamp=MfWP0jYm&fromLevel=0&fromLat=32.9878185&fromLng=-96.7479817&key=0001085cc708b9cef47080f064612ca5


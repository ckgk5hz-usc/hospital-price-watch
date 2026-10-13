"""Small file for the home-page map: only what the map needs (keeps the home page light). Run from the repo root."""
import json
d = json.load(open('data/hospitals.json'))
out = [{'name': h['name'], 'city': h.get('city'), 'county': h.get('county'), 'lat': h['lat'], 'lon': h['lon'],
        'licensed_beds': h.get('licensed_beds'), 'operating_margin': h.get('operating_margin'), 'is_general_acute': h.get('is_general_acute')}
       for h in d['hospitals'] if h.get('lat') is not None]
s = json.dumps({'note': 'Subset of hospitals.json for the home-page map (FY2023 operating margin).', 'hospitals': out}, allow_nan=False, separators=(',', ':'))
open('data/hospitals_map.json', 'w').write(s); print(len(out), 'hospitals', len(s)//1024, 'KB')

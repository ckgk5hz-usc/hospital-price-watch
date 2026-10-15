"""Small file for the home-page map: yearly arrays (FY2012-24) of the few measures the map cycles through. Run from the repo root."""
import json
Y = list(range(2012, 2025)); KEYS = ['operating_margin', 'uncompensated_care_rate', 'medical_discharge_share', 'natural_births']
d = json.load(open('data/hospitals.json')); mat = json.load(open('data/maternity.json'))
def series(h, k): return [h.get('annual', {}).get(str(y), {}).get(k) for y in Y]
out = []
for h in d['hospitals']:
    if h.get('lat') is None: continue
    r = {'name': h['name'], 'city': h.get('city'), 'county': h.get('county'), 'lat': h['lat'], 'lon': h['lon'], 'licensed_beds': h.get('licensed_beds'),
         'is_general_acute': h.get('is_general_acute'), 'operating_margin': h.get('operating_margin')}
    for k in KEYS: r[k] = series(h, k)
    out.append(r)
s = json.dumps({'note': 'Subset of hospitals.json for the home-page map. Arrays are FY2012-FY2024.', 'years': Y, 'hospitals': out, 'maternity_losses': mat['items']}, allow_nan=False, separators=(',', ':'))
open('data/hospitals_map.json', 'w').write(s); print(len(out), 'hospitals', len(s)//1024, 'KB')

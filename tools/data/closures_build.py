"""Assemble data/closures.json from data/closure_candidates.csv + the researched verdicts in closures_verdicts.py.
Geocodes to Census Gazetteer place centroids (city centers). Run from the repo root:  python3 tools/data/closures_build.py <gazetteer.txt>"""
import sys, csv, json, re, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from closures_verdicts import V
gaz = sys.argv[1]
places = {}
for line in open(gaz, encoding='latin-1'):
    f = line.rstrip('\n').split('\t')
    if f[0] != 'CA': continue
    nm = re.sub(r' (city|CDP|town)$', '', f[3]).strip().upper().replace('SAINT ', 'ST ').replace('ST. ', 'ST ')
    places.setdefault(nm, []).append((float(f[10]), float(f[11]), f[4]))
ALIAS = {'LOS ANGELES': 'LOS ANGELES', 'VENTURA': 'SAN BUENAVENTURA (VENTURA)'}
geo = json.load(open('data/ca_counties.geojson'))
def rings(g): return g['coordinates'] if g['type'] == 'Polygon' else [r for p in g['coordinates'] for r in p]
def pip(x, y, ring):
    ins = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: ins = not ins
        j = i
    return ins
def county_at(lon, lat):
    for f in geo['features']:
        for r in rings(f['geometry']):
            if pip(lon, lat, r): return f['properties']['name']
    return None
def city_point(city):
    k = city.strip().upper().replace('SAINT ', 'ST ').replace('ST. ', 'ST ')
    k = ALIAS.get(k, k)
    c = places.get(k)
    if not c: return None
    c = sorted(c, key=lambda t: 0 if t[2] == '25' else 1)  # prefer incorporated city
    return c[0][0], c[0][1]
MAPPED = ('closed_permanent', 'ceased_inpatient_converted')
items = []; unmatched = []
for r in csv.DictReader(open('data/closure_candidates.csv')):
    v = V.get(r['oshpd_id'])
    if not v: unmatched.append(r['oshpd_id']); continue
    m = re.search(r'(19|20)\d\d', v['closed_date'] or '')
    cy = int(m.group(0)) if m else None
    lat = lon = None; src = None; cty = v.get('county_override') or r['county'] or None
    if v['status'] in MAPPED + ('closed_then_reopened',):
        pt = city_point(r['city'])
        if pt: lat, lon = round(pt[0], 4), round(pt[1], 4); src = 'census_place_centroid'; cty = cty or county_at(lon, lat)
    items.append(dict(oshpd_id=r['oshpd_id'], name=r['name'].title().replace("'S", "'s"), city=r['city'].title(), county=cty, beds=float(r['beds']) if r['beds'] else None,
        hcai_care=r['hcai_care'], hcai_class=r['hcai_class'], control=r['control'], first_year_filed=int(r['first_year_filed']), last_year_filed=int(r['last_year_filed']),
        status=v['status'], closed_date=v['closed_date'], closed_year=cy, note=v['note'], evidence=v['evidence'], evidence_fetched=v['evidence_fetched'], confidence=v['confidence'],
        lat=lat, lon=lon, geo_source=src, map=bool(v['status'] in MAPPED and lat is not None)))
from collections import Counter
cnt = Counter(i['status'] for i in items)
out = dict(generated=datetime.date.today().isoformat(),
    source='Candidates: California hospitals that filed an HCAI annual financial disclosure in 2012-2023 and then stopped (matched by OSHPD ID in the HCAI multi-year panel). Verdicts: researched from news, state, county and hospital sources listed per row.',
    definition='map:true = verified closure or end of inpatient care. A facility that merely stops filing is not a closure: many are new IDs after a sale, a merger into another license, or a reopening. Only closed_permanent and ceased_inpatient_converted rows are drawn.',
    caveats=['Points are Census place centroids (city centers), not street addresses.', 'closed_year is the year of the closure or conversion, not the last year the facility filed.', "Rows marked cannot_verify are not drawn on the map and are not claimed to be closures.", 'Evidence confidence is low/medium/high; evidence_fetched lists pages that were opened and read, other links came from search summaries.'],
    counts=dict(cnt), items=items)
s = json.dumps(out, indent=1, allow_nan=False); json.loads(s); assert not re.search(r'Infinity|NaN', s)
open('data/closures.json', 'w').write(s)
print(dict(cnt), 'mapped:', sum(i['map'] for i in items), 'unverdicted:', unmatched, 'no-geo:', [i['name'] for i in items if i['status'] in MAPPED and i['lat'] is None])
for i in items:
    if i['map']: print(i['closed_year'], i['name'], '|', i['city'], i['county'], i['lat'], i['lon'])

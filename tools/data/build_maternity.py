"""Adds yearly natural (vaginal) births per hospital (HCAI panel field NAT_BIRTHS, FY2012-24) to data/hospitals.json
and writes data/maternity.json: hospitals whose reported births fell to zero and stayed there.
Inference, not an announcement date: first fiscal year with 0 births after >=100 the year before, zero in every later year filed.
Exclusions: Loma Linda University Medical Center (1,906 births vanish in FY2014, likely reporting under another license) and
San Gabriel Valley Medical Center (FY2024 disclosure file reports 595 births, contradicting the panel's preliminary zero).
Run from repo root with the Issue Brief venv. Needs local OneDrive files, so output JSON is committed."""
import json, math, openpyxl
YEARS = list(range(2012, 2025))
PANEL = '/Users/ckgk5hz/Library/CloudStorage/OneDrive-UniversityofSouthernCalifornia/Melnick/years_data.xlsx'
EXCLUDE = {'106361246': 'Prior births of 1,906 vanish in one year at a large university hospital; probably reported under another license.',
           '106190200': 'FY2024 disclosure file reports 595 total births; the panel zero is preliminary.'}
def num(v):
    try:
        f = float(str(v).replace(',', '').replace('\xa0', '').strip()); return f if math.isfinite(f) else None
    except Exception: return None
d = json.load(open('data/hospitals.json')); H = d['hospitals']; N = {h['oshpd_id']: h for h in H}
wb = openpyxl.load_workbook(PANEL, read_only=True, data_only=True)
B = {}
for y in YEARS:
    r = wb[str(y)].iter_rows(values_only=True); hdr = list(next(r)); i = hdr.index('FAC_NO'); j = hdr.index('NAT_BIRTHS')
    for x in r:
        f = str(x[i]).strip(); f = f[:-2] if f.endswith('.0') else f
        if f in N:
            v = num(x[j])
            if v is not None: B.setdefault(f, {})[y] = int(v)
for h in H:
    for y, v in B.get(h['oshpd_id'], {}).items():
        ann = h.setdefault('annual', {}); ann.setdefault(str(y), {})['natural_births'] = v
items = []
for f, s in B.items():
    ys = sorted(s)
    for a, b in zip(ys, ys[1:]):
        if s[a] >= 100 and s[b] == 0 and all(s[z] == 0 for z in ys if z >= b):
            h = N[f]
            if f in EXCLUDE or h.get('lat') is None: break
            items.append({'oshpd_id': f, 'name': h['name'], 'city': h.get('city'), 'county': h.get('county'), 'lat': h['lat'], 'lon': h['lon'],
                          'last_year_with_births': a, 'births_that_year': s[a], 'first_year_zero': b, 'preliminary': b == 2024})
            break
items.sort(key=lambda c: (c['first_year_zero'], c['name']))
out = {'note': 'Hospitals whose reported natural (vaginal) births fell to zero and stayed there. Inferred from HCAI disclosure data, not from announcements; the unit may have closed earlier in the prior fiscal year. Counts exclude C-section births. Natural births undercount total births by roughly 25 to 30 percent.',
       'context': 'CalMatters counted 56 California hospitals that stopped delivering babies between 2012 and 2024; this list is smaller because it needs 100+ births and a clean persistent zero in this data.',
       'excluded': EXCLUDE, 'items': items}
open('data/maternity.json', 'w').write(json.dumps(out, allow_nan=False, separators=(',', ':')))
open('data/hospitals.json', 'w').write(json.dumps(d, allow_nan=False, separators=(',', ':')))
print(len(items), 'maternity losses;', sum(1 for h in H if any('natural_births' in v for v in h.get('annual', {}).values())), 'hospitals with births series')

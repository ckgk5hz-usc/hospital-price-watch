"""Drop duplicate FY2023 filings: eight hospitals filed two reporting periods under one OSHPD ID (a short stub after a sale or
fiscal-year change). Keep the row covering the longest period. Run from the repo root with the Issue Brief Project venv."""
import sys, json, collections
sys.path.insert(0, '/Users/ckgk5hz/Documents/Claude/Projects/Melnick/Melnick/Issue Brief Project/code')
from hcai_loader import HCAIDataset
ds = HCAIDataset('/Users/ckgk5hz/Library/CloudStorage/OneDrive-UniversityofSouthernCalifornia/Melnick/49hospitaldata.csv')
hh = ds.hospitals(); days = ds.period_days()
d = json.load(open('data/hospitals.json')); H = d['hospitals']
assert len(H) == len(hh), (len(H), len(hh))
# hospitals.json keeps the CSV row order; confirm row i of each is the same filing before using the CSV's period length
for i, h in enumerate(H):
    assert str(h['oshpd_id']).strip() == str(hh.oshpd_id[i]).strip() and h['name'].strip().upper() == hh.name[i].strip().upper(), (i, h['name'])
by = collections.defaultdict(list)
for i, h in enumerate(H): by[h['oshpd_id']].append(i)
drop = set()
for oid, idx in by.items():
    if len(idx) < 2: continue
    idx.sort(key=lambda i: -(0 if days.iloc[i] != days.iloc[i] else int(days.iloc[i])))
    for i in idx[1:]: drop.add(i)
    print('keep', H[idx[0]]['name'], int(days.iloc[idx[0]]), '| drop', [(H[i]['name'], int(days.iloc[i])) for i in idx[1:]])
d['hospitals'] = [h for i, h in enumerate(H) if i not in drop]
d['count'] = len(d['hospitals'])
d['dedupe_note'] = 'Duplicate FY2023 filings removed (kept the longest reporting period per OSHPD ID); %d distinct hospitals.' % d['count']
s = json.dumps(d, allow_nan=False, separators=(',', ':')); open('data/hospitals.json', 'w').write(s)
print('now', d['count'], 'hospitals')

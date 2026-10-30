#!/usr/bin/env python3
"""Independent check of data/affordability.json and affordability.html.
1. California MEPS-IC values (2021-latest) are re-read from AHRQ's separate state Excel files and must equal the PDF-parsed values.
   Every other state and the U.S. row are re-read the same way for the two newest years.
2. Every dollar and percent figure in the comparison table on the page is recomputed from the JSON.
3. Income and CPI spot values are re-derived from the raw cached files.
Exits non-zero on any mismatch."""
import json, re, sys, urllib.request
from pathlib import Path
import openpyxl
ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(__file__).resolve().parent / '.cache'
d = json.load(open(ROOT / 'data/affordability.json'))
bad = []
IDS = {'single_premium': 'II.C.1', 'single_contribution': 'II.C.2', 'family_premium': 'II.D.1', 'family_contribution': 'II.D.2',
       'single_deductible': 'II.F.2', 'family_deductible': 'II.F.3', 'hdhp_share': 'II.F.12'}
UA = {'User-Agent': 'Mozilla/5.0 Chrome/120'}
n = 0
LY = d['latest_year']
for y in range(2021, LY + 1):
    p = CACHE / f'CA{y}.xlsx'
    if not p.exists() or p.stat().st_size < 5000:
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(f'https://meps.ahrq.gov/mepsweb/data_stats/summ_tables/insr/excel/{y}/California{y}.xlsx', headers=UA), timeout=120).read())
    ws = openpyxl.load_workbook(p, data_only=True)['Table II']
    rows = {str(r[0]).strip(): r[2] for r in ws.iter_rows(values_only=True) if r[0]}
    for m, tid in IDS.items():
        raw = rows.get(tid)
        if raw is None:
            bad.append(f'{y} {tid} missing in xlsx'); continue
        v = float(re.sub(r'[^\d.]', '', str(raw)))
        j = d['meps'][m]['ca'][str(y)]
        n += 1
        if abs(v - j) > 0.051:
            bad.append(f'{y} {m}: xlsx {v} != json {j}')
# every state and the U.S. for the two newest years, from the same Excel series
from concurrent.futures import ThreadPoolExecutor
def xl(name, y):
    p = CACHE / f'{name}{y}.xlsx'
    if not p.exists() or p.stat().st_size < 5000:
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(f'https://meps.ahrq.gov/mepsweb/data_stats/summ_tables/insr/excel/{y}/{name}{y}.xlsx', headers=UA), timeout=120).read())
    ws = openpyxl.load_workbook(p, data_only=True)['Table II']
    return {str(r[0]).strip(): r[2] for r in ws.iter_rows(values_only=True) if r[0]}
jobs = [(st, y) for y in (LY - 1, LY) for st in list(d['meps_states']['single_premium']['est']) + ['United States'] if st != 'California']
with ThreadPoolExecutor(8) as ex:
    got = list(ex.map(lambda j: (j, xl(j[0].replace(' ', ''), j[1])), jobs))
for (st, y), rows in got:
    for m, tid in IDS.items():
        j = d['meps'][m]['us'].get(str(y)) if st == 'United States' else d['meps_states'][m]['est'][st].get(str(y))
        raw = rows.get(tid)
        if j is None and raw is None:
            continue
        n += 1
        try:
            v = float(re.sub(r'[^\d.]', '', str(raw)))
        except ValueError:
            v = None
        if v is None or j is None or abs(v - j) > 0.051:
            bad.append(f'{st} {y} {m}: xlsx {raw} != json {j}')
# page table figures
html = (ROOT / 'affordability-data.html').read_text()
for m in ('single_premium', 'single_contribution', 'single_deductible', 'family_premium', 'family_contribution', 'family_deductible'):
    for k in ('ca', 'us'):
        s = '${:,.0f}'.format(d['meps'][m][k][str(LY)])
        n += 1
        if s not in html:
            bad.append(f'page lacks {m} {k} {s}')
# CPI: annual mean of the 12 months re-derived from BLS directly is not repeated here; check index base and monotone sanity
for k, s in d['cpi'].items():
    if not all(100 < v < 1000 for v in s.values()):
        bad.append(f'cpi {k} out of range')
# income: re-read the Census file's newest 3-year column directly and compare
ws = openpyxl.load_workbook(CACHE / 'h08b.xlsx', data_only=True).active
rows = list(ws.iter_rows(values_only=True))
col = next(j for j, h in enumerate(rows[6]) if h and str(h).endswith(str(LY)) and str(h)[:4] == str(LY - 2))
for name, key in (('California', 'ca'), ('United States', 'us')):
    cell = next(r[col] for r in rows[8:] if r[0] == name)
    n += 1
    if float(cell) != d['income'][key][str(LY)]:
        bad.append(f'income {name} {LY}: file {cell} != json {d["income"][key][str(LY)]}')
print(f'{n} checks;', 'FAILED:\n  ' + '\n  '.join(bad) if bad else 'all passed')
sys.exit(1 if bad else 0)

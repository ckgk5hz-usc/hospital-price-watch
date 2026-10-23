#!/usr/bin/env python3
"""Build data/affordability.json from four public sources. Mechanical pulls only.

  MEPS-IC (AHRQ)  California (state Series II) and US (national Series I) PDF tables, 2015-2025
  Census CPS ASEC Table H-8B  median household income by state, 3-year averages, 2025 dollars
  NY Fed Consumer Credit Panel  state per-capita debt and 90+ day delinquency, Q4
  BLS CPI (API v1, no key)  US city average and West region, annual averages

Every record carries its source, table id and file URL. The script fails (non-zero exit)
on a missing year, a changed table layout, or a missing series. It never fills a gap.

Needs: pdftotext (poppler), openpyxl. Raw downloads are cached in tools/data/.cache.
"""
import json, os, re, subprocess, sys, urllib.request, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(__file__).resolve().parent / '.cache'
CACHE.mkdir(exist_ok=True)
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'
YEARS = list(range(2015, 2026))
MEPS = 'https://meps.ahrq.gov/mepsweb/data_stats/summ_tables/insr'
ALLSTATES = {}
fails = []
PARTIAL = set()


def get(url, name):
    p = CACHE / name
    if not p.exists() or p.stat().st_size < 5000:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=240) as r:
            p.write_bytes(r.read())
    return p


def num(s):
    s = s.replace('*', '').replace(',', '').replace('%', '').strip()
    return None if s in ('--', '', 'suppressed') else float(s)


# measure id -> (table suffix, label, unit)
MEASURES = {
    'single_premium': ('C.1', 'Average total single premium per enrolled employee', 'usd'),
    'single_contribution': ('C.2', 'Average employee contribution, single coverage', 'usd'),
    'family_premium': ('D.1', 'Average total family premium per enrolled employee', 'usd'),
    'family_contribution': ('D.2', 'Average employee contribution, family coverage', 'usd'),
    'single_deductible': ('F.2', 'Average individual deductible (enrollees in plans with a deductible)', 'usd'),
    'family_deductible': ('F.3', 'Average family deductible (enrollees in plans with a deductible)', 'usd'),
    'hdhp_share': ('F.12', 'Single-coverage enrollees in a high-deductible plan', 'pct'),
}


def table_value(lines, table, kind, row):
    """First number on `row` ('California' / 'United States') in the table block."""
    pat = re.compile(r'^Table ' + re.escape(table) + r' (Standard errors)?')
    for i, ln in enumerate(lines):
        m = pat.match(ln)
        if not m or bool(m.group(1)) != (kind == 'se'):
            continue
        for ln2 in lines[i:i + 140]:
            if ln2.startswith(row):
                toks = re.findall(r'--|[\d,]+\.?\d*%?\*?', ln2[len(row):])
                if toks:
                    return num(toks[0])
        break
    raise ValueError(f'{table} {kind} {row} not found')


STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming']


def table_states(lines, table, kind):
    """{state: Total value} for every state row in the table block (Total column = first number)."""
    pat = re.compile(r'^Table ' + re.escape(table) + r' (Standard errors)?')
    for i, ln in enumerate(lines):
        m = pat.match(ln)
        if not m or bool(m.group(1)) != (kind == 'se'):
            continue
        got = {}
        for ln2 in lines[i:i + 160]:
            for st in STATES:
                if ln2.startswith(st) and ln2[len(st):len(st) + 1] == ' ':
                    toks = re.findall(r'--|[\d,]+\.?\d*%?\*?', ln2[len(st):])
                    if toks and st not in got:
                        got[st] = num(toks[0])
        if len(got) < 45:
            raise ValueError(f'{table} {kind}: only {len(got)} states parsed')
        return got
    raise ValueError(f'{table} {kind} block not found')


def meps():
    out = {k: {'ca': {}, 'us': {}, 'ca_se': {}, 'us_se': {}} for k in MEASURES}
    global ALLSTATES
    ALLSTATES = {k: {'est': {}, 'se': {}} for k in MEASURES}
    for y in YEARS:
        yy = str(y)[2:]
        urls = {
            'state': f'{MEPS}/state/series_2/{y}/ic{yy}_iia_f.pdf',
            'nat': f'{MEPS}/national/series_1/{y}/ic{yy}_ia_g.pdf',
        }
        txt = {}
        for k, u in urls.items():
            pdf = get(u, f'{k}{y}.pdf')
            t = CACHE / f'{k}{y}.txt'
            subprocess.run(['pdftotext', '-layout', str(pdf), str(t)], check=True)
            txt[k] = t.read_text(errors='ignore').splitlines()
        for mid, (suf, _, unit) in MEASURES.items():
            if mid == 'hdhp_share' and y < 2016:
                continue  # table first appears in the 2016 series; not back-filled
            for side, key, series, pre in (('ca', 'state', 'II.', 'California'), ('us', 'nat', 'I.', 'United States')):
                if side == 'ca':
                    for kind in ('est', 'se'):
                        try:
                            for st, v in table_states(txt['state'], series + suf, kind).items():
                                ALLSTATES[mid][kind].setdefault(st, {})[str(y)] = v
                        except ValueError as e:
                            fails.append(f'MEPS states {y} {mid} {kind}: {e}')
                for kind, dest in (('est', side), ('se', side + '_se')):
                    try:
                        v = table_value(txt[key], series + suf, kind, pre)
                        out[mid][dest][str(y)] = v
                    except ValueError as e:
                        fails.append(f'MEPS {y} {mid} {side} {kind}: {e}')
    return out


def income():
    import openpyxl
    p = get('https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-income-households/h08b.xlsx', 'h08b.xlsx')
    ws = openpyxl.load_workbook(p, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[6]
    res = {'ca': {}, 'us': {}, 'ca_se': {}, 'us_se': {}, 'states': {}}
    for r in rows[8:]:
        name = (r[0] or '').strip() if isinstance(r[0], str) else ''
        key = {'California': 'ca', 'United States': 'us'}.get(name)
        if name in STATES:
            for j in range(1, len(hdr) - 1, 2):
                lab = hdr[j]
                if lab and re.match(r'^\d{4}-\d{4}', str(lab)) and r[j] is not None:
                    res['states'].setdefault(name, {}).setdefault(str(lab)[5:9], float(r[j]))
        if not key:
            continue
        for j in range(1, len(hdr) - 1, 2):
            lab = hdr[j]
            if not lab or not re.match(r'^\d{4}-\d{4}', str(lab)):
                continue
            end = str(lab)[5:9]
            if r[j] is not None and not res[key].get(end):
                res[key][end] = float(r[j])
                res[key + '_se'][end] = float(r[j + 1]) if r[j + 1] is not None else None
    for k in ('ca', 'us'):
        if len(res[k]) < 30:
            fails.append(f'CPS H-8B {k}: only {len(res[k])} vintages')
    return res


def nyfed():
    import openpyxl
    p = get('https://www.newyorkfed.org/medialibrary/interactives/householdcredit/data/xls/area_report_by_year.xlsx', 'nyfed_area.xlsx')
    wb = openpyxl.load_workbook(p, data_only=True)
    out = {}
    for sheet, mid in (('total', 'total_debt_per_capita'), ('creditcard', 'card_debt_per_capita'),
                       ('mortgage', 'mortgage_debt_per_capita'), ('creditcard_delinq', 'card_delinq_90_pct')):
        rows = list(wb[sheet].iter_rows(values_only=True))
        hi = next(i for i, r in enumerate(rows) if r[0] == 'state')
        hdr = rows[hi]
        out[mid] = {}
        for r in rows[hi + 1:]:
            if r[0] == 'CA':
                for c, v in zip(hdr[1:], r[1:]):
                    if v is not None:
                        out[mid][c[3:]] = float(v)
        # US per-capita is not in this file: population-weight the 51 state rows
        if mid != 'card_delinq_90_pct':
            pop = {r[0]: r[1:] for r in list(wb['population'].iter_rows(values_only=True))[hi + 1:] if isinstance(r[0], str) and len(r[0]) == 2}
            us = {}
            for r in rows[hi + 1:]:
                if isinstance(r[0], str) and len(r[0]) == 2 and r[0] in pop:
                    for c, v, pw in zip(hdr[1:], r[1:], pop[r[0]]):
                        if v is not None and pw:
                            a = us.setdefault(c[3:], [0.0, 0.0])
                            a[0] += float(v) * float(pw); a[1] += float(pw)
            out[mid + '_us'] = {k: round(a[0] / a[1], 1) for k, a in us.items()}
    # US card delinquency: weight each state's 90+ day share by its card balances (per-capita x panel population)
    drows = list(wb['creditcard_delinq'].iter_rows(values_only=True)); crows = list(wb['creditcard'].iter_rows(values_only=True)); prow = list(wb['population'].iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(drows) if r[0] == 'state')
    cp = {r[0]: r[1:] for r in crows[hi + 1:] if isinstance(r[0], str) and len(r[0]) == 2}
    pp = {r[0]: r[1:] for r in prow[hi + 1:] if isinstance(r[0], str) and len(r[0]) == 2}
    acc = {}
    for r in drows[hi + 1:]:
        if isinstance(r[0], str) and len(r[0]) == 2 and r[0] in cp and r[0] in pp:
            for c, dl, bal, pw in zip(drows[hi][1:], r[1:], cp[r[0]], pp[r[0]]):
                if dl is not None and bal and pw:
                    a = acc.setdefault(c[3:], [0.0, 0.0]); w = float(bal) * float(pw)
                    a[0] += float(dl) * w; a[1] += w
    out['card_delinq_90_pct_us'] = {k: round(a[0] / a[1], 2) for k, a in acc.items()}
    if not out['total_debt_per_capita'].get('2025'):
        fails.append('NY Fed: no CA Q4 2025')
    return out


def bls():
    series = {'us_all': 'CUUR0000SA0', 'west_all': 'CUUR0400SA0', 'us_medical': 'CUUR0000SAM',
              'west_medical': 'CUUR0400SAM', 'us_shelter': 'CUUR0000SAH1', 'west_shelter': 'CUUR0400SAH1'}
    body = json.dumps({'seriesid': list(series.values()), 'startyear': '2016', 'endyear': '2025'}).encode()
    req = urllib.request.Request('https://api.bls.gov/publicAPI/v1/timeseries/data/', body, {'Content-type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get('status') != 'REQUEST_SUCCEEDED':
        fails.append('BLS: ' + str(d.get('message')))
        return {}
    out = {}
    for s in d['Results']['series']:
        k = next(n for n, i in series.items() if i == s['seriesID'])
        out[k] = {}
        for x in s['data']:
            if x['period'] == 'M13' and x['value'] not in ('-', ''):
                out[k][x['year']] = float(x['value'])
        # fall back to the mean of 12 months only when every month is present
        if not out[k]:
            by = {}
            for x in s['data']:
                if x['period'].startswith('M') and x['value'] not in ('-', ''):
                    by.setdefault(x['year'], []).append(float(x['value']))
            out[k] = {y: round(sum(v) / len(v), 3) for y, v in by.items() if len(v) == 12 or (y == '2025' and len(v) == 11)}
            if '2025' in out[k] and len(by['2025']) == 11:
                PARTIAL.add('2025 CPI annual average uses 11 of 12 months: BLS collected no October 2025 data (lapse in appropriations).')
        for y in range(2016, 2026):
            if str(y) not in out[k]:
                fails.append(f'BLS {k} {y} missing')
    return out


def nhe():
    import openpyxl, zipfile
    z = get('https://www.cms.gov/files/zip/nhe-tables.zip', 'nhe-tables.zip')
    zf = zipfile.ZipFile(z)
    name = next(n for n in zf.namelist() if n.split('/')[-1].startswith('Table 04'))
    p = CACHE / 'nhe_table04.xlsx'
    p.write_bytes(zf.read(name))
    rows = list(openpyxl.load_workbook(p, data_only=True)['Table 4'].iter_rows(values_only=True))
    hdr = [r for r in rows[2]]
    col = hdr.index('Private Health Insurance')
    yi = max(i for i, r in enumerate(rows) if r[0] and re.match(r'^Year \d{4}$', str(r[0]).strip()))
    year = int(str(rows[yi][0]).strip()[5:])
    want = {'total': 'National Health Expenditures', 'personal': 'Personal Health Care', 'hospital': 'Hospital Care', 'physician': 'Physician and Clinical Services',
            'drugs': 'Prescription Drugs', 'net_cost': 'Non-Medical Insurance Expenditures'}
    v = {}
    for r in rows[yi + 1:yi + 22]:
        lab = re.sub(r'\d+$', '', str(r[0]).strip()).strip()
        for k, w in want.items():
            if lab == w and k not in v:
                v[k] = float(r[col])
    if set(v) != set(want):
        fails.append('NHE: missing lines ' + str(set(want) - set(v)))
        return {}
    v['other_care'] = round(v['personal'] - v['hospital'] - v['physician'] - v['drugs'], 1)
    if abs(v['personal'] + v['net_cost'] - v['total']) > 0.6:
        fails.append('NHE: lines do not sum to total')
    v['year'] = year
    return v


def main():
    data = {
        'generated': datetime.date.today().isoformat(),
        'meps': meps(), 'meps_states': ALLSTATES, 'income': income(), 'nyfed': nyfed(), 'cpi': bls(), 'nhe': nhe(),
        'cpi_notes': sorted(PARTIAL),
        'measures': {k: {'table_ca': 'II.' + v[0], 'table_us': 'I.' + v[0], 'label': v[1], 'unit': v[2]} for k, v in MEASURES.items()},
        'sources': {
            'meps': {'name': 'AHRQ Medical Expenditure Panel Survey, Insurance Component (MEPS-IC)',
                     'url': 'https://meps.ahrq.gov/mepsweb/data_stats/state_tables.jsp',
                     'files': f'{MEPS}/state/series_2/YYYY/icYY_iia_f.pdf (California); {MEPS}/national/series_1/YYYY/icYY_ia_g.pdf (US)'},
            'income': {'name': 'U.S. Census Bureau, CPS ASEC, Table H-8B',
                       'url': 'https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html',
                       'files': 'https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-income-households/h08b.xlsx'},
            'nyfed': {'name': 'Federal Reserve Bank of New York Consumer Credit Panel / Equifax, State Level Household Debt Statistics',
                      'url': 'https://www.newyorkfed.org/microeconomics/hhdc',
                      'files': 'https://www.newyorkfed.org/medialibrary/interactives/householdcredit/data/xls/area_report_by_year.xlsx'},
            'nhe': {'name': 'CMS National Health Expenditure Accounts, Table 4 (private health insurance column)', 'url': 'https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/historical', 'files': 'https://www.cms.gov/files/zip/nhe-tables.zip'},
            'cpi': {'name': 'U.S. Bureau of Labor Statistics, Consumer Price Index (CPI-U, not seasonally adjusted, annual average)',
                    'url': 'https://www.bls.gov/cpi/', 'files': 'https://api.bls.gov/publicAPI/v1/timeseries/data/'}},
    }
    if fails:
        print('FAILED:\n  ' + '\n  '.join(fails[:40]))
        sys.exit(1)
    (ROOT / 'data' / 'affordability.json').write_text(json.dumps(data, indent=1, allow_nan=False))
    print('wrote data/affordability.json')


if __name__ == '__main__':
    main()

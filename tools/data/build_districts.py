#!/usr/bin/env python3
"""California congressional districts (119th Congress): affordability measures from the Urban Institute's American Affordability
Tracker, joined to Census geography for a ZIP lookup, a county/city description and a map.

Sources
  Urban Institute, The American Affordability Tracker data catalog (ODC-BY 1.0): healthcare, tces, credit CSVs on Urban's S3 bucket.
  Census Bureau 119th Congressional District relationship files (ZCTA, county, place) and the 1:5,000,000 cartographic boundary KML.
Output: data/districts.json. Every number is copied from Urban's files; this script only selects California rows, de-duplicates,
and attaches geography. If a download fails and a previous data/districts.json exists, it is kept and DISTRICTS_STALE is printed.
Stdlib only. Run from the repo root:  python3 tools/data/build_districts.py
"""
import csv, io, json, math, os, re, sys, urllib.request, zipfile, datetime as dt
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'data', 'districts.json')
URBAN = 'https://urban-data-catalog.s3.amazonaws.com/drupal-root-live/'
URBAN_FILES = {'healthcare': '2026/10/23/healthcare_combined.csv', 'tces': '2026/10/29/tces_combined.csv', 'credit': '2026/10/23/credit_combined.csv',
               'dictionary': '2026/10/29/data-dictionary.csv'}
CENSUS = 'https://www2.census.gov/geo/docs/maps-data/data/rel2020/cd-sld/tab20_cd11920_%s_natl.txt'
KML = 'https://www2.census.gov/geo/tiger/GENZ2025/kml/cb_2025_us_cd119_5m.zip'
CATALOG = 'https://datacatalog.urban.org/dataset/american-affordability-tracker'
TOOL = 'https://www.urban.org/data-tools/american-affordability-tracker'
APPENDIX = 'https://www.urban.org/sites/default/files/2026-10/The_American_Affordability_Tracker_Technical_Appendix.pdf'


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'curl/8.7'}), timeout=180).read()


def rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8', errors='replace').lstrip('﻿'))))


def num(v):
    return None if v in ('', 'NA', None) else float(v)


def rel(fileword, k):
    """Census relationship rows for California districts: (district number, other GEOID, other name, land overlap, other land, district land)."""
    out = []
    for r in csv.DictReader(io.StringIO(get(CENSUS % fileword).decode('utf-8-sig')), delimiter='|'):
        g = r['GEOID_CD119_20']
        if g.startswith('06') and r.get('GEOID_%s_20' % k):
            out.append((g[2:], r['GEOID_%s_20' % k], r['NAMELSAD_%s_20' % k], int(r['AREALAND_PART'] or 0), int(r['AREALAND_%s_20' % k] or 0), int(r['AREALAND_CD119_20'] or 0)))
    return out


# ---- map: KML polygons -> projected, simplified SVG paths
LAT0 = 37.0
def proj(lon, lat):
    return ((lon + 124.5) * math.cos(math.radians(LAT0)) * 60, (42.1 - lat) * 60)


def dp(pts, tol):
    """Douglas-Peucker simplification, iterative."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1e-9
        best, bi = -1, None
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
            if d > best: best, bi = d, i
        if bi is not None and best > tol:
            keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def shapes():
    z = zipfile.ZipFile(io.BytesIO(get(KML)))
    root = ET.fromstring(z.read([n for n in z.namelist() if n.endswith('.kml')][0]))
    ns = {'k': 'http://www.opengis.net/kml/2.2'}
    out = {}
    for pm in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        f = {e.get('name'): e.text for e in pm.iter('{http://www.opengis.net/kml/2.2}SimpleData')}
        if f.get('STATEFP') != '06':
            continue
        rings = []
        for c in pm.iter('{http://www.opengis.net/kml/2.2}coordinates'):
            pts = [proj(*map(float, t.split(',')[:2])) for t in c.text.split()]
            h = len(pts) // 2
            s = dp(pts[:h + 1], 0.12) + dp(pts[h:], 0.12)[1:]   # rings are closed; simplify each half
            if len(s) >= 4:
                rings.append('M' + 'L'.join('%.2f,%.2f' % p for p in s) + 'Z')
        out[f['CD119FP']] = ''.join(rings)
    return out


def main():
    try:
        U = {k: get(URBAN + v) for k, v in URBAN_FILES.items()}
        zc, co, pl = rel('zcta520', 'ZCTA5'), rel('county20', 'COUNTY'), rel('place20', 'PLACE')
        geo = shapes()
    except Exception as e:
        if os.path.exists(OUT):
            print('DISTRICTS_STALE: a download failed (%s); kept data/districts.json from %s. Run tools/data/build_districts.py on a regular computer.' % (str(e)[:120], json.load(open(OUT))['generated']))
            return
        raise
    # definitions come from Urban's own dictionary, so a changed definition shows up in the diff
    txt = U['dictionary'].decode('utf-8', errors='replace')
    defs = {r['series_prefix']: r['definition'] for r in csv.DictReader(io.StringIO(txt[txt.index('file,series_prefix'):]))}
    def ca_and_us(name, fields):
        out = {'us': {}, 'ca': {}, 'cd': {}}
        seen = set()
        for r in rows(U[name]):
            key = (r['state_abbr'], r['cd_code'], r['date'])
            if key in seen:
                continue                                     # Urban's 2026 credit rows appear twice, word for word
            seen.add(key)
            y = r['date'][:4]
            vals = {f: num(r[f]) for f in fields}
            if r['state_abbr'] == 'NA' and r['state_name'] == 'NA':
                out['us'][y] = vals
            elif r['state_abbr'] == 'CA' and r['cd_code'] in ('NA', ''):
                out['ca'][y] = vals
            elif r['state_abbr'] == 'CA':
                out['cd'].setdefault(r['cd_code'], {})[y] = vals
        return out
    hc = ca_and_us('healthcare', ['healthinsurancecost_nominal'])
    tc = ca_and_us('tces', ['tces_rate_all'])
    cr = ca_and_us('credit', ['creditcard_delinquency_rate', 'auto_delinquency_rate', 'average_credit_score'])
    cds = sorted(hc['cd'])
    if len(cds) != 52 or set(cds) != set(geo):
        sys.exit('district count changed: %d in Urban, %d in Census map' % (len(cds), len(geo)))
    prem = lambda d: {y: v['healthinsurancecost_nominal'] for y, v in sorted(d.items()) if v['healthinsurancecost_nominal'] is not None}
    ly = max(hc['ca']); cy = max(cr['ca']); ty = max(tc['ca'])
    counties, places = {}, {}
    for cd, gid, name, part, oland, cland in co:
        if cland: counties.setdefault(cd, []).append((part / cland, name))
    for cd, gid, name, part, oland, cland in pl:
        if cland and part:   # incorporated cities and towns first; unincorporated places (CDPs) only fill in
            places.setdefault(cd, []).append((not name.endswith(' CDP'), part / cland, re.sub(r' (city|town|CDP)$', '', name)))
    zips = {}
    for cd, gid, name, part, oland, cland in zc:
        if oland and part:
            zips.setdefault(gid, []).append([cd, round(part / oland, 3)])
    zips = {z: sorted(v, key=lambda x: -x[1]) for z, v in sorted(zips.items())}
    D = {}
    for cd in cds:
        D[cd] = {'premium': prem(hc['cd'][cd]),
                 'tces': (tc['cd'].get(cd, {}).get(ty) or {}).get('tces_rate_all'),
                 'credit': {k: (cr['cd'].get(cd, {}).get(cy) or {}).get(k) for k in ('creditcard_delinquency_rate', 'auto_delinquency_rate', 'average_credit_score')},
                 'counties': [[n, round(s, 3)] for s, n in sorted(counties.get(cd, []), reverse=True)],
                 'places': [n for inc, s, n in sorted(places.get(cd, []), reverse=True)[:6]],
                 'path': geo[cd]}
    out = {'generated': dt.date.today().isoformat(), 'premium_year': ly, 'credit_year': cy, 'tces_year': ty,
           'ca': {'premium': prem(hc['ca']), 'tces': tc['ca'][ty]['tces_rate_all'], 'credit': cr['ca'][cy]},
           'us': {'premium': prem(hc['us']), 'tces': tc['us'][ty]['tces_rate_all'], 'credit': cr['us'][cy]},
           'districts': D, 'zips': zips,
           'definitions': {'premium': 'Unsubsidized monthly premium of the second-lowest-cost ("benchmark") Silver plan on the ACA Marketplace for a 40-year-old nonsmoker, averaged across the district by population (Urban Institute technical appendix).',
                           'premium_dictionary': defs.get('healthinsurancecost'), 'tces_dictionary': defs.get('tces_rate_all'),
                           'tces': 'The share of people in families whose resources fall below what it takes to pay for the goods and services needed to take full part in today\'s economy and society, and to save for emergencies and the future (Urban Institute, %s data).' % ty,
                           'creditcard': defs.get('creditcard_delinquency_rate'), 'auto': defs.get('auto_delinquency_rate'), 'score': defs.get('average_credit_score')},
           'sources': {'tool': TOOL, 'catalog': CATALOG, 'appendix': APPENDIX, 'license': 'ODC-BY 1.0',
                       'citation': 'Urban Institute. 2025. The American Affordability Tracker. Accessible from https://datacatalog.urban.org/dataset/american-affordability-tracker. Data originally sourced from The American Affordability Tracker, developed at the Urban Institute, and made available under the ODC-BY 1.0 Attribution License.',
                       'census': 'https://www.census.gov/geographies/reference-files/2020/geo/relationship-files.html', 'boundaries': KML}}
    json.dump(out, open(OUT, 'w'), separators=(',', ':'), allow_nan=False)
    print('districts: %d, zips: %d, premium %s CA $%.0f, %d bytes' % (len(D), len(zips), ly, out['ca']['premium'][ly], os.path.getsize(OUT)))


if __name__ == '__main__':
    main()

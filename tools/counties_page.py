"""County profiles: county.html plus data/counties.json. One page per California county (picked with ?c=), optionally side by side
with a second county (&vs=), always next to the state. Every figure is computed here from the same files the rest of the site uses:
data/hospitals.json (HCAI annual disclosures), data/hospital_prices.json (HCAI Hospital Measurement dataset, CMS stars),
data/maternity.json, data/closures.json, data/districts.json (Urban Institute) and data/county_pop.json (2020 Census)."""
import json, math, statistics as st

MIN_N = 3   # medians of fewer hospitals are not shown


def med(v):
    v = [x for x in v if x is not None]
    return (round(st.median(v), 5), len(v)) if len(v) >= MIN_N else (None, len(v))


def project(lon, lat):
    k = 30.0
    return round((lon + 124.6) * k * math.cos(math.radians(37.5)), 1), round((42.1 - lat) * k, 1)


def ring_path(ring):
    pts, last = [], None
    for lon, lat in ring:
        p = project(lon, lat)
        if last is None or abs(p[0] - last[0]) + abs(p[1] - last[1]) >= 0.9:
            pts.append(p); last = p
    if len(pts) < 3:
        return ''
    return 'M' + 'L'.join('%g,%g' % p for p in pts) + 'Z'


def build(root, H, head, header, tail, write):
    J = lambda f: json.load(open(root + '/data/' + f))
    hosp = J('hospitals.json'); hp = J('hospital_prices.json'); mat = J('maternity.json'); clo = J('closures.json')
    dz = J('districts.json'); pop = J('county_pop.json'); geo = J('ca_counties.geojson')
    names = {r[0]: r[1] for r in J('profiles/list.json')}
    price = {h['id']: h for h in hp['hospitals'] if h.get('ip') is not None}
    active = lambda h: h['is_general_acute'] is not False and ('2023' in h['annual'] or '2024' in h['annual'])
    A = lambda h, y, f: (h['annual'].get(y) or {}).get(f)
    counties = sorted(pop['pop2020'])

    def stats(hs, ppl, mats, clos):
        live = [h for h in hs if active(h)]
        m23 = [A(h, '2023', 'operating_margin') for h in live]
        m23 = [m for m in m23 if m is not None]
        pr = [price[h['oshpd_id']] for h in live if h['oshpd_id'] in price]
        beds = sum(h['licensed_beds'] or 0 for h in live)
        births = lambda y: sum(1 for h in hs if (A(h, y, 'natural_births') or 0) > 0)
        return {
            'pop': ppl, 'hosp': len(live), 'beds': beds, 'beds_per_k': round(1000 * beds / ppl, 2) if ppl else None,
            'losing': [sum(1 for m in m23 if m < 0), len(m23)],
            'margin': med(m23), 'medi': med([(h.get('payer_mix') or {}).get('medical') for h in live]),
            'uncomp': med([A(h, '2023', 'uncompensated_care_rate') for h in live]),
            'ip': med([p['ip'] for p in pr]), 'ipx': med([p['ip_x'] for p in pr]),
            'births': [births('2012'), births('2023')], 'matstop': len(mats), 'closed': len(clos)}

    verified = [c for c in clo['items'] if c['status'] in ('closed_permanent', 'ceased_inpatient_converted')]
    # districts: share of each county's 2020 residents living in each congressional district
    dist = {}
    for cd, d in dz['districts'].items():
        for cn, sh in d['counties']:
            dist.setdefault(cn.replace(' County', ''), []).append([int(cd), d['name'], round(sh * d['pop2020']), d['premium'].get(dz['premium_year'])])
    paths = {f['properties']['name']: ' '.join(filter(None, (ring_path(poly[0]) for poly in (f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']])))) for f in geo['features']}
    assert set(paths) == set(counties), set(paths) ^ set(counties)
    out = {}
    for c in counties:
        hs = [h for h in hosp['hospitals'] if h['county'] == c]
        mats = [m for m in mat['items'] if m['county'] == c]
        clos = [x for x in verified if x['county'] == c]
        s = stats(hs, pop['pop2020'][c], mats, clos)
        ds = sorted(([n, nm, round(p / pop['pop2020'][c], 3), pr] for n, nm, p, pr in dist.get(c, [])), key=lambda x: -x[2])
        rows = []
        for h in sorted((h for h in hs if active(h)), key=lambda h: names.get(h['oshpd_id'], h['name'])):
            p = price.get(h['oshpd_id']) or {}
            x, y = project(h['lon'], h['lat']) if h.get('lat') else (None, None)
            rows.append([h['oshpd_id'], names.get(h['oshpd_id'], h['name']), (h['city'] or '').title(), h['licensed_beds'], A(h, '2023', 'operating_margin'),
                         p.get('ip'), p.get('ip_x'), p.get('stars'), x, y, 1 if p.get('ip_odd') else 0])
        s.update({'path': paths[c], 'hospitals': rows, 'districts': [d for d in ds if d[2] >= 0.005],
                  'maternity': [[m['oshpd_id'], names.get(m['oshpd_id'], m['name'].title()), m['first_year_zero'], m['preliminary']] for m in mats],
                  'closures': [[x['name'], x['city'], x['closed_year'], x['status'] == 'ceased_inpatient_converted'] for x in sorted(clos, key=lambda x: x['closed_year'] or 0)]})
        out[c] = s
    state = stats(hosp['hospitals'], sum(pop['pop2020'].values()), mat['items'], verified)
    data = {'odd': [hp['odd_low'], hp['odd_high']], 'generated': hosp['generated'], 'premium_year': dz['premium_year'], 'price_year': hp['year'], 'ca': state, 'nocounty': state['hosp'] - sum(v['hosp'] for v in out.values()), 'counties': out,
            'sources': {'hcai': hosp['source'], 'prices': hp['source'], 'pop': pop['source'], 'pop_url': pop['url'], 'cms_date': hp['cms_date']}}
    json.dump(data, open(root + '/data/counties.json', 'w'), separators=(',', ':'), allow_nan=False)

    f = 'county.html'
    opts = ''.join('<option>%s</option>' % H(c) for c in counties)
    page = head('County profiles: hospitals, prices and access in each California county | Hospital Price Watch',
                'Pick a California county to see its hospitals, their finances and prices, birth units that closed, verified closures and its congressional districts, next to the state or another county.',
                f, '<link rel="stylesheet" href="county.css">\n') + header(f)
    page += '''<main id="main"><div class="page-head"><div class="wrap"><h1 id="co-title">County profiles</h1>
<p class="lede" id="co-sub">Hospitals, their finances and prices, and access to care in each of California's 58 counties, next to the state or another county.</p></div></div>
<div class="wrap co">
<form class="co-pick" id="co-form"><label>County<select id="co-c"><option value="">Choose a county</option>%s</select></label>
<label>Compare with<select id="co-vs"><option value="">California only</option>%s</select></label>
<button type="button" class="btn ghost co-copy" id="co-copy" hidden>Copy link</button></form>
<div id="co-body" aria-live="polite"></div>
<section class="co-notes" aria-labelledby="co-how"><h2 id="co-how">How these numbers are built</h2><ul class="gaps">
<li><b>Hospitals</b> are general-acute hospitals that filed an annual financial disclosure with HCAI for fiscal year 2023 or 2024, placed in the county HCAI lists. Beds are licensed beds; residents are 2020 Census counts.</li>
<li><b>Medians</b> are the middle hospital, shown only when at least %d hospitals have data. Margins and free care are FY2023; payer mix is each payer's share of gross charges.</li>
<li><b>Prices</b> are what commercial insurers paid per case-mix adjusted stay, and that payment as a multiple of what Medicare paid the same hospital (HCAI Hospital Measurement dataset, %s). Hospitals with fewer than 100 commercial stays are left out.</li>
<li><b>Birth units stopped</b> counts hospitals whose natural births fell to zero and stayed there (this site's count from state filings). <b>Closures</b> are closures or ends of inpatient care since 2012, each checked against news and state records.</li>
<li><b>Districts</b> are the congressional districts the county's residents live in, with the share of the county in each and Urban Institute's benchmark Marketplace premium for a 40-year-old (%s).</li>
</ul></section>
</div></main>
''' % (opts, opts, MIN_N, hp['year'], dz['premium_year'])
    write(f, page + tail('<script src="county.js"></script>\n'))
    return len(out)

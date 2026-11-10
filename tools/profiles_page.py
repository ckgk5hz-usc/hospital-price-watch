"""Hospital profiles: hospital.html plus one small data file per hospital (data/profiles/<oshpd_id>.json), an index for search,
and statewide medians for comparison. Every figure is copied or computed from data/hospitals.json (HCAI annual disclosures),
data/hospital_prices.json (HCAI Hospital Measurement dataset, CMS star ratings) and data/maternity.json. hospital.js renders."""
import json, os, statistics as st
from hospital_prices_page import pretty

FIELDS = ['operating_margin', 'total_margin', 'net_patient_revenue', 'total_operating_expenses', 'operating_income', 'net_income', 'uncompensated_care_rate',
          'outpatient_share', 'charge_ratio', 'discharges', 'avg_stay_days', 'medical_discharge_share', 'private_discharge_share', 'natural_births']
PEER = ['operating_margin', 'total_margin', 'uncompensated_care_rate', 'outpatient_share', 'charge_ratio', 'avg_stay_days', 'medical_discharge_share', 'private_discharge_share']


def build(root, H, head, header, tail, write):
    hosp = json.load(open(root + '/data/hospitals.json'))
    hp = json.load(open(root + '/data/hospital_prices.json'))
    mat = {m['oshpd_id']: m for m in json.load(open(root + '/data/maternity.json'))['items']}
    price = {h['id']: h for h in hp['hospitals']}
    ga = [h for h in hosp['hospitals'] if h['is_general_acute'] is not False]
    years = sorted({y for h in hosp['hospitals'] for y in h['annual']})
    # statewide medians: the explorer's default cohort (general acute unless HCAI marks it otherwise), one value per hospital per year
    med = {}
    for f in PEER:
        med[f] = {}
        for y in years:
            v = [h['annual'][y][f] for h in ga if y in h['annual'] and h['annual'][y].get(f) is not None]
            if len(v) >= 30:
                med[f][y] = round(st.median(v), 5)
    own = {}
    for h in ga:
        o = (h.get('segments') or {}).get('ownership')
        a = h['annual'].get('2023')
        if o and a and a.get('operating_margin') is not None:
            own.setdefault(o, []).append(a['operating_margin'])
    peers = {'years': years, 'median': med, 'n_cohort': len(ga), 'ownership_2023': {k: [round(st.median(v), 5), len(v)] for k, v in own.items()},
             'price': {'ip': hp['summary']['ip'], 'ip_x': hp['summary']['ip_x'], 'op': hp['summary']['op'], 'op_x': hp['summary']['op_x'], 'year': hp['year']},
             'sources': {'hcai': hosp['source'], 'prices': hp['source'], 'cms_date': hp['cms_date'], 'generated': hosp['generated']}}
    d = root + '/data/profiles'
    os.makedirs(d, exist_ok=True)
    index = []
    for h in hosp['hospitals']:
        i = h['oshpd_id']; p = price.get(i); sg = h.get('segments') or {}
        name = pretty(p['name']) if p else pretty(h['name'])
        prof = {'id': i, 'name': name, 'hcai_name': pretty(h['name']), 'city': h['city'].title(), 'county': h['county'], 'beds': h['licensed_beds'],
                'general_acute': h['is_general_acute'], 'ownership': sg.get('ownership'), 'system': sg.get('system'), 'safety_net': sg.get('safety_net'),
                'setting': sg.get('setting'), 'payer_mix_2023': h.get('payer_mix'), 'low_income_share': h.get('low_income_share'),
                'annual': {y: {f: a.get(f) for f in FIELDS} for y, a in sorted(h['annual'].items())},
                'price': {k: p.get(k) for k in ('period_end', 'ip', 'ip_mcr', 'ip_x', 'stays', 'op', 'op_mcr', 'op_x', 'visits', 'ccn', 'cah', 'stars', 'ip_odd', 'op_odd', 'high_cost')} if p else None,
                'maternity': mat.get(i)}
        json.dump(prof, open('%s/%s.json' % (d, i), 'w'), separators=(',', ':'), allow_nan=False)
        last = max(h['annual']) if h['annual'] else None
        index.append([i, name, prof['city'], h['county'] or '', 1 if h['is_general_acute'] is not False else 0, last])
    keep = {x[0] for x in index}
    for f in os.listdir(d):
        if f.endswith('.json') and f[:-5] not in keep and f not in ('list.json', 'peers.json'):
            os.remove(os.path.join(d, f))
    json.dump(sorted(index, key=lambda x: x[1]), open(d + '/list.json', 'w'), separators=(',', ':'))
    json.dump(peers, open(d + '/peers.json', 'w'), separators=(',', ':'), allow_nan=False)

    out = head('Hospital profiles: finances, prices and quality for each California hospital | Hospital Price Watch',
               'A profile of each California hospital: operating margin since 2012, payer mix, free care, commercial prices against Medicare and the CMS star rating, compared with the state median and with any other hospital.',
               'hospital.html', '<link rel="stylesheet" href="hospital-prices.css">\n<link rel="stylesheet" href="hospital.css">\n') + header('hospital.html')
    out += '''<main id="main"><div class="page-head"><div class="wrap"><h1 id="hp-name">Hospital profiles</h1>
<p class="lede" id="hp-sub">Finances, prices and quality for each California hospital, from its own filings with the state, next to the state median.</p></div></div>
<div class="wrap hp" id="hp-root">
<section aria-labelledby="pf-find"><h2 id="pf-find" class="sr">Find a hospital</h2>
<form class="hp-tools" id="pf-form" role="search"><label>Hospital name or city<input id="pf-q" list="pf-list" autocomplete="off" placeholder="e.g. Cedars-Sinai, Fresno"></label><datalist id="pf-list"></datalist>
<label id="pf-vs-wrap" hidden>Compare with<input id="pf-vs" list="pf-list" autocomplete="off" placeholder="Another hospital"></label>
<p class="sub" id="pf-msg" aria-live="polite"></p></form>
<ul class="pf-pick" id="pf-pick"></ul></section>
<div id="pf-body"></div>
<section aria-labelledby="pf-read"><h2 id="pf-read">How to read a profile</h2><ul class="gaps">
<li><b>Source.</b> Finances, volumes and payer mix come from each hospital's annual financial disclosure to HCAI. A fiscal year is the year the reporting period ends; FY2024 is preliminary. Reports shorter than a full year are left out.</li>
<li><b>Operating margin</b> is income from patient care and other operations, divided by operating revenue. <b>Total margin</b> adds investment and other income. Hospitals in a system can book costs and income at the parent, so one facility's margin may not show the system's position.</li>
<li><b>State median</b> is the middle hospital among general-acute hospitals with data that year (the explorer's default group), so a few outliers do not move it.</li>
<li><b>Payer mix</b> is each payer's share of gross charges, not of payments; charges are list prices that few payers pay in full.</li>
<li><b>Prices</b> are what commercial insurers and Medicare actually paid per case-mix adjusted stay and per adjusted outpatient visit, from HCAI's Hospital Measurement dataset; shown only for hospitals with at least 100 commercial stays or 1,000 visits. <b>Stars</b> are the CMS Overall Hospital Quality Star Rating.</li>
<li><b>Not shown:</b> days of cash on hand. Systems sweep cash to the parent, so a facility's own figure is misleading.</li>
</ul><p class="sub">Every hospital's figures can be downloaded from its profile. Profiles are rebuilt whenever the underlying data are refreshed.</p></section>
</div></main>
'''
    write('hospital.html', out + tail('<script src="hospital.js"></script>\n'))
    return len(index)

"""Exhibits computed from the site's own data files at build time. Nothing here is typed in: every number on a card is read or
computed from data/*.json, so a data refresh updates the card. Published findings from named studies stay in content.py.
computed(root) -> list of exhibit dicts in the same shape as content.EXHIBITS, plus kind='computed'."""
import json, statistics as st

pct0 = lambda v: '%d%%' % round(v)
pct1 = lambda v: '%.1f%%' % v
sgn1 = lambda v: ('%+.1f%%' % v).replace('-', '−')
usd = lambda v: '$' + format(int(round(v)), ',')
month = lambda d: __import__('datetime').date.fromisoformat(d).strftime('%B %Y')
ksd = lambda v: '$%.1fk' % (v / 1000) if v >= 10000 else usd(v)


def _j(root, f):
    return json.load(open('%s/data/%s' % (root, f), encoding='utf-8'))


def computed(root):
    hosp = _j(root, 'hospitals.json'); aff = _j(root, 'affordability.json'); bench = _j(root, 'benchmarks.json')
    hp = _j(root, 'hospital_prices.json'); out = _j(root, 'outcomes.json'); mat = _j(root, 'maternity.json'); clo = _j(root, 'closures.json')
    E = []
    HCAI = 'HCAI annual disclosure data, computed on this site.'

    # ---- hospital finances: same cohort as the explorer's default view (general acute unless HCAI marks it otherwise)
    ga = [h for h in hosp['hospitals'] if h['is_general_acute'] is not False]
    yrs = ['2020', '2021', '2022', '2023', '2024']
    def series(field):
        return {y: [h['annual'][y][field] for h in ga if y in h['annual'] and h['annual'][y].get(field) is not None] for y in yrs}
    lab = lambda y: 'FY%s%s' % (y[2:], '*' if y == '2024' else '')
    om = series('operating_margin')
    neg = {y: 100 * sum(v < 0 for v in om[y]) / len(om[y]) for y in yrs}
    ns = '%d to %d' % (min(len(om[y]) for y in yrs), max(len(om[y]) for y in yrs))
    E.append(dict(id='losing', kind='computed', place='ca', topics=['finances'], date=hosp['generated'],
        claim='**%s** of California general-acute hospitals lost money on operations in FY2023.' % pct0(neg['2023']),
        chart=('bars', [(lab(y), neg[y], 'bar', 'FY%s%s: %s had a negative operating margin' % (y, ' (preliminary)' if y == '2024' else '', pct0(neg[y]))) for y in yrs], 0, 70, pct0,
               'Bar chart of the share of general-acute hospitals with a negative operating margin, FY2020 to FY2024: ' + ', '.join('%s %s' % (y, pct0(neg[y])) for y in yrs)),
        source="Share with a negative operating margin among %s general-acute hospitals with data each year (the explorer's default view, one record per hospital). %s *FY2024 is preliminary." % (ns, HCAI),
        link=('Open in the explorer', 'explorer.html#preset=losing')))
    med = {y: 100 * st.median(om[y]) for y in yrs}
    E.append(dict(id='margin', kind='computed', place='ca', topics=['finances'], date=hosp['generated'],
        claim='Median operating margin was **%s** in FY2023 and **%s** in preliminary FY2024.' % (sgn1(med['2023']), sgn1(med['2024'])),
        chart=('line', [(lab(y), med[y], 'FY%s%s: %s' % (y, ' (preliminary)' if y == '2024' else '', sgn1(med[y]))) for y in yrs], -3, 4, sgn1,
               'Line chart of median operating margin, FY2020 to FY2024: ' + ', '.join('%s %s' % (y, sgn1(med[y])) for y in yrs)),
        source='Median of %s general-acute hospitals each year, so a few outliers do not drive it. %s *FY2024 is preliminary.' % (ns, HCAI),
        link=('Open in the explorer', 'explorer.html#preset=covid')))
    uc = series('uncompensated_care_rate'); u3 = ['2022', '2023', '2024']
    umed = {y: 100 * st.median(uc[y]) for y in u3}
    E.append(dict(id='uncomp', kind='computed', place='ca', topics=['access', 'finances'], date=hosp['generated'],
        claim='The median general-acute hospital wrote off **%s** of billed charges as bad debt or charity care in FY2023.' % pct1(umed['2023']),
        chart=('bars', [(lab(y), umed[y], 'bar', 'FY%s%s: %s' % (y, ' (preliminary)' if y == '2024' else '', pct1(umed[y]))) for y in u3], 0, 2.4, pct1,
               'Bar chart of the median uncompensated care rate: ' + ', '.join('FY%s %s' % (y, pct1(umed[y])) for y in u3)),
        source='Bad debt plus charity discounts (HCAI line 355, "Other"; Hill-Burton and restricted donations are not included), divided by gross patient revenue. Median of %d to %d general-acute hospitals each year. %s *FY2024 is preliminary.' % (min(len(uc[y]) for y in u3), max(len(uc[y]) for y in u3), HCAI),
        link=('Open in the explorer', 'explorer.html#preset=free')))

    def by_group(key):
        g = {}
        for h in ga:
            a = h['annual'].get('2023')
            if a and a.get('operating_margin') is not None:
                g.setdefault(key(h), []).append(a['operating_margin'])
        return {k: (100 * st.median(v), len(v)) for k, v in g.items() if k is not None}
    own = by_group(lambda h: (h.get('segments') or {}).get('ownership'))
    order = sorted(own, key=lambda k: own[k][0])
    lo, hi = order[0], order[-1]
    E.append(dict(id='ownership', kind='computed', place='ca', topics=['finances'], date=hosp['generated'],
        claim='In FY2023 the median %s hospital ran a **%s** operating margin; the median %s hospital, **%s**.' % (hi.lower(), sgn1(own[hi][0]), lo.lower(), sgn1(own[lo][0])),
        chart=('hbars', [('%s (%d)' % (k, own[k][1]), own[k][0], 'FY2023 median operating margin, %s hospitals (%d): %s' % (k.lower(), own[k][1], sgn1(own[k][0]))) for k in order], sgn1,
               'Horizontal bar chart of FY2023 median operating margin by ownership: ' + ', '.join('%s %s' % (k, sgn1(own[k][0])) for k in order)),
        source='Number of hospitals in parentheses. Ownership type as HCAI classifies it in its latest year. A median for a small group moves a lot with one hospital. %s' % HCAI,
        link=('Group by ownership in the explorer', 'explorer.html')))
    sn = by_group(lambda h: (h.get('segments') or {}).get('safety_net'))
    if True in sn and False in sn:
        E.append(dict(id='safetynet', kind='computed', place='ca', topics=['finances', 'access'], date=hosp['generated'],
            claim='Safety-net hospitals had a median FY2023 operating margin of **%s**, against **%s** at other general-acute hospitals.' % (sgn1(sn[True][0]), sgn1(sn[False][0])),
            chart=('bars', [('Safety-net (%d)' % sn[True][1], sn[True][0], 'bar', 'Safety-net (DSH) hospitals, median: %s' % sgn1(sn[True][0])), ('Other (%d)' % sn[False][1], sn[False][0], 'base', 'Other general-acute hospitals, median: %s' % sgn1(sn[False][0]))],
                   min(-4, sn[True][0] - 1), max(2, sn[False][0] + 1), sgn1, 'Bar chart of FY2023 median operating margin: safety-net %s, other %s' % (sgn1(sn[True][0]), sgn1(sn[False][0]))),
            source='Safety-net means the hospital qualifies for Medicare disproportionate share (DSH) payments, as flagged in the HCAI panel. Number of hospitals in parentheses. %s' % HCAI,
            link=('Compare in the explorer', 'explorer.html')))
    pm = [h['payer_mix'] for h in ga if h.get('payer_mix')]
    top = {}
    for m in pm:
        k = max(m, key=lambda x: m[x] or 0); top[k] = top.get(k, 0) + 1
    names = {'medicare': 'Medicare', 'medical': 'Medi-Cal', 'private': 'Private insurance', 'county': 'County programs', 'other': 'Other'}
    porder = sorted(top, key=lambda k: -top[k])
    E.append(dict(id='payer', kind='computed', place='ca', topics=['finances', 'insurance'], date=hosp['generated'],
        claim='Medicare was the largest payer at **%d of %d** general-acute hospitals in FY2023, and Medi-Cal at %d.' % (top.get('medicare', 0), len(pm), top.get('medical', 0)),
        chart=('hbars', [(names[k], top[k], 'Largest payer, by share of gross patient revenue, at %d hospitals: %s' % (top[k], names[k])) for k in porder], lambda v: '%d' % v,
               'Horizontal bar chart of the number of hospitals by largest payer: ' + ', '.join('%s %d' % (names[k], top[k]) for k in porder)),
        source='Largest payer by share of gross patient revenue (charges, not payments), inpatient and outpatient combined, FY2023. %s' % HCAI,
        link=('Color by dominant payer in the explorer', 'explorer.html')))
    oy = [str(y) for y in range(2014, 2025)]
    osh = {y: [h['annual'][y]['outpatient_share'] for h in ga if y in h['annual'] and h['annual'][y].get('outpatient_share') is not None] for y in oy}
    omed = {y: 100 * st.median(osh[y]) for y in oy if osh[y]}
    show = [y for y in oy if y in omed and int(y) % 2 == 0]
    E.append(dict(id='outpatient', kind='computed', place='ca', topics=['finances'], date=hosp['generated'],
        claim='Outpatient care made up **%s** of gross patient revenue at the median hospital in FY2024, up from %s in FY2014.' % (pct0(omed['2024']), pct0(omed['2014'])),
        chart=('line', [('FY%s%s' % (y[2:], '*' if y == '2024' else ''), omed[y], 'FY%s%s: %s' % (y, ' (preliminary)' if y == '2024' else '', pct1(omed[y]))) for y in show], 0, 60, pct0,
               'Line chart of the median outpatient share of gross patient revenue: ' + ', '.join('FY%s %s' % (y, pct0(omed[y])) for y in show)),
        source='Median of general-acute hospitals with data each year (%d in FY2014, %d in FY2024), so the set of hospitals changes a little from year to year. The Center\'s brief uses a fixed set of 248 hospitals and aggregate revenue, so its figures differ. %s *FY2024 is preliminary.' % (len(osh['2014']), len(osh['2024']), HCAI),
        link=('Read the Center\'s brief', 'https://sites.usc.edu/improvinghealth/issue-briefs/california-hospital-outpatient-revenue-shift/')))

    # ---- hospital prices (HCAI Hospital Measurement dataset, built by tools/data/build_hospital_prices.py)
    s = hp['summary']; HP = 'HCAI Hospital Measurement dataset, %d reporting year, computed on this site.' % hp['year']
    E.append(dict(id='ipprice', kind='computed', place='ca', topics=['prices'], date=hp['updated'],
        claim='Commercial insurers paid the median California hospital **%s** per adjusted inpatient stay, %.2f times what Medicare paid.' % (usd(s['ip']), s['ip_x']),
        chart=('bars', [('Medicare', s['ip_mcr'], 'base', 'Medicare, median per adjusted stay: %s' % usd(s['ip_mcr'])), ('Commercial', s['ip'], 'bar', 'Commercial insurance, median per adjusted stay: %s' % usd(s['ip']))], 0, s['ip'] * 1.2, ksd,
               'Bar chart of median payment per case-mix adjusted inpatient stay: Medicare %s, commercial %s' % (usd(s['ip_mcr']), usd(s['ip']))),
        source='Median across %d general-acute hospitals with at least %d commercial stays; the ratio is the median of each hospital\'s own ratio (%d hospitals). Payments are adjusted for how sick patients were. %s' % (s['n_ip'], hp['min_stays'], s['n_ip_x'], HP),
        link=('Look up a hospital', 'hospital-prices.html')))
    E.append(dict(id='opprice', kind='computed', place='ca', topics=['prices'], date=hp['updated'],
        claim='For outpatient visits, commercial insurers paid the median hospital **%.2f times** Medicare.' % s['op_x'],
        chart=('bars', [('Medicare', s['op_mcr'], 'base', 'Medicare, median per adjusted visit: %s' % usd(s['op_mcr'])), ('Commercial', s['op'], 'bar', 'Commercial insurance, median per adjusted visit: %s' % usd(s['op']))], 0, s['op'] * 1.2, usd,
               'Bar chart of median payment per adjusted outpatient visit: Medicare %s, commercial %s' % (usd(s['op_mcr']), usd(s['op']))),
        source='Median across hospitals with at least %d commercial outpatient visits; the ratio is the median of each hospital\'s own ratio (%d hospitals). %s' % (hp['min_visits'], s['n_op_x'], HP),
        link=('Look up a hospital', 'hospital-prices.html')))
    ips = sorted(h['ip'] for h in hp['hospitals'] if h.get('ip') is not None)
    assert round(st.median(ips)) == round(s['ip']), 'hospital price median does not match summary'
    q = st.quantiles(ips, n=10)
    E.append(dict(id='pricespread', kind='computed', place='ca', topics=['prices'], date=hp['updated'],
        claim='A hospital at the 90th percentile was paid **%s** per commercial stay, %.1f times one at the 10th percentile.' % (usd(q[8]), q[8] / q[0]),
        chart=('bars', [('10th pct.', q[0], 'base', '10th percentile: %s per adjusted stay' % usd(q[0])), ('Median', st.median(ips), 'base', 'Median: %s' % usd(st.median(ips))), ('90th pct.', q[8], 'bar', '90th percentile: %s' % usd(q[8]))], 0, q[8] * 1.2, ksd,
               'Bar chart of commercial payment per adjusted inpatient stay across hospitals: 10th percentile %s, median %s, 90th percentile %s' % (usd(q[0]), usd(st.median(ips)), usd(q[8]))),
        source='Distribution across %d general-acute hospitals with at least %d commercial stays. Part of the gap reflects patient mix and services that the case-mix adjustment does not capture. %s' % (len(ips), hp['min_stays'], HP),
        link=('Sort hospitals by price', 'hospital-prices.html')))
    stt = hp['star_table']
    E.append(dict(id='stars', kind='computed', place='ca', topics=['prices'], date=hp['cms_date'],
        claim='Hospitals with higher federal quality ratings were paid more: **%s** per commercial stay at 5 stars, against %s at 1 star (medians).' % (usd(stt[-1]['median_ip']), usd(stt[0]['median_ip'])),
        chart=('bars', [('%d star%s' % (r['stars'], '' if r['stars'] == 1 else 's'), r['median_ip'], 'bar', '%d-star hospitals (%d): median %s per adjusted stay' % (r['stars'], r['n'], usd(r['median_ip']))) for r in stt], 0, stt[-1]['median_ip'] * 1.2, ksd,
               'Bar chart of median commercial payment per stay by CMS star rating: ' + ', '.join('%d stars %s' % (r['stars'], usd(r['median_ip'])) for r in stt)),
        source='CMS Overall Hospital Quality Star Rating (%s release), joined by CMS number through the state facility listing. Hospitals per group: %s. A pattern, not a cause: larger teaching hospitals tend to rate higher and treat more complex cases. %s' % (hp['cms_date'], ', '.join('%d' % r['n'] for r in stt), HP),
        link=('See the full table', 'hospital-prices.html')))

    # ---- employer coverage (AHRQ MEPS-IC, Census, BLS), built by tools/data/build_affordability.py
    LY = aff['latest_year']; Y0 = LY - 9; mp = aff['meps']; inc = aff['income']; cpi = aff['cpi']['us_all']
    MEPS = 'AHRQ MEPS-IC, private-sector employers, table %s.'
    fp = mp['family_premium']
    real = lambda v, y: v * cpi[str(LY)] / cpi[str(y)]
    gp = 100 * (real(fp['ca'][str(LY)], LY) / real(fp['ca'][str(Y0)], Y0) - 1)
    gi = 100 * (inc['ca'][str(LY)] / inc['ca'][str(Y0)] - 1)
    idx = [(str(y), 100 * real(fp['ca'][str(y)], y) / real(fp['ca'][str(Y0)], Y0), 100 * inc['ca'][str(y)] / inc['ca'][str(Y0)]) for y in range(Y0, LY + 1) if str(y) in fp['ca'] and str(y) in inc['ca']]
    E.append(dict(id='premvsincome', kind='computed', place='ca', topics=['insurance', 'household'], date=aff['generated'],
        claim='After inflation, California\'s average employer family premium rose **%s** from %d to %d; median household income rose %s.' % (pct0(gp), Y0, LY, pct0(gi)),
        chart=('lines2', [("'" + y[2:], a, b, '%s: premium index %.0f, income index %.0f' % (y, a, b)) for y, a, b in idx], ('Family premium', 'Household income'), lambda v: '%.0f' % v,
               'Line chart indexed to %d = 100: family premium reaches %.0f and median household income %.0f in %d, both adjusted for inflation' % (Y0, idx[-1][1], idx[-1][2], LY)),
        source='Index, %d = 100, both in %d dollars: the premium converted with CPI-U, income as Census publishes it in constant dollars. Premium: %s Income: Census CPS ASEC Table H-8B, three-year averages. Income covers all households, not only those with employer plans.' % (Y0, LY, MEPS % aff['measures']['family_premium']['table_ca']),
        link=('Open the affordability story', 'affordability.html')))
    share = 100 * fp['ca'][str(LY)] / inc['ca'][str(LY)]; share_us = 100 * fp['us'][str(LY)] / inc['us'][str(LY)]
    E.append(dict(id='premshare', kind='computed', place='ca', topics=['insurance', 'household'], date=aff['generated'],
        claim='California\'s average employer family premium, **%s** in %d, equaled %s of median household income.' % (usd(fp['ca'][str(LY)]), LY, pct0(share)),
        chart=('bars', [('California', share, 'bar', 'California: family premium %s, %s of median income %s' % (usd(fp['ca'][str(LY)]), pct1(share), usd(inc['ca'][str(LY)]))), ('U.S.', share_us, 'base', 'U.S.: family premium %s, %s of median income %s' % (usd(fp['us'][str(LY)]), pct1(share_us), usd(inc['us'][str(LY)])))], 0, 40, pct0,
               'Bar chart of the family premium as a share of median household income in %d: California %s, U.S. %s' % (LY, pct1(share), pct1(share_us))),
        source='Total premium, employer and worker shares together, %d. %s Income: Census CPS ASEC Table H-8B (three-year average).' % (LY, MEPS % aff['measures']['family_premium']['table_ca']),
        link=('Try the household calculator', 'affordability.html')))
    fc = mp['family_contribution']['ca']
    E.append(dict(id='workershare', kind='computed', place='ca', topics=['insurance', 'household'], date=aff['generated'],
        claim='California workers paid **%s** toward family coverage in %d, up from %s in %d.' % (usd(fc[str(LY)]), LY, usd(fc[str(Y0)]), Y0),
        chart=('line', [("'" + str(y)[2:], fc[str(y)], '%d: %s' % (y, usd(fc[str(y)]))) for y in range(Y0, LY + 1) if str(y) in fc], 0, max(fc.values()) * 1.25, ksd,
               'Line chart of the average worker contribution to family coverage in California, %d to %d, from %s to %s' % (Y0, LY, usd(fc[str(Y0)]), usd(fc[str(LY)]))),
        source='Average yearly employee contribution, family coverage. Not adjusted for inflation. %s' % (MEPS % aff['measures']['family_contribution']['table_ca']),
        link=('Open the affordability story', 'affordability.html')))
    sd = mp['single_deductible']['ca']
    E.append(dict(id='deductible', kind='computed', place='ca', topics=['insurance', 'household'], date=aff['generated'],
        claim='The average single deductible in California employer plans reached **%s** in %d, against %s in %d.' % (usd(sd[str(LY)]), LY, usd(sd[str(Y0)]), Y0),
        chart=('line', [("'" + str(y)[2:], sd[str(y)], '%d: %s' % (y, usd(sd[str(y)]))) for y in range(Y0, LY + 1) if str(y) in sd], 0, max(sd.values()) * 1.25, ksd,
               'Line chart of the average single deductible in California, %d to %d' % (Y0, LY)),
        source='Average deductible for single coverage, among enrollees in plans with a deductible. Not adjusted for inflation. %s' % (MEPS % aff['measures']['single_deductible']['table_ca']),
        link=('Open the affordability story', 'affordability.html')))
    hd = mp['hdhp_share']; hy = max(set(hd['ca']) & set(hd['us']))
    E.append(dict(id='hdhp', kind='computed', place='ca', topics=['insurance'], date=aff['generated'],
        claim='**%s** of single-coverage enrollees in California private-sector employer plans were in a high-deductible plan in %s, against %s nationally.' % (pct0(hd['ca'][hy]), hy, pct0(hd['us'][hy])),
        chart=('bars', [('California', hd['ca'][hy], 'bar', 'California: %s' % pct1(hd['ca'][hy])), ('U.S.', hd['us'][hy], 'base', 'U.S.: %s' % pct1(hd['us'][hy]))], 0, 70, pct0,
               'Bar chart of the share of single-coverage enrollees in a high-deductible plan in %s: California %s, U.S. %s' % (hy, pct1(hd['ca'][hy]), pct1(hd['us'][hy]))),
        source='High-deductible as the IRS defines it for health savings accounts. %s Survey estimates have sampling error; the affordability page tests whether gaps are real.' % (MEPS % aff['measures']['hdhp_share']['table_ca']),
        link=('Open the detailed tables', 'affordability-data.html')))
    w = aff['cpi']
    cm = 100 * (w['west_medical'][str(LY)] / w['west_medical'][str(Y0)] - 1); ca_ = 100 * (w['west_all'][str(LY)] / w['west_all'][str(Y0)] - 1)
    E.append(dict(id='cpimed', kind='computed', place='ca', topics=['household', 'prices'], date=aff['generated'],
        claim='In the West, medical care prices rose **%s** from %d to %d, against %s for all consumer prices.' % (pct0(cm), Y0, LY, pct0(ca_)),
        chart=('bars', [('Medical care', cm, 'bar', 'CPI-U West, medical care: +%s' % pct1(cm)), ('All items', ca_, 'base', 'CPI-U West, all items: +%s' % pct1(ca_))], 0, max(cm, ca_) * 1.25, lambda v: '+%d%%' % round(v),
               'Bar chart of price growth in the West, %d to %d: medical care %s, all items %s' % (Y0, LY, pct1(cm), pct1(ca_))),
        source='BLS Consumer Price Index, West region (CPI-U, annual averages). It measures price changes, not total spending. %s' % ' '.join(aff.get('cpi_notes', [])),
        link=('BLS CPI', 'https://www.bls.gov/cpi/')))
    n = aff['nhe']
    parts = [('Hospitals', n['hospital']), ('Physicians and clinics', n['physician']), ('Other care', n['other_care']), ('Insurer overhead and profit', n['net_cost']), ('Prescription drugs', n['drugs'])]
    assert abs(sum(v for _, v in parts) - n['total']) < 0.5, 'NHE parts do not add to total'
    parts.sort(key=lambda p: -p[1])
    E.append(dict(id='nhe', kind='computed', place='us', topics=['insurance', 'prices'], date=aff['generated'],
        claim='Hospitals took **%s** of private health insurance spending in %d, the largest share.' % (pct0(100 * n['hospital'] / n['total']), n['year']),
        chart=('hbars', [(k, 100 * v / n['total'], '%s: $%.0f billion, %s of $%.0f billion' % (k, v, pct1(100 * v / n['total']), n['total'])) for k, v in parts], pct0,
               'Horizontal bar chart of private health insurance spending by service in %d: ' % n['year'] + ', '.join('%s %s' % (k, pct0(100 * v / n['total'])) for k, v in parts)),
        source='CMS National Health Expenditure Accounts, Table 4, %d: $%.0f billion of private health insurance spending. "Insurer overhead and profit" is CMS\'s net cost of health insurance.' % (n['year'], n['total']),
        link=('CMS NHE tables', 'https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/historical')))

    # ---- published benchmarks, read from data/benchmarks.json (checked against the source text by verify_benchmarks.py)
    nx = bench.get('ehbs_us_next') or bench['ehbs_us']; pv = bench['ehbs_us']; nv = nx['values']
    up = 100 * (nv['family_premium'] / pv['values']['family_premium'] - 1) if nx is not pv else None
    E.append(dict(id='premium', kind='published', place='us', topics=['insurance'], date=nx['published'],
        claim='Employer family coverage cost **%s** in %d%s. Workers paid %s.' % (usd(nv['family_premium']), nx['year'], ', up %s in a year' % pct1(up) if up is not None else '', usd(nv['family_contribution'])),
        chart=('bars', [('Worker pays', nv['family_contribution'], 'bar', 'Covered workers paid an average of %s toward family coverage' % usd(nv['family_contribution'])), ('Employer pays', nv['family_premium'] - nv['family_contribution'], 'base', 'Employer share: about %s (total premium minus the worker contribution)' % usd(nv['family_premium'] - nv['family_contribution']))], 0, nv['family_premium'] * 0.95, usd,
               'Bar chart splitting the %s family premium into the worker contribution of %s and the employer share' % (usd(nv['family_premium']), usd(nv['family_contribution']))),
        source='%s, %s (employers with 10 or more workers). Employer share is the total premium minus the worker contribution. National average, not California.' % (nx['org'] + ' ' + nx['title'], month(nx['published'])),
        link=('Read the survey', nx['page'])))
    cb = bench['chbs_ca']
    E.append(dict(id='cafamily', kind='published', place='ca', topics=['insurance'], date=cb['published'],
        claim='California employer family coverage averaged **%s** in %d, against %s nationally.' % (usd(cb['values']['family_premium']), cb['year'], usd(pv['values']['family_premium'])),
        chart=('bars', [('California', cb['values']['family_premium'], 'bar', 'California, %d: %s (KFF and CHCF)' % (cb['year'], usd(cb['values']['family_premium']))), ('U.S.', pv['values']['family_premium'], 'base', 'U.S., %d: %s (KFF)' % (pv['year'], usd(pv['values']['family_premium'])))], 0, cb['values']['family_premium'] * 1.2, ksd,
               'Bar chart of the average family premium in %d: California %s, U.S. %s' % (cb['year'], usd(cb['values']['family_premium']), usd(pv['values']['family_premium']))),
        source='%s, %s; U.S. figure from the %s. Both survey employers with 10 or more workers, public and private. Workers in California paid %s toward family coverage.' % (cb['org'], cb['title'], pv['title'], usd(cb['values']['family_contribution'])),
        link=('Read the California survey', cb['page'])))
    oh = bench['ohca']; ov = oh['values']; tgt = oh['target']['values']; t0 = min(tgt)
    E.append(dict(id='ohcagrowth', kind='published', place='ca', topics=['insurance', 'policy'], date=oh['published'],
        claim='Commercial health spending per member in California rose **%s** in %d, more than twice the state\'s %s yearly target that began in %s.' % (pct1(ov['commercial_growth']), oh['year'], pct1(tgt[t0]), t0),
        chart=('bars', [('%d growth' % oh['year'], ov['commercial_growth'], 'bar', 'Commercial spending per member, %d to %d: +%s (%s to %s)' % (oh['year'] - 1, oh['year'], pct1(ov['commercial_growth']), usd(ov['commercial_pmpy_2023']), usd(ov['commercial_pmpy_2024']))), ('Target from %s' % t0, tgt[t0], 'base', 'State spending growth target for %s: %s' % (t0, pct1(tgt[t0])))], 0, 10, pct1,
               'Bar chart: commercial spending per member grew %s in %d, against a %s target from %s' % (pct1(ov['commercial_growth']), oh['year'], pct1(tgt[t0]), t0)),
        source='%s, %s (%s). Per member per year: %s in %d, %s in %d. The target applies from %s, so %d spending was not held to it. Targets: %s.' % (oh['org'], oh['title'], oh['published'], usd(ov['commercial_pmpy_2023']), oh['year'] - 1, usd(ov['commercial_pmpy_2024']), oh['year'], t0, oh['year'], ', '.join('%s %s' % (k, pct1(v)) for k, v in sorted(tgt.items()))),
        link=('Read the report', oh['doc'])))
    rg = sorted(oh['regions'], key=lambda r: -r['y2024'])
    E.append(dict(id='ohcaregions', kind='published', place='ca', topics=['insurance', 'prices'], date=oh['published'],
        claim='Commercial spending per member ranged from **%s** in %s to %s in the %s in 2024.' % (usd(rg[0]['y2024']), rg[0]['name'], usd(rg[-1]['y2024']), rg[-1]['name'].replace('Eastern counties', 'eastern counties')),
        chart=('hbars', [(r['name'].replace(' County', '').replace(', and ', ', ').replace(' counties', ''), r['y2024'], '%s: %s per member in 2024 (%s in 2023, %+.1f%%)' % (r['name'], usd(r['y2024']), usd(r['y2023']), r['growth'])) for r in rg], ksd,
               'Horizontal bar chart of commercial spending per member per year in 2024 by OHCA region, from %s to %s' % (usd(rg[0]['y2024']), usd(rg[-1]['y2024']))),
        source='%s, %s. Per member per year, commercial market, by the office\'s 19 rating regions. Not adjusted for age or health, so part of the gap reflects who lives where.' % (oh['org'], oh['title']),
        link=('Read the report', oh['doc'])))
    shares = [('Hospital outpatient', ov['share_hosp_outpatient']), ('Pharmacy', ov['share_pharmacy']), ('Hospital inpatient', ov['share_hosp_inpatient'])]
    shares.append(('Everything else', 100 - sum(v for _, v in shares)))
    E.append(dict(id='ohcashares', kind='published', place='ca', topics=['insurance', 'prices'], date=oh['published'],
        claim='Hospitals accounted for **%s** of California commercial health spending in 2024: %s outpatient and %s inpatient.' % (pct1(ov['share_hosp_outpatient'] + ov['share_hosp_inpatient']), pct1(ov['share_hosp_outpatient']), pct1(ov['share_hosp_inpatient'])),
        chart=('hbars', [(k, v, '%s: %s of commercial spending' % (k, pct1(v))) for k, v in shares], pct1,
               'Horizontal bar chart of commercial spending shares in 2024: ' + ', '.join('%s %s' % (k, pct1(v)) for k, v in shares)),
        source='%s, %s. "Everything else" (physicians, other professionals, and other services) is 100%% minus the three shares the report gives.' % (oh['org'], oh['title']),
        link=('Read the report', oh['doc'])))
    dm = bench['dmhc']; lg = dm['large_group']; ly_ = sorted(lg)
    big = max(ly_, key=lambda y: lg[y])
    E.append(dict(id='dmhc', kind='published', place='ca', topics=['insurance'], date=dm['checked_by_hand'],
        claim='Large-group premium rates in DMHC-regulated plans rose **%s** in %s, the most in the decade shown, and %s in %s.' % (pct1(lg[big]), big, pct1(lg[ly_[-1]]), ly_[-1]),
        chart=('bars', [("'" + y[2:], lg[y], 'bar', '%s: %s weighted average rate change' % (y, pct1(lg[y]))) for y in ly_], 0, max(lg.values()) * 1.25, lambda v: '%.1f' % v,
               'Bar chart of weighted average large-group rate changes, %s to %s: ' % (ly_[0], ly_[-1]) + ', '.join('%s %s' % (y, pct1(lg[y])) for y in ly_)),
        source='%s, %s. %s Plans expected %s for %d. Values in percent.' % (dm['org'], dm['title'], dm['method'], pct1(dm['expected_next']['large_group']), dm['expected_next']['year']),
        link=('Read the report', dm['doc'])))
    cs = bench['chcf_survey']; cv = cs['values']
    E.append(dict(id='chcfskip', kind='published', place='ca', topics=['household', 'access'], date=cs['published'],
        claim='**%d%%** of Californians said they or a family member skipped or delayed care because of cost in the past year.' % cv['skipped'],
        chart=('bars', [('Lower incomes', cv['skipped_low'], 'bar', 'Lower incomes: %d%%' % cv['skipped_low']), ('All adults', cv['skipped'], 'base', 'All adults: %d%%' % cv['skipped']), ('Higher incomes', cv['skipped_high'], 'base', 'Higher incomes: %d%%' % cv['skipped_high'])], 0, 100, lambda v: '%d%%' % v,
               'Bar chart of Californians who skipped or delayed care because of cost: lower incomes %d%%, all adults %d%%, higher incomes %d%%' % (cv['skipped_low'], cv['skipped'], cv['skipped_high'])),
        source='%s, %s: %s adults, %s; margin of error ±%.1f points overall, larger for income groups. Of those who skipped or delayed, %d%% said their condition got worse.' % (cs['org'], cs['title'], format(cs['n'], ','), cs['fielded'], cs['moe'], cv['worse']),
        link=('Read the survey', cs['page'])))

    # ---- surveys on cost barriers (SHADAC), built by tools/data/build_outcomes.py
    sh = out['shadac']; meta = out['shadac_meta']
    def last(geo, k):
        d = sh[geo][k]
        for f, v, m in zip(reversed(d['frames']), reversed(d['v']), reversed(d['moe'])):
            if v is not None:
                return f, 100 * v, 100 * m
    fb, cab, cam = last('California', 'bills'); fu, usb, usm = last('United States', 'bills')
    if fb == fu:
        E.append(dict(id='bills', kind='computed', place='ca', topics=['household', 'access'], date=out['generated'],
            claim='**%s** of Californians had trouble paying medical bills in %s, against %s nationally.' % (pct1(cab), fb, pct1(usb)),
            chart=('bars', [('California', cab, 'bar', 'California, %s: %s (±%.1f points)' % (fb, pct1(cab), cam)), ('U.S.', usb, 'base', 'U.S., %s: %s (±%.1f points)' % (fb, pct1(usb), usm))], 0, 16, pct0,
                   'Bar chart of people with trouble paying medical bills in %s: California %s, U.S. %s' % (fb, pct1(cab), pct1(usb))),
            source='SHADAC State Health Compare, from the federal National Health Interview Survey (%s): %s. Two-year pooled estimate; California margin of error ±%.1f points.' % (meta['bills']['survey'], meta['bills']['label'].lower(), cam),
            link=('SHADAC', meta['bills']['url'])))
    fc_, cac, cacm = last('California', 'care_cost'); _, usc, uscm = next((f, 100 * v, 100 * m) for f, v, m in zip(sh['United States']['care_cost']['frames'], sh['United States']['care_cost']['v'], sh['United States']['care_cost']['moe']) if f == fc_)
    E.append(dict(id='forgone', kind='computed', place='ca', topics=['household', 'access'], date=out['generated'],
        claim='**%s** of California adults could not get medical care when needed because of cost in %s (U.S.: %s).' % (pct1(cac), fc_, pct1(usc)),
        chart=('bars', [('California', cac, 'bar', 'California, %s: %s (±%.1f points)' % (fc_, pct1(cac), cacm)), ('U.S.', usc, 'base', 'U.S., %s: %s (±%.1f points)' % (fc_, pct1(usc), uscm))], 0, 16, pct0,
               'Bar chart of adults who could not get care because of cost in %s: California %s, U.S. %s' % (fc_, pct1(cac), pct1(usc))),
        source='SHADAC State Health Compare, from the CDC Behavioral Risk Factor Surveillance System (%s). California margin of error ±%.1f points. Asks about the respondent only, so it runs lower than surveys that count family members.' % (meta['care_cost']['survey'], cacm),
        link=('SHADAC', meta['care_cost']['url'])))

    # ---- access: maternity and closures (built from HCAI filings plus researched verdicts)
    mi = mat['items']; my = sorted({i['first_year_zero'] for i in mi}); prelim = sum(i['preliminary'] for i in mi)
    yrs_m = list(range(my[0], my[-1] + 1)); cnt = {y: sum(i['first_year_zero'] == y for i in mi) for y in yrs_m}
    E.append(dict(id='maternity', kind='computed', place='ca', topics=['access'], date=hosp['generated'],
        claim='At least **%d** California hospitals stopped natural births between %d and %d, by this site\'s count from state filings.' % (len(mi), my[0], my[-1]),
        chart=('bars', [("'" + str(y)[2:], cnt[y], 'bar', '%d: %d hospital%s first reported zero natural births' % (y, cnt[y], '' if cnt[y] == 1 else 's')) for y in yrs_m], 0, max(cnt.values()) + 2, lambda v: '%d' % v if v else '',
               'Bar chart of hospitals by first year with zero natural births, %d to %d, %d in all' % (my[0], my[-1], len(mi))),
        source='Hospitals with 100 or more natural births whose count fell to zero and stayed there, inferred from HCAI disclosures, not announcements (%d rest on preliminary FY2024 data). CalMatters counted 56 hospitals that stopped delivering babies since 2012, with a broader method.' % prelim,
        link=('Map them in the explorer', 'explorer.html')))
    cc = clo['counts']
    cats = [('Closed for good', cc.get('closed_permanent', 0)), ('Ended inpatient care', cc.get('ceased_inpatient_converted', 0)), ('New license or name', cc.get('continues_under_new_license_or_name', 0)),
            ('Merged into another campus', cc.get('merged_into_other_campus', 0)), ('Closed, then reopened', cc.get('closed_then_reopened', 0)), ('Still operating', cc.get('still_operating_stopped_filing', 0)), ('Could not verify', cc.get('cannot_verify', 0))]
    tot = sum(v for _, v in cats); real_c = cats[0][1] + cats[1][1]
    E.append(dict(id='closures', kind='computed', place='ca', topics=['access'], date=clo['generated'],
        claim='Of %d California hospitals that stopped filing state disclosures, **%d** had closed or ended inpatient care; most of the rest changed name or owner.' % (tot, real_c),
        chart=('hbars', [(k, v, '%s: %d hospital%s' % (k, v, '' if v == 1 else 's')) for k, v in cats], lambda v: '%d' % v,
               'Horizontal bar chart of what happened to %d hospitals that stopped filing: ' % tot + ', '.join('%s %d' % (k, v) for k, v in cats)),
        source='Hospitals that filed an HCAI annual disclosure between 2012 and 2023 and then stopped, each researched in news, state, county and hospital sources. A hospital that stops filing has often only been sold or relicensed, so the filing gap alone is not a closure.',
        link=('Map closures in the explorer', 'explorer.html')))

    # ---- congressional districts (Urban Institute American Affordability Tracker), built by tools/data/build_districts.py
    dz = _j(root, 'districts.json'); Yd = dz['premium_year']; Pd = str(int(Yd) - 1); dca, dus = dz['ca'], dz['us']; DD = dz['districts']
    URB = 'Urban Institute, American Affordability Tracker (ODC-BY 1.0): unsubsidized second-lowest-cost Silver premium for a 40-year-old, averaged by population. Most Covered California members pay much less after subsidies.'
    gca = 100 * (dca['premium'][Yd] / dca['premium'][Pd] - 1); gus = 100 * (dus['premium'][Yd] / dus['premium'][Pd] - 1)
    E.append(dict(id='mktjump', kind='computed', place='ca', topics=['insurance'], date=dz['generated'],
        claim='The benchmark Marketplace premium for a 40-year-old rose **%s** in California in %s, to %s a month, against %s nationally.' % (pct0(gca), Yd, usd(dca['premium'][Yd]), pct0(gus)),
        chart=('bars', [('California', gca, 'bar', 'California: %s to %s a month (+%s)' % (usd(dca['premium'][Pd]), usd(dca['premium'][Yd]), pct1(gca))), ('U.S.', gus, 'base', 'U.S.: %s to %s a month (+%s)' % (usd(dus['premium'][Pd]), usd(dus['premium'][Yd]), pct1(gus)))], 0, max(gca, gus) * 1.3, lambda v: '+%d%%' % round(v),
               'Bar chart of the %s to %s change in the benchmark premium: California %s, U.S. %s' % (Pd, Yd, pct1(gca), pct1(gus))),
        source=URB + ' KFF, which averages by enrollment, puts California\'s %s benchmark slightly higher.' % Yd,
        link=('See every district', 'districts.html')))
    yrs_d = sorted(dca['premium'])
    E.append(dict(id='mkttrend', kind='computed', place='ca', topics=['insurance'], date=dz['generated'],
        claim='California\'s benchmark Marketplace premium for a 40-year-old went from %s a month in %s to **%s** in %s.' % (usd(dca['premium'][yrs_d[0]]), yrs_d[0], usd(dca['premium'][Yd]), Yd),
        chart=('line', [("'" + y[2:], dca['premium'][y], '%s: %s a month (U.S. %s)' % (y, usd(dca['premium'][y]), usd(dus['premium'][y]))) for y in yrs_d], 0, max(dca['premium'].values()) * 1.25, usd,
               'Line chart of the California benchmark premium, %s to %s, from %s to %s a month' % (yrs_d[0], Yd, usd(dca['premium'][yrs_d[0]]), usd(dca['premium'][Yd]))),
        source=URB + ' Not adjusted for inflation.',
        link=('See every district', 'districts.html')))
    pr = sorted(((v['premium'][Yd], k) for k, v in DD.items()), reverse=True)
    pick = pr[:5] + pr[-5:]
    def named(rows, v):
        ks = sorted(k for x, k in rows if x == v)
        if len(ks) == 1:
            return 'District %d' % int(ks[0])
        cos = {DD[k]['counties'][0][0] for k in ks if DD[k]['counties'][0][1] >= 0.9}
        where = ' (all within %s)' % cos.pop() if len(cos) == 1 and all(DD[k]['counties'][0][1] >= 0.9 for k in ks) else ''
        return '%d districts%s' % (len(ks), where) if len(ks) > 3 else 'Districts ' + ', '.join(str(int(k)) for k in ks[:-1]) + ' and %d' % int(ks[-1])
    E.append(dict(id='mktdistricts', kind='computed', place='ca', topics=['insurance', 'household'], date=dz['generated'],
        claim='In %s the benchmark premium ran from **%s** a month in %s to %s in %s.' % (Yd, usd(pr[0][0]), named(pr, pr[0][0]), usd(pr[-1][0]), named(pr, pr[-1][0])),
        chart=('hbars', [('District %d' % int(k), v, 'District %d (%s): %s a month in %s' % (int(k), DD[k]['places'][0] if DD[k]['places'] else DD[k]['counties'][0][0], usd(v), Yd)) for v, k in pick], usd,
               'Horizontal bar chart of the five highest and five lowest district benchmark premiums in %s' % Yd),
        source='The five highest and five lowest of California\'s 52 districts. ' + URB + ' Urban builds district values from county prices, so districts inside one county often share a value; %s tie at the lowest.' % named(pr, pr[-1][0]).split(' (')[0],
        link=('Find your district', 'districts.html')))
    ts = sorted(((v['tces'], k) for k, v in DD.items() if v['tces'] is not None))
    E.append(dict(id='tces', kind='computed', place='ca', topics=['household'], date=dz['generated'],
        claim='**%s** of Californians lived in families below the true cost of economic security in %s, against %s nationally.' % (pct0(100 * dca['tces']), dz['tces_year'], pct0(100 * dus['tces'])),
        chart=('bars', [('Lowest district', 100 * ts[0][0], 'base', 'Lowest: District %d, %s' % (int(ts[0][1]), pct0(100 * ts[0][0]))), ('California', 100 * dca['tces'], 'bar', 'California: %s' % pct0(100 * dca['tces'])), ('U.S.', 100 * dus['tces'], 'base', 'U.S.: %s' % pct0(100 * dus['tces'])), ('Highest district', 100 * ts[-1][0], 'base', 'Highest: District %d, %s' % (int(ts[-1][1]), pct0(100 * ts[-1][0])))], 0, 100, pct0,
               'Bar chart of the share below the true cost of economic security in %s: California %s, U.S. %s, districts from %s to %s' % (dz['tces_year'], pct0(100 * dca['tces']), pct0(100 * dus['tces']), pct0(100 * ts[0][0]), pct0(100 * ts[-1][0]))),
        source='Urban Institute, American Affordability Tracker and Measuring the True Cost of Economic Security (ODC-BY 1.0). The threshold is what a family needs to cover essentials and save for emergencies and the future, set higher than the poverty line. Districts range from %s (District %d) to %s (District %d).' % (pct0(100 * ts[0][0]), int(ts[0][1]), pct0(100 * ts[-1][0]), int(ts[-1][1])),
        link=('See every district', 'districts.html')))
    return E

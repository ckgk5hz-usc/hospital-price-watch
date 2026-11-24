"""Scroll stories: story-spending.html, story-prices.html, story-finances.html, story-access.html.
Each story is a sequence of steps. A pinned SVG holds a fixed set of marks (squares, dots, bars); every step gives each mark
a position, size, color and opacity, and stories.js animates the marks from one step to the next as the reader scrolls.
All positions and every number in the text are computed here from the same data files the exhibits use."""
import json, math, statistics as st

W, HT = 640, 460
INK3, BASE = '#9aa1ad', '#c9cfd9'


def lr_round(parts, total=100):
    """Largest-remainder rounding, so whole squares add up to exactly `total`."""
    raw = [(k, v * total / sum(v for _, v in parts)) for k, v in parts]
    fl = [(k, int(v)) for k, v in raw]
    short = total - sum(v for _, v in fl)
    order = sorted(range(len(raw)), key=lambda i: -(raw[i][1] - fl[i][1]))
    out = dict(fl)
    for i in order[:short]:
        out[raw[i][0]] += 1
    return [(k, out[k]) for k, _ in parts]


def blocks(parts, n_marks, size=13, gap=3, cols=5, x0=40, x1=W - 40, base_y=HT - 70):
    """Lay squares out as side-by-side blocks (cols squares wide), bottom-aligned. Returns per-mark [x,y,w,h,color,op] and labels."""
    states, labels = [], []
    bw = cols * (size + gap)
    spare = (x1 - x0 - bw * len(parts)) / max(1, len(parts) - 1)
    for b, (name, n, color, lab) in enumerate(parts):
        bx = x0 + b * (bw + spare)
        for i in range(n):
            r, c = divmod(i, cols)
            states.append([bx + c * (size + gap), base_y - (r + 1) * (size + gap), size, size, color, 1])
        labels.append([bx + bw / 2, base_y + 20, name, 'middle', 600])
        labels.append([bx + bw / 2, base_y + 38, lab, 'middle', 400])
    while len(states) < n_marks:
        s0 = states[-1] if states else [W / 2, HT / 2, size, size, BASE, 0]
        states.append([s0[0], s0[1], size, size, s0[4], 0])
    return states, labels


def swarm(values, x_of, y_mid, r=4.2, band=120):
    """Beeswarm: dots at x, nudged up and down until they do not overlap. Returns y per value (same order)."""
    placed, ys = [], [None] * len(values)
    order = sorted(range(len(values)), key=lambda i: values[i])
    for i in order:
        x = x_of(values[i])
        for k in range(0, 400):
            dy = (k + 1) // 2 * (2 * r * 0.92) * (1 if k % 2 else -1)
            if abs(dy) > band / 2:
                dy = (hash(i) % band) - band / 2
                break
            if all((x - px) ** 2 + (y_mid + dy - py) ** 2 >= (2 * r * 0.95) ** 2 for px, py in placed if abs(px - x) < 2 * r):
                break
        placed.append((x, y_mid + dy)); ys[i] = y_mid + dy
    return ys


def money(v):
    return '$' + format(int(round(v)), ',')


# ------------------------------------------------------------------ spending
def spending(root):
    aff = json.load(open(root + '/data/affordability.json')); bench = json.load(open(root + '/data/benchmarks.json'))
    n = aff['nhe']; oh = bench['ohca']; ov = oh['values']; tgt = oh['target']['values']; t0 = min(tgt)
    N = 120
    cols = {'hosp': '#0f6e66', 'phys': '#3c9a8f', 'other': '#8cc5bc', 'net': '#b4570f', 'drugs': '#5b3d8a', 'rx': '#5b3d8a', 'out': '#0f6e66', 'in': '#2f8a7f', 'rest': '#a6a49d'}
    grid = [[W / 2 - 5 * 26 + (i % 10) * 26, 60 + (i // 10) * 30, 20, 20, BASE, 1 if i < 100 else 0] for i in range(N)]
    nhe = lr_round([('Hospitals', n['hospital']), ('Doctors, clinics', n['physician']), ('Other care', n['other_care']), ('Insurers', n['net_cost']), ('Drugs', n['drugs'])])
    ck = ['hosp', 'phys', 'other', 'net', 'drugs']
    s1, l1 = blocks([(nm, v, cols[ck[i]], '%d¢' % v) for i, (nm, v) in enumerate(nhe)], N)
    ohp = lr_round([('Hospital outpatient', ov['share_hosp_outpatient']), ('Pharmacy', ov['share_pharmacy']), ('Hospital inpatient', ov['share_hosp_inpatient']), ('Everything else', 100 - ov['share_hosp_outpatient'] - ov['share_pharmacy'] - ov['share_hosp_inpatient'])])
    ok = ['out', 'rx', 'in', 'rest']
    s2, l2 = blocks([(nm, v, cols[ok[i]], '%d¢' % v) for i, (nm, v) in enumerate(ohp)], N, cols=6)
    g, tg = int(round(ov['commercial_growth'] * 10)), int(round(tgt[t0] * 10))   # one square = 0.1 percentage point
    s3, l3 = blocks([('Growth, %d' % oh['year'], g, '#0f6e66', '+%.1f%% per person' % ov['commercial_growth']), ('State target from %s' % t0, tg, '#a6a49d', '%.1f%% a year' % tgt[t0])], N, cols=8, x0=150, x1=W - 150, size=11, gap=3)
    rg = sorted(oh['regions'], key=lambda r: -r['y2024'])
    mx = rg[0]['y2024']; rows = len(rg); rh = (HT - 60) / rows
    s4 = [[200, 28 + i * rh, (W - 290) * r['y2024'] / mx, rh - 6, '#0f6e66' if i == 0 else ('#b4570f' if i == rows - 1 else '#8cc5bc'), 1] for i, r in enumerate(rg)]
    s4 += [[200, HT, 0, 0, BASE, 0] for _ in range(N - rows)]
    short = lambda nm: nm.replace(' County', '').replace(', and ', ', ').replace(' counties', '')
    l4 = [[192, 28 + i * rh + rh / 2 + 1, short(r['name']), 'end', 400] for i, r in enumerate(rg)] + [[200 + (W - 290) * r['y2024'] / mx + 6, 28 + i * rh + rh / 2 + 1, money(r['y2024']), 'start', 600] for i, r in enumerate(rg)]
    steps = [
     dict(h='Start with one dollar', t='Every dollar that private health insurance spends goes somewhere. Here it is as 100 cents, one square each.', s=grid, l=[[W / 2, 40, '$1 of private health insurance spending', 'middle', 600], [W / 2, HT - 40, 'Each square is 1 cent', 'middle', 400]]),
     dict(h='Hospitals take the biggest slice', t='Nationally, hospitals received %d cents of each private insurance dollar in %d, more than physicians and clinics (%d cents). Insurers kept %d cents for overhead and profit.' % (nhe[0][1], n['year'], nhe[1][1], nhe[3][1]), s=s1, l=l1, src='CMS National Health Expenditure Accounts, Table 4, %d. Rounded to whole cents.' % n['year']),
     dict(h='California looks similar', t='In California\'s commercial market, hospital outpatient care alone took %.1f%% of spending in %d and inpatient care %.1f%%: together %.1f cents of every dollar. Pharmacy took %.1f%%.' % (ov['share_hosp_outpatient'], oh['year'], ov['share_hosp_inpatient'], ov['share_hosp_outpatient'] + ov['share_hosp_inpatient'], ov['share_pharmacy']), s=s2, l=l2, src='%s, %s. A different measure from the national one above: California commercial market only.' % (oh['org'], oh['title'])),
     dict(h='And it is growing fast', t='Commercial spending per person in California rose %.1f%% in %d, from %s to %s. The state has set a limit of %.1f%% a year starting in %s, so %d spending was not held to it, but it shows how far the market has to come down.' % (ov['commercial_growth'], oh['year'], money(ov['commercial_pmpy_2023']), money(ov['commercial_pmpy_2024']), tgt[t0], t0, oh['year']), s=s3, l=l3 + [[W / 2, HT - 70 - (g // 8 + 1) * 14 - 22, 'Each square is 0.1 percentage point', 'middle', 400]], src='%s. Target: HCAI Office of Health Care Affordability.' % oh['title']),
     dict(h='Where you live matters', t='Spending per person ranged from %s in %s to %s in the %s. Some of the gap reflects age and health, which these figures do not adjust for.' % (money(rg[0]['y2024']), rg[0]['name'], money(rg[-1]['y2024']), rg[-1]['name'].replace('Eastern counties', 'eastern counties')), s=s4, l=l4, src='%s, by the office\'s 19 regions, %d.' % (oh['title'], oh['year'])),
    ]
    return dict(slug='spending', title='Follow a dollar of health spending', theme='spending', color='#0f6e66', marks=N, shape='rect', steps=steps,
                dek='Where private health insurance money goes, how fast California\'s spending is growing, and how much it differs by region.',
                end=[('theme-spending.html', 'All spending charts'), ('affordability.html', 'Spending by region, in the affordability story')])


# ------------------------------------------------------------------ prices
def prices(root):
    hp = json.load(open(root + '/data/hospital_prices.json'))
    hs = [h for h in hp['hospitals'] if h.get('ip') is not None]
    s = hp['summary']; N = 2 + len(hs)
    x0, x1, vmax = 60, W - 80, 60000
    X = lambda v: x0 + (x1 - x0) * min(v, vmax) / vmax
    r = 4.4
    colors = {1: '#c9d8ee', 2: '#9dbbe3', 3: '#6a98d1', 4: '#3a76bd', 5: '#1b4f8f', None: '#c9cfd9'}
    by = (HT - 80)
    bar = lambda x, v, c, op=1: [x, by - (by - 50) * v / 40000, 90, (by - 50) * v / 40000, c, op]
    hide_at = lambda: [W / 2 + 60, by, 2 * r, 2 * r, '#3a76bd', 0]
    s0 = [bar(W / 2 - 130, s['ip_mcr'], '#a6a49d'), bar(W / 2 + 40, 0, '#1b4f8f')] + [hide_at() for _ in hs]
    s1 = [bar(W / 2 - 130, s['ip_mcr'], '#a6a49d'), bar(W / 2 + 40, s['ip'], '#1b4f8f')] + [hide_at() for _ in hs]
    l0 = [[W / 2 - 85, by + 22, 'Medicare', 'middle', 600], [W / 2 - 85, by - (by - 50) * s['ip_mcr'] / 40000 - 10, money(s['ip_mcr']), 'middle', 600]]
    l1 = l0 + [[W / 2 + 85, by + 22, 'Commercial insurance', 'middle', 600], [W / 2 + 85, by - (by - 50) * s['ip'] / 40000 - 10, money(s['ip']), 'middle', 600]]
    ys = swarm([h['ip'] for h in hs], X, HT / 2, r=r, band=230)
    gone = lambda st_: [st_[0][:5] + [0], st_[1][:5] + [0]]
    s2 = gone(s1) + [[X(h['ip']) - r, y - r, 2 * r, 2 * r, '#3a76bd', 1] for h, y in zip(hs, ys)]
    ips = sorted(h['ip'] for h in hs); q = st.quantiles(ips, n=10)
    axis = [[X(v), HT - 30, money(v) if v else '$0', 'middle', 400] for v in (0, 20000, 40000, 60000)]
    l2 = axis + [[X(q[0]), 40, '10th percentile ' + money(q[0]), 'middle', 600], [X(q[8]), 62, '90th percentile ' + money(q[8]), 'middle', 600]]
    rows = [5, 4, 3, 2, 1, None]; rh = (HT - 90) / len(rows)
    rowy = {k: 30 + i * rh + rh / 2 for i, k in enumerate(rows)}
    grp = {k: [h for h in hs if h.get('stars') == k] for k in rows}
    rowpos = {}
    for k in rows:
        yy = swarm([h['ip'] for h in grp[k]], X, rowy[k], r=3.6, band=rh - 6)
        for h, y in zip(grp[k], yy):
            rowpos[id(h)] = y
    s3 = gone(s1) + [[X(h['ip']) - 3.6, rowpos[id(h)] - 3.6, 7.2, 7.2, colors[h.get('stars')], 1] for h in hs]
    meds = {k: st.median([h['ip'] for h in grp[k]]) for k in rows if grp[k]}
    l3 = axis + [[x0 - 8, rowy[k] + 4, ('%d star%s' % (k, '' if k == 1 else 's')) if k else 'No rating', 'end', 600] for k in rows] + [[W - 6, rowy[k] + 4, money(meds[k]), 'end', 600] for k in rows if k and k in meds] + [[W - 6, 22, 'Median', 'end', 400]]
    xr0, xr1, rmax = 60, W - 30, 6.0
    XR = lambda v: xr0 + (xr1 - xr0) * min(v, rmax) / rmax
    hx = [h for h in hs if h.get('ip_x')]
    ysr = swarm([h['ip_x'] for h in hx], XR, HT / 2, r=r, band=230)
    pos = {id(h): (XR(h['ip_x']) - r, y - r) for h, y in zip(hx, ysr)}
    above3 = sum(1 for h in hx if h['ip_x'] > 3)
    s4 = gone(s1) + [[pos[id(h)][0], pos[id(h)][1], 2 * r, 2 * r, '#b4570f' if h['ip_x'] > 3 else '#3a76bd', 1] if id(h) in pos else [x0, HT, 0, 0, BASE, 0] for h in hs]
    l4 = [[XR(v), HT - 30, '%dx' % v if v else '0', 'middle', 400] for v in (0, 1, 2, 3, 4, 5, 6)] + [[XR(1), 40, 'Medicare = 1x', 'middle', 600], [XR(s['ip_x']), 62, 'median %.2fx' % s['ip_x'], 'middle', 600]]
    lines4 = [[XR(1), 50, XR(1), HT - 46]]
    steps = [
     dict(h='Start with Medicare', t='For a hospital stay, adjusted for how sick the patient was, Medicare paid the median California hospital %s in %d.' % (money(s['ip_mcr']), hp['year']), s=s0, l=l0, src='HCAI Hospital Measurement dataset, %d reporting year. Median across hospitals.' % hp['year']),
     dict(h='Commercial insurers paid about twice as much', t='For the same kind of stay, commercial insurers paid the median hospital %s: %.2f times Medicare.' % (money(s['ip']), s['ip_x']), s=s1, l=l1, src='Ratio is the median of each hospital\'s own ratio.'),
     dict(h='But hospitals are far apart', t='Each dot is one of %d general-acute hospitals with at least %d commercial stays. A hospital at the 90th percentile was paid %s per stay, %.1f times one at the 10th percentile (%s).' % (len(hs), hp['min_stays'], money(q[8]), q[8] / q[0], money(q[0])), s=s2, l=l2, lines=[[X(q[0]), 50, X(q[0]), HT - 46], [X(q[8]), 72, X(q[8]), HT - 46]], src='Payments above $60,000 are drawn at the right edge. Part of the spread reflects patient mix the adjustment misses.'),
     dict(h='Paying more is not the same as rating higher', t='Sorted by their federal quality rating, higher-rated hospitals were paid more on average: a median of %s at 5 stars against %s at 1 star. That is a pattern, not proof that price buys quality: larger teaching hospitals tend to rate higher and treat harder cases.' % (money(meds.get(5, 0)), money(meds.get(1, 0))), s=s3, l=l3, lines=[[X(meds[k]), rowy[k] - rh / 2 + 6, X(meds[k]), rowy[k] + rh / 2 - 6] for k in rows if k and k in meds], src='CMS Overall Hospital Quality Star Rating, %s. Dashed ticks mark each group\'s median.' % hp['cms_date']),
     dict(h='Against each hospital\'s own Medicare rate', t='Compared with what Medicare paid the same hospital, commercial insurers paid the median hospital %.2f times as much, and %d hospitals more than 3 times as much (orange).' % (s['ip_x'], above3), s=s4, l=l4, lines=lines4, src='Ratios above 6x are drawn at the right edge.'),
    ]
    return dict(slug='prices', title='One hospital stay, two prices', theme='prices', color='#1b4f8f', marks=N, shape='dot2', steps=steps,
                dek='What commercial insurers paid California hospitals for a stay, against Medicare, against each other, and against quality ratings.',
                end=[('hospital-prices.html', 'Look up any hospital'), ('theme-prices.html', 'All price charts')])


# ------------------------------------------------------------------ finances
def finances(root):
    hosp = json.load(open(root + '/data/hospitals.json'))
    ga = [h for h in hosp['hospitals'] if h['is_general_acute'] is not False and '2023' in h['annual'] and h['annual']['2023'].get('operating_margin') is not None]
    ms = [h['annual']['2023']['operating_margin'] for h in ga]
    N = len(ga); r = 4.2
    LOSS, GAIN = '#b4570f', '#2a78d6'
    col = lambda m: LOSS if m < 0 else GAIN
    per = 20
    grid = [[W / 2 - per * 11 + (i % per) * 22, 50 + (i // per) * 22, 2 * r + 4, 2 * r + 4, BASE, 1] for i in range(N)]
    neg = [i for i, m in enumerate(ms) if m < 0]; pos_ = [i for i, m in enumerate(ms) if m >= 0]
    s1 = [None] * N
    for side, idx, xc in ((0, neg, W * 0.27), (1, pos_, W * 0.73)):
        for j, i in enumerate(idx):
            s1[i] = [xc - 7 * 10 + (j % 14) * 10.5, HT - 70 - (j // 14 + 1) * 10.5, 8, 8, col(ms[i]), 1]
    pct_neg = 100 * len(neg) / N
    l1 = [[W * 0.27, HT - 48, 'Lost money: %d' % len(neg), 'middle', 600], [W * 0.73, HT - 48, 'Made money: %d' % len(pos_), 'middle', 600], [W * 0.27, HT - 30, '%.0f%%' % pct_neg, 'middle', 400], [W * 0.73, HT - 30, '%.0f%%' % (100 - pct_neg), 'middle', 400]]
    lo, hi = -0.4, 0.3
    X = lambda m: 50 + (W - 80) * (max(lo, min(hi, m)) - lo) / (hi - lo)
    ys = swarm(ms, X, HT / 2, r=r, band=260)
    s2 = [[X(m) - r, y - r, 2 * r, 2 * r, col(m), 1] for m, y in zip(ms, ys)]
    med = st.median(ms)
    axis = [[X(v), HT - 30, ('%+d%%' % (v * 100)).replace('+0', '0') if v else '0%', 'middle', 400] for v in (-0.4, -0.2, 0, 0.2)]
    l2 = axis + [[X(med), 40, 'median %+.1f%%' % (med * 100), 'middle', 600]]
    own = {}
    for i, h in enumerate(ga):
        own.setdefault((h.get('segments') or {}).get('ownership') or 'Not reported', []).append(i)
    order = sorted(own, key=lambda k: st.median([ms[i] for i in own[k]]))
    rh = (HT - 90) / len(order); rowy = {k: 34 + j * rh + rh / 2 for j, k in enumerate(order)}
    s3 = [None] * N; l3 = list(axis)
    for k in order:
        ids = own[k]; yy = swarm([ms[i] for i in ids], X, rowy[k], r=3.4, band=rh - 8)
        for i, y in zip(ids, yy):
            s3[i] = [X(ms[i]) - 3.4, y - 3.4, 6.8, 6.8, col(ms[i]), 1]
        m = st.median([ms[i] for i in ids])
        l3 += [[46, rowy[k] - rh / 2 + 12, '%s (%d): median %+.1f%%' % (k, len(ids), m * 100), 'start', 600]]
    sn = {True: [], False: []}
    for i, h in enumerate(ga):
        v = (h.get('segments') or {}).get('safety_net')
        if v is not None: sn[v].append(i)
    rowy2 = {True: HT * 0.33, False: HT * 0.68}
    s4 = [[X(ms[i]) - r, HT + 20, 2 * r, 2 * r, BASE, 0] for i in range(N)]; l4 = list(axis)
    for k in (True, False):
        yy = swarm([ms[i] for i in sn[k]], X, rowy2[k], r=3.6, band=120)
        for i, y in zip(sn[k], yy):
            s4[i] = [X(ms[i]) - 3.6, y - 3.6, 7.2, 7.2, col(ms[i]), 1]
        m = st.median([ms[i] for i in sn[k]])
        l4 += [[46, rowy2[k] - 70, '%s (%d): median %+.1f%%' % ('Safety-net hospitals' if k else 'Other general-acute hospitals', len(sn[k]), m * 100), 'start', 600]]
    ownm = {k: st.median([ms[i] for i in own[k]]) for k in order}
    steps = [
     dict(h='%d hospitals, one year' % N, t='Each dot is one of California\'s %d general-acute hospitals that filed a full-year financial report with the state for fiscal year 2023.' % N, s=grid, l=[[W / 2, 30, 'Each dot is a hospital', 'middle', 600]], src='HCAI annual financial disclosures, FY2023.'),
     dict(h='More than half lost money', t='%d of them (%.0f%%) spent more running the hospital than they took in from patient care and other operations. Investment income can still leave some of them in the black overall.' % (len(neg), pct_neg), s=s1, l=l1, src='Operating margin below zero. Same group as the explorer\'s default view.'),
     dict(h='Most cluster near break-even', t='Lined up by operating margin, most hospitals sit within a few points of zero. The median was %+.1f%%; a few lost or made far more.' % (med * 100), s=s2, l=l2, lines=[[X(0), 50, X(0), HT - 46]], src='Margins beyond -40% or +30% are drawn at the edge.'),
     dict(h='Ownership makes a difference', t='Grouped by who owns them, the median %s hospital ran %+.1f%%, and the median %s hospital %+.1f%%. Small groups move with one or two hospitals.' % (order[-1].lower(), ownm[order[-1]] * 100, order[0].lower(), ownm[order[0]] * 100), s=s3, l=l3, lines=[[X(0), 30, X(0), HT - 46]], src='Ownership as HCAI classifies it in its latest year.'),
     dict(h='Safety-net hospitals are under more pressure', t='Hospitals that qualify for Medicare payments for serving many low-income patients had a median margin of %+.1f%%, against %+.1f%% at other general-acute hospitals.' % (st.median([ms[i] for i in sn[True]]) * 100, st.median([ms[i] for i in sn[False]]) * 100), s=s4, l=l4, lines=[[X(0), 40, X(0), HT - 46]], src='Safety-net: Medicare disproportionate share (DSH) status in the HCAI panel.'),
    ]
    return dict(slug='finances', title='Who is losing money', theme='finances', color='#334155', marks=N, shape='dot', steps=steps,
                dek='California\'s general-acute hospitals in fiscal year 2023: how many lost money on operations, and which kinds of hospitals did worst.',
                end=[('explorer.html', 'Explore every hospital'), ('theme-finances.html', 'All finance charts')])


# ------------------------------------------------------------------ access
def access(root):
    hosp = json.load(open(root + '/data/hospitals.json'))['hospitals']; mat = json.load(open(root + '/data/maternity.json'))
    clo = json.load(open(root + '/data/closures.json')); out = json.load(open(root + '/data/outcomes.json'))
    P, PL, GREY = '#5b3d8a', '#a995cf', BASE
    nb = lambda h, y: (h['annual'].get(str(y)) or {}).get('natural_births')
    base = [h for h in hosp if any((nb(h, y) or 0) >= 100 for y in range(2012, 2024))]
    base.sort(key=lambda h: (h['county'] or '', h['name']))
    stop = {i['oshpd_id']: i for i in mat['items']}
    assert all(k in {h['oshpd_id'] for h in base} for k in stop)
    N = len(base); per = 20; pitch = 22
    gx = lambda i: W / 2 - per * pitch / 2 + (i % per) * pitch + 2
    gy = lambda i: 46 + (i // per) * pitch
    grid = [[gx(i), gy(i), 14, 14, P, 1] for i in range(N)]
    hi = [[gx(i), gy(i), 14, 14, P if h['oshpd_id'] in stop else GREY, 1 if h['oshpd_id'] in stop else .45] for i, h in enumerate(base)]
    # step 3: the hospitals that stopped, stacked by the first year with no natural births
    yrs = list(range(min(i['first_year_zero'] for i in stop.values()), max(i['first_year_zero'] for i in stop.values()) + 1))
    cx = lambda y: 70 + (W - 140) * (y - yrs[0]) / (len(yrs) - 1)
    stack = {y: 0 for y in yrs}; s3 = []
    for i, h in enumerate(base):
        it = stop.get(h['oshpd_id'])
        if it:
            y = it['first_year_zero']; k = stack[y]; stack[y] += 1
            s3.append([cx(y) - 9, HT - 92 - (k + 1) * 22, 18, 18, PL if it['preliminary'] else P, 1])
        else:
            s3.append([gx(i), gy(i), 14, 14, GREY, 0])
    l3 = [[cx(y), HT - 64, "'" + str(y)[2:], 'middle', 400] for y in yrs] + [[cx(y), HT - 92 - stack[y] * 22 - 10, str(stack[y]), 'middle', 600] for y in yrs if stack[y]]
    l3 += [[W / 2, 30, 'Each dot is a hospital, placed at the first year it reported no natural births', 'middle', 400]]
    since20 = sum(1 for i in stop.values() if i['first_year_zero'] >= 2020); prelim = sum(i['preliminary'] for i in stop.values())
    # step 4: hospitals reporting any natural births, every year (bars grow out of the first marks)
    by = list(range(2012, 2025))
    cnt = {y: sum(1 for h in hosp if (nb(h, y) or 0) > 0) for y in by}
    tot = {y: sum(nb(h, y) or 0 for h in hosp) for y in by}
    b0, b1, bw = 50, W - 30, 28; pb = (b1 - b0 - bw) / (len(by) - 1); bh = lambda v: (HT - 150) * v / 250
    s4 = [[b0 + j * pb, HT - 70 - bh(cnt[y]), bw, bh(cnt[y]), PL if y == by[-1] else P, 1] for j, y in enumerate(by)]
    s4 += [[gx(i), HT - 70, 14, 0, GREY, 0] for i in range(len(by), N)]
    l4 = [[b0 + j * pb + bw / 2, HT - 50, "'" + str(y)[2:], 'middle', 400] for j, y in enumerate(by)] + [[b0 + j * pb + bw / 2, HT - 78 - bh(cnt[y]), str(cnt[y]), 'middle', 600 if y in (2015, 2023) else 400] for j, y in enumerate(by)]
    pk = max(by[:-1], key=lambda y: cnt[y])
    # step 5: hospitals that stopped filing, by what actually happened
    cc = clo['counts']
    grp = [('Closed or ended inpatient care', cc.get('closed_permanent', 0) + cc.get('ceased_inpatient_converted', 0), P),
           ('New license, name or campus', cc.get('continues_under_new_license_or_name', 0) + cc.get('merged_into_other_campus', 0), '#9aa1ad'),
           ('Reopened or still open', cc.get('closed_then_reopened', 0) + cc.get('still_operating_stopped_filing', 0), '#c2c7d0'),
           ('Could not verify', cc.get('cannot_verify', 0), '#dde1e7')]
    nstop = sum(g[1] for g in grp)
    short = {grp[0][0]: 'Closed', grp[1][0]: 'Renamed or relicensed', grp[2][0]: 'Reopened or open', grp[3][0]: 'Not verified'}
    s5, l5 = blocks([(short[g[0]], g[1], g[2], str(g[1])) for g in grp], N, size=14, gap=4, cols=5, x0=40, x1=W - 40)
    # step 6: the verified closures, by year, Los Angeles County highlighted
    real = sorted([c for c in clo['items'] if c['status'] in ('closed_permanent', 'ceased_inpatient_converted') and c.get('closed_year')], key=lambda c: (c['closed_year'], c['name']))
    cy = list(range(real[0]['closed_year'], real[-1]['closed_year'] + 1)); cst = {y: 0 for y in cy}
    ccx = lambda y: 80 + (W - 160) * (y - cy[0]) / (len(cy) - 1)
    la = sum(1 for c in real if c['county'] == 'Los Angeles')
    s6 = []
    for c in real:
        y = c['closed_year']; k = cst[y]; cst[y] += 1
        s6.append([ccx(y) - 9, HT - 92 - (k + 1) * 24, 18, 18, P if c['county'] == 'Los Angeles' else PL, 1])
    s6 += [[ccx(cy[0]), HT - 92, 18, 18, GREY, 0] for _ in range(N - len(real))]
    l6 = [[ccx(y), HT - 64, "'" + str(y)[2:], 'middle', 400] for y in cy] + [[60, 40, 'Dark: Los Angeles County (%d)' % la, 'start', 600], [60, 62, 'Light: elsewhere in California (%d)' % (len(real) - la), 'start', 400]]
    state_dc = sum(1 for c in real if 'Developmental Center' in c['name'])
    # step 7: going without care because of cost
    sh = out['shadac']; f_, v_, m_ = next((f, 100 * v, 100 * m) for f, v, m in zip(reversed(sh['California']['care_cost']['frames']), reversed(sh['California']['care_cost']['v']), reversed(sh['California']['care_cost']['moe'])) if v is not None)
    us_ = next(100 * v for f, v in zip(sh['United States']['care_cost']['frames'], sh['United States']['care_cost']['v']) if f == f_)
    k7 = int(round(v_))
    s7 = [[W / 2 - 5 * 30 + (i % 10) * 30, 70 + (i // 10) * 30, 18, 18, P if i < k7 else GREY, 1] if i < 100 else [W / 2, HT / 2, 18, 18, GREY, 0] for i in range(N)]
    l7 = [[W / 2, 40, '%d of every 100 California adults' % k7, 'middle', 600]]
    steps = [
     dict(h='%d hospitals that delivered babies' % N, t='Each dot is one of %d California hospitals that reported at least 100 natural (non-cesarean) births in at least one year from 2012 to 2023.' % N, s=grid, l=[[W / 2, 28, 'Each dot is a hospital', 'middle', 600]], src='HCAI annual financial disclosures. Natural births leave out cesarean deliveries, so they undercount all births.'),
     dict(h='%d stopped for good' % len(stop), t='%d of them later reported no natural births and kept reporting none. That points to a closed birth unit, though the unit may have closed earlier in the year before.' % len(stop), s=hi, l=[[W / 2, 28, '%d of %d' % (len(stop), N), 'middle', 600]], src='Inferred from state filings, not from announcements. CalMatters counted 56 hospitals that stopped delivering babies since 2012, using a broader method.'),
     dict(h='Most since 2020', t='%d of the %d stopped in %d or later. The %d lighter dots in %d rest on preliminary %d data and could change.' % (since20, len(stop), 2020, prelim, yrs[-1], yrs[-1]), s=s3, l=l3, src='First fiscal year with no natural births. FY2024 data are preliminary.'),
     dict(h='Fewer hospitals delivering, and fewer births', t='The number of hospitals reporting any natural births peaked at %d in %d and was %d in 2023. Births fell too: natural births dropped %.0f%% from 2012 to 2023.' % (cnt[pk], pk, cnt[2023], 100 * (1 - tot[2023] / tot[2012])), s=s4, l=l4, src='Hospitals with one or more natural births in the year, from HCAI disclosures. The lighter %d bar is preliminary.' % by[-1]),
     dict(h='Closures are rarer than they look', t='%d California hospitals stopped filing state financial reports after 2012. Checked one by one in news, state and county records, %d had closed or ended inpatient care. Most of the rest had a new owner, name or license.' % (nstop, grp[0][1]), s=s5, l=l5, src='This site\'s research on each hospital, listed with sources in the explorer\'s closures layer.'),
     dict(h='Los Angeles County lost the most', t='Of the %d verified closures, %d were in Los Angeles County. %d of the %d were state developmental centers rather than community hospitals.' % (len(real), la, state_dc, len(real)), s=s6, l=l6, src='Year the hospital closed or ended inpatient care.'),
     dict(h='And people go without', t='In %s, %.1f%% of California adults said they could not get medical care when they needed it because of the cost, against %.1f%% nationally. That is about %d in 100.' % (f_, v_, us_, k7), s=s7, l=l7, src='SHADAC State Health Compare, from the CDC Behavioral Risk Factor Surveillance System. California margin of error ±%.1f points.' % m_),
    ]
    return dict(slug='access', title='Where care is disappearing', theme='access', color=P, marks=N, shape='dotbar', steps=steps,
                dek='Birth units that closed, hospitals that shut, and Californians who go without care because of what it costs.',
                end=[('explorer.html', 'Map closures and birth units'), ('theme-access.html', 'All access charts')])


def build(root, H, head, header, tail, write):
    import hashlib
    made = []
    for spec in (spending(root), prices(root), finances(root), access(root)):
        for s_ in spec['steps']:
            assert len(s_['s']) == spec['marks'], (spec['slug'], s_['h'], len(s_['s']), spec['marks'])
            s_['s'] = [[round(v, 1) if isinstance(v, float) else v for v in m] for m in s_['s']]
            s_['l'] = [[round(v, 1) if isinstance(v, float) else v for v in lab] for lab in s_['l']]
        f = 'story-%s.html' % spec['slug']
        steps = ''.join('<section class="sstep" data-i="%d"><div class="sstep-card"><p class="sstep-n">%d of %d</p><h2>%s</h2><p>%s</p>%s</div></section>' % (
            i, i + 1, len(spec['steps']), H(s_['h']), H(s_['t']), '<p class="sstep-src">%s</p>' % H(s_['src']) if s_.get('src') else '') for i, s_ in enumerate(spec['steps']))
        data = {'W': W, 'H': HT, 'shape': spec['shape'], 'steps': [{'s': s_['s'], 'l': s_['l'], 'ln': s_.get('lines', []), 'alt': s_['t']} for s_ in spec['steps']]}
        end = ''.join('<a class="btn%s" href="%s">%s</a>' % ('' if i == 0 else ' ghost', H(u), H(t)) for i, (u, t) in enumerate(spec['end']))
        out = head('%s | Hospital Price Watch' % spec['title'], spec['dek'], f, '<link rel="stylesheet" href="stories.css">\n') + header(f)
        out += '''<main id="main" class="story-x" style="--tc:%s"><div class="sx-head"><div class="wrap"><p class="theme-kicker"><a href="theme-%s.html">%s</a> &middot; Story</p><h1>%s</h1><p class="lede">%s</p><p class="sx-skip"><a href="theme-%s.html#t-ex">Skip to the charts</a></p></div></div>
<div class="wrap sx"><div class="sx-graphic" aria-hidden="false"><svg id="sx-svg" viewBox="0 0 %d %d" role="img" aria-label="%s"></svg></div><div class="sx-steps">%s
<section class="sstep sx-end"><div class="sstep-card"><h2>Keep going</h2><p>Every number here comes from a chart on this site, with its source, its numbers and a download.</p><p class="sx-btns">%s</p></div></section></div></div>
</main>
<script type="application/json" id="sx-data">%s</script>
''' % (spec['color'], spec['theme'], H(dict(spending='Spending', prices='Hospital prices', finances='Hospital finances', access='Access to care')[spec['theme']]), H(spec['title']), H(spec['dek']), spec['theme'],
       W, HT, H(spec['steps'][0]['t']), steps, end, json.dumps(data, separators=(',', ':')).replace('</', '<\\/'))
        write(f, out + tail('<script src="stories.js"></script>\n'))
        made.append(f)
    return made

"""Renders districts.html from data/districts.json (built by tools/data/build_districts.py). The map and the table are in the HTML,
so the page works without JavaScript; districts.js adds the ZIP lookup, the district panel and table sorting."""
import json, re

BLUES = ['#dbe7f6', '#a9c6ea', '#6fa0d8', '#3a76bd', '#1b4f8f']   # one hue, light to dark: premium level
INSETS = {'la': ('Los Angeles area', (-118.95, -117.55, 33.62, 34.36)), 'bay': ('Bay Area', (-122.62, -121.55, 37.2, 38.12))}


def proj(lon, lat):   # must match tools/data/build_districts.py
    import math
    return ((lon + 124.5) * math.cos(math.radians(37.0)) * 60, (42.1 - lat) * 60)


def bbox(path):
    v = [float(x) for x in re.findall(r'-?\d+\.\d+', path)]
    xs, ys = v[0::2], v[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def build(root, H, head, header, tail, write):
    d = json.load(open(root + '/data/districts.json'))
    D, Y, CY, TY = d['districts'], d['premium_year'], d['credit_year'], d['tces_year']
    py = str(int(Y) - 1)
    ca, us = d['ca'], d['us']
    p = {k: v['premium'][Y] for k, v in D.items()}
    order = sorted(p, key=lambda k: p[k])
    cuts = [p[order[int(len(order) * i / 5)]] for i in range(1, 5)]
    cls = lambda v: sum(v >= c for c in cuts)
    rank = {k: 1 + sum(p[j] > p[k] for j in p) for k in p}      # tied districts share a rank
    ties = {k: sum(p[j] == p[k] for j in p) - 1 for k in p}
    money = lambda v: '$' + format(int(round(v)), ',')
    pct = lambda v: '%.0f%%' % (100 * v)
    pct1 = lambda v: '%.1f%%' % (100 * v)
    chg = lambda a, b: '%+.0f%%' % (100 * (a / b - 1))
    def area(v):
        cs = v['counties']
        lead = cs[0][0] if cs[0][1] >= 0.9 else ', '.join(c[0].replace(' County', '') for c in cs[:3]) + (' counties' if len(cs) > 1 else '')
        return lead, ', '.join(v['places'][:4])

    # map: all districts, plus two zoomed insets for the dense metros
    allb = [bbox(v['path']) for v in D.values()]
    X0, Y0, X1, Y1 = min(b[0] for b in allb), min(b[1] for b in allb), max(b[2] for b in allb), max(b[3] for b in allb)
    def paths(keys):
        return ''.join('<path class="tip d c%d" data-cd="%s" data-tip="%s" d="%s"/>' % (cls(p[k]), k, H('District %d: %s a month in %s' % (int(k), money(p[k]), Y)), D[k]['path']) for k in keys)
    boxes, insets = '', ''
    for key, (name, (lo0, lo1, la0, la1)) in INSETS.items():
        (ax, ay), (bx, by) = proj(lo0, la1), proj(lo1, la0)
        boxes += '<rect class="ibox" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (ax, ay, bx - ax, by - ay)
        keys = [k for k, b in zip(D, allb) if not (b[2] < ax or b[0] > bx or b[3] < ay or b[1] > by)]
        insets += '<figure class="inset"><figcaption>%s</figcaption><svg class="chart dmap" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="%s, zoomed">%s</svg></figure>' % (H(name), ax, ay, bx - ax, by - ay, H(name), paths(keys))
    pad = 4
    mapsvg = '<svg class="chart dmap" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="Map of California\'s 52 congressional districts shaded by the %s benchmark premium">%s%s</svg>' % (
        X0 - pad, Y0 - pad, X1 - X0 + 2 * pad, Y1 - Y0 + 2 * pad, Y, paths(D), boxes)
    edges = [min(p.values())] + cuts + [max(p.values())]
    legend = ''.join('<span><i style="background:%s"></i>%s&ndash;%s</span>' % (BLUES[i], money(edges[i]), money(edges[i + 1])) for i in range(5))

    rows = ''.join(
        '<tr data-cd="%s"><th scope="row"><button type="button" class="link-btn" data-pick="%s">District %d</button><small>%s</small></th><td data-v="%s">%s</td><td data-v="%s">%s</td><td data-v="%s">%s</td><td data-v="%s">%s</td><td data-v="%s">%s</td></tr>' % (
            k, k, int(k), H(' &middot; '.join(x for x in area(v) if x)).replace('&amp;middot;', '&middot;'),
            p[k], money(p[k]), p[k] / v['premium'][py] - 1, chg(p[k], v['premium'][py]), p[k] / v['premium']['2017'] - 1, chg(p[k], v['premium']['2017']),
            v['tces'] if v['tces'] is not None else -1, pct(v['tces']) if v['tces'] is not None else 'n/a',
            v['credit']['creditcard_delinquency_rate'] or -1, pct1(v['credit']['creditcard_delinquency_rate']) if v['credit']['creditcard_delinquency_rate'] is not None else 'n/a')
        for k, v in sorted(D.items()))
    opts = ''.join('<option value="%s">District %d (%s)</option>' % (k, int(k), H(area(v)[0])) for k, v in sorted(D.items()))
    payload = {'Y': Y, 'PY': py, 'CY': CY, 'TY': TY, 'ca': ca, 'us': us, 'rank': rank, 'zips': d['zips'],
               'ties': ties, 'd': {k: {'p': v['premium'], 't': v['tces'], 'c': v['credit'], 'a': area(v)[0], 'pl': v['places']} for k, v in D.items()}}
    hi, lo = order[-1], order[0]
    def named(v):
        ks = sorted(k for k in p if p[k] == v)
        if len(ks) == 1:
            return 'District %d' % int(ks[0])
        cos = {D[k]['counties'][0][0] for k in ks if D[k]['counties'][0][1] >= 0.9}
        where = ' (all within %s)' % cos.pop() if len(cos) == 1 and all(D[k]['counties'][0][1] >= 0.9 for k in ks) else ''
        return '%d districts%s' % (len(ks), where) if len(ks) > 3 else 'Districts ' + ', '.join(str(int(k)) for k in ks[:-1]) + ' and %d' % int(ks[-1])
    big_tie = max(set(p.values()), key=lambda v: sum(x == v for x in p.values()))
    S = d['sources']
    out = head('California by congressional district: health premiums and affordability | Hospital Price Watch',
               'Health insurance premiums, the cost of economic security and credit distress for each of California\'s 52 congressional districts, from the Urban Institute\'s American Affordability Tracker.',
               'districts.html', '<link rel="stylesheet" href="hospital-prices.css">\n<link rel="stylesheet" href="districts.css">\n') + header('districts.html')
    out += '''<main id="main"><div class="page-head"><div class="wrap"><h1>California by congressional district</h1>
<p class="lede">What a Marketplace health plan costs before subsidies, how many people fall short of a secure budget, and how many are behind on bills, for each of California's 52 districts.</p></div></div>
<div class="wrap hp">
<section aria-labelledby="dz-find"><h2 id="dz-find" class="sr">Find a district</h2>
<form class="hp-tools" id="dz-form"><label>ZIP code<input id="dz-zip" inputmode="numeric" pattern="[0-9]{5}" maxlength="5" placeholder="e.g. 90089" autocomplete="postal-code"></label>
<label>Or pick a district<select id="dz-sel"><option value="">Choose a district</option>%s</select></label>
<button class="btn sm" type="submit">Find</button><p class="sub" id="dz-msg" aria-live="polite"></p></form>
<div class="dz-grid"><div class="dz-maps">%s<div class="dz-insets">%s</div>
<p class="dz-legend"><b>Benchmark premium, %s, per month</b>%s</p></div>
<div class="dz-panel" id="dz-panel" aria-live="polite"><p class="sub">Search a ZIP code, pick a district, or click the map. Across California the benchmark plan for a 40-year-old cost <b>%s</b> a month in %s before subsidies, from %s in %s to %s in %s.</p></div></div></section>
<section aria-labelledby="dz-all"><h2 id="dz-all">All 52 districts</h2><p class="sub lead2">Click a column to sort. California: %s a month in %s (%s since %s); %s of people below the cost of economic security; %s of cardholders 60+ days late.</p>
<div class="hp-tbl"><table id="dz-t"><thead><tr><th scope="col">District</th><th scope="col" aria-sort="descending"><button type="button" data-k="1">Premium, %s</button></th><th scope="col"><button type="button" data-k="2">Change since %s</button></th><th scope="col"><button type="button" data-k="3">Since 2017</button></th><th scope="col"><button type="button" data-k="4">Below cost of security, %s</button></th><th scope="col"><button type="button" data-k="5">Card debt 60+ days late, %s</button></th></tr></thead><tbody>%s</tbody></table></div>
<p class="sub"><a href="data/downloads/districts.csv" download>Download the table (CSV)</a></p></section>
<section aria-labelledby="dz-read"><h2 id="dz-read">How to read this</h2><ul class="gaps">
<li><b>Premium.</b> %s It is the sticker price before subsidies. Most Covered California members get federal or state help and pay much less. Dollars are not adjusted for inflation.</li>
<li><b>Why it differs from KFF.</b> Urban averages premiums by population; KFF averages by plan enrollment, so KFF's California benchmark for %s is a little higher. Covered California sets prices for 19 rating regions; Urban gives each county its region's price and averages the counties in a district by population.</li>
<li><b>Cost of economic security.</b> %s Urban advises caution when comparing it across years.</li>
<li><b>Credit card delinquency.</b> %s. From Urban's credit bureau panel, a sample of credit records, not a survey.</li>
<li><b>Districts.</b> Boundaries of the 119th Congress are used for every year, so earlier years describe today's district area. ZIP matches use land area from the Census Bureau, so a ZIP split between districts shows each share. The page names districts, not their representatives.</li>
<li><b>Districts often share a value.</b> Urban builds each district's premium from county prices, and Covered California sets one price for a whole region, so districts inside the same county usually get the same number. For %s, %s show %s a month. Read a district's premium as its county's or region's price, and the ranking as a rough guide.</li>
<li><b>Hospitals are not shown by district.</b> This site places hospitals at city centers, which is not precise enough to assign them to districts.</li>
</ul>
<p class="sub">Source: <a href="%s" target="_blank" rel="noopener">Urban Institute, The American Affordability Tracker</a> (<a href="%s" target="_blank" rel="noopener">data catalog</a>, <a href="%s" target="_blank" rel="noopener">technical appendix</a>), used under the %s license. %s District geography: <a href="%s" target="_blank" rel="noopener">Census Bureau 119th Congressional District relationship files</a> and cartographic boundaries. Data pulled %s.</p></section>
</div></main>
<script type="application/json" id="dz-data">%s</script>
''' % (opts, mapsvg, insets, Y, legend, money(ca['premium'][Y]), Y, money(p[lo]), named(p[lo]), money(p[hi]), named(p[hi]),
       money(ca['premium'][Y]), Y, chg(ca['premium'][Y], ca['premium'][py]), py, pct(ca['tces']), pct1(ca['credit']['creditcard_delinquency_rate']),
       Y, py, TY, CY, rows,
       H(d['definitions']['premium']), Y, H(d['definitions']['tces'] or ''), H(d['definitions']['creditcard'] or ''), Y, named(big_tie), money(big_tie),
       H(S['tool']), H(S['catalog']), H(S['appendix']), H(S['license']), H(S['citation']), H(S['census']), H(d['generated']),
       json.dumps(payload, separators=(',', ':')).replace('</', '<\\/'))
    write('districts.html', out + tail('<script src="districts.js"></script>\n'))
    import csv
    with open(root + '/data/downloads/districts.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['district', 'main_area', 'places'] + ['benchmark_premium_%s' % y for y in sorted(ca['premium'])] + ['tces_share_%s' % TY, 'creditcard_delinquency_%s' % CY, 'auto_delinquency_%s' % CY, 'average_credit_score_%s' % CY, 'source'])
        for k, v in sorted(D.items()):
            w.writerow(['CA-%s' % k, area(v)[0], '; '.join(v['places'])] + [v['premium'].get(y) for y in sorted(ca['premium'])] +
                       [v['tces'], v['credit']['creditcard_delinquency_rate'], v['credit']['auto_delinquency_rate'], v['credit']['average_credit_score'], 'Urban Institute, American Affordability Tracker (ODC-BY 1.0)'])

"""Renders affordability.html from data/affordability.json (built by tools/data/build_affordability.py).
Every figure on the page is read from that file; nothing is typed in by hand."""
import json, math

Y0, Y1 = 2016, 2025


def build(root, H, head, header, tail, write):
    d = json.load(open(root + '/data/affordability.json'))
    cpi_us = d['cpi']['us_all']
    defl = lambda y: cpi_us[str(Y1)] / cpi_us[str(y)]          # to 2025 dollars
    usd = lambda v: '${:,.0f}'.format(v)
    yrs = [str(y) for y in range(Y0, Y1 + 1)]

    def real(series):
        return {y: series[y] * defl(int(y)) for y in yrs if series.get(y) is not None}

    # ---------- chart ----------
    W, HH, L, R, T, B = 440, 210, 46, 64, 20, 30

    def chart(title, lines, fmt, zero=True, years=yrs, aria='', note_2020=True):
        """lines: [(label, cls, {year: value})]"""
        vals = [v for _, _, s in lines for y, v in s.items() if y in years]
        def nice(x):
            e = 10 ** math.floor(math.log10(x)); f = x / e
            return next(m for m in (1, 2, 2.5, 5, 10) if f <= m) * e
        if zero:
            step = nice(max(vals) * 1.05 / 4); lo = 0; hi = step * 4
        else:
            step = nice((max(vals) - min(vals)) * 1.05 / 4); lo = math.floor(min(vals) / step) * step; hi = lo + step * math.ceil((max(vals) - lo) / step)
        xs = lambda y: L + (int(y) - int(years[0])) / (int(years[-1]) - int(years[0])) * (W - L - R)
        ys = lambda v: T + (hi - v) / (hi - lo) * (HH - T - B)
        o = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, HH, H(aria or title))]
        for k in range(int(round((hi - lo) / step)) + 1):
            v = lo + step * k
            o.append('<line class="grid" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text x="%d" y="%.1f" font-size="10" text-anchor="end">%s</text>' % (L, W - R, ys(v), ys(v), L - 6, ys(v) + 3.5, H(fmt(v, True))))
        for y in years:
            if (int(y) - int(years[-1])) % 3 == 0 and int(years[-1]) - int(y) < 40:
                o.append('<text x="%.1f" y="%d" font-size="10" text-anchor="middle">%s</text>' % (xs(y), HH - 10, y))
        if note_2020 and '2020' in years:
            o.append('<line class="mark2020" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/><text x="%.1f" y="%d" font-size="9" text-anchor="middle">2020</text>' % (xs('2020'), xs('2020'), T, HH - B, xs('2020'), T - 6))
        for lab, cls, s in lines:
            pts = [(xs(y), ys(s[y]), y, s[y]) for y in years if y in s]
            o.append('<polyline class="ln %s" points="%s"/>' % (cls, ' '.join('%.1f,%.1f' % (a, b) for a, b, _, _ in pts)))
            for a, b, y, v in pts:
                o.append('<circle class="hit tip" tabindex="0" data-tip="%s" cx="%.1f" cy="%.1f" r="9"/>' % (H('%s, %s: %s' % (lab, y, fmt(v, False))), a, b))
            a, b, y, v = pts[-1]
            o.append('<circle class="dt %s" cx="%.1f" cy="%.1f" r="3.5"/>' % (cls, a, b))
        # direct labels at the right end, nudged apart
        ends = sorted([(ys(s[years[-1]]), lab, cls, s[years[-1]]) for lab, cls, s in lines])
        last = -99
        for yy, lab, cls, v in ends:
            yy = max(yy, last + 13); last = yy
            o.append('<text class="endlab %s" x="%d" y="%.1f" font-size="10.5">%s</text>' % (cls, W - R + 6, yy + 3.5, H(lab)))
        o.append('</svg>')
        rows = ''.join('<tr><th scope="row">%s</th>%s</tr>' % (lab, ''.join('<td>%s</td>' % (fmt(s[y], False) if y in s else '') for y in years)) for lab, _, s in lines)
        tbl = '<details class="dt-wrap"><summary>Data table</summary><div class="tbl"><table><thead><tr><th></th>%s</tr></thead><tbody>%s</tbody></table></div></details>' % (''.join('<th>%s</th>' % y for y in years), rows)
        return '<figure class="fig"><figcaption>%s</figcaption>%s%s</figure>' % (title, ''.join(o), tbl)

    fm_usd = lambda v, ax: ('${:,.0f}'.format(v) if not ax else (('${:,.0f}k'.format(v / 1000) if v % 1000 == 0 else '${:,.1f}k'.format(v / 1000)) if v else '$0'))
    fm_pct = lambda v, ax: '%.0f%%' % v if ax else '%.1f%%' % v
    fm_idx = lambda v, ax: '%.0f' % v if ax else '%.1f' % v

    def sig(m, y='2025'):
        a, b = d['meps'][m]['ca'][y], d['meps'][m]['us'][y]
        se = math.hypot(d['meps'][m]['ca_se'][y], d['meps'][m]['us_se'][y])
        z = abs(a - b) / se
        return a, b, a - b, z

    # ---------- measure table (2025, CA vs US) ----------
    order = [('single_premium', 'Total premium, single coverage'), ('single_contribution', 'Employee share, single coverage'),
             ('single_deductible', 'Deductible, single coverage'), ('family_premium', 'Total premium, family coverage'),
             ('family_contribution', 'Employee share, family coverage'), ('family_deductible', 'Deductible, family coverage'),
             ('hdhp_share', 'Single-coverage enrollees in a high-deductible plan')]
    trs = []
    for m, lab in order:
        a, b, g, z = sig(m)
        pct = m == 'hdhp_share'
        f = (lambda v: '%.1f%%' % v) if pct else usd
        gap = (('+' if g > 0 else '−') + '%.1f pts' % abs(g)) if pct else ('%s%s' % ('+' if g > 0 else '−', usd(abs(g))))
        verdict = ('Evidence California is %s' % ('higher' if g > 0 else 'lower')) if z >= 1.96 else 'Gap within sampling error'
        cls = 'sig' if z >= 1.96 else 'ns'
        trs.append('<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td><td class="%s">%s</td></tr>' % (H(lab), f(a), f(b), gap, cls, verdict))
    tbl = ('<div class="tbl"><table class="cmp"><thead><tr><th>2025 average</th><th>California</th><th>U.S.</th><th>Difference</th><th>Larger than sampling error?</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(trs))

    # ---------- insurance trend panels (real 2025 dollars) ----------
    def pair(m):
        return [('California', 'ca', real(d['meps'][m]['ca'])), ('U.S.', 'us', real(d['meps'][m]['us']))]
    panels = ''.join(chart(t, pair(m), fm_usd, aria=t + ', California and U.S., 2016 to 2025, in 2025 dollars') for m, t in (
        ('single_premium', 'Total premium, single coverage'), ('single_contribution', 'Employee share, single coverage'), ('single_deductible', 'Deductible, single coverage'),
        ('family_premium', 'Total premium, family coverage'), ('family_contribution', 'Employee share, family coverage'), ('family_deductible', 'Deductible, family coverage')))
    hd = chart('High-deductible plan share, single coverage', [('California', 'ca', {y: d['meps']['hdhp_share']['ca'][y] for y in yrs}), ('U.S.', 'us', {y: d['meps']['hdhp_share']['us'][y] for y in yrs})], fm_pct, aria='Share of single-coverage enrollees in a high-deductible plan')

    # ---------- potential exposure (latest vintage only) ----------
    inc_ca, inc_us = d['income']['ca']['2025'], d['income']['us']['2025']
    ex = lambda mc, md, k: (d['meps'][mc][k]['2025'] + d['meps'][md][k]['2025'])
    e_rows = ''
    for lab, mc, md in (('Single coverage', 'single_contribution', 'single_deductible'), ('Family coverage', 'family_contribution', 'family_deductible')):
        ca, us = ex(mc, md, 'ca'), ex(mc, md, 'us')
        e_rows += '<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%.1f%%</td><td>%s</td><td>%s</td><td>%.1f%%</td></tr>' % (lab, usd(ca), usd(inc_ca), ca / inc_ca * 100, usd(us), usd(inc_us), us / inc_us * 100)
    exposure = '<div class="tbl"><table class="cmp"><thead><tr><th rowspan="2">Potential exposure, 2025</th><th colspan="3">California</th><th colspan="3">U.S.</th></tr><tr><th>Employee share + deductible</th><th>Median household income</th><th>Share</th><th>Employee share + deductible</th><th>Median household income</th><th>Share</th></tr></thead><tbody>%s</tbody></table></div>' % e_rows

    # ---------- income ----------
    iy = [str(y) for y in range(2000, 2026)]
    inc_chart = chart('Median household income, 3-year average, 2025 dollars', [('California', 'ca', {y: d['income']['ca'][y] for y in iy if y in d['income']['ca']}), ('U.S.', 'us', {y: d['income']['us'][y] for y in iy if y in d['income']['us']})], fm_usd, years=iy, note_2020=False,
                      aria='Median household income, California and U.S., three-year averages ending 2000 to 2025, in 2025 dollars')

    # ---------- CPI ----------
    def idx(k):
        s = d['cpi'][k]
        return {y: s[y] / s[str(Y0)] * 100 for y in yrs[:-1] if y in s} | ({str(Y1): s[str(Y1)] / s[str(Y0)] * 100} if str(Y1) in s else {})
    cpi_chart = chart('Consumer prices, West region, index (2016 = 100)', [('Medical care', 'c3', idx('west_medical')), ('Shelter', 'c2', idx('west_shelter')), ('All items', 'ca', idx('west_all')), ('U.S. all items', 'us', idx('us_all'))], fm_idx, zero=False, note_2020=False,
                      aria='West-region consumer price index for medical care, shelter and all items, and the U.S. all-items index, 2016 to 2025, 2016 equals 100')

    # ---------- debt ----------
    ny = d['nyfed']
    dy = [str(y) for y in range(2008, 2026)]
    debt1 = chart('Total debt per person, nominal dollars', [('California', 'ca', {y: ny['total_debt_per_capita'][y] for y in dy}), ('U.S.*', 'us', {y: ny['total_debt_per_capita_us'][y] for y in dy})], fm_usd, years=dy, note_2020=False, aria='Total debt balance per person, California and U.S., 2008 to 2025')
    debt2 = chart('Credit-card debt per person, nominal dollars', [('California', 'ca', {y: ny['card_debt_per_capita'][y] for y in dy}), ('U.S.*', 'us', {y: ny['card_debt_per_capita_us'][y] for y in dy})], fm_usd, years=dy, note_2020=False, aria='Credit card balance per person, California and U.S., 2008 to 2025')
    debt3 = chart('Credit-card balances 90+ days delinquent', [('California', 'ca', {y: ny['card_delinq_90_pct'][y] for y in dy}), ('U.S.*', 'us', {y: ny['card_delinq_90_pct_us'][y] for y in dy})], fm_pct, years=dy, note_2020=False, aria='Share of credit card balances 90 or more days delinquent, California and U.S., 2008 to 2025')

    pc = d['meps']['single_premium']
    s25 = d['meps']['single_premium']['ca']['2025']
    out = head('The numbers in detail: household affordability | Hospital Price Watch', 'What employer health coverage costs in California compared with the U.S., next to household income, prices and debt, from federal sources with each source named.', 'affordability-data.html', '<link rel="stylesheet" href="afford.css">\n') + header('affordability.html')
    out += '<main id="main"><div class="page-head"><div class="wrap"><h1>The numbers in detail</h1><p class="lede">What employer health coverage costs in California compared with the U.S., set beside household income, prices and debt.</p></div></div>'
    out += '''<div class="wrap afford">
<aside class="readfirst" aria-label="How to read this page"><h2>Read this first</h2><ul>
<li><b>Whose costs.</b> Premiums and deductibles come from the federal MEPS-IC survey of private-sector employers that offer coverage. They are not what all Californians pay. Public employers, workers at firms with no plan, the self-employed and the uninsured are not in them.</li>
<li><b>Averages, not typical bills.</b> A deductible average covers only enrollees in plans that have one. It is a plan feature, not what a patient actually paid. Actual out-of-pocket spending is not on this page.</li>
<li><b>Dollars.</b> Trend charts are in 2025 dollars, adjusted with the U.S. all-items consumer price index (annual average of monthly values). Census adjusted income to 2025 dollars with its own index (C-CPI-U), and premiums here use CPI-U. Debt charts are nominal and say so.</li>
<li><b>Sampling error.</b> California figures come from a sample. A gap is called real only if it is larger than the combined standard errors (about 1.96 times).</li>
<li><b>Not shown.</b> Medical debt, skipped care, trouble paying bills and out-of-pocket spending are the real consequences of cost, and this page has none of them yet. See the last section.</li></ul>
<p class="asof">%sData pulled %s. Built by <code>tools/data/build_affordability.py</code>; each figure traces to a federal file listed under Sources.</p></aside>
''' % (H(' '.join(d.get('cpi_notes', []))) + ' ' if d.get('cpi_notes') else '', H(d['generated']))
    out += '<section id="exposure"><h2>What employer coverage costs a worker</h2><p class="sub">California and U.S. private-sector employers offering coverage, 2025.</p>%s' % tbl
    lo_ = [l for m, l in order if m != 'hdhp_share' and sig(m)[3] >= 1.96 and sig(m)[2] < 0]
    hi_ = [l for m, l in order if m != 'hdhp_share' and sig(m)[3] >= 1.96 and sig(m)[2] > 0]
    nd_ = [l for m, l in order if m != 'hdhp_share' and sig(m)[3] < 1.96]
    out += '<p class="note">Reading the table: There is evidence California is lower than the U.S. on %s; higher on %s; and the gap is within sampling error on %s. Within sampling error does not mean equal. The tests treat the two estimates as independent although California is inside the national sample, which makes them conservative, and seven comparisons are shown without adjustment.</p>' % (
        '; '.join(x.lower() for x in lo_) or 'none of these measures', '; '.join(x.lower() for x in hi_) or 'none of these measures', '; '.join(x.lower() for x in nd_) or 'none of these measures')
    out += '<h3>Ten-year trends, 2025 dollars</h3><div class="grid3">%s%s</div>' % (panels, hd)
    out += '<p class="note">The dotted line marks 2020, when the pandemic changed both who was employed and how much care was used. California\'s year-to-year swings are partly sampling error (the standard error of its 2024 average single premium was $%s, in nominal dollars), so read the direction over several years, not single points. Dollars are per enrolled employee; percentages are of enrollees.</p>' % usd(d['meps']['single_premium']['ca_se']['2024'])
    out += '<h3>Employee share plus deductible, against income</h3><p class="sub">A rough scale for the latest year, not a maximum and not spending. It adds the average employee share of the premium to the average deductible, and divides by <em>median household income of all households</em> (Census CPS, 3-year average 2023 to 2025). Coinsurance and copayments can add more, many enrollees never reach their deductible, and the deductible average covers only plans that have one. Workers with single coverage probably live in lower-income households than the median, so the single-coverage share probably understates their burden; workers with family coverage probably live in higher-income households, so that share probably overstates it. This page has no worker-income data to check that. The shares are not tested for sampling error.</p>%s' % exposure
    out += '</section>'
    out += '<section id="capacity"><h2>Household income, prices and debt</h2><p class="sub">The household side of the comparison.</p><div class="grid2">%s%s</div>' % (inc_chart, cpi_chart)
    out += '<p class="note">Income is the Census median for all households and is a 3-year average, so each point lags and the 2014 average (2012 to 2014) is not in the Census table. It is not the same as the 2025 employer data above. The price chart is the West region (13 states, not California alone). Medical-care prices measure the price of a fixed basket of care, which is different from what employers pay in premiums, so the two should not be compared as growth rates. Metro-area indexes for Los Angeles and San Francisco are not shown.</p></section>'
    out += '<section id="debt"><h2>Household debt context (not medical debt)</h2><p class="sub">New York Fed credit-bureau data count all debt. They do not say how much comes from medical bills.</p><div class="grid3">%s%s%s</div>' % (debt1, debt2, debt3)
    out += '<p class="note">California\'s total is mostly mortgage debt (%s of %s per person in Q4 2025) because of home prices, so it should not be read as a sign of financial strain. *The file gives states only, so U.S. lines are computed on this site: per-person debt is the average of the 50 states and DC weighted by each state\'s credit-panel population, and the delinquency share is weighted by each state\'s card balances.</p></section>' % (usd(ny['mortgage_debt_per_capita']['2025']), usd(ny['total_debt_per_capita']['2025']))
    out += '''<section id="missing"><h2>Financial consequences: not yet included</h2>
<p class="sub">The page shows costs and household capacity. It does not yet show what happens when the two collide. Each item below is absent, and the source named is what would fill it.</p>
<ul class="gaps">
<li><b>Medical debt in collections</b>, by county, income and race. Needs credit-bureau data from the <a href="https://apps.urban.org/features/debt-interactive-map/" target="_blank" rel="noopener">Urban Institute Debt in America project</a>, which is published there. Not reproduced here.</li>
<li><b>Skipped or delayed care and trouble paying medical bills.</b> Needs California Health Interview Survey microdata. SHADAC publishes California estimates at <a href="https://statehealthcompare.shadac.org/" target="_blank" rel="noopener">State Health Compare</a>. Not reproduced here.</li>
<li><b>Out-of-pocket spending and the share of income going to health care.</b> Needs MEPS Household Component or CPS ASEC microdata.</li>
<li><b>Savings against a deductible.</b> Needs Census SIPP state tables or Federal Reserve SHED survey data.</li>
<li><b>Premium and spending data from California claims.</b> Needs the state's Health Care Payments Data Program.</li></ul>
<p class="note">Related on this site: <a href="exhibits.html?place=ca&amp;topic=prices">hospital price exhibits</a> and <a href="news.html#premiums">premium-increase news</a>. Placing them on one page does not show that hospital prices caused any of the household figures above.</p></section>'''
    srcs = d['sources']
    out += '<section id="sources"><h2>Sources</h2><ul class="gaps">%s</ul></section></div></main>' % ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a>. File: <span class="url">%s</span></li>' % (H(s['url']), H(s['name']), H(s['files'])) for s in srcs.values())
    write('affordability-data.html', out + tail())
    return {'single_premium_ca': s25}

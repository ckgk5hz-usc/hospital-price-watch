"""Renders hospital-prices.html from data/hospital_prices.json (built by tools/data/build_hospital_prices.py). The table is in the HTML, so it works without JavaScript;
hospital-prices.js adds search, a county filter and sorting."""
import json, re, statistics as st


def pretty(name):
    """Readable hospital name from HCAI's capitals. Only changes case."""
    t = re.sub(r"(?<=[a-z])'S\b", "'s", name.title())
    t = re.sub(r"\b(Of|And|The|At|In)\b", lambda m: m.group(1).lower(), t)
    return re.sub(r"\b(Usc|Ucla|Ucsf|Uci|Uc|Pih|Lac|Mc|Ii)\b", lambda m: m.group(1).upper(), t)


def build(root, H, head, header, tail, write):
    d = json.load(open(root + '/data/hospital_prices.json'))
    S, hs, Y = d['summary'], d['hospitals'], d['year']
    money = lambda v: '$' + format(v, ',') if v else '<span class="na">n/a</span>'
    x = lambda v, odd: ('<span class="na">n/a</span>' if v is None else '%.1fx%s' % (v, ' <span class="odd" title="Unusual figure, see note">unusual</span>' if odd else ''))
    star = lambda n: ('<span class="na">no rating</span>' if not n else '<span class="stars" aria-label="%d of 5 stars">%s<i>%s</i></span>' % (n, '&#9733;' * n, '&#9733;' * (5 - n)))
    tb = d['star_table']
    star_rows = ''.join('<tr><th scope="row">%s</th><td>%d</td><td>$%s</td></tr>' % (star(t['stars']), t['n'], format(t['median_ip'], ',')) for t in tb)
    # histogram of the inpatient ratio
    bins = [0] * 9
    vals = [h['ip_x'] for h in hs if h['ip_x']]
    for v in vals:
        bins[min(int(v / .5), 8)] += 1
    W, Hh, b = 640, 190, 24
    bw, mx = W / 9, max(bins)
    bars = ''.join('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/><text x="%.1f" y="%.1f" text-anchor="middle" font-size="12">%d</text><text x="%.1f" y="%d" text-anchor="middle" font-size="11">%s</text>' % (
        'hb hl' if i * .5 <= S['ip_x'] < (i + 1) * .5 else 'hb', i * bw + 6, Hh - b - c / mx * (Hh - b - 22), bw - 12, c / mx * (Hh - b - 22), i * bw + bw / 2, Hh - b - c / mx * (Hh - b - 22) - 5, c, i * bw + bw / 2, Hh - 7,
        ('%.1f&ndash;%.1fx' % (i * .5, (i + 1) * .5)) if i < 8 else '4.0x+') for i, c in enumerate(bins))
    hist = '<svg class="hist" viewBox="0 0 %d %d" role="img" aria-label="Number of hospitals by commercial-to-Medicare ratio. Median %.2f times.">%s</svg>' % (W, Hh, S['ip_x'], bars)
    # county medians, only with enough hospitals to mean anything
    cty = {}
    for h in hs:
        if h['ip'] and h['county']:
            cty.setdefault(h['county'], []).append(h['ip'])
    big = sorted(((st.median(v), k, len(v)) for k, v in cty.items() if len(v) >= 5), reverse=True)
    top = big[0][0]
    ctyhtml = ''.join('<li><span class="rn">%d</span><span class="nm">%s <small>%d hospitals</small></span><span class="rb"><i style="width:%.1f%%"></i></span><span class="rv2">$%s</span></li>' % (i + 1, H(k), n, m / top * 100, format(round(m), ',')) for i, (m, k, n) in enumerate(big))
    rows = ''.join(
        '<tr data-name="%s" data-county="%s"><th scope="row">%s%s<small>%s, %s County</small></th><td data-l="Commercial, per stay" data-v="%s">%s</td><td data-l="Stay, compared with Medicare" data-v="%s">%s</td><td data-l="Commercial, per visit" data-v="%s">%s</td><td data-l="Visit, compared with Medicare" data-v="%s">%s</td><td data-l="CMS quality stars" data-v="%s">%s</td></tr>' % (
            H(h['name'].lower()), H(h['county'] or ''), '<a href="hospital.html?id=%s">%s</a>' % (H(h['id']), H(pretty(h['name']))), ' <span class="hc">OHCA high-cost list</span>' if h['high_cost'] else '', H((h['city'] or '').title()), H(h['county'] or ''),
            h['ip'] or '', money(h['ip']), h['ip_x'] or '', x(h['ip_x'], h['ip_odd']), h['op'] or '', money(h['op']), h['op_x'] or '', x(h['op_x'], h['op_odd']), h['stars'] or '', star(h['stars'])) for h in hs)
    counties = ''.join('<option>%s</option>' % H(c) for c in sorted({h['county'] for h in hs if h['county']}))
    out = head('California hospital price lookup | Hospital Price Watch', 'What commercial insurers paid each California hospital per adjusted stay and visit, compared with Medicare at the same hospital, from HCAI data.', 'hospital-prices.html', '<link rel="stylesheet" href="afford.css">\n<link rel="stylesheet" href="hospital-prices.css">\n') + header('hospital-prices.html')
    out += '''<main id="main"><div class="page-head"><div class="wrap"><h1>What insurers paid California hospitals</h1><p class="lede">Look up a hospital to see what commercial insurers paid it, on average, for a hospital stay or outpatient visit, and how that compares with what Medicare paid the same hospital.</p></div></div>
<div class="wrap hp">
<section class="hp-sum"><div class="hp-big"><div><b>$%s</b><span>Median commercial payment per adjusted hospital stay</span></div><div><b>%.2fx</b><span>Median commercial payment compared with Medicare at the same hospital, stays</span></div><div><b>%.2fx</b><span>The same comparison for outpatient visits</span></div></div>
<p class="sub">%d general acute care hospitals, reporting years ending in %d. These are payments to the hospital averaged across patients, not a bill and not what a patient owes.</p></section>
<section><h2>Find a hospital</h2><div class="hp-tools"><label>Hospital name<input type="search" id="hp-q" placeholder="Start typing a name" autocomplete="off"></label><label>County<select id="hp-c"><option value="">All counties</option>%s</select></label><p class="sub" id="hp-n" aria-live="polite"></p></div>
<div class="tbl hp-tbl"><table id="hp-t"><thead><tr><th scope="col">Hospital</th><th scope="col"><button type="button" data-sort="1">Commercial, per stay</button></th><th scope="col"><button type="button" data-sort="2">Compared with Medicare</button></th><th scope="col"><button type="button" data-sort="3">Commercial, per visit</button></th><th scope="col"><button type="button" data-sort="4">Compared with Medicare</button></th><th scope="col"><button type="button" data-sort="5">CMS quality stars</button></th></tr></thead><tbody>%s</tbody></table></div>
<p class="sub"><a href="data/downloads/hospital_prices.csv">Download this table (CSV)</a>. To cite: Hospital Price Watch, from HCAI Hospital Measurement Combined Dataset, version updated %s.</p></section>
<section><h2>Does paying more buy higher quality?</h2><p class="sub lead2">Median commercial payment per adjusted stay at hospitals with each CMS overall star rating. This shows a pattern, not a cause: teaching hospitals, patient mix and location all differ, and the stars are built mostly from Medicare patients' care.</p><div class="tbl"><table class="two-src star-t"><thead><tr><th>CMS rating</th><th>Hospitals</th><th>Median per stay</th></tr></thead><tbody>%s</tbody></table></div><p class="src">Sources: HCAI, as below; <a href="https://data.cms.gov/provider-data/topics/hospitals/overall-hospital-quality-star-rating/" target="_blank" rel="noopener">CMS Overall Hospital Quality Star Rating</a>, file dated %s.</p></section>
<section><h2>How far apart hospitals are</h2><p class="sub lead2">Number of hospitals at each commercial-to-Medicare ratio for hospital stays. The darker bar holds the median.</p><div class="card-plain">%s</div></section>
<section><h2>By county</h2><p class="sub lead2">Median commercial payment per adjusted stay, for counties with at least five hospitals in the data. A median of hospitals, not weighted by patients.</p><ol class="rank small hp-rank">%s</ol></section>
<section><h2>What other researchers find</h2><p class="sub lead2">RAND's <a href="https://www.rand.org/pubs/research_reports/RRA1144-2-v2.html" target="_blank" rel="noopener">national hospital price study</a> (Round 5.1) reprices private claims at Medicare's rates. It found private payers at 254%% of Medicare in 2022 and placed California among eight states above 300%%. That study uses claims from employers who chose to take part and from 12 state claims databases, none of them California's, and covers about 6%% of U.S. commercial hospital spending. RAND also found more of the price differences were explained by hospital market power than by a hospital's share of Medicare or Medicaid patients.</p>
<p class="sub lead2">To go further: <a href="https://www.sagetransparency.org/" target="_blank" rel="noopener">Sage Transparency</a> shows RAND's hospital-level prices with quality; the <a href="https://tool.nashp.org/" target="_blank" rel="noopener">NASHP Hospital Cost Tool</a> shows what hospitals spend and what they would need to break even, from Medicare cost reports; <a href="https://www.medicare.gov/care-compare/" target="_blank" rel="noopener">Medicare Care Compare</a> shows each hospital's quality measures.</p></section>
<section id="read"><h2>How to read these numbers</h2><ul class="gaps">
<li><b>Adjusted.</b> A stay is adjusted for how complex the patients were (case mix), and a visit for how intensive it was, so hospitals treating sicker patients are not simply shown as pricier. The adjustment is imperfect.</li>
<li><b>Estimated from financial reports.</b> HCAI estimates these from what hospitals report each year, not from individual claims. "Commercial" is HCAI's "other third party" category.</li>
<li><b>A different yardstick from RAND.</b> <a href="https://www.rand.org/health/projects/hospital-pricing/round5.html" target="_blank" rel="noopener">RAND's national study</a> reprices the same services at Medicare rates and found private payers at 254%% of Medicare in 2022. This page divides average payments per adjusted unit, so the two should not be compared directly.</li>
<li><b>Who is left out.</b> Kaiser hospitals and other facilities HCAI treats as non-comparable are not in the file. Psychiatric, rehabilitation and other specialty hospitals are removed here. A stay figure needs at least %d stays for that payer in the year (%d for Medicare too), and a visit figure %s visits; %d hospitals have a commercial stay figure.</li>
<li><b>"Unusual" labels.</b> A ratio below %.2fx or above %.0fx is labeled. It may be real, or it may reflect how a hospital reported its revenue or how many patients it had. Check before relying on it. This page does not rank hospitals from highest to lowest for that reason, though you can sort any column.</li>
<li><b>OHCA high-cost list.</b> The label marks the hospitals the state's <a href="%s" target="_blank" rel="noopener">Office of Health Care Affordability</a> identified using 2018 to 2022 data under its own definition. <a href="https://jamanetwork.com/journals/jama-health-forum/fullarticle/2836506" target="_blank" rel="noopener">A JAMA Health Forum commentary</a> questioned the list because pandemic years and data anomalies affected it.</li>
<li><b>Prices and quality.</b> A higher payment does not by itself show a hospital is overcharging; costs, patient mix and local competition differ. Stars are CMS's single summary of mortality, safety, readmission, patient experience and timely care, and they are built from reported measures. %d hospitals here have a rating; others had too few reported measures or no linked CMS number. Linking uses California's official facility listing, not name matching.</li>
<li><b>Critical access hospitals.</b> Medicare pays these small rural hospitals based on their costs, so their ratios are not comparable with other hospitals'. %d are in this table.</li>
</ul><p class="src">Source: <a href="%s" target="_blank" rel="noopener">HCAI Hospital Measurement Combined Dataset</a>, fiscal years 2022 and 2023, updated %s. Each per-unit figure shown was recomputed from HCAI's revenue and volume columns and matched.</p></section>
</div></main>
''' % (format(round(S['ip']), ','), S['ip_x'], S['op_x'], S['n'], Y, counties, rows, d['updated'], star_rows, d['cms_date'], hist, ctyhtml, d['min_stays'], d['min_stays'], format(d['min_visits'], ','), S['n_ip'], d['odd_low'], d['odd_high'], d['cost_source'], S['with_stars'], S['cah'], d['source'], d['updated'])
    write('hospital-prices.html', out + tail('<script src="hospital-prices.js"></script>\n'))

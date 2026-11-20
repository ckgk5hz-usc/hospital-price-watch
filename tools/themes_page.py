"""Theme hubs: one page per theme (theme-<slug>.html) and the theme tiles on the home page. A theme gathers the site's
exhibits, tools, research and news on one subject. The exhibit lists name exhibit ids; every number shown comes from
those exhibits (computed from data/*.json or typed from a checked source), so a theme page never has numbers of its own."""
import json, re

THEMES = [
 dict(slug='affordability', name='Affordability', color='#9a3412',
      q='What do households pay for health coverage, and who is falling behind?',
      intro='Premiums, worker contributions and deductibles in employer and Marketplace coverage, set against income, plus surveys on skipped care and medical bills. California first, with the U.S. and every congressional district for comparison.',
      lead=['chcfskip', 'mktjump', 'premvsincome'],
      exhibits=['premvsincome', 'premshare', 'workershare', 'deductible', 'hdhp', 'cafamily', 'premium', 'mktjump', 'mkttrend', 'mktdistricts', 'tces', 'chcfskip', 'bills', 'forgone', 'dmhc'],
      tools=[('affordability.html', 'Affordability story', 'Employer coverage costs year by year, with a household calculator'),
             ('districts.html', 'Districts', 'Marketplace premiums and money strain in each of the 52 districts'),
             ('affordability-data.html', 'The numbers in detail', 'Every affordability figure in plain tables'),
             ('news.html#premiums', 'Premium Watch', 'Premium-increase stories, California first')],
      news=('topics', ['insurance']), research=['insurance'],
      outside=[('https://www.kff.org/health-costs/', 'KFF Health Costs'), ('https://www.chcf.org/topic/consumer-affordability', 'CHCF: Consumer affordability'), ('https://www.urban.org/data-tools/american-affordability-tracker', 'Urban Institute Affordability Tracker')]),
 dict(slug='spending', name='Spending', color='#0f6e66',
      q='How fast is total health spending growing, and where does the money go?',
      intro='Commercial health spending per person and its growth against California\'s new spending target, how much differs by region, which services take the largest share, and what drives premium growth.',
      lead=['ohcagrowth', 'ohcashares', 'nhe'],
      exhibits=['ohcagrowth', 'ohcaregions', 'ohcashares', 'nhe', 'yale', 'cpimed', 'dmhc'],
      tools=[('affordability.html', 'Spending by region', 'The state\'s 19 spending regions, in the affordability story'),
             ('exhibits.html?topic=insurance', 'Spending and premium charts', 'Every chart on premiums and spending')],
      news=('title', r'spending|cost growth|health care costs|healthcare costs|OHCA|affordability office|spending target'), research=['insurance'],
      outside=[('https://hcai.ca.gov/affordability/ohca/', 'HCAI Office of Health Care Affordability'), ('https://www.chcf.org/almanac/', 'CHCF California Health Care Almanac'), ('https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data', 'CMS National Health Expenditure data'), ('https://www.healthsystemtracker.org/', 'Peterson-KFF Health System Tracker')]),
 dict(slug='prices', name='Hospital prices', color='#1b4f8f',
      q='What do insurers pay hospitals, and why does it vary so much?',
      intro='What commercial insurers and Medicare actually paid each California hospital, how far apart hospitals are, how price lines up with quality, and the research on why: market power, systems and trauma designation.',
      lead=['ipprice', 'pricespread', 'rand'],
      exhibits=['ipprice', 'opprice', 'pricespread', 'stars', 'rand', 'kffprices', 'sutter', 'trauma'],
      tools=[('hospital-prices.html', 'Hospital prices', 'What insurers and Medicare paid each hospital'),
             ('hospital.html', 'Hospital profiles', 'One hospital\'s prices, finances and quality, or two side by side')],
      news=('topics', ['prices', 'markets']), research=['prices', 'markets'],
      outside=[('https://www.rand.org/health/projects/hospital-pricing.html', 'RAND Health Care Price Transparency Initiative'), ('https://tool.nashp.org/', 'NASHP Hospital Cost Tool'), ('https://www.sagetransparency.com/', 'Sage Transparency')]),
 dict(slug='finances', name='Hospital finances', color='#334155',
      q='Are California hospitals making money, and which ones are struggling?',
      intro='Operating margins from every hospital\'s filings with the state since 2012: how many lose money, how results differ by ownership and safety-net status, who pays the bills, and the shift to outpatient care.',
      lead=['losing', 'margin', 'safetynet'],
      exhibits=['losing', 'margin', 'ownership', 'safetynet', 'payer', 'outpatient', 'uncomp'],
      tools=[('explorer.html', 'Data explorer', 'Chart, map and filter all 441 hospitals'),
             ('hospital.html', 'Hospital profiles', 'Thirteen years of one hospital\'s finances'),
             ('briefs.html', 'Issue briefs', 'The Center\'s briefs on hospital finances')],
      news=('topics', ['finances']), research=['finances'],
      outside=[('https://hcai.ca.gov/data/cost-transparency/hospital-financials/', 'HCAI hospital financial data'), ('https://www.chcf.org/topic/health-care-costs-financing/hospitals/', 'CHCF: Hospital financing')]),
 dict(slug='access', name='Access to care', color='#5b3d8a',
      q='Where is hospital care disappearing, and who goes without?',
      intro='Hospitals that stopped delivering babies, hospitals that closed or ended inpatient care, the drop in emergency visits, and how much free care hospitals provide.',
      lead=['maternity', 'closures', 'uncomp'],
      exhibits=['maternity', 'closures', 'ed', 'uncomp', 'forgone'],
      tools=[('explorer.html', 'Closures and maternity map', 'Map closed hospitals and birth units in the explorer'),
             ('hospital.html', 'Hospital profiles', 'See whether a hospital stopped deliveries')],
      news=('topics', ['access', 'emergency']), research=['emergency'],
      outside=[('https://calmatters.org/health/', 'CalMatters Health'), ('https://www.chcf.org/almanac/', 'CHCF California Health Care Almanac')]),
]


def stat_of(e):
    """The bold figure in an exhibit's one-line claim, used as the tile and key-number value."""
    m = re.search(r'\*\*(.+?)\*\*', e['claim'])
    return m.group(1) if m else ''


def build(root, H, head, header, tail, write, EXN, r_ex, RESEARCH, BRIEFS):
    try:
        news = json.load(open(root + '/data/news.json'))
        news = news['items'] if isinstance(news, dict) else news
    except Exception:
        news = []
    missing = [(t['slug'], x) for t in THEMES for x in t['exhibits'] + t['lead'] if x not in EXN]
    if missing:
        raise SystemExit('theme lists name exhibits that do not exist: %s' % missing)
    plain = lambda s: re.sub(r'\*\*', '', s)
    for t in THEMES:
        how, key = t['news']
        if how == 'topics':
            items = [n for n in news if set(n.get('topics') or []) & set(key)]
        else:
            items = [n for n in news if re.search(key, n.get('title', ''), re.I)]
        items = sorted(items, key=lambda n: n.get('date', ''), reverse=True)[:6]
        reading = [r for r in BRIEFS + RESEARCH if set(r['topics']) & set(t['research'])]
        reading = sorted(reading, key=lambda r: r['date'], reverse=True)[:6]
        keynums = ''.join('<a class="tk" href="#%s"><b>%s</b><span>%s</span></a>' % (x, H(stat_of(EXN[x])), H(plain(EXN[x]['claim']))) for x in t['lead'])
        tools = ''.join('<a class="tt" href="%s"><b>%s</b><span>%s</span></a>' % (H(f), H(n), H(d)) for f, n, d in t['tools'])
        nlist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a><span>%s, %s</span></li>' % (H(n['url']), H(n['title']), H(n.get('source', '')), H(n.get('date', ''))) for n in items) or '<li class="sub">No recent stories on this theme.</li>'
        rlist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a><span>%s</span></li>' % (H(r['url']), H(r['title']), H(r.get('by', ''))) for r in reading) or '<li class="sub">See <a href="research.html">all research</a>.</li>'
        olist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (H(u), H(n)) for u, n in t['outside'])
        others = ''.join('<a href="theme-%s.html" style="--tc:%s">%s</a>' % (o['slug'], o['color'], H(o['name'])) for o in THEMES if o is not t)
        f = 'theme-%s.html' % t['slug']
        out = head('%s: %s | Hospital Price Watch' % (t['name'], t['q'].rstrip('?')), t['intro'], f, '<link rel="stylesheet" href="themes.css">\n') + header(f)
        out += '''<main id="main" class="theme" style="--tc:%s"><div class="theme-head"><div class="wrap"><p class="theme-kicker"><a href="index.html#themes">Themes</a></p><h1>%s</h1><p class="lede">%s</p><p class="theme-intro">%s</p></div></div>
<div class="wrap theme-body">
<section aria-labelledby="t-key"><h2 id="t-key">Key numbers</h2><div class="tk-row">%s</div></section>
<section aria-labelledby="t-tools"><h2 id="t-tools">Tools for this theme</h2><div class="tt-row">%s</div></section>
<section aria-labelledby="t-ex"><h2 id="t-ex">Charts</h2><p class="sub">%d charts. Each has its source, a table of its numbers, a CSV and a citation. <a href="exhibits.html">All exhibits</a>.</p><div class="exgrid">%s</div></section>
<div class="theme-cols">
<section aria-labelledby="t-news"><h2 id="t-news">Recent news</h2><ul class="t-list">%s</ul><p class="sub"><a href="news.html">All news</a></p></section>
<section aria-labelledby="t-read"><h2 id="t-read">Research and briefs</h2><ul class="t-list">%s</ul><p class="sub"><a href="research.html">All research</a> &middot; <a href="briefs.html">Issue briefs</a></p></section>
<section aria-labelledby="t-out"><h2 id="t-out">Elsewhere</h2><ul class="t-list">%s</ul></section>
</div>
<nav class="theme-others" aria-label="Other themes"><span>Other themes</span>%s</nav>
</div></main>
''' % (t['color'], H(t['name']), H(t['q']), H(t['intro']), keynums, tools, len(t['exhibits']), ''.join(r_ex(EXN[x]) for x in t['exhibits']), nlist, rlist, olist, others)
        write(f, out + tail())


def tiles(H, EXN):
    """Home-page tiles: Affordability and Spending large, then the rest."""
    out = []
    for i, t in enumerate(THEMES):
        e = EXN[t['lead'][0]]
        links = ''.join('<li><a href="%s">%s</a></li>' % (H(f), H(n)) for f, n, _ in t['tools'][:3])
        out.append('<article class="tile%s" style="--tc:%s"><a class="tile-main" href="theme-%s.html"><span class="tile-name">%s</span><span class="tile-q">%s</span><b class="tile-stat">%s</b><span class="tile-cap">%s</span><span class="tile-go">Open %s</span></a><ul class="tile-links">%s</ul></article>' % (
            ' big' if i < 2 else '', t['color'], t['slug'], H(t['name']), H(t['q']), H(stat_of(e)), H(re.sub(r'\*\*', '', e['claim'])), H(t['name'].lower()), links))
    return '<div class="tiles">%s</div>' % ''.join(out)

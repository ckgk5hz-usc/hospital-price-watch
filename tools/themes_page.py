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
             ('hospital.html', 'Hospital profiles', 'See whether a hospital stopped deliveries'),
             ('county.html', 'County profiles', 'Hospitals, closures and birth units in each county')],
      news=('topics', ['access', 'emergency']), research=['emergency'],
      outside=[('https://calmatters.org/health/', 'CalMatters Health'), ('https://www.chcf.org/almanac/', 'CHCF California Health Care Almanac')]),
]


# Sub-topics: each theme is broken into a few sub-domains, each with a one-line intro and its charts in reading order.
# These also become the tags on every chart and the Theme / Sub-topic filters on the exhibits page.
SUBS = {
 'affordability': [('employer', 'Employer coverage', 'Most Californians under 65 get coverage through a job. What it costs, who pays, and how fast it has grown.', ['premvsincome', 'premshare', 'workershare', 'deductible', 'hdhp', 'cafamily', 'premium', 'dmhc']),
                   ('marketplace', 'Marketplace plans', 'What a plan bought on Covered California costs before subsidies, and how that differs by district.', ['mktjump', 'mkttrend', 'mktdistricts']),
                   ('strain', 'Households under strain', 'What people do when costs are too high: skip care, carry medical bills, fall short of a secure budget.', ['chcfskip', 'bills', 'forgone', 'tces'])],
 'spending': [('growth', 'Growth vs. the target', 'How fast commercial spending is rising, against the state\'s new limit, and what premiums did.', ['ohcagrowth', 'dmhc']),
              ('where', 'Where the money goes', 'Which services take the largest share of each dollar.', ['ohcashares', 'nhe']),
              ('regions', 'Regional differences', 'Spending per person by the state\'s 19 regions.', ['ohcaregions']),
              ('drivers', 'What drives it', 'Prices against volume, and medical prices against everything else.', ['yale', 'cpimed'])],
 'prices': [('paid', 'What hospitals are paid', 'What commercial insurers and Medicare paid California hospitals, and how far apart hospitals are.', ['ipprice', 'opprice', 'pricespread']),
            ('quality', 'Price and quality', 'Whether hospitals paid more rate higher on federal quality measures.', ['stars']),
            ('national', 'National benchmarks', 'How hospital prices compare across the country and over time.', ['rand', 'kffprices']),
            ('power', 'Market power', 'Research on why some hospitals can charge more.', ['sutter', 'trauma'])],
 'finances': [('margins', 'Margins', 'How many hospitals lose money on patient care, and the median result year by year.', ['losing', 'margin']),
              ('who', 'Who is struggling', 'How results differ by ownership and for safety-net hospitals.', ['ownership', 'safetynet']),
              ('revenue', 'Where revenue comes from', 'Which payers hospitals depend on, and the shift to outpatient care.', ['payer', 'outpatient']),
              ('free', 'Free care', 'Bad debt and charity care as a share of charges.', ['uncomp'])],
 'access': [('births', 'Maternity care', 'Hospitals that stopped delivering babies.', ['maternity']),
            ('closures', 'Closures', 'Hospitals that closed or ended inpatient care.', ['closures']),
            ('er', 'Emergency care', 'The drop in emergency visits and whether it lasted.', ['ed']),
            ('without', 'Going without', 'Care people skip because of cost, and the free care hospitals give.', ['forgone', 'uncomp'])],
}
STORIES = {'affordability': ('affordability.html', 'Follow the money from paycheck to premium'), 'spending': ('story-spending.html', 'Follow a dollar of health spending'),
           'prices': ('story-prices.html', 'One hospital stay, two prices'), 'finances': ('story-finances.html', 'Who is losing money'),
           'access': ('story-access.html', 'Where care is disappearing')}
for _t in THEMES:
    _t['exhibits'] = list(dict.fromkeys(x for _, _, _, xs in SUBS[_t['slug']] for x in xs))


# News: the news classifier's sub-topics (tools/news/taxonomy.json) mapped onto theme sub-topics. Policy-only stories stay untagged.
NEWS_MAP = {'insurance/employer-coverage': ('affordability', 'employer'), 'insurance/marketplace-premiums': ('affordability', 'marketplace'),
            'insurance/premium-increases': ('affordability', 'marketplace'), 'insurance/coverage-insurers': ('affordability', 'strain'),
            'insurance/denials-prior-auth': ('affordability', 'strain'), 'access/charity-medical-debt': ('affordability', 'strain'),
            'prices/affordability-spending': ('spending', 'growth'), 'policy/california-policy': ('spending', 'growth'),
            'insurance/medicare-advantage': ('spending', 'where'), 'insurance/insurer-performance': ('spending', 'where'), 'prices/drug-prices': ('spending', 'drivers'),
            'prices/commercial-rates': ('prices', 'paid'), 'prices/price-transparency': ('prices', 'paid'), 'prices/facility-fees': ('prices', 'paid'), 'prices/surprise-billing': ('prices', 'paid'),
            'markets/mergers': ('prices', 'power'), 'markets/private-equity': ('prices', 'power'), 'markets/antitrust': ('prices', 'power'), 'markets/physician-practices': ('prices', 'power'),
            'finances/margins-profits': ('finances', 'margins'), 'finances/distress-layoffs': ('finances', 'who'), 'finances/capital-investment': ('finances', 'revenue'), 'finances/nonprofit-status': ('finances', 'free'),
            'access/medicaid-cuts': ('access', 'without'), 'access/behavioral-health-access': ('access', 'without'), 'access/rural-safety-net': ('access', 'closures'),
            'access/closures-service-cuts': ('access', 'closures'), 'access/workforce-staffing': ('access', 'closures'), 'emergency/emergency-rooms': ('access', 'er'),
            'emergency/trauma': ('access', 'er'), 'emergency/ambulance': ('access', 'er')}
# Research and briefs carry broad topics; each maps to one or more themes (no sub-topic).
READ_MAP = {'prices': ['prices'], 'markets': ['prices'], 'finances': ['finances'], 'insurance': ['affordability', 'spending'], 'emergency': ['access'], 'access': ['access'], 'policy': []}
# Tool pages belong to themes; shown as a breadcrumb on each page.
PAGE_THEMES = {'hospital-prices.html': ['prices'], 'county.html': ['finances', 'access'], 'hospital.html': ['prices', 'finances'], 'districts.html': ['affordability'], 'affordability.html': ['affordability', 'spending'],
               'affordability-data.html': ['affordability'], 'briefs.html': [], 'research.html': []}
BYSLUG = {}


def theme(slug):
    if not BYSLUG:
        BYSLUG.update({t['slug']: t for t in THEMES})
    return BYSLUG[slug]


def subname(ts, ss):
    return next(nm for sl, nm, _, _ in SUBS[ts] if sl == ss)


def news_tags(item):
    """[(theme slug, theme name, sub slug, sub name, color)] for a news item, from its classifier sub-topics."""
    out = []
    for x in item.get('subtopics') or []:
        if x in NEWS_MAP:
            ts, ss = NEWS_MAP[x]; t = theme(ts)
            tag = (ts, t['name'], ss, subname(ts, ss), t['color'])
            if tag not in out:
                out.append(tag)
    return out


def read_tags(item):
    out = []
    for tp in item.get('topics') or []:
        for ts in READ_MAP.get(tp, []):
            t = theme(ts); tag = (ts, t['name'], '', '', t['color'])
            if tag not in out:
                out.append(tag)
    return out


def apply_tags(exhibits):
    """Give every exhibit its theme/sub-topic tags: [(theme slug, theme name, sub slug, sub name, color)]."""
    by = {e['id']: e for e in exhibits}
    for e in exhibits:
        e['tags'] = []
    for t in THEMES:
        for sl, nm, _, xs in SUBS[t['slug']]:
            for x in xs:
                if x in by:
                    by[x]['tags'].append((t['slug'], t['name'], sl, nm, t['color']))
    untagged = [e['id'] for e in exhibits if not e['tags']]
    if untagged:
        raise SystemExit('exhibits with no theme: %s' % untagged)


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
        tagged = sorted(((n, news_tags(n)) for n in news), key=lambda x: x[0].get('date', ''), reverse=True)
        items = [n for n, tg in tagged if any(g[0] == t['slug'] for g in tg)][:6]
        subnews = {sl: [n for n, tg in tagged if (t['slug'], sl) in [(g[0], g[2]) for g in tg]][:3] for sl, _, _, _ in SUBS[t['slug']]}
        reading = [r for r in BRIEFS + RESEARCH if any(g[0] == t['slug'] for g in read_tags(r))]
        reading = sorted(reading, key=lambda r: r['date'], reverse=True)[:6]
        keynums = ''.join('<a class="tk" href="#%s"><b>%s</b><span>%s</span></a>' % (x, H(stat_of(EXN[x])), H(plain(EXN[x]['claim']))) for x in t['lead'])
        tools = ''.join('<a class="tt" href="%s"><b>%s</b><span>%s</span></a>' % (H(f), H(n), H(d)) for f, n, d in t['tools'])
        nlist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a><span>%s, %s</span></li>' % (H(n['url']), H(n['title']), H(n.get('source', '')), H(n.get('date', ''))) for n in items) or '<li class="sub">No recent stories on this theme.</li>'
        rlist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a><span>%s</span></li>' % (H(r['url']), H(r['title']), H(r.get('by', ''))) for r in reading) or '<li class="sub">See <a href="research.html">all research</a>.</li>'
        olist = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (H(u), H(n)) for u, n in t['outside'])
        others = ''.join('<a href="theme-%s.html" style="--tc:%s">%s</a>' % (o['slug'], o['color'], H(o['name'])) for o in THEMES if o is not t)
        f = 'theme-%s.html' % t['slug']
        st = STORIES.get(t['slug'])
        story_btn = '<p class="theme-story"><a class="btn" href="%s">Read it as a story: %s</a></p>' % (st[0], H(st[1])) if st else ''
        subs = SUBS[t['slug']]
        tabs = '<nav class="subtabs" aria-label="%s sub-topics"><span>Jump to</span>%s</nav>' % (H(t['name']), ''.join('<a href="#s-%s">%s <i>%d</i></a>' % (sl, H(nm), len(xs)) for sl, nm, _, xs in subs))
        def carousel(sl, nm, intro, xs):
            cards = ''.join(r_ex(EXN[x]) for x in xs)
            ctl = '<div class="car-ctl"><button type="button" class="car-prev" aria-label="Previous chart">&#8592;</button><span class="car-n" aria-live="polite">1 of %d</span><button type="button" class="car-next" aria-label="Next chart">&#8594;</button></div>' % len(xs) if len(xs) > 1 else ''
            sn = subnews.get(sl) or []
            nb = '<div class="sub-news"><h4>In the news</h4><ul>%s</ul><a href="news.html?theme=%s&amp;sub=%s">More %s news</a></div>' % (''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a><span>%s, %s</span></li>' % (H(n['url']), H(n['title']), H(n.get('source', '')), H(n.get('date', ''))) for n in sn), t['slug'], sl, H(nm.lower())) if sn else ''
            return '<section class="subsec" id="s-%s" aria-labelledby="h-%s"><div class="subsec-head"><div><h3 id="h-%s">%s</h3><p>%s</p></div>%s</div><div class="car" role="region" aria-label="%s charts" tabindex="0">%s</div>%s</section>' % (sl, sl, sl, H(nm), H(intro), ctl, H(nm), cards, nb)
        subs_html = '<section aria-labelledby="t-ex"><h2 id="t-ex">Charts by sub-topic</h2><p class="sub">%d charts in %d sub-topics. Swipe or use the arrows; every chart has its source, its numbers, a CSV and an embed code. <a href="exhibits.html?theme=%s">Filter them on the exhibits page</a>.</p>%s%s</section>' % (
            len(t['exhibits']), len(subs), t['slug'], tabs, ''.join(carousel(*x) for x in subs))
        out = head('%s: %s | Hospital Price Watch' % (t['name'], t['q'].rstrip('?')), t['intro'], f, '<link rel="stylesheet" href="themes.css">\n') + header(f)
        out += '''<main id="main" class="theme" style="--tc:%s"><div class="theme-head"><div class="wrap"><p class="theme-kicker"><a href="index.html#themes">Themes</a></p><h1>%s</h1><p class="lede">%s</p><p class="theme-intro">%s</p>%s</div></div>
<div class="wrap theme-body">
<section aria-labelledby="t-key"><h2 id="t-key">Key numbers</h2><div class="tk-row">%s</div></section>
<section aria-labelledby="t-tools"><h2 id="t-tools">Tools for this theme</h2><div class="tt-row">%s</div></section>
%s
<div class="theme-cols">
<section aria-labelledby="t-news"><h2 id="t-news">Recent news</h2><ul class="t-list">%s</ul><p class="sub"><a href="news.html?theme=%s">All %s news</a></p></section>
<section aria-labelledby="t-read"><h2 id="t-read">Research and briefs</h2><ul class="t-list">%s</ul><p class="sub"><a href="research.html?theme=%s">All %s research</a> &middot; <a href="briefs.html">Issue briefs</a></p></section>
<section aria-labelledby="t-out"><h2 id="t-out">Elsewhere</h2><ul class="t-list">%s</ul></section>
</div>
<nav class="theme-others" aria-label="Other themes"><span>Other themes</span>%s</nav>
</div></main>
''' % (t['color'], H(t['name']), H(t['q']), H(t['intro']), story_btn, keynums, tools, subs_html, nlist, t['slug'], H(t['name'].lower()), rlist, t['slug'], H(t['name'].lower()), olist, others)
        write(f, out + tail('<script src="themes.js"></script>\n'))


def tiles(H, EXN):
    """Home-page tiles: Affordability and Spending large, then the rest."""
    out = []
    for i, t in enumerate(THEMES):
        e = EXN[t['lead'][0]]
        links = ''.join('<li><a href="%s">%s</a></li>' % (H(f), H(n)) for f, n, _ in t['tools'][:3])
        links = ''.join('<li><a href="theme-%s.html#s-%s">%s</a></li>' % (t['slug'], sl, H(nm)) for sl, nm, _, _ in SUBS[t['slug']])
        if t['slug'] in STORIES: links = '<li><a class="tile-story" href="%s">Story: %s</a></li>' % (STORIES[t['slug']][0], H(STORIES[t['slug']][1])) + links
        out.append('<article class="tile%s" style="--tc:%s"><a class="tile-main" href="theme-%s.html"><span class="tile-name">%s</span><span class="tile-q">%s</span><b class="tile-stat">%s</b><span class="tile-cap">%s</span><span class="tile-go">Open %s</span></a><ul class="tile-links">%s</ul></article>' % (
            ' big' if i < 2 else '', t['color'], t['slug'], H(t['name']), H(t['q']), H(stat_of(e)), H(re.sub(r'\*\*', '', e['claim'])), H(t['name'].lower()), links))
    return '<div class="tiles">%s</div>' % ''.join(out)

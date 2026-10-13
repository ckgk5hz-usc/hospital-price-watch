"""Static site builder. Run from the repo root: python3 tools/build.py
Writes index/exhibits/briefs/news/research/about + redirect stubs. explorer.html is hand-written."""
import html, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from content import *
H = html.escape
BASE = 'https://ckgk5hz-usc.github.io/hospital-price-watch/'

def vbars(items, vmin, vmax, fmt, aria, W=420, Hh=170):
    top, bot = 26, 28; ph = Hh - top - bot
    y = lambda v: top + (vmax - v) / (vmax - vmin) * ph
    y0 = y(0); n = len(items); slot = (W - 40) / n; bw = min(48, slot * .5)
    o = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, Hh, H(aria)), '<line class="axis" x1="20" y1="%.1f" x2="%d" y2="%.1f"/>' % (y0, W-20, y0)]
    for i, (lab, v, kind, tip) in enumerate(items):
        cx = 20 + slot * (i + .5); yy = y(v); ytop = min(yy, y0); hh = max(1.5, abs(yy - y0))
        o.append('<rect class="%s tip" tabindex="0" data-tip="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3"/>' % ('bar' if kind == 'bar' else 'bar-base', H(tip), cx-bw/2, ytop, bw, hh))
        o.append('<text class="valtext" x="%.1f" y="%.1f" font-size="12" text-anchor="middle">%s</text>' % (cx, ytop-6 if v >= 0 else ytop+hh+14, H(fmt(v))))
        o.append('<text x="%.1f" y="%d" font-size="11.5" text-anchor="middle">%s</text>' % (cx, Hh-8, H(lab)))
    return ''.join(o) + '</svg>'

def line(items, vmin, vmax, fmt, aria, W=420, Hh=170):
    top, bot = 26, 28; ph = Hh - top - bot
    y = lambda v: top + (vmax - v) / (vmax - vmin) * ph
    slot = (W - 60) / (len(items) - 1); pts = [(30 + slot * i, y(v)) for i, (l, v, t) in enumerate(items)]
    o = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s">' % (W, Hh, H(aria)),
         '<line class="axis" x1="20" y1="%.1f" x2="%d" y2="%.1f"/><text x="22" y="%.1f" font-size="10">0%%</text>' % (y(0), W-20, y(0), y(0)-4),
         '<polyline class="line-mark" points="%s"/>' % ' '.join('%.1f,%.1f' % p for p in pts)]
    for (px, py), (l, v, t) in zip(pts, items):
        o.append('<circle class="dot-mark" cx="%.1f" cy="%.1f" r="5"/><circle class="tip" tabindex="0" data-tip="%s" fill="transparent" cx="%.1f" cy="%.1f" r="16"/>' % (px, py, H(t), px, py))
        o.append('<text class="valtext" x="%.1f" y="%.1f" font-size="11.5" text-anchor="middle">%s</text>' % (px, py-10 if v >= 0 else py+20, H(fmt(v))))
        o.append('<text x="%.1f" y="%d" font-size="11.5" text-anchor="middle">%s</text>' % (px, Hh-8, H(l)))
    return ''.join(o) + '</svg>'

def chart(e):
    kind, *a = e['chart']
    return (vbars if kind == 'bars' else line)(*a)

def bold(s): return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', H(s))
def ext(u): return ' target="_blank" rel="noopener"' if u.startswith('http') else ''

NAV = [('exhibits.html', 'Exhibits'), ('briefs.html', 'Issue briefs'), ('news.html', 'News'), ('research.html', 'Research'), ('about.html', 'About')]
def head(title, desc, file, extra=''):
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%s</title>
<meta name="color-scheme" content="light">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="%s">
<link rel="canonical" href="%s%s">
<meta property="og:type" content="website"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s%s">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="site.css">
%s</head>
<body>
<a class="skip" href="#main">Skip to content</a>
''' % (H(title), H(desc), BASE, '' if file == 'index.html' else file, H(title), H(desc), BASE, '' if file == 'index.html' else file, extra)

def header(cur):
    links = ''.join('<a href="%s"%s>%s</a>' % (f, ' aria-current="page"' if f == cur else '', t) for f, t in NAV)
    return '''<div class="util"><div class="wrap"><span>An independent research companion to the USC Center for Health Financing, Policy, and Management</span><a href="https://sites.usc.edu/improvinghealth/" target="_blank" rel="noopener">Visit the Center</a></div></div>
<header class="site-header"><div class="wrap">
  <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 12 L6 7 L9 9.5 L14 3.5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>Hospital Price Watch</a>
  <nav class="nav" aria-label="Primary">%s<span class="tool"><a href="explorer.html"%s>Data explorer</a></span></nav>
</div></header>
''' % (links, ' aria-current="page"' if cur == 'explorer.html' else '')

FOOTER = '''<footer class="site-footer"><div class="wrap">
  <div class="fgrid">
    <div><h2>Hospital Price Watch</h2><p>Hospital pricing and affordability, tracked. Built on California's public hospital disclosure data and on published research, with every number tied to its source.</p></div>
    <div><h2>Browse</h2><a href="exhibits.html">Exhibits</a><a href="briefs.html">Issue briefs</a><a href="news.html">News</a><a href="research.html">Research</a></div>
    <div><h2>Data</h2><a href="explorer.html">Data explorer</a><a href="https://github.com/ckgk5hz-usc/hospital-price-watch/blob/main/data/README.md" target="_blank" rel="noopener">Data notes</a><a href="about.html#method">How we source numbers</a></div>
    <div><h2>Parent center</h2><a href="https://sites.usc.edu/improvinghealth/" target="_blank" rel="noopener">Center for Health Financing, Policy, and Management</a><a href="https://sites.usc.edu/improvinghealth/publications/" target="_blank" rel="noopener">All Center publications</a></div>
  </div>
  <div class="fbottom"><span>Prototype built 2026. Not yet on its own domain.</span><span>Research by Glenn Melnick and the Center for Health Financing, Policy, and Management</span></div>
</div></footer>
<script src="site.js"></script>
'''
def tail(extra=''): return FOOTER + extra + '</body>\n</html>\n'
def write(f, s): open(f, 'w').write(s)

def counts(items):
    pc = {k: 0 for k in PLACES}; tc = {k: 0 for k in TOPICS}
    for it in items:
        pc[it['place']] += 1
        for t in it['topics']: tc[t] += 1
    return pc, tc

def facets(items, noun):
    pc, tc = counts(items)
    p = '<li><button class="opt" type="button" data-place="all" aria-pressed="true">All places<span class="count">%d</span></button></li>' % len(items)
    p += ''.join('<li><button class="opt" type="button" data-place="%s" aria-pressed="false">%s<span class="count">%d</span></button></li>' % (k, v, pc[k]) for k, v in PLACES.items())
    t = ''.join('<li><label><span class="lab"><input type="checkbox" data-topic="%s">%s</span><span class="count">%d</span></label></li>' % (k, v, tc[k]) for k, v in TOPICS.items() if tc[k])
    return '<aside class="facets" aria-label="Filter %s"><div class="facet"><h2>Place</h2><ul>%s</ul></div><div class="facet"><h2>Topic</h2><ul>%s</ul></div><button class="link-btn" id="clear" type="button" hidden>Clear filters</button></aside>' % (noun, p, t)

def listpage(file, title, h1, lede, desc, items, render, nounplural, kind, intro_extra=''):
    items = sorted(items, key=lambda i: i['date'], reverse=True)
    body = head(title, desc, file) + header(file)
    body += '<main id="main"><div class="page-head"><div class="wrap"><h1>%s</h1><p class="lede">%s</p></div></div>' % (H(h1), H(lede))
    body += '<div class="wrap split">' + facets(items, nounplural)
    body += '<section aria-label="%s"><div class="results-head"><span><span class="n" id="count">%d</span> <span id="noun">%s</span></span></div>' % (nounplural, len(items), nounplural)
    body += '<%s id="results" class="%s">%s</%s><p class="empty" id="empty" hidden>Nothing matches those filters. <button class="link-btn" type="button" id="reset">Show everything</button></p>%s</section></div></main>' % (
        'div' if kind == 'grid' else 'ul', 'exgrid' if kind == 'grid' else 'rows', ''.join(render(i) for i in items), 'div' if kind == 'grid' else 'ul', intro_extra)
    body += tail('<script src="filter.js"></script>\n')
    write(file, body)

def attrs(i): return 'data-place="%s" data-topics="%s"' % (i['place'], ' '.join(i['topics']))
def tags(i): return '<div class="tags"><span class="chip accent">%s</span>%s</div>' % (PLACES[i['place']], ''.join('<span class="chip">%s</span>' % TOPICS[t] for t in i['topics']))

def r_ex(e):
    t, u = e['link']
    return '<article class="ex" %s><h2 class="claim" style="font-size:1.2rem">%s</h2>%s<div class="foot"><span class="src">%s</span><span><a href="%s"%s>%s</a></span>%s</div></article>' % (attrs(e), bold(e['claim']), chart(e), H(e['source']), H(u), ext(u), H(t), tags(e).replace('class="tags"', 'class="tags" style="margin-top:4px"'))
def r_brief(b):
    return '<li class="row" %s><div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3><p>%s</p><div class="by">%s</div>%s</div><div class="side">%s</div></li>' % (attrs(b), H(b['url']), H(b['title']), H(b['summary']), H(b['by']), tags(b), H(b['datelabel']))
def r_news(n):
    note = '<div class="by">%s</div>' % H(n['note']) if n.get('note') else ''
    return '<li class="row" %s><div><div class="meta" style="font-weight:600;color:var(--accent-ink);margin-bottom:4px">%s</div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3>%s%s</div><div class="side">%s</div></li>' % (attrs(n), H(n['outlet']), H(n['url']), H(n['title']), note, tags(n), H(n['datelabel']))
def r_res(r):
    return '<li class="row" %s><div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3><div class="by">%s</div>%s</div><div class="side">%s</div></li>' % (attrs(r), H(r['url']), H(r['title']), H(r['by']), tags(r), H(r['datelabel']))

listpage('exhibits.html', 'Exhibits: hospital finance and price charts | Hospital Price Watch', 'Exhibits', 'One chart, one sentence, one source. Filter by place and topic.',
  'Charts on California and U.S. hospital finances, prices, and premiums, each with a one-line takeaway and its source.', EXHIBITS, r_ex, 'exhibits', 'grid',
  '<p class="src" style="margin-top:28px;max-width:70ch">Charts marked "computed on this site" are built from the state\'s public hospital financial disclosures; the rest restate a published finding and name it. Hospitals whose reporting period was shorter than a year are left out of the yearly figures.</p>')
also = '<div style="margin-top:32px;padding:22px 24px;border:1px solid var(--rule);border-radius:var(--r-lg);background:var(--wash)"><h2 style="font-size:1.15rem;margin-bottom:10px">More questions the Center\'s California brief series takes up</h2><ul style="margin:0;padding-left:20px;color:var(--ink-2)">%s</ul><p class="src" style="margin:12px 0 0">See the Center\'s <a href="https://sites.usc.edu/improvinghealth/issue-briefs/" target="_blank" rel="noopener">issue briefs page</a> for what is published so far.</p></div>' % ''.join('<li>%s</li>' % H(q) for q in BRIEFS_ALSO)
listpage('briefs.html', 'Issue briefs on hospital finance and prices | Hospital Price Watch', 'Issue briefs', 'Short, policy-focused reads on hospital finances and prices.',
  'Issue briefs on California and U.S. hospital finances and prices from the USC Center, KFF, and the Health Care Cost Institute.', BRIEFS, r_brief, 'issue briefs', 'rows', also)
listpage('news.html', 'News on hospital costs and health care affordability | Hospital Price Watch', 'News', 'Independent coverage of hospital costs and affordability, picked by hand.',
  'News and commentary on California and U.S. hospital costs, premiums, and health policy.', NEWS, r_news, 'stories', 'rows',
  '<p class="src" style="margin-top:28px;max-width:70ch">Checked on October 11 and 12, 2026. This site has no backend, so the list is updated by hand, not by a feed. Outlets are independent of the Center, apart from the commentary written by Glenn Melnick.</p>')
listpage('research.html', 'Reports and research on hospital prices and premiums | Hospital Price Watch', 'Reports and research', 'Peer-reviewed papers and major reports from the Center and from national researchers.',
  'Reports and peer-reviewed research on California and U.S. hospital prices, finances, and premiums.', RESEARCH, r_res, 'reports', 'rows',
  '<p style="margin-top:24px"><a class="btn ghost sm" href="https://sites.usc.edu/improvinghealth/publications/" target="_blank" rel="noopener">All Center publications</a></p>')

# ---------------- home ----------------
latest = sorted(NEWS, key=lambda n: n['date'], reverse=True)[:4]
home_news = ''.join('<li class="row" style="padding:16px 0"><div><div class="meta" style="font-weight:600;color:var(--accent-ink);margin-bottom:2px">%s</div><h3 style="font-size:1.15rem"><a href="%s" target="_blank" rel="noopener">%s</a></h3></div><div class="side">%s</div></li>' % (H(n['outlet']), H(n['url']), H(n['title']), H(n['datelabel'])) for n in latest)
Q = [('Are California hospitals making money?', 'More than half lost money on operations in FY2022 and FY2023. The median hospital was slightly in the red in FY2023 and roughly break-even in preliminary FY2024.', 'See the exhibits', 'exhibits.html?place=ca&topic=finances'),
     ('Do bigger hospital systems charge more?', 'Sutter Health hospitals charged 30% more under all-or-nothing contracts, and system-affiliated hospitals price emergency visits 20% to 30% higher.', 'See the evidence', 'exhibits.html?topic=markets'),
     ('Where is the money going?', 'Employer family coverage now costs $26,993 a year. A Yale study traces 91% of premium growth to higher health care spending.', 'See the national numbers', 'exhibits.html?place=us&topic=insurance')]
qhtml = ''.join('<li class="row" style="grid-template-columns:minmax(0,1fr) auto;align-items:center"><div><h3>%s</h3><p>%s</p></div><a class="btn ghost sm" href="%s">%s</a></li>' % (H(q), H(a), H(u), H(t)) for q, a, t, u in Q)
home = head('Hospital Price Watch: California hospital finances and prices', "Real financial data from every California hospital, plus the research that explains it. Charts, issue briefs, news, and a data explorer built on the state's public disclosures.", 'index.html') + header('index.html')
home += '''<main id="main">
<section class="hero"><div class="wrap hero-grid">
  <div>
    <h1>California's hospitals, with the books open.</h1>
    <p class="lede" style="margin-top:20px">Financial data from every California hospital, and the research that explains it. Each number on this site names its source.</p>
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:28px"><a class="btn" href="explorer.html">Open the data explorer</a><a class="btn ghost" href="exhibits.html">Browse the exhibits</a></div>
  </div>
  <figure class="hero-map" aria-label="Map of California hospitals colored by operating margin">
    <div id="map" role="img" aria-label="Map of California hospitals. Orange dots lost money on operations in FY2023, blue dots earned a surplus."><div class="map-loading">Loading the map&hellip;</div></div>
    <figcaption><span class="key"><i style="background:#eb6834"></i>Lost money</span><span class="key"><i style="background:#9fa6b2"></i>Break-even</span><span class="key"><i style="background:#2a78d6"></i>Surplus</span><span class="small">Operating margin, FY2023. Dots sit at city centers, not street addresses.</span></figcaption>
  </figure>
</div></section>
<section class="band"><div class="wrap">
  <div class="band-head"><h2>Questions the data answers</h2><a href="exhibits.html">All exhibits</a></div>
  <ul class="rows">%s</ul>
</div></section>
<section class="band tinted"><div class="wrap tool-grid">
  <div><h2>Explore the data yourself</h2><p class="lede" style="margin-top:12px;font-size:1.125rem">Filter 449 hospitals by county, size and payer mix. Search for a measure in plain words, then chart it eleven ways with trend lines and equations shown.</p>
    <p style="display:flex;gap:12px;flex-wrap:wrap;margin-top:24px"><a class="btn" href="explorer.html">Open the data explorer</a><a class="btn ghost" href="explorer.html#preset=losing">Who is losing money?</a></p></div>
  <dl class="facts"><div><dt>449</dt><dd>hospitals</dd></div><div><dt>19</dt><dd>measures</dd></div><div><dt>11</dt><dd>chart types</dd></div><div><dt>3</dt><dd>fiscal years</dd></div></dl>
</div></section>
<section class="band"><div class="wrap">
  <div class="band-head"><h2>In the news</h2><a href="news.html">All news</a></div>
  <ul class="rows">%s</ul>
</div></section>
<section class="band tinted"><div class="wrap method">
  <div><h2>How we source every number</h2></div>
  <div><p>Hospital-level figures come from California's Hospital Annual Financial Disclosure data. Everything else is a published finding, cited by author, outlet and date. If a method is borrowed, we say whose it is.</p><p style="margin-top:16px"><a href="about.html#method">Read the sourcing rules</a></p></div>
</div></section>
</main>
''' % (qhtml, home_news)
home = home.replace('<link rel="stylesheet" href="site.css">\n', '<link rel="stylesheet" href="site.css">\n<link rel="stylesheet" href="home.css">\n')
home = home.replace('</head>', '</head>', 1)
write('index.html', home + tail('<script src="home.js"></script>\n'))

# ---------------- about ----------------
about = head('About Hospital Price Watch and how we source numbers', 'What Hospital Price Watch is, who is behind the research, and the rules for how every number is sourced.', 'about.html') + header('about.html')
about += '''<main id="main"><div class="page-head"><div class="wrap"><h1>About</h1><p class="lede">An independent companion to the USC Center for Health Financing, Policy, and Management.</p></div></div>
<div class="wrap aside-grid"><nav class="toc" aria-label="On this page"><a href="#site">The site</a><a href="#center">The Center</a><a href="#method">How we source numbers</a><a href="#data">Data and limits</a><a href="#cite">Cite this</a></nav>
<div class="prose">
<h2 id="site" style="margin-top:0">The site</h2>
<p>Hospital Price Watch collects California hospital financial data and the research around hospital prices and health care affordability in one place. It is built on the Center's published work and on the state's public hospital disclosures. It is a prototype and is not yet on its own domain.</p>
<h2 id="center">The Center</h2>
<p>The Center for Health Financing, Policy, and Management was established in 1996 within the USC Sol Price School of Public Policy. It is led by Glenn Melnick, PhD, Blue Cross of California Chair in Health Care Finance and Senior Scholar at the USC Leonard D. Schaeffer Center for Health Policy &amp; Economics. Its mission is to expand knowledge that improves health care, health system performance and the management of health services.</p>
<p><a href="https://sites.usc.edu/improvinghealth/" target="_blank" rel="noopener">Visit the Center's official site</a></p>
<h2 id="method">How we source numbers</h2>
<h3>Primary data</h3>
<p>Every hospital-level statistic comes directly from California's Hospital Annual Financial Disclosure Data, collected by the Department of Health Care Access and Information (HCAI). Hospitals report income statements, payer mix and utilization every year.</p>
<h3>Published research</h3>
<p>Every other finding is cited by name: journal or outlet, author, year. We do not restate a finding without saying where it came from, and exhibits that restate a finding link to it.</p>
<h3>When we build on someone else's method</h3>
<p>If this site applies an analytical framework developed elsewhere, such as a financial-distress index or an affordability model, we say so directly: <em>method adapted from [source], applied to California data by Hospital Price Watch.</em> A borrowed method, openly credited, is still real research. The same method with the source removed is not.</p>
<h3>News</h3>
<p>News and commentary are picked by hand and checked before they are listed. The site has no backend, so the list does not update itself.</p>
<h2 id="data">Data and limits</h2>
<ul>
<li>449 California hospitals, fiscal years 2022 to 2024, plus an operating-margin panel back to 2020. A fiscal year is the year the reporting period ends.</li>
<li>FY2024 figures are preliminary. Reports covering less than a full year are left out of yearly figures.</li>
<li>Map positions are city centers from the Census Gazetteer, not street addresses. 27 hospitals could not be placed and are not on the map.</li>
<li>Medians are used throughout so a few very large or very small hospitals do not drive results.</li>
</ul>
<p><a href="https://github.com/ckgk5hz-usc/hospital-price-watch/blob/main/data/README.md" target="_blank" rel="noopener">Full data notes and known gaps</a></p>
<h2 id="cite">Cite this</h2>
<p>Hospital Price Watch, built on HCAI Hospital Annual Financial Disclosure Data. When you use a chart, cite the source named under it as well.</p>
</div></div></main>
'''
write('about.html', about + tail('<script>(function(){var l=[].slice.call(document.querySelectorAll(".toc a"));var s=l.map(function(a){return document.getElementById(a.getAttribute("href").slice(1));});if(!("IntersectionObserver" in window))return;var io=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting){l.forEach(function(a){a.classList.remove("on")});l[s.indexOf(x.target)].classList.add("on")}})},{rootMargin:"-20% 0px -70% 0px"});s.forEach(function(x){io.observe(x)})})();</script>\n'))

# ---------------- redirect stubs for the earlier prototype URLs ----------------
for f, to in (('california.html', 'exhibits.html?place=ca'), ('nation.html', 'exhibits.html?place=us')):
    write(f, '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved | Hospital Price Watch</title><meta name="robots" content="noindex"><link rel="canonical" href="%sexhibits.html"><meta http-equiv="refresh" content="0; url=%s"></head><body><p>This page moved to <a href="%s">%s</a>.</p></body></html>\n' % (BASE, to, to, to))
# explorer.html is hand-written; keep its header and footer in sync with the other pages
import re as _re
ex = open('explorer.html').read()
ex = _re.sub(r'<!--HEADER-->.*?<!--/HEADER-->', lambda m: '<!--HEADER-->\n' + header('explorer.html') + '<!--/HEADER-->', ex, flags=_re.S)
ex = _re.sub(r'<!--FOOTER-->.*?<!--/FOOTER-->', lambda m: '<!--FOOTER-->\n' + FOOTER + '<!--/FOOTER-->', ex, flags=_re.S)
write('explorer.html', ex)
print('built')

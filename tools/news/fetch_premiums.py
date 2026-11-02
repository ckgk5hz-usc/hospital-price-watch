#!/usr/bin/env python3
"""Premium watch: collect news stories about health insurance premium increases, for California and every other state.

Source: Google News public RSS search results (one query per topic, plus one per state). Each result is a headline, a publisher name, a date
and a link to the publisher's story. Headline, publisher and date are copied as published. We never copy article text, and no model writes anything.
A headline is kept only if it passes the premium rules in tools/news/taxonomy.json ('premium_watch') and its publisher is named in data/source_policy.json. Place (California / one state / national) comes
from the headline text. Output: data/premiums.json (rolling 120 days). Stdlib only. Run from the repo root:  python3 tools/news/fetch_premiums.py
"""
import concurrent.futures as cf, datetime as dt, hashlib, html, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_news import ROOT, BROWSER_UA, parse_date, clean, fetch_feed, FEEDS
from classify import premium_hit, place_of, STATES

OUT = os.path.join(ROOT, 'data', 'premiums.json')
EXCLUDED = os.path.join(ROOT, 'data', 'premiums_excluded.json')
POLICY = json.load(open(os.path.join(ROOT, 'data', 'source_policy.json'), encoding='utf-8'))
ALLOWED = {name: tier for tier, names in POLICY['tiers'].items() for name in names}
ALIASES, CA_ONLY = POLICY['aliases'], set(POLICY['california_only'])
BLOCKED = {re.sub(r'[^a-z0-9]+', ' ', t.lower()).strip() for t in POLICY['blocked_titles']}
RANK = ['hand-checked', 'official', 'research', 'nonprofit', 'public_media', 'trade', 'national', 'metro']  # which copy of a shared headline to keep
KEEP_DAYS = 120
# California publishers searched one by one, so a California story is found even when statewide searches rank it low.
CA_SITES = ['calmatters.org', 'coveredca.com', 'chcf.org', 'dmhc.ca.gov', 'hcai.ca.gov', 'insurance.ca.gov', 'calpers.ca.gov', 'lao.ca.gov', 'dhcs.ca.gov', 'ppic.org', 'chbrp.org', 'healthpolicy.ucla.edu', 'laborcenter.berkeley.edu',
            'capitolweekly.net', 'latimes.com', 'sfchronicle.com', 'sacbee.com', 'mercurynews.com', 'ocregister.com', 'sandiegouniontribune.com', 'pressdemocrat.com', 'fresnobee.com', 'modbee.com', 'bakersfield.com', 'desertsun.com', 'vcstar.com', 'noozhawk.com', 'independent.com', 'marinij.com',
            'timesofsandiego.com', 'voiceofsandiego.org', 'inewsource.org', 'missionlocal.org', 'sfstandard.com', 'kqed.org', 'laist.com', 'kpbs.org', 'capradio.org', 'kvpr.org']
COMMON = '(premium OR premiums OR rates) (increase OR hike OR rise OR jump OR surge OR higher)'
QUERIES = [('California', f'when:60d ("health insurance" OR "health plan" OR "Covered California") {COMMON} California'),
           ('California', 'when:60d "Covered California" 2027 rates premiums'),
           ('California', 'when:60d California health insurance costs employers workers premiums 2027'),
           ('California', 'when:60d ("Blue Shield of California" OR "Kaiser Permanente" OR Anthem OR "Health Net") California rates increase 2027'),
           ('California', 'when:60d CalPERS OR "California small business" OR "Covered California for Small Business" health premiums 2027'),
           ('National', f'when:60d "health insurance" {COMMON} 2027 ACA marketplace'),
           ('National', 'when:60d employer health insurance costs rise survey KFF premiums workers'),
           ('National', 'when:60d state regulators approve health insurance rate increases 2027'),
           ('National', 'when:60d Medicare Medigap Part D premiums 2027 increase')] + \
          [('California', f'when:120d site:{site} ("health insurance" OR premiums OR "Covered California" OR "health plan" OR "health care costs")') for site in CA_SITES] + \
          [('California', f'when:60d "health insurance" OR "health plan" premiums increase ("{a}") 2027') for a in ('Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'Fresno', 'Inland Empire', 'Central Valley', 'Bay Area', 'Orange County')] + \
          [(s, f'when:60d "health insurance" (premium OR premiums OR rates) (increase OR hike OR rise OR jump) 2027 "{s}"') for s in STATES]

# Publishers read directly (their own feeds, so links go straight to the story). LA Times business is added here because it is not in the main news feeds.
DIRECT = [(name, url) for _, name, url, _, _ in FEEDS] + [('Los Angeles Times', 'https://www.latimes.com/business/rss2.0.xml'), ('Los Angeles Times', 'https://www.latimes.com/california/rss2.0.xml'),
    ('Public Policy Institute of California', 'https://www.ppic.org/feed/'), ('Capitol Weekly', 'https://capitolweekly.net/feed/'), ('LAist', 'https://laist.com/index.atom'), ('Times of San Diego', 'https://timesofsandiego.com/feed/'),
    ('Voice of San Diego', 'https://www.voiceofsandiego.org/feed/'), ('inewsource', 'https://inewsource.org/feed/'), ('Mission Local', 'https://missionlocal.org/feed/')]


def search(q):
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(q) + '&hl=en-US&gl=US&ceid=US:en'
    for n in range(3):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': BROWSER_UA}), timeout=30).read()
            break
        except Exception:
            time.sleep(2 * (n + 1))
    else:
        return None
    out = []
    for it in ET.fromstring(raw).iter('item'):
        g = lambda t: (it.findtext(t) or '').strip()
        src = it.find('source')
        title, pub = clean(g('title')), (src.text or '').strip() if src is not None else ''
        if pub and title.endswith(' - ' + pub):
            title = title[:-len(pub) - 3].rstrip()
        out.append({'title': title, 'url': g('link'), 'source': pub, 'date': parse_date(g('pubDate'))})
    return out


def norm(t):
    return re.sub(r'[^a-z0-9]+', ' ', t.lower()).strip()


def where(title, source):
    """Place from the headline. A publisher that covers only California counts as California unless the headline names another state."""
    place, state = place_of(title)
    return ('california', None) if place == 'national' and source in CA_ONLY else (place, state)


def keep_title(title):
    return premium_hit(title) and norm(title) not in BLOCKED


def one_per_headline(items):
    """Wire and partner stories run word for word at many papers. Keep one copy: official and research first, then the earliest date."""
    best = {}
    for i in items:
        rank = RANK.index('hand-checked' if i.get('found_via') == 'hand-checked' else ALLOWED.get(i['source'], 'metro'))
        k, v = norm(i['title']), (rank, i['date'])
        if k not in best or v < best[k][0]:
            best[k] = (v, i)
    return [x[1] for x in best.values()]


def main():
    now = dt.datetime.now(dt.timezone.utc); cutoff = (now - dt.timedelta(days=KEEP_DAYS)).date().isoformat()
    try:
        prev = json.load(open(OUT, encoding='utf-8'))['items']
    except Exception:
        prev = []
    items, left_out = {}, {}
    for i in prev:  # re-apply today's rules to what was kept before, so a rule change applies to the whole list
        i['source'] = ALIASES.get(i['source'], i['source'])
        if i['source'] not in ALLOWED and i.get('found_via') != 'hand-checked':
            left_out[i['source']] = left_out.get(i['source'], 0) + 1
            continue
        if keep_title(i['title']):
            i['place'], i['state'] = where(i['title'], i['source'])
            items[norm(i['title']) + '|' + i['source']] = i
    failed = []
    with cf.ThreadPoolExecutor(4) as ex:
        for (label, q), res in zip(QUERIES, ex.map(lambda x: (time.sleep(0.4), search(x[1]))[1], QUERIES)):
            if res is None:
                failed.append(label); continue
            for r in res:
                r['source'] = ALIASES.get(r['source'], r['source'])
                if '/site:insurance.ca.gov' in '/' + q and r['source'] == 'Department of Insurance (.gov)':  # generic name, shared with other states; safe only from this search
                    r['source'] = 'California Department of Insurance'
                if not r['date'] or not r['title'] or not r['source'] or not keep_title(r['title']):
                    continue
                if r['source'] not in ALLOWED:
                    left_out[r['source']] = left_out.get(r['source'], 0) + 1
                    continue
                d = r['date'].date().isoformat()
                if d < cutoff or r['date'] > now + dt.timedelta(days=2):
                    continue
                place, state = where(r['title'], r['source'])
                k = norm(r['title']) + '|' + r['source']
                if k in items:
                    continue
                m = re.search(r'\d{1,3}(?:\.\d)?%', r['title'])
                items[k] = {'id': hashlib.sha1(r['url'].encode()).hexdigest()[:12], 'title': r['title'], 'source': r['source'], 'date': d, 'url': r['url'],
                            'place': place, 'state': state, 'figure': m.group(0) if m else None, 'found_via': label}
    for name, url in DIRECT:
        try:
            feed = fetch_feed(url)
        except Exception as e:
            failed.append(name); continue
        for r in feed:
            if not r['date'] or not keep_title(r['title']):
                continue
            d = r['date'].date().isoformat()
            if d < cutoff:
                continue
            k = norm(r['title']) + '|' + name   # a direct link replaces a search-result link from the same publisher
            place, state = where(r['title'], name)
            m = re.search(r'\d{1,3}(?:\.\d)?%', r['title'])
            items[k] = {'id': hashlib.sha1(r['url'].encode()).hexdigest()[:12], 'title': r['title'], 'source': name, 'date': d, 'url': r['url'],
                        'place': place, 'state': state, 'figure': m.group(0) if m else None, 'found_via': 'direct feed'}
    try:  # hand-checked stories (data/news_curated.json) that match the premium rules
        for c in json.load(open(os.path.join(ROOT, 'data', 'news_curated.json'), encoding='utf-8')):
            if keep_title(c['title']):
                place, state = where(c['title'], c['source'])
                k = norm(c['title']) + '|' + c['source']
                items[k] = {'id': hashlib.sha1(c['url'].encode()).hexdigest()[:12], 'title': c['title'], 'source': c['source'], 'date': c['date'], 'url': c['url'],
                            'place': c.get('place') or place, 'state': c.get('state') or state, 'figure': None, 'found_via': 'hand-checked'}
    except Exception:
        pass
    out = sorted((i for i in one_per_headline(items.values()) if i['date'] >= cutoff), key=lambda i: i['date'], reverse=True)[:500]
    for i in out:
        i['tier'] = ALLOWED.get(i['source'], 'hand-checked')
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'generated': now.isoformat(timespec='seconds'), 'queries': len(QUERIES), 'failed_queries': failed, 'count': len(out), 'items': out}, f, indent=1, ensure_ascii=False, allow_nan=False)
    with open(EXCLUDED, 'w', encoding='utf-8') as f:
        json.dump({'note': 'Publishers found by search this run but not on data/source_policy.json, with headline counts. For human review; none of these headlines are published.', 'publishers': dict(sorted(left_out.items(), key=lambda x: (-x[1], x[0])))}, f, indent=1, ensure_ascii=False)
    print('left out', len(left_out), 'publishers,', sum(left_out.values()), 'headlines', file=sys.stderr)
    by = {}
    for i in out: by[i['place']] = by.get(i['place'], 0) + 1
    print('premium stories:', len(out), by, '| failed queries:', failed, file=sys.stderr)


if __name__ == '__main__':
    main()

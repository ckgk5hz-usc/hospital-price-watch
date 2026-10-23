#!/usr/bin/env python3
"""Premium watch: collect news stories about health insurance premium increases, for California and every other state.

Source: Google News public RSS search results (one query per topic, plus one per state). Each result is a headline, a publisher name, a date
and a link to the publisher's story. Headline, publisher and date are copied as published. We never copy article text, and no model writes anything.
A headline is kept only if it passes the premium rules in tools/news/taxonomy.json ('premium_watch'). Place (California / one state / national) comes
from the headline text. Output: data/premiums.json (rolling 120 days). Stdlib only. Run from the repo root:  python3 tools/news/fetch_premiums.py
"""
import concurrent.futures as cf, datetime as dt, hashlib, html, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_news import ROOT, BROWSER_UA, parse_date, clean, fetch_feed, FEEDS
from classify import premium_hit, place_of, STATES

OUT = os.path.join(ROOT, 'data', 'premiums.json')
KEEP_DAYS = 120
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
          [(s, f'when:60d "health insurance" (premium OR premiums OR rates) (increase OR hike OR rise OR jump) 2027 "{s}"') for s in STATES]

# Publishers read directly (their own feeds, so links go straight to the story). LA Times business is added here because it is not in the main news feeds.
DIRECT = [(name, url) for _, name, url, _, _ in FEEDS] + [('Los Angeles Times', 'https://www.latimes.com/business/rss2.0.xml'), ('Los Angeles Times', 'https://www.latimes.com/california/rss2.0.xml')]


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


def main():
    now = dt.datetime.now(dt.timezone.utc); cutoff = (now - dt.timedelta(days=KEEP_DAYS)).date().isoformat()
    try:
        prev = json.load(open(OUT, encoding='utf-8'))['items']
    except Exception:
        prev = []
    items = {}
    for i in prev:  # re-apply today's rules to what was kept before, so a rule change applies to the whole list
        if premium_hit(i['title']):
            i['place'], i['state'] = place_of(i['title'])
            items[norm(i['title']) + '|' + i['source']] = i
    failed = []
    with cf.ThreadPoolExecutor(4) as ex:
        for (label, q), res in zip(QUERIES, ex.map(lambda x: (time.sleep(0.4), search(x[1]))[1], QUERIES)):
            if res is None:
                failed.append(label); continue
            for r in res:
                if not r['date'] or not r['title'] or not r['source'] or not premium_hit(r['title']):
                    continue
                d = r['date'].date().isoformat()
                if d < cutoff or r['date'] > now + dt.timedelta(days=2):
                    continue
                place, state = place_of(r['title'])
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
            if not r['date'] or not premium_hit(r['title']):
                continue
            d = r['date'].date().isoformat()
            if d < cutoff:
                continue
            k = norm(r['title']) + '|' + name
            old = [x for x in items if x.startswith(norm(r['title']) + '|')]
            for x in old:                       # a direct link replaces a search-result link to the same headline
                if x != k: del items[x]
            if k in items:
                continue
            place, state = place_of(r['title'])
            m = re.search(r'\d{1,3}(?:\.\d)?%', r['title'])
            items[k] = {'id': hashlib.sha1(r['url'].encode()).hexdigest()[:12], 'title': r['title'], 'source': name, 'date': d, 'url': r['url'],
                        'place': place, 'state': state, 'figure': m.group(0) if m else None, 'found_via': 'direct feed'}
    try:  # hand-checked stories (data/news_curated.json) that match the premium rules
        for c in json.load(open(os.path.join(ROOT, 'data', 'news_curated.json'), encoding='utf-8')):
            if premium_hit(c['title']):
                place, state = place_of(c['title'])
                k = norm(c['title']) + '|' + c['source']
                items[k] = {'id': hashlib.sha1(c['url'].encode()).hexdigest()[:12], 'title': c['title'], 'source': c['source'], 'date': c['date'], 'url': c['url'],
                            'place': c.get('place') or place, 'state': c.get('state') or state, 'figure': None, 'found_via': 'hand-checked'}
    except Exception:
        pass
    out = sorted((i for i in items.values() if i['date'] >= cutoff), key=lambda i: i['date'], reverse=True)[:500]
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'generated': now.isoformat(timespec='seconds'), 'queries': len(QUERIES), 'failed_queries': failed, 'count': len(out), 'items': out}, f, indent=1, ensure_ascii=False, allow_nan=False)
    by = {}
    for i in out: by[i['place']] = by.get(i['place'], 0) + 1
    print('premium stories:', len(out), by, '| failed queries:', failed, file=sys.stderr)


if __name__ == '__main__':
    main()

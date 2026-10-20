#!/usr/bin/env python3
"""Mass-download titles (and source, date, link) from every feed we use or are considering, for vocabulary analysis.

Titles only. Nothing here is displayed on the site; it feeds tools/news/analyze_corpus.py, which counts words so the topic
taxonomy (tools/news/taxonomy.json) is built from what these outlets actually publish rather than guessed.
Method per source: WordPress REST API (100 per page, walks back in time) where the site has one, else the RSS feed with ?paged=N,
else the single RSS page. Stdlib only. Run from the repo root:  python3 tools/news/harvest_corpus.py [--since 2024-01-01] [--cap 4000]
"""
import argparse, concurrent.futures as cf, datetime as dt, html, json, os, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from fetch_news import parse_feed, clean, ROOT

BR = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
OUT = os.path.join(ROOT, 'data', 'analysis', 'corpus.json')

# (id, display name, base url, method, in_site) method: wp = WP REST; rsspage = RSS ?paged=N; rss = single RSS page
# in_site: True = feed is (or may be) used by the site's news pipeline; False = candidate, kept for vocabulary/comparison
SOURCES = [
 ('kffhn',  'KFF Health News',                  'https://kffhealthnews.org',            'wp', True),
 ('kff',    'KFF',                              'https://www.kff.org',                  'wp', True),
 ('chcf',   'California Health Care Foundation','https://www.chcf.org',                 'wp', True),
 ('calm',   'CalMatters',                       'https://calmatters.org',               'wp', True),
 ('becker', "Becker's Hospital Review",         'https://www.beckershospitalreview.com','wp', True),
 ('chir',   'Georgetown CHIR',                  'https://chir.georgetown.edu',          'wp', False),
 ('nashp',  'NASHP',                            'https://nashp.org',                    'wp', False),
 ('hst',    'Peterson-KFF Health System Tracker','https://www.healthsystemtracker.org', 'wp', False),
 ('capweek','Capitol Weekly',                   'https://capitolweekly.net',            'wp', False),
 ('hcai',   'California HCAI',                  'https://hcai.ca.gov',                  'wp', False),
 ('stat',   'STAT',                             'https://www.statnews.com/feed/',       'rsspage', True),
 ('hdive',  'Healthcare Dive',                  'https://www.healthcaredive.com/feeds/news/', 'rss', True),
 ('fierce', 'Fierce Healthcare',                'https://www.fiercehealthcare.com/rss/xml',   'rss', True),
 ('axios',  'Axios',                            'https://www.axios.com/feeds/feed.rss', 'rss', True),
 ('hafairs','Health Affairs',                   'https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss&jc=hlthaff', 'rss', True),
 ('cmwf',   'Commonwealth Fund',                'https://www.commonwealthfund.org/rss.xml', 'rss', True),
 ('politico','Politico Healthcare',             'https://rss.politico.com/healthcare.xml', 'rss', False),
 ('pnhp',   'PNHP',                             'https://pnhp.org/feed/',               'rss', False),
]


def get(url, ua=BR, timeout=30, tries=3):
    last = None
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': ua, 'Accept': '*/*'}), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (400, 404):      # past the last page / no such endpoint
                raise
            time.sleep(1.5 * (n + 1))
        except Exception as e:
            last = e; time.sleep(1.5 * (n + 1))
    raise last


def wp(base, since, cap):
    out, page = [], 1
    while len(out) < cap:
        url = f'{base}/wp-json/wp/v2/posts?per_page=100&page={page}&orderby=date&order=desc&_fields=date_gmt,title,link'
        try:
            rows = json.loads(get(url))
        except urllib.error.HTTPError as e:
            if e.code in (400, 404) and page > 1:
                break
            raise
        if not rows:
            break
        for r in rows:
            out.append({'title': clean(r['title']['rendered']), 'url': r['link'], 'date': r['date_gmt'][:10]})
        if rows[-1]['date_gmt'][:10] < since:
            break
        page += 1
        time.sleep(0.25)
    return out


def rss(url, since, cap, paged):
    out, seen, page = [], set(), 1
    while len(out) < cap:
        u = url if page == 1 else url + ('&' if '?' in url else '?') + f'paged={page}'
        try:
            items = parse_feed(get(u))
        except urllib.error.HTTPError:
            break
        new = [i for i in items if i['url'] not in seen]
        if not new:
            break
        for i in new:
            seen.add(i['url'])
            out.append({'title': i['title'], 'url': i['url'], 'date': i['date'].date().isoformat() if i['date'] else None})
        if not paged or (new[-1]['date'] and new[-1]['date'].date().isoformat() < since):
            break
        page += 1
        time.sleep(0.25)
    return out


def run(src, since, cap):
    sid, name, base, method, in_site = src
    t0 = time.time()
    try:
        items = wp(base, since, cap) if method == 'wp' else rss(base, since, cap, method == 'rsspage')
        err = None
    except Exception as e:
        items, err = [], str(e)[:100]
    items = [i for i in items if i['date'] is None or i['date'] >= since]
    for i in items:
        i.update(source=name, sid=sid)
    ds = sorted(i['date'] for i in items if i['date'])
    return {'id': sid, 'name': name, 'method': method, 'in_site': in_site, 'ok': err is None and bool(items), 'error': err, 'count': len(items),
            'first': ds[0] if ds else None, 'last': ds[-1] if ds else None, 'secs': round(time.time() - t0, 1)}, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', default='2024-01-01')
    ap.add_argument('--cap', type=int, default=4000, help='max titles per source')
    a = ap.parse_args()
    health, items = [], []
    with cf.ThreadPoolExecutor(6) as ex:
        for h, its in ex.map(lambda s: run(s, a.since, a.cap), SOURCES):
            print(f"{h['id']:8} {h['method']:8} {h['count']:5} {h['first']} -> {h['last']}  {h['error'] or ''}", file=sys.stderr)
            health.append(h); items += its
    seen, uniq = set(), []
    for i in items:
        if i['url'] not in seen:
            seen.add(i['url']); uniq.append(i)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'generated': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'since': a.since, 'sources': health, 'items': uniq}, f, ensure_ascii=False, allow_nan=False)
    print('total titles:', len(uniq), file=sys.stderr)


if __name__ == '__main__':
    main()

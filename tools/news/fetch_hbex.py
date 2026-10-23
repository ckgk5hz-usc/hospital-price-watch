#!/usr/bin/env python3
"""Watch Covered California's Data & Research page (https://hbex.coveredca.com/data-research/) for new documents.

Mechanical page scrape: link text and URL are copied as published, grouped under the page's own section headings. The page shows no dates,
so each link gets 'first_seen' (the day this script first saw it). Nothing is rewritten. Output: data/coveredca_data.json. Stdlib only.
"""
import datetime as dt, html, json, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_news import ROOT, BROWSER_UA

PAGE = 'https://hbex.coveredca.com/data-research/'
OUT = os.path.join(ROOT, 'data', 'coveredca_data.json')


def main():
    raw = urllib.request.urlopen(urllib.request.Request(PAGE, headers={'User-Agent': BROWSER_UA}), timeout=30).read().decode('utf-8', 'ignore')
    try:
        prev = json.load(open(OUT, encoding='utf-8'))
    except Exception:
        prev = {'items': []}
    known = {i['url']: i for i in prev['items']}
    today = dt.date.today().isoformat()
    first_run = not known
    section, items, seen = None, [], set()
    for m in re.finditer(r'<li[^>]*class="tab"[^>]*>\s*<a[^>]*>(.*?)</a>|<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', raw, re.S):
        if m.group(1) is not None:
            section = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).strip(); continue
        href, text = html.unescape(m.group(2)), re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(3)))).strip()
        if not section or not text or href.startswith('#') or href.startswith('mailto:'):
            continue
        if not re.search(r'financial-reports/|data-research/', href):
            continue
        url = urllib.parse.quote(urllib.parse.urljoin(PAGE, href), safe=":/?&=%#")
        if url in seen:
            continue
        seen.add(url)
        old = known.get(url)
        items.append({'section': section, 'title': text, 'url': url, 'first_seen': old['first_seen'] if old else ('baseline' if first_run else today)})
    if len(items) < 20:
        raise SystemExit(f'only {len(items)} links parsed; page layout changed? leaving {OUT} untouched')
    new = [i for i in items if i['first_seen'] == today]
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'source': PAGE, 'generated': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'count': len(items), 'items': items}, f, indent=1, ensure_ascii=False, allow_nan=False)
    print(f'{len(items)} links, {len(new)} new today', file=sys.stderr)
    for i in new: print('  NEW:', i['section'], '|', i['title'], file=sys.stderr)


if __name__ == '__main__':
    main()

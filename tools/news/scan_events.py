#!/usr/bin/env python3
"""List possible public appearances (interviews, talks, events) that mention Glenn Melnick or the Center.

Scans USC Schaeffer and USC Price feeds for 'Melnick'. Output goes to data/events_candidates.json for a human to review.
Nothing here is published: copy a confirmed entry into data/events.json by hand. Stdlib only.
"""
import json, os, re, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from fetch_news import fetch, parse_feed, clean, ROOT

FEEDS = [('USC Schaeffer Center', 'https://schaeffer.usc.edu/feed/'), ('USC Price School', 'https://priceschool.usc.edu/feed/')]
OUT = os.path.join(ROOT, 'data', 'events_candidates.json')
KNOWN = set()
try:
    KNOWN = {i['url'] for i in json.load(open(os.path.join(ROOT, 'data', 'events.json')))['items']}
except Exception:
    pass
found, health = [], []
for name, url in FEEDS:
    try:
        items = parse_feed(fetch(url))
        health.append({'feed': url, 'ok': True, 'items': len(items)})
    except Exception as e:
        health.append({'feed': url, 'ok': False, 'error': str(e)[:100]}); continue
    for it in items:
        if re.search(r'melnick|improving health|Center for Health Financing', it['title'] + ' ' + it['summary'], re.I) and it['url'] not in KNOWN:
            found.append({'source': name, 'title': it['title'], 'url': it['url'], 'date': it['date'].date().isoformat() if it['date'] else None, 'snippet': it['summary']})
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'generated': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'feeds': health, 'candidates': found}, f, indent=1, ensure_ascii=False)
print('candidates:', len(found), file=sys.stderr)

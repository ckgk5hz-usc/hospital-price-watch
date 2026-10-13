#!/usr/bin/env python3
"""Pull hospital-cost and affordability news from public RSS/Atom feeds into data/news.json.

Design rules (see README.md):
  * Displayed text (title, url, source, date, summary) is copied VERBATIM from the feed. No model ever writes or edits it.
  * Step 1: keyword rules decide relevance, place (national / california / one state) and topics.
  * Step 2 (optional): if ANTHROPIC_API_KEY is set, a small model double-checks each NEW item and returns labels only:
    {relevant, place, state, topics, reliable, reason}. Its labels can drop an item or fix its place/topics. It cannot change text.
    Without a key every item is stamped verified_by = "rules-only"; with a key, "llm-verified".
  * Step 3: mechanical link check on new items (404/410 drops the item; 401/403/429 is left as unchecked).
  * Decisions are cached by URL in data/news_cache.json so nothing is re-sent to the model.
Stdlib only. Run from the repo root:  python3 tools/news/fetch_news.py [--no-llm] [--no-linkcheck]
"""
import argparse, datetime as dt, email.utils, hashlib, html, json, os, re, sys, urllib.error, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'data', 'news.json')
CACHE = os.path.join(ROOT, 'data', 'news_cache.json')
CURATED = os.path.join(ROOT, 'data', 'news_curated.json')
UA = 'Mozilla/5.0 (compatible; HospitalPriceWatchBot/1.0; +https://github.com/ckgk5hz-usc/hospital-price-watch)'
KEEP_DAYS = 120
PER_FEED_CAP = 40
MAX_TOTAL = 400
MODEL = 'claude-haiku-5-5'

# (id, display name, url, place hint, strict)  strict=True: general-news feed, needs a stronger keyword score
FEEDS = [
    ('kffhn',   'KFF Health News',            'https://kffhealthnews.org/feed/',                  None,         False),
    ('kff',     'KFF',                        'https://www.kff.org/feed/',                        None,         False),
    ('hdive',   'Healthcare Dive',            'https://www.healthcaredive.com/feeds/news/',       None,         False),
    ('fierce',  'Fierce Healthcare',          'https://www.fiercehealthcare.com/rss/xml',      None,         False),
    ('stat',    'STAT',                       'https://www.statnews.com/feed/',                   None,         True),
    ('becker',  "Becker's Hospital Review",   'https://www.beckershospitalreview.com/feed/',      None,         False),
    ('axios',   'Axios',                      'https://www.axios.com/feeds/feed.rss',             None,         True),
    ('hafairs', 'Health Affairs',             'https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss&jc=hlthaff', None, False),
    ('cmwf',    'Commonwealth Fund',          'https://www.commonwealthfund.org/rss.xml',         None,         False),
    ('chcf',    'California Health Care Foundation', 'https://www.chcf.org/feed/',               'california', False),
    ('calm',    'CalMatters',                 'https://calmatters.org/feed/',                     'california', True),
]

TOPICS = ['prices', 'finances', 'markets', 'emergency', 'insurance', 'access', 'policy']
TOPIC_WORDS = {
    'prices':    r'hospital prices?|price transparency|health care prices|chargemaster|facility fees?|surprise bill|medical bills?|price caps?|reference pric|commercial (?:rates|prices)|site-neutral|prices paid|price growth|price negotiation',
    'finances':  r'operating margin|hospital (?:finances|margins?|profit|losses|revenue)|financial (?:performance|distress)|bankrupt|layoffs?|credit rating|profit',
    'markets':   r'consolidat|merger|acqui(?:re|sition)|private equity|health system|antitrust|market power|monopol|all-or-nothing|vertical integration',
    'emergency': r'emergency (?:room|department|care|visit)|\bER\b|trauma|ambulance|EMTALA',
    'insurance': r'premium|deductible|out-of-pocket|health insurance|health plan|marketplace|obamacare|affordable care act|\bACA\b|medicare advantage|employer coverage|coverage loss|uninsured',
    'access':    r'charity care|uncompensated|medical debt|financial assistance|safety[- ]net|rural hospital|hospital clos|closure|maternity|\bmedi-?cal\b|medicaid|underinsured|skipp(?:ed|ing) care',
    'policy':    r'legislat|\bbill\b|congress|senate|governor|\bCMS\b|rule\b|regulat|spending target|\bOHCA\b|\bHCAI\b|price limit|waiver|budget|reconciliation|executive order|ruling|lawsuit',
}
CORE = re.compile(r'hospitals?\b|health care|healthcare|health systems?|health insurance|health plans?|medicaid|medi-cal|medicare|insurers?\b|uninsured|medical (?:bills?|debt)|health spending|health costs?|price transparency|affordable care act|\bACA\b|marketplace premiums?|health premiums?|out-of-pocket|deductibles?', re.I)
# cheap rules-only guard against obvious non-cost items; the model step does the real judgement
NEG = re.compile(r'vice presidents?|names? (?:new )?(?:chief|CEO|CFO)|\bnaming\b|COVID-19 Tracker|residency programs|\bpodcast\b|webinar|sponsored', re.I)
COST = re.compile(r'price|cost|afford|bill|premium|spend|margin|revenue|profit|payment|pay\b|charge|fee|debt|expens|deductible|reimburse|rate\b|rates\b|budget|cut|loss|clos', re.I)

STATES = {
 'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington State':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}
CA_STRONG = re.compile(r'\bCalifornia\b|\bCalifornians\b|\bCalif\.|\bMedi-?Cal\b|\bNewsom\b|\bCovered California\b|\bCalPERS\b|\bOHCA\b|\bCHCF\b')
CA_TITLE_ONLY = re.compile(r'Los Angeles|San Francisco|Sacramento|San Diego|\bSutter\b|\bCedars-Sinai\b|\bSharp HealthCare\b|\bUCLA\b|\bUCSF\b')


def log(*a):
    print(*a, file=sys.stderr)


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean(s, limit=None):
    if not s:
        return ''
    s = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s*(?:The post|Read more|Continue reading|\[…\]|\[\.\.\.\]).*$', '', s, flags=re.I).strip()
    if limit and len(s) > limit:
        cut = s[:limit].rsplit(' ', 1)[0].rstrip(' ,;:-')
        s = cut + '…'
    return s


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        pass
    for fmt in ('%b %d, %Y %I:%M%p', '%B %d, %Y %I:%M%p', '%b %d, %Y'):
        try:
            return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            pass
    try:
        d = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def local(tag):
    return tag.rsplit('}', 1)[-1]


def parse_feed(data):
    root = ET.fromstring(data)
    out = []
    for el in root.iter():
        t = local(el.tag)
        if t not in ('item', 'entry'):
            continue
        d = {}
        for ch in el:
            n = local(ch.tag)
            if n == 'link':
                href = ch.get('href')
                if href and ch.get('rel', 'alternate') == 'alternate':
                    d.setdefault('link', href)
                elif ch.text and ch.text.strip():
                    d.setdefault('link', ch.text.strip())
            elif n in ('title', 'description', 'summary', 'pubDate', 'published', 'updated', 'date', 'encoded'):
                d.setdefault(n, ''.join(ch.itertext()))
        link = d.get('link')
        title = clean(d.get('title'))
        if not link or not title:
            continue
        when = parse_date(d.get('pubDate') or d.get('published') or d.get('date') or d.get('updated'))
        summ = d.get('description') or d.get('summary') or ''
        out.append({'title': title, 'url': link.strip(), 'date': when, 'summary': clean(summ, 300)})
    return out


def score_and_label(it, feed_place, strict):
    text = it['title'] + ' ' + it['summary']
    topics = [k for k, rx in TOPIC_WORDS.items() if re.search(rx, text, re.I)]
    core = bool(CORE.search(text)); cost = bool(COST.search(text))
    # every feed needs a health term, a cost term and at least one topic hit; strict (general-news) feeds also need the health term in the TITLE
    relevant = core and cost and len(topics) >= 1 and not NEG.search(it['title'])
    if strict:
        relevant = relevant and bool(CORE.search(it['title']))
    # place
    place, state = 'national', None
    named = sorted({s for s in STATES if s != 'California' and re.search(r'\b' + re.escape(s) + r'\b', text)})
    if feed_place == 'california' or CA_STRONG.search(text) or CA_TITLE_ONLY.search(it['title']):
        place = 'california'
    elif len(named) == 1:
        place, state = 'state', named[0]
    return relevant, place, state, topics[:4]


def load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def link_check(url):
    """Return True/False/None (None = could not tell, e.g. paywall/bot block)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status < 400
    except urllib.error.HTTPError as e:
        return None if e.code in (401, 403, 405, 406, 429, 999) else False
    except Exception:
        return None


LLM_SYSTEM = (
    'You label news items for a site about hospital prices, hospital finances and health care affordability in California and the U.S. '
    'You never write or rewrite text for the site. Reply with JSON only: an array with one object per input item, in order, each with keys '
    '"i" (the input index), "relevant" (true if the item is substantially about health care costs, prices, hospital finances, insurance affordability, '
    'consolidation, coverage affordability or related policy; false for clinical news, product launches, personnel items, or tangential mentions), '
    '"place" ("national", "california" or "state"), "state" (full state name when place is "state", else null), '
    '"topics" (subset of ' + json.dumps(TOPICS) + '), "reliable" (false only if the item looks like a press release dressed as news, sponsored content, or the snippet is clearly misleading), '
    'and "reason" (under 15 words).')


def llm_label(batch, key):
    payload = [{'i': n, 'source': it['source'], 'title': it['title'], 'snippet': it['summary'][:300]} for n, it in enumerate(batch)]
    body = json.dumps({'model': MODEL, 'max_tokens': 1500, 'system': LLM_SYSTEM,
                       'messages': [{'role': 'user', 'content': json.dumps(payload)}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, method='POST',
                                 headers={'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01'})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    text = ''.join(b.get('text', '') for b in resp.get('content', []) if b.get('type') == 'text')
    m = re.search(r'\[[\s\S]*\]', text)
    arr = json.loads(m.group(0))
    out = {}
    for o in arr:
        i = o.get('i')
        if not isinstance(i, int) or not 0 <= i < len(batch):
            continue
        place = o.get('place') if o.get('place') in ('national', 'california', 'state') else None
        state = o.get('state') if o.get('state') in STATES else None
        if place == 'state' and not state:
            place = None
        out[i] = {'relevant': bool(o.get('relevant')), 'place': place, 'state': state if place == 'state' else None,
                  'topics': [t for t in (o.get('topics') or []) if t in TOPICS][:4], 'reliable': o.get('reliable') is not False,
                  'reason': str(o.get('reason') or '')[:120]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-llm', action='store_true')
    ap.add_argument('--no-linkcheck', action='store_true')
    args = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=KEEP_DAYS)
    key = None if args.no_llm else os.environ.get('ANTHROPIC_API_KEY')
    prev = load_json(OUT, {'items': []})
    cache = load_json(CACHE, {})
    existing = {it['url']: it for it in prev.get('items', []) if not it.get('curated')}

    health, fresh = [], []
    for fid, name, url, hint, strict in FEEDS:
        try:
            items = parse_feed(fetch(url))
            health.append({'id': fid, 'name': name, 'url': url, 'ok': True, 'items': len(items), 'error': None})
        except Exception as e:
            health.append({'id': fid, 'name': name, 'url': url, 'ok': False, 'items': 0, 'error': str(e)[:120]})
            log('feed failed', fid, e)
            continue
        kept = 0
        for it in items:
            if not it['date'] or it['date'] < cutoff or it['date'] > now + dt.timedelta(days=2):
                continue
            if it['url'] in existing:
                continue
            relevant, place, state, topics = score_and_label(it, hint, strict)
            if not relevant:
                continue
            it.update(source=name, feed=fid, place=place, state=state, topics=topics)
            fresh.append(it)
            kept += 1
            if kept >= PER_FEED_CAP:
                break
        log(f'{fid}: {len(items)} in feed, {kept} new relevant')

    # Step 2: optional model labels (new items only, cached by URL)
    need = [it for it in fresh if it['url'] not in cache]
    llm_ok = False
    if key and need:
        for n in range(0, len(need), 12):
            batch = need[n:n + 12]
            try:
                res = llm_label(batch, key)
                llm_ok = True
                for i, it in enumerate(batch):
                    if i in res:
                        cache[it['url']] = dict(res[i], when=now.isoformat(timespec='seconds'))
            except Exception as e:
                log('LLM batch failed, those items stay rules-only:', str(e)[:120])
    final = []
    for it in fresh:
        c = cache.get(it['url'])
        verified = 'rules-only'
        if c:
            verified = 'llm-verified'
            if not c['relevant'] or not c['reliable']:
                log('dropped by model:', it['title'][:70], '|', c['reason'])
                continue
            if c['place']:
                it['place'], it['state'] = c['place'], c['state']
            if c['topics']:
                it['topics'] = c['topics']
        final.append((it, verified))

    # Step 3: mechanical link check on new items
    out_items = list(existing.values())
    for it, verified in final:
        ok = None if args.no_linkcheck else link_check(it['url'])
        if ok is False:
            log('dead link dropped:', it['url'])
            continue
        out_items.append({
            'id': hashlib.sha1(it['url'].encode()).hexdigest()[:12], 'title': it['title'], 'url': it['url'], 'source': it['source'],
            'date': it['date'].date().isoformat(), 'summary': it['summary'], 'place': it['place'], 'state': it['state'],
            'topics': it['topics'], 'verified_by': verified, 'link_ok': ok, 'fetched_at': now.isoformat(timespec='seconds')})

    # curated items (hand-maintained) always carried over
    for c in load_json(CURATED, []):
        out_items.append(dict({'summary': '', 'state': None, 'verified_by': 'hand-checked', 'link_ok': True, 'fetched_at': c.get('checked', ''), 'curated': True,
                               'id': hashlib.sha1(c['url'].encode()).hexdigest()[:12]}, **{k: v for k, v in c.items() if k != 'checked'}))
    seen, uniq = set(), []
    for it in sorted(out_items, key=lambda x: x['date'], reverse=True):
        if it['url'] in seen or it['date'] < cutoff.date().isoformat() and not it.get('curated'):
            continue
        seen.add(it['url']); uniq.append(it)
    uniq = uniq[:MAX_TOTAL]
    mode = 'llm-verified' if llm_ok else ('rules-only (no ANTHROPIC_API_KEY)' if not key else 'rules-only (LLM call failed)')
    result = {'generated': now.isoformat(timespec='seconds'), 'mode': mode, 'model': MODEL if llm_ok else None, 'feeds': health, 'count': len(uniq), 'items': uniq}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=1, ensure_ascii=False, allow_nan=False)
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)
    by = {}
    for it in uniq:
        k = it['place'] if it['place'] != 'state' else 'state'
        by[k] = by.get(k, 0) + 1
    log('mode:', mode, '| items:', len(uniq), '| by place:', by, '| feeds failed:', [h['id'] for h in health if not h['ok']])


if __name__ == '__main__':
    main()

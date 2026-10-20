"""Renders news.html (static, SEO-friendly) from data/news.json, data/external_briefs.json, data/events.json and the Center's briefs.
Called from tools/build.py. JS (news.js) only switches tabs and filters; with JS off every section is visible."""
import json, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import SUBGROUPS, TAX

def build(ROOT, H, head, header, tail, write, TOPICS, BRIEFS, BRIEFS_ALSO):
    def load(name, default):
        try:
            return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))
        except Exception:
            return default
    news = load('news.json', {'items': [], 'feeds': [], 'mode': 'unknown', 'generated': ''})
    ext = load('external_briefs.json', {'items': []})['items']
    events = load('events.json', {'items': []})['items']
    items = sorted(news['items'], key=lambda i: i['date'], reverse=True)

    def pretty(d):
        try:
            return dt.date.fromisoformat(d).strftime('%B %-d, %Y')
        except Exception:
            return d
    def place_label(i): return i['state'] if i['place'] == 'state' else ('California' if i['place'] == 'california' else 'National')
    def chips(i, topics=True):
        c = '<span class="chip accent">%s</span>' % H(place_label(i))
        if topics:
            subs = [SUBGROUPS[x] for x in i.get('subtopics', []) if x in SUBGROUPS][:2]
            c += ''.join('<span class="chip">%s</span>' % H(t) for t in (subs or [TOPICS[t] for t in i.get('topics', []) if t in TOPICS]))
        return '<div class="tags">%s</div>' % c
    def news_row(i):
        summ = '<p>%s</p>' % H(i['summary']) if i.get('summary') else ''
        ver = {'llm-verified': 'Labels checked by a model', 'rules-only': 'Labels set by keyword rules', 'hand-checked': 'Picked and checked by hand'}.get(i.get('verified_by'), '')
        return ('<li class="row" data-scope="%s" data-state="%s" data-topics="%s" data-subs="%s"><div><div class="meta" style="font-weight:600;color:var(--accent-ink);margin-bottom:4px">%s</div>'
                '<h3><a href="%s" target="_blank" rel="noopener">%s</a></h3>%s%s</div><div class="side">%s<br><span title="%s">%s</span></div></li>') % (
            'california' if i['place'] == 'california' else ('state' if i['place'] == 'state' else 'national'), H(i.get('state') or ''), H(' '.join(i.get('topics', []))), H(' '.join(i.get('subtopics', []))), H(i['source']),
            H(i['url']), H(i['title']), summ, chips(i), H(pretty(i['date'])), H(ver), H({'llm-verified': 'model-checked', 'rules-only': 'rules-checked', 'hand-checked': 'hand-checked'}.get(i.get('verified_by'), '')))
    n_nat = sum(1 for i in items if i['place'] == 'national'); n_ca = sum(1 for i in items if i['place'] == 'california'); n_st = sum(1 for i in items if i['place'] == 'state')
    states = sorted({i['state'] for i in items if i['place'] == 'state' and i.get('state')})
    state_opts = '<option value="">All states</option>' + ''.join('<option>%s</option>' % H(s) for s in states)
    cnt_t, cnt_s = {}, {}
    for i in items:
        for t in i.get('topics', []): cnt_t[t] = cnt_t.get(t, 0) + 1
        for x in i.get('subtopics', []): cnt_s[x] = cnt_s.get(x, 0) + 1
    topic_opts = '<option value="">All topics</option>' + ''.join(
        '<optgroup label="%s"><option value="%s">All %s (%d)</option>%s</optgroup>' % (H(c['label']), cat, H(c['label'].lower()), cnt_t.get(cat, 0),
            ''.join('<option value="%s/%s">%s (%d)</option>' % (cat, k, H(v['label']), cnt_s.get(cat + '/' + k, 0)) for k, v in c['subgroups'].items() if cnt_s.get(cat + '/' + k, 0)))
        for cat, c in TAX['categories'].items() if cnt_t.get(cat, 0))
    gen = pretty(news.get('generated', '')[:10]) if news.get('generated') else 'not yet'
    mode = news.get('mode', '')
    mode_txt = 'A model double-checked each item\'s relevance and labels.' if mode.startswith('llm') else 'Items were labeled by keyword rules. A model check switches on when an API key is added to the pipeline.'
    bad = [f['name'] for f in news.get('feeds', []) if not f.get('ok')]
    feeds_txt = ', '.join(sorted({f['name'] for f in news.get('feeds', []) if f.get('ok')}))

    current = ('<section class="panel" id="news" data-panel="news"><h2 class="ph">Current news</h2>'
      '<div class="seg" role="group" aria-label="Scope"><button type="button" class="opt" data-scope="national" aria-pressed="true">National <span class="count">%d</span></button>'
      '<button type="button" class="opt" data-scope="california" aria-pressed="false">California <span class="count">%d</span></button>'
      '<button type="button" class="opt" data-scope="state" aria-pressed="false">By state <span class="count">%d</span></button>'
      '<label class="state-pick" hidden><span class="sr">Choose a state</span><select id="state-select">%s</select></label>'
      '<label class="topic-pick"><span class="sr">Filter by topic</span><select id="topic-select">%s</select></label></div>'
      '<ul class="rows" id="news-list">%s</ul><p class="empty" id="news-empty" hidden>Nothing here yet. The feeds are checked daily.</p>'
      '<p class="src" style="margin-top:20px;max-width:75ch">Updated %s from public RSS feeds (%s). Titles, snippets and dates are copied from each publisher\'s feed, not written by us. Only items about hospital prices and finances, insurance costs and affordability are kept. %s%s</p></section>') % (
        n_nat, n_ca, n_st, state_opts, topic_opts, ''.join(news_row(i) for i in items), H(gen), H(feeds_txt), H(mode_txt),
        (' Feeds that failed on the last run: %s.' % H(', '.join(bad))) if bad else '')

    ext_rows = ''.join('<li class="row"><div><div class="meta" style="font-weight:600;color:var(--accent-ink);margin-bottom:4px">%s</div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3><p>%s</p><div class="by">%s</div><div class="tags"><span class="chip accent">California</span>%s</div></div><div class="side">%s</div></li>' % (
        H(e['org']), H(e['url']), H(e['title']), H(e['summary']), H(e['authors']), ''.join('<span class="chip">%s</span>' % H(TOPICS[t]) for t in e.get('topics', []) if t in TOPICS), H(e['datelabel'])) for e in sorted(ext, key=lambda x: x['date'], reverse=True))
    external = ('<section class="panel" id="external" data-panel="external"><h2 class="ph">External briefs <span class="chip accent" style="vertical-align:middle">California only</span></h2>'
      '<p class="lede2">Briefs and reports on California hospital prices and affordability from state agencies and foundations. Picked by hand and read before listing.</p><ul class="rows">%s</ul></section>') % ext_rows

    own = [b for b in sorted(BRIEFS, key=lambda x: x['date'], reverse=True) if b['place'] == 'ca']
    own_rows = ''.join('<li class="row"><div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3><p>%s</p><div class="by">%s</div></div><div class="side">%s</div></li>' % (H(b['url']), H(b['title']), H(b['summary']), H(b['by']), H(b['datelabel'])) for b in own)
    internal = ('<section class="panel" id="issue-briefs" data-panel="issue-briefs"><h2 class="ph">Issue briefs from the Center</h2>'
      '<p class="lede2">Short data briefs from the USC Center for Health Financing, Policy, and Management, built on California hospital disclosure data.</p><ul class="rows">%s</ul>'
      '<div class="also"><h3>More questions the series takes up</h3><ul>%s</ul><p class="src" style="margin:10px 0 0">See the Center\'s <a href="https://sites.usc.edu/improvinghealth/issue-briefs/" target="_blank" rel="noopener">issue briefs page</a> for what is published so far. All briefs, Center and national, are also on the <a href="briefs.html">issue briefs page</a>.</p></div></section>') % (own_rows, ''.join('<li>%s</li>' % H(q) for q in BRIEFS_ALSO))

    def ev_row(e):
        links = ''.join(' <a href="%s" target="_blank" rel="noopener">%s</a>' % (H(l['url']), H(l['label'])) for l in e.get('links', []))
        note = '<div class="by">%s</div>' % H(e['check_note']) if e.get('check_note') else ''
        return ('<li class="row"><div><div class="meta" style="font-weight:600;color:var(--accent-ink);margin-bottom:4px">%s</div><h3><a href="%s" target="_blank" rel="noopener">%s</a></h3>'
                '<div class="by">%s</div><p>%s%s</p>%s</div><div class="side">%s</div></li>') % (H(e['format']), H(e['url']), H(e['title']), H(e['host']), H(e['about']), (' Slides:' + links) if links else '', note, H(e['datelabel']))
    evs = sorted(events, key=lambda x: x.get('date') or '0000', reverse=True)
    eventsec = ('<section class="panel" id="events" data-panel="events"><h2 class="ph">Interviews, talks and events</h2>'
      '<p class="lede2">Public appearances by Glenn Melnick and the Center: interviews, testimony, podcasts, workshops and seminars. Only material anyone can open is listed. Each entry was opened and read before it was added.</p>'
      '<ul class="rows">%s</ul><p class="src" style="margin-top:20px;max-width:75ch">This list is hand-curated. A daily scan of USC Schaeffer and USC Price feeds flags possible new appearances for review, and nothing is listed until someone confirms it.</p></section>') % ''.join(ev_row(e) for e in evs)

    tabs = [('news', 'Current news', len(items)), ('external', 'External briefs (CA)', len(ext)), ('issue-briefs', 'Issue briefs', len(own)), ('events', 'Interviews and events', len(evs))]
    tabbar = '<div class="tabbar" role="tablist" aria-label="News sections">%s</div>' % ''.join(
        '<a role="tab" class="tab" href="#%s" data-tab="%s" aria-selected="false">%s <span class="count">%d</span></a>' % (i, i, H(t), n) for i, t, n in tabs)

    page = head('News, briefs and events on hospital costs | Hospital Price Watch', 'Current news on hospital prices and health care affordability (national, California, by state), California briefs, the Center\'s issue briefs, and public interviews and events.', 'news.html',
                '<link rel="stylesheet" href="news.css">\n')
    page += header('news.html')
    page += ('<main id="main"><div class="page-head"><div class="wrap"><h1>News and events</h1><p class="lede">Current coverage, California briefs, the Center\'s own issue briefs, and public interviews and talks.</p></div></div>'
             '<div class="wrap news-wrap">%s%s%s%s%s</div></main>') % (tabbar, current, external, internal, eventsec)
    page += tail('<script src="news.js"></script>\n')
    write('news.html', page)
    return {'items': len(items), 'national': n_nat, 'california': n_ca, 'state': n_st, 'external': len(ext), 'own': len(own), 'events': len(evs)}

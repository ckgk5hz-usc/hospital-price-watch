"""Simple reports: report-<theme>.html, one plain brief per theme. No charts and no motion: a title, key findings,
findings by sub-topic as bullets with the numbers in bold, and numbered source notes. Every bullet is an exhibit's
one-line claim and every note is that exhibit's own source line, so the brief says nothing the charts do not."""
import re
import themes_page


def build(H, head, header, tail, write, EXN, bold):
    made = []
    for th in themes_page.THEMES:
        notes, order = [], {}

        def cite(eid):
            if eid not in order:
                e = EXN[eid]; t, u = e['link']
                notes.append('<li id="n-%s">%s <a href="exhibits.html#%s">See the chart</a>%s</li>' % (
                    eid, bold(e['source']), eid, '' if u.startswith('exhibits') else ' <a href="%s"%s>%s</a>' % (H(u), ' target="_blank" rel="noopener"' if u.startswith('http') else '', H(t))))
                order[eid] = len(notes)
            n = order[eid]
            return '<sup><a href="#n-%s" aria-label="Source %d">%d</a></sup>' % (eid, n, n)

        def bullet(eid):
            e = EXN[eid]
            return '<li>%s%s</li>' % (bold(e['claim']), cite(eid))

        key = ''.join(bullet(x) for x in th['lead'] if x in EXN)
        secs = ''
        for sl, nm, intro, ids in themes_page.SUBS[th['slug']]:
            rest = [x for x in ids if x in EXN]
            if rest:
                secs += '<section><h2>%s</h2><p class="rp-intro">%s</p><ul>%s</ul></section>' % (H(nm), H(intro), ''.join(bullet(x) for x in rest))
        story = themes_page.STORIES.get(th['slug'])
        generated = max(EXN[x]['date'] for x in th['exhibits'] if x in EXN)
        f = 'report-%s.html' % th['slug']
        page = head('%s: simple report | Hospital Price Watch' % th['name'], 'A plain brief on %s: key findings with numbers and sources, no charts.' % th['name'].lower(), f,
                    '<link rel="stylesheet" href="report.css">\n') + header(f)
        page += '''<main id="main" class="rp" style="--tc:%s"><div class="wrap rp-wrap">
<p class="rp-tools"><a href="theme-%s.html">Back to the interactive page</a>%s<button type="button" class="btn ghost sm" onclick="window.print()">Print or save as PDF</button></p>
<article class="rp-doc">
<header><p class="rp-kind">Hospital Price Watch brief</p><h1>%s</h1><p class="rp-q">%s</p>
<p class="rp-meta">Data as of %s. Companion to the USC Center for Health Financing, Policy, and Management. Every finding links to its chart and source.</p></header>
<section class="rp-key"><h2>Key findings</h2><ul>%s</ul></section>
%s
<section class="rp-notes"><h2>Sources</h2><ol>%s</ol></section>
</article></div></main>
''' % (th['color'], th['slug'], '<a href="%s">Read the visual story</a>' % story[0] if story else '', H(th['name']), H(th['q']), H(generated), key, secs, ''.join(notes))
        write(f, page + tail())
        made.append(f)
    return made

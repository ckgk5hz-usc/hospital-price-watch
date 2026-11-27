"""The global bar: five sections and search.
Desktop: each section with pages opens one full-width panel under the bar (Topics as five theme cards, the rest as icon rows).
Phone: one menu button opens a sheet with a collapsible group per section. site.js drives both; site.css styles them."""
import re
import themes_page

ICONS = {'hospital.html': '<path d="M5 20V6l7-3 7 3v14M9 20v-5h6v5M12 8v4M10 10h4"/>',
         'hospital-prices.html': '<path d="M4 20V10M10 20V4M16 20v-7M2 20h20"/>',
         'county.html': '<path d="M4 6l5-2 6 2 5-2v14l-5 2-6-2-5 2zM9 4v14M15 6v14"/>',
         'districts.html': '<path d="M3 5h8v6H3zM13 5h8v14h-8zM3 13h8v6H3z"/>',
         'explorer.html': '<path d="M4 19l5-6 4 3 7-9"/><circle cx="20" cy="7" r="1.5"/>',
         'briefs.html': '<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 13h7M9 17h7"/>',
         'research.html': '<path d="M4 5h7v15H4zM13 5h7v15h-7z"/>',
         'about.html': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
         'sources.html': '<path d="M4 6c0-2 16-2 16 0v12c0 2-16 2-16 0zM4 6c0 2 16 2 16 0M4 12c0 2 16 2 16 0"/>',
         'glossary.html': '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11"/>'}

SEARCH = ('<button type="button" class="search-btn" aria-label="Search the site (press /)" aria-haspopup="dialog">'
          '<svg width="17" height="17" viewBox="0 0 17 17" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
          '<path d="M11.2 11.2 L15.5 15.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><span>Search</span><kbd>/</kbd></button>')

UTIL = ('<div class="util"><div class="wrap"><span>An independent research companion to the USC Center for Health Financing, Policy, and Management</span>'
        '<a href="https://sites.usc.edu/improvinghealth/" target="_blank" rel="noopener">Visit the Center</a></div></div>\n')

BRAND = ('<a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 16 16">'
         '<path d="M2 12 L6 7 L9 9.5 L14 3.5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>Hospital Price Watch</a>')


def section_of(SITE, cur):
    for label, x in SITE:
        if (x == cur) if isinstance(x, str) else any(f == cur for f, _, _ in x):
            return label
    if cur.startswith(('story-', 'theme-', 'affordability')):
        return 'Topics'
    return ''


def icon(f):
    return ('<span class="gi" aria-hidden="true"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg></span>' % ICONS.get(f, ''))


def header(SITE, cur):
    here = section_of(SITE, 'county.html' if cur == 'districts.html' else cur)
    cc = lambda f: ' aria-current="page"' if f == cur else ''
    bar, panels, sheet = [], [], []
    for label, x in SITE:
        on = ' on' if label == here else ''
        if isinstance(x, str):
            bar.append('<li><a class="gb%s" href="%s"%s>%s</a></li>' % (on, x, cc(x), label))
            sheet.append('<a class="gs-top" href="%s"%s>%s</a>' % (x, cc(x), label))
            continue
        pid = 'gp-' + re.sub(r'\W+', '', label.lower())
        bar.append('<li><button type="button" class="gb%s" aria-expanded="false" aria-controls="%s">%s</button></li>' % (on, pid, label))
        if label == 'Topics':
            cards = ''.join(
                '<div class="gt" style="--tc:%s"><a class="gt-main" href="theme-%s.html"%s><b>%s</b><span>%s</span></a><div class="gt-subs">%s</div>%s</div>' % (
                    th['color'], th['slug'], cc('theme-%s.html' % th['slug']), th['name'], th['q'],
                    ''.join('<a href="theme-%s.html#s-%s">%s</a>' % (th['slug'], sl, nm) for sl, nm, _, _ in themes_page.SUBS[th['slug']]),
                    '<a class="gt-story" href="%s"%s>Story: %s</a>' % (themes_page.STORIES[th['slug']][0], cc(themes_page.STORIES[th['slug']][0]), themes_page.STORIES[th['slug']][1])
                    if th['slug'] in themes_page.STORIES else '')
                for th in themes_page.THEMES)
            extra = [(f, t, d) for f, t, d in x if not f.startswith('theme-')]
            body = '<div class="gt-grid">%s</div>%s' % (cards, ''.join('<p class="gp-foot"><a href="%s"%s>%s</a><span>%s</span></p>' % (f, cc(f), t, d) for f, t, d in extra))
        else:
            body = '<div class="gl-grid">%s</div>' % ''.join('<a class="gl" href="%s"%s>%s<b>%s</b><span>%s</span></a>' % (f, cc(f), icon(f), t, d) for f, t, d in x)
        panels.append('<div class="gp" id="%s" role="region" aria-label="%s" hidden><div class="wrap">%s</div></div>' % (pid, label, body))
        stories = ''.join('<a class="gs-story" href="%s"%s>Story: %s</a>' % (u, cc(u), t) for u, t in themes_page.STORIES.values()) if label == 'Topics' else ''
        sheet.append('<details class="gs"%s><summary>%s</summary><div>%s%s</div></details>' % (
            ' open' if on else '', label, ''.join('<a href="%s"%s>%s</a>' % (f, cc(f), t) for f, t, _ in x), stories))
    return (UTIL + '<header class="site-header gnav"><div class="wrap gbar">\n  ' + BRAND +
            '\n  <nav class="gnav-nav" aria-label="Primary"><ul class="glist">' + ''.join(bar) + '</ul></nav>\n'
            '  <div class="gend">' + SEARCH + '<button type="button" class="gmenu" aria-expanded="false" aria-controls="gsheet" aria-label="Menu"><span></span><span></span></button></div>\n'
            '</div>\n<div class="gpanels">' + ''.join(panels) + '</div>\n'
            '<div class="gsheet" id="gsheet" hidden><nav aria-label="Site">' + ''.join(sheet) + '</nav></div>\n'
            '</header><div class="gscrim" hidden></div>\n')

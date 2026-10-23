"""Renders the scrolling story page affordability.html and its compact data file data/story.json
from data/affordability.json. All numbers shown on the page are read from story.json by afford.js."""
import json

Y0, Y1 = 2016, 2025
MS = ['single_premium', 'single_contribution', 'single_deductible', 'family_premium', 'family_contribution', 'family_deductible', 'hdhp_share']


def build(root, H, head, header, tail, write):
    d = json.load(open(root + '/data/affordability.json'))
    ys = [str(y) for y in range(Y0, Y1 + 1)]
    arr = lambda m: [None if m.get(y) is None else m[y] for y in ys]
    geos = {}
    for st, _ in d['meps_states']['single_premium']['est'].items():
        g = {'meps': {}, 'income': arr(d['income']['states'][st])}
        for m in MS:
            g['meps'][m] = {'v': arr(d['meps_states'][m]['est'][st]), 'se': arr(d['meps_states'][m]['se'][st])}
        geos[st] = g
    us = {'meps': {m: {'v': arr(d['meps'][m]['us']), 'se': arr(d['meps'][m]['us_se'])} for m in MS}, 'income': arr(d['income']['us'])}
    geos['United States'] = us
    story = {'asof': d['generated'], 'years': [int(y) for y in ys], 'cpi': arr(d['cpi']['us_all']), 'cpi_note': d.get('cpi_notes', []),
             'nhe': d['nhe'], 'tables': {m: d['measures'][m]['table_ca'].replace('II.', '') for m in MS}, 'geos': geos}
    oc = json.load(open(root + '/data/outcomes.json'))
    story['out'] = {'asof': oc['generated'], 'meta': oc['shadac_meta'], 'shadac': {k: v for k, v in oc['shadac'].items() if k in geos},
                    'urban': oc['urban'], 'unreported': oc['urban_unreported'], 'urban_note': oc['urban_note']}
    open(root + '/data/story.json', 'w').write(json.dumps(story, separators=(',', ':'), allow_nan=False))

    out = head('Where your health-care money goes: employer coverage costs, year by year | Hospital Price Watch',
               'A scrolling story of what employer health coverage costs in California, the U.S. and each state, who pays it, where it goes, and how it has climbed since 2016.',
               'affordability.html', '<link rel="stylesheet" href="story.css">\n') + header('affordability.html')
    out += '''<main id="main" class="story-page">
<div class="geo-bar"><div class="wrap geo-inner">
  <div class="geo-tabs" role="tablist" aria-label="Choose a place">
    <button type="button" role="tab" data-geo="California" aria-selected="true">California</button>
    <button type="button" role="tab" data-geo="United States" aria-selected="false">United States</button>
    <button type="button" role="tab" data-geo="other" aria-selected="false">Other states</button>
  </div>
  <label class="state-pick" id="state-pick" hidden><span>State</span><select id="state-select" aria-label="Choose a state"></select></label>
</div></div>
<div class="wrap story-wrap" id="story-wrap">
  <svg class="flight" id="flight" aria-hidden="true" focusable="false"></svg>
  <div id="story"><p class="loading">Loading the story&hellip;</p></div>
  <noscript><p class="loading">This story needs JavaScript. The same numbers are in plain tables on <a href="affordability-data.html">the detailed page</a>.</p></noscript>
</div>
</main>
'''
    write('affordability.html', out + tail('<script src="afford.js"></script>\n'))
    return story

"""Renders sources.html from data/source_registry.json and data/source_policy.json."""
import json


def build(root, H, head, header, tail, write):
    reg = json.load(open(root + '/data/source_registry.json'))
    pol = json.load(open(root + '/data/source_policy.json'))
    n_pub = sum(len(v) for v in pol['tiers'].values())
    groups = ''.join('<section><h2>%s</h2><div class="tbl"><table class="src-t"><thead><tr><th scope="col">Source</th><th scope="col">Used for</th><th scope="col">What to keep in mind</th></tr></thead><tbody>%s</tbody></table></div></section>' % (
        H(g['group']), ''.join('<tr><th scope="row"><a href="%s" target="_blank" rel="noopener">%s</a></th><td>%s</td><td>%s</td></tr>' % (H(i['url']), H(i['name']), H(i['use']), H(i['limit'])) for i in g['items'])) for g in reg)
    tiers = ''.join('<li><b>%s</b> (%d): %s</li>' % (H(pol['labels'][k]), len(v), H(', '.join(v))) for k, v in pol['tiers'].items())
    def gen(f, key='generated'):
        try:
            v = json.load(open(root + '/data/' + f)).get(key) or ''
        except Exception:
            v = ''
        return str(v)[:10] or 'unknown'
    fresh = [('Premium watch headlines', gen('premiums.json'), 'Every day', 'Google News searches and publisher feeds'),
             ('Current news', gen('news.json'), 'Every day', 'Publisher feeds'),
             ('Covered California documents', gen('coveredca_data.json'), 'Every day', "Covered California's Data and Research page"),
             ('Employer premiums, income, prices, debt', gen('affordability.json'), 'Checked monthly, November to March', 'AHRQ MEPS-IC, Census, BLS, New York Fed, CMS'),
             ('Cost-barrier surveys and medical debt', gen('outcomes.json'), 'Checked monthly, November to March', 'SHADAC, Urban Institute'),
             ('Hospital prices', gen('hospital_prices.json', 'updated'), 'Checked monthly, November to March', 'HCAI Hospital Measurement dataset'),
             ('Hospital quality ratings', gen('hospital_prices.json', 'cms_date'), 'By hand (CMS blocks automated downloads)', 'CMS Care Compare'),
             ('Hospital finances (explorer, exhibits)', gen('hospitals.json'), 'By hand when HCAI posts a new year', 'HCAI annual financial disclosures')]
    fresh_html = '<section id="freshness"><h2>Data freshness</h2><p class="sub lead2">When each dataset on the site was last refreshed, and how it is updated. An automated refresh that fails opens an issue instead of publishing.</p><div class="tbl"><table class="src-t"><thead><tr><th scope="col">Data</th><th scope="col">Last refreshed</th><th scope="col">How it updates</th><th scope="col">From</th></tr></thead><tbody>%s</tbody></table></div></section>' % ''.join(
        '<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td></tr>' % (H(a), H(b), H(c), H(d)) for a, b, c, d in fresh)
    out = head('Sources and how we check them | Hospital Price Watch', 'Every data source on Hospital Price Watch, what it is used for, its limits, and the checks each number goes through.', 'sources.html', '<link rel="stylesheet" href="afford.css">\n<link rel="stylesheet" href="hospital-prices.css">\n') + header('sources.html')
    out += '''<main id="main"><div class="page-head"><div class="wrap"><h1>Sources and how we check them</h1><p class="lede">Where the numbers on this site come from, what each source is good for, and where it falls short.</p></div></div>
<div class="wrap hp">
<section><h2>Our rules</h2><ul class="gaps">
<li><b>Original source first.</b> Numbers come from the agency or research group that produced them, not from a story about them.</li>
<li><b>Nothing is filled in.</b> When a source does not publish a figure, the page says so. No gap is estimated.</li>
<li><b>How numbers are checked.</b> Federal employer premium figures and the latest Census income figures are re-read from a second official file. Hospital figures are recomputed from the state's own columns. Figures typed from reports are matched against the report's text, except two whose sites block scripted downloads, which were checked by hand on a recorded date. Other federal series, such as the price index, come straight from the agency's file without a second copy to compare.</li>
<li><b>Two sources where possible.</b> Where a second credible survey exists, both are shown, including where they disagree.</li>
<li><b>Limits stay beside the number.</b> Margins of error, odd values and missing states are shown on the page.</li>
<li><b>No software writes the numbers or the findings.</b> Scripts pull and check data on a schedule, and a failed check stops the update and opens an issue for a person.</li>
</ul></section>
%s
<section id="news"><h2>News and headline lists</h2><p class="sub lead2">Headlines link to the publisher. A headline appears only if its publisher is on the list below (%d publishers). Search results from anyone else are left out and logged for a person to review, so a real story can be missed, especially local coverage. Being listed does not mean a story is correct, and leaving a publisher out is not a finding about it.</p>
<p class="sub lead2">Generally left out: republishing sites, insurers and brokers, advocacy groups and elected officials on any side, partisan outlets, business-marketing sites, and sites with no clear editorial staff. Local TV and commercial radio are also left out for now because many stations run shared syndicated copy.</p>
<p class="sub lead2">When the same headline runs at several publishers, as wire stories do, it is listed once, preferring the agency or research group that published it. Opinion pieces are left out where the headline marks them as opinion, and a few others have been removed by hand, so some may still slip through. Stories from outlets that cover only California are counted as California unless the headline names another state. The California tab of Premium Watch also lists California stories on health costs, coverage and affordability, under a separate published rule; other tabs list premium increases only.</p>
<ul class="gaps tiers">%s</ul></section>
<section><h2>Spot a mistake?</h2><p class="sub lead2">Every source above is linked, and the code and data are <a href="https://github.com/ckgk5hz-usc/hospital-price-watch" target="_blank" rel="noopener">public on GitHub</a>. Open an issue there with the page and the number.</p></section>
</div></main>
''' % (groups + fresh_html, n_pub, tiers)
    write('sources.html', out + tail())

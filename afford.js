/* Affordability story. Reads data/story.json (built by tools/afford_story.py) and draws every chapter in the browser.
   Each figure on the page is a value from that file. Most come from the federal data pulls; the second-survey, state-agency
   and California survey figures come from data/benchmarks.json, typed in from named reports and checked by tools/data/verify_benchmarks.py. */
(function () {
  'use strict';
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var D, geo = 'California', cov = 'family', ctl = {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var money = function (n) { return '$' + Math.round(n).toLocaleString('en-US'); };
  var pct0 = function (n) { return Math.round(n) + '%'; };
  var sgn = function (n, dec) { return (n >= 0 ? '+' : '−') + Math.abs(n).toFixed(dec == null ? 0 : dec) + '%'; };
  var L, FIRST = 0;

  var URL = {
    meps: 'https://meps.ahrq.gov/mepsweb/data_stats/state_tables.jsp',
    state: function (y) { return 'https://meps.ahrq.gov/mepsweb/data_stats/summ_tables/insr/state/series_2/' + y + '/ic' + String(y).slice(2) + '_iia_f.pdf'; },
    nat: function (y) { return 'https://meps.ahrq.gov/mepsweb/data_stats/summ_tables/insr/national/series_1/' + y + '/ic' + String(y).slice(2) + '_ia_g.pdf'; },
    nhe: 'https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/historical',
    cps: 'https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html',
    bls: 'https://www.bls.gov/cpi/'
  };

  fetch('data/story.json').then(function (r) { return r.json(); }).then(function (d) { D = d; L = d.years.length - 1; init(); })
    .catch(function () { $('#story').innerHTML = '<p class="loading">The data file could not be loaded. The same numbers are in tables on <a href="affordability-data.html">the detailed page</a>.</p>'; });

  /* ---------- data helpers ---------- */
  function G(name) { return D.geos[name || geo]; }
  function V(m, i, g) { var a = (g || G()).meps[m].v[i == null ? L : i]; return a == null ? null : a; }
  function SE(m, i, g) { return (g || G()).meps[m].se[i == null ? L : i]; }
  function place(g) { g = g || geo; return g === 'United States' ? 'the U.S.' : g; }
  function Place(g) { g = g || geo; return g === 'United States' ? 'The U.S.' : g; }
  function ok() { for (var i = 0; i < arguments.length; i++) if (arguments[i] == null || isNaN(arguments[i])) return false; return true; }
  function src(text, url) { return '<p class="src">Source: <a href="' + url + '" target="_blank" rel="noopener">' + esc(text) + '</a></p>'; }
  function mepsSrc(m, g) {
    var t = D.tables[m], yr = D.years[L];
    if ((g || geo) === 'United States') return src('AHRQ MEPS-IC, Table I.' + t + ', ' + yr, URL.nat(yr));
    return src('AHRQ MEPS-IC, Table II.' + t + ', ' + yr, URL.state(yr));
  }
  function missing(what) { return '<div class="card soft"><p>The federal survey does not publish ' + esc(what) + ' for ' + esc(place()) + ' in these years, usually because too few employers were sampled.</p></div>'; }
  function count(to, fmt) { return '<span class="num" data-count="' + to + '" data-fmt="' + (fmt || '$') + '">' + (fmt === '%' ? Math.round(to) + '%' : money(to)) + '</span>'; }
  function bigCard(label, to, sub, source, extra) {
    return '<article class="card rv"><h3>' + label + '</h3><p class="big">' + count(to) + '</p><p class="sub">' + sub + '</p>' + (extra || '') + source + '</article>';
  }
  function chapter(id, inner, cls) { return '<section class="ch ' + (cls || '') + '" id="' + id + '" data-stop>' + inner + '</section>'; }

  /* ---------- chapters ---------- */
  function hero() {
    var a = V('family_premium', 0), b = V('family_premium');
    var h = '<h1>Where your health-care money goes</h1><p class="lede">Follow the average paycheck through employer health coverage in ' + esc(place()) + ': who pays, where it goes, and how the price has climbed since ' + D.years[0] + '.</p>';
    if (ok(a, b)) {
      h += '<div class="hero-pair rv"><div><span class="small">A family plan in ' + D.years[0] + '</span><p class="big">' + count(a) + '</p></div>' +
        '<div class="hero-up"><span class="chip up">' + sgn((b / a - 1) * 100) + '</span><span class="small">from ' + D.years[0] + ' to ' + D.years[L] + '</span></div>' +
        '<div><span class="small">A family plan in ' + D.years[L] + '</span><p class="big">' + count(b) + '</p></div></div>';
      h += '<p class="small rv">Total yearly price of a family plan through an employer, in the dollars of each year. What you pay and what your employer pays are added together.</p>';
    }
    h += '<p class="cue rv">Scroll to follow the money</p>';
    return chapter('c-hero', h, 'hero');
  }

  function price() {
    var s = V('single_premium'), f = V('family_premium');
    var h = '<h2>The price tag</h2><p class="lede">In ' + D.years[L] + ', the average employer health plan in ' + esc(place()) + ' cost this much for a full year.</p><div class="cards two">';
    h += ok(s) ? bigCard('One person', s, 'Total yearly price of single coverage', mepsSrc('single_premium')) : missing('single-coverage prices');
    h += ok(f) ? bigCard('A family', f, 'Total yearly price of family coverage', mepsSrc('family_premium')) : missing('family-coverage prices');
    return chapter('c-price', h + secondSurvey() + '</div>', '');
  }

  /* A second, independent employer survey for the same year (California and U.S. only). */
  function secondSurvey() {
    var b = geo === 'California' ? D.bench.chbs_ca : geo === 'United States' ? D.bench.ehbs_us : null, yi = b ? D.years.indexOf(b.year) : -1;
    if (!b || yi < 0) return '';
    var rows = [['single_premium', 'Price, one person'], ['family_premium', 'Price, a family'], ['single_contribution', 'Your share, one person'], ['family_contribution', 'Your share, a family'], ['single_deductible', 'Deductible, one person']];
    var who = geo === 'California' ? 'KFF and CHCF' : 'KFF';
    var h = '<article class="card wide rv"><h3>Checked against a second survey</h3><p class="sub lead">' + esc(b.org) + ' run a separate survey of employers. Same year, different employers asked in a different way, so the two never match exactly. Where they land close, the figure is solid; where they differ, read the truth as somewhere in between.</p>' +
      '<div class="tbl"><table class="two-src"><thead><tr><th scope="col">' + b.year + '</th><th scope="col">Federal (AHRQ)</th><th scope="col">' + who + '</th></tr></thead><tbody>';
    rows.forEach(function (r) { var a = V(r[0], yi), c = b.values[r[0]]; h += '<tr><th scope="row">' + r[1] + '</th><td>' + (ok(a) ? money(a) : 'not published') + '</td><td>' + money(c) + '</td></tr>'; });
    h += '</tbody></table></div><p class="sub">' + (geo === 'California'
      ? 'The federal survey covers private-sector employers of every size. The KFF and CHCF survey covers employers with 10 or more workers, including state and local governments, and interviewed 464 firms, so its margin of error is wider. Deductibles are averages among workers whose plan has one.'
      : 'The federal survey covers private-sector employers of every size. KFF covers employers with 10 or more workers, including state and local governments. Deductibles are averages among workers whose plan has one.') + '</p>';
    var nx = D.bench.ehbs_us_next;
    if (geo === 'United States' && nx && nx.year > D.years[L]) h += '<p class="sub">Newer: KFF\'s ' + nx.year + ' survey puts the family price at ' + money(nx.values.family_premium) + ' and one person at ' + money(nx.values.single_premium) + '. The federal survey for ' + nx.year + ' is not out yet.</p>' + src(nx.org + ', ' + nx.title, nx.page);
    return h + src(b.org + ', ' + b.title, b.page) + '</article>';
  }

  function who() {
    var pm = cov + '_premium', cm = cov + '_contribution', P = V(pm), C = V(cm);
    var h = '<h2>Who pays the bill</h2><p class="lede">The price is split between two pockets. One is taken out of your paycheck. The other is the employer\'s share, paid by the company that chose to offer the plan.</p>';
    h += '<div class="toggle" role="group" aria-label="Coverage type"><button type="button" data-cov="single" aria-pressed="' + (cov === 'single') + '">One person</button><button type="button" data-cov="family" aria-pressed="' + (cov === 'family') + '">A family</button></div>';
    if (!ok(P, C)) return chapter('c-who', h + missing('this split'), '');
    var E = P - C, share = C / P * 100;
    h += '<div class="card flow rv"><svg id="flow" viewBox="0 0 640 300" role="img" aria-label="Diagram: ' + money(C) + ' from your paycheck and ' + money(E) + ' from your employer flow into the health plan each year."></svg>' +
      '<div class="split" aria-hidden="true"><span class="you" style="width:' + share.toFixed(1) + '%"></span><span class="emp" style="width:' + (100 - share).toFixed(1) + '%"></span></div>' +
      '<p class="legend"><span class="dot you"></span>You: ' + money(C) + ' (' + pct0(share) + ')<span class="dot emp"></span>Your employer: ' + money(E) + ' (' + pct0(100 - share) + ')</p>' +
      '<p class="sub">Average per enrolled worker, per year, ' + D.years[L] + '. The employer share is the total price minus the worker\'s share. Where an employer pays claims itself instead of buying insurance, the survey counts an equivalent premium.</p>' + mepsSrc(pm) + '</div>';
    return chapter('c-who', h, '');
  }

  function destination() {
    var n = D.nhe; if (!n || !n.total) return '';
    var parts = [['hospital', 'Hospitals', n.hospital, 'h'], ['physician', 'Doctors and clinics', n.physician, 'd'], ['drugs', 'Prescription drugs', n.drugs, 'p'], ['other', 'Other care', n.other_care, 'o'], ['net', 'Plan overhead and profit', n.net_cost, 'n']];
    var raw = parts.map(function (p) { return p[2] / n.total * 100; }), fl = raw.map(Math.floor), left = 100 - fl.reduce(function (a, b) { return a + b; }, 0);
    raw.map(function (r, i) { return [r - fl[i], i]; }).sort(function (a, b) { return b[0] - a[0]; }).slice(0, left).forEach(function (x) { fl[x[1]]++; });
    var h = '<h2>Where the plan sends it</h2><p class="lede">Once the money reaches the health plan, it is paid out. Across all U.S. private health insurance in ' + n.year + ', each premium dollar was spent roughly like this.</p>';
    h += '<div class="card rv"><div class="dollar" role="img" aria-label="Premium dollar split">' + parts.map(function (p, i) { return '<span class="seg ' + p[3] + '" data-w="' + fl[i] + '" style="width:' + (RM ? fl[i] : 0) + '%"></span>'; }).join('') + '</div>';
    h += '<ul class="cents">' + parts.map(function (p, i) { return '<li><span class="dot ' + p[3] + '"></span><b>' + fl[i] + '¢</b> ' + p[1] + '</li>'; }).join('') + '</ul>';
    h += '<p class="sub">National figures for all private health insurance (employer, individual and marketplace plans), not for ' + esc(place()) + ' alone. "Other care" is dental, home health, equipment, other professionals and similar. "Plan overhead and profit" is what CMS calls the net cost of insurance: administration plus profit, reserves, taxes and similar items. This is calendar-year ' + n.year + ' data, the latest published, while the price tag above is from the ' + D.years[L] + ' survey. Shares are rounded to whole cents.</p>' +
      src('CMS National Health Expenditure Accounts, Table 4, ' + n.year, URL.nhe) + '</div>';
    return chapter('c-dest', h, '');
  }

  function rateBars(series, next) {
    var ys = Object.keys(series).sort(), n = ys.length + (next ? 1 : 0), W = 560, H = 200, l = 6, r = 6, t = 20, b = 24;
    var mx = Math.max.apply(null, ys.map(function (y) { return series[y]; }).concat(next ? [next.v] : [])) * 1.1, bw = (W - l - r) / n;
    var bar = function (i, y, v, cls) { var x = l + i * bw + bw * .18, w = bw * .64, hh = v / mx * (H - t - b); return '<rect class="' + cls + '" x="' + x.toFixed(1) + '" y="' + (H - b - hh).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + hh.toFixed(1) + '" rx="2"/><text x="' + (x + w / 2).toFixed(1) + '" y="' + (H - b - hh - 5).toFixed(1) + '" text-anchor="middle" font-size="10.5">' + v.toFixed(1) + '%</text><text x="' + (x + w / 2).toFixed(1) + '" y="' + (H - 7) + '" text-anchor="middle" font-size="10">' + (n > 8 ? "'" + String(y).slice(2) : y) + '</text>'; };
    var o = '<svg class="bars" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Yearly rate increases: ' + ys.map(function (y) { return y + ' ' + series[y] + '%'; }).join(', ') + (next ? '; ' + next.y + ' expected ' + next.v + '%' : '') + '">';
    ys.forEach(function (y, i) { o += bar(i, y, series[y], 'b'); });
    if (next) o += bar(ys.length, next.y, next.v, 'b nx');
    return o + '<line class="base" x1="' + l + '" x2="' + (W - r) + '" y1="' + (H - b) + '" y2="' + (H - b) + '"/></svg>';
  }
  function stateWatch() {
    var o = D.bench.ohca, m = D.bench.dmhc; if (geo !== 'California' || !o || !m) return '';
    var ov = o.values, tg = o.target.values, ty = Object.keys(tg).sort();
    var h = '<h2>California now checks this itself</h2><p class="lede">Two state agencies collect these numbers straight from health plans. HCAI\'s Office of Health Care Affordability adds up what plans spend per member, and has set a goal that this should grow no faster than family incomes. The Department of Managed Health Care collects the premium increases plans charge employers.</p><div class="cards two">';
    h += '<article class="card rv"><h3>Spending per member, private insurance</h3><p class="big">' + count(ov.commercial_pmpy_2024) + '</p><p class="sub lead">spent on medical care per member in 2024, up ' + ov.commercial_growth.toFixed(1) + '% from ' + money(ov.commercial_pmpy_2023) + ' in 2023.</p>' +
      '<div class="vsbar"><div><span>Growth, 2023 to 2024</span><i class="act" style="width:' + (ov.commercial_growth / 8 * 100).toFixed(1) + '%"></i><b>' + ov.commercial_growth.toFixed(1) + '%</b></div><div><span>State target from ' + ty[0] + '</span><i class="tgt" style="width:' + (tg[ty[0]] / 8 * 100).toFixed(1) + '%"></i><b>' + tg[ty[0]].toFixed(1) + '%</b></div></div>' +
      '<p class="sub">The target starts with ' + ty[0] + ' spending, so 2024 came before it. It steps down to ' + tg[ty[ty.length - 1]].toFixed(1) + '% by ' + ty[ty.length - 1] + '. Of the 2024 increase, hospital outpatient care made up ' + ov.share_hosp_outpatient + '%, retail prescriptions before drug-maker rebates ' + ov.share_pharmacy + '% and hospital stays ' + ov.share_hosp_inpatient.toFixed(1) + '%. Members\' own copays, coinsurance and deductibles averaged ' + money(ov.cost_sharing_2024) + ', up from ' + money(ov.cost_sharing_2023) + '.</p>' +
      '<p class="sub">Covers employer and individual plans together, medical spending only (no plan overhead or profit).</p>' + src('HCAI Office of Health Care Affordability, ' + o.title, o.doc) + src('HCAI, statewide health care spending target', o.target.page) + '</article>';
    var ys = Object.keys(m.large_group).sort(), c = m.components_2025;
    h += '<article class="card rv"><h3>Premium increases for large employers</h3><p class="sub lead">Average yearly increase in what plans charged employers with more than 100 workers, ' + ys[0] + ' to ' + ys[ys.length - 1] + ', and the increase plans expect for ' + m.expected_next.year + '.</p>' +
      rateBars(m.large_group, { y: m.expected_next.year, v: m.expected_next.large_group }) +
      '<p class="legend sm"><span class="dot rbx"></span>Charged<span class="dot rbn"></span>Expected, from rate filings</p>' +
      '<p class="sub">In ' + ys[ys.length - 1] + ', per member each month, medical costs in these premiums rose ' + c.medical + '%, prescription drugs ' + c.drugs + '% and plan profit ' + c.profit + '%. Profit was ' + c.profit_share + '% of the premium. Weighted by members; about 7.5 million members of DMHC-regulated large-group plans.</p>' +
      src('California Department of Managed Health Care, ' + m.title, m.doc) + '</article>';
    return chapter('c-state', h + '</div><p class="note rv">These figures come from health plans, not from an employer survey. They measure spending and rate changes, not the full yearly price of a plan, so they should not be compared dollar for dollar with the price tag above.</p>', '');
  }

  function yoyCard(i, pm, cm) {
    var P = V(pm, i), C = V(cm, i), pp = i > 0 ? V(pm, i - 1) : null, cp = D.cpi[i], cq = i > 0 ? D.cpi[i - 1] : null, y = D.years[i];
    if (!ok(P, C)) return '<li class="yr"><h3>' + y + '</h3><p class="sub">Not published</p></li>';
    var ch = ok(pp) ? (P / pp - 1) * 100 : null, inf = ok(cq, cp) ? (cp / cq - 1) * 100 : null, noisy = false;
    if (ch != null) { var s1 = SE(pm, i), s0 = SE(pm, i - 1); noisy = !ok(s1, s0) || Math.abs(P - pp) < 1.96 * Math.sqrt(s1 * s1 + s0 * s0); }
    return '<li class="yr" data-year="' + y + '"><h3>' + y + '</h3><p class="big">' + money(P) + '</p>' +
      '<div class="mini" aria-hidden="true"><span class="you" style="height:' + (C / P * 100).toFixed(1) + '%"></span><span class="emp" style="height:' + (100 - C / P * 100).toFixed(1) + '%"></span></div>' +
      '<p class="sub">You pay <b>' + money(C) + '</b></p>' +
      (ch == null ? '<p class="sub chg">First year shown</p>' : '<p class="chg"><span class="chip ' + (noisy ? 'flat' : (ch >= 0 ? 'up' : 'down')) + '">' + sgn(ch, 1) + '</span> plan price</p>' + (noisy ? '<p class="sub">Within sampling error: could be noise</p>' : '') + '<p class="sub">Prices overall: ' + (inf == null ? 'n/a' : sgn(inf, 1)) + '</p>') + '</li>';
  }

  function timeline() {
    var pm = cov + '_premium', cm = cov + '_contribution', a = V(pm, 0), b = V(pm);
    var h = '<div class="tl-pin"><div class="tl-head"><h2>The climb, year by year</h2><p class="lede">Keep scrolling and the years move across. Each card is one year\'s average yearly price, with the part you pay in red at the bottom.</p>' +
      '<div class="toggle" role="group" aria-label="Coverage type"><button type="button" data-cov="single" aria-pressed="' + (cov === 'single') + '">One person</button><button type="button" data-cov="family" aria-pressed="' + (cov === 'family') + '">A family</button></div></div>' +
      '<div class="tl-view"><ol class="tl-track">';
    for (var i = 0; i <= L; i++) h += yoyCard(i, pm, cm);
    if (ok(a, b)) h += '<li class="yr total"><h3>Since ' + D.years[0] + '</h3><p class="big">' + sgn((b / a - 1) * 100) + '</p><p class="sub">' + money(a) + ' to ' + money(b) + '</p><p class="sub">About ' + sgn((Math.pow(b / a, 1 / L) - 1) * 100, 1) + ' a year</p><p class="sub">Prices overall: ' + sgn((D.cpi[L] / D.cpi[0] - 1) * 100) + '</p></li>';
    h += '</ol></div><div class="tl-rail" aria-hidden="true"><span class="tl-bill">$</span></div>' +
      '</div><div class="tl-after"><p class="sub tl-note">Dollars of each year, not adjusted. A grey change is small enough to be survey noise. "Prices overall" is the U.S. consumer price index, annual average; the ' + D.years[L] + ' average leaves out October, when the federal government collected no data. These are survey averages: a single-year jump in one state can partly be sampling noise, so read the long climb more than any one year. The share you pay is especially noisy from year to year.</p>' +
      src('AHRQ MEPS-IC, Table ' + (geo === 'United States' ? 'I.' : 'II.') + D.tables[pm] + ' and ' + D.tables[cm] + ', ' + D.years[0] + ' to ' + D.years[L], URL.meps) +
      src('U.S. Bureau of Labor Statistics, CPI-U all items', URL.bls) + '</div>';
    return chapter('tl', h, 'tl');
  }

  function incomeNominal(g, i) { var r = g.income[i]; return r == null ? null : r * D.cpi[i] / D.cpi[L]; }
  function indexChart(lines) {
    var W = 560, H = 230, l = 14, r = 120, t = 14, b = 26, n = D.years.length, all = [];
    lines.forEach(function (x) { x.v.forEach(function (q) { if (q != null) all.push(q); }); });
    var lo = Math.floor(Math.min.apply(null, all) / 10) * 10 - 0, hi = Math.ceil(Math.max.apply(null, all) / 10) * 10 + 5;
    var X = function (i) { return l + i / (n - 1) * (W - l - r); }, Y = function (q) { return t + (hi - q) / (hi - lo) * (H - t - b); };
    var o = '<svg class="idx" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Index chart, ' + D.years[0] + ' equals 100: ' + lines.map(function (x) { return x.name + ' ends at ' + Math.round(x.v[n - 1]); }).join('; ') + '">';
    for (var k = lo; k <= hi; k += 10) o += '<line class="gl" x1="' + l + '" x2="' + (W - r) + '" y1="' + Y(k) + '" y2="' + Y(k) + '"/><text x="' + (l) + '" y="' + (Y(k) - 3) + '" font-size="10">' + k + '</text>';
    D.years.forEach(function (y, i) { if (i % 3 === L % 3) o += '<text x="' + X(i) + '" y="' + (H - 6) + '" font-size="10" text-anchor="middle">' + y + '</text>'; });
    var ends = [];
    lines.forEach(function (x) {
      var pts = x.v.map(function (q, i) { return q == null ? null : X(i).toFixed(1) + ',' + Y(q).toFixed(1); }).filter(Boolean);
      o += '<polyline class="ln ' + x.cls + '" points="' + pts.join(' ') + '" pathLength="1"/>';
      ends.push([Y(x.v[n - 1]), x]);
    });
    ends.sort(function (a, b2) { return a[0] - b2[0]; }); var last = -99;
    ends.forEach(function (e) { var y = Math.max(e[0], last + 14); last = y; o += '<circle class="ed ' + e[1].cls + '" cx="' + X(n - 1) + '" cy="' + e[0] + '" r="3.5"/><text class="el ' + e[1].cls + '" x="' + (X(n - 1) + 8) + '" y="' + (y + 3.5) + '" font-size="11.5">' + e[1].name + ' ' + Math.round(e[1].v[n - 1]) + '</text>'; });
    return o + '</svg>';
  }
  function compareTime() {
    var g = G(), pm = 'family_premium', cm = 'family_contribution', a = V(pm, 0), b = V(pm), ca = V(cm, 0), cb = V(cm), ia = incomeNominal(g, 0), ib = incomeNominal(g, L);
    var h = '<h2>Compared with paychecks and prices</h2>';
    if (!ok(a, b, ia, ib, ca, cb)) return chapter('c-time', h + missing('enough data for this comparison'), '');
    var cp = (D.cpi[L] / D.cpi[0] - 1) * 100, pr = (b / a - 1) * 100, inc = (ib / ia - 1) * 100, sh = (cb / ca - 1) * 100;
    var rel = pr > inc + 2 ? 'faster than' : (pr < inc - 2 ? 'a little slower than' : 'about as fast as');
    var vs = Math.min(pr, inc) > cp ? 'Both rose faster than prices overall.' : 'Prices overall rose ' + sgn(cp) + '.';
    h += '<p class="lede">From ' + D.years[0] + ' to ' + D.years[L] + ' in ' + esc(place()) + ', the average family plan price rose ' + rel + ' median household income. ' + vs + ' These are averages: the typical household in the income figure does not necessarily hold one of these plans.</p>';
    h += '<div class="cards four">' +
      '<article class="card rv"><h3>Family plan price</h3><p class="big">' + sgn(pr) + '</p><p class="sub">' + money(a) + ' to ' + money(b) + '</p></article>' +
      '<article class="card rv"><h3>The part you pay</h3><p class="big">' + sgn(sh) + '</p><p class="sub">' + money(ca) + ' to ' + money(cb) + '. Noisy from year to year.</p></article>' +
      '<article class="card rv"><h3>Median household income</h3><p class="big">' + sgn(inc) + '</p><p class="sub">All households, not just those with employer plans</p></article>' +
      '<article class="card rv"><h3>Prices overall</h3><p class="big">' + sgn(cp) + '</p><p class="sub">U.S. consumer price index</p></article></div>';
    var idx = function (arr) { return arr.map(function (q) { return q == null ? null : q / arr[0] * 100; }); };
    var prem = [], inco = [];
    for (var i = 0; i <= L; i++) { prem.push(V(pm, i)); inco.push(incomeNominal(g, i)); }
    h += '<div class="card rv"><h3 class="ct">Index, ' + D.years[0] + ' = 100</h3>' + indexChart([{ name: 'Family plan', cls: 'a', v: idx(prem) }, { name: 'Income', cls: 'b', v: idx(inco) }, { name: 'Prices', cls: 'c', v: idx(D.cpi) }]) +
      '<p class="sub">Income is the Census median for all households in ' + esc(place()) + ', a three-year average that lags by about a year. Census publishes it in ' + D.years[L] + ' dollars; this page turns it back into each year\'s dollars with the same consumer price index used for the prices line, so the three lines are comparable. Census uses a slightly different price index, so the income change here can differ a little from Census\'s own. The ' + D.years[L] + ' price index leaves out October.</p>' +
      src('AHRQ MEPS-IC, Table ' + (geo === 'United States' ? 'I.' : 'II.') + D.tables[pm], URL.meps) + src('U.S. Census Bureau, CPS ASEC Table H-8B', URL.cps) + src('U.S. Bureau of Labor Statistics, CPI-U', URL.bls) + '</div>';
    return chapter('c-time', h, '');
  }


  /* ---------- outcomes: what happens when costs outrun households ---------- */
  var FRAMEFMT = function (f) { return f.indexOf('-') > 0 ? "'" + f.slice(2, 4) + '–' + f.slice(7) : f; };
  function oser(m, g) { var o = D.out.shadac[g || geo]; return o && o[m]; }
  function olast(m, g) { var s = oser(m, g); if (!s) return null; for (var i = s.v.length - 1; i >= 0; i--) if (s.v[i] != null) return { v: s.v[i], moe: s.moe[i], frame: s.frames[i], i: i }; return null; }
  function miniLine(m) {
    var a = oser(m), b = oser(m, 'United States'); if (!a) return '';
    var n = a.frames.length, W = 300, H = 120, l = 30, r = 8, t = 10, bt = 22, all = [];
    a.v.concat(geo === 'United States' ? [] : b.v).forEach(function (q) { if (q != null) all.push(q); });
    var mx = Math.max.apply(null, all), step = [1, 2, 2.5, 5, 10].map(function (f) { return f * Math.pow(10, Math.floor(Math.log10(mx * 1.05 / 3))); }).filter(function (q) { return q * 3 >= mx * 1.02; })[0] || mx / 3, top = step * 3;
    var X = function (i) { return l + i / Math.max(1, n - 1) * (W - l - r); }, Y = function (q) { return t + (top - q) / top * (H - t - bt); };
    var money_ = m === 'oop', fmt = function (q) { return money_ ? money(q) : Math.round(q * 100) + '%'; };
    var o = '<svg class="mini-line" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(D.out.meta[m].label) + ', ' + esc(place()) + (geo === 'United States' ? '' : ' and U.S.') + ', ' + FRAMEFMT(a.frames[0]) + ' to ' + FRAMEFMT(a.frames[n - 1]) + '">';
    for (var k = 0; k <= 3; k++) o += '<line class="gl" x1="' + l + '" x2="' + (W - r) + '" y1="' + Y(step * k) + '" y2="' + Y(step * k) + '"/><text x="' + (l - 4) + '" y="' + (Y(step * k) + 3) + '" text-anchor="end" font-size="9">' + fmt(step * k) + '</text>';
    o += '<text x="' + X(0) + '" y="' + (H - 6) + '" font-size="9" text-anchor="middle">' + FRAMEFMT(a.frames[0]) + '</text><text x="' + X(n - 1) + '" y="' + (H - 6) + '" font-size="9" text-anchor="end">' + FRAMEFMT(a.frames[n - 1]) + '</text>';
    function line(s, cls) { var pts = s.v.map(function (q, i) { return q == null ? null : X(i).toFixed(1) + ',' + Y(q).toFixed(1); }).filter(Boolean); return pts.length ? '<polyline class="ml ' + cls + '" points="' + pts.join(' ') + '"/>' : ''; }
    if (geo !== 'United States' && b) o += line(b, 'us');
    o += line(a, 'geo');
    return o + '</svg><p class="legend sm">' + (geo === 'United States' ? '' : '<span class="dot geo"></span>' + esc(place()) + '<span class="dot usg"></span>U.S.') + '</p>';
  }
  function chipVs(m) {
    if (geo === 'United States') return '';
    var a = olast(m), b = olast(m, 'United States'); if (!a || !b || a.frame !== b.frame) return '<p class="vs">U.S. figure is for a different period.</p>';
    if (m === 'oop') return '<p class="vs">U.S.: ' + money(b.v) + '</p>';
    var real = ok(a.moe, b.moe) && Math.abs(a.v - b.v) > Math.sqrt(a.moe * a.moe + b.moe * b.moe), hi = a.v > b.v;
    var us = m === 'oop' ? money(b.v) : (b.v * 100).toFixed(1) + '%';
    return '<p class="vs"><span class="chip ' + (real ? (hi ? 'up' : 'down') : 'flat') + '">' + (real ? (hi ? 'Higher than U.S.' : 'Lower than U.S.') : 'About the same as U.S.') + '</span> U.S.: ' + us + '</p>';
  }
  function outCard(m, title, lead, bigFmt) {
    var a = olast(m), meta = D.out.meta[m], ser = oser(m);
    var srcl = src('SHADAC State Health Compare, from ' + meta.survey + ' (' + (a ? FRAMEFMT(a.frame) : '') + ')', meta.url);
    if (!a) return '<article class="card soft rv"><h3>' + title + '</h3><p class="sub">Not published for ' + esc(place()) + '. The survey sample was too small or the state did not collect enough data.</p>' + srcl + '</article>';
    if (a.i !== ser.v.length - 1) return '<article class="card soft rv"><h3>' + title + '</h3><p class="sub">The latest figure (' + FRAMEFMT(ser.frames[ser.frames.length - 1]) + ') is not published for ' + esc(place()) + '. The last published figure was ' + (bigFmt === '$' ? money(a.v) : (a.v * 100).toFixed(1) + '%') + ' in ' + FRAMEFMT(a.frame) + '.</p>' + srcl + '</article>';
    var big = bigFmt === '$' ? count(a.v, '$') : '<span class="num" data-count="' + (a.v * 100).toFixed(1) + '" data-fmt="%1">' + (a.v * 100).toFixed(1) + '%</span>';
    return '<article class="card rv"><h3>' + title + '</h3><p class="big">' + big + '</p><p class="sub lead">' + lead + '</p>' + chipVs(m) + miniLine(m) + srcl + '</article>';
  }
  function debtCard() {
    var u = D.out.urban[geo], nat = D.out.urban['United States'], n = D.out.asof;
    var s = src('Urban Institute, Debt in America 2025 (credit bureau data, August 2025)', 'https://datacatalog.urban.org/dataset/debt-america-2025');
    if (u && u.reported === false) {
      return '<article class="card soft wide rv"><h3>Medical debt in collections</h3><p class="lead">Not available for ' + esc(place()) + '.</p><p class="sub">The Urban Institute measures medical debt from credit-bureau records, and it leaves out the seven states whose laws restrict reporting medical debt on credit reports: ' + D.out.unreported.join(', ') + '. ' + (geo === 'California' ? 'California\'s law took effect January 1, 2025 (<a href="https://calmatters.org/health/2024/12/medical-debt-credit-report-new-laws-2025/" target="_blank" rel="noopener">CalMatters</a>). ' : '') + 'There is no comparable credit-record number for ' + esc(place()) + (geo === 'California' ? '. The California survey card above asks people directly instead, a broader measure that is not comparable with collections.' : ', so the survey cards above are the better guide.') + '</p><p class="sub">Other states: <a href="https://library.nclc.org/article/latest-keeping-medical-debt-out-credit-reports" target="_blank" rel="noopener">National Consumer Law Center tracker</a>.</p>' + s + '</article>';
    }
    var rows = Object.keys(D.out.urban).filter(function (k) { return k !== 'United States' && D.out.urban[k].reported; }).sort(function (a, b) { return D.out.urban[b].share - D.out.urban[a].share; });
    var rk = rows.indexOf(geo);
    var isUS = geo === 'United States';
    return '<article class="card wide rv"><h3>Medical debt in collections</h3><p class="big">' + (u.share * 100).toFixed(1) + '%</p>' +
      '<p class="sub lead">of people with a credit record in ' + esc(place()) + ' had unpaid medical bills in collections in August 2025. The typical amount was ' + (u.median ? money(u.median) : 'not reported') + '.</p>' +
      (isUS ? '<p class="sub">Urban does not say how this U.S. figure treats the seven states that do not report, so use it as context, not as a benchmark for any one state.</p>' :
        '<p class="sub">' + (rk >= 0 ? 'Ranks ' + (rk + 1) + ' of ' + rows.length + ' reporting states and D.C. (1 is highest). ' : '') + 'U.S.: ' + (nat.share * 100).toFixed(1) + '%. Urban does not say how its U.S. figure treats the seven states that do not report, so compare states with each other rather than with this line.</p>') +
      (isUS ? '' : '<div id="cty" class="cty"></div>') +
      '<p class="sub">Since 2022 the three big credit bureaus have removed many medical debts from credit files (Urban Institute), so this shows less than the full amount people owe.</p>' + s + '</article>';
  }
  function caSurvey() {
    var c = D.bench.chcf_survey; if (geo !== 'California' || !c) return '';
    var v = c.values, item = function (n, t, lo, hi) { return '<li><b>' + n + '%</b><span>' + t + '</span>' + (lo != null ? '<em>' + lo + '% with lower incomes, ' + hi + '% with higher incomes</em>' : '') + '</li>'; };
    return '<article class="card wide rv"><h3>What Californians say</h3><p class="sub lead">A statewide survey of ' + c.n.toLocaleString('en-US') + ' adults, ' + c.fielded + ', asked about the past year.</p><ul class="says">' +
      item(v.skipped, 'skipped or delayed care because of cost, themselves or a family member', v.skipped_low, v.skipped_high) +
      item(v.debt, 'have medical debt of any kind, including medical bills on a credit card', v.debt_low, v.debt_high) +
      item(v.bills, 'had problems paying medical bills, themselves or a family member') + '</ul>' +
      '<p class="sub">Of those who skipped or delayed care, ' + v.worse + '% said it made the condition worse. Margin of error &plusmn;' + c.moe.toFixed(1) + ' points overall, larger for income groups. These questions count family members and delays, so they run higher than the federal survey cards on this page; they are a different measure, not a different trend.</p>' +
      src(c.org + ', ' + c.title, c.page) + '</article>';
  }
  function trouble() {
    var h = '<h2>When the bill is too much</h2><p class="lede">Prices are one half. Surveys also ask what people do when costs get too high. Each card comes from a different survey with its own years, so read them one at a time.</p><div class="cards two">';
    h += outCard('care_cost', 'Skipped care because of cost', 'of adults said they needed medical care but could not get it because of cost, in the past year.');
    h += outCard('bills', 'Trouble paying medical bills', 'of people had trouble paying off medical bills in the past year. Two-year survey window.');
    h += outCard('drugs', 'Skipped or changed medicine', 'of people who were prescribed medicine delayed filling it, took less, or skipped doses to save money. Two-year survey window.');
    h += outCard('burden', 'Health costs above 10% of income', 'of people live in families where out-of-pocket health spending, premiums included, was more than a tenth of income.');
    h += outCard('oop', 'Typical family out-of-pocket spending', 'a year for the median family (health insurance unit), counting premiums and costs the plan did not cover.', '$');
    h += caSurvey() + debtCard() + '</div><p class="note rv">Survey figures have a margin of error, and a state\'s line moves around from year to year. Higher-or-lower labels use that margin but are not adjusted for the many comparisons across states and measures. The two medical-bill and medicine cards use overlapping two-year windows, so neighbouring points are not independent, and they start in 2019 because the survey was redesigned then. Skipped care starts in 2011 when the survey changed its method, and a few states are missing in some years. The 2019 and 2020 estimates for the income-based cards were affected by pandemic non-response. These describe what people report, not what caused it.</p>';
    return chapter('c-trouble', h, '');
  }
  function loadCounties() {
    var box = $('#cty'); if (!box) return;
    var want = geo;
    var go = function (C) {
      var list = (C[want] || []).slice().sort(function (a, b) { return b[1] - a[1]; });
      if (want !== geo || !$('#cty')) return;
      if (list.length < 3) { $('#cty').innerHTML = ''; return; }
      var top = list.slice(0, 8), mx = top[0][1];
      $('#cty').innerHTML = '<h4>' + (geo === 'Alaska' ? 'Boroughs and census areas' : geo === 'Louisiana' ? 'Parishes' : 'Counties') + ' with the highest share</h4><ol class="rank small">' + top.map(function (c, i) { return '<li><span class="rn">' + (i + 1) + '</span><span class="nm">' + esc(c[0]) + '</span><span class="rb"><i style="width:' + (c[1] / mx * 100).toFixed(1) + '%"></i></span><span class="rv2">' + (c[1] * 100).toFixed(1) + '%</span></li>'; }).join('') + '</ol><p class="sub">Only places with enough people in medical debt for Urban to report an amount are ranked (' + list.length + '). Small places swing more, so the top of this list is often rural.' + (geo === 'Connecticut' ? ' Connecticut uses its pre-2022 county boundaries in this file.' : '') + '</p>';
    };
    if (ctl.counties) go(ctl.counties); else fetch('data/story_counties.json').then(function (r) { return r.json(); }).then(function (C) { ctl.counties = C; go(C); }).catch(function () {});
  }

  function deductible() {
    var s = V('single_deductible'), f = V('family_deductible'), hd = V('hdhp_share');
    var h = '<h2>What you pay before the plan helps</h2><p class="lede">A deductible is the amount you pay yourself each year before the plan starts paying most claims. These are averages among workers whose plan has one.</p><div class="cards three">';
    h += ok(s) ? bigCard('One person', s, 'Average deductible', mepsSrc('single_deductible')) : missing('single deductibles');
    h += ok(f) ? bigCard('A family', f, 'Average deductible', mepsSrc('family_deductible')) : missing('family deductibles');
    h += ok(hd) ? '<article class="card rv"><h3>High-deductible plans</h3><p class="big">' + count(hd, '%') + '</p><p class="sub">of workers with single coverage are in one</p>' + mepsSrc('hdhp_share') + '</article>' : missing('high-deductible plan shares');
    return chapter('c-ded', h + '</div><p class="note rv">A deductible is not a bill. It is how much cost could fall on you before the plan pays most claims. Copayments and coinsurance can add more, and many people never reach their deductible. What people actually paid out of pocket is not in this survey.</p>', '');
  }

  var VERDICT_ROWS = [['single_premium', 'Price, one person', 'p'], ['family_premium', 'Price, a family', 'p'], ['single_contribution', 'Your share, one person', 'c'], ['family_contribution', 'Your share, a family', 'c'], ['single_deductible', 'Deductible, one person', 'd'], ['family_deductible', 'Deductible, a family', 'd']];
  function compareUS() {
    var g = G(), us = G('United States');
    var h = '<h2>How ' + esc(place()) + ' compares with the nation</h2><p class="lede">Higher or lower only counts when the gap is bigger than what a survey sample could produce by chance.</p><div class="rows rv">';
    VERDICT_ROWS.forEach(function (r) {
      var a = V(r[0], null, g), b = V(r[0], null, us), s1 = SE(r[0], null, g), s2 = SE(r[0], null, us);
      if (!ok(a, b)) { h += '<div class="vr"><span class="vl">' + r[1] + '</span><span class="vv">not published</span></div>'; return; }
      var known = ok(s1, s2), z = known ? Math.abs(a - b) / Math.sqrt(s1 * s1 + s2 * s2) : 0, real = z >= 1.96, hi = a > b;
      h += '<div class="vr"><span class="vl">' + r[1] + '</span><span class="vv"><b>' + money(a) + '</b> here, ' + money(b) + ' U.S.</span><span class="chip ' + (real ? (hi ? 'up' : 'down') : 'flat') + '">' + (!known ? 'Cannot tell' : real ? (hi ? 'Higher' : 'Lower') : 'About the same') + '</span></div>';
    });
    h += '</div><p class="note rv">"About the same" means the gap is within sampling error, not that the two are known to be equal. The test treats the two estimates as independent although ' + esc(place()) + ' is inside the national sample, so it is cautious. Six comparisons are shown without adjustment.</p>' + mepsSrc('family_premium') + mepsSrc('family_premium', 'United States');
    return chapter('c-cmp', h, '');
  }

  function ranking() {
    var names = Object.keys(D.geos).filter(function (k) { return k !== 'United States' && V('family_premium', null, D.geos[k]) != null; });
    names.sort(function (a, b) { return V('family_premium', null, D.geos[b]) - V('family_premium', null, D.geos[a]); });
    var mx = V('family_premium', null, D.geos[names[0]]), rk = names.indexOf(geo);
    var h = '<h2>' + (geo === 'United States' ? 'Which states pay the most' : 'Where ' + esc(place()) + ' ranks') + '</h2>';
    h += '<p class="lede">' + (rk >= 0 ? esc(place()) + ' ranks ' + (rk + 1) + ' of ' + names.length + ' states and D.C. in the average yearly price of a family plan, ' + D.years[L] + '.' : 'Average yearly price of a family plan, ' + D.years[L] + ', highest to lowest.') + ' States close together in the list are often within sampling error of each other.</p>';
    h += '<div class="card rv"><ol class="rank">' + names.map(function (n, i) { var v = V('family_premium', null, D.geos[n]); return '<li class="' + (n === geo ? 'sel' : '') + '"><span class="rn">' + (i + 1) + '</span><span class="nm">' + n + '</span><span class="rb"><i style="width:' + (v / mx * 100).toFixed(1) + '%"></i></span><span class="rv2">' + money(v) + '</span></li>'; }).join('') + '</ol>' + mepsSrc('family_premium', 'x') + '</div>';
    return chapter('c-rank', h, '');
  }

  function notYet() {
    var h = '<h2>What this story does not show</h2><p class="lede">Even with surveys and credit records, several things are missing.</p><ul class="gaps rv">' +
      '<li><b>Credit-record medical debt in California and six other states.</b> Credit records there no longer show it.' + (geo === 'California' ? ' The California survey above asks people instead, which is a different measure.' : '') + '</li>' +
      '<li><b>Who is hit hardest.</b> Skipped care and medical bills by income, race and county are published by <a href="https://statehealthcompare.shadac.org/" target="_blank" rel="noopener">SHADAC</a> and the <a href="https://healthpolicy.ucla.edu/our-work/california-health-interview-survey-chis" target="_blank" rel="noopener">California Health Interview Survey</a>. They are not reproduced here.</li>' +
      '<li><b>Cause and effect.</b> Nothing here shows that higher premiums led to skipped care or debt. The measures come from different surveys and are shown side by side.</li>' +
      '<li><b>Who has these plans.</b> The price data cover private-sector employers that offer coverage. They leave out public employers, firms with no plan, the self-employed and people without insurance.</li></ul>' +
      '<p class="rv"><a class="btn ghost" href="affordability-data.html">See the detailed numbers and charts</a></p>' +
      '<p class="small rv">Data pulled ' + esc(D.asof) + '. Plain-language wording is this site\'s; every figure is from the sources linked under each card. Hospital prices are tracked in the <a href="exhibits.html?topic=prices">exhibits</a>; this story does not show that hospital prices caused anything here.</p>';
    return chapter('c-end', h, 'last');
  }

  /* ---------- render ---------- */
  function render() {
    var html = hero() + price() + who() + destination() + stateWatch() + timeline() + compareTime() + deductible() + trouble();
    html += geo === 'United States' ? '' : compareUS();
    html += ranking() + notYet();
    $('#story').innerHTML = html;
    document.title = (geo === 'California' ? 'Where your health-care money goes' : 'Where health-care money goes in ' + place()) + ' | Hospital Price Watch';
    wire(); layout(); loadCounties();
  }

  function setGeo(g, fromHash) {
    geo = g;
    var tab = (g === 'California' || g === 'United States') ? g : 'other';
    $$('.geo-tabs button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.geo === tab); });
    $('#state-pick').hidden = tab !== 'other';
    if (tab === 'other') $('#state-select').value = g;
    if (!fromHash) { try { history.replaceState(null, '', '#' + encodeURIComponent(tab === 'other' ? g : (g === 'California' ? 'california' : 'us'))); } catch (e) {} }
    window.scrollTo(0, 0); render();
  }

  function init() {
    document.body.classList.add('story-open');
    var sel = $('#state-select');
    Object.keys(D.geos).filter(function (k) { return k !== 'United States' && k !== 'California'; }).sort().forEach(function (k) { sel.insertAdjacentHTML('beforeend', '<option>' + k + '</option>'); });
    $$('.geo-tabs button').forEach(function (b) { b.addEventListener('click', function () { var t = b.dataset.geo; setGeo(t === 'other' ? (sel.value || sel.options[0].value) : t); }); });
    sel.addEventListener('change', function () { setGeo(sel.value); });
    var hsh = decodeURIComponent((location.hash || '').slice(1));
    var hl = hsh.toLowerCase(); if (hl === 'us' || hl === 'united states') geo = 'United States'; else { var hit = Object.keys(D.geos).filter(function (k) { return k.toLowerCase() === hl && k !== 'United States'; })[0]; if (hit) geo = hit; }
    $$('.geo-tabs button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.geo === (geo === 'California' || geo === 'United States' ? geo : 'other')); });
    $('#state-pick').hidden = !(geo !== 'California' && geo !== 'United States'); if (geo !== 'California' && geo !== 'United States') sel.value = geo;
    render();
    window.addEventListener('hashchange', function () { var h2 = decodeURIComponent((location.hash || '').slice(1)).toLowerCase(), t = (h2 === 'us' || h2 === 'united states') ? 'United States' : (h2 === 'california' || !h2) ? 'California' : Object.keys(D.geos).filter(function (k) { return k.toLowerCase() === h2 && k !== 'United States'; })[0]; if (t && t !== geo) setGeo(t, true); });
    $$('.geo-tabs button').forEach(function (b, i, all) { b.addEventListener('keydown', function (e) { var j = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : -1; if (j < 0) return; var n = all[(j + all.length) % all.length]; n.focus(); n.click(); e.preventDefault(); }); });
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { clearTimeout(ctl.rs); ctl.rs = setTimeout(layout, 150); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
  }

  /* ---------- behaviour ---------- */
  function wire() {
    $$('[data-cov]', $('#story')).forEach(function (b) { b.addEventListener('click', function () { cov = b.dataset.cov; var y = window.pageYOffset, id = b.closest('section').id; render(); window.scrollTo(0, y); var nb = $('#' + id + ' [data-cov="' + cov + '"]'); if (nb) nb.focus({ preventScroll: true }); }); });
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (!e.isIntersecting) return; var el = e.target; el.classList.add('in'); io.unobserve(el); reveal(el); }); }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
    $$('.rv, .idx, .seg', $('#story')).forEach(function (el) { if (RM) { el.classList.add('in'); return; } io.observe(el); });
    var fl = $('#flow'); if (fl) startFlow(fl);
  }
  function reveal(el) {
    $$('[data-count]', el).concat(el.hasAttribute('data-count') ? [el] : []).forEach(function (n) { countUp(n); });
    if (el.classList.contains('seg')) el.style.width = el.dataset.w + '%';
    $$('.seg', el).forEach(function (s) { s.style.width = s.dataset.w + '%'; });
    if (el.classList.contains('idx') || $('.idx', el)) $$('.ln', el.classList.contains('idx') ? el.parentNode : el).forEach(function (p) { p.classList.add('draw'); });
  }
  function countUp(n) {
    var to = parseFloat(n.dataset.count), f = n.dataset.fmt, t0 = null;
    var fmt = function (x) { return f === '%' ? Math.round(x) + '%' : f === '%1' ? x.toFixed(1) + '%' : money(x); };
    if (RM) { n.textContent = fmt(to); return; }
    (function step(t) { if (t0 == null) t0 = t; var p = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - p, 3); n.textContent = fmt(to * e); if (p < 1) requestAnimationFrame(step); })(performance.now());
  }

  function startFlow(svg) {
    var pm = cov + '_premium', cm = cov + '_contribution', P = V(pm), C = V(cm), share = C / P, E = P - C;
    var ns = 'http://www.w3.org/2000/svg';
    svg.innerHTML = '<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa3b2"/></marker></defs>' +
      '<rect class="nd you" x="10" y="26" width="170" height="68" rx="12"/><text class="nt" x="95" y="55" text-anchor="middle">Your paycheck</text><text class="nv you" x="95" y="80" text-anchor="middle">' + money(C) + ' a year</text>' +
      '<rect class="nd emp" x="10" y="206" width="170" height="68" rx="12"/><text class="nt" x="95" y="235" text-anchor="middle">Your employer</text><text class="nv emp" x="95" y="260" text-anchor="middle">' + money(E) + ' a year</text>' +
      '<rect class="nd plan" x="440" y="110" width="190" height="80" rx="14"/><text class="nt" x="535" y="144" text-anchor="middle">Health plan</text><text class="nv" x="535" y="170" text-anchor="middle">' + money(P) + ' a year</text>' +
      '<path id="p1" class="pipe" d="M180 60 C 320 60 320 150 440 150" marker-end="url(#ar)"/><path id="p2" class="pipe" d="M180 240 C 320 240 320 150 440 150" marker-end="url(#ar)"/>';
    if (RM) return;
    var paths = [$('#p1', svg), $('#p2', svg)], len = paths.map(function (p) { return p.getTotalLength(); }), coins = [], last = 0, vis = false;
    new IntersectionObserver(function (es) { vis = es[0].isIntersecting; }).observe(svg);
    function tick(t) {
      if (!document.body.contains(svg)) return;
      if (vis) {
        if (t - last > 170) { last = t; var k = Math.random() < share ? 0 : 1; var c = document.createElementNS(ns, 'circle'); c.setAttribute('r', 5.5); c.setAttribute('class', 'coin ' + (k ? 'emp' : 'you')); svg.appendChild(c); coins.push({ el: c, k: k, p: 0 }); }
        for (var i = coins.length - 1; i >= 0; i--) {
          var q = coins[i]; q.p += 0.012; if (q.p >= 1) { svg.removeChild(q.el); coins.splice(i, 1); continue; }
          var pt = paths[q.k].getPointAtLength(q.p * len[q.k]); q.el.setAttribute('cx', pt.x); q.el.setAttribute('cy', pt.y);
        }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* flight path: a paper plane carrying a dollar bill follows scroll down the left gutter */
  var PLANE = '<g id="plane"><g transform="scale(1.25)"><rect x="-22" y="-6" width="18" height="12" rx="2" fill="#1b7a52" stroke="#0f5a3a" stroke-width="1"/><text x="-13" y="3.6" font-size="9" font-weight="700" fill="#fff" text-anchor="middle" font-family="Public Sans,sans-serif">$</text>' +
    '<path d="M0 -9 L28 0 L0 9 L7 0 Z" fill="#fff" stroke="#11151c" stroke-width="1.6" stroke-linejoin="round"/><path d="M7 0 L28 0 L0 9 Z" fill="#dde1e8" stroke="#11151c" stroke-width="1.2" stroke-linejoin="round"/></g></g>';
  function layout() {
    var hd = $('.site-header'); if (hd) $('.story-page').style.setProperty('--bar-top', (getComputedStyle(hd).position === 'sticky' ? hd.offsetHeight : 0) + 'px');
    var wrap = $('#story-wrap'), svg = $('#flight'); if (!wrap || !svg) return;
    var H = wrap.offsetHeight, w = svg.clientWidth || 56, stops = $$('[data-stop]', wrap).map(function (c) { return c.offsetTop + Math.min(60, c.offsetHeight / 2); });
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + H); svg.setAttribute('height', H);
    var d = 'M' + w / 2 + ' 0', px = w / 2, py = 0;
    stops.forEach(function (y, i) { var x = i % 2 ? w - 12 : 12, dy = y - py; d += ' C ' + px + ' ' + (py + dy * .55) + ' ' + x + ' ' + (y - dy * .55) + ' ' + x + ' ' + y; px = x; py = y; });
    d += ' L ' + px + ' ' + H;
    svg.innerHTML = '<path id="fp" class="fp-bg" d="' + d + '"/><path id="fd" class="fp-done" d="' + d + '"/>' + stops.map(function (y, i) { return '<circle class="stop" data-y="' + y + '" cx="' + (i % 2 ? w - 12 : 12) + '" cy="' + y + '" r="6"/>'; }).join('') + PLANE;
    ctl.fp = $('#fp'); ctl.fd = $('#fd'); ctl.len = ctl.fp.getTotalLength(); ctl.fd.style.strokeDasharray = ctl.len; ctl.plane = $('#plane'); ctl.stops = $$('.stop', svg); ctl.wrap = wrap;
    ctl.dashed = true; setupTimeline(); onScroll();
  }

  function setupTimeline() {
    var s = $('#tl'); if (!s) return; ctl.tl = s; var pin = $('.tl-pin', s), tr = $('.tl-track', s), vw = $('.tl-view', s);
    s.style.height = ''; s.style.paddingBottom = ''; s.classList.remove('pinned');
    var over = tr.scrollWidth - vw.clientWidth;
    if (RM || over < 8) return;
    var gb = $('.geo-bar').getBoundingClientRect(); ctl.tlTop = Math.ceil(gb.bottom) + 6; s.classList.add('pinned'); var ph = Math.min(window.innerHeight - ctl.tlTop - 8, 760);
    var af = $('.tl-after', s).offsetHeight + 24; s.style.paddingBottom = af + 'px'; pin.style.top = ctl.tlTop + 'px'; pin.style.height = ph + 'px'; s.style.height = (ph + af + over * 0.75) + 'px'; ctl.tlOver = over; ctl.tlPh = ph;
  }

  var raf = 0;
  function onScroll() { if (raf) return; raf = requestAnimationFrame(function () { raf = 0; frame(); }); }
  function frame() {
    if (!ctl.fp) return;
    var wr = ctl.wrap.getBoundingClientRect(), H = ctl.wrap.offsetHeight;
    var p = Math.max(0, Math.min(1, (window.innerHeight * 0.5 - wr.top) / H)), l = p * ctl.len;
    var pt = ctl.fp.getPointAtLength(l), pt2 = ctl.fp.getPointAtLength(Math.min(ctl.len, l + 2)), ang = Math.atan2(pt2.y - pt.y, pt2.x - pt.x) * 180 / Math.PI;
    ctl.plane.setAttribute('transform', 'translate(' + pt.x + ',' + pt.y + ') rotate(' + ang + ')');
    ctl.fd.style.strokeDashoffset = ctl.len - l;
    ctl.stops.forEach(function (c) { c.classList.toggle('lit', parseFloat(c.dataset.y) <= pt.y); });
    var s = ctl.tl; if (s && s.classList.contains('pinned')) {
      var r = s.getBoundingClientRect(), q = Math.max(0, Math.min(1, (ctl.tlTop - r.top) / (s.offsetHeight - ctl.tlPh)));
      $('.tl-track', s).style.transform = 'translate3d(' + (-q * ctl.tlOver) + 'px,0,0)';
      $('.tl-bill', s).style.left = (q * 100) + '%';
      $$('.yr', s).forEach(function (y, k) { var b = y.getBoundingClientRect(); y.classList.toggle('now', (q === 0 && k === 0) || (b.left > 0 && b.left < window.innerWidth * .45)); });
    }
  }
})();

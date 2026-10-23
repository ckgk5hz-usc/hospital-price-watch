/* Affordability story. Reads data/story.json (built by tools/afford_story.py) and draws every chapter in the browser.
   Nothing is typed in by hand: each figure on the page is a value from that file. */
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
    return chapter('c-price', h + '</div>', '');
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
    var h = '<h2>What this story does not show</h2><p class="lede">Prices and paychecks are only half of affordability. The other half is what happens when the two collide, and that data is not on this page yet.</p><ul class="gaps rv">' +
      '<li><b>Medical debt.</b> Credit-bureau data on debt in collections is published by the <a href="https://apps.urban.org/features/debt-interactive-map/" target="_blank" rel="noopener">Urban Institute</a>. We have not reproduced it.</li>' +
      '<li><b>Skipped care and trouble paying bills.</b> California Health Interview Survey estimates are published by <a href="https://statehealthcompare.shadac.org/" target="_blank" rel="noopener">SHADAC</a>. We have not reproduced them.</li>' +
      '<li><b>What people actually paid out of pocket</b>, and how much savings they had to cover it.</li>' +
      '<li><b>Who has these plans.</b> The survey covers private-sector employers that offer coverage. It leaves out public employers, workers at firms with no plan, the self-employed and people without insurance.</li></ul>' +
      '<p class="rv"><a class="btn ghost" href="affordability-data.html">See every number, chart and test</a></p>' +
      '<p class="small rv">Data pulled ' + esc(D.asof) + '. Plain-language wording is this site\'s; every figure is from the sources linked under each card. Hospital prices are tracked in the <a href="exhibits.html?topic=prices">exhibits</a>; this story does not show that hospital prices caused anything here.</p>';
    return chapter('c-end', h, 'last');
  }

  /* ---------- render ---------- */
  function render() {
    var html = hero() + price() + who() + destination() + timeline() + compareTime() + deductible();
    html += geo === 'United States' ? '' : compareUS();
    html += ranking() + notYet();
    $('#story').innerHTML = html;
    document.title = (geo === 'California' ? 'Where your health-care money goes' : 'Where health-care money goes in ' + place()) + ' | Hospital Price Watch';
    wire(); layout();
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
    var fmt = function (x) { return f === '%' ? Math.round(x) + '%' : money(x); };
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

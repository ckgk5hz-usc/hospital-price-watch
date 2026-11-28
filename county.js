(function(){
  // County profiles: ?c=County[&vs=Other][&view=report]. All numbers come precomputed from data/counties.json.
  // Colors carry meaning only where a direction is clear: green is better than California, red is worse, grey is about the same
  // or has no better/worse (a count of residents, a payer share).
  var body = document.getElementById('co-body'), selA = document.getElementById('co-c'), selB = document.getElementById('co-vs'), copy = document.getElementById('co-copy');
  var D = null, view = 'profile', mapState = null;
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pct(v, k){ return (v * 100).toFixed(k == null ? 1 : k) + '%'; }
  function sgn(v){ return (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(1) + '%'; }
  function money(v){ return '$' + Math.round(v).toLocaleString('en-US'); }
  function num(v){ return Math.round(v).toLocaleString('en-US'); }
  function enc(c){ return encodeURIComponent(c).replace(/%20/g, '+'); }
  var M = function(pair){ return pair[0]; };
  // each row: label, value getter (null if missing), formatter, direction (+1 higher is better, -1 higher is worse, 0 none), "same" band, note
  var ROWS = [
    ['People and hospitals'],
    ['Residents, 2020', function(s){ return s.pop; }, num, 0],
    ['General-acute hospitals', function(s){ return s.hosp; }, num, 0],
    ['Licensed beds per 1,000 residents', function(s){ return s.beds_per_k; }, function(v){ return v.toFixed(2); }, +1, 0.15, function(s){ return num(s.beds) + ' beds'; }],
    ['Finances, FY2023'],
    ['Hospitals losing money on operations', function(s){ return s.losing[1] ? s.losing[0] / s.losing[1] : null; }, function(v){ return pct(v, 0); }, -1, 0.05, function(s){ return s.losing[0] + ' of ' + s.losing[1]; }],
    ['Median operating margin', function(s){ return M(s.margin); }, sgn, +1, 0.01, function(s){ return n(s.margin); }],
    ['Median Medi-Cal share of charges', function(s){ return M(s.medi); }, function(v){ return pct(v, 0); }, 0, 0, function(s){ return n(s.medi); }],
    ['Median bad debt and charity care, share of charges', function(s){ return M(s.uncomp); }, function(v){ return pct(v, 1); }, 0, 0, function(s){ return n(s.uncomp); }],
    ['Prices paid by commercial insurers'],
    ['Median payment per hospital stay', function(s){ return M(s.ip); }, money, -1, 0.05, function(s){ return n(s.ip); }],
    ['Median payment as a multiple of Medicare', function(s){ return M(s.ipx); }, function(v){ return v.toFixed(2) + 'x'; }, -1, 0.05, function(s){ return n(s.ipx); }],
    ['Access'],
    ['Hospitals reporting births, 2012 to 2023', function(s){ return s.births[1] - s.births[0]; }, function(v, s){ return s.births[0] + ' → ' + s.births[1]; }, 'self'],
    ['Birth units that stopped', function(s){ return s.matstop; }, num, 'count'],
    ['Hospitals closed since 2012', function(s){ return s.closed; }, num, 'count']
  ];
  function n(pair){ return pair[0] == null ? (pair[1] ? 'too few hospitals (' + pair[1] + ')' : 'no hospitals') : 'median of ' + pair[1]; }
  // judge a county value against California: 'good', 'bad' or 'same'
  function judge(r, v, s){
    if (v == null) return 'na';
    if (r[3] === 'self') return v < 0 ? 'bad' : v > 0 ? 'good' : 'same';
    if (r[3] === 'count') return v > 0 ? 'bad' : 'same';
    if (!r[3]) return 'plain';
    var c = r[1](D.ca); if (c == null) return 'same';
    var band = r[4] || 0, d = (r[3] === -1 ? -1 : 1) * (v - c);
    var rel = (r[2] === sgn || r[0].indexOf('losing') > -1) ? d : d / Math.abs(c);   // margins and shares compare in points, money and ratios in percent
    return Math.abs(rel) <= band ? 'same' : rel > 0 ? 'good' : 'bad';
  }
  var WORD = {good: 'better than California', bad: 'worse than California', same: 'about the same as California', na: '', plain: ''};
  function cell(r, s, compare){
    var v = r[1](s);
    if (v == null) return '<td><span class="na">' + (r[5] ? r[5](s) : '–') + '</span></td>';
    var j = compare ? judge(r, v, s) : 'st';
    var txt = r[3] === 'self' ? r[2](v, s) : r[2](v);
    return '<td><span class="v ' + j + '"' + (compare && WORD[j] ? ' title="' + WORD[j] + '"' : '') + '>' + txt + '</span>' + (r[5] ? '<small>' + r[5](s) + '</small>' : '') + '</td>';
  }
  function table(a, b, na, nb){
    var h = '<div class="co-tw"><table class="co-t"><thead><tr><th scope="col">Measure</th><th scope="col"><i class="sw a"></i>' + esc(na) + '</th>' + (b ? '<th scope="col"><i class="sw b"></i>' + esc(nb) + '</th>' : '') + '<th scope="col">California</th></tr></thead><tbody>';
    ROWS.forEach(function(r){
      if (r.length === 1) { h += '<tr class="grp"><th colspan="' + (b ? 4 : 3) + '" scope="rowgroup">' + r[0] + '</th></tr>'; return; }
      h += '<tr><th scope="row">' + r[0] + '</th>' + cell(r, a, true) + (b ? cell(r, b, true) : '') + cell(r, D.ca, false).replace('<td>', '<td class="st">') + '</tr>';
    });
    return h + '</tbody></table></div><p class="co-key"><span><i class="good"></i>Better than California</span><span><i class="bad"></i>Worse</span><span><i class="same"></i>About the same</span><span>Uncolored: no better or worse</span></p>';
  }
  function lede(c, s){
    var l = s.losing, share = l[1] ? l[0] / l[1] : null, st = D.ca.losing[0] / D.ca.losing[1];
    var j = share == null ? 'same' : Math.abs(share - st) <= 0.05 ? 'same' : share > st ? 'bad' : 'good';
    var h = '<b>' + num(s.pop) + '</b> residents and <b>' + s.hosp + '</b> general-acute hospital' + (s.hosp === 1 ? '' : 's') + '.';
    if (l[1]) h += ' <b class="v ' + j + '">' + l[0] + ' of ' + l[1] + '</b> with FY2023 results lost money on operations, against <b>' + pct(st, 0) + '</b> statewide.';
    if (s.closed) h += ' <b class="v bad">' + s.closed + '</b> hospital' + (s.closed === 1 ? '' : 's') + ' closed since 2012.';
    if (s.matstop) h += ' <b class="v bad">' + s.matstop + '</b> stopped delivering babies.';
    return h;
  }

  /* ---------- map: click a county to open it; the view glides to the chosen county ---------- */
  function mapHTML(a, b){
    var s = '<div class="co-mapbar"><span id="co-mapcap">' + esc(a) + ' County' + (b ? ' and ' + esc(b) + ' County' : '') + '</span><button type="button" class="btn ghost sm" id="co-zoom">Show all of California</button></div>' +
      '<svg id="co-svg" viewBox="0 0 256 292" role="img" aria-label="Map of California counties with ' + esc(a) + ' County highlighted. Click a county to open it."><g id="co-g">';
    Object.keys(D.counties).forEach(function(c){ s += '<path class="' + (c === a ? 'a' : c === b ? 'b' : '') + '" data-c="' + esc(c) + '" d="' + D.counties[c].path + '"><title>' + esc(c) + ' County, ' + D.counties[c].hosp + ' hospitals</title></path>'; });
    s += '</g><g id="co-dots">';
    [a, b].forEach(function(c){ if (c) D.counties[c].hospitals.forEach(function(h){ if (h[8] != null) s += '<a href="hospital.html?id=' + h[0] + '"><circle data-x="' + h[8] + '" data-y="' + h[9] + '" cx="' + h[8] + '" cy="' + h[9] + '" r="2.2" class="' + (h[4] != null && h[4] < 0 ? 'neg' : 'pos') + '"><title>' + esc(h[1]) + (h[4] != null ? ', FY2023 margin ' + sgn(h[4]) : '') + '</title></circle></a>'; }); });
    return s + '</g></svg><p class="co-mapkey"><span><i class="neg"></i>Lost money in FY2023</span><span><i class="pos"></i>Made money or no data</span></p><p class="sub">Dots sit at the hospital\'s address or city center. Click a dot for the hospital\'s profile.</p>';
  }
  function bbox(names){
    var bb = null;
    names.forEach(function(c){ var p = document.querySelector('#co-g path[data-c="' + CSS.escape(c) + '"]'); if (!p) return; var r = p.getBBox();
      bb = bb ? {x0: Math.min(bb.x0, r.x), y0: Math.min(bb.y0, r.y), x1: Math.max(bb.x1, r.x + r.width), y1: Math.max(bb.y1, r.y + r.height)} : {x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height}; });
    if (!bb) return [0, 0, 256, 292];
    var w = bb.x1 - bb.x0, h = bb.y1 - bb.y0, pad = Math.max(w, h) * 0.18 + 4, W = w + 2 * pad, H = h + 2 * pad, ar = 256 / 292;
    if (W / H > ar) H = W / ar; else W = H * ar;   // keep the map's shape so nothing stretches
    var cx = (bb.x0 + bb.x1) / 2, cy = (bb.y0 + bb.y1) / 2;
    return [cx - W / 2, cy - H / 2, W, H];
  }
  function setView(to, animate){
    var svg = document.getElementById('co-svg'); if (!svg) return;
    var from = mapState || [0, 0, 256, 292], t0 = null, rm = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function apply(v){
      svg.setAttribute('viewBox', v.map(function(x){ return x.toFixed(2); }).join(' '));
      var k = v[2] / 256;   // keep dots and borders the same size on screen at any zoom
      [].forEach.call(svg.querySelectorAll('circle'), function(c){ c.setAttribute('r', (3.2 * k).toFixed(2)); c.style.strokeWidth = (0.9 * k) + 'px'; });
      [].forEach.call(svg.querySelectorAll('path'), function(p){ p.style.strokeWidth = (0.7 * k) + 'px'; });
      mapState = v;
    }
    if (!animate || rm) return apply(to);
    (function step(ts){ if (t0 == null) t0 = ts; var p = Math.min(1, (ts - t0) / 650), e = p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      apply(from.map(function(f, i){ return f + (to[i] - f) * e; })); if (p < 1) requestAnimationFrame(step); })(performance.now());
  }
  function wireMap(a, b){
    var zoomed = true, z = document.getElementById('co-zoom');
    mapState = null; setView([0, 0, 256, 292], false); setView(bbox([a, b].filter(Boolean)), true);
    z.addEventListener('click', function(){ zoomed = !zoomed; setView(zoomed ? bbox([a, b].filter(Boolean)) : [0, 0, 256, 292], true); z.textContent = zoomed ? 'Show all of California' : 'Zoom to ' + a; });
    [].forEach.call(document.querySelectorAll('#co-g path'), function(p){ p.addEventListener('click', function(){ var c = p.getAttribute('data-c'); if (c === a) return; selA.value = c; render(); }); });
  }

  /* ---------- lists ---------- */
  function hospitals(c){
    var hs = D.counties[c].hospitals;
    if (!hs.length) return '<p class="none">No general-acute hospital filed a recent annual report in ' + esc(c) + ' County.</p>';
    return '<div class="co-hw"><table class="co-h"><thead><tr><th scope="col">Hospital</th><th scope="col">Beds</th><th scope="col">Operating margin, FY2023</th><th scope="col">Commercial per stay</th><th scope="col">× Medicare</th><th scope="col">CMS stars</th></tr></thead><tbody>' +
      hs.map(function(h){ return '<tr><td><a href="hospital.html?id=' + h[0] + '">' + esc(h[1]) + '</a><span>' + esc(h[2]) + '</span></td><td>' + (h[3] == null ? '–' : num(h[3])) + '</td><td>' + (h[4] == null ? '–' : '<span class="v ' + (h[4] < 0 ? 'bad' : 'good') + '">' + sgn(h[4]) + '</span>') + '</td><td>' + (h[5] == null ? '–' : money(h[5])) + '</td><td>' + (h[6] == null ? '–' : (h[10] ? '<span class="odd" title="Outside ' + D.odd[0] + 'x to ' + D.odd[1] + 'x Medicare. The price page flags these as possibly misreported.">check</span> ' : '') + h[6].toFixed(2) + 'x') + '</td><td>' + (h[7] || '–') + '</td></tr>'; }).join('') + '</tbody></table></div>';
  }
  function lists(c){
    var x = D.counties[c];
    var mat = x.maternity.length ? '<ul>' + x.maternity.map(function(r){ return '<li><a href="hospital.html?id=' + r[0] + '">' + esc(r[1]) + '</a><span>No natural births from FY' + r[2] + (r[3] ? ' (preliminary)' : '') + '</span></li>'; }).join('') + '</ul>' : '<p class="none">None found in state filings.</p>';
    var clo = x.closures.length ? '<ul>' + x.closures.map(function(r){ return '<li>' + esc(r[0]) + '<span>' + esc(r[1] || '') + ', ' + (r[3] ? 'ended inpatient care' : 'closed') + ' ' + (r[2] || '') + '</span></li>'; }).join('') + '</ul>' : '<p class="none">No verified closures since 2012.</p>';
    var dis = '<ul>' + x.districts.map(function(r){ return '<li><a href="districts.html?d=' + r[0] + '">' + esc(r[1]) + '</a><span>District ' + r[0] + ': ' + pct(r[2], 0) + ' of the county\'s residents' + (r[3] != null ? '; benchmark premium ' + money(r[3]) + ' a month' : '') + '</span></li>'; }).join('') + '</ul>';
    return '<div class="co-lists"><section><h3>Birth units that stopped</h3>' + mat + '</section><section><h3>Closures since 2012</h3>' + clo + '</section><section><h3>Congressional districts</h3>' + dis + '<p class="sub">Premiums: Urban Institute, ' + D.premium_year + ', before subsidies.</p></section></div>';
  }

  /* ---------- simple report: the same numbers as a plain brief ---------- */
  // paired bars, county against California, one measure per row; each row has its own scale since units differ
  function cmpChart(c, s){
    var ca = D.ca, rows = [
      ['Hospitals losing money, FY2023', s.losing[1] ? s.losing[0] / s.losing[1] : null, ca.losing[0] / ca.losing[1], function(v){ return pct(v, 0); }],
      ['Medi-Cal share of charges, median', s.medi[0], ca.medi[0], function(v){ return pct(v, 0); }],
      ['Commercial payment as a multiple of Medicare', s.ipx[0], ca.ipx[0], function(v){ return v.toFixed(2) + 'x'; }],
      ['Licensed beds per 1,000 residents', s.beds_per_k, ca.beds_per_k, function(v){ return v.toFixed(2); }]
    ].filter(function(r){ return r[1] != null; });
    if (!rows.length) return '';
    var W = 560, L = 0, bw = 330, rh = 58, H = rows.length * rh + 26, svg = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(c) + ' County compared with California">';
    rows.forEach(function(r, i){
      var y = i * rh + 4, mx = Math.max(r[1], r[2]) * 1.15 || 1, w1 = bw * r[1] / mx, w2 = bw * r[2] / mx;
      svg += '<text x="0" y="' + (y + 11) + '" font-size="12.5" font-weight="600" fill="#11151c">' + r[0] + '</text>' +
        '<rect x="0" y="' + (y + 18) + '" width="' + w1.toFixed(1) + '" height="13" rx="3" fill="#2a78d6"/><text x="' + (w1 + 6).toFixed(1) + '" y="' + (y + 29) + '" font-size="12" fill="#11151c">' + r[3](r[1]) + '</text>' +
        '<rect x="0" y="' + (y + 34) + '" width="' + w2.toFixed(1) + '" height="13" rx="3" fill="#9aa1ad"/><text x="' + (w2 + 6).toFixed(1) + '" y="' + (y + 45) + '" font-size="12" fill="#52514e">' + r[3](r[2]) + '</text>';
    });
    svg += '<rect x="0" y="' + (H - 14) + '" width="10" height="10" rx="2" fill="#2a78d6"/><text x="15" y="' + (H - 5) + '" font-size="12" fill="#434b59">' + esc(c) + ' County</text><rect x="150" y="' + (H - 14) + '" width="10" height="10" rx="2" fill="#9aa1ad"/><text x="165" y="' + (H - 5) + '" font-size="12" fill="#434b59">California</text></svg>';
    return '<figure class="rp-fig">' + svg + '</figure>';
  }
  function report(c){
    var s = D.counties[c], ca = D.ca, b = [];
    b.push('<b>' + num(s.pop) + '</b> residents (2020 Census) and <b>' + s.hosp + '</b> general-acute hospitals with <b>' + num(s.beds) + '</b> licensed beds, or <b>' + (s.beds_per_k == null ? 'n/a' : s.beds_per_k.toFixed(2)) + '</b> per 1,000 residents (California: ' + ca.beds_per_k.toFixed(2) + ').<sup>1,2</sup>');
    if (s.losing[1]) b.push('<b>' + s.losing[0] + ' of ' + s.losing[1] + '</b> hospitals (' + pct(s.losing[0] / s.losing[1], 0) + ') lost money on operations in FY2023 (California: ' + pct(ca.losing[0] / ca.losing[1], 0) + ').' + (s.margin[0] != null ? ' The median operating margin was <b>' + sgn(s.margin[0]) + '</b> (California: ' + sgn(ca.margin[0]) + ').' : '') + '<sup>1</sup>');
    if (s.medi[0] != null) b.push('Medi-Cal accounted for <b>' + pct(s.medi[0], 0) + '</b> of charges at the median hospital (California: ' + pct(ca.medi[0], 0) + ').<sup>1</sup>');
    if (s.ip[0] != null) b.push('Commercial insurers paid the median hospital <b>' + money(s.ip[0]) + '</b> per adjusted stay, <b>' + s.ipx[0].toFixed(2) + ' times</b> what Medicare paid (California: ' + money(ca.ip[0]) + ', ' + ca.ipx[0].toFixed(2) + ' times).<sup>3</sup>');
    b.push('Hospitals reporting births went from <b>' + s.births[0] + '</b> in 2012 to <b>' + s.births[1] + '</b> in 2023. <b>' + s.matstop + '</b> birth unit' + (s.matstop === 1 ? '' : 's') + ' stopped and <b>' + s.closed + '</b> hospital' + (s.closed === 1 ? '' : 's') + ' closed or ended inpatient care since 2012.<sup>1,4</sup>');
    if (s.districts.length) b.push('Residents live in <b>' + s.districts.length + '</b> congressional district' + (s.districts.length === 1 ? '' : 's') + '; the largest share, ' + pct(s.districts[0][2], 0) + ', in District ' + s.districts[0][0] + ' (' + esc(s.districts[0][1]) + '), where the benchmark Marketplace premium for a 40-year-old is <b>' + money(s.districts[0][3]) + '</b> a month before subsidies.<sup>5</sup>');
    return '<article class="rp-doc co-rp"><header><p class="rp-kind">Hospital Price Watch county brief</p><h1>' + esc(c) + ' County</h1><p class="rp-meta">Built from the same data as the county profile. Medians need at least 3 hospitals.</p></header>' +
      '<section class="rp-key"><h2>Key findings</h2><ul>' + b.map(function(x){ return '<li>' + x + '</li>'; }).join('') + '</ul></section>' +
      '<section><h2>Compared with California</h2>' + cmpChart(c, s) + '</section>' +
      '<section class="rp-notes"><h2>Sources</h2><ol><li>HCAI Hospital Annual Financial Disclosure data, FY2012 to FY2023, general-acute hospitals (Kaiser Foundation hospitals excluded as non-comparable).</li><li><a href="' + D.sources.pop_url + '" target="_blank" rel="noopener">U.S. Census Bureau, 2020 Census DHC</a>, table P1.</li><li>HCAI Hospital Measurement dataset, ' + D.price_year + ', hospitals with at least 100 commercial stays.</li><li>Hospital Price Watch research on birth units (from HCAI filings) and on closures (each checked against news and state records).</li><li>Urban Institute, American Affordability Tracker, ' + D.premium_year + '; Census congressional district relationship files.</li></ol></section></article>';
  }

  function render(){
    var a = selA.value, b = selB.value === a ? '' : selB.value;
    var u = new URL(location.href); u.search = '';
    if (a) u.searchParams.set('c', a); if (a && b) u.searchParams.set('vs', b); if (a && view === 'report') u.searchParams.set('view', 'report');
    history.replaceState(null, '', u.toString().replace(/%20/g, '+'));
    copy.hidden = !a;
    if (!a) {
      document.getElementById('co-title').textContent = 'County profiles';
      var big = Object.keys(D.counties).sort(function(x, y){ return D.counties[y].pop - D.counties[x].pop; }).slice(0, 8);
      body.innerHTML = '<div class="co-empty">Choose a county above, or start with one of the largest:<ul>' + big.map(function(c){ return '<li><a href="?c=' + enc(c) + '">' + esc(c) + '</a></li>'; }).join('') + '</ul></div>';
      return;
    }
    var A = D.counties[a], B = b ? D.counties[b] : null;
    document.getElementById('co-title').textContent = a + ' County' + (b ? ' and ' + b + ' County' : '');
    document.title = a + ' County' + (b ? ' vs. ' + b : '') + ' | County profiles | Hospital Price Watch';
    var tabs = '<div class="co-views" role="group" aria-label="View"><button type="button" data-v="profile" aria-pressed="' + (view === 'profile') + '">Profile</button><button type="button" data-v="report" aria-pressed="' + (view === 'report') + '">Simple report</button></div>';
    if (view === 'report') {
      body.innerHTML = tabs + '<div class="co-rpwrap">' + report(a) + (b ? report(b) : '') + '<p class="rp-tools"><button type="button" class="btn ghost sm" onclick="window.print()">Print or save as PDF</button></p></div>';
    } else {
      var h = tabs + '<section aria-labelledby="co-h-a"><div class="co-top"><div class="co-main"><h2 id="co-h-a">At a glance</h2><p class="co-lede">' + lede(a, A) + (b ? '</p><p class="co-lede"><b>' + esc(b) + ' County:</b> ' + lede(b, B) : '') + '</p>' + table(A, B, a, b) +
        '<p class="sub">Medians need at least 3 hospitals. California includes ' + D.nocounty + ' hospitals HCAI lists without a county. Sources: HCAI annual financial disclosures (FY2023) and Hospital Measurement dataset (' + D.price_year + '); CMS star ratings (' + esc(D.sources.cms_date) + '); <a href="' + D.sources.pop_url + '" target="_blank" rel="noopener">2020 Census</a>; this site\'s maternity and closure research.</p></div><div class="co-map">' + mapHTML(a, b) + '</div></div></section>';
      [a, b].forEach(function(c){ if (!c) return; h += '<section><h2>Hospitals in ' + esc(c) + ' County</h2>' + hospitals(c) + '<p class="sub">Click a hospital for its full profile. A dash means no data or too few cases. <span class="odd">check</span> marks a payment outside ' + D.odd[0] + 'x to ' + D.odd[1] + 'x Medicare, which the price page flags as possibly misreported.</p></section><section>' + lists(c) + '</section>'; });
      body.innerHTML = h;
      wireMap(a, b);
    }
    [].forEach.call(body.querySelectorAll('.co-views button'), function(x){ x.addEventListener('click', function(){ view = x.dataset.v; render(); }); });
  }
  copy.addEventListener('click', function(){ navigator.clipboard && navigator.clipboard.writeText(location.href).then(function(){ copy.textContent = 'Link copied'; setTimeout(function(){ copy.textContent = 'Copy link'; }, 1600); }); });
  fetch('data/counties.json?v=' + (body.getAttribute('data-v') || '')).then(function(r){ return r.json(); }).then(function(d){
    D = d;
    var p = new URLSearchParams(location.search), c = p.get('c'), vs = p.get('vs');
    if (c && D.counties[c]) selA.value = c;
    if (vs && D.counties[vs]) selB.value = vs;
    if (p.get('view') === 'report') view = 'report';
    selA.addEventListener('change', render); selB.addEventListener('change', render);
    render();
  }).catch(function(){ body.innerHTML = '<p class="co-empty">The county data did not load. Reload the page to try again.</p>'; });
})();

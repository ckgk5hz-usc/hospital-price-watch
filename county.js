(function(){
  // County profiles: ?c=County[&vs=Other]. All numbers come precomputed from data/counties.json.
  var body = document.getElementById('co-body'), selA = document.getElementById('co-c'), selB = document.getElementById('co-vs'), copy = document.getElementById('co-copy');
  var D = null;
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pct(v, k){ return (v * 100).toFixed(k == null ? 1 : k) + '%'; }
  function sgn(v){ return (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(1) + '%'; }
  function money(v){ return '$' + Math.round(v).toLocaleString('en-US'); }
  function num(v){ return Math.round(v).toLocaleString('en-US'); }
  function m(pair, f){ return pair[0] == null ? '<span class="na">' + (pair[1] ? 'too few (' + pair[1] + ')' : 'none') + '</span>' : f(pair[0]) + '<small>median of ' + pair[1] + '</small>'; }
  var ROWS = [
    ['People and hospitals'],
    ['Residents, 2020', function(s){ return num(s.pop); }],
    ['General-acute hospitals', function(s){ return num(s.hosp); }],
    ['Licensed beds per 1,000 residents', function(s){ return s.beds_per_k == null ? '–' : s.beds_per_k.toFixed(2) + '<small>' + num(s.beds) + ' beds</small>'; }],
    ['Finances, FY2023'],
    ['Hospitals losing money on operations', function(s){ return s.losing[1] ? pct(s.losing[0] / s.losing[1], 0) + '<small>' + s.losing[0] + ' of ' + s.losing[1] + '</small>' : '<span class="na">none</span>'; }],
    ['Operating margin', function(s){ return m(s.margin, sgn); }],
    ['Medi-Cal share of charges', function(s){ return m(s.medi, function(v){ return pct(v, 0); }); }],
    ['Bad debt and charity care, share of charges', function(s){ return m(s.uncomp, function(v){ return pct(v, 1); }); }],
    ['Prices'],
    ['Commercial payment per hospital stay', function(s){ return m(s.ip, money); }],
    ['Commercial payment as a multiple of Medicare', function(s){ return m(s.ipx, function(v){ return v.toFixed(2) + 'x'; }); }],
    ['Access'],
    ['Hospitals reporting births, 2012 and 2023', function(s){ return s.births[0] + ' → ' + s.births[1]; }],
    ['Birth units that stopped', function(s){ return num(s.matstop); }],
    ['Hospitals closed since 2012', function(s){ return num(s.closed); }]
  ];
  function table(a, b, na, nb){
    var h = '<div class="co-tw"><table class="co-t"><thead><tr><th scope="col">Measure</th><th scope="col"><i style="background:#2a78d6"></i>' + esc(na) + '</th>' + (b ? '<th scope="col"><i style="background:#e3a467"></i>' + esc(nb) + '</th>' : '') + '<th scope="col">California</th></tr></thead><tbody>';
    ROWS.forEach(function(r){
      if (r.length === 1) { h += '<tr class="grp"><th colspan="' + (b ? 4 : 3) + '" scope="rowgroup">' + r[0] + '</th></tr>'; return; }
      h += '<tr><th scope="row">' + r[0] + '</th><td>' + r[1](a) + '</td>' + (b ? '<td>' + r[1](b) + '</td>' : '') + '<td class="st">' + r[1](D.ca) + '</td></tr>';
    });
    return h + '</tbody></table></div>';
  }
  function map(a, b){
    var s = '<svg viewBox="0 0 256 292" role="img" aria-label="Map of California with ' + esc(a) + (b ? ' and ' + esc(b) : '') + ' highlighted">';
    Object.keys(D.counties).forEach(function(c){ s += '<path class="' + (c === a ? 'a' : c === b ? 'b' : '') + '" d="' + D.counties[c].path + '"><title>' + esc(c) + '</title></path>'; });
    [a, b].forEach(function(c){ if (c) D.counties[c].hospitals.forEach(function(h){ if (h[8] != null) s += '<circle r="2.2" cx="' + h[8] + '" cy="' + h[9] + '"><title>' + esc(h[1]) + '</title></circle>'; }); });
    return s + '</svg><p>Dots are general-acute hospitals, placed at their address or city.</p>';
  }
  function hospitals(c){
    var hs = D.counties[c].hospitals;
    if (!hs.length) return '<p class="none">No general-acute hospital filed a recent annual report in ' + esc(c) + ' County.</p>';
    return '<div class="co-hw"><table class="co-h"><thead><tr><th scope="col">Hospital</th><th scope="col">Beds</th><th scope="col">Operating margin, FY2023</th><th scope="col">Commercial per stay</th><th scope="col">× Medicare</th><th scope="col">CMS stars</th></tr></thead><tbody>' +
      hs.map(function(h){ return '<tr><td><a href="hospital.html?id=' + h[0] + '">' + esc(h[1]) + '</a><span>' + esc(h[2]) + '</span></td><td>' + (h[3] == null ? '–' : num(h[3])) + '</td><td' + (h[4] != null && h[4] < 0 ? ' class="neg"' : '') + '>' + (h[4] == null ? '–' : sgn(h[4])) + '</td><td>' + (h[5] == null ? '–' : money(h[5])) + '</td><td>' + (h[6] == null ? '–' : (h[10] ? '<span class="odd" title="Outside ' + D.odd[0] + 'x to ' + D.odd[1] + 'x Medicare. The price page flags these as possibly misreported.">check</span> ' : '') + h[6].toFixed(2) + 'x') + '</td><td>' + (h[7] || '–') + '</td></tr>'; }).join('') + '</tbody></table></div>';
  }
  function lists(c){
    var x = D.counties[c];
    var mat = x.maternity.length ? '<ul>' + x.maternity.map(function(r){ return '<li><a href="hospital.html?id=' + r[0] + '">' + esc(r[1]) + '</a><span>No natural births from FY' + r[2] + (r[3] ? ' (preliminary)' : '') + '</span></li>'; }).join('') + '</ul>' : '<p class="none">None found in state filings.</p>';
    var clo = x.closures.length ? '<ul>' + x.closures.map(function(r){ return '<li>' + esc(r[0]) + '<span>' + esc(r[1] || '') + ', ' + (r[3] ? 'ended inpatient care' : 'closed') + ' ' + (r[2] || '') + '</span></li>'; }).join('') + '</ul>' : '<p class="none">No verified closures since 2012.</p>';
    var dis = '<ul>' + x.districts.map(function(r){ return '<li><a href="districts.html?d=' + r[0] + '">' + esc(r[1]) + '</a><span>District ' + r[0] + ': ' + pct(r[2], 0) + ' of the county\'s residents' + (r[3] != null ? '; benchmark premium ' + money(r[3]) + '/month' : '') + '</span></li>'; }).join('') + '</ul>';
    return '<div class="co-lists"><section><h3>Birth units that stopped</h3>' + mat + '</section><section><h3>Closures since 2012</h3>' + clo + '</section><section><h3>Congressional districts</h3>' + dis + '<p class="sub">Premiums: Urban Institute, ' + D.premium_year + ', before subsidies.</p></section></div>';
  }
  function render(){
    var a = selA.value, b = selB.value === a ? '' : selB.value;
    var u = new URL(location.href); u.search = '';
    if (a) u.searchParams.set('c', a); if (a && b) u.searchParams.set('vs', b);
    history.replaceState(null, '', u.toString().replace(/%20/g, '+'));
    copy.hidden = !a;
    if (!a) {
      document.getElementById('co-title').textContent = 'County profiles';
      var big = Object.keys(D.counties).sort(function(x, y){ return D.counties[y].pop - D.counties[x].pop; }).slice(0, 8);
      body.innerHTML = '<div class="co-empty">Choose a county above, or start with one of the largest:<ul>' + big.map(function(c){ return '<li><a href="?c=' + encodeURIComponent(c).replace(/%20/g, '+') + '">' + esc(c) + '</a></li>'; }).join('') + '</ul></div>';
      return;
    }
    var A = D.counties[a], B = b ? D.counties[b] : null;
    document.getElementById('co-title').textContent = a + ' County' + (b ? ' and ' + b + ' County' : '');
    document.title = a + ' County' + (b ? ' vs. ' + b : '') + ' | County profiles | Hospital Price Watch';
    var lede = num(A.pop) + ' residents and ' + A.hosp + ' general-acute hospital' + (A.hosp === 1 ? '' : 's') + '.' + (A.losing[1] ? ' ' + A.losing[0] + ' of ' + A.losing[1] + ' with FY2023 results lost money on operations (California: ' + pct(D.ca.losing[0] / D.ca.losing[1], 0) + ').' : '');
    var h = '<section aria-labelledby="co-h-a"><div class="co-top"><div><h2 id="co-h-a">At a glance</h2><p class="co-lede">' + lede + '</p>' + table(A, B, a, b) +
      '<p class="sub">Medians need at least 3 hospitals. California includes ' + D.nocounty + ' hospitals HCAI lists without a county. Sources: HCAI annual financial disclosures (FY2023) and Hospital Measurement dataset (' + D.price_year + '); CMS star ratings (' + esc(D.sources.cms_date) + '); <a href="' + D.sources.pop_url + '" target="_blank" rel="noopener">2020 Census</a>; this site\'s maternity and closure research.</p></div><div class="co-map">' + map(a, b) + '</div></div></section>';
    [a, b].forEach(function(c){ if (!c) return; h += '<section><h2>Hospitals in ' + esc(c) + ' County</h2>' + hospitals(c) + '<p class="sub">Click a hospital for its full profile. A dash means no data or too few cases. <span class="odd">check</span> marks a payment outside ' + D.odd[0] + 'x to ' + D.odd[1] + 'x Medicare, which the price page flags as possibly misreported.</p></section><section>' + lists(c) + '</section>'; });
    body.innerHTML = h;
  }
  copy.addEventListener('click', function(){ navigator.clipboard && navigator.clipboard.writeText(location.href).then(function(){ copy.textContent = 'Link copied'; setTimeout(function(){ copy.textContent = 'Copy link'; }, 1600); }); });
  fetch('data/counties.json').then(function(r){ return r.json(); }).then(function(d){
    D = d;
    var p = new URLSearchParams(location.search), c = p.get('c'), vs = p.get('vs');
    if (c && D.counties[c]) selA.value = c;
    if (vs && D.counties[vs]) selB.value = vs;
    selA.addEventListener('change', render); selB.addEventListener('change', render);
    render();
  }).catch(function(){ body.innerHTML = '<p class="co-empty">The county data did not load. Reload the page to try again.</p>'; });
})();

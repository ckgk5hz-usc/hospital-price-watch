(function(){
  var D = JSON.parse(document.getElementById('dz-data').textContent);
  var panel = document.getElementById('dz-panel'), sel = document.getElementById('dz-sel'), msg = document.getElementById('dz-msg'), zip = document.getElementById('dz-zip');
  function money(v){ return '$' + Math.round(v).toLocaleString('en-US'); }
  function pct(v, k){ return (v*100).toFixed(k||0) + '%'; }
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function vs(a, b){ var d = (a - b) / b; return Math.abs(d) < 0.005 ? 'about the same as California' : (d > 0 ? pct(d) + ' above' : pct(-d) + ' below') + ' California'; }

  // district line vs. California, one axis, dollars a month
  function trend(dp){
    var ys = Object.keys(D.ca.premium).filter(function(y){ return dp[y] != null; }), W = 380, Hh = 150, t = 18, b = 24, l = 6, r = 92;
    var all = ys.map(function(y){ return dp[y]; }).concat(ys.map(function(y){ return D.ca.premium[y]; }));
    var lo = Math.min.apply(null, all) * .92, hi = Math.max.apply(null, all) * 1.04;
    var X = function(i){ return l + i * (W - l - r) / (ys.length - 1); }, Y = function(v){ return t + (hi - v) / (hi - lo) * (Hh - t - b); };
    var line = function(get, c){ return '<polyline class="' + c + '" points="' + ys.map(function(y, i){ return X(i).toFixed(1) + ',' + Y(get(y)).toFixed(1); }).join(' ') + '"/>'; };
    var last = ys.length - 1, a = Y(dp[ys[last]]), c = Y(D.ca.premium[ys[last]]);
    if (Math.abs(a - c) < 13) { if (a < c) { a -= 6; c += 6; } else { a += 6; c -= 6; } }
    var s = '<svg class="chart" viewBox="0 0 ' + W + ' ' + Hh + '" role="img" aria-label="Benchmark premium by year, district and California">' +
      '<line class="axis" x1="' + l + '" y1="' + (Hh - b) + '" x2="' + (W - r) + '" y2="' + (Hh - b) + '"/>' +
      line(function(y){ return D.ca.premium[y]; }, 'line-mark2') + line(function(y){ return dp[y]; }, 'line-mark');
    ys.forEach(function(y, i){ s += '<circle class="tip" fill="transparent" r="10" cx="' + X(i) + '" cy="' + Y(dp[y]) + '" data-tip="' + y + ': ' + money(dp[y]) + ' (California ' + money(D.ca.premium[y]) + ')"/>';
      if (i % 3 === 0 || i === last) s += '<text x="' + X(i) + '" y="' + (Hh - 7) + '" font-size="11" text-anchor="middle">' + y + '</text>'; });
    s += '<text class="valtext" x="' + (X(last) + 6) + '" y="' + (a + 4) + '" font-size="11.5">' + money(dp[ys[last]]) + ' district</text>' +
         '<text x="' + (X(last) + 6) + '" y="' + (c + 4) + '" font-size="11.5">' + money(D.ca.premium[ys[last]]) + ' CA</text></svg>';
    return s;
  }

  function show(cd, from){
    var v = D.d[cd]; if (!v) return;
    var Y = D.Y, p = v.p[Y], n = Object.keys(D.rank).length;
    var row = function(label, val, ca, note){ return '<li><b>' + val + '</b><span>' + label + '</span><em>California: ' + ca + (note ? '. ' + note : '') + '</em></li>'; };
    panel.innerHTML = '<h3>District ' + parseInt(cd, 10) + '</h3><p class="sub" style="margin-top:0">' + esc(v.a) + (v.pl.length ? ': ' + esc(v.pl.slice(0, 5).join(', ')) : '') + '</p>' +
      '<p class="dz-big"><b>' + money(p) + '</b> a month in ' + Y + ', ' + vs(p, D.ca.premium[Y]) + '. Ranks ' + D.rank[cd] + ' of ' + n + (D.ties[cd] ? ', tied with ' + D.ties[cd] + ' other district' + (D.ties[cd] > 1 ? 's' : '') : '') + ' (1 is highest).</p>' +
      '<p class="sub">Benchmark Silver plan, 40-year-old, before subsidies. Up ' + pct(p / v.p[D.PY] - 1) + ' from ' + D.PY + ' and ' + pct(p / v.p['2017'] - 1) + ' since 2017 (California: ' + pct(D.ca.premium[Y] / D.ca.premium[D.PY] - 1) + ' and ' + pct(D.ca.premium[Y] / D.ca.premium['2017'] - 1) + ').</p>' +
      trend(v.p) + '<p class="sub" style="margin-top:2px">Solid: this district. Dashed: California.</p>' +
      '<ul class="dz-facts">' +
      (v.t != null ? row('of people live in families below the true cost of economic security (' + D.TY + ')', pct(v.t), pct(D.ca.tces)) : '') +
      (v.c.creditcard_delinquency_rate != null ? row('of people with credit card debt are 60 or more days late (' + D.CY + ')', pct(v.c.creditcard_delinquency_rate, 1), pct(D.ca.credit.creditcard_delinquency_rate, 1)) : '') +
      (v.c.auto_delinquency_rate != null ? row('of people with an auto or retail loan are 60 or more days late (' + D.CY + ')', pct(v.c.auto_delinquency_rate, 1), pct(D.ca.credit.auto_delinquency_rate, 1)) : '') +
      '</ul><p class="sub">Source: Urban Institute, American Affordability Tracker. <a href="#dz-read">How to read this</a>.</p>';
    [].forEach.call(document.querySelectorAll('.dmap path.on, #dz-t tr.on'), function(e){ e.classList.remove('on'); });
    [].forEach.call(document.querySelectorAll('.dmap path[data-cd="' + cd + '"], #dz-t tr[data-cd="' + cd + '"]'), function(e){ e.classList.add('on'); });
    sel.value = cd;
    try { history.replaceState(null, '', location.pathname + '?d=' + parseInt(cd, 10)); } catch (e) {}
    if (from === 'table') panel.scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  function lookup(z){
    var m = D.zips[z];
    if (!/^\d{5}$/.test(z)) { msg.textContent = 'Enter a five-digit ZIP code.'; return; }
    if (!m) { msg.textContent = 'ZIP ' + z + ' is not a California ZIP code area in the Census files. Some ZIPs used only for P.O. boxes are not included; try a nearby residential ZIP or pick the district.'; return; }
    if (m[0][1] >= 0.9) { msg.textContent = 'ZIP ' + z + ' is in District ' + parseInt(m[0][0], 10) + (m.length > 1 ? ' (' + pct(m[0][1]) + ' of its land area).' : '.'); show(m[0][0]); return; }
    msg.innerHTML = 'ZIP ' + z + ' is split: ' + m.map(function(x){ return '<button type="button" class="link-btn" data-pick="' + x[0] + '">District ' + parseInt(x[0], 10) + '</button> (' + pct(x[1]) + ' of its land)'; }).join(', ') + '. Showing the largest share.';
    show(m[0][0]);
  }

  document.getElementById('dz-form').addEventListener('submit', function(e){ e.preventDefault(); if (zip.value.trim()) lookup(zip.value.trim()); else if (sel.value) show(sel.value); });
  sel.addEventListener('change', function(){ if (sel.value) { msg.textContent = ''; show(sel.value); } });
  document.addEventListener('click', function(e){
    var t = e.target.closest && e.target.closest('[data-pick], .dmap path');
    if (!t) return;
    show(t.dataset.pick || t.dataset.cd, t.dataset.pick && t.closest('#dz-t') ? 'table' : 'map');
  });

  // table sorting
  var tb = document.querySelector('#dz-t tbody'), ths = [].slice.call(document.querySelectorAll('#dz-t thead th'));
  ths.forEach(function(th){ var b = th.querySelector('button'); if (!b) return; b.addEventListener('click', function(){
    var k = +b.dataset.k, desc = th.getAttribute('aria-sort') !== 'descending';
    ths.forEach(function(x){ x.removeAttribute('aria-sort'); }); th.setAttribute('aria-sort', desc ? 'descending' : 'ascending');
    [].slice.call(tb.rows).sort(function(a, c){ var x = +a.cells[k].dataset.v, y = +c.cells[k].dataset.v; return desc ? y - x : x - y; }).forEach(function(r){ tb.appendChild(r); });
  }); });
  ths[1].querySelector('button').click(); ths[1].querySelector('button').click();   // start sorted high to low

  var q = new URLSearchParams(location.search).get('d');
  if (q) show(('0' + q).slice(-2));
})();

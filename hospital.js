(function(){
  var body = document.getElementById('pf-body'), q = document.getElementById('pf-q'), vs = document.getElementById('pf-vs'), msg = document.getElementById('pf-msg');
  var IDX = [], PEERS = null, byLabel = {};
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pct(v, k){ return v == null ? 'n/a' : (v * 100).toFixed(k == null ? 1 : k) + '%'; }
  function sgn(v){ return v == null ? 'n/a' : (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(1) + '%'; }
  function money(v){ return v == null ? 'n/a' : '$' + Math.round(v).toLocaleString('en-US'); }
  function bigMoney(v){ if (v == null) return 'n/a'; var a = Math.abs(v), s = v < 0 ? '−$' : '$'; return a >= 1e9 ? s + (a / 1e9).toFixed(2) + 'B' : a >= 1e6 ? s + (a / 1e6).toFixed(1) + 'M' : s + Math.round(a).toLocaleString('en-US'); }
  function num(v){ return v == null ? 'n/a' : Math.round(v).toLocaleString('en-US'); }
  function label(r){ return r[1] + ' — ' + r[2]; }
  function get(u){ return fetch(u).then(function(r){ if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function lastFull(p){ var ys = Object.keys(p.annual).filter(function(y){ return y !== '2024' && p.annual[y].operating_margin != null; }); return ys.length ? ys[ys.length - 1] : Object.keys(p.annual).pop(); }

  // one axis, one unit: operating margin by year for each hospital and the state median
  function chart(ps){
    var med = PEERS.median.operating_margin, ys = PEERS.years.filter(function(y){ return med[y] != null; });
    var series = ps.map(function(p){ return ys.map(function(y){ return p.annual[y] ? p.annual[y].operating_margin : null; }); });
    var vals = [].concat.apply(ys.map(function(y){ return med[y]; }), series).filter(function(v){ return v != null; });
    var lo = Math.min(-0.05, Math.min.apply(null, vals)), hi = Math.max(0.05, Math.max.apply(null, vals));
    lo = Math.max(lo, -0.6); hi = Math.min(hi, 0.6);          // extreme years are clipped at +/-60% and say so in the tooltip
    var W = 640, Hh = 240, t = 16, b = 26, l = 44, r = 16, n = ys.length;
    var X = function(i){ return l + i * (W - l - r) / (n - 1); }, Y = function(v){ return t + (hi - Math.max(lo, Math.min(hi, v))) / (hi - lo) * (Hh - t - b); };
    var s = '<svg class="chart pf-chart" viewBox="0 0 ' + W + ' ' + Hh + '" role="img" aria-label="Operating margin by fiscal year">';
    [-0.4, -0.2, -0.1, 0, 0.1, 0.2, 0.4].forEach(function(g){ if (g >= lo && g <= hi) s += '<line class="' + (g === 0 ? 'axis' : 'grid') + '" x1="' + l + '" x2="' + (W - r) + '" y1="' + Y(g) + '" y2="' + Y(g) + '"/><text x="' + (l - 6) + '" y="' + (Y(g) + 4) + '" font-size="11" text-anchor="end">' + (g * 100) + '%</text>'; });
    var path = function(arr, cls){ var d = '', pen = false; arr.forEach(function(v, i){ if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(v).toFixed(1); pen = true; }); return '<path class="' + cls + '" d="' + d + '"/>'; };
    s += path(ys.map(function(y){ return med[y]; }), 'line-mark2');
    series.forEach(function(a, k){ s += path(a, k ? 'line-mark pf-b' : 'line-mark'); a.forEach(function(v, i){ if (v != null) s += '<circle class="tip ' + (k ? 'pf-dot-b' : 'dot-mark') + '" r="' + (k ? 3.5 : 3.5) + '" cx="' + X(i) + '" cy="' + Y(v) + '" data-tip="' + esc(ps[k].name) + ', FY' + ys[i] + (ys[i] === '2024' ? ' (preliminary)' : '') + ': ' + sgn(v) + (v < lo || v > hi ? ' (off the chart)' : '') + '; state median ' + sgn(med[ys[i]]) + '"/>'; }); });
    ys.forEach(function(y, i){ if (i % 2 === 0 || i === n - 1) s += '<text x="' + X(i) + '" y="' + (Hh - 7) + '" font-size="11" text-anchor="middle">' + "'" + y.slice(2) + (y === '2024' ? '*' : '') + '</text>'; });
    return s + '</svg><p class="pf-key"><span class="k a"></span>' + esc(ps[0].name) + (ps[1] ? '<span class="k b"></span>' + esc(ps[1].name) : '') + '<span class="k m"></span>State median</p>';
  }

  function payer(p){
    var m = p.payer_mix_2023; if (!m) return '<p class="sub">No payer mix reported.</p>';
    var parts = [['medicare', 'Medicare'], ['medical', 'Medi-Cal'], ['private', 'Private'], ['county', 'County'], ['other', 'Other']];
    return '<div class="pf-stack" role="img" aria-label="Payer mix of gross charges, FY2023">' + parts.map(function(x, i){ var v = m[x[0]] || 0; return v > 0 ? '<i class="s' + i + ' tip" style="width:' + (v * 100) + '%" title="' + x[1] + ': ' + pct(v) + '"></i>' : ''; }).join('') + '</div>' +
      '<p class="pf-legend">' + parts.map(function(x, i){ return '<span><i class="s' + i + '"></i>' + x[1] + ' ' + pct(m[x[0]] || 0, 0) + '</span>'; }).join('') + '</p>';
  }

  function stars(n){ return n ? '<span class="stars" aria-label="' + n + ' of 5 stars">' + '★'.repeat(n) + '<i>' + '★'.repeat(5 - n) + '</i></span>' : '<span class="na">no rating</span>'; }

  function facts(p){
    var f = [['City', p.city + ', ' + (p.county || '') + ' County'], ['Ownership', p.ownership || 'n/a'], ['System', p.system || 'Independent or not reported'], ['Licensed beds', num(p.beds)],
             ['County', p.county ? '<a href="county.html?c=' + encodeURIComponent(p.county).replace(/%20/g, '+') + '">' + esc(p.county) + ' County profile</a>' : 'n/a'], ['Setting', p.setting || 'n/a'], ['Safety-net (DSH)', p.safety_net == null ? 'n/a' : (p.safety_net ? 'Yes' : 'No')], ['CMS stars', p.price ? stars(p.price.stars) : '<span class="na">no rating</span>'], ['HCAI ID', p.id]];
    var flags = [];
    if (p.general_acute === false) flags.push('<span class="hc">Not a general-acute hospital</span> State medians below are for general-acute hospitals, so comparisons may not fit.');
    if (p.price && p.price.high_cost) flags.push('<span class="hc">OHCA high-cost hospital</span> Named by the state Office of Health Care Affordability as a high-cost hospital.');
    if (p.maternity) flags.push('<span class="odd">Births stopped</span> Reported natural births fell to zero from FY' + p.maternity.first_year_zero + ' (' + p.maternity.births_that_year + ' in FY' + p.maternity.last_year_with_births + ').');
    if (p.name !== p.hcai_name) flags.push('Listed in the HCAI financial disclosure as <b>' + esc(p.hcai_name) + '</b>.');
    return '<dl class="pf-facts">' + f.map(function(x){ return '<div><dt>' + x[0] + '</dt><dd>' + (x[0] === 'CMS stars' || x[0] === 'County' ? x[1] : esc(x[1])) + '</dd></div>'; }).join('') + '</dl>' + (flags.length ? '<ul class="pf-flags">' + flags.map(function(x){ return '<li>' + x + '</li>'; }).join('') + '</ul>' : '');
  }

  // dir: +1 higher is better, -1 higher is worse, 0 no better or worse; band: how close to the median still counts as "about the same"
  function keyRow(lab, get, fmt, medKey, y, dir, band, pts){ return {lab: lab, get: get, fmt: fmt, med: medKey ? PEERS.median[medKey][y] : null, dir: dir || 0, band: band || 0, pts: pts}; }
  var WORD = {good: 'better than the state median', bad: 'worse than the state median', same: 'about the same as the state median'};
  function judged(r, v){
    if (v == null) return r.fmt(v);
    if (!r.dir || r.med == null) return r.fmt(v);
    var d = r.dir * (v - r.med), rel = r.pts ? d : d / Math.abs(r.med), j = Math.abs(rel) <= r.band ? 'same' : rel > 0 ? 'good' : 'bad';
    return '<span class="v ' + j + '" title="' + WORD[j] + '">' + r.fmt(v) + '</span>';
  }

  // simple report: one hospital's figures as a plain brief, numbers in bold, numbered sources
  function brief(p, y){
    var a = p.annual[y] || {}, med = function(k){ return PEERS.median[k] ? PEERS.median[k][y] : null; }, b = [];
    b.push('<b>' + esc(p.name) + '</b> is a ' + esc((p.ownership || 'hospital').toLowerCase()) + ' hospital in ' + esc(p.city) + ', ' + esc(p.county || '') + ' County, with <b>' + num(p.beds) + '</b> licensed beds' + (p.system ? ', part of ' + esc(p.system) : '') + '.<sup>1</sup>');
    if (a.operating_margin != null) b.push('In FY' + y + ' its operating margin was <b>' + sgn(a.operating_margin) + '</b> (state median ' + sgn(med('operating_margin')) + ') and its total margin <b>' + sgn(a.total_margin) + '</b> (state median ' + sgn(med('total_margin')) + ').<sup>1</sup>');
    if (a.net_patient_revenue != null) b.push('Net patient revenue was <b>' + bigMoney(a.net_patient_revenue) + '</b>; operating income <b>' + bigMoney(a.operating_income) + '</b>.<sup>1</sup>');
    if (p.payer_mix_2023) b.push('Medicare accounted for <b>' + pct(p.payer_mix_2023.medicare || 0, 0) + '</b> of gross charges in FY2023, Medi-Cal <b>' + pct(p.payer_mix_2023.medical || 0, 0) + '</b> and private insurers <b>' + pct(p.payer_mix_2023.private || 0, 0) + '</b>.<sup>1</sup>');
    if (a.uncompensated_care_rate != null) b.push('Bad debt and charity care came to <b>' + pct(a.uncompensated_care_rate) + '</b> of charges (state median ' + pct(med('uncompensated_care_rate')) + ').<sup>1</sup>');
    if (p.price && p.price.ip != null) b.push('Commercial insurers paid <b>' + money(p.price.ip) + '</b> per adjusted stay, <b>' + (p.price.ip_x != null ? p.price.ip_x.toFixed(2) + ' times' : 'n/a') + '</b> what Medicare paid (state median ' + money(PEERS.price.ip) + ', ' + PEERS.price.ip_x.toFixed(2) + ' times).<sup>2</sup>');
    if (p.price && p.price.stars) b.push('CMS overall quality rating: <b>' + p.price.stars + ' of 5 stars</b>.<sup>3</sup>');
    if (p.maternity) b.push('Reported natural births fell to zero from <b>FY' + p.maternity.first_year_zero + '</b> (' + num(p.maternity.births_that_year) + ' in FY' + p.maternity.last_year_with_births + ').<sup>1</sup>');
    return '<article class="rp-doc co-rp"><header><p class="rp-kind">Hospital Price Watch hospital brief</p><h1>' + esc(p.name) + '</h1><p class="rp-meta">FY' + y + ', the latest full fiscal year. State medians are for ' + PEERS.n_cohort + ' general-acute hospitals.</p></header>' +
      '<section class="rp-key"><h2>Key findings</h2><ul>' + b.map(function(x){ return '<li>' + x + '</li>'; }).join('') + '</ul></section>' +
      '<section><h2>Operating margin since FY' + PEERS.years[0] + '</h2><figure class="rp-fig">' + chart([p]) + '</figure><p class="rp-intro">FY2024 is preliminary. Points beyond plus or minus 60% are drawn at the edge.</p></section>' +
      (p.payer_mix_2023 ? '<section><h2>Who pays, FY2023</h2><figure class="rp-fig">' + payer(p) + '</figure><p class="rp-intro">Share of gross charges by payer.</p></section>' : '') +
      '<section class="rp-notes"><h2>Sources</h2><ol><li>HCAI Hospital Annual Financial Disclosure data (HCAI ID ' + esc(p.id) + '). Margins are operating and total income over revenue.</li><li>HCAI Hospital Measurement dataset, ' + PEERS.price.year + '; payments adjusted for how sick patients were.</li><li>CMS Overall Hospital Quality Star Rating, ' + esc(PEERS.sources.cms_date) + '.</li></ol></section></article>';
  }

  function render(ps){
    var a = ps[0], y = lastFull(a), two = ps.length > 1;
    var A = function(p, k){ return p.annual[y] ? p.annual[y][k] : null; };
    var rows = [
      keyRow('Operating margin', function(p){ return A(p, 'operating_margin'); }, sgn, 'operating_margin', y, 1, 0.01, true),
      keyRow('Total margin', function(p){ return A(p, 'total_margin'); }, sgn, 'total_margin', y, 1, 0.01, true),
      keyRow('Net patient revenue', function(p){ return A(p, 'net_patient_revenue'); }, bigMoney),
      keyRow('Operating income', function(p){ return A(p, 'operating_income'); }, bigMoney),
      keyRow('Bad debt and charity care, share of charges', function(p){ return A(p, 'uncompensated_care_rate'); }, function(v){ return pct(v); }, 'uncompensated_care_rate', y),
      keyRow('Outpatient share of revenue', function(p){ return A(p, 'outpatient_share'); }, function(v){ return pct(v, 0); }, 'outpatient_share', y),
      keyRow('Medi-Cal share of discharges', function(p){ return A(p, 'medical_discharge_share'); }, function(v){ return pct(v, 0); }, 'medical_discharge_share', y),
      keyRow('Charges per dollar of net revenue', function(p){ return A(p, 'charge_ratio'); }, function(v){ return v == null ? 'n/a' : v.toFixed(1) + 'x'; }, 'charge_ratio', y, -1, 0.1),
      keyRow('Discharges', function(p){ return A(p, 'discharges'); }, num),
      keyRow('Average stay (days)', function(p){ return A(p, 'avg_stay_days'); }, function(v){ return v == null ? 'n/a' : v.toFixed(1); }, 'avg_stay_days', y)];
    var head = '<tr><th scope="col">FY' + y + '</th>' + ps.map(function(p){ return '<th scope="col">' + esc(p.name) + '</th>'; }).join('') + '<th scope="col">State median</th></tr>';
    var key = '<div class="hp-tbl pf-tbl"><table><thead>' + head + '</thead><tbody>' + rows.map(function(r){ return '<tr><th scope="row">' + r.lab + '</th>' + ps.map(function(p){ return '<td>' + judged(r, r.get(p)) + '</td>'; }).join('') + '<td class="med">' + (r.med == null ? '<span class="na">—</span>' : r.fmt(r.med)) + '</td></tr>'; }).join('') + '</tbody></table></div>';

    var P = PEERS.price, price = function(p){
      if (!p.price || (p.price.ip == null && p.price.op == null)) return '<p class="sub">' + esc(p.name) + ': no price data. The state publishes prices only for hospitals with enough commercial patients, and this site shows them only for general-acute hospitals.</p>';
      var r = p.price;
      return '<div class="pf-price"><h3>' + esc(p.name) + '</h3><div class="hp-big">' +
        (r.ip != null ? '<div><b>' + money(r.ip) + '</b><span>commercial payment per adjusted stay; Medicare paid ' + money(r.ip_mcr) + ' (' + (r.ip_x != null ? '<span class="v ' + (Math.abs(r.ip_x / P.ip_x - 1) <= .05 ? 'same' : r.ip_x > P.ip_x ? 'bad' : 'good') + '">' + r.ip_x.toFixed(2) + 'x</span>' : 'n/a') + (r.ip_odd ? ', unusual figure' : '') + '). State median ' + money(P.ip) + ', ' + P.ip_x.toFixed(2) + 'x.</span></div>' : '') +
        (r.op != null ? '<div><b>' + money(r.op) + '</b><span>commercial payment per adjusted outpatient visit; Medicare paid ' + money(r.op_mcr) + ' (' + (r.op_x != null ? '<span class="v ' + (Math.abs(r.op_x / P.op_x - 1) <= .05 ? 'same' : r.op_x > P.op_x ? 'bad' : 'good') + '">' + r.op_x.toFixed(2) + 'x</span>' : 'n/a') + (r.op_odd ? ', unusual figure' : '') + '). State median ' + money(P.op) + ', ' + P.op_x.toFixed(2) + 'x.</span></div>' : '') +
        '</div><p class="sub">' + num(r.stays) + ' commercial stays and ' + num(r.visits) + ' visits in the reporting year ending ' + esc(r.period_end) + '.' + (r.cah ? ' Critical access hospital.' : '') + '</p></div>';
    };

    var years = Object.keys(a.annual), cols = [['operating_margin', 'Op. margin', sgn], ['total_margin', 'Total margin', sgn], ['net_patient_revenue', 'Net patient revenue', bigMoney], ['uncompensated_care_rate', 'Bad debt + charity', function(v){ return pct(v); }],
      ['outpatient_share', 'Outpatient share', function(v){ return pct(v, 0); }], ['discharges', 'Discharges', num], ['avg_stay_days', 'Avg. stay', function(v){ return v == null ? 'n/a' : v.toFixed(1); }], ['medical_discharge_share', 'Medi-Cal discharges', function(v){ return pct(v, 0); }], ['natural_births', 'Natural births', num]];
    var yearTable = '<div class="hp-tbl"><table class="pf-years"><thead><tr><th scope="col">Fiscal year</th>' + cols.map(function(c){ return '<th scope="col">' + c[1] + '</th>'; }).join('') + '</tr></thead><tbody>' +
      years.slice().reverse().map(function(yy){ var r = a.annual[yy]; return '<tr><th scope="row">FY' + yy + (yy === '2024' ? '*' : '') + '</th>' + cols.map(function(c){ var v = r[c[0]], t = c[2](v); return '<td>' + (/margin/.test(c[0]) && v != null ? '<span class="v ' + (v < 0 ? 'bad' : 'good') + '">' + t + '</span>' : t) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';

    document.getElementById('hp-name').textContent = two ? a.name + ' and ' + ps[1].name : a.name;
    document.getElementById('hp-sub').textContent = two ? 'Side by side, with the state median.' : a.city + ', ' + (a.county || '') + ' County. ' + (a.ownership || '') + (a.system ? ', part of ' + a.system : '') + '.';
    document.title = (two ? a.name + ' vs ' + ps[1].name : a.name) + ' | Hospital Price Watch';
    var view = new URLSearchParams(location.search).get('view') === 'report' ? 'report' : 'profile';
    var tabs = '<div class="co-views" role="group" aria-label="View"><button type="button" data-v="profile" aria-pressed="' + (view === 'profile') + '">Profile</button><button type="button" data-v="report" aria-pressed="' + (view === 'report') + '">Simple report</button></div>';
    function setView(v){ var u = new URL(location.href); if (v === 'report') u.searchParams.set('view', 'report'); else u.searchParams.delete('view'); history.replaceState(null, '', u); render(ps); }
    if (view === 'report') {
      body.innerHTML = tabs + '<div class="co-rpwrap">' + ps.map(function(p){ return brief(p, y); }).join('') + '<p class="rp-tools"><button type="button" class="btn ghost sm" onclick="window.print()">Print or save as PDF</button></p></div>';
      [].forEach.call(body.querySelectorAll('.co-views button'), function(x){ x.addEventListener('click', function(){ setView(x.dataset.v); }); });
      return;
    }
    body.innerHTML = tabs + '<section><h2>Overview</h2><div class="pf-cols' + (two ? ' two' : '') + '">' + ps.map(function(p){ return '<div>' + (two ? '<h3>' + esc(p.name) + '</h3>' : '') + facts(p) + '</div>'; }).join('') + '</div></section>' +
      '<section><h2>Key figures, FY' + y + '</h2><p class="sub lead2">Latest full fiscal year. State median: ' + PEERS.n_cohort + ' general-acute hospitals.</p>' + key + '<p class="v-key"><span><i class="good"></i>Better than the state median</span><span><i class="bad"></i>Worse</span><span>Uncolored: no better or worse, such as payer shares or size</span></p></section>' +
      '<section><h2>Operating margin since FY' + PEERS.years[0] + '</h2>' + chart(ps) + '<p class="sub">*FY2024 is preliminary. Points beyond ±60% are drawn at the edge; hover for the value.</p></section>' +
      '<section><h2>Who pays</h2><p class="sub lead2">Share of gross charges by payer, FY2023.</p>' + ps.map(function(p){ return (two ? '<h3 class="pf-h3">' + esc(p.name) + '</h3>' : '') + payer(p); }).join('') + '</section>' +
      '<section><h2>Prices and quality</h2>' + ps.map(price).join('') + '<p class="sub">Prices from HCAI’s Hospital Measurement dataset (' + P.year + ' reporting year); payments adjusted for how sick patients were. Star rating: CMS, ' + esc(PEERS.sources.cms_date) + '. <a href="hospital-prices.html">Compare all hospitals</a>.</p></section>' +
      '<section><h2>Every year' + (two ? ', ' + esc(a.name) : '') + '</h2>' + yearTable + '<p class="sub"><button type="button" class="link-btn" id="pf-csv">Download this hospital’s figures (CSV)</button> · <a href="explorer.html">Explore all hospitals</a></p></section>';
    [].forEach.call(body.querySelectorAll('.co-views button'), function(x){ x.addEventListener('click', function(){ setView(x.dataset.v); }); });
    document.getElementById('pf-csv').addEventListener('click', function(){
      var lines = [['hospital', 'hcai_id', 'fiscal_year'].concat(Object.keys(a.annual[years[0]])).join(',')];
      years.forEach(function(yy){ var r = a.annual[yy]; lines.push(['"' + a.name.replace(/"/g, '""') + '"', a.id, yy].concat(Object.keys(r).map(function(k){ return r[k] == null ? '' : r[k]; })).join(',')); });
      lines.push('# Source: HCAI Hospital Annual Financial Disclosure data, via Hospital Price Watch. FY2024 preliminary.');
      var u = URL.createObjectURL(new Blob([lines.join('\n')], {type: 'text/csv'})), l = document.createElement('a'); l.href = u; l.download = 'hospital_' + a.id + '.csv'; document.body.appendChild(l); l.click(); l.remove(); URL.revokeObjectURL(u);
    });
  }

  function load(){
    var p = new URLSearchParams(location.search), id = p.get('id'), b = p.get('vs');
    document.getElementById('pf-vs-wrap').hidden = !id;
    if (!id) { body.innerHTML = ''; return; }
    var row = IDX.filter(function(r){ return r[0] === id; })[0];
    if (!row) { msg.textContent = 'No hospital with that ID. Search by name instead.'; return; }
    q.value = label(row);
    var vrow = b && IDX.filter(function(r){ return r[0] === b; })[0]; vs.value = vrow ? label(vrow) : '';
    body.innerHTML = '<p class="loading">Loading the profile…</p>';
    Promise.all([get('data/profiles/' + id + '.json')].concat(vrow ? [get('data/profiles/' + b + '.json')] : [])).then(render, function(){ body.innerHTML = '<p class="sub">The profile could not be loaded. Try again, or <a href="explorer.html">open the explorer</a>.</p>'; });
  }

  function go(id, b){ var u = '?id=' + id + (b ? '&vs=' + b : ''); history.pushState(null, '', u); load(); window.scrollTo(0, 0); }
  function pick(input){ var r = byLabel[input.value.trim()]; if (r) return r[0];
    var t = input.value.trim().toLowerCase(), m = IDX.filter(function(r){ return (r[1] + ' ' + r[2]).toLowerCase().indexOf(t) > -1; }); return m.length === 1 ? m[0][0] : null; }

  q.addEventListener('change', function(){ var id = pick(q); if (id) { msg.textContent = ''; go(id); } else if (q.value.trim()) { showMatches(q.value); } });
  vs.addEventListener('change', function(){ var b = pick(vs), id = new URLSearchParams(location.search).get('id'); if (b && id) go(id, b === id ? null : b); else if (!vs.value.trim() && id) go(id); });
  document.getElementById('pf-form').addEventListener('submit', function(e){ e.preventDefault(); var id = pick(q); if (id) go(id); else showMatches(q.value); });
  function showMatches(t){
    t = t.trim().toLowerCase(); var m = IDX.filter(function(r){ return (r[1] + ' ' + r[2] + ' ' + r[3]).toLowerCase().indexOf(t) > -1; }); if (t) m = m.slice(0, 30);
    msg.textContent = !t ? 'All ' + m.length + ' hospitals, A to Z.' : m.length ? m.length + (m.length === 30 ? '+' : '') + ' matches.' : 'No hospital matches "' + t + '".';
    document.getElementById('pf-pick').innerHTML = m.map(function(r){ return '<li><a href="?id=' + r[0] + '">' + esc(r[1]) + '</a> <span class="sub">' + esc(r[2]) + ', ' + esc(r[3]) + ' County' + (r[4] ? '' : ' · not general acute') + '</span></li>'; }).join('');
  }
  window.addEventListener('popstate', load);

  Promise.all([get('data/profiles/list.json'), get('data/profiles/peers.json')]).then(function(r){
    IDX = r[0]; PEERS = r[1];
    document.getElementById('pf-list').innerHTML = IDX.map(function(x){ byLabel[label(x)] = x; return '<option value="' + esc(label(x)) + '">'; }).join('');
    if (!new URLSearchParams(location.search).get('id')) showMatches('');
    load();
  });
})();

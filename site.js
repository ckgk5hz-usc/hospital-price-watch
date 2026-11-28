(function(){
  // chart tooltips (hover + keyboard focus)
  var tip = document.createElement('div'); tip.className = 'chart-tip'; tip.setAttribute('role','tooltip'); document.body.appendChild(tip);
  function place(x,y){ tip.style.left = Math.min(x+14, window.innerWidth-250) + 'px'; tip.style.top = (y+14) + 'px'; }
  document.addEventListener('mouseover', function(e){ var el = e.target.closest && e.target.closest('svg.chart .tip'); if (!el) return; tip.textContent = el.dataset.tip; tip.classList.add('on'); place(e.clientX,e.clientY); });
  document.addEventListener('mousemove', function(e){ if (tip.classList.contains('on')) place(e.clientX,e.clientY); });
  document.addEventListener('mouseout', function(e){ if (e.target.closest && e.target.closest('svg.chart .tip')) tip.classList.remove('on'); });
  document.addEventListener('focusin', function(e){ var el = e.target; if (el.matches && el.matches('svg.chart .tip')){ var r = el.getBoundingClientRect(); tip.textContent = el.dataset.tip; tip.classList.add('on'); place(r.left+r.width/2, r.top); } });
  document.addEventListener('focusout', function(){ tip.classList.remove('on'); });
})();

// global bar: a section button opens its full-width panel (click, Enter or Space; hover on a mouse once the pointer rests);
// Escape, the scrim, or a click elsewhere closes it. On phones the menu button opens one sheet instead.
(function(){
  var hdr = document.querySelector('.gnav'); if (!hdr) return;
  var btns = [].slice.call(hdr.querySelectorAll('.gb[aria-controls]')), scrim = document.querySelector('.gscrim');
  var menu = hdr.querySelector('.gmenu'), sheet = document.getElementById('gsheet');
  var cur = null, t = 0, at = 0, fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  function panel(b){ return document.getElementById(b.getAttribute('aria-controls')); }
  function open(b, focus){
    if (cur === b) return;
    var was = !!cur; shut(true);
    cur = b; at = Date.now(); b.setAttribute('aria-expanded', 'true');
    var p = panel(b); p.hidden = false; if (!was) { p.classList.remove('in'); void p.offsetWidth; p.classList.add('in'); }
    scrim.hidden = false;
    if (focus) { var a = p.querySelector('a'); if (a) a.focus(); }
  }
  function shut(keepScrim){
    if (cur) { cur.setAttribute('aria-expanded', 'false'); panel(cur).hidden = true; cur = null; }
    if (!keepScrim) scrim.hidden = true;
  }
  btns.forEach(function(b){
    b.addEventListener('click', function(e){ clearTimeout(t); if (cur === b) { if (Date.now() - at > 600) shut(); } else open(b, e.detail === 0); });   // a click just after a hover-open keeps the panel
    if (fine) {
      b.addEventListener('mouseenter', function(){ clearTimeout(t); t = setTimeout(function(){ open(b); }, cur ? 0 : 140); });
      b.addEventListener('mouseleave', function(){ clearTimeout(t); });
    }
  });
  if (fine) {
    hdr.addEventListener('mouseleave', function(){ clearTimeout(t); t = setTimeout(function(){ shut(); }, 260); });
    hdr.addEventListener('mouseenter', function(){ if (cur) clearTimeout(t); });
  }
  scrim.addEventListener('click', function(){ shut(); });
  document.addEventListener('keydown', function(e){
    if (e.key !== 'Escape') return;
    if (cur) { var b = cur; shut(); b.focus(); }
    if (menu && menu.getAttribute('aria-expanded') === 'true') { toggleSheet(false); menu.focus(); }
  });
  document.addEventListener('click', function(e){ if (cur && !hdr.contains(e.target)) shut(); });
  hdr.addEventListener('focusout', function(e){ if (cur && !hdr.contains(e.relatedTarget)) shut(); });
  function toggleSheet(on){
    menu.setAttribute('aria-expanded', on); sheet.hidden = !on; document.body.classList.toggle('gsheet-open', on);
    if (on) sheet.style.setProperty('--gsheet-top', Math.max(0, hdr.getBoundingClientRect().bottom) + 'px');
  }
  if (menu) menu.addEventListener('click', function(){ toggleSheet(menu.getAttribute('aria-expanded') !== 'true'); });
  matchMedia('(max-width:960px)').addEventListener('change', function(){ shut(); if (menu) toggleSheet(false); });
})();

(function(){
  // copy link / citation buttons on exhibit cards
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('[data-copy]'); if (!b) return;
    var done = function(){ var t = b.textContent; b.textContent = 'Copied'; setTimeout(function(){ b.textContent = t; }, 1400); };
    if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.copy).then(done, function(){ window.prompt('Copy this:', b.dataset.copy); });
    else window.prompt('Copy this:', b.dataset.copy);
  });
})();

// site search: header button or "/" opens a dialog; results come from data/search.json (pages, charts, hospitals, districts, glossary, reading)
(function(){
  var btn = document.querySelector('.search-btn'); if (!btn) return;
  var IDX = null, dlg, inp, out, sel = -1;
  var esc = function(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };
  var ORDER = ['Page', 'Story', 'Chart', 'Hospital', 'County', 'District', 'Glossary', 'Reading'];
  function build(){
    dlg = document.createElement('div'); dlg.className = 'srch'; dlg.hidden = true;
    dlg.innerHTML = '<div class="srch-box" role="dialog" aria-modal="true" aria-label="Search the site"><label class="srch-in"><svg width="18" height="18" viewBox="0 0 17 17" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M11.2 11.2 L15.5 15.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><span class="sr-only">Search</span><input type="search" placeholder="Hospital, county, ZIP code, chart or term" autocomplete="off" spellcheck="false"></label><div class="srch-out" role="listbox"></div><p class="srch-foot">Pages, charts, all 441 hospitals, 58 counties, 52 districts, glossary terms and research. <kbd>Esc</kbd> to close.</p></div>';
    document.body.appendChild(dlg); inp = dlg.querySelector('input'); out = dlg.querySelector('.srch-out');
    dlg.addEventListener('click', function(e){ if (e.target === dlg) close(); });
    inp.addEventListener('input', run);
    inp.addEventListener('keydown', function(e){
      var links = [].slice.call(out.querySelectorAll('a'));
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, Math.min(links.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1))); links.forEach(function(a, i){ a.classList.toggle('on', i === sel); }); if (links[sel]) links[sel].scrollIntoView({block: 'nearest'}); }
      if (e.key === 'Enter' && links.length) { e.preventDefault(); (links[sel] || links[0]).click(); }
    });
    dlg.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); });
  }
  function open(){ if (!dlg) build(); dlg.hidden = false; document.body.classList.add('srch-on'); inp.focus(); inp.select();
    if (!IDX) { out.innerHTML = '<p class="srch-empty">Loading&hellip;</p>'; fetch('data/search.json').then(function(r){ return r.json(); }).then(function(d){ IDX = d.map(function(r){ return r.concat([(r[1] + ' ' + r[2]).toLowerCase()]); }); run(); }); } else run(); }
  function close(){ dlg.hidden = true; document.body.classList.remove('srch-on'); btn.focus(); }
  function run(){
    if (!IDX) return; sel = -1;
    var q = inp.value.trim().toLowerCase(), words = q.split(/\s+/).filter(Boolean);
    if (!words.length) { out.innerHTML = '<p class="srch-empty">Try <button type="button" data-q="Kaiser">Kaiser</button> <button type="button" data-q="Fresno">Fresno</button> <button type="button" data-q="premium">premium</button> <button type="button" data-q="operating margin">operating margin</button> <button type="button" data-q="Medi-Cal">Medi-Cal</button></p>';
      [].forEach.call(out.querySelectorAll('[data-q]'), function(b){ b.onclick = function(){ inp.value = b.dataset.q; run(); inp.focus(); }; }); return; }
    // a five-digit ZIP code goes straight to its congressional district (premium and money strain) on the districts page
    if (/^9\d{4}$/.test(q)) { out.innerHTML = '<div class="srch-g"><h3>ZIP code</h3><a href="districts.html?zip=' + q + '" role="option"><b>ZIP ' + q + ': your congressional district</b><span>Its benchmark Marketplace premium, how many people fall short of a secure budget, and the counties and hospitals around it.</span></a></div>'; return; }
    var hits = IDX.map(function(r){ var t = r[1].toLowerCase(), s = 0;
      for (var i = 0; i < words.length; i++) { var w = words[i]; if (r[4].indexOf(w) < 0) return null; s += t.indexOf(w) === 0 ? 6 : (t.indexOf(' ' + w) > -1 ? 4 : (t.indexOf(w) > -1 ? 3 : 1)); }
      return [s, r]; }).filter(Boolean).sort(function(a, b){ return b[0] - a[0]; });
    if (!hits.length) { out.innerHTML = '<p class="srch-empty">Nothing matches "' + esc(inp.value) + '". Try a city, a hospital name or a word like "premium".</p>'; return; }
    var groups = {}; hits.forEach(function(h){ (groups[h[1][0]] = groups[h[1][0]] || []).push(h[1]); });
    out.innerHTML = ORDER.filter(function(g){ return groups[g]; }).map(function(g){
      return '<div class="srch-g"><h3>' + g + (groups[g].length > 6 ? ' <span>' + groups[g].length + '</span>' : '') + '</h3>' + groups[g].slice(0, 6).map(function(r){ var ext = /^https?:/.test(r[3]);
        return '<a href="' + esc(r[3]) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + ' role="option"><b>' + esc(r[1]) + '</b>' + (r[2] ? '<span>' + esc(r[2].length > 150 ? r[2].slice(0, 150) + '…' : r[2]) + '</span>' : '') + '</a>'; }).join('') + '</div>';
    }).join('');
  }
  btn.addEventListener('click', open);
  window.openSearch = function(q){ open(); if (q) { inp.value = q; run(); } };   // the home page's search field hands off here
  document.addEventListener('keydown', function(e){ if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) { e.preventDefault(); open(); } });
})();

// plain-English definitions in place: the first use of a glossary term in running text gets a dotted underline;
// hovering, focusing or tapping it shows the definition, with a link to the glossary.
(function(){
  var SCOPE = '.theme-intro, .theme-head .lede, .tk span, .ex .claim, .ex .src, .sstep p, .co-lede, .ch .lede, .ch .sub.lead, .rp-doc li, .rp-intro, .page-head .lede, .band-lede, .tile-cap';
  var roots = [].slice.call(document.querySelectorAll(SCOPE)); if (!roots.length || /glossary\.html/.test(location.pathname)) return;
  fetch('data/glossary.json').then(function(r){ return r.json(); }).then(function(G){
    var rules = []; G.forEach(function(g){ g.p.forEach(function(p){ rules.push({g: g, re: new RegExp('(^|[^\\w-])(' + p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')(?![\\w])', p === p.toUpperCase() ? '' : 'i')}); }); });
    rules.sort(function(a, b){ return b.re.source.length - a.re.source.length; });
    var used = {};
    roots.forEach(function(root){
      if (root.closest('a, button, .gterm, [hidden]')) return;
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), nodes = [], n;
      while ((n = walker.nextNode())) if (!n.parentNode.closest('a, button, .gterm, svg, script')) nodes.push(n);
      nodes.forEach(function(node){
        for (var i = 0; i < rules.length; i++) {
          var r = rules[i]; if (used[r.g.s]) continue;
          var m = r.re.exec(node.nodeValue); if (!m) continue;
          used[r.g.s] = 1;
          var at = m.index + m[1].length, word = m[2], after = node.splitText(at); after.nodeValue = after.nodeValue.slice(word.length);
          var sp = document.createElement('span'); sp.className = 'gterm'; sp.tabIndex = 0; sp.textContent = word; sp.dataset.g = r.g.s;
          node.parentNode.insertBefore(sp, after);
          node = after; i = -1;   // keep looking in the rest of this text for other terms
        }
      });
    });
    var by = {}; G.forEach(function(g){ by[g.s] = g; });
    var pop = document.createElement('div'); pop.className = 'gpop'; pop.setAttribute('role', 'tooltip'); pop.hidden = true; document.body.appendChild(pop);
    var cur = null, t = 0;
    function show(el){ var g = by[el.dataset.g]; if (!g) return; cur = el; clearTimeout(t);
      pop.innerHTML = '<b>' + g.t.replace(/</g, '&lt;') + '</b><span>' + g.d.replace(/</g, '&lt;') + '</span><a href="glossary.html#' + g.s + '">In the glossary</a>'; pop.hidden = false;
      var r = el.getBoundingClientRect(), w = Math.min(320, innerWidth - 24); pop.style.width = w + 'px';
      pop.style.left = Math.max(12, Math.min(innerWidth - w - 12, r.left + scrollX)) + 'px'; pop.style.top = (r.bottom + scrollY + 8) + 'px'; }
    function hide(){ t = setTimeout(function(){ pop.hidden = true; cur = null; }, 180); }
    document.addEventListener('mouseover', function(e){ var el = e.target.closest && e.target.closest('.gterm'); if (el) show(el); else if (e.target.closest && e.target.closest('.gpop')) clearTimeout(t); });
    document.addEventListener('mouseout', function(e){ if (e.target.closest && (e.target.closest('.gterm') || e.target.closest('.gpop'))) hide(); });
    document.addEventListener('focusin', function(e){ if (e.target.classList && e.target.classList.contains('gterm')) show(e.target); });
    document.addEventListener('focusout', function(e){ if (e.target.classList && e.target.classList.contains('gterm')) hide(); });
    document.addEventListener('click', function(e){ var el = e.target.closest && e.target.closest('.gterm'); if (el) { if (cur === el && !pop.hidden) { pop.hidden = true; cur = null; } else show(el); } else if (!e.target.closest('.gpop')) pop.hidden = true; });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') pop.hidden = true; });
  });
})();

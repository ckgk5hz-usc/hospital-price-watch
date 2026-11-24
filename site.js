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

// grouped nav menus: click or Enter/Space opens; Escape, a click elsewhere, or opening another menu closes
(function(){
  var groups = [].slice.call(document.querySelectorAll('.nav .grp'));
  function close(except){ groups.forEach(function(g){ if (g !== except) { g.classList.remove('open'); g.querySelector('button').setAttribute('aria-expanded', 'false'); } }); }
  groups.forEach(function(g){
    var b = g.querySelector('button');
    b.addEventListener('click', function(e){ e.stopPropagation(); var open = !g.classList.contains('open'); close(g); g.classList.toggle('open', open); b.setAttribute('aria-expanded', open); if (open && e.detail === 0) { var a = g.querySelector('.menu a'); if (a) a.focus(); } });
    g.addEventListener('keydown', function(e){ if (e.key === 'Escape') { close(); b.focus(); } });
    g.addEventListener('focusout', function(e){ if (!g.contains(e.relatedTarget)) { g.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); } });
  });
  document.addEventListener('click', function(e){ if (!e.target.closest('.nav .grp')) close(); });
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
  var ORDER = ['Page', 'Story', 'Chart', 'Hospital', 'District', 'Glossary', 'Reading'];
  function build(){
    dlg = document.createElement('div'); dlg.className = 'srch'; dlg.hidden = true;
    dlg.innerHTML = '<div class="srch-box" role="dialog" aria-modal="true" aria-label="Search the site"><label class="srch-in"><svg width="18" height="18" viewBox="0 0 17 17" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M11.2 11.2 L15.5 15.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><span class="sr-only">Search</span><input type="search" placeholder="Hospital, district, chart or term" autocomplete="off" spellcheck="false"></label><div class="srch-out" role="listbox"></div><p class="srch-foot">Pages, charts, all 441 hospitals, all 52 districts, glossary terms and research. <kbd>Esc</kbd> to close.</p></div>';
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
  document.addEventListener('keydown', function(e){ if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) { e.preventDefault(); open(); } });
})();

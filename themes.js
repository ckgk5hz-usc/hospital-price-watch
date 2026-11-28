(function(){
  // Key insights: one chart at a time. A finding in the list swaps the chart beside it; #s-<sub-topic> or #<chart id> opens that one.
  var list = document.querySelector('.ki-list'), panel = document.getElementById('ki-panel'); if (!list || !panel) return;
  var btns = [].slice.call(list.querySelectorAll('.ki-i'));
  function show(id, focus, scroll){
    var card = document.getElementById(id); if (!card) return;
    [].forEach.call(panel.children, function(c){ c.hidden = c !== card; });
    btns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.x === id); });
    var narrow = matchMedia('(max-width: 900px)').matches;
    if (scroll || narrow) { var r = panel.getBoundingClientRect(); if (r.top < 70 || r.top > innerHeight * 0.6) window.scrollTo({top: r.top + scrollY - 90, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}); }
    if (focus) { var h = card.querySelector('.claim'); if (h) { h.setAttribute('tabindex', '-1'); h.focus({preventScroll: true}); } }
  }
  btns.forEach(function(b, i){
    b.addEventListener('click', function(){ show(b.dataset.x, false, false); history.replaceState(null, '', '#' + b.dataset.x); });
    b.addEventListener('keydown', function(e){ var j = e.key === 'ArrowDown' ? i + 1 : e.key === 'ArrowUp' ? i - 1 : -1; if (j < 0 || !btns[j]) return; e.preventDefault(); btns[j].focus(); btns[j].click(); });
  });
  function fromHash(){
    var h = decodeURIComponent(location.hash.slice(1)); if (!h) return;
    if (h.indexOf('s-') === 0) { var g = document.getElementById(h); var b = g && g.querySelector('.ki-i'); if (b) show(b.dataset.x, false, true); return; }
    if (btns.some(function(b){ return b.dataset.x === h; })) show(h, false, true);
  }
  fromHash(); window.addEventListener('hashchange', fromHash);
})();

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

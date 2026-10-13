(function(){
  var root = document.documentElement; root.classList.add('js');
  var tabs = [].slice.call(document.querySelectorAll('.tab')), panels = [].slice.call(document.querySelectorAll('.panel'));
  function showTab(id){
    if (!panels.some(function(p){ return p.id===id; })) id = 'news';
    panels.forEach(function(p){ p.hidden = p.id!==id; });
    tabs.forEach(function(t){ t.setAttribute('aria-selected', t.dataset.tab===id); });
  }
  function fromHash(){ showTab((location.hash||'#news').slice(1)); }
  window.addEventListener('hashchange', fromHash); fromHash();
  tabs.forEach(function(t){ t.addEventListener('click', function(e){ e.preventDefault(); history.replaceState(null,'','#'+t.dataset.tab); showTab(t.dataset.tab); }); });

  var scope = 'national', stateSel = document.getElementById('state-select'), pick = document.querySelector('.state-pick');
  var rows = [].slice.call(document.querySelectorAll('#news-list > li'));
  var p = new URLSearchParams(location.search);
  if (['national','california','state'].indexOf(p.get('scope'))>-1) scope = p.get('scope');
  if (p.get('state')) stateSel.value = p.get('state');
  function apply(){
    var shown = 0, st = stateSel.value;
    rows.forEach(function(r){
      var ok = r.dataset.scope===scope && (scope!=='state' || !st || r.dataset.state===st);
      r.hidden = !ok; if (ok) shown++;
    });
    pick.hidden = scope!=='state';
    document.querySelectorAll('.seg .opt').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.scope===scope); });
    document.getElementById('news-empty').hidden = shown>0;
    var q = new URLSearchParams(); if (scope!=='national') q.set('scope',scope); if (scope==='state' && st) q.set('state',st);
    history.replaceState(null,'',location.pathname+(q.toString()?'?'+q:'')+location.hash);
  }
  document.querySelectorAll('.seg .opt').forEach(function(b){ b.addEventListener('click', function(){ scope = b.dataset.scope; apply(); }); });
  stateSel.addEventListener('change', apply); apply();
})();

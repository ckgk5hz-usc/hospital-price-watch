(function(){
  var items = [].slice.call(document.querySelectorAll('#results > [data-place]'));
  var placeBtns = [].slice.call(document.querySelectorAll('[data-place].opt'));
  var topicBoxes = [].slice.call(document.querySelectorAll('input[data-topic]'));
  var kindBtns = [].slice.call(document.querySelectorAll('[data-kind].opt'));
  var qBox = document.getElementById('q');
  var themeBtns = [].slice.call(document.querySelectorAll('[data-theme].opt'));
  var subBoxes = [].slice.call(document.querySelectorAll('input[data-sub]'));
  var state = {place:'all', topics:[], kind:'all', q:'', theme:'all', subs:[]};
  function read(){
    var p = new URLSearchParams(location.search);
    var pl = p.get('place'); if (pl && placeBtns.some(function(b){ return b.dataset.place===pl; })) state.place = pl;
    var k = p.get('source'); if (k && kindBtns.some(function(b){ return b.dataset.kind===k; })) state.kind = k;
    if (qBox && p.get('q')) { state.q = p.get('q'); qBox.value = state.q; }
    var th = p.get('theme'); if (th && themeBtns.some(function(b){ return b.dataset.theme===th; })) state.theme = th;
    (p.get('sub')||'').split(',').filter(Boolean).forEach(function(x){ var v = x.indexOf('/') > -1 ? x : state.theme + '/' + x; if (subBoxes.some(function(b){ return b.dataset.sub===v; })) state.subs.push(v); });
    (p.get('topic')||'').split(',').filter(Boolean).forEach(function(t){ if (topicBoxes.some(function(b){ return b.dataset.topic===t; })) state.topics.push(t); });
  }
  function write(){
    var p = new URLSearchParams();
    if (state.place!=='all') p.set('place', state.place);
    if (state.topics.length) p.set('topic', state.topics.join(','));
    if (state.kind!=='all') p.set('source', state.kind);
    if (state.q) p.set('q', state.q);
    if (state.theme!=='all') p.set('theme', state.theme);
    if (state.subs.length) p.set('sub', state.subs.map(function(x){ return x.split('/')[1]; }).join(','));
    var q = p.toString(); history.replaceState(null, '', location.pathname + (q ? '?'+q : '') + location.hash);
  }
  function apply(){
    var shown = 0;
    items.forEach(function(it){
      var ok = (state.place==='all' || it.dataset.place===state.place) &&
        (!state.topics.length || state.topics.some(function(t){ return it.dataset.topics.split(' ').indexOf(t)>-1; })) &&
        (state.kind==='all' || it.dataset.kind===state.kind) &&
        (state.theme==='all' || (' ' + (it.dataset.themes||'') + ' ').indexOf(' ' + state.theme + ' ') > -1) &&
        (!state.subs.length || state.subs.some(function(x){ return (' ' + (it.dataset.themes||'') + ' ').indexOf(' ' + x + ' ') > -1; })) &&
        (!state.q || it.textContent.toLowerCase().indexOf(state.q.toLowerCase())>-1);
      it.hidden = !ok; if (ok) shown++;
    });
    document.getElementById('count').textContent = shown;
    document.getElementById('empty').hidden = shown>0;
    placeBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.place===state.place); });
    topicBoxes.forEach(function(b){ b.checked = state.topics.indexOf(b.dataset.topic)>-1; });
    kindBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.kind===state.kind); });
    themeBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.theme===state.theme); });
    var sf = document.getElementById('sub-facet'); if (sf) { sf.hidden = state.theme==='all'; [].forEach.call(sf.querySelectorAll('li[data-parent]'), function(li){ li.hidden = li.dataset.parent !== state.theme; }); }
    subBoxes.forEach(function(b){ b.checked = state.subs.indexOf(b.dataset.sub) > -1; });
    document.getElementById('clear').hidden = state.place==='all' && !state.topics.length && state.kind==='all' && !state.q && state.theme==='all';
    write();
  }
  placeBtns.forEach(function(b){ b.addEventListener('click', function(){ state.place = b.dataset.place; apply(); }); });
  topicBoxes.forEach(function(b){ b.addEventListener('change', function(){ state.topics = topicBoxes.filter(function(x){ return x.checked; }).map(function(x){ return x.dataset.topic; }); apply(); }); });
  kindBtns.forEach(function(b){ b.addEventListener('click', function(){ state.kind = b.dataset.kind; apply(); }); });
  if (qBox) qBox.addEventListener('input', function(){ state.q = qBox.value.trim(); apply(); });
  themeBtns.forEach(function(b){ b.addEventListener('click', function(){ state.theme = b.dataset.theme; state.subs = []; apply(); }); });
  subBoxes.forEach(function(b){ b.addEventListener('change', function(){ state.subs = subBoxes.filter(function(x){ return x.checked; }).map(function(x){ return x.dataset.sub; }); apply(); }); });
  function reset(){ state.theme='all'; state.subs=[]; state.place='all'; state.topics=[]; state.kind='all'; state.q=''; if (qBox) qBox.value=''; apply(); }
  document.getElementById('clear').addEventListener('click', reset);
  document.getElementById('reset').addEventListener('click', reset);
  read(); apply();
  // a link to one exhibit shows it even if filters would hide it
  var h = location.hash.slice(1), el = h && document.getElementById(h);
  if (el && el.hidden) reset();
  if (el) { el.classList.add('target'); el.scrollIntoView(); }
})();

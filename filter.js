(function(){
  var items = [].slice.call(document.querySelectorAll('#results > [data-place]'));
  var placeBtns = [].slice.call(document.querySelectorAll('[data-place].opt'));
  var topicBoxes = [].slice.call(document.querySelectorAll('input[data-topic]'));
  var kindBtns = [].slice.call(document.querySelectorAll('[data-kind].opt'));
  var qBox = document.getElementById('q');
  var state = {place:'all', topics:[], kind:'all', q:''};
  function read(){
    var p = new URLSearchParams(location.search);
    var pl = p.get('place'); if (pl && placeBtns.some(function(b){ return b.dataset.place===pl; })) state.place = pl;
    var k = p.get('source'); if (k && kindBtns.some(function(b){ return b.dataset.kind===k; })) state.kind = k;
    if (qBox && p.get('q')) { state.q = p.get('q'); qBox.value = state.q; }
    (p.get('topic')||'').split(',').filter(Boolean).forEach(function(t){ if (topicBoxes.some(function(b){ return b.dataset.topic===t; })) state.topics.push(t); });
  }
  function write(){
    var p = new URLSearchParams();
    if (state.place!=='all') p.set('place', state.place);
    if (state.topics.length) p.set('topic', state.topics.join(','));
    if (state.kind!=='all') p.set('source', state.kind);
    if (state.q) p.set('q', state.q);
    var q = p.toString(); history.replaceState(null, '', location.pathname + (q ? '?'+q : '') + location.hash);
  }
  function apply(){
    var shown = 0;
    items.forEach(function(it){
      var ok = (state.place==='all' || it.dataset.place===state.place) &&
        (!state.topics.length || state.topics.some(function(t){ return it.dataset.topics.split(' ').indexOf(t)>-1; })) &&
        (state.kind==='all' || it.dataset.kind===state.kind) &&
        (!state.q || it.textContent.toLowerCase().indexOf(state.q.toLowerCase())>-1);
      it.hidden = !ok; if (ok) shown++;
    });
    document.getElementById('count').textContent = shown;
    document.getElementById('empty').hidden = shown>0;
    placeBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.place===state.place); });
    topicBoxes.forEach(function(b){ b.checked = state.topics.indexOf(b.dataset.topic)>-1; });
    kindBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.kind===state.kind); });
    document.getElementById('clear').hidden = state.place==='all' && !state.topics.length && state.kind==='all' && !state.q;
    write();
  }
  placeBtns.forEach(function(b){ b.addEventListener('click', function(){ state.place = b.dataset.place; apply(); }); });
  topicBoxes.forEach(function(b){ b.addEventListener('change', function(){ state.topics = topicBoxes.filter(function(x){ return x.checked; }).map(function(x){ return x.dataset.topic; }); apply(); }); });
  kindBtns.forEach(function(b){ b.addEventListener('click', function(){ state.kind = b.dataset.kind; apply(); }); });
  if (qBox) qBox.addEventListener('input', function(){ state.q = qBox.value.trim(); apply(); });
  function reset(){ state.place='all'; state.topics=[]; state.kind='all'; state.q=''; if (qBox) qBox.value=''; apply(); }
  document.getElementById('clear').addEventListener('click', reset);
  document.getElementById('reset').addEventListener('click', reset);
  read(); apply();
  // copy link / citation buttons on exhibit cards
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('[data-copy]'); if (!b) return;
    var done = function(){ var t = b.textContent; b.textContent = 'Copied'; setTimeout(function(){ b.textContent = t; }, 1400); };
    if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.copy).then(done, function(){ window.prompt('Copy this:', b.dataset.copy); });
    else window.prompt('Copy this:', b.dataset.copy);
  });
  // a link to one exhibit shows it even if filters would hide it
  var h = location.hash.slice(1), el = h && document.getElementById(h);
  if (el && el.hidden) reset();
  if (el) { el.classList.add('target'); el.scrollIntoView(); }
})();

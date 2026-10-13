(function(){
  var items = [].slice.call(document.querySelectorAll('#results > [data-place]'));
  var placeBtns = [].slice.call(document.querySelectorAll('[data-place].opt'));
  var topicBoxes = [].slice.call(document.querySelectorAll('input[data-topic]'));
  var state = {place:'all', topics:[]};
  function read(){
    var p = new URLSearchParams(location.search);
    var pl = p.get('place'); if (pl && placeBtns.some(function(b){ return b.dataset.place===pl; })) state.place = pl;
    (p.get('topic')||'').split(',').filter(Boolean).forEach(function(t){ if (topicBoxes.some(function(b){ return b.dataset.topic===t; })) state.topics.push(t); });
  }
  function write(){
    var p = new URLSearchParams();
    if (state.place!=='all') p.set('place', state.place);
    if (state.topics.length) p.set('topic', state.topics.join(','));
    var q = p.toString(); history.replaceState(null, '', location.pathname + (q ? '?'+q : ''));
  }
  function apply(){
    var shown = 0;
    items.forEach(function(it){
      var ok = (state.place==='all' || it.dataset.place===state.place) &&
        (!state.topics.length || state.topics.some(function(t){ return it.dataset.topics.split(' ').indexOf(t)>-1; }));
      it.hidden = !ok; if (ok) shown++;
    });
    document.getElementById('count').textContent = shown;
    document.getElementById('empty').hidden = shown>0;
    placeBtns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.place===state.place); });
    topicBoxes.forEach(function(b){ b.checked = state.topics.indexOf(b.dataset.topic)>-1; });
    document.getElementById('clear').hidden = state.place==='all' && !state.topics.length;
    write();
  }
  placeBtns.forEach(function(b){ b.addEventListener('click', function(){ state.place = b.dataset.place; apply(); }); });
  topicBoxes.forEach(function(b){ b.addEventListener('change', function(){ state.topics = topicBoxes.filter(function(x){ return x.checked; }).map(function(x){ return x.dataset.topic; }); apply(); }); });
  function reset(){ state.place='all'; state.topics=[]; apply(); }
  document.getElementById('clear').addEventListener('click', reset);
  document.getElementById('reset').addEventListener('click', reset);
  read(); apply();
})();

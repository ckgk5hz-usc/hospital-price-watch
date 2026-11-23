(function(){
  // Scroll story engine. Each step gives every mark [x, y, w, h, color, opacity]; marks glide to their new place when a step
  // reaches the middle of the screen. Labels and reference lines cross-fade. Reduced-motion readers get the end state at once.
  var D = JSON.parse(document.getElementById('sx-data').textContent);
  var svg = document.getElementById('sx-svg'), NS = 'http://www.w3.org/2000/svg';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var marks = [], cur = [], step = -1, raf = 0;
  var gLines = el('g', {'class': 'sx-lines'}), gMarks = el('g', {'class': 'sx-marks'}), gLabs = el('g', {'class': 'sx-labs'});
  svg.appendChild(gLines); svg.appendChild(gMarks); svg.appendChild(gLabs);
  function el(n, a){ var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); return e; }
  function rgb(h){ h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
  function hex(c){ return 'rgb(' + c.map(function(v){ return Math.round(v); }).join(',') + ')'; }
  var first = D.steps[0].s;
  first.forEach(function(m, i){
    var r = el('rect', {});
    gMarks.appendChild(r); marks.push(r);
    cur.push([m[0], m[1], m[2], m[3], rgb(m[4]), 0]);
  });
  function round(i, w){ return D.shape === 'rect' ? 2 : (D.shape === 'dot2' && i < 2 ? 4 : w / 2); }
  function paint(){
    for (var i = 0; i < marks.length; i++) {
      var c = cur[i], r = marks[i];
      r.setAttribute('x', c[0].toFixed(1)); r.setAttribute('y', c[1].toFixed(1));
      r.setAttribute('width', Math.max(0, c[2]).toFixed(1)); r.setAttribute('height', Math.max(0, c[3]).toFixed(1));
      r.setAttribute('rx', Math.min(round(i, c[2]), c[2] / 2, c[3] / 2).toFixed(1));
      r.setAttribute('fill', hex(c[4])); r.setAttribute('opacity', c[5].toFixed(2));
    }
  }
  function ease(t){ return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function overlay(s){
    var old = [].slice.call(gLabs.childNodes).concat([].slice.call(gLines.childNodes));
    old.forEach(function(n){ n.classList.add('out'); setTimeout(function(){ n.remove(); }, reduce ? 0 : 350); });
    (s.ln || []).forEach(function(l){ var e = el('line', {x1: l[0], y1: l[1], x2: l[2], y2: l[3], 'class': 'sx-ref in'}); gLines.appendChild(e); });
    s.l.forEach(function(l){ var t = el('text', {x: l[0], y: l[1], 'text-anchor': l[3], 'font-weight': l[4], 'class': 'sx-lab in'}); t.textContent = l[2]; gLabs.appendChild(t); });
    requestAnimationFrame(function(){ [].forEach.call(svg.querySelectorAll('.in'), function(n){ n.classList.remove('in'); }); });
  }
  function go(k){
    if (k === step || !D.steps[k]) return;
    step = k; var s = D.steps[k], from = cur.map(function(c){ return c.slice(); }), to = s.s.map(function(m){ return [m[0], m[1], m[2], m[3], rgb(m[4]), m[5]]; });
    svg.setAttribute('aria-label', s.alt);
    overlay(s);
    cancelAnimationFrame(raf);
    var dur = reduce ? 0 : 1100, spread = reduce ? 0 : 450, n = marks.length, t0 = performance.now();
    function frame(now){
      var done = true;
      for (var i = 0; i < n; i++) {
        var d = (i / n) * spread, p = dur ? Math.min(1, Math.max(0, (now - t0 - d) / dur)) : 1, e = ease(p);
        if (p < 1) done = false;
        for (var j = 0; j < 4; j++) cur[i][j] = from[i][j] + (to[i][j] - from[i][j]) * e;
        for (j = 0; j < 3; j++) cur[i][4][j] = from[i][4][j] + (to[i][4][j] - from[i][4][j]) * e;
        cur[i][5] = from[i][5] + (to[i][5] - from[i][5]) * e;
      }
      paint();
      if (!done) raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    [].forEach.call(document.querySelectorAll('.sstep'), function(x){ x.classList.toggle('on', +x.dataset.i === k); });
  }
  paint();
  var steps = [].slice.call(document.querySelectorAll('.sstep[data-i]'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting) go(+e.target.dataset.i); }); }, {rootMargin: '-45% 0px -45% 0px'});
    steps.forEach(function(s){ io.observe(s); });
  }
  go(0);
})();

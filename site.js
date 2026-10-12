(function(){
  // Chart tooltips (hover + keyboard focus)
  var tip = document.createElement('div'); tip.className = 'chart-tip'; tip.setAttribute('role','tooltip'); document.body.appendChild(tip);
  function place(x,y){ tip.style.left = Math.min(x+14, window.innerWidth-250) + 'px'; tip.style.top = (y+14) + 'px'; }
  document.querySelectorAll('svg.chart .tip').forEach(function(el){
    el.addEventListener('mouseenter', function(e){ tip.textContent = el.dataset.tip; tip.classList.add('on'); place(e.clientX,e.clientY); });
    el.addEventListener('mousemove', function(e){ place(e.clientX,e.clientY); });
    el.addEventListener('mouseleave', function(){ tip.classList.remove('on'); });
    el.addEventListener('focus', function(){ var r = el.getBoundingClientRect(); tip.textContent = el.dataset.tip; tip.classList.add('on'); place(r.left+r.width/2, r.top); });
    el.addEventListener('blur', function(){ tip.classList.remove('on'); });
  });
  // Highlight the section under the reading line in the jump bar
  var links = {};
  document.querySelectorAll('.jump a[href^="#"]').forEach(function(a){ links[a.getAttribute('href').slice(1)] = a; });
  var secs = Array.prototype.filter.call(document.querySelectorAll('section[id]'), function(s){ return links[s.id]; });
  if ('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (!e.isIntersecting) return;
        Object.keys(links).forEach(function(k){ links[k].classList.remove('is-selected'); links[k].removeAttribute('aria-current'); });
        links[e.target.id].classList.add('is-selected'); links[e.target.id].setAttribute('aria-current','location');
      });
    }, {rootMargin:'-30% 0px -60% 0px'});
    secs.forEach(function(s){ io.observe(s); });
  }
})();

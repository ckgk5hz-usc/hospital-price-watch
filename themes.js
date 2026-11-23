(function(){
  // chart slideshows: arrows move one card, the counter follows scrolling, arrow keys work when the row has focus
  [].forEach.call(document.querySelectorAll('.subsec'), function(sec){
    var car = sec.querySelector('.car'), prev = sec.querySelector('.car-prev'), next = sec.querySelector('.car-next'), n = sec.querySelector('.car-n');
    if (!car) return;
    var cards = [].slice.call(car.children);
    function step(){ return cards.length > 1 ? cards[1].offsetLeft - cards[0].offsetLeft : car.clientWidth; }
    function at(){ return Math.round(car.scrollLeft / step()); }
    function update(){
      if (!n) return;
      var i = at(), shown = Math.max(1, Math.round(car.clientWidth / step())), last = Math.min(cards.length, i + shown);
      n.textContent = (shown > 1 && last > i + 1 ? (i + 1) + '–' + last : (i + 1)) + ' of ' + cards.length;
      prev.disabled = i <= 0; next.disabled = car.scrollLeft + car.clientWidth >= car.scrollWidth - 4;
    }
    function go(d){ car.scrollBy({left: d * step(), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}); }
    if (prev) { prev.addEventListener('click', function(){ go(-1); }); next.addEventListener('click', function(){ go(1); }); }
    car.addEventListener('keydown', function(e){ if (e.target !== car) return; if (e.key === 'ArrowRight') { e.preventDefault(); go(1); } if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); } });
    var t; car.addEventListener('scroll', function(){ clearTimeout(t); t = setTimeout(update, 60); });
    window.addEventListener('resize', update); update();
  });
  // sub-topic tabs: highlight the section in view
  var links = [].slice.call(document.querySelectorAll('.subtabs a'));
  if (!links.length || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting) links.forEach(function(a){ a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id); }); }); }, {rootMargin: '-35% 0px -55% 0px'});
  links.forEach(function(a){ var s = document.querySelector(a.getAttribute('href')); if (s) io.observe(s); });
})();

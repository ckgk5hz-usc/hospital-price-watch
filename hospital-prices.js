/* Hospital price lookup: search, county filter and column sorting on the table already in the page. */
(function () {
  'use strict';
  var t = document.getElementById('hp-t'), q = document.getElementById('hp-q'), c = document.getElementById('hp-c'), n = document.getElementById('hp-n');
  if (!t) return;
  var body = t.tBodies[0], rows = Array.prototype.slice.call(body.rows), total = rows.length, sortCol = 0, dir = 1;
  function apply() {
    var s = q.value.trim().toLowerCase(), co = c.value, shown = 0;
    rows.forEach(function (r) { var on = (!s || r.dataset.name.indexOf(s) >= 0) && (!co || r.dataset.county === co); r.hidden = !on; if (on) shown++; });
    n.textContent = shown === total ? total + ' hospitals' : shown ? shown + ' of ' + total + ' hospitals' : 'No hospital matches. Check the spelling, or clear the county filter. Kaiser hospitals are not in this file.';
  }
  q.addEventListener('input', apply);
  c.addEventListener('change', apply);
  Array.prototype.forEach.call(t.querySelectorAll('[data-sort]'), function (b) {
    b.addEventListener('click', function () {
      var i = +b.dataset.sort;
      dir = sortCol === i ? -dir : -1; sortCol = i;
      Array.prototype.forEach.call(t.querySelectorAll('th[aria-sort]'), function (h) { h.removeAttribute('aria-sort'); });
      b.parentNode.setAttribute('aria-sort', dir > 0 ? 'ascending' : 'descending');
      rows.sort(function (x, y) {
        var a = parseFloat(x.cells[i].dataset.v), d = parseFloat(y.cells[i].dataset.v);
        if (isNaN(a)) return isNaN(d) ? 0 : 1;   /* n/a stays last whichever way the column is sorted */
        if (isNaN(d)) return -1;
        return (a - d) * dir;
      });
      rows.forEach(function (r) { body.appendChild(r); });
    });
  });
  apply();
})();

(function(){
  var NS='http://www.w3.org/2000/svg', box=document.getElementById('map');
  function el(p,t,a){ var e=document.createElementNS(NS,t); for (var k in a) e.setAttribute(k,a[k]); p.appendChild(e); return e; }
  function lerp(a,b,t){ var A=[1,3,5].map(function(i){return parseInt(a.substr(i,2),16);}), B=[1,3,5].map(function(i){return parseInt(b.substr(i,2),16);}); return 'rgb('+A.map(function(v,i){return Math.round(v+(B[i]-v)*t);}).join(',')+')'; }
  function color(v){ if (v==null) return '#9fa6b2'; var t=Math.max(-1,Math.min(1,v/0.12)), m=Math.abs(t); return t<0 ? lerp('#c9ccd3','#eb6834',Math.min(1,m*1.1)) : lerp('#c9ccd3','#2a78d6',m); }
  function rings(g){ return g.type==='Polygon' ? g.coordinates : g.type==='MultiPolygon' ? g.coordinates.reduce(function(a,p){return a.concat(p);},[]) : []; }
  Promise.all([fetch('data/hospitals_map.json').then(function(r){return r.json();}), fetch('data/ca_counties.geojson').then(function(r){return r.json();})]).then(function(res){
    var hs=res[0].hospitals.filter(function(h){ return h.lat!=null && h.is_general_acute!==false; }), geo=res[1];
    var b={x0:999,x1:-999,y0:999,y1:-999};
    geo.features.forEach(function(f){ rings(f.geometry).forEach(function(r){ r.forEach(function(p){ b.x0=Math.min(b.x0,p[0]); b.x1=Math.max(b.x1,p[0]); b.y0=Math.min(b.y0,p[1]); b.y1=Math.max(b.y1,p[1]); }); }); });
    var k=Math.cos(37.5*Math.PI/180), pad=8, H=640, s=(H-2*pad)/(b.y1-b.y0), W=Math.ceil((b.x1-b.x0)*k*s+2*pad);
    function px(x){ return pad+(x-b.x0)*k*s; } function py(y){ return pad+(b.y1-y)*s; }
    var svg=document.createElementNS(NS,'svg'); svg.setAttribute('viewBox','0 0 '+W+' '+H); svg.setAttribute('class','chart'); svg.setAttribute('aria-hidden','true');
    geo.features.forEach(function(f){ el(svg,'path',{d:rings(f.geometry).map(function(r){ return 'M'+r.map(function(p){ return px(p[0]).toFixed(1)+','+py(p[1]).toFixed(1); }).join('L')+'Z'; }).join(''),fill:'#fff',stroke:'#d3d8e0','stroke-width':.7}); });
    hs.slice().sort(function(a,b2){ return (b2.licensed_beds||0)-(a.licensed_beds||0); }).forEach(function(h){
      var v=h.operating_margin, r=Math.max(3.5,Math.min(11,2.5+Math.sqrt(h.licensed_beds||40)/3.4));
      var c=el(svg,'circle',{cx:px(h.lon).toFixed(1),cy:py(h.lat).toFixed(1),r:r,fill:color(v),stroke:'#fff','stroke-width':1.3,'fill-opacity':.9,'class':'tip','data-tip':h.name+'\n'+(h.city||'')+', '+(h.county||'')+' County\nOperating margin FY2023: '+(v==null?'n/a':(v*100).toFixed(1)+'%')});
      c.style.cursor='crosshair';
    });
    box.innerHTML=''; box.appendChild(svg);
  }).catch(function(){ box.innerHTML='<div class="map-loading">The map could not load. Open the data explorer instead.</div>'; });
})();

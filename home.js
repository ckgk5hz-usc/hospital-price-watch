(function(){
  var NS='http://www.w3.org/2000/svg', box=document.getElementById('map');
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function el(p,t,a){ var e=document.createElementNS(NS,t); for (var k in a) e.setAttribute(k,a[k]); p.appendChild(e); return e; }
  function hex(h){ return [1,3,5].map(function(i){ return parseInt(h.substr(i,2),16); }); }
  function mix(a,b,t){ return 'rgb('+[0,1,2].map(function(i){ return Math.round(a[i]+(b[i]-a[i])*t); }).join(',')+')'; }
  function rings(g){ return g.type==='Polygon' ? g.coordinates : g.type==='MultiPolygon' ? g.coordinates.reduce(function(a,p){return a.concat(p);},[]) : []; }
  function q(sorted,p){ var i=(sorted.length-1)*p, lo=Math.floor(i), hi=Math.ceil(i); return sorted[lo]+(sorted[hi]-sorted[lo])*(i-lo); }
  var GRAY=hex('#c9ccd3'), ORANGE=hex('#eb6834'), BLUE=hex('#2a78d6'), PALE=hex('#bcd4f3'), DEEP=hex('#0d366b');
  function pct(v,d){ return (v*100).toFixed(d==null?1:d)+'%'; }
  // four scenes; each is a measure that has a value for every hospital and fiscal year
  var SCENES = [
    {id:'margin', tab:'Margins', key:'operating_margin', div:true, lim:.12, fmt:function(v){ return pct(v); }, ends:['Lost money','Surplus'], title:'Operating margin',
     stat:function(S){ return pct(S.share(function(v){return v<0;}),0)+' of hospitals lost money on operations in FY'+S.fy+'.'; }},
    {id:'free', tab:'Free care', key:'uncompensated_care_rate', fmt:function(v){ return pct(v); }, title:'Unpaid and charity care, share of charges',
     stat:function(S){ return 'The typical hospital wrote off '+pct(S.median,1)+' of its charges as unpaid or charity care in FY'+S.fy+'.'; }},
    {id:'medical', tab:'Medi-Cal', key:'medical_discharge_share', fmt:function(v){ return pct(v,0); }, title:'Medi-Cal share of discharges',
     stat:function(S){ return 'Medi-Cal paid for '+pct(S.median,0)+' of the typical hospital’s inpatient stays in FY'+S.fy+'.'; }},
    {id:'births', tab:'Maternity', key:'natural_births', fmt:function(v){ return Math.round(v).toLocaleString(); }, title:'Natural births per year', maternity:true,
     stat:function(S){ return S.lost+' hospitals with a persistent drop in reported births to zero by FY'+S.fy+'. A unit lost, not a hospital.'; }}
  ];
  Promise.all([fetch('data/hospitals_map.json').then(function(r){return r.json();}), fetch('data/ca_counties.geojson').then(function(r){return r.json();})]).then(function(res){
    var data=res[0], Y0=data.years[0], hs=data.hospitals.filter(function(h){ return h.lat!=null && h.is_general_acute!==false; }), geo=res[1], lost=data.maternity_losses||[];
    var b={x0:999,x1:-999,y0:999,y1:-999};
    geo.features.forEach(function(f){ rings(f.geometry).forEach(function(r){ r.forEach(function(p){ b.x0=Math.min(b.x0,p[0]); b.x1=Math.max(b.x1,p[0]); b.y0=Math.min(b.y0,p[1]); b.y1=Math.max(b.y1,p[1]); }); }); });
    var k=Math.cos(37.5*Math.PI/180), pad=8, H=640, s=(H-2*pad)/(b.y1-b.y0), W=Math.ceil((b.x1-b.x0)*k*s+2*pad);
    function px(x){ return pad+(x-b.x0)*k*s; } function py(y){ return pad+(b.y1-y)*s; }
    var svg=document.createElementNS(NS,'svg'); svg.setAttribute('viewBox','0 0 '+W+' '+H); svg.setAttribute('class','chart'); svg.setAttribute('aria-hidden','true');
    geo.features.forEach(function(f){ el(svg,'path',{d:rings(f.geometry).map(function(r){ return 'M'+r.map(function(p){ return px(p[0]).toFixed(1)+','+py(p[1]).toFixed(1); }).join('L')+'Z'; }).join(''),fill:'#fff',stroke:'#d3d8e0','stroke-width':.7}); });
    var dots = hs.slice().sort(function(a,c){ return (c.licensed_beds||0)-(a.licensed_beds||0); }).map(function(h){
      var r=Math.max(3.5,Math.min(11,2.5+Math.sqrt(h.licensed_beds||40)/3.4));
      var c=el(svg,'circle',{cx:px(h.lon).toFixed(1),cy:py(h.lat).toFixed(1),r:r,fill:'#c9ccd3',stroke:'#fff','stroke-width':1.3,'fill-opacity':.92,'class':'tip'});
      c.style.cursor='crosshair'; return {h:h,c:c};
    });
    var marks = lost.map(function(m){
      var cx=px(m.lon), cy=py(m.lat), d=9;
      var t=el(svg,'path',{d:'M'+cx.toFixed(1)+','+(cy-d).toFixed(1)+' L'+(cx+d).toFixed(1)+','+(cy+d*.8).toFixed(1)+' L'+(cx-d).toFixed(1)+','+(cy+d*.8).toFixed(1)+' Z',fill:'#7b3fa0',stroke:'#fff','stroke-width':1.4,opacity:0,'class':'tip'});
      return {m:m,t:t};
    });
    box.innerHTML=''; box.appendChild(svg);
    // value of a hospital at a fractional year: glide between the two neighboring fiscal years
    function val(h,key,t){
      var arr=h[key]; if(!arr) return null; var i=Math.floor(t-Y0), f=t-Y0-i, a=arr[i], c=arr[Math.min(i+1,arr.length-1)];
      if (a==null && c==null) return null; if (a==null) return c; if (c==null||f===0) return a; return a+(c-a)*f;
    }
    // fixed color range for each measure across all years, so colors can fade without the scale shifting
    SCENES.forEach(function(S){
      if (S.div) return;
      var pool=[]; hs.forEach(function(h){ (h[S.key]||[]).forEach(function(v){ if(v!=null) pool.push(v); }); }); pool.sort(function(a,c){return a-c;});
      S.lo=q(pool,.05); S.hi=q(pool,.95);
    });
    function color(S,v){
      if (v==null) return '#c9ccd3';
      if (S.div){ var t=Math.max(-1,Math.min(1,v/S.lim)), m=Math.abs(t); return t<0 ? mix(GRAY,ORANGE,Math.min(1,m*1.1)) : mix(GRAY,BLUE,m); }
      return mix(PALE,DEEP,Math.max(0,Math.min(1,(v-S.lo)/(S.hi-S.lo||1))));
    }
    var tabs=document.getElementById('map-tabs'), stat=document.getElementById('map-stat'), slider=document.getElementById('map-year'), fyOut=document.getElementById('map-fy'), play=document.getElementById('map-play'), keyEl=document.getElementById('map-key'), note=document.getElementById('map-note');
    var cur=0, curS=SCENES[0], year=2023, playing=!reduced, blend=1, prevCols=null, tipYear=null;
    SCENES.forEach(function(S,i){ var bt=document.createElement('button'); bt.type='button'; bt.textContent=S.tab; bt.addEventListener('click',function(){ playing=false; syncPlay(); go(i,true); }); tabs.appendChild(bt); S.btn=bt; });
    function syncPlay(){ play.textContent=playing?'Pause':'Play'; play.setAttribute('aria-label',playing?'Pause the map animation':'Play the map animation'); }
    function legend(S){
      var g=S.div ? 'linear-gradient(90deg,#eb6834,#c9ccd3,#2a78d6)' : 'linear-gradient(90deg,#bcd4f3,#0d366b)';
      var lo=S.div?S.ends[0]:S.fmt(S.lo), hi=S.div?S.ends[1]:S.fmt(S.hi);
      keyEl.innerHTML='<b style="font-weight:600">'+S.title+'</b>&ensp;'+lo+'<span class="grad" style="background:'+g+'"></span>'+hi+(S.maternity?'&emsp;<span class="tri"></span>Maternity unit lost':'');
      note.textContent = S.maternity ? 'Natural (non-cesarean) births only. Purple triangles are inferred from filings (births reported as zero and staying zero), not announcements. Dots sit at city centers.' : 'Dots sit at city centers, not street addresses. FY2024 is preliminary.';
    }
    function go(i,instant){ cur=i; curS=SCENES[i]; SCENES.forEach(function(S,j){ S.btn.setAttribute('aria-pressed',j===i?'true':'false'); }); legend(curS); blend = (instant||reduced) ? 1 : 0; if (instant && !reduced) blend=0; prevCols = dots.map(function(d){ return d.c.getAttribute('fill'); }); if (reduced) { prevCols=null; paint(); } }
    function paint(){
      var S=curS, fy=Math.round(year), medians=[], neg=0, n=0;
      dots.forEach(function(d,i){
        var v=val(d.h,S.key,year), tgt=color(S,v);
        var from=prevCols&&blend<1?prevCols[i]:null;
        d.c.setAttribute('fill', from && from.indexOf('rgb')===0 ? mixStr(from,tgt,ease(blend)) : tgt);
        var vr=val(d.h,S.key,fy); if (vr!=null){ medians.push(vr); n++; if (vr<0) neg++; }
        if (tipYear!==fy+S.id) d.c.setAttribute('data-tip', d.h.name+'\n'+(d.h.city||'')+', '+(d.h.county||'')+' County\n'+S.title+', FY'+fy+': '+(vr==null?'n/a':S.fmt(vr)));
      });
      tipYear=fy+S.id;
      medians.sort(function(a,c){return a-c;}); var med=medians.length?q(medians,.5):0, nLost=0;
      marks.forEach(function(m){
        var o = S.maternity ? Math.max(0,Math.min(1, year-(m.m.first_year_zero-1))) : 0;
        m.t.setAttribute('opacity', (o*.95).toFixed(2));
        if (+m.t.getAttribute('opacity')>.5) nLost++;
        m.t.setAttribute('data-tip', m.m.name+'\nBirths reported as zero from FY'+m.m.first_year_zero+(m.m.preliminary?' (preliminary)':'')+'\nFY'+m.m.last_year_with_births+': '+m.m.births_that_year.toLocaleString()+' natural births');
      });
      stat.textContent = S.stat({fy:fy, median:med, lost:nLost, share:function(f){ var c=0; medians.forEach(function(v){ if(f(v)) c++; }); return medians.length? c/medians.length : 0; }});
      fyOut.textContent='FY'+fy; if (document.activeElement!==slider) slider.value=year;
    }
    function ease(t){ return t<.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2; }
    function mixStr(a,c,t){ var A=/(\d+),(\d+),(\d+)/.exec(a), C=/(\d+),(\d+),(\d+)/.exec(c); if(!A||!C) return c; return 'rgb('+[1,2,3].map(function(i){ return Math.round(+A[i]+(+C[i]-A[i])*t); }).join(',')+')'; }
    // clock: each scene glides from FY2012 to FY2024, holds, then fades into the next measure
    var last=null, hold=0, SPAN=11000, HOLD=2600;
    function tick(ts){
      if (last==null) last=ts; var dt=Math.min(100,ts-last); last=ts;
      if (blend<1){ blend=Math.min(1,blend+dt/700); if (blend>=1) prevCols=null; }
      if (playing){
        if (hold>0){ hold-=dt; if (hold<=0){ go((cur+1)%SCENES.length); year=2012; } }
        else { year+=dt/SPAN*12; if (year>=2024){ year=2024; hold=HOLD; } }
      }
      paint(); requestAnimationFrame(tick);
    }
    slider.addEventListener('input',function(){ playing=false; syncPlay(); year=+slider.value; hold=0; paint(); });
    play.addEventListener('click',function(){ playing=!playing; syncPlay(); if (playing && year>=2024){ year=2012; } last=null; });
    go(0,true); blend=1; prevCols=null; syncPlay();
    if (reduced){ year=2023; paint(); } else { year=2012; requestAnimationFrame(tick); }
    slider.value=year;
  }).catch(function(){ box.innerHTML='<div class="map-loading">The map could not load. Open the data explorer instead.</div>'; });
})();

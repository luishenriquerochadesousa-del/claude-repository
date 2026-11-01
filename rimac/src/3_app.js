/* ---------------- section activation ---------------- */
function activate(id,scroll){
  document.querySelectorAll('#nav a').forEach(x=>x.classList.toggle('on',x.dataset.s===id));
  document.querySelectorAll('main > section').forEach(s=>s.classList.toggle('on',s.id===id));
  if(scroll!==false) window.scrollTo(0,0);
}
const nav=document.getElementById('nav');
const side=document.getElementById('side');
nav.addEventListener('click',e=>{
  const a=e.target.closest('a[data-s]'); if(!a)return;
  activate(a.dataset.s);
  side.classList.remove('navopen');
});
document.getElementById('navToggle').addEventListener('click',()=>side.classList.toggle('navopen'));

/* ---------------- countdown (13:00 local time, Mon 2 Nov 2026) ---------------- */
(function(){
  const target=new Date(2026,10,2,13,0,0);
  function tick(){
    const el=document.getElementById('cd');
    const d=target-new Date();
    if(d<=-3600000){el.innerHTML='<span style="color:var(--good);font-weight:700">Interview done</span>';return}
    if(d<=0){el.innerHTML='<span style="color:var(--warn);font-weight:700">Now</span>';return}
    const h=Math.floor(d/3600000), m=Math.floor(d%3600000/60000);
    el.innerHTML='<span style="color:var(--acc);font-weight:700">'+h+'h '+m+'m to 13:00</span> <span style="color:var(--warn)">(confirm time, &sect;0)</span>';
  }
  tick(); setInterval(tick,30000);
})();

/* ---------------- question bank ---------------- */
(function(){
  const f=document.getElementById('filt'), m=document.getElementById('mockScope');
  Object.keys(TIER).forEach(k=>{
    if(!QS.some(q=>String(q.t)===k))return;
    f.insertAdjacentHTML('beforeend','<option value="'+k+'">'+TIER[k][1]+'</option>');
    m.insertAdjacentHTML('beforeend','<option value="'+k+'">'+TIER[k][1]+' only</option>');
  });
  m.insertAdjacentHTML('beforeend','<option value="drills">Hand-calc drills only</option>');
})();
function setTier(v){document.getElementById('filt').value=v;renderBank();renderPills();}
function renderPills(){
  const host=document.getElementById('tierPills');
  const cur=document.getElementById('filt').value||'all';
  const counts={}; QS.forEach(o=>{counts[o.t]=(counts[o.t]||0)+1});
  let html='<span class="tpill all'+(cur==='all'?' on':'')+'" data-t="all">All <span class="tn">'+QS.length+'</span></span>';
  Object.keys(TIER).forEach(k=>{
    if(!counts[k])return;
    html+='<span class="tpill '+TIER[k][0]+(String(cur)===k?' on':'')+'" data-t="'+k+'">'+TIER[k][1]+' <span class="tn">'+counts[k]+'</span></span>';
  });
  host.innerHTML=html;
  host.querySelectorAll('.tpill').forEach(el=>{el.onclick=()=>setTier(el.dataset.t)});
}
function renderBank(){
  const f=document.getElementById('filt').value;
  const list=document.getElementById('bankList');
  list.innerHTML='';
  QS.forEach((q,i)=>{
    if(f!=='all'&&String(q.t)!==f)return;
    const d=document.createElement('div');
    d.className='q'; d.dataset.qi=i;
    d.innerHTML='<div class="qh"><span class="qn">'+String(i+1).padStart(2,'0')+'</span><span class="qt">'+q.q+'<br><span class="pill '+TIER[q.t][0]+'" style="margin-top:6px;display:inline-block">'+TIER[q.t][1]+'</span><span class="qw">likely: '+q.w+'</span></span><span class="chev">&#9660;</span></div><div class="qb">'+q.a+'</div>';
    d.querySelector('.qh').onclick=()=>d.classList.toggle('open');
    list.appendChild(d);
  });
}
function allQ(o){document.querySelectorAll('#bankList .q').forEach(q=>q.classList.toggle('open',o))}
renderBank(); renderPills();

/* ---------------- drills ---------------- */
(function(){
  const l=document.getElementById('drillList');
  DRILLS.forEach((d,i)=>{
    const e=document.createElement('div');
    e.className='drill'; e.dataset.di=i;
    e.innerHTML='<h5>'+d.h+'</h5>'+d.b;
    l.appendChild(e);
  });
})();

/* ---------------- mock mode ---------------- */
let cur=null, t0=null, tint=null;
const KEY='rimac_prep_v1';
function prog(){try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return {}}}
function save(p){try{localStorage.setItem(KEY,JSON.stringify(p))}catch(e){}}
function pool(){
  const s=document.getElementById('mockScope').value;
  if(s==='drills') return DRILLS.map((d,i)=>({id:'d'+i,q:d.h.replace(/^\d+ · /,'')+': work it out loud.',a:d.b,m:'Hand-calc drill'}));
  return QS.map((q,i)=>({id:'q'+i,t:q.t,q:q.q,a:q.a,m:TIER[q.t][1]+' · likely: '+q.w+' · question '+(i+1)}))
           .filter(x=>s==='all'||String(x.t)===s);
}
function nextQ(){
  const p=prog(), all=pool(); if(!all.length)return;
  let cand=all.filter(x=>p[x.id]!==1); if(!cand.length)cand=all;
  cur=cand[Math.floor(Math.random()*cand.length)];
  document.getElementById('stageQ').textContent=cur.q;
  document.getElementById('stageMeta').textContent=cur.m;
  const A=document.getElementById('stageA'); A.innerHTML=cur.a; A.classList.remove('on');
  resetTimer(); startTimer(); updProg();
}
function toggleAns(){document.getElementById('stageA').classList.toggle('on')}
function startTimer(){
  clearInterval(tint); t0=Date.now();
  tint=setInterval(()=>{
    const s=Math.floor((Date.now()-t0)/1000), el=document.getElementById('timer');
    el.textContent=Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
    el.className=s>150?'over':(s>90?'hot':'');
  },500);
}
function resetTimer(){clearInterval(tint);const el=document.getElementById('timer');el.textContent='0:00';el.className=''}
function mark(v){if(!cur)return;const p=prog();p[cur.id]=v;save(p);nextQ()}
function resetProg(){save({});updProg()}
function updProg(){
  const p=prog(), all=pool(), done=all.filter(x=>p[x.id]===1).length;
  document.getElementById('prog').textContent=done+' / '+all.length+' marked solid in this set';
  document.getElementById('barI').style.width=(all.length?done/all.length*100:0)+'%';
}
document.getElementById('mockScope').onchange=updProg;
updProg();

/* ---------------- day-of checklist ---------------- */
(function(){
  const K='rimac_chk_v1';
  let st={}; try{st=JSON.parse(localStorage.getItem(K))||{}}catch(e){}
  document.querySelectorAll('#dayChk input').forEach(cb=>{
    const li=cb.closest('li');
    cb.checked=!!st[cb.dataset.k]; li.classList.toggle('done',cb.checked);
    cb.onchange=()=>{st[cb.dataset.k]=cb.checked;li.classList.toggle('done',cb.checked);try{localStorage.setItem(K,JSON.stringify(st))}catch(e){}};
  });
})();

/* ---------------- global search ---------------- */
(function(){
  const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&nbsp;/gi,' ').replace(/&mdash;|&ndash;/gi,'-')
    .replace(/&amp;/gi,'&').replace(/&lt;/gi,'<').replace(/&gt;/gi,'>').replace(/&[a-z]+;/gi,' ').replace(/\s+/g,' ').trim();
  const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const escHtml=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const SECNAME={}; document.querySelectorAll('#nav a').forEach(a=>{SECNAME[a.dataset.s]=strip(a.textContent)});
  const IDX=[];
  QS.forEach((o,i)=>IDX.push({kind:'q',sec:'bank',qi:i,tier:TIER[o.t][1],pill:TIER[o.t][0],title:strip(o.q),body:strip(o.a)}));
  DRILLS.forEach((d,i)=>IDX.push({kind:'d',sec:'drill',di:i,tier:'Drill',pill:'pT',title:strip(d.h),body:strip(d.b)}));
  const HEAD=/^H[2-5]$/;
  document.querySelectorAll('main > section').forEach(sec=>{
    sec.querySelectorAll('h2,h3,h4,h5').forEach(el=>{
      if(el.closest('#drillList')||el.closest('#bankList'))return;
      const t=strip(el.textContent); if(t.length<3)return;
      let body='', n=el.nextElementSibling, budget=12;
      while(n&&!HEAD.test(n.tagName)&&budget-->0){body+=' '+strip(n.textContent);n=n.nextElementSibling}
      IDX.push({kind:'s',sec:sec.id,el:el,tier:'Section',pill:'pT',title:t,body:body.trim().slice(0,1500)});
    });
  });
  function score(it,terms){
    const T=it.title.toLowerCase(), B=it.body.toLowerCase(); let s=0;
    for(const t of terms){
      const inT=T.indexOf(t)!==-1, inB=B.indexOf(t)!==-1;
      if(!inT&&!inB)return 0;
      if(inT) s+= T.indexOf(t)===0?14:(new RegExp('\\b'+esc(t)).test(T)?9:5);
      else s+= new RegExp('\\b'+esc(t)).test(B)?2:1;
    }
    return s+(it.kind==='q'?2:it.kind==='d'?1.5:0);
  }
  function hl(text,terms){let out=escHtml(text);terms.forEach(t=>{out=out.replace(new RegExp('('+esc(escHtml(t))+')','ig'),'<mark>$1</mark>')});return out}
  function snippet(it,terms){
    if(!it.body)return '';
    const low=it.body.toLowerCase(); let at=-1;
    for(const t of terms){const i=low.indexOf(t);if(i!==-1&&(at===-1||i<at))at=i}
    if(at===-1)at=0;
    const from=Math.max(0,at-70); let frag=it.body.slice(from,from+200);
    if(from>0)frag='…'+frag; if(from+200<it.body.length)frag+='…';
    return hl(frag,terms);
  }
  const wrap=document.getElementById('searchWrap'), input=document.getElementById('searchIn'),
        panel=document.getElementById('searchRes'), clearBtn=document.getElementById('searchClear');
  let hits=[], sel=-1;
  function close(){panel.classList.remove('on');sel=-1}
  function run(){
    const raw=input.value.trim(); wrap.classList.toggle('has',raw.length>0);
    if(raw.length<2){close();return}
    const terms=raw.toLowerCase().split(/\s+/).filter(Boolean);
    hits=IDX.map(it=>({it,s:score(it,terms)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s).slice(0,25).map(x=>x.it);
    sel=hits.length?0:-1; draw(terms);
  }
  function draw(terms){
    if(!hits.length){panel.innerHTML='<div class="rEmpty">No match for <strong>'+escHtml(input.value)+'</strong>. Try one keyword: <em>sag</em>, <em>Riks</em>, <em>OptiStruct</em>, <em>Volvo</em>.</div>';panel.classList.add('on');return}
    let html='<div class="rcount">'+hits.length+' result'+(hits.length>1?'s':'')+' · ↑↓ move · ↵ open · esc close</div>';
    hits.forEach((it,i)=>{
      const where=it.kind==='q'?'Question bank → '+it.tier:it.kind==='d'?'Hand-calc drills':(SECNAME[it.sec]||it.sec);
      const sn=snippet(it,terms);
      html+='<div class="rItem'+(i===sel?' sel':'')+'" data-i="'+i+'"><span class="pill '+it.pill+'">'+it.tier+'</span><div class="rmain"><div class="rt">'+hl(it.title,terms)+'</div>'+(sn?'<div class="rs">'+sn+'</div>':'')+'<div class="rwhere">'+escHtml(where)+'</div></div></div>';
    });
    panel.innerHTML=html; panel.classList.add('on');
    panel.querySelectorAll('.rItem').forEach(el=>{el.onmousedown=e=>{e.preventDefault();go(hits[+el.dataset.i])}});
  }
  function flash(el){
    if(!el)return; el.classList.remove('hitflash'); void el.offsetWidth; el.classList.add('hitflash');
    setTimeout(()=>{try{el.scrollIntoView({behavior:'smooth',block:'center'})}catch(err){}},60);
  }
  function go(it){
    if(!it)return; activate(it.sec,false); close(); input.blur();
    if(it.kind==='q'){
      const f=document.getElementById('filt'); if(f.value!=='all'){f.value='all';renderBank();renderPills()}
      const el=document.querySelector('#bankList .q[data-qi="'+it.qi+'"]'); if(el){el.classList.add('open');flash(el)}
    } else if(it.kind==='d'){flash(document.querySelector('#drillList .drill[data-di="'+it.di+'"]'))}
    else flash(it.el);
  }
  input.addEventListener('input',run);
  input.addEventListener('focus',()=>{if(input.value.trim().length>=2)run()});
  input.addEventListener('blur',()=>setTimeout(close,120));
  clearBtn.onclick=()=>{input.value='';wrap.classList.remove('has');close();input.focus()};
  input.addEventListener('keydown',e=>{
    if(e.key==='Escape'){close();input.blur();return}
    if(!panel.classList.contains('on')||!hits.length)return;
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){
      e.preventDefault(); sel=(sel+(e.key==='ArrowDown'?1:-1)+hits.length)%hits.length;
      panel.querySelectorAll('.rItem').forEach((el,i)=>el.classList.toggle('sel',i===sel));
      const s=panel.querySelector('.rItem.sel'); if(s){try{s.scrollIntoView({block:'nearest'})}catch(err){}}
    } else if(e.key==='Enter'){e.preventDefault();go(hits[sel])}
  });
  document.addEventListener('keydown',e=>{
    const tag=(document.activeElement&&document.activeElement.tagName)||'';
    const typing=tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT';
    if((e.key==='k'||e.key==='K')&&(e.metaKey||e.ctrlKey)){e.preventDefault();input.focus();input.select()}
    else if(e.key==='/'&&!typing){e.preventDefault();input.focus();input.select()}
  });
})();

/* ---------------- theme toggle ---------------- */
(function(){
  const btn=document.getElementById('themeToggle'), root=document.documentElement;
  function paint(){const light=root.getAttribute('data-theme')==='light';btn.innerHTML=(light?'◐ Dark':'◑ Light');}
  btn.addEventListener('click',()=>{
    const light=root.getAttribute('data-theme')==='light';
    if(light)root.removeAttribute('data-theme');else root.setAttribute('data-theme','light');
    try{localStorage.setItem('prep_theme',light?'dark':'light')}catch(e){}
    paint();
  });
  paint();
})();

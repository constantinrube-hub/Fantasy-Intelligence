/* FIE UI v10 player reader + compare tray (R2 · WP2.2) — UI contract §4.5.
 *
 * Any player name rendered with FIEV10Kit.playerLink opens ONE reader (side panel) — the same in
 * Lineup, Bench, Waivers, review and My players. It shows the player in the league you are looking at:
 * this week (league-scored projection, status, game, range), the next weeks of the waiver horizon, who
 * rosters him, his value to YOUR lineup (on your roster: cost if he can't play; elsewhere: the legal
 * lineup gain if you added him and the drop — FIEWaivers in exact mode), your other leagues, and the
 * shared Expand/Advanced layers. "Pin" adds him to the compare tray (max 3, this browser session);
 * "Compare" puts the pinned players side by side in the same league's scoring.
 */
(function(){
'use strict';
const VERSION='10.5.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
const PINS='fieV10Pins',MAX=3;
let token=0;
function pins(){try{const x=JSON.parse(sessionStorage.getItem(PINS)||'[]');return Array.isArray(x)?x.slice(0,MAX):[];}catch{return [];}}
function setPins(x){try{sessionStorage.setItem(PINS,JSON.stringify(x.slice(0,MAX)));}catch{}renderTray();}
function currentLeague(){const h=(location.hash||'').match(/^#\/league\/([^/?]+)/);return h?decodeURIComponent(h[1]):null;}
function panel(){let el=document.getElementById('fieV10Reader');if(!el){el=document.createElement('aside');el.id='fieV10Reader';el.setAttribute('role','dialog');el.setAttribute('aria-label','Player');el.hidden=true;(document.getElementById('fieV10')||document.body).appendChild(el);}return el;}
function close(){const el=document.getElementById('fieV10Reader');if(el){el.hidden=true;el.innerHTML='';}token++;}
async function leagueEntry(lid){const list=await D().leagues();return list.find(x=>String(x.id)===String(lid))||list[0]||null;}
/** Values of one player over the waiver horizon in this league's scoring. */
async function horizonValues(wm,pid){
  const n=Number(window.FIE_UI_POLICY?.waivers?.horizon_weeks)||3,[hz,sched,cat]=await Promise.all([D().horizon(wm.key.season,wm.key.week,n),D().schedule(),D().catalog()]);
  return hz.map((h,i)=>{if(i===0)return{week:h.week,value:wm.player(pid)?.status?.unavailable?0:wm.player(pid)?.active?.value??null,published:h.projRows.size>0};
    const v=window.FIEWaivers.futureValuer({projRows:h.projRows,scoring:wm.league.scoring,schedule:sched,week:h.week,season:wm.key.season,now:Date.now(),catalog:cat,longTermOut:()=>false})(pid);return{week:h.week,value:h.projRows.size?v.value:null,published:h.projRows.size>0};});
}
async function impact(entry,wm,pid){
  const own=wm.ownerOf(pid);
  if(own?.me){const c=wm.lineupContext(pid);return{kind:'mine',own,ctx:c};}
  try{const r=(await D().waivers(entry,{pids:[pid]})).result,row=[...r.rows,...r.watch].find(x=>x.pid===String(pid));return{kind:own?'other':'fa',own,row,weeks:r.weeks};}catch{return{kind:own?'other':'fa',own,row:null};}
}
function impactText(im){
  const k=K();if(!im)return '–';
  if(im.kind==='mine'){const c=im.ctx;return c?(c.role==='starter'?`Your roster, in your best lineup: losing him costs ${k.pts(-c.delta)} pts this week${c.nextBest?` (next best ${k.esc(c.nextBest)})`:''}.`:`Your roster, not in your best lineup: starting him ${c.delta>=0?'adds':'costs'} ${k.pts(Math.abs(c.delta))} pts this week.`):'On your roster.';}
  const r=im.row,who=im.kind==='other'?`Rostered by ${k.esc(im.own.name)}${im.own.where!=='roster'?` (${k.esc(im.own.where)})`:''}. If you acquired him: `:'Free agent. If you add him: ';
  if(!r)return who+'no projection.';
  return who+`${r.gainWeek>0?k.signed(r.gainWeek)+' this week, ':''}${k.signed(r.gainHorizon)} over W${im.weeks[0]}–W${im.weeks[im.weeks.length-1]}${r.drop?`, dropping ${k.esc(r.drop.name)}`:r.freeSpot?' (free roster spot)':''}${r.action?` · ${k.esc(r.action)} (${k.esc(r.reason)})`:''}.`;
}
async function open(pid,lid){
  const my=++token,k=K(),el=panel();el.hidden=false;el.innerHTML=`<div class="v10-rd-head"><b>Loading…</b><button class="v10-btn v10-ghost" data-v10-close>✕</button></div>`;
  const entry=await leagueEntry(lid||currentLeague());if(!entry){el.innerHTML=k.empty('No league loaded.');return;}
  const wm=await D().model(entry);if(my!==token)return;
  const p=wm.player(pid);if(!p){el.innerHTML=`<div class="v10-rd-head"><b>Unknown player</b><button class="v10-btn v10-ghost" data-v10-close>✕</button></div>`;return;}
  const [hv,im]=await Promise.all([horizonValues(wm,pid),impact(entry,wm,pid)]);if(my!==token)return;
  const mp=window.FIEV10Overview?.last?.()?.rows?window.FIEPortfolioViews.myPlayers(window.FIEV10Overview.last().rows).rows.find(x=>x.pid===String(pid)):null;
  const det=k.playerDetail(p,wm),pinned=pins().some(x=>x.pid===String(pid));
  el.innerHTML=`<div class="v10-rd-head"><div><h2>${k.esc(p.name)}</h2><div class="v10-muted">${k.esc(p.position)} · ${k.esc(p.team||'FA')} ${k.statusChip(p.status)} · ${k.esc(k.gameText(p.game))}</div></div><button class="v10-btn v10-ghost" data-v10-close aria-label="Close">✕</button></div>
    <div class="v10-rd-body"><div class="v10-muted">In ${k.esc(wm.entry.name)} (week ${k.esc(wm.key.week)})</div>
    <table class="v10-mini"><thead><tr>${hv.map(h=>`<th class="v10-num">W${h.week}</th>`).join('')}</tr></thead><tbody><tr>${hv.map(h=>`<td class="v10-num">${h.published?k.pts(h.value):'<span class="v10-muted" title="Sleeper has not published this week yet">not yet</span>'}</td>`).join('')}</tr></tbody></table>
    <p>${impactText(im)}</p>
    ${mp?`<p class="v10-muted">Your leagues: ${mp.leagues.map(l=>`${k.esc(l.leagueName)} (${l.role==='start'?k.esc(l.slot):l.role})`).join(', ')}</p>`:''}
    ${k.expand('<b>Details</b>',det.body,{adv:det.adv,cls:'v10-rd-x',open:true,key:`rd:${pid}`})}
    <div class="v10-row"><button class="v10-btn" data-v10-pin="${k.esc(pid)}" data-v10-pin-league="${k.esc(wm.key.leagueId)}" data-v10-pin-name="${k.esc(p.name)}"${pinned?' disabled':''}>${pinned?'Pinned':'Pin to compare'}</button>${pins().length?'<button class="v10-btn" data-v10-compare>Compare pinned</button>':''}</div></div>`;
}
// R5.7 · P10…P90 curve (one line per player, outcome on the y axis): source position × projection tier until
// player-level spreads exist (policy switch) — the note says which. Inline SVG, theme colours via currentColor/CSS vars.
const CURVE_COLORS=['var(--v-accent)','var(--v-rec)','var(--v-good)'];
function curve(ps){const k=K(),xs=ps.filter(p=>p?.range?.deciles);if(!xs.length)return '';
  const W=520,H=210,L=40,B=26,T=10,R=10,max=Math.max(1,...xs.flatMap(p=>p.range.deciles.q)),ymax=Math.ceil(max/5)*5,X=i=>L+i*(W-L-R)/8,Y=v=>T+(H-T-B)*(1-v/ymax);
  const grid=[0,.25,.5,.75,1].map(f=>{const v=ymax*f;return `<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--v-line)"/><text x="${L-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--v-muted)">${Math.round(v)}</text>`;}).join('');
  const xl=Array.from({length:9},(_,i)=>`<text x="${X(i)}" y="${H-8}" text-anchor="middle" font-size="11" fill="var(--v-muted)">P${(i+1)*10}</text>`).join('');
  const lines=xs.map((p,j)=>`<polyline fill="none" stroke="${CURVE_COLORS[j%3]}" stroke-width="2.5" points="${p.range.deciles.q.map((v,i)=>`${X(i)},${Y(v)}`).join(' ')}"/>${p.range.deciles.q.map((v,i)=>`<circle cx="${X(i)}" cy="${Y(v)}" r="3" fill="${CURVE_COLORS[j%3]}"><title>${k.esc(p.name)} P${(i+1)*10}: ${k.pts(v)}</title></circle>`).join('')}`).join('');
  const legend=xs.map((p,j)=>`<span class="v10-chip" style="border-color:${CURVE_COLORS[j%3]};color:${CURVE_COLORS[j%3]}">${k.esc(p.name)} · P50 ${k.pts(p.range.deciles.q[4])}</span>`).join(' ');
  const src=xs[0].range.deciles.source;
  return `<h3>Outcome range this week</h3><div class="v10-row">${legend}</div><svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="P10 to P90 points per player">${grid}${xl}${lines}</svg>
    <p class="v10-muted v10-small">Points at each percentile (P10 = 1 week in 10 below, P90 = 1 week in 10 above). Shape: ${k.esc(src)}${src==='player'?'':' — measured on 2026 Weeks 1–6 for QB/RB/WR/TE (a low projection has a relatively wider spread); two players of the same position and projection level have the same shape. Player-specific spreads replace this when available.'} K, D/ST and IDP have no curve yet.</p>`;}
// R5.7 · Where the projection comes from: Sleeper's projected stat line × this league's scoring, per stat.
function statTable(ps,wm){const k=K(),xs=ps.filter(p=>p?.stats);if(!xs.length)return '';
  const sc=wm.league.scoring||{},rows=xs.map(p=>new Map((window.FIEScoringCore.breakdown(p.stats,sc,p.position)||[]).filter(r=>Math.abs(r.points)>=0.05).map(r=>[r.key,r]))),keys=[...new Set(rows.flatMap(m=>[...m.keys()]))];
  keys.sort((a,b)=>Math.max(...rows.map(m=>Math.abs(m.get(b)?.points||0)))-Math.max(...rows.map(m=>Math.abs(m.get(a)?.points||0))));
  return `<h3>Projection breakdown <span class="v10-muted">Sleeper stat line × ${k.esc(wm.entry.name)} scoring</span></h3><table class="v10-table v10-cmpstats"><thead><tr><th>Stat (points per unit)</th>${xs.map(p=>`<th class="v10-num">${k.esc(p.name)}</th>`).join('')}</tr></thead><tbody>
    ${keys.map(key=>`<tr><td>${k.esc(key)} <span class="v10-muted">×${k.esc(rows.find(m=>m.get(key))?.get(key)?.weight)}</span></td>${rows.map(m=>{const r=m.get(key);return `<td class="v10-num">${r?`${k.pts(r.points)} <span class="v10-muted v10-small">(${k.esc(Math.round(r.stat*10)/10)})</span>`:'–'}</td>`;}).join('')}</tr>`).join('')}
    <tr><td><b>Total</b></td>${xs.map(p=>`<td class="v10-num"><b>${k.pts(p.active.value)}</b></td>`).join('')}</tr></tbody></table>`;}
async function compare(){
  const my=++token,k=K(),el=panel(),list=pins();el.hidden=false;el.classList.add('v10-rd-wide');
  if(!list.length){el.innerHTML=k.empty('Nothing pinned.');return;}
  el.innerHTML=`<div class="v10-rd-head"><b>Comparing…</b><button class="v10-btn v10-ghost" data-v10-close>✕</button></div>`;
  const entry=await leagueEntry(currentLeague()||list[0].leagueId),wm=await D().model(entry);if(my!==token)return;
  const data=await Promise.all(list.map(async x=>({x,p:wm.player(x.pid),hv:await horizonValues(wm,x.pid),im:await impact(entry,wm,x.pid)})));if(my!==token)return;
  const weeks=data[0]?.hv.map(h=>h.week)||[];
  const cell=(f)=>data.map(d=>`<td>${f(d)}</td>`).join('');
  el.innerHTML=`<div class="v10-rd-head"><div><h2>Compare</h2><div class="v10-muted">in ${k.esc(wm.entry.name)} scoring · week ${k.esc(wm.key.week)}</div></div><button class="v10-btn v10-ghost" data-v10-close aria-label="Close">✕</button></div>
    <div class="v10-rd-body"><table class="v10-table v10-cmp"><thead><tr><th></th>${data.map(d=>`<th>${k.esc(d.p?.name||d.x.name)} <button class="v10-btn v10-ghost" data-v10-unpin="${k.esc(d.x.pid)}" title="Remove">✕</button></th>`).join('')}</tr></thead><tbody>
    <tr><td>Position · team</td>${cell(d=>`${k.esc(d.p?.position)} · ${k.esc(d.p?.team||'FA')}`)}</tr>
    <tr><td>Status</td>${cell(d=>k.statusChip(d.p?.status)||'Active')}</tr>
    <tr><td>Game</td>${cell(d=>k.esc(k.gameText(d.p?.game)))}</tr>
    ${weeks.map((w,i)=>`<tr><td>W${w} projection</td>${cell(d=>d.hv[i].published?`<span class="v10-num">${k.pts(d.hv[i].value)}</span>`:'<span class="v10-muted" title="Sleeper has not published this week yet">not yet</span>')}</tr>`).join('')}
    <tr><td>Sum W${weeks[0]}–W${weeks[weeks.length-1]}</td>${cell(d=>`<b>${k.pts(d.hv.reduce((s,h)=>s+(h.value||0),0))}</b>`)}</tr>
    <tr><td>Range (P10–P90 where calibrated)</td>${cell(d=>d.p?.range?`${k.pts(d.p.range.low)}–${k.pts(d.p.range.high)}${d.p.range.calibrated?'':' <span class="v10-muted" title="Rule-of-thumb range (no calibration for this position)">*</span>'}`:'–')}</tr>
    <tr><td>Your lineup</td>${cell(d=>`<span class="v10-small">${impactText(d.im)}</span>`)}</tr>
    </tbody></table>${curve(data.map(d=>d.p))}${statTable(data.map(d=>d.p),wm)}<p class="v10-muted">Lineup impact = full re-optimisation of your legal lineup in this league (same engine as Waivers). Ranges: P10–P90 calibrated on 2026 Weeks 1–5 for QB/RB/WR/TE (out of sample Week 6: 79 % inside, RB/TE a bit narrow); * = rule of thumb (K, D/ST, IDP).</p></div>`;
}
function renderTray(){
  const root=document.getElementById('fieV10');if(!root)return;let t=document.getElementById('fieV10Tray');const list=pins(),k=K();
  if(!list.length){if(t)t.remove();return;}
  if(!t){t=document.createElement('div');t.id='fieV10Tray';root.appendChild(t);}
  t.innerHTML=`<span class="v10-muted">Compare (${list.length}/${MAX})</span>${list.map(x=>`<span class="v10-chip v10-poschip">${k.esc(x.name)} <a href="#" data-v10-unpin="${k.esc(x.pid)}" aria-label="Remove">✕</a></span>`).join('')}<button class="v10-btn" data-v10-compare>Compare</button><button class="v10-btn v10-ghost" data-v10-clearpins>Clear</button>`;
}
document.addEventListener('click',e=>{
  const a=e.target.closest?.('[data-v10-player]');if(a&&a.closest('#fieV10')){e.preventDefault();e.stopPropagation();open(a.dataset.v10Player,a.dataset.v10League||null);return;}
  if(e.target.closest?.('[data-v10-close]')){e.preventDefault();close();document.getElementById('fieV10Reader')?.classList.remove('v10-rd-wide');return;}
  const pin=e.target.closest?.('[data-v10-pin]');if(pin){const l=pins();if(!l.some(x=>x.pid===pin.dataset.v10Pin)&&l.length<MAX)setPins([...l,{pid:pin.dataset.v10Pin,leagueId:pin.dataset.v10PinLeague,name:pin.dataset.v10PinName}]);pin.disabled=true;pin.textContent='Pinned';return;}
  const un=e.target.closest?.('[data-v10-unpin]');if(un){e.preventDefault();setPins(pins().filter(x=>x.pid!==un.dataset.v10Unpin));if(document.querySelector('#fieV10Reader.v10-rd-wide:not([hidden])'))compare();return;}
  if(e.target.closest?.('[data-v10-compare]')){e.preventDefault();compare();return;}
  if(e.target.closest?.('[data-v10-clearpins]')){e.preventDefault();setPins([]);return;}
},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!document.getElementById('fieV10Reader')?.hidden)close();});
window.addEventListener('hashchange',()=>{close();renderTray();});
window.FIEV10Reader={VERSION,open,compare,close,pins,renderTray};
})();

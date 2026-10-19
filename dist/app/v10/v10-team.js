/* FIE UI v10 Players and Team tabs (R3 · WP3.2, WP3.3) — UI contract §7.2.
 *
 * Players: every player the league can start, in this league's scoring, with owner and status.
 *   Visible filters (position, owner, horizon, search); defaults reset when the league changes; sorted by the
 *   chosen horizon; rows expand to the shared player detail; names open the shared reader.
 * Team: position strength vs the league, depth / thin positions, byes in the next weeks, roster with real
 *   Sleeper slots and the gap to the best free agent at the position.
 * Numbers: FIETeamViews on FIEV10Data.inputs() — the same WeekModel and horizon as Lineup and Waivers.
 */
(function(){
'use strict';
const VERSION='10.3.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
const DEF={pos:'ALL',own:'ALL',hz:'week',q:'',n:50};
let ps={...DEF,leagueId:null},last=null;
function filtered(data){
  const q=ps.q.trim().toLowerCase(),key=ps.hz==='week'?'week':'next';
  return data.rows.filter(r=>(ps.pos==='ALL'||r.position===ps.pos)&&(ps.own==='ALL'||(ps.own==='FA'&&r.fa)||(ps.own==='ME'&&r.mine)||(ps.own==='OTHER'&&!r.fa&&!r.mine))&&(!q||r.name.toLowerCase().includes(q)||String(r.team||'').toLowerCase()===q))
    .sort((a,b)=>(b[key]??0)-(a[key]??0)||String(a.name).localeCompare(String(b.name)));
}
function ownText(r){const k=K();if(r.fa)return '<span class="v10-good">free agent</span>';if(r.mine)return `<b>yours</b>${r.owner.where!=='roster'?` <span class="v10-muted">(${k.esc(r.owner.where)})</span>`:''}`;return `${k.esc(r.owner?.name||'')}${r.owner?.where&&r.owner.where!=='roster'?` <span class="v10-muted">(${k.esc(r.owner.where)})</span>`:''}`;}
function playersTable(data,wm){
  const k=K(),rows=filtered(data),shown=rows.slice(0,ps.n),w=data.weeks;
  const head=`<div class="v10-plhead"><span class="v10-num">#</span><span>Player</span><span>Game</span>${w.map((x,i)=>`<span class="v10-num">${i===0?'Proj':'W'+x} (pts)</span>`).join('')}<span class="v10-num">W${w[0]}–W${w[w.length-1]}</span><span>Owner</span></div>`;
  const body=shown.map((r,i)=>{const p=wm.player(r.pid),det=k.playerDetail(p,wm);
    const sum=`<span class="v10-num v10-muted">${i+1}</span><span class="v10-p-name">${k.playerLink(r,{leagueId:wm.key.leagueId})} <span class="v10-muted">${k.esc(r.position)} · ${k.esc(r.team||'FA')}</span> ${k.statusChip(r.status)}</span><span class="v10-p-game">${k.esc(k.gameText(r.game))}</span>${r.values.map((v,j)=>`<span class="v10-num">${data.published[j]?k.pts(v):'<span class="v10-muted">not yet</span>'}</span>`).join('')}<span class="v10-num"><b>${k.pts(r.next)}</b></span><span>${ownText(r)}</span>`;
    return k.expand(sum,det.body,{adv:det.adv,cls:'v10-plrow',key:`pl:${wm.key.leagueId}:${r.pid}`});}).join('');
  return `<div class="v10-muted v10-small">${rows.length} players${rows.length>shown.length?` · showing ${shown.length}`:''} · sorted by ${ps.hz==='week'?`Week ${w[0]}`:`W${w[0]}–W${w[w.length-1]}`}${data.published.some(x=>!x)?` · Sleeper has published ${data.published.filter(Boolean).length} of ${w.length} weeks`:''}</div>${head}${body||k.empty('No player matches these filters.')}${rows.length>shown.length?`<div class="v10-row"><button class="v10-btn" data-v10-more>Show 50 more</button></div>`:''}`;
}
function playersBody(data,wm){
  const k=K();if(ps.leagueId!==wm.key.leagueId)ps={...DEF,leagueId:wm.key.leagueId};
  last={data,wm};
  const pos=[...new Set(data.rows.map(r=>r.position))].sort((a,b)=>{const o=['QB','RB','WR','TE','K','DEF','DL','LB','DB'];return (o.indexOf(a)+99)%99-(o.indexOf(b)+99)%99;});
  const sel=(name,opts,v)=>`<select data-v10-pf="${name}" aria-label="${name}">${opts.map(([val,l])=>`<option value="${k.esc(val)}"${val===v?' selected':''}>${k.esc(l)}</option>`).join('')}</select>`;
  const w=data.weeks;
  return `<section class="v10-card"><h2>Players <span class="v10-muted">league scoring · status as in Lineup</span></h2>
    <div class="v10-row v10-filters">${sel('pos',[['ALL','All positions'],...pos.map(p=>[p,p])],ps.pos)}${sel('own',[['ALL','All owners'],['FA','Free agents'],['ME','Mine'],['OTHER','Other teams']],ps.own)}${sel('hz',[['week',`Week ${w[0]}`],['next',`W${w[0]}–W${w[w.length-1]}`]],ps.hz)}
    <input type="search" data-v10-pf="q" placeholder="Search player or team" value="${k.esc(ps.q)}" aria-label="Search"><button class="v10-btn v10-ghost" data-v10-preset>Reset filters</button></div>
    <div id="v10PlTable" style="--wk:${w.length}">${playersTable(data,wm)}</div></section>`;
}
function bindPlayers(root){
  const redraw=()=>{const t=root.querySelector('#v10PlTable');if(t&&last)K().repaint(t,playersTable(last.data,last.wm));};
  root.querySelectorAll('[data-v10-pf]').forEach(el=>el.addEventListener(el.tagName==='INPUT'?'input':'change',e=>{ps[e.target.dataset.v10Pf]=e.target.value;ps.n=DEF.n;redraw();}));
  root.querySelector('[data-v10-preset]')?.addEventListener('click',()=>{ps={...DEF,leagueId:ps.leagueId};root.querySelectorAll('[data-v10-pf]').forEach(el=>{el.value=ps[el.dataset.v10Pf];});redraw();});
  if(!root.__v10PlMore){root.__v10PlMore=true;root.addEventListener('click',e=>{if(e.target.closest?.('[data-v10-more]')&&root.querySelector('#v10PlTable')){ps.n+=50;const t=root.querySelector('#v10PlTable');if(t&&last)K().repaint(t,playersTable(last.data,last.wm));}});}
}
function teamBody(t,wm){
  const k=K(),w=t.weeks;
  let html=`<section class="v10-card"><h2>Team strength <span class="v10-muted">optimal lineup this week, status-adjusted</span></h2>
    <p>Your best lineup: <b>${k.pts(t.myTotal)}</b> pts · rank <b>${k.esc(t.totalRank??'–')}</b> of ${k.esc(t.teams)} active teams · league median ${k.pts(t.medianTotal)}</p>
    <table class="v10-table"><thead><tr><th>Position</th><th class="v10-num">Your pts</th><th class="v10-num">Rank</th><th class="v10-num">League median</th><th class="v10-num">Best team</th></tr></thead><tbody>
    ${t.strength.map(s=>`<tr class="${s.rank&&s.rank>Math.ceil(s.of*0.75)?'v10-weak':''}"><td>${k.esc(s.position)}</td><td class="v10-num">${k.pts(s.points)}</td><td class="v10-num">${k.esc(s.rank??'–')}/${k.esc(s.of)}</td><td class="v10-num">${k.pts(s.median)}</td><td class="v10-num">${k.pts(s.best)}</td></tr>`).join('')}</tbody></table>
    <p class="v10-muted">Points are credited to the player's position (a FLEX RB counts as RB). Bottom quarter shaded.</p></section>`;
  html+=`<section class="v10-card"><h2>Depth</h2>${t.thin.length?`<div class="v10-warn">Thin: ${t.thin.map(x=>`<b>${k.esc(x.position)}</b> — if ${x.starters.map(s=>`${k.esc(s.name)} can't play, your bench recovers ${k.pct(s.recovered)}${s.nextBest?` (${k.esc(s.nextBest)})`:''} and the best free agent ${k.pct(s.faRecovered)}${s.bestFa?` (${k.esc(s.bestFa.name)})`:''}`).join('; ')}`).join(' · ')}</div>`:`<div class="v10-ok">No thin position: for every starter your bench or the best free agent recovers at least ${k.pct(t.thinAt)} of his points.</div>`}
    ${k.expand('<b>Every starter</b> <span class="v10-muted">points lost if he can\'t play (full re-optimisation)</span>',`<table class="v10-table"><thead><tr><th>Slot</th><th>Starter</th><th class="v10-num">Proj</th><th class="v10-num">Lost if out</th><th class="v10-num">Bench recovers</th><th>Next best</th><th class="v10-num">Best FA recovers</th></tr></thead><tbody>${t.depth.map(d=>`<tr><td>${k.esc(d.slot)}</td><td>${k.esc(d.name)} <span class="v10-muted">${k.esc(d.position)}</span></td><td class="v10-num">${k.pts(d.value)}</td><td class="v10-num">${d.loss===null?'–':k.pts(d.loss)}</td><td class="v10-num">${d.recovered===null?'–':k.pct(d.recovered)}</td><td>${k.esc(d.nextBest||'–')}</td><td class="v10-num" title="${d.bestFa?k.esc(d.bestFa.name):''}">${k.pct(d.faRecovered)}</td></tr>`).join('')}</tbody></table>`,{key:`depth:${wm.key.leagueId}`})}</section>`;
  html+=`<section class="v10-card"><h2>Byes W${w[1]??''}–W${w[w.length-1]}</h2>${t.byes.length?`<table class="v10-table"><thead><tr><th>Week</th><th>On bye</th><th class="v10-num">Lineup cost</th></tr></thead><tbody>${t.byes.map(b=>`<tr><td>W${k.esc(b.week)}${b.published?'':' <span class="v10-muted">(not published)</span>'}</td><td>${b.players.length?b.players.map(p=>`${p.starter?'<b>':''}${k.esc(p.name)}${p.starter?'</b>':''} <span class="v10-muted">${k.esc(p.position)}</span>`).join(', '):'–'}</td><td class="v10-num">${b.cost>0?`<b class="v10-bad">−${k.pts(b.cost)}</b>`:'0.0'}</td></tr>`).join('')}</tbody></table><p class="v10-muted">Lineup cost = your best lineup with this week's values, minus the same with bye players at 0 (works before Sleeper publishes the week). Bold = in your best lineup now.</p>`:k.empty('No later weeks in the horizon.')}</section>`;
  html+=`<section class="v10-card"><h2>Roster <span class="v10-muted">Sleeper slots</span></h2><table class="v10-table"><thead><tr><th>Slot</th><th>Player</th>${w.map((x,i)=>`<th class="v10-num">${i===0?'Proj':'W'+x}</th>`).join('')}<th class="v10-num">Season /gm</th><th class="v10-num">${wm.format?.dynasty?'Dynasty ADP':'ADP'}</th><th class="v10-num" title="This week's value minus the best free agent at the position">vs best FA</th></tr></thead><tbody>
    ${t.roster.map(r=>`<tr class="${r.inBest?'':'v10-muted-row'}"><td>${k.esc(r.slot)}</td><td>${k.playerLink(r,{leagueId:wm.key.leagueId})} <span class="v10-muted">${k.esc(r.position)} · ${k.esc(r.team||'FA')}</span> ${k.statusChip(r.status)}</td>${r.values.map(v=>`<td class="v10-num">${v===null?'<span class="v10-muted">–</span>':k.pts(v)}</td>`).join('')}<td class="v10-num">${r.ros===null?'–':k.pts(r.ros)}</td><td class="v10-num">${r.adp&&r.adp<999?k.esc(Math.round(r.adp)):'–'}</td><td class="v10-num" title="${r.bestFa?`Best free agent: ${k.esc(r.bestFa.name)} (${k.pts(r.bestFa.value)})`:''}">${r.gap===null?'–':k.signed(r.gap)}</td></tr>`).join('')}</tbody></table>
    <p class="v10-muted">"vs best FA" is a replacement gap (a simple VOR proxy) for this week: your player's value minus the best unrostered player at his position. Season /gm = Sleeper season projection in your scoring ÷ games. Greyed = not in your best lineup this week.</p></section>`;
  return html;
}
async function players(entry){const i=await D().inputs(entry);return{wm:i.wm,data:window.FIETeamViews.players(i)};}
async function team(entry){const i=await D().inputs(entry);return{wm:i.wm,data:window.FIETeamViews.team(i)};}
window.FIEV10Team={VERSION,players,team,playersBody,teamBody,bindPlayers,_state:()=>({...ps})};
})();

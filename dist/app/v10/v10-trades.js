/* FIE UI v10 Trades tab (R3 · WP3.4) — UI contract §7.2.
 *
 * Pick a trade partner, tick players on both sides; the effect on BOTH teams' optimal lineups is computed per week
 * of the horizon and at season rates (FIETrades on the same WeekModel/horizon as Lineup, Waivers and Team).
 * Advisory only: no offer is sent. Picks are not valued in v10; dynasty leagues link to the classic trade evaluator
 * (its asset index) for pick trades. The asset view in Expand is Sleeper's market ADP, labelled as such.
 */
(function(){
'use strict';
const VERSION='10.3.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
let ts={leagueId:null,partner:null,send:new Set(),receive:new Set()},ctx=null;
function teams(i){const names=new Map(i.wm.standings.rows.map(r=>[Number(r.rosterId),r.name]));return (i.rosters||[]).filter(r=>(r.players||[]).length&&Number(r.roster_id)!==Number(i.wm.key.rosterId)).map(r=>({id:Number(r.roster_id),name:names.get(Number(r.roster_id))||`Roster ${r.roster_id}`})).sort((a,b)=>a.name.localeCompare(b.name));}
function rosterList(i,rid,set,side){
  const k=K(),r=(i.rosters||[]).find(x=>Number(x.roster_id)===Number(rid));if(!r)return '';
  const off=new Map([...(r.reserve||[]).map(x=>[String(x),'IR']),...(r.taxi||[]).map(x=>[String(x),'TAXI'])]);
  const rows=(r.players||[]).map(String).map(id=>({id,p:i.wm.player(id)})).filter(x=>x.p).sort((a,b)=>((b.p.status.unavailable?0:b.p.active.value)||0)-((a.p.status.unavailable?0:a.p.active.value)||0));
  return rows.map(({id,p})=>`<label class="v10-tr-pl"><input type="checkbox" data-v10-tr="${side}" value="${k.esc(id)}"${set.has(id)?' checked':''}> ${k.esc(p.name)} <span class="v10-muted">${k.esc(p.position)} · ${k.esc(p.team||'FA')}${off.has(id)?` · ${off.get(id)}`:''}</span> ${k.statusChip(p.status)} <span class="v10-num v10-muted">${k.pts(p.status.unavailable?0:p.active.value)}</span></label>`).join('');
}
function result(i){
  const k=K();if(!ts.partner||(!ts.send.size&&!ts.receive.size))return k.empty('Tick players on both sides to see the effect on both lineups.');
  const e=window.FIETrades.evaluate({wm:i.wm,rosters:i.rosters,partnerRosterId:ts.partner,send:[...ts.send],receive:[...ts.receive],horizon:i.horizon,schedule:i.schedule,catalog:i.catalog,season:i.season,
    seasonRows:i.seasonRows,adp:i.adp,constraints:D().constraintsFor(i.wm.key.leagueId),rosterPositions:i.league?.roster_positions||[],now:Date.now()});
  const w=e.weeks,pn=teams(i).find(t=>t.id===Number(ts.partner))?.name||'Partner';
  const cell=(s,j)=>e.counted[j]?`${k.pts(s.before[j])} → ${k.pts(s.after[j])} <b class="${s.delta[j]>0?'v10-good':s.delta[j]<0?'v10-bad':''}">${k.signed(s.delta[j])}</b>`:`<span class="v10-muted">${e.published[j]?'not counted':'not yet'}</span>`;
  const verdict=(()=>{const a=e.me.horizonDelta,b=e.partner.horizonDelta,ra=e.me.rateDelta;const sa=a>0.25?'helps you':a<-0.25?'costs you':'is neutral for you',sb=b>0.25?'helps them':b<-0.25?'costs them':'is neutral for them';
    return `Over W${w[0]}–W${w[w.length-1]} this trade ${sa} (${k.signed(a)}) and ${sb} (${k.signed(b)}). At season rates: ${k.signed(ra)} pts/game for you, ${k.signed(e.partner.rateDelta)} for them.${Math.sign(a)!==Math.sign(ra)&&Math.abs(a)>0.25&&Math.abs(ra)>0.25?' <b>Short-term and season effects point in different directions.</b>':''}`;})();
  const assets=side=>`<table class="v10-mini"><thead><tr><th>Player</th>${w.map(x=>`<th class="v10-num">W${x}</th>`).join('')}<th class="v10-num">Season /gm</th><th class="v10-num">${i.wm.format?.dynasty?'Dynasty ADP':'ADP'}</th><th class="v10-num">Age</th></tr></thead><tbody>${e.assets[side].map(a=>`<tr><td>${k.esc(a.name)} <span class="v10-muted">${k.esc(a.position)}</span></td>${a.values.map(v=>`<td class="v10-num">${v===null?'–':k.pts(v)}</td>`).join('')}<td class="v10-num">${a.position==='DEF'?'–':k.pts(a.rate)}</td><td class="v10-num">${a.adp&&a.adp<999?k.esc(Math.round(a.adp)):'–'}</td><td class="v10-num">${a.age??'–'}</td></tr>`).join('')}</tbody></table>`;
  return `<table class="v10-table"><thead><tr><th>Week</th><th>You (best lineup)</th><th>${k.esc(pn)}</th></tr></thead><tbody>
    ${w.map((x,j)=>`<tr><td>W${x}</td><td>${cell(e.me,j)}</td><td>${cell(e.partner,j)}</td></tr>`).join('')}
    <tr><td><b>W${w[0]}–W${w[w.length-1]}</b></td><td><b>${k.signed(e.me.horizonDelta)}</b></td><td><b>${k.signed(e.partner.horizonDelta)}</b></td></tr>
    <tr><td>Season rate <span class="v10-muted">pts/game</span></td><td>${k.pts(e.me.rateBefore)} → ${k.pts(e.me.rateAfter)} <b>${k.signed(e.me.rateDelta)}</b></td><td>${k.pts(e.partner.rateBefore)} → ${k.pts(e.partner.rateAfter)} <b>${k.signed(e.partner.rateDelta)}</b></td></tr></tbody></table>
    <p>${verdict}</p>
    ${e.issues.length?`<div class="v10-warn">${e.issues.map(k.esc).join('<br>')}</div>`:''}
    ${e.roster.meDrops||e.roster.partnerDrops?`<div class="v10-note">Roster size: ${e.roster.meDrops?`you must drop ${e.roster.meDrops}`:''}${e.roster.meDrops&&e.roster.partnerDrops?', ':''}${e.roster.partnerDrops?`they must drop ${e.roster.partnerDrops}`:''} (lineups above assume the weakest bench players go).</div>`:''}
    ${!e.rateComplete?'<p class="v10-muted">Some players have no Sleeper season projection; their season rate counts as 0.</p>':''}
    ${k.expand('<b>Assets</b> <span class="v10-muted">market view, not an FIE value</span>',`<div class="v10-grid2"><div><h3>You send</h3>${assets('send')}</div><div><h3>You receive</h3>${assets('receive')}</div></div><p class="v10-muted">ADP = Sleeper market average draft position (${i.wm.format?.dynasty?'dynasty, 2QB variant in superflex':'redraft'}); a market signal, not FIE's value model.</p>`,
      {key:`tr-assets:${i.wm.key.leagueId}`,adv:k.kv([['Method','Full re-optimisation of both legal lineups per week (FIECore.LineupOptimizer); reserve/taxi players excluded; this week skipped if a traded player is locked'],['Season rate','Sleeper season projection in league scoring ÷ games; D/ST excluded (bucket scoring)'],['Horizon',w.map(x=>'W'+x).join(', ')]])})}`;
}
function body(i){
  const k=K();if(ts.leagueId!==i.wm.key.leagueId)ts={leagueId:i.wm.key.leagueId,partner:null,send:new Set(),receive:new Set()};
  ctx=i;const list=teams(i);if(ts.partner===null&&list.length)ts.partner=list[0].id;
  if(i.wm.field?.meEliminated)return k.empty('Your team has been eliminated in this league.');
  return `<section class="v10-card"><h2>Trade check <span class="v10-muted">effect on both lineups · advisory, nothing is sent</span></h2>
    <div class="v10-row"><label>Trade with <select data-v10-tr-partner aria-label="Trade partner">${list.map(t=>`<option value="${t.id}"${t.id===Number(ts.partner)?' selected':''}>${k.esc(t.name)}</option>`).join('')}</select></label><button class="v10-btn v10-ghost" data-v10-tr-clear>Clear</button></div>
    <div class="v10-grid2 v10-tr-sides"><div><h3>You send</h3><div class="v10-tr-list">${rosterList(i,i.wm.key.rosterId,ts.send,'send')}</div></div><div><h3>You receive</h3><div class="v10-tr-list" id="v10TrTheirs">${rosterList(i,ts.partner,ts.receive,'receive')}</div></div></div></section>
    <section class="v10-card"><h2>Effect</h2><div id="v10TrResult">${result(i)}</div>${i.wm.format?.dynasty?`<p class="v10-muted">Draft picks are not valued here. For trades with picks use the classic evaluator (asset index): <a href="#/classic/${encodeURIComponent(i.wm.key.leagueId)}/trades">Trades (classic) ↗</a></p>`:''}</section>`;
}
function bind(root){
  const k=K(),res=()=>{const el=root.querySelector('#v10TrResult');if(el&&ctx)k.repaint(el,result(ctx));};
  root.querySelector('[data-v10-tr-partner]')?.addEventListener('change',e=>{ts.partner=Number(e.target.value);ts.receive=new Set();const el=root.querySelector('#v10TrTheirs');if(el&&ctx)el.innerHTML=rosterList(ctx,ts.partner,ts.receive,'receive');res();});
  root.querySelector('[data-v10-tr-clear]')?.addEventListener('click',()=>{ts.send=new Set();ts.receive=new Set();root.querySelectorAll('input[data-v10-tr]').forEach(x=>{x.checked=false;});res();});
  root.querySelector('.v10-tr-sides')?.addEventListener('change',e=>{const t=e.target;if(!t?.dataset?.v10Tr)return;const set=t.dataset.v10Tr==='send'?ts.send:ts.receive;t.checked?set.add(t.value):set.delete(t.value);res();});
}
async function load(entry){return D().inputs(entry);}
window.FIEV10Trades={VERSION,load,body,bind,_state:()=>({...ts,send:[...ts.send],receive:[...ts.receive]})};
})();

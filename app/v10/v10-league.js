/* FIE UI v10 league views (R1 · WP1.4 Lineup, WP1.6 Matchup & Standings, WP1.7 League Home).
 * UI contract §4.2–§4.4.
 *
 * Every number comes from FIEV10Data.model() → FIEWeekModel, the same object the Overview uses.
 * Advisory only: the app never changes a Sleeper lineup; it links to Sleeper.
 * Routes not rewritten in R1 (Waivers, Trades, Draft, Research Lab) open the classic UI for the
 * same league (#/classic/<id>/<tab>), see v10-shell.js.
 */
(function(){
'use strict';
const VERSION='10.1.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
let token=0;
const sleeperUrl=id=>`https://sleeper.com/leagues/${encodeURIComponent(id)}/team`;
function tabs(id,active,wm){
  const k=K(),t=[['home','Home'],['lineup',wm?.format?.bestBall?'Lineup (auto)':'Lineup'],['matchup',wm?.format?.chopped?'Field & standings':'Matchup & standings']];
  const classic=[['waivers','Waivers'],['trades','Trades'],['draft','Draft'],['lab','Research Lab']];
  return `<nav class="v10-tabs">${t.map(([k2,l])=>`<a href="#/league/${encodeURIComponent(id)}/${k2}" class="${k2===active?'active':''}">${k.esc(l)}</a>`).join('')}<span class="v10-tabs-sep"></span>${classic.map(([k2,l])=>`<a class="v10-classic-link" href="#/classic/${encodeURIComponent(id)}/${k2}" title="Opens the classic view">${k.esc(l)} ↗</a>`).join('')}</nav>`;
}
function headerBlock(wm){
  const k=K(),r=wm.standings.rows.find(x=>x.me);
  return `<header class="v10-lhdr"><div><h1>${k.esc(wm.entry.name)} ${k.formatChip(wm.format.key)}</h1><div class="v10-muted">Week ${k.esc(wm.key.week)} · ${k.esc(wm.league.teams)} teams${r?(wm.standings.chopped?` · points-for rank ${r.rank}`:` · ${r.wins}-${r.losses}${r.ties?`-${r.ties}`:''} · rank ${r.rank}`):''} · data ${k.esc(k.clock(wm.dataAt))}</div></div><a class="v10-btn" href="${sleeperUrl(wm.key.leagueId)}" target="_blank" rel="noopener">Open in Sleeper ↗</a></header>`;
}
function valueCell(p){const k=K();if(!p)return '–';const v=p.status.unavailable?0:p.active.value;return `${k.pts(v)}${p.active.dot?' '+k.dot(p.active.dot):''}`;}
/** Points already scored by a lineup part (null before kickoff). */
function scored(part){if(!part||part.kind==='pregame'||part.kind==='empty')return null;return part.actual??part.value;}
function playerRow(e,wm,{mark='',cls='',slotLabel=null,actual=null,keyPrefix='s'}={}){
  const k=K(),p=e.p;
  if(!p)return `<div class="v10-prow v10-empty-slot"><span class="v10-p-slot">${k.esc(slotLabel??e.slot)}</span><span class="v10-p-name"><b class="v10-bad">Empty slot</b></span><span></span><span></span><span></span><span>${mark}</span></div>`;
  const det=k.playerDetail(p,wm);
  const sum=`<span class="v10-p-slot">${k.esc(slotLabel??e.slot??'')}</span><span class="v10-p-name">${k.esc(p.name)} <span class="v10-muted">${k.esc(p.position)} · ${k.esc(p.team||'FA')}</span> ${k.statusChip(p.status)}</span><span class="v10-p-game">${k.esc(k.gameText(p.game))}${p.game.locked&&p.game.state!=='final'?' 🔒':''}</span><span class="v10-num v10-p-proj">${valueCell(p)}</span><span class="v10-num v10-p-act">${actual===null||actual===undefined?'':k.pts(actual,2)}</span><span class="v10-p-mark">${mark}</span>`;
  return k.expand(sum,det.body,{adv:det.adv,cls:`v10-prow ${cls}`,key:`${keyPrefix}:${wm.key.leagueId}:${p.pid}`});
}
function rowsHead(){return `<div class="v10-phead"><span>Slot</span><span>Player</span><span>Game</span><span class="v10-num">Proj</span><span class="v10-num">Pts</span><span></span></div>`;}
function totalsLine(t,label){const k=K();return `<div class="v10-total"><span>${k.esc(label)}</span><b>${k.pts(t.projected)}</b>${t.banked?`<span class="v10-muted">${k.pts(t.banked)} scored + ${k.pts(t.projected-t.banked)} to come</span>`:''}</div>`;}

function lineup(wm){
  const k=K(),rec=wm.me.recommended,outs=new Map(rec.changes.filter(c=>c.outPid).map(c=>[c.outPid,c])),ins=new Map(rec.changes.map(c=>[c.inPid,c]));
  const parts=wm.me.totals.parts;
  let html='';
  if(wm.format.bestBall)html+=`<div class="v10-note">Best Ball: Sleeper sets the optimal lineup automatically after the games. Shown is the projected best lineup; there is nothing to change.</div>`;
  else if(rec.changes.length){
    const q=rec.changes.map(c=>wm.player(c.inPid)).filter(p=>p?.status?.monitor);
    html+=`<div class="v10-rec v10-rec-${k.esc(rec.tier)}"><div class="v10-rec-h">${k.tierChip(rec.tier)} <b>Suggested lineup: ${k.signed(rec.gain)} projected pts</b> <span class="v10-muted">(${k.pts(rec.submittedTotal)} → ${k.pts(rec.optimizedTotal)} on unlocked slots)</span></div><ul>${rec.changes.map(c=>`<li>Start <b>${k.esc(wm.player(c.inPid)?.name)}</b> ${c.slot?`at ${k.esc(c.slot)} `:''}for ${c.outPid?k.esc(wm.player(c.outPid)?.name):'the empty slot'} <span class="v10-muted">(${k.signed(c.delta)})</span></li>`).join('')}</ul>${q.length?`<div class="v10-warn">${q.map(p=>{const fb=(rec.fallbacks||[]).find(f=>f.forPid===p.pid),alt=fb?.pid?wm.player(fb.pid):null;return `<b>${k.esc(p.name)}</b> is Questionable — confirm before lock (${k.esc(k.time(p.game.kickoff))}, inactives ~${k.esc(k.clock(p.game.kickoff-90*60000))}). If ruled out: ${alt?`start <b>${k.esc(alt.name)}</b> instead (${k.signed(fb.gain)} vs your lineup)`:'keep your current lineup'}.`;}).join('<br>')}</div>`:''}<a class="v10-btn" href="${sleeperUrl(wm.key.leagueId)}" target="_blank" rel="noopener">Change lineup in Sleeper ↗</a></div>`;
  }else if(wm.me.matchupFound)html+=`<div class="v10-ok">Your Sleeper lineup is the best projected lineup for the unlocked slots${rec.tier==='none'&&rec.optimizedTotal!==null&&rec.optimizedTotal-rec.submittedTotal>0.005?` (best alternative only ${k.signed(rec.optimizedTotal-rec.submittedTotal,2)})`:''}.</div>`;
  else html+=`<div class="v10-note">No Sleeper matchup for this week yet — showing roster starters.</div>`;
  html+=`<section class="v10-card"><h2>${wm.format.bestBall?'Projected best lineup':'Your Sleeper lineup'}</h2>${totalsLine(wm.me.totals,'Projected total')}${rowsHead()}${wm.me.submitted.map((e,i)=>playerRow(e,wm,{actual:scored(parts[i]),mark:outs.has(e.pid)?`<span class="v10-chip v10-tier-${outs.get(e.pid).delta>=0?'recommended':'monitor'}">bench</span>`:'',cls:outs.has(e.pid)?'v10-out':''})).join('')}</section>`;
  const bench=wm.me.bench.filter(p=>!wm.me.submitted.some(e=>e.pid===p.pid)).sort((a,b)=>b.recValue-a.recValue);
  html+=`<section class="v10-card"><h2>Bench <span class="v10-muted">${bench.length}</span></h2>${rowsHead()}${bench.map(p=>playerRow({slot:'BN',pid:p.pid,p},wm,{keyPrefix:'b',mark:ins.has(p.pid)?`<span class="v10-chip v10-tier-${k.esc(rec.tier==='close'?'close':rec.tier)}">start ${k.esc(ins.get(p.pid).slot||'')}</span>`:'',cls:ins.has(p.pid)?'v10-in':''})).join('')||k.empty('No bench players.')}</section>`;
  const res=[...wm.me.reserve.map(p=>({p,slot:'IR'})),...wm.me.taxi.map(p=>({p,slot:'TAXI'}))];
  if(res.length)html+=k.expand(`<b>Reserve & taxi</b> <span class="v10-muted">${res.length}</span>`,`${rowsHead()}${res.map(x=>playerRow({slot:x.slot,pid:x.p.pid,p:x.p},wm,{keyPrefix:'r'})).join('')}`,{cls:'v10-card v10-resv',key:`res:${wm.key.leagueId}`});
  return html;
}
function matchup(wm){
  const k=K();let html='';
  if(wm.opponent){
    const w=wm.winEstimate,o=wm.opponent;
    html+=`<section class="v10-card v10-h2h"><div class="v10-h2h-side"><div class="v10-muted">You</div><div class="v10-big">${k.pts(wm.me.totals.projected)}</div>${wm.me.totals.banked?`<div class="v10-muted">${k.pts(wm.me.totals.banked)} scored</div>`:''}</div>
      <div class="v10-h2h-mid"><div class="v10-big">${k.winPct(w?.value)} ${k.dot('amber',w?.note)}</div><div class="v10-muted">win estimate</div>${w?.withRecommended!==undefined?`<div class="v10-muted">${k.winPct(w.withRecommended)} with suggested lineup</div>`:''}</div>
      <div class="v10-h2h-side"><div class="v10-muted">${k.esc(o.name)}</div><div class="v10-big">${k.pts(o.totals.projected)}</div>${o.totals.banked?`<div class="v10-muted">${k.pts(o.totals.banked)} scored</div>`:''}</div></section>`;
    html+=k.expand(`<b>Opponent lineup</b> <span class="v10-muted">${k.esc(o.name)}</span>`,`${rowsHead()}${o.starters.map((e,i)=>playerRow(e,wm,{keyPrefix:'o',actual:scored(o.totals.parts[i])})).join('')}`,{cls:'v10-card',key:`opp:${wm.key.leagueId}`,adv:k.kv([['Win estimate method',k.esc(w?.method)],['Note',k.esc(w?.note)],['Inputs',k.esc(w?.inputsHash)]])});
  }
  if(wm.field){
    const f=wm.field;
    html+=`<section class="v10-card"><h2>Field <span class="v10-muted">${f.activeCount} active · ${f.eliminatedCount} chopped${f.verified?'':' '+k.dot('amber',`Sleeper reports ${f.scoredWeeks} scored weeks but ${f.eliminatedCount} empty rosters`)}</span></h2>
      <table class="v10-table"><thead><tr><th>#</th><th>Team</th><th class="v10-num">Projected</th><th class="v10-num">vs lowest</th></tr></thead><tbody>${f.rows.map(r=>`<tr class="${r.me?'v10-me':''}${r.rank===f.rows.length?' v10-cut':''}"><td>${r.rank}</td><td>${k.esc(r.name)}${r.me?' (you)':''}</td><td class="v10-num">${k.pts(r.projected)}</td><td class="v10-num">${f.cutLine===null?'–':k.signed(r.projected-Math.min(...f.rows.map(x=>x.projected)))}</td></tr>`).join('')}</tbody></table>
      ${f.marginToCut!==null?`<p>${f.marginToCut<10?'<b class="v10-bad">Chop risk</b> — ':''}You are projected ${k.signed(f.marginToCut)} pts above the lowest other team.</p>`:''}
      ${f.eliminated.length?`<div class="v10-muted">Chopped: ${f.eliminated.map(x=>k.esc(x.name)).join(', ')}</div>`:''}</section>`;
  }
  const s=wm.standings,po=s.playoffTeams,ties=s.rows.some(r=>r.ties);
  const head=s.chopped?`<th>#</th><th>Team</th><th class="v10-num">Points for</th><th>Status</th><th class="v10-num" id="v10OddsHead">Survival</th>`
    :`<th>#</th><th>Team</th><th>W-L${ties?'-T':''}</th><th class="v10-num">PF</th><th class="v10-num">PA</th><th class="v10-num" id="v10OddsHead">Playoff odds</th>`;
  const row=r=>s.chopped?`<tr class="${r.me?'v10-me':''}${r.active?'':' v10-muted'}"><td>${r.rank}</td><td>${k.esc(r.name)}${r.me?' (you)':''}</td><td class="v10-num">${k.pts(r.pf,1)}</td><td>${r.active?'Active':'Chopped'}</td><td class="v10-num" data-odds="${r.rosterId}"></td></tr>`
    :`<tr class="${r.me?'v10-me':''}${po&&r.rank===po?' v10-line':''}"><td>${r.rank}</td><td>${k.esc(r.name)}${r.me?' (you)':''}</td><td>${r.wins}-${r.losses}${ties?`-${r.ties}`:''}</td><td class="v10-num">${k.pts(r.pf,1)}</td><td class="v10-num">${k.pts(r.pa,1)}</td><td class="v10-num" data-odds="${r.rosterId}"></td></tr>`;
  html+=`<section class="v10-card"><h2>Standings</h2><table class="v10-table"><thead><tr>${head}</tr></thead><tbody>${s.rows.map(row).join('')}</tbody></table>
    <div class="v10-row"><button class="v10-btn" data-v10-odds="${k.esc(wm.key.leagueId)}">${s.chopped?'Compute survival odds':'Compute playoff odds'}</button><span class="v10-muted" id="v10OddsStatus">Runs the classic league simulation on demand (≈10–60 s). ${k.dot('amber','Simulation spread not yet calibrated (WP-V1)')}</span></div>${s.medianGames?'<div class="v10-muted">This league also plays against the weekly median.</div>':''}${po?`<div class="v10-muted">Line under rank ${po}: playoff cut.</div>`:''}</section>`;
  return html;
}
function home(wm){
  const k=K(),alerts=window.FIEAlerts.sort(window.FIEAlerts.forLeague(wm,{leagueId:wm.key.leagueId,leagueName:wm.entry.name,priority:wm.entry.priority}));
  let html=`<section class="v10-card"><h2>To do</h2>${alerts.length?alerts.map(a=>`<div class="v10-task v10-q-${k.esc(a.tier)}">${k.tierChip(a.code==='CLOSE_CALL'?'close':a.tier)} <a href="#/league/${encodeURIComponent(wm.key.leagueId)}/${a.route==='matchup'?'matchup':a.route==='home'?'home':'lineup'}">${k.esc(a.title)}</a>${a.detail?` <span class="v10-muted">${k.esc(a.detail)}</span>`:''}${a.lockAt?` <span class="v10-lock">${k.esc(k.until(a.lockAt))}</span>`:''}</div>`).join(''):k.empty('Nothing to do in this league right now.')}</section>`;
  const sum=wm.opponent?`${k.pts(wm.me.totals.projected)} – ${k.pts(wm.opponent.totals.projected)} vs ${k.esc(wm.opponent.name)} · win estimate ${k.winPct(wm.winEstimate?.value)} ${k.dot('amber',wm.winEstimate?.note)}`:wm.field?(wm.field.meEliminated?'Eliminated':`Projected #${wm.field.myRank} of ${wm.field.activeCount} · ${k.signed(wm.field.marginToCut)} vs the lowest team`):`${k.pts(wm.me.totals.projected)} projected`;
  const unavailable=wm.me.submitted.filter(e=>e.p?.status?.unavailable).length,q=wm.me.submitted.filter(e=>e.p?.status?.monitor).length;
  html+=`<section class="v10-card v10-grid2"><div><h3>This week</h3><p>${sum}</p><a href="#/league/${encodeURIComponent(wm.key.leagueId)}/matchup">Matchup & standings →</a></div><div><h3>Lineup</h3><p>${wm.format.bestBall?'Automatic (Best Ball)':`${wm.me.submitted.filter(e=>e.p).length}/${wm.slots.length} slots filled · ${unavailable} can't play · ${q} questionable`}</p><a href="#/league/${encodeURIComponent(wm.key.leagueId)}/lineup">Lineup →</a></div></section>`;
  html+=`<section class="v10-card"><h3>More for this league</h3><p class="v10-muted">Not rebuilt yet in the new interface — these open the classic view for this league.</p><div class="v10-row">${[['waivers','Waivers'],['trades','Trades'],['draft','Draft'],['lab','Research Lab']].map(([t,l])=>`<a class="v10-btn" href="#/classic/${encodeURIComponent(wm.key.leagueId)}/${t}">${l} ↗</a>`).join('')}</div></section>`;
  return html;
}
async function oddsFor(id,root){
  const st=root.querySelector('#v10OddsStatus'),btn=root.querySelector(`[data-v10-odds]`);if(btn)btn.disabled=true;if(st)st.textContent='Loading the league in the classic engine…';
  try{
    const ctl=window.FIELeagueController;if(!ctl?.switchLeague)throw new Error('classic engine not available');
    if(String(window.state?.league?.league_id||'')!==String(id)){const ok=await ctl.switchLeague(String(id));if(!ok)throw new Error('league did not load');}
    if(st)st.textContent='Simulating…';
    const data=await window.FIEDecisionEngines.runLeagueSimulation(true);const rows=data?.strategic?.rows||[];
    if(!rows.length)throw new Error('simulation returned no rows');
    for(const r of rows){const cell=root.querySelector(`[data-odds="${Number(r.rosterId)}"]`);if(!cell)continue;const v=r.playoff??r.survival??r.winner;cell.textContent=v===undefined?'–':K().pct(v);cell.title=r.title!==undefined?`Title ${K().pct(r.title)}`:r.winner!==undefined?`Win league ${K().pct(r.winner)}`:'';}
    const head=root.querySelector('#v10OddsHead');if(head&&data.chopped)head.textContent='Survival';
    if(st)st.innerHTML=`${K().esc(data.strategic.iterations||'')} simulated seasons · classic engine ${K().dot('amber','Simulation spread not yet calibrated (WP-V1)')}`;
  }catch(e){if(st)st.textContent=`Could not compute: ${String(e?.message||e)}`;}
  finally{if(btn)btn.disabled=false;}
}
async function render(root,id,tab='home'){
  const my=++token,k=K(),entry=(await D().leagues()).find(x=>String(x.id)===String(id))||{id,name:id};
  if(my!==token)return;
  if(!root.querySelector(`[data-v10-league="${id}"]`))root.innerHTML=`<div class="v10-league" data-v10-league="${k.esc(id)}">${tabs(id,tab,null)}<div class="v10-loading">Loading ${k.esc(entry.name)}…</div></div>`;
  let wm;try{wm=await D().model(entry);}catch(e){if(my===token)root.innerHTML=`<div class="v10-league">${tabs(id,tab,null)}${k.empty(`Could not load this league: ${String(e?.message||e)}`)}</div>`;return;}
  if(my!==token)return;
  const body=tab==='lineup'?lineup(wm):tab==='matchup'?matchup(wm):home(wm);
  k.repaint(root,`<div class="v10-league" data-v10-league="${k.esc(id)}">${headerBlock(wm)}${tabs(id,tab,wm)}${wm.issues.length?`<div class="v10-warn">${wm.issues.map(i=>k.esc(i.text)).join(' · ')}</div>`:''}${body}</div>`);
  root.querySelector('[data-v10-odds]')?.addEventListener('click',()=>oddsFor(id,root));
}
function cancel(){token++;}
window.FIEV10League={VERSION,render,cancel};
})();

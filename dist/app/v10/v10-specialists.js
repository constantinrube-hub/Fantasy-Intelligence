/* FIE UI v10 Kicker & D/ST board in Lineup (R3 · WP3.5) — UI contract §4.2.1.
 *
 * For each specialist position the league starts (K, DEF), one card under the bench:
 *   · your rostered kickers / D/STs: this week (league-scored, status) and the next weeks of the waiver
 *     horizon with opponent and byes;
 *   · the best free agents at that position: the same per-week values plus the full legal lineup gain
 *     and the drop, taken from FIEWaivers on the same WeekModel (identical to the Waivers tab).
 * In-season copy only: no PAY / WAIT / STREAM labels (the old draft-time board); numbers speak.
 * Read-only and advisory; no new projection is created.
 */
(function(){
'use strict';
const VERSION='10.3.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
const LABEL={K:'Kicker',DEF:'D/ST'};
function specialistPositions(wm){const PR=window.FIECore.PositionRegistry;return ['K','DEF'].filter(pos=>wm.slots.some(s=>PR.eligible(pos,s)));}
/** Per-week values (this week = WeekModel value after status; later weeks = Sleeper's projection for that week) and opponents. */
function weekly(wm,pid,hz,sched,cat){
  const p=wm.player(pid),team=p?.team;
  return hz.map((h,i)=>{
    if(i===0)return{week:h.week,value:p?(p.status.unavailable?0:p.active.value):null,opp:p?.game?.bye?'BYE':p?.game?.opp?`${p.game.homeAway||'vs'} ${p.game.opp}`:'',published:true};
    const g=window.FIEGameState.forTeam(sched,team,{week:h.week,season:wm.key.season,now:Date.now()});
    const v=h.projRows.size?window.FIEWaivers.futureValuer({projRows:h.projRows,scoring:wm.league.scoring,schedule:sched,week:h.week,season:wm.key.season,now:Date.now(),catalog:cat,longTermOut:()=>false})(pid).value:null;
    return{week:h.week,value:v,opp:g.bye?'BYE':g.opp?`${g.homeAway} ${g.opp}`:'',published:h.projRows.size>0};});
}
function cells(ws){const k=K();return ws.map(x=>`<td class="v10-num">${x.opp==='BYE'?'<span class="v10-muted">BYE</span>':x.published?`${k.pts(x.value)} <span class="v10-muted v10-small">${k.esc(x.opp)}</span>`:`<span class="v10-muted" title="Sleeper has not published this week yet">not yet</span>${x.opp?` <span class="v10-muted v10-small">${k.esc(x.opp)}</span>`:''}`}</td>`).join('');}
const sumValues=r=>(r.values||[]).reduce((a,v)=>a+(Number(v)||0),0);
/** HTML of the board for the live week, or '' when the league starts no kicker / D/ST. */
async function board(entry,wm){
  const k=K(),poss=specialistPositions(wm);if(!poss.length||wm.field?.meEliminated)return '';
  const n=Number(window.FIE_UI_POLICY?.waivers?.horizon_weeks)||3;
  const [hz,sched,cat,wv]=await Promise.all([D().horizon(wm.key.season,wm.key.week,n),D().schedule(),D().catalog(),D().waivers(entry,{}).catch(()=>null)]);
  const res=wv?.result,weeks=hz.map(h=>h.week),started=new Set(wm.me.submitted.map(e=>e.pid)),rec=new Set((wm.me.recommended.starters||[]).map(e=>e.pid));
  const mineAll=[...wm.me.submitted.map(e=>e.p).filter(Boolean),...wm.me.bench];
  let html='';
  for(const pos of poss){
    const mine=[...new Map(mineAll.filter(p=>p.position===pos).map(p=>[p.pid,p])).values()];
    // Best free agents: lineup gain first, then projected points over the horizon (ties are common for kickers).
    const fas=(res?.rows||[]).filter(r=>r.position===pos).sort((a,b)=>(Math.max(0,b.gainHorizon)-Math.max(0,a.gainHorizon))||(sumValues(b)-sumValues(a))).slice(0,5);
    const head=`<thead><tr><th>${k.esc(LABEL[pos])}</th>${weeks.map(w=>`<th class="v10-num">W${w}</th>`).join('')}<th class="v10-num">Gain W${weeks[0]}</th><th class="v10-num">Gain W${weeks[0]}–W${weeks[weeks.length-1]}</th><th>Note</th></tr></thead>`;
    const mineRows=mine.map(p=>{const ws=weekly(wm,p.pid,hz,sched,cat);const role=started.has(p.pid)?'starting':'bench';
      return `<tr class="v10-me"><td>${k.playerLink(p,{leagueId:wm.key.leagueId})} ${k.statusChip(p.status)} <span class="v10-muted">yours · ${role}${!wm.format.bestBall&&rec.has(p.pid)!==started.has(p.pid)?(rec.has(p.pid)?' · suggested to start':' · suggested to bench'):''}</span></td>${cells(ws)}<td class="v10-num">–</td><td class="v10-num">–</td><td class="v10-muted">${ws.some((x,i)=>i>0&&x.opp==='BYE')?`bye W${ws.find((x,i)=>i>0&&x.opp==='BYE').week}`:''}</td></tr>`;}).join('');
    const faRows=fas.map(r=>{const ws=weekly(wm,r.pid,hz,sched,cat);
      return `<tr><td>${k.playerLink(r,{leagueId:wm.key.leagueId})} ${k.statusChip(r.status)} <span class="v10-muted">free agent</span></td>${cells(ws)}<td class="v10-num">${r.gainWeek>0?`<b class="v10-good">${k.signed(r.gainWeek)}</b>`:'0.0'}</td><td class="v10-num">${r.gainHorizon>0?`<b class="v10-good">${k.signed(r.gainHorizon)}</b>`:'0.0'}</td><td class="v10-muted">${r.gainHorizon>0?(r.drop?`drop ${k.esc(r.drop.name)}`:r.freeSpot?'free roster spot':''):'no lineup gain'}${r.fillIn?` · fill-in until ${k.esc(r.fillIn.name)}`:''}</td></tr>`;}).join('');
    const best=fas.find(r=>r.gainHorizon>0);
    // A bye of every rostered player at the position inside the horizon: the waiver gain cannot count an unpublished week.
    const mw=mine.map(p=>weekly(wm,p.pid,hz,sched,cat)),uncovered=weeks.filter((w,i)=>i>0&&mw.length&&mw.every(ws=>ws[i].opp==='BYE'));
    const summary=`<b>${k.esc(LABEL[pos])} — next ${weeks.length} weeks</b> <span class="v10-muted">${mine.length?mine.map(p=>k.esc(p.name)).join(', '):'none rostered'}${best?` · best add ${k.esc(best.name)} ${k.signed(best.gainHorizon)}`:' · no free agent improves your lineup'}</span>${uncovered.length?` <span class="v10-chip v10-tier-monitor" title="No other ${k.esc(LABEL[pos])} on your roster plays that week">no ${k.esc(LABEL[pos])} in W${uncovered.join(', W')} (bye)</span>`:''}`;
    const body=`<div class="v10-specwrap"><table class="v10-table v10-spec">${head}<tbody>${mineRows}${faRows||`<tr><td colspan="${weeks.length+4}" class="v10-muted">No free agent with a projection at this position.</td></tr>`}</tbody></table></div>
      <p class="v10-muted">Values: this week as in your lineup; later weeks Sleeper's projection for that week in your league's scoring, with opponent. Gain = full re-optimisation of your legal lineup with the add and the drop (same numbers as the Waivers tab).${res&&res.weeksAvailable<weeks.length?` Projections published for ${res.weeksAvailable} of ${weeks.length} weeks.`:''}</p>`;
    html+=k.expand(summary,body,{cls:'v10-card v10-specboard',key:`spec:${wm.key.leagueId}:${pos}`,open:!!best&&best.gainWeek>=(Number(window.FIE_UI_POLICY?.waivers?.alert_week_gain)||1),
      adv:k.kv([['Source','Sleeper weekly projections (this and the next weeks), league scoring; status from the projection feed'],['Free agents','FIEWaivers.build, top 5 at the position by horizon gain'],['Horizon',weeks.map(w=>'W'+w).join(', ')]])});
  }
  return html;
}
window.FIEV10Specialists={VERSION,board,specialistPositions};
})();

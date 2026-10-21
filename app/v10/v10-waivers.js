/* FIE UI v10 Waivers (R2 · WP2.4) — UI contract §5.12.
 *
 * Basic: best adds ranked by the full legal re-optimisation gain this week and over the horizon,
 * with the drop that loses least; per-position best-add chips. No CLAIM button and no bid in Basic
 * (acceptance A-25): the app is advisory, the decision is the manager's.
 * Expand: per-week values and gains, who the add replaces, the drop's values, league FAAB market
 * for that position and your budget. Advanced: provenance (sources, ADP, entry class, rules).
 * Sections: injured "watch / stash", last processed waiver run, FAAB budgets.
 * Numbers come from FIEWaivers.build on the same WeekModel the Lineup tab shows.
 * R3 WP3.7: injured players count again from the week Sleeper projects them back; a "fill-in until X" chip marks adds
 * whose gain ends when X returns, and Expand shows the horizon gain if X stays out.
 */
(function(){
'use strict';
const VERSION='10.5.0';
const K=()=>window.FIEV10Kit;
function bidLine(m,pos){
  const k=K();if(!m?.faab)return m?`Waiver type: ${m.waiverType===0?'rolling priority':m.waiverType===1?'reverse standings':'—'} (no FAAB bids).`:'';
  const b=m.byPosition?.[pos];
  return `${b?`Winning ${k.esc(pos)} bids this season: median $${k.esc(b.median)}, 75th percentile $${k.esc(b.p75)}, max $${k.esc(b.max)} (${b.n} claims).`:`No completed ${k.esc(pos)} FAAB claims this season yet.`} Your budget: $${k.esc(m.mine?.remaining??'–')} of $${k.esc(m.budget)} (${m.budget?Math.round(100*(m.mine?.remaining??0)/m.budget):0}%) · league median remaining $${k.esc(m.medianRemaining??'–')}.`;
}
// R5.1 · Bid range per add (FIEBids via FIEV10Data.bidAdvice): own league's winning bids rank-matched by position,
// other leagues with lower weight. Before this week's waiver run: "Bid $a–b"; after it: free agent, add now.
function bidCell(r,bids){const k=K();if(!bids)return '<span class="v10-muted">–</span>';if(bids.schedule?.ranThisWeek)return '<span class="v10-muted" title="This week\'s waiver run has processed: unclaimed players are free agents (players dropped since are on waivers again)">FA · add</span>';
  const e=bids.byPid.get(r.pid);if(!e)return '<span class="v10-muted">–</span>';return `<b>$${k.esc(e.low)}–${k.esc(e.high)}</b>`;}
function bidNote(r,bids){const k=K();if(!bids)return null;const e=bids.byPid.get(r.pid);
  const when=bids.nextRun&&!bids.schedule?.ranThisWeek?` Waivers usually process ${k.esc(k.time(bids.nextRun))}.`:bids.schedule?.ranThisWeek?' This week\'s run has processed — unclaimed players can be added now (first come); players dropped since are on waivers again.':'';
  if(!e)return `No comparable winning bid for ${k.esc(r.position)} yet.${when}`;
  return `Bid range $${k.esc(e.low)}–${k.esc(e.high)} (${Math.round(100*e.pctLow)}–${Math.round(100*e.pctHigh)} % of the budget): winning bids for the #${k.esc(e.rank)}${e.rank>=3?'+':''} ${k.esc(r.position)} of a week, ${k.esc(e.scope)} — ${k.esc(e.nOwn)} in this league, ${k.esc(e.nOther)} in your other leagues (weighted less; last 3 weeks double). p50–p80; bidding the top of the range matched or beat the winner in 80–90 % of Weeks 3–6 claims (backtest).${e.capped?' Capped at your remaining budget.':''}${when}`;}
function row(r,res,m,{lid,bids=null}){
  const k=K(),w=res.weeks;
  const dropTxt=r.drop?`${k.esc(r.drop.name)} <span class="v10-muted">${k.esc(r.drop.position)}</span>${r.drop.costly?' <span class="v10-chip v10-tier-monitor" title="High ADP — think twice">costly</span>':''}`:r.freeSpot?'<span class="v10-muted">free roster spot</span>':r.noDrop?'<span class="v10-bad">no legal drop</span>':'–';
  const sum=`<span class="v10-w-name">${k.playerLink(r,{leagueId:lid})} <span class="v10-muted">${k.esc(r.position)} · ${k.esc(r.team||'FA')}</span> ${k.statusChip(r.status)}</span>
    <span class="v10-num">${r.gainWeek===null?'–':r.gainWeek>0?`<b class="v10-good">${k.signed(r.gainWeek)}</b>`:'0.0'}</span>
    <span class="v10-num">${r.gainHorizon>0?`<b class="v10-good">${k.signed(r.gainHorizon)}</b>`:'0.0'}</span>
    <span>${dropTxt}</span><span class="v10-num">${m?.faab?bidCell(r,bids):'<span class="v10-muted">–</span>'}</span><span>${r.tier==='recommended'?k.tierChip('recommended'):''}${r.fillIn?` <span class="v10-chip v10-tier-monitor" title="The gain ends when ${k.esc(r.fillIn.name)} is back (Sleeper projects him in W${k.esc(r.fillIn.week)})">fill-in until ${k.esc(r.fillIn.name.split(' ').slice(-1)[0])} W${k.esc(r.fillIn.week)}</span>`:''}</span>`;
  const perWeek=`<table class="v10-mini"><thead><tr><th>Week</th><th class="v10-num">${k.esc(r.name.split(' ').slice(-1)[0])} proj</th><th class="v10-num">Lineup gain</th><th>Replaces</th>${r.drop?`<th class="v10-num">${k.esc(r.drop.name.split(' ').slice(-1)[0])} (drop) proj</th>`:''}</tr></thead><tbody>${w.map((x,i)=>`<tr><td>W${x}${res.baseline[i]?.published?'':' <span class="v10-muted">(not published)</span>'}</td><td class="v10-num">${k.pts(r.values[i])}</td><td class="v10-num">${r.gains[i]===null?'–':k.signed(r.gains[i])}</td><td>${r.replaces?.[i]?r.replaces[i].map(z=>k.esc(z.name)).join(', '):'–'}</td>${r.drop?`<td class="v10-num">${k.pts(r.drop.values[i])}</td>`:''}</tr>`).join('')}</tbody></table>`;
  const notes=[r.fillIn?`Fill-in: helps until ${k.esc(r.fillIn.name)} returns in W${k.esc(r.fillIn.week)} (per Sleeper's projections); in W${k.esc(r.fillIn.week)} it would add ${k.signed(r.fillIn.gainIfOut)} only if he is still out.`:null,
    r.ifOut&&Math.abs(r.ifOut.gainHorizon-r.gainHorizon)>=0.1?`If ${k.esc(r.ifOut.names.join(', '))} ${r.ifOut.names.length>1?'stay':'stays'} out: ${k.signed(r.ifOut.gainHorizon)} over W${w[0]}–W${w[w.length-1]} (other players' projections unchanged — a backup's projection still assumes the starter plays).`:null,
    r.rule?k.esc(r.rule):null,r.drop?.adp&&r.drop.adp<999?`Drop ${k.esc(r.drop.name)}: ADP ${k.esc(Math.round(r.drop.adp))}${r.drop.costly?' — a high-value player; the gain only covers the weeks shown':''}${r.drop.ros!==null&&r.drop.ros!==undefined?` · season projection ${k.pts(r.drop.ros)} pts/week`:''}.`:null,m?(m.faab?bidNote(r,bids):bidLine(m,r.position)):null].filter(Boolean);
  const body=perWeek+(notes.length?`<p class="v10-muted">${notes.join('<br>')}</p>`:'');
  const adv=k.kv([['Projection source','Sleeper weekly projections, league scoring (same as Lineup)'],['Horizon',`${w.map(x=>'W'+x).join(', ')} · ${res.weeksAvailable} published`],['ADP (add)',r.adp&&r.adp<999?k.esc(Math.round(r.adp)):'–'],['NFL entry class',r.entry??'–'],['Sleeper ID',k.esc(r.pid)],['Method','Full re-optimisation of your legal lineup per week (FIECore.LineupOptimizer); drop = least valuable legal player not needed in any week, else the best of your 4 weakest; later weeks use Sleeper\'s projection for that week (injured players count from the week he is projected back)']]);
  return k.expand(sum,body,{adv,cls:'v10-wrow',key:`w:${lid}:${r.pid}`});
}
function head(res){const w=res.weeks;return `<div class="v10-whead"><span>Player</span><span class="v10-num">Gain this week</span><span class="v10-num">Gain W${w[0]}–W${w[w.length-1]}</span><span>Suggested drop</span><span class="v10-num">Bid</span><span></span></div>`;}
/** Body HTML for the Waivers tab. data = FIEV10Data.waivers(..., {market:true}). */
function body(data,{selectedWeek=null}={}){
  const k=K(),{wm,result:res,market:m,bids=null}=data,lid=wm.key.leagueId;
  let html='';
  if(selectedWeek&&selectedWeek!==wm.key.week)html+=`<div class="v10-note">Waivers always use the current week (${wm.key.week}).</div>`;
  if(res.eliminated||res.addsDisabled)return html+k.empty(res.issues[0]);
  if(res.issues.length)html+=`<div class="v10-warn">${res.issues.map(k.esc).join(' · ')}</div>`;
  const pos=Object.entries(res.byPosition).sort((a,b)=>b[1].gainHorizon-a[1].gainHorizon);
  const chips=pos.length?`<div class="v10-row">${pos.map(([p,r])=>`<span class="v10-chip v10-poschip" title="${k.esc(r.name)}">${k.esc(p)} ${k.esc(r.name)} ${k.signed(r.gainHorizon)}</span>`).join('')}</div>`:'';
  const byAdp=res.protectedDrops.filter(x=>x.reason!=='injured'),byInj=res.protectedDrops.filter(x=>x.reason==='injured');
  const back=(res.returning||[]).filter(x=>x.week),away=(res.returning||[]).filter(x=>!x.week);
  const rules=[...(res.rules||[]),res.freeSpots>0?`${res.freeSpots} free roster spot${res.freeSpots>1?'s':''} — adds need no drop.`:null,
    byAdp.length?`${byAdp.length} players protected from drop suggestions (dynasty ADP ≤ ${window.FIE_UI_POLICY?.waivers?.dynasty_protect_adp??150}): ${byAdp.map(x=>k.esc(x.name)).join(', ')}.`:null,
    byInj.length?`Injured starters never suggested as drops: ${byInj.map(x=>`${k.esc(x.name)} (${k.pts(x.healthy)} pts/wk when healthy)`).join(', ')}.`:null,
    back.length?`Back per Sleeper's projections (counted from that week): ${back.map(x=>`${k.esc(x.name)} W${k.esc(x.week)}${x.inReserve?' — in your IR slot, activating him needs a roster spot':''}`).join('; ')}.`:null,
    away.length?`Not projected back within W${res.weeks[0]}–W${res.weeks[res.weeks.length-1]}: ${away.map(x=>k.esc(x.name)).join(', ')}.`:null,
    res.weeksAvailable<res.weeks.length?`Projections published for ${res.weeksAvailable} of ${res.weeks.length} weeks.`:null].filter(Boolean);
  // At most 3 per position so one streamable position (D/ST, K) cannot crowd the list; chips show the rest.
  const perPos={},positive=res.rows.filter(r=>r.gainHorizon>0).filter(r=>(perPos[r.position]=(perPos[r.position]||0)+1)<=3).slice(0,15);
  html+=`<section class="v10-card"><h2>Best adds <span class="v10-muted">lineup gain this week and W${res.weeks[0]}–W${res.weeks[res.weeks.length-1]}</span></h2>${chips}${rules.length?`<p class="v10-muted">${rules.join('<br>')}</p>`:''}
    ${positive.length?head(res)+positive.map(r=>row(r,res,m,{lid,bids})).join(''):k.empty('No free agent improves your projected lineup in these weeks.')}</section>`;
  if(!positive.length&&res.rows.length){const depth=res.rows.slice(0,8);html+=k.expand(`<b>Best available by projection</b> <span class="v10-muted">no lineup gain — depth only</span>`,head(res)+depth.map(r=>row(r,res,m,{lid,bids})).join(''),{cls:'v10-card',key:`depth:${lid}`});}
  if(res.watch.length)html+=k.expand(`<b>Injured — watch${wm.format.dynasty?' / stash':''}</b> <span class="v10-muted">${res.watch.length}</span>`,`<p class="v10-muted">Can't play this week; never shown as an add. STASH = dynasty with a free legal reserve slot.</p>${head(res)}${res.watch.slice(0,10).map(r=>row({...r,tier:'none'},res,m,{lid,bids})).join('')}`,{cls:'v10-card',key:`watch:${lid}`});
  if(m){
    const table=items=>`<table class="v10-table"><thead><tr><th>Team</th><th>Added</th><th>Dropped</th>${m.faab?'<th class="v10-num">Bid</th>':''}<th>Result</th></tr></thead><tbody>${items.map(t=>`<tr class="${t.mine?'v10-me':''}"><td>${k.esc(t.team)}${t.mine?' (you)':''}</td><td>${t.adds.map(a=>`${k.esc(a.name)} <span class="v10-muted">${k.esc(a.position||'')}</span>`).join(', ')}</td><td>${t.drops.map(a=>k.esc(a.name)).join(', ')||'–'}</td>${m.faab?`<td class="v10-num">${t.bid===null?'–':'$'+k.esc(t.bid)}</td>`:''}<td>${t.status==='complete'?'won':`<span class="v10-muted" title="${k.esc(t.note||'')}">${k.esc(t.status)}</span>`}</td></tr>`).join('')}</tbody></table>`;
    if(m.weekRuns){const runs=m.weekRuns,n=runs.reduce((s,r)=>s+r.items.length,0);
      html+=k.expand(`<b>This week's waiver runs</b> <span class="v10-muted">${runs.length?`${runs.length} run${runs.length>1?'s':''} · ${n} claims since the last game of Week ${k.esc(wm.key.week-1)}`:'none yet this week'}</span>`,
        runs.length?runs.map((r,i)=>`<h3>${i===0?'Main run':'Run'} · ${k.esc(k.time(r.at))} <span class="v10-muted">${r.items.length} claims · ${r.items.filter(t=>t.status==='complete').length} won</span></h3>${table(r.items)}`).join(''):k.empty('No waiver claims processed since the last game of last week.'),{cls:'v10-card',key:`run:${lid}`});}
    else{const run=m.lastRun||[];
      html+=k.expand(`<b>Last waiver run</b> <span class="v10-muted">${m.lastRunAt?k.esc(k.time(m.lastRunAt)):'none yet'} · ${run.length} claims</span>`,run.length?table(run):k.empty('No processed waiver claims this season.'),{cls:'v10-card',key:`run:${lid}`});}
    if(m.faab)html+=k.expand(`<b>FAAB budgets</b> <span class="v10-muted">you: $${k.esc(m.mine?.remaining??'–')} of $${k.esc(m.budget)}</span>`,
      `<table class="v10-table"><thead><tr><th>Team</th><th class="v10-num">Remaining</th><th class="v10-num" title="Points per scored week (Sleeper points for ÷ weeks played)">Avg pts / week</th><th class="v10-num">Rank W${k.esc(wm.key.week-1)}</th></tr></thead><tbody>${m.budgets.filter(b=>b.active||!wm.format.chopped).map(b=>`<tr class="${b.mine?'v10-me':''}"><td>${k.esc(b.team)}${b.mine?' (you)':''}</td><td class="v10-num">$${k.esc(b.remaining)}</td><td class="v10-num">${b.avgPoints===null?'–':k.pts(b.avgPoints,1)}</td><td class="v10-num">${b.lastWeekRank?`${k.esc(b.lastWeekRank)}/${k.esc(b.lastWeekTeams)}`:'–'}</td></tr>`).join('')}</tbody></table>
       <p class="v10-muted">Strong teams (high average, top ranks) with money left are the likeliest big bidders; survival / playoff odds per team follow with the v10 season simulation (R6).</p>`,{cls:'v10-card',key:`faab:${lid}`});
  }
  return html;
}
window.FIEV10Waivers={VERSION,body};
})();

/* FIE UI v10 Waivers (R2 · WP2.4) — UI contract §5.12.
 *
 * Basic: best adds ranked by the full legal re-optimisation gain this week and over the horizon,
 * with the drop that loses least; per-position best-add chips. No CLAIM button and no bid in Basic
 * (acceptance A-25): the app is advisory, the decision is the manager's.
 * Expand: per-week values and gains, who the add replaces, the drop's values, league FAAB market
 * for that position and your budget. Advanced: provenance (sources, ADP, entry class, rules).
 * Sections: injured "watch / stash", last processed waiver run, FAAB budgets.
 * Numbers come from FIEWaivers.build on the same WeekModel the Lineup tab shows.
 */
(function(){
'use strict';
const VERSION='10.2.0';
const K=()=>window.FIEV10Kit;
function bidLine(m,pos){
  const k=K();if(!m?.faab)return m?`Waiver type: ${m.waiverType===0?'rolling priority':m.waiverType===1?'reverse standings':'—'} (no FAAB bids).`:'';
  const b=m.byPosition?.[pos];
  return `${b?`Winning ${k.esc(pos)} bids this season: median $${k.esc(b.median)}, 75th percentile $${k.esc(b.p75)}, max $${k.esc(b.max)} (${b.n} claims).`:`No completed ${k.esc(pos)} FAAB claims this season yet.`} Your budget: $${k.esc(m.mine?.remaining??'–')} of $${k.esc(m.budget)} (${m.budget?Math.round(100*(m.mine?.remaining??0)/m.budget):0}%) · league median remaining $${k.esc(m.medianRemaining??'–')}.`;
}
function row(r,res,m,{lid}){
  const k=K(),w=res.weeks;
  const dropTxt=r.drop?`${k.esc(r.drop.name)} <span class="v10-muted">${k.esc(r.drop.position)}</span>${r.drop.costly?' <span class="v10-chip v10-tier-monitor" title="High ADP — think twice">costly</span>':''}`:r.freeSpot?'<span class="v10-muted">free roster spot</span>':r.noDrop?'<span class="v10-bad">no legal drop</span>':'–';
  const sum=`<span class="v10-w-name">${k.playerLink(r,{leagueId:lid})} <span class="v10-muted">${k.esc(r.position)} · ${k.esc(r.team||'FA')}</span> ${k.statusChip(r.status)}</span>
    <span class="v10-num">${r.gainWeek===null?'–':r.gainWeek>0?`<b class="v10-good">${k.signed(r.gainWeek)}</b>`:'0.0'}</span>
    <span class="v10-num">${r.gainHorizon>0?`<b class="v10-good">${k.signed(r.gainHorizon)}</b>`:'0.0'}</span>
    <span>${dropTxt}</span><span>${r.tier==='recommended'?k.tierChip('recommended'):''}</span>`;
  const perWeek=`<table class="v10-mini"><thead><tr><th>Week</th><th class="v10-num">${k.esc(r.name.split(' ').slice(-1)[0])} proj</th><th class="v10-num">Lineup gain</th><th>Replaces</th>${r.drop?`<th class="v10-num">${k.esc(r.drop.name.split(' ').slice(-1)[0])} (drop) proj</th>`:''}</tr></thead><tbody>${w.map((x,i)=>`<tr><td>W${x}${res.baseline[i]?.published?'':' <span class="v10-muted">(not published)</span>'}</td><td class="v10-num">${k.pts(r.values[i])}</td><td class="v10-num">${r.gains[i]===null?'–':k.signed(r.gains[i])}</td><td>${r.replaces?.[i]?r.replaces[i].map(z=>k.esc(z.name)).join(', '):'–'}</td>${r.drop?`<td class="v10-num">${k.pts(r.drop.values[i])}</td>`:''}</tr>`).join('')}</tbody></table>`;
  const notes=[r.rule?k.esc(r.rule):null,r.drop?.adp&&r.drop.adp<999?`Drop ${k.esc(r.drop.name)}: ADP ${k.esc(Math.round(r.drop.adp))}${r.drop.costly?' — a high-value player; the gain only covers the weeks shown':''}${r.drop.ros!==null&&r.drop.ros!==undefined?` · season projection ${k.pts(r.drop.ros)} pts/week`:''}.`:null,m?bidLine(m,r.position):null].filter(Boolean);
  const body=perWeek+(notes.length?`<p class="v10-muted">${notes.join('<br>')}</p>`:'');
  const adv=k.kv([['Projection source','Sleeper weekly projections, league scoring (same as Lineup)'],['Horizon',`${w.map(x=>'W'+x).join(', ')} · ${res.weeksAvailable} published`],['ADP (add)',r.adp&&r.adp<999?k.esc(Math.round(r.adp)):'–'],['NFL entry class',r.entry??'–'],['Sleeper ID',k.esc(r.pid)],['Method','Full re-optimisation of your legal lineup per week (FIECore.LineupOptimizer); drop = least valuable legal player not needed in any week, else the best of your 4 weakest']]);
  return k.expand(sum,body,{adv,cls:'v10-wrow',key:`w:${lid}:${r.pid}`});
}
function head(res){const w=res.weeks;return `<div class="v10-whead"><span>Player</span><span class="v10-num">Gain this week</span><span class="v10-num">Gain W${w[0]}–W${w[w.length-1]}</span><span>Suggested drop</span><span></span></div>`;}
/** Body HTML for the Waivers tab. data = FIEV10Data.waivers(..., {market:true}). */
function body(data,{selectedWeek=null}={}){
  const k=K(),{wm,result:res,market:m}=data,lid=wm.key.leagueId;
  let html='';
  if(selectedWeek&&selectedWeek!==wm.key.week)html+=`<div class="v10-note">Waivers always use the current week (${wm.key.week}).</div>`;
  if(res.eliminated)return html+k.empty(res.issues[0]);
  if(res.issues.length)html+=`<div class="v10-warn">${res.issues.map(k.esc).join(' · ')}</div>`;
  const pos=Object.entries(res.byPosition).sort((a,b)=>b[1].gainHorizon-a[1].gainHorizon);
  const chips=pos.length?`<div class="v10-row">${pos.map(([p,r])=>`<span class="v10-chip v10-poschip" title="${k.esc(r.name)}">${k.esc(p)} ${k.esc(r.name)} ${k.signed(r.gainHorizon)}</span>`).join('')}</div>`:'';
  const rules=[...(res.rules||[]),res.freeSpots>0?`${res.freeSpots} free roster spot${res.freeSpots>1?'s':''} — adds need no drop.`:null,res.protectedDrops.length?`${res.protectedDrops.length} players protected from drop suggestions (dynasty ADP ≤ ${window.FIE_UI_POLICY?.waivers?.dynasty_protect_adp??150}): ${res.protectedDrops.map(x=>k.esc(x.name)).join(', ')}.`:null,
    res.weeksAvailable<res.weeks.length?`Projections published for ${res.weeksAvailable} of ${res.weeks.length} weeks.`:null].filter(Boolean);
  // At most 3 per position so one streamable position (D/ST, K) cannot crowd the list; chips show the rest.
  const perPos={},positive=res.rows.filter(r=>r.gainHorizon>0).filter(r=>(perPos[r.position]=(perPos[r.position]||0)+1)<=3).slice(0,15);
  html+=`<section class="v10-card"><h2>Best adds <span class="v10-muted">lineup gain this week and W${res.weeks[0]}–W${res.weeks[res.weeks.length-1]}</span></h2>${chips}${rules.length?`<p class="v10-muted">${rules.join('<br>')}</p>`:''}
    ${positive.length?head(res)+positive.map(r=>row(r,res,m,{lid})).join(''):k.empty('No free agent improves your projected lineup in these weeks.')}</section>`;
  if(!positive.length&&res.rows.length){const depth=res.rows.slice(0,8);html+=k.expand(`<b>Best available by projection</b> <span class="v10-muted">no lineup gain — depth only</span>`,head(res)+depth.map(r=>row(r,res,m,{lid})).join(''),{cls:'v10-card',key:`depth:${lid}`});}
  if(res.watch.length)html+=k.expand(`<b>Injured — watch${wm.format.dynasty?' / stash':''}</b> <span class="v10-muted">${res.watch.length}</span>`,`<p class="v10-muted">Can't play this week; never shown as an add. STASH = dynasty with a free legal reserve slot.</p>${head(res)}${res.watch.slice(0,10).map(r=>row({...r,tier:'none'},res,m,{lid})).join('')}`,{cls:'v10-card',key:`watch:${lid}`});
  if(m){
    const run=m.lastRun||[];
    html+=k.expand(`<b>Last waiver run</b> <span class="v10-muted">${m.lastRunAt?k.esc(k.time(m.lastRunAt)):'none yet'} · ${run.length} claims</span>`,
      run.length?`<table class="v10-table"><thead><tr><th>Team</th><th>Added</th><th>Dropped</th>${m.faab?'<th class="v10-num">Bid</th>':''}<th>Result</th></tr></thead><tbody>${run.map(t=>`<tr class="${t.mine?'v10-me':''}"><td>${k.esc(t.team)}${t.mine?' (you)':''}</td><td>${t.adds.map(a=>`${k.esc(a.name)} <span class="v10-muted">${k.esc(a.position||'')}</span>`).join(', ')}</td><td>${t.drops.map(a=>k.esc(a.name)).join(', ')||'–'}</td>${m.faab?`<td class="v10-num">${t.bid===null?'–':'$'+k.esc(t.bid)}</td>`:''}<td>${t.status==='complete'?'won':k.esc(t.status)}</td></tr>`).join('')}</tbody></table>`:k.empty('No processed waiver claims this season.'),{cls:'v10-card',key:`run:${lid}`});
    if(m.faab)html+=k.expand(`<b>FAAB budgets</b> <span class="v10-muted">you: $${k.esc(m.mine?.remaining??'–')} of $${k.esc(m.budget)}</span>`,
      `<table class="v10-table"><thead><tr><th>Team</th><th class="v10-num">Remaining</th><th class="v10-num">Spent</th></tr></thead><tbody>${m.budgets.filter(b=>b.active||!wm.format.chopped).map(b=>`<tr class="${b.mine?'v10-me':''}"><td>${k.esc(b.team)}${b.mine?' (you)':''}</td><td class="v10-num">$${k.esc(b.remaining)}</td><td class="v10-num">$${k.esc(b.used)}</td></tr>`).join('')}</tbody></table>
       <p class="v10-muted">Winning bids by position: ${Object.entries(m.byPosition).map(([p,b])=>`${k.esc(p)} median $${k.esc(b.median)} (n=${b.n})`).join(' · ')||'none yet'}.</p>`,{cls:'v10-card',key:`faab:${lid}`});
  }
  return html;
}
window.FIEV10Waivers={VERSION,body};
})();

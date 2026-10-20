/* FIE UI v10 Research Lab v1 (R3 · WP3.1) — UI contract §7.3.
 *
 * Display-only, labelled "research" where it shows research artifacts; nothing here changes a projection,
 * lineup, recommendation or rank (guide §3.2). Route: #/lab/<state|eval|forecasts|rankings|docs>?league=<id>.
 *
 *   Model state  — per league: active projection source per position (from the WeekModels), governed FIE rows,
 *                  the research pipeline's per-position decision, the weekly research view's status / blockers.
 *   Evaluations  — last completed week: projection error by position for every rostered player of a league in
 *                  league scoring (Sleeper projection re-scored vs Sleeper players_points), biggest misses; and the
 *                  four-row review across all leagues (submitted / best by projection / hindsight / bench points).
 *   Forecasts    — this week by game: active value, Sleeper's own published number, last-4 average (league scoring).
 *   Rankings     — this week and the horizon in league scoring, beside the FIE season board p50 (research,
 *                  preseason pipeline run), joined by Sleeper ID.
 *   Documents    — the league's research artifacts (status, dates, raw JSON) and the classic Lab for detail.
 */
(function(){
'use strict';
const VERSION='10.5.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
const TABS=[['state','Model state'],['eval','Evaluations'],['forecasts','Forecasts'],['rankings','Rankings'],['docs','Documents']];
let token=0;
const cache=new Map();
async function getJson(url){if(cache.has(url))return cache.get(url);const p=window.FIEDataClient.json(url,{sourceId:'v10-lab',ttlMs:30*60e3}).catch(()=>null);cache.set(url,p);return p;}
const rp=id=>`/data/research/leagues/${encodeURIComponent(id)}/performance/2026/research_pipeline`;
function href(tab,lid){return `#/lab/${tab}${lid?`?league=${encodeURIComponent(lid)}`:''}`;}
function nav(tab,lid){const k=K();return `<nav class="v10-tabs">${TABS.map(([t,l])=>`<a href="${href(t,lid)}" class="${t===tab?'active':''}">${k.esc(l)}</a>`).join('')}<span class="v10-tabs-sep"></span>${lid?`<a class="v10-classic-link" href="#/classic/${encodeURIComponent(lid)}/lab" title="Classic Research Lab: model detail, validation">Classic Lab ↗</a>`:''}</nav>`;}
async function leaguePicker(lid,tab){const k=K(),list=await D().leagues();return `<select data-v10-lab-league aria-label="League">${list.map(l=>`<option value="${k.esc(l.id)}"${String(l.id)===String(lid)?' selected':''}>${k.esc(l.name)}</option>`).join('')}</select>`;}
const nameOf=(wm,cat)=>pid=>wm.player(pid)?.name||cat.get(String(pid))?.full_name||pid;
const posOf=(wm,cat)=>pid=>wm.player(pid)?.position||String(cat.get(String(pid))?.position||'').toUpperCase();

async function state(lid){
  const k=K(),port=await D().portfolio({withWaivers:false,withTx:false}),wms=port.map(x=>x.wm).filter(Boolean);
  const season=wms[0]?.key.season||2026,week=wms[0]?.key.week||1;
  const [view,gov]=await Promise.all([getJson(`/data/research/prospective/weekly-research-view/${season}/week_${String(week).padStart(2,'0')}.json`),getJson('/data/research/governance/active_release.json')]);
  // Research-pipeline artifacts exist only for leagues the pipeline has run for (no index is served): fetch the
  // selected league's readiness only, so the Lab never fires 23 requests of which some 404.
  const sel=lid||wms[0]?.key.leagueId,readiness=new Map([[String(sel),await getJson(`${rp(sel)}/readiness.json`)]]);
  const rows=window.FIELab.modelState({wms,readiness,researchView:view});
  const governed=rows.reduce((s,r)=>s+r.governed,0),players=rows.reduce((s,r)=>s+r.players,0);
  const srcText=c=>Object.entries(c).map(([pos,x])=>`${k.esc(pos)}: ${Object.entries(x).map(([t,n])=>`${t==='SLEEPER'?'Sleeper':t==='FIE_GOVERNED'||t==='FIE_WEEKLY'?'<b>FIE</b>':t==='BYE'?'bye':t.toLowerCase()} ${n}`).join(', ')}`).join(' · ');
  let html=`<section class="v10-card"><h2>Model state <span class="v10-muted">Week ${k.esc(week)} · research display only</span></h2>
    <p>${governed?`<b>${governed}</b> of ${players} rostered players use a governed FIE projection.`:`<b>Sleeper-only mode:</b> 0 of ${players} rostered players in ${rows.length} leagues use a governed FIE projection — every number in the app is Sleeper's weekly projection re-scored to your league.`}
    ${view?` Weekly research view: <b>${k.esc((view.blockers||[]).join(', ')||'no blocker')}</b> (${view.leagues?.filter(l=>l.forecast_eligible).length||0} of ${view.leagues?.length||0} leagues forecast-eligible).`:' Weekly research view: not available.'}
    ${gov?` Runtime model activation: <b>${gov.runtime_enabled?'on':'off'}</b> (active build ${k.esc(gov.active_build||'–')}, fallback ${k.esc(gov.fallback||'–')}).`:''}</p>
    <table class="v10-table"><thead><tr><th>League</th><th>Active sources (your players)</th><th>Weekly research</th></tr></thead><tbody>
    ${rows.map(r=>`<tr${String(r.leagueId)===String(sel)?' class="v10-me"':''}><td><a href="${href('state',r.leagueId)}">${k.esc(r.name)}</a></td><td class="v10-small">${srcText(r.counts)}</td><td class="v10-small">${r.research?`${k.esc(r.research.status)}${r.research.blockers.length?` <span class="v10-muted">(${k.esc(r.research.blockers.join(', '))})</span>`:''}`:'–'}</td></tr>`).join('')}</tbody></table></section>`;
  const one=rows.find(r=>String(r.leagueId)===String(sel));
  html+=`<section class="v10-card"><h2>Research pipeline <span class="v10-muted">${k.esc(one?.name||sel)} · pick a league above or in the table</span></h2>${one?.pipeline?.decisions?`<p>Status <b>${k.esc(one.pipeline.status||'–')}</b>, run ${k.esc(String(one.pipeline.generatedAt||'').slice(0,10))}.</p><table class="v10-table"><thead><tr><th>Position</th><th>Production model</th><th>Decision</th><th>Best challenger</th><th>Reason</th></tr></thead><tbody>${Object.entries(one.pipeline.decisions).map(([pos,d])=>`<tr><td>${k.esc(pos)}</td><td>${k.esc(d.model||'–')}</td><td>${k.esc(d.decision||'–')}</td><td>${k.esc(d.challenger||'–')}</td><td class="v10-small">${k.esc(String(d.reason||'').replace(/_/g,' '))}</td></tr>`).join('')}</tbody></table><p class="v10-muted">These decisions govern the research season board (Rankings); weekly numbers stay Sleeper until a weekly gate opens.</p>`:k.empty('No research-pipeline run is served for this league.')}</section>`;
  return html;
}

async function evals(lid,wsel=null){
  const k=K(),entry=(await D().leagues()).find(x=>String(x.id)===String(lid));if(!entry)return k.empty('Pick a league.');
  const cur=await D().model(entry),last=cur.key.week-1,week=wsel&&wsel>=1&&wsel<=last?Number(wsel):last;if(week<1)return k.empty('No completed week yet.');
  const picker=`<select data-v10-lab-week aria-label="Week">${Array.from({length:last},(_,j)=>j+1).reverse().map(x=>`<option value="${x}"${x===week?' selected':''}>Week ${x}</option>`).join('')}</select>`;
  const [proj,mm,cat]=await Promise.all([D().projections(cur.key.season,week),D().matchups(lid,week),D().catalog()]);
  const ev=window.FIELab.evaluate({projRows:proj.rows,matchups:mm,scoring:cur.league.scoring,positionOf:posOf(cur,cat),nameOf:nameOf(cur,cat)});
  let html=`<section class="v10-card"><h2>Projection accuracy <span class="v10-muted">${k.esc(entry.name)} · league scoring · rostered players projected ≥ ${ev.minProjection}</span></h2><div class="v10-row">${picker}</div>
    ${ev.n?`<table class="v10-table"><thead><tr><th>Position</th><th class="v10-num">Players</th><th class="v10-num">Mean abs. error</th><th class="v10-num">Bias (actual − proj)</th><th class="v10-num">RMSE</th></tr></thead><tbody>
    ${[...ev.byPosition,{position:'All',...ev.overall}].map(r=>`<tr${r.position==='All'?' class="v10-me"':''}><td>${k.esc(r.position)}</td><td class="v10-num">${r.n}</td><td class="v10-num">${k.pts(r.mae)}</td><td class="v10-num">${k.signed(r.bias)}</td><td class="v10-num">${k.pts(r.rmse)}</td></tr>`).join('')}</tbody></table>
    <p class="v10-muted">Active source = Sleeper in every league (Model state), so this is also the accuracy of the numbers the app used. Projection = Sleeper's Week ${k.esc(week)} projection as published now, re-scored to this league; actual = Sleeper's league-scored points; did not play = 0.${ev.n&&ev.scored&&week===last?' If games of this week are still being played, the numbers are partial.':''}</p>`:k.empty(ev.scored===false?`Sleeper has not scored Week ${week} for this league yet.`:'No rostered player with a projection this week.')}</section>`;
  if(ev.misses.length)html+=k.expand('<b>Biggest misses</b>',`<table class="v10-table"><thead><tr><th>Player</th><th class="v10-num">Projected</th><th class="v10-num">Actual</th><th class="v10-num">Error</th></tr></thead><tbody>${ev.misses.map(m=>`<tr><td>${k.playerLink(m,{leagueId:lid})} <span class="v10-muted">${k.esc(m.position)}</span></td><td class="v10-num">${k.pts(m.projected)}</td><td class="v10-num">${k.pts(m.actual,2)}</td><td class="v10-num ${m.error>=0?'v10-good':'v10-bad'}">${k.signed(m.error)}</td></tr>`).join('')}</tbody></table>`,{cls:'v10-card',key:`lab-miss:${lid}:${week}`});
  html+=`<section class="v10-card"><h2>Your lineups in Week ${k.esc(week)}, all leagues</h2><div id="v10LabReview"><button class="v10-btn" data-v10-lab-review="${k.esc(week)}">Review all leagues</button> <span class="v10-muted">Loads each league's Week ${k.esc(week)} matchups (≈2 requests per league).</span></div></section>`;
  return html;
}
async function reviewAll(week,el){
  const k=K(),list=await D().leagues(),rows=[];el.innerHTML='<div class="v10-loading">Reviewing…</div>';
  let i=0;await Promise.all(Array.from({length:4},async()=>{while(i<list.length){const e=list[i++];try{const wm=await D().model(e,{week});const rv=window.FIEReview.build({wm,matchups:await D().matchups(e.id,week)});if(rv.available)rows.push({name:wm.entry.name,rv});}catch{}}}));
  rows.sort((a,b)=>a.name.localeCompare(b.name));
  const sum=f=>rows.reduce((s,r)=>s+(f(r.rv)||0),0);
  el.innerHTML=rows.length?`<table class="v10-table"><thead><tr><th>League</th><th class="v10-num">Submitted</th><th class="v10-num">By projection</th><th class="v10-num">Hindsight</th><th class="v10-num">Bench pts left</th><th class="v10-num">Efficiency</th></tr></thead><tbody>
    ${rows.map(({name,rv})=>`<tr><td>${k.esc(name)}</td><td class="v10-num">${k.pts(rv.submitted.points,2)}</td><td class="v10-num">${rv.bestBall?'–':k.pts(rv.projectionBest.points,2)}</td><td class="v10-num">${k.pts(rv.hindsight.points,2)}</td><td class="v10-num">${rv.bestBall?'–':k.pts(rv.leftOnBench,2)}</td><td class="v10-num">${rv.bestBall?'–':k.pct(rv.efficiency)}</td></tr>`).join('')}
    <tr class="v10-me"><td>All ${rows.length} leagues</td><td class="v10-num">${k.pts(sum(r=>r.submitted.points),1)}</td><td class="v10-num">${k.pts(sum(r=>r.bestBall?r.submitted.points:r.projectionBest.points),1)}</td><td class="v10-num">${k.pts(sum(r=>r.hindsight.points),1)}</td><td class="v10-num">${k.pts(sum(r=>r.bestBall?0:r.leftOnBench),1)}</td><td></td></tr></tbody></table>
    <p class="v10-muted">"By projection" = what starting the best lineup by Sleeper's projection would have scored (Best Ball: Sleeper picks the lineup). "Submitted − by projection" across leagues is the cost (or gain) of deviating from the projections.</p>`:k.empty('No scored matchups for that week.');
}
// R5.7 · Week picker over the current week and the next two: a week is selectable once Sleeper has published projections
// for it (FIE research forecasts stay blocked — Model state). Last-4 averages always end at the current week.
async function forecasts(lid,week=null){
  const k=K(),entry=(await D().leagues()).find(x=>String(x.id)===String(lid));if(!entry)return k.empty('Pick a league.');
  const cur=await D().model(entry),i=await D().inputs(entry),live=cur.key.week;
  const opts=await Promise.all([0,1,2].map(d=>live+d).filter(x=>x<=18).map(async x=>({week:x,published:x===live||((await D().projections(cur.key.season,x).catch(()=>null))?.rows?.size>0)})));
  const sel=week&&opts.some(o=>o.week===week&&o.published)?week:live,wm=sel===live?cur:await D().model(entry,{week:sel}),w=sel;
  const picker=`<select data-v10-lab-fweek aria-label="Week">${opts.map(o=>`<option value="${o.week}"${o.week===sel?' selected':''}${o.published?'':' disabled'}>Week ${o.week}${o.week===live?' · live':o.published?'':' · not published yet'}</option>`).join('')}</select>`;
  const past=await Promise.all([1,2,3,4].map(d=>w-d).filter(x=>x>=1).map(async x=>({week:x,matchups:await D().matchups(lid,x)})));
  const ids=new Set();for(const r of i.rosters||[])for(const id of r.players||[])ids.add(String(id));
  const l4=window.FIELab.lastN({weeks:past,pids:ids,n:4});
  const games=new Map();
  for(const id of ids){const p=wm.player(id);if(!p||!(p.active.value>=3)||!p.game?.opp)continue;const key=p.game.gameId||`${[p.team,p.game.opp].sort().join('-')}`;if(!games.has(key))games.set(key,{kickoff:p.game.kickoff,label:`${[p.team,p.game.opp].sort().join(' – ')}`,players:[]});games.get(key).players.push(p);}
  const list=[...games.values()].sort((a,b)=>(a.kickoff||0)-(b.kickoff||0));
  const own=wm.ownerOf;
  return `<section class="v10-card"><h2>Forecasts, Week ${k.esc(w)} ${picker} <span class="v10-muted">${k.esc(entry.name)} · rostered players projected ≥ 3 · league scoring</span></h2>
    <p class="v10-muted">Active = the value the app uses (Sleeper re-scored to this league). Sleeper = Sleeper's own published total (its default scoring). Last 4 = average league-scored points in the last ${past.length} weeks this player was rostered here (Sleeper matchups; 0 if he did not play). FIE research (M10): not shown — the weekly research view is blocked (Model state).</p>
    ${list.map(g=>k.expand(`<b>${k.esc(g.label)}</b> <span class="v10-muted">${k.esc(k.time(g.kickoff))} · ${g.players.length} players</span>`,
      `<table class="v10-table"><thead><tr><th>Player</th><th>Owner</th><th class="v10-num">Active</th><th class="v10-num">Sleeper</th><th class="v10-num">Last 4</th><th class="v10-num">Active − last 4</th></tr></thead><tbody>${g.players.sort((a,b)=>b.active.value-a.active.value).map(p=>{const x=l4.get(p.pid),pub=p.alternatives?.[0]?.value??p.active.value,o=own(p.pid);
        return `<tr${o?.me?' class="v10-me"':''}><td>${k.playerLink(p,{leagueId:lid})} <span class="v10-muted">${k.esc(p.position)} · ${k.esc(p.team)}</span> ${k.statusChip(p.status)}</td><td class="v10-small">${o?.me?'yours':k.esc(o?.name||'')}</td><td class="v10-num">${k.pts(p.status.unavailable?0:p.active.value)}</td><td class="v10-num">${k.pts(pub)}</td><td class="v10-num">${x?`${k.pts(x.avg)} <span class="v10-muted v10-small">(${x.games})</span>`:'–'}</td><td class="v10-num">${x?k.signed((p.status.unavailable?0:p.active.value)-x.avg):'–'}</td></tr>`;}).join('')}</tbody></table>`,{cls:'v10-labgame',key:`lab-g:${lid}:${g.label}`})).join('')||k.empty('No games found.')}</section>`;
}
async function rankings(lid,pos){
  const k=K(),entry=(await D().leagues()).find(x=>String(x.id)===String(lid));if(!entry)return k.empty('Pick a league.');
  const i=await D().inputs(entry),wm=i.wm,pl=window.FIETeamViews.players(i),board=await getJson(`${rp(lid)}/rankings.json`),ready=await getJson(`${rp(lid)}/readiness.json`);
  const bmap=new Map(((board?.players)||[]).map(b=>[String(b.sleeper_id||String(b.player_id).replace(/^DST:/,'')),b]));
  const positions=[...new Set(pl.rows.map(r=>r.position))];const P=pos&&positions.includes(pos)?pos:(positions.includes('RB')?'RB':positions[0]);
  const rows=pl.rows.filter(r=>r.position===P).sort((a,b)=>(b.week??0)-(a.week??0)).slice(0,40);
  const w=pl.weeks;
  return `<section class="v10-card"><h2>Rankings <span class="v10-muted">${k.esc(entry.name)} · league scoring</span></h2>
    <div class="v10-row">${positions.map(p=>`<a class="v10-chip v10-poschip${p===P?' v10-chip-on':''}" href="${href('rankings',lid)}&pos=${encodeURIComponent(p)}">${k.esc(p)}</a>`).join(' ')}</div>
    <table class="v10-table"><thead><tr><th class="v10-num">#</th><th>Player</th><th class="v10-num">W${w[0]}</th><th class="v10-num">W${w[0]}–W${w[w.length-1]}</th><th class="v10-num" title="FIE season board p50 (research, preseason run)">Season p50 <span class="v10-muted">research</span></th><th class="v10-num">Board rank</th><th>Owner</th></tr></thead><tbody>
    ${rows.map((r,j)=>{const b=bmap.get(r.pid);return `<tr${r.mine?' class="v10-me"':''}><td class="v10-num">${j+1}</td><td>${k.playerLink(r,{leagueId:lid})} <span class="v10-muted">${k.esc(r.team||'')}</span> ${k.statusChip(r.status)}</td><td class="v10-num">${k.pts(r.week)}</td><td class="v10-num">${pl.published.every(Boolean)?k.pts(r.next):`${k.pts(r.next)} <span class="v10-muted v10-small">(${pl.published.filter(Boolean).length} wk)</span>`}</td><td class="v10-num">${b&&(b.p50??b.projection_points)!=null?k.pts(b.p50??b.projection_points,0):'–'}</td><td class="v10-num">${b?.position_rank?`${k.esc(P)}${Math.round(b.position_rank)}`:'–'}</td><td class="v10-small">${r.fa?'free agent':r.mine?'yours':k.esc(r.owner?.name||'')}</td></tr>`;}).join('')}</tbody></table>
    <p class="v10-muted">Weekly columns = Sleeper weekly projections in league scoring (same as Lineup/Players). Season p50 and board rank = the FIE league season board from the research pipeline run of ${k.esc(String(ready?.pipeline?.generated_at||'–').slice(0,10))} (${k.esc(board?.canonical_rank_source||'research')}), research only, joined by Sleeper ID; it is a full-season value and not refreshed weekly.</p></section>`;
}
async function docs(lid){
  const k=K(),entry=(await D().leagues()).find(x=>String(x.id)===String(lid));if(!entry)return k.empty('Pick a league.');
  const wm=await D().model(entry),base=rp(lid),files=[['readiness.json','Model readiness and per-position decisions'],['report-summary.json','Research report summary (outliers, sleepers, challengers)'],['rankings.json','League season board (research)']];
  const meta=await Promise.all(files.map(async([f,label])=>{const j=await getJson(`${base}/${f}`);return{f,label,ok:!!j,at:j?.pipeline?.generated_at||j?.generated_at||null,schema:j?.schema||null,status:j?.pipeline?.status||j?.headline?.pipeline_status||null};}));
  const week=`/data/research/prospective/weekly-research-view/${wm.key.season}/week_${String(wm.key.week).padStart(2,'0')}.json`,wv=await getJson(week);
  return `<section class="v10-card"><h2>Documents <span class="v10-muted">${k.esc(entry.name)} · research artifacts served with this build</span></h2>
    <table class="v10-table"><thead><tr><th>Document</th><th>Status</th><th>Generated</th><th>Raw</th></tr></thead><tbody>
    ${meta.map(m=>`<tr><td>${k.esc(m.label)}<div class="v10-muted v10-small">${k.esc(m.schema||'')}</div></td><td>${m.ok?k.esc(m.status||'available'):'<span class="v10-muted">not available</span>'}</td><td>${k.esc(String(m.at||'–').slice(0,16).replace('T',' '))}</td><td>${m.ok?`<a href="${k.esc(`${base}/${m.f}`)}" target="_blank" rel="noopener">JSON ↗</a>`:''}</td></tr>`).join('')}
    <tr><td>Weekly research view, Week ${k.esc(wm.key.week)}<div class="v10-muted v10-small">${k.esc(wv?.schema||'')}</div></td><td>${wv?k.esc((wv.blockers||[]).join(', ')||'ready'):'<span class="v10-muted">not available</span>'}</td><td>${k.esc(String(wv?.generated_at||'–').slice(0,16).replace('T',' '))}</td><td>${wv?`<a href="${k.esc(week)}" target="_blank" rel="noopener">JSON ↗</a>`:''}</td></tr></tbody></table>
    <p class="v10-muted">Validation and model detail pages stay in the <a href="#/classic/${encodeURIComponent(lid)}/lab">classic Research Lab ↗</a>. Project documents (build reports, calibration notes) live in the Claude project, not in the app.</p></section>`;
}
async function render(root,tab='state',lid=null,pos=null,week=null){
  const my=++token,k=K();const list=await D().leagues();if(!lid)lid=list[0]?.id||null;
  if(!['state','eval','forecasts','rankings','docs'].includes(tab))tab='state';
  root.innerHTML=`<div class="v10-league" data-v10-lab="${k.esc(tab)}"><header class="v10-lhdr"><div><h1>Research Lab</h1><div class="v10-muted">Research display only — nothing here changes a lineup, recommendation or projection. ${await leaguePicker(lid,tab)}</div></div></header>${nav(tab,lid)}<div class="v10-loading">Loading…</div></div>`;
  let body;
  try{body=tab==='state'?await state(lid):tab==='eval'?await evals(lid,week):tab==='forecasts'?await forecasts(lid,week):tab==='rankings'?await rankings(lid,pos):await docs(lid);}
  catch(e){body=k.empty(`Could not load: ${String(e?.message||e)}`);}
  if(my!==token)return;
  const ld=root.querySelector('.v10-loading');if(ld)ld.outerHTML=body;
  root.querySelector('select[data-v10-lab-league]')?.addEventListener('change',e=>{location.hash=href(tab,e.target.value);});
  root.querySelector('select[data-v10-lab-week]')?.addEventListener('change',e=>{location.hash=`${href('eval',lid)}&week=${e.target.value}`;});
  root.querySelector('select[data-v10-lab-fweek]')?.addEventListener('change',e=>{location.hash=`${href('forecasts',lid)}&week=${e.target.value}`;});
  root.querySelector('[data-v10-lab-review]')?.addEventListener('click',e=>{const el=root.querySelector('#v10LabReview');if(el)reviewAll(Number(e.target.dataset.v10LabReview),el);});
}
function cancel(){token++;}
window.FIEV10Lab={VERSION,render,cancel};
})();

/* FIE UI v10 Overview (R1 · WP1.5) — UI contract §4.1.
 *
 * Home for a many-league manager: (1) the to-do queue across all leagues — urgent, recommended,
 * monitor — with one grouped line per player who appears in several leagues; (2) one row per
 * league with this week's matchup state; (3) latest results of the last completed week.
 * Rules enforced here: no draft tasks in-season (WP0.3 — only leagues whose Sleeper status is
 * pre_draft/drafting get a draft line); Best Ball leagues never produce lineup tasks (FIEAlerts);
 * all numbers come from the same WeekModel the league views use (A-03).
 */
(function(){
'use strict';
const VERSION='10.4.0';
const K=()=>window.FIEV10Kit,D=()=>window.FIEV10Data;
let token=0,last=null;
function draftAlert(r){const st=r.wm?.league?.status;if(st!=='drafting'&&st!=='pre_draft')return null;
  return{code:'DRAFT',tier:st==='drafting'?'urgent':'monitor',leagueId:r.entry.id,leagueName:r.wm.entry.name,priority:r.entry.priority,title:st==='drafting'?'Draft in progress':'Draft not held yet',dedupKey:`${r.entry.id}:draft`,route:'classic:draft'};}
function alertRow(a,now){
  const k=K(),lock=a.lockAt?`<span class="v10-lock" title="${k.esc(k.time(a.lockAt))}">${k.esc(k.until(a.lockAt,now))}</span>`:'';
  const where=a.grouped?`${a.grouped.length} leagues`:k.esc(a.leagueName);
  const sum=`<span class="v10-q-tier">${k.tierChip(a.code==='CLOSE_CALL'?'close':a.tier)}</span><span class="v10-q-title">${where}</span><span class="v10-q-issue">${k.esc(a.issue||a.title)}</span><span class="v10-q-action">${k.esc(a.action||a.detail||'')}</span>${lock||'<span></span>'}`;
  const links=(a.grouped||[a]).map(x=>`<li><a href="${href(x)}">${k.esc(x.leagueName)}</a>${x.detail?` — ${k.esc(x.detail)}`:''}${x.inactivesAt?` · inactives ${k.esc(k.time(x.inactivesAt))}`:''}</li>`).join('');
  const body=`<ul class="v10-q-links">${links}</ul>`;
  const adv=k.kv([['Rule',k.esc(a.code)],['Lock',a.lockAt?k.esc(k.time(a.lockAt)):'–'],['League priority',k.esc(a.priority||'–')],['Gain',a.gain!==undefined&&a.gain!==null?k.signed(a.gain):'–']]);
  return k.expand(sum,body,{adv,cls:`v10-q v10-q-${a.tier}${a.quiet?' v10-quiet':''}`,key:`q:${a.dedupKey}`});
}
function href(a){if(String(a.route||'').startsWith('classic:'))return `#/classic/${encodeURIComponent(a.leagueId)}/${a.route.slice(8)}`;return `#/league/${encodeURIComponent(a.leagueId)}/${a.route||'home'}`;}
function matchupCell(wm){
  const k=K();if(!wm)return '–';
  if(wm.field){const f=wm.field;if(f.meEliminated)return '<span class="v10-muted">Eliminated</span>';
    return `#${f.myRank??'–'} of ${f.activeCount} · ${f.marginToCut===null?'–':k.signed(f.marginToCut)} vs cut${f.verified?'':' '+k.dot('amber','Field not verified against Sleeper eliminations')}`;}
  const me=wm.me.totals.projected,o=wm.opponent?.totals?.projected;
  if(wm.opponent)return `${k.pts(me)} – ${k.pts(o)} <span class="v10-muted">vs ${k.esc(wm.opponent.name)}</span>`;
  return `${k.pts(me)} <span class="v10-muted">projected</span>`;
}
function winCell(wm){const k=K(),w=wm?.winEstimate;if(!w)return '';return `${k.winPct(w.value)} ${k.dot('amber',w.note)}`;}
function record(wm){const r=wm?.standings?.rows?.find(x=>x.me);if(!r)return '';return wm.standings.chopped?`PF #${r.rank}`:`${r.wins}-${r.losses}${r.ties?`-${r.ties}`:''} · #${r.rank}`;}
function lineupMini(wm){
  const k=K(),rec=wm.me.recommended,changed=new Set(rec.changes.map(c=>c.outPid));
  const rows=wm.me.submitted.map(e=>`<tr class="${changed.has(e.pid)?'v10-out':''}"><td>${k.esc(e.slot)}</td><td>${e.p?`${k.esc(e.p.name)} ${k.statusChip(e.p.status)}`:'<b class="v10-bad">Empty</b>'}</td><td class="v10-num">${e.p?k.pts(e.p.status.unavailable?0:e.p.active.value):'–'}${e.p?.active?.dot?' '+k.dot(e.p.active.dot):''}</td><td class="v10-muted">${e.p?k.esc(k.gameText(e.p.game)):''}</td></tr>`).join('');
  const changes=rec.changes.length?`<p><b>Suggested:</b> ${rec.changes.map(c=>`${k.esc(wm.player(c.inPid)?.name)} for ${k.esc(c.outPid?wm.player(c.outPid)?.name:'empty slot')} (${k.signed(c.delta)})`).join('; ')}</p>`:'';
  return `<table class="v10-mini"><tbody>${rows}</tbody></table>${changes}`;
}
function leagueRow(r,now){
  const k=K(),wm=r.wm,e=r.entry;
  if(!wm)return `<div class="v10-lrow v10-lrow-err"><span class="v10-l-name">${k.esc(e.name||e.id)}</span><span class="v10-bad">${k.esc(r.error||'Loading failed')}</span></div>`;
  const tasks=r.alerts.filter(a=>!a.quiet),u=tasks.filter(a=>a.tier==='urgent').length,rc=tasks.filter(a=>a.tier==='recommended').length;
  const taskTxt=[u?`<span class="v10-chip v10-tier-urgent">${u}</span>`:'',rc?`<span class="v10-chip v10-tier-recommended">${rc}</span>`:''].join('')||'<span class="v10-muted">—</span>';
  const sum=`<span class="v10-l-name"><a href="#/league/${encodeURIComponent(e.id)}/home">${k.esc(wm.entry.name)}</a> ${k.formatChip(wm.format.key)}</span><span class="v10-l-match">${matchupCell(wm)}</span><span class="v10-l-win">${winCell(wm)}</span><span class="v10-l-rec">${k.esc(record(wm))}</span><span class="v10-l-tasks">${taskTxt}</span><span class="v10-l-lock">${wm.nextLock?k.esc(k.until(wm.nextLock,now)):'<span class="v10-muted">all locked</span>'}</span>`;
  const adv=k.kv([['Data as of',k.esc(k.clock(wm.dataAt))],['Projections as of',k.esc(k.clock(wm.projectionsAt))],['Week',k.esc(wm.key.week)],['Win-estimate method',wm.winEstimate?`${k.esc(wm.winEstimate.method)} · ${k.esc(wm.winEstimate.note)}`:'–'],['Issues',wm.issues.map(i=>k.esc(i.text)).join('<br>')||'none']]);
  return k.expand(sum,lineupMini(wm),{adv,cls:'v10-lrow',key:`l:${e.id}`});
}
function header(rows,now){
  const k=K(),ok=rows.filter(r=>r?.wm),locks=ok.map(r=>r.wm.nextLock).filter(Boolean),next=locks.length?Math.min(...locks):null,week=ok[0]?.wm?.key?.week;
  return `<div class="v10-ov-head"><h1>Week ${k.esc(week??'–')}</h1><div class="v10-muted">${ok.length}/${rows.length} leagues loaded${next?` · next lock ${k.esc(k.time(next))} (${k.esc(k.until(next,now))})`:''}</div></div>`;
}
function taskRow(t,now){
  const k=K(),lock=t.lockAt?`<span class="v10-lock" title="${k.esc(k.time(t.lockAt))}">${k.esc(k.until(t.lockAt,now))}</span>`:'';
  const sum=`<span class="v10-q-tier">${k.tierChip(t.close?'close':t.tier)}</span><span class="v10-q-title"><a href="#/league/${encodeURIComponent(t.leagueId)}/lineup">${k.esc(t.leagueName)}</a></span><span class="v10-q-issue">${k.esc(t.issue||t.title)}</span><span class="v10-q-action">${k.esc(t.action||'')}</span>${lock||'<span></span>'}`;
  const body=`<ul class="v10-q-links">${t.items.map(a=>`<li>${k.tierChip(a.code==='CLOSE_CALL'?'close':a.tier)} <a href="${href(a)}">${k.esc(a.title)}</a>${a.detail?` — ${k.esc(a.detail)}`:''}${a.inactivesAt?` · inactives ${k.esc(k.time(a.inactivesAt))}`:''}${a.lockAt?` <span class="v10-lock">${k.esc(k.time(a.lockAt))}</span>`:''}</li>`).join('')}</ul>`;
  const adv=k.kv([['Rules',t.items.map(a=>k.esc(a.code)).join(', ')],['League priority',k.esc(t.priority||'–')],['Projected gain (sum)',k.signed(t.gain)]]);
  return k.expand(sum,body,{adv,cls:`v10-q v10-q-${t.tier}`,key:`t:${t.leagueId}`});
}
function queue(rows,now){
  const k=K(),per=rows.filter(Boolean).map(r=>{const d=draftAlert(r);return d?[...r.alerts,d]:r.alerts;});
  const {actions,monitor,quiet}=window.FIEAlerts.queue(per);
  const sec=(xs,label,fn)=>xs.length?`<h3>${label} <span class="v10-muted">${xs.length}</span></h3>${xs.map(x=>fn(x,now)).join('')}`:'';
  const body=sec(actions.filter(a=>a.tier==='urgent'),'Urgent',taskRow)+sec(actions.filter(a=>a.tier==='recommended'),'Recommended',taskRow)+sec(actions.filter(a=>a.tier==='monitor'),'Close calls',taskRow)+sec(monitor,'Monitor',alertRow)
    ||k.empty('Nothing to do right now. Lineups match the best projected lineup in every league.');
  const q=quiet.length?k.expand(`<span class="v10-muted">Data issues (${quiet.length})</span>`,quiet.map(a=>`<div>${k.esc(a.leagueName)}: ${k.esc(a.title)}</div>`).join(''),{cls:'v10-quietbox',key:'quiet'}):'';
  // R4.7 · One header for all groups; every row reads League · Issue · Proposed action · Locks in (Monitor used to put the
  // player first and the league second).
  const headRow=body.startsWith('<h3')?'<div class="v10-qhead"><span></span><span>League</span><span>Issue</span><span>Proposed action</span><span>Locks in</span></div>':'';
  return `<section class="v10-card"><h2>To do</h2>${headRow}${body}${q}</section>`;
}
// ---- R2 · WP2.5: changes since last visit + my players this week ----
const LAST='fieV10LastVisit',BASE='fieV10FeedBase';
function readJSON(store,key){try{return JSON.parse(store.getItem(key)||'null');}catch{return null;}}
function writeJSON(store,key,v){try{store.setItem(key,JSON.stringify(v));}catch{}}
/** Baseline = the snapshot of the previous visit; kept per browser session so live re-renders keep the same feed. */
function feedBaseline(){let b=readJSON(sessionStorage,BASE);if(!b){b=readJSON(localStorage,LAST)||{none:true};writeJSON(sessionStorage,BASE,b);}return b.none?null:b;}
function feedSection(rows){
  const k=K(),ok=rows.filter(r=>r?.wm);if(ok.length<rows.length)return `<section class="v10-card" id="v10Feed"><h2>Since your last visit</h2>${k.empty('Loading…')}</section>`;
  const tx={};for(const r of ok)tx[r.wm.key.leagueId]=r.tx||[];
  const f=window.FIEPortfolioViews.changes(feedBaseline(),ok,tx);
  writeJSON(localStorage,LAST,window.FIEPortfolioViews.snapshot(ok));
  if(f.firstVisit)return `<section class="v10-card" id="v10Feed"><h2>Since your last visit</h2>${k.empty('First visit in this browser — status changes, waiver results and trades will appear here from your next visit.')}</section>`;
  const items=f.items.slice(0,25);
  return `<section class="v10-card" id="v10Feed"><h2>Since your last visit <span class="v10-muted">${k.esc(k.time(f.since))}</span></h2>${items.length?`<ul class="v10-feed">${items.map(x=>`<li class="v10-feed-${k.esc(x.tier)}">${x.tier==='urgent'?k.tierChip('urgent')+' ':''}${x.kind==='tx'?`<span class="v10-muted">${k.esc(x.leagueName)} ·</span> `:''}${k.esc(x.text)}${x.at?` <span class="v10-lock">${k.esc(k.time(x.at))}</span>`:''}</li>`).join('')}</ul>${f.items.length>items.length?`<div class="v10-muted">${f.items.length-items.length} more</div>`:''}`:k.empty('Nothing changed for your players or rosters.')}</section>`;
}
function myPlayersSection(rows){
  const k=K(),ok=rows.filter(r=>r?.wm);if(!ok.length)return '';
  const mp=window.FIEPortfolioViews.myPlayers(ok),top=mp.rows.filter(r=>r.starts>0).slice(0,40);
  const line=x=>{const sum=`<span class="v10-mp-name">${k.playerLink(x,{leagueId:x.leagues[0]?.leagueId})} <span class="v10-muted">${k.esc(x.position)} · ${k.esc(x.team||'FA')}</span> ${k.statusChip(x.status)}</span><span class="v10-num">${x.starts}</span><span class="v10-num">${x.rostered}</span><span class="v10-muted">${k.esc(k.gameText(x.game))}</span>`;
    const body=`<table class="v10-mini"><tbody>${x.leagues.map(l=>`<tr><td><a href="#/league/${encodeURIComponent(l.leagueId)}/lineup">${k.esc(l.leagueName)}</a></td><td>${l.role==='start'?k.esc(l.slot):l.role}</td><td class="v10-num">${k.pts(l.value)}</td></tr>`).join('')}</tbody></table>`;
    return k.expand(sum,body,{cls:'v10-mprow',key:`mp:${x.pid}`});};
  return `<section class="v10-card"><h2>My players this week <span class="v10-muted">${mp.players} players · ${mp.startSlots} starting slots${mp.unavailableStarters.length?` · <b class="v10-bad">${mp.unavailableStarters.length} starting but can't play</b>`:''}</span></h2>
    <div class="v10-mphead"><span>Player</span><span class="v10-num">Starts</span><span class="v10-num">Rostered</span><span>Game</span></div>${top.map(line).join('')}
    ${mp.rows.length>top.length?k.expand(`<span class="v10-muted">${mp.rows.length-top.length} more players (bench / IR / taxi only)</span>`,mp.rows.filter(r=>!top.includes(r)).map(line).join(''),{key:'mp:rest'}):''}</section>`;
}
function leaguesTable(rows,now){
  const k=K(),wk=rows.find(r=>r?.wm)?.wm.key.week;return `<section class="v10-card"><h2>Leagues</h2><div class="v10-lhead"><span>League</span><span>${wk?`Week ${k.esc(wk)}`:'This week'}</span><span>Win est.</span><span>Record</span><span>Tasks</span><span>Lock</span></div>${rows.map(r=>r?leagueRow(r,now):`<div class="v10-lrow v10-loading">Loading…</div>`).join('')}</section>`;
}
function resultsSection(res){
  const k=K();if(!res)return `<section class="v10-card" id="v10Results"><h2>Latest results</h2>${k.empty('Loading last week…')}</section>`;
  const rows=res.filter(x=>x&&x.r);if(!rows.length)return `<section class="v10-card" id="v10Results"><h2>Latest results</h2>${k.empty('No completed week yet.')}</section>`;
  return `<section class="v10-card" id="v10Results"><h2>Latest results <span class="v10-muted">Week ${k.esc(rows[0].r.week)}</span></h2><table class="v10-table"><thead><tr><th>League</th><th>Result</th><th class="v10-num">Points</th><th class="v10-num">Rank of week</th></tr></thead><tbody>${rows.map(({entry,r,chopped})=>{
    const res=r.eliminated?'<span class="v10-muted">Eliminated</span>':r.oppPoints!==null&&!chopped?(r.points>r.oppPoints?'<b class="v10-good">W</b>':r.points<r.oppPoints?'<b class="v10-bad">L</b>':'T'):chopped?(r.lowest?'<b class="v10-bad">Chopped</b>':'Survived'):'';
    return `<tr><td><a href="#/league/${encodeURIComponent(entry.id)}/matchup">${k.esc(entry.name)}</a></td><td>${res}</td><td class="v10-num">${r.eliminated?'–':k.pts(r.points,2)}${!r.eliminated&&r.oppPoints!==null&&!chopped?` – ${k.pts(r.oppPoints,2)}`:''}</td><td class="v10-num">${r.eliminated?'–':`${r.rank}/${r.teams}`}</td></tr>`;}).join('')}</tbody></table></section>`;
}
async function render(root){
  const my=++token,now=Date.now(),list=await D().leagues();if(my!==token)return;
  const rows=new Array(list.length).fill(null);let resultsRows=null;
  const paint=()=>{if(my!==token)return;const t=Date.now(),done=rows.every(Boolean);K().repaint(root,`<div class="v10-overview">${header(rows.map((r,i)=>r||{entry:list[i]}),t)}${queue(rows,t)}${done?feedSection(rows):''}${leaguesTable(rows,t)}${done?myPlayersSection(rows):''}${resultsSection(resultsRows)}</div>`);};
  let pending=null;const schedule=()=>{if(!pending)pending=setTimeout(()=>{pending=null;paint();},120);};
  paint();
  await D().portfolio({onEach:(i,r)=>{rows[i]=r;schedule();}});
  if(my!==token)return;clearTimeout(pending);pending=null;paint();last={at:Date.now(),rows};
  // Latest results: previous completed week, after the current week is on screen.
  const week=rows.find(r=>r?.wm)?.wm?.key?.week;
  if(week>1){const res=await Promise.all(rows.map(async r=>r?.wm?{entry:r.wm.entry,chopped:!!r.wm.format.chopped,r:await D().results(r.wm.entry,week-1)}:null));if(my!==token)return;resultsRows=res;const el=root.querySelector('#v10Results');if(el)el.outerHTML=resultsSection(resultsRows);}
  else{resultsRows=[];const el=root.querySelector('#v10Results');if(el)el.outerHTML=resultsSection(resultsRows);}
}
function cancel(){token++;}
window.FIEV10Overview={VERSION,render,cancel,last:()=>last};
})();

/* Fantasy Intelligence Engine V9.3.3A-C runtime integrity patch.
 * A: league/week/season isolation + null-safe weekly projection fast path.
 * B: snapshot-first switching, manual/live overlay isolation, enrichment render
 *    coalescing, schedule/projection fast path and main-thread yielding.
 * C: visible Matchup/Playoffs week control, schedule-backed opponents,
 *    Next 3 Avg labeling, honest range labeling and player-name repair.
 *
 * This module is intentionally additive. It wraps the stable V9.3.2 runtime
 * instead of duplicating the 70k-line decision/UI modules.
 */
(function(){
'use strict';
if(window.FIE933ABC?.installed)return;

const VERSION='9.3.3A-C';
const RELEASE='runtime-integrity-fast-weekly-special-teams';
const DAY=24*60*60*1000;
const scheduleCache=new Map();
const weekProjectionCache=new Map();
const liveFingerprints=new Map();
let switchingLeagueId=null;
let installAttempts=0;
let enrichmentActive=false;
let pendingRender=false;
let pendingKpis=false;
let lastUserInput=0;
let renderBypass=0;
let originalRender=null;
let originalUpdateKPIs=null;
let domTimer=null;
let observer=null;
let leagueSimGuardInstalled=false;
let dataClientWrapped=false;
let enrichmentYieldWrapped=false;
let renderWrapped=false;
let weeklyLoadToken=0;
const diagnostics={staleSimulationRejects:0,snapshotFastHits:0,snapshotFastMisses:0,scheduleLoads:0,weeklyProjectionLoads:0,automaticRendersSuppressed:0,liveOverlayChanges:0};

const stateObj=()=>window.state||(typeof state!=='undefined'?state:null);
const core=()=>window.FIECore||{};
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function clone(v){try{return typeof structuredClone==='function'?structuredClone(v):JSON.parse(JSON.stringify(v));}catch{return v;}}
function leagueId(){return String(stateObj()?.league?.league_id||stateObj()?.activeLeagueId||'');}
function activeSeason(){
  let s=null;try{s=core().SeasonResolver?.resolve?.({league:stateObj()?.league,selected:document.getElementById('seasonSelect')?.value,weekly:stateObj()?.weekly?.season});}catch{}
  s=finite(s)??finite(stateObj()?.league?.season)??finite(stateObj()?.weekly?.season);
  if(s!==null&&s>1900)return Math.round(s);
  const d=new Date();return d.getUTCMonth()<=1?d.getUTCFullYear()-1:d.getUTCFullYear();
}
function activeWeek(){const w=finite(document.getElementById('weekSelect')?.value)??finite(stateObj()?.weekly?.week)??1;return Math.max(1,Math.min(18,Math.round(w)));}
function currentContext(){return{leagueId:leagueId(),season:activeSeason(),week:activeWeek()};}
function idle(timeout=600){return new Promise(resolve=>{const cb=()=>requestAnimationFrame(()=>resolve());if(typeof requestIdleCallback==='function')requestIdleCallback(cb,{timeout});else setTimeout(cb,Math.min(120,timeout));});}
function diag(error,meta={}){try{core().Diagnostics?.capture?.(error,{domain:'v9.3.3-runtime',...meta});}catch{} }
function markUserInput(){lastUserInput=Date.now();}
for(const ev of ['pointerdown','keydown','change','touchstart'])document.addEventListener(ev,markUserInput,true);
function recentUserInput(){return Date.now()-lastUserInput<800;}

/* -------------------------- A · season invariants ------------------------- */
function ensureSeasonInvariant(){
  const s=activeSeason(),st=stateObj();if(!st)return s;
  st.weekly=st.weekly||{};if(finite(st.weekly.season)===null||Number(st.weekly.season)<=1900)st.weekly.season=s;
  if(st.league&&(finite(st.league.season)===null||Number(st.league.season)<=1900))st.league.season=s;
  const sel=document.getElementById('seasonSelect');
  if(sel&&String(sel.value||'')!==String(s)){
    let opt=[...sel.options].find(o=>Number(o.value)===s);if(!opt){opt=document.createElement('option');opt.value=String(s);opt.textContent=String(s);sel.appendChild(opt);}sel.value=String(s);
  }
  return s;
}

/* -------------------------- B · schedule fast path ------------------------ */
function parseCsvLine(line){
  const out=[];let cur='',quoted=false;
  for(let i=0;i<line.length;i++){
    const c=line[i];
    if(c==='"'){if(quoted&&line[i+1]==='"'){cur+='"';i++;}else quoted=!quoted;continue;}
    if(c===','&&!quoted){out.push(cur);cur='';continue;}cur+=c;
  }
  out.push(cur);return out;
}
function parseCSV(text){
  if(typeof window.parseCSV==='function'){try{return window.parseCSV(text)||[];}catch{} }
  const lines=String(text||'').replace(/^\uFEFF/,'').split(/\r?\n/).filter(Boolean);if(!lines.length)return[];
  const head=parseCsvLine(lines.shift());return lines.map(line=>{const vals=parseCsvLine(line),row={};head.forEach((h,i)=>row[h]=vals[i]??'');return row;});
}
function scheduleGame(team,week=activeWeek(),season=activeSeason()){
  const t=String(team||'').toUpperCase();if(!t)return null;
  return (stateObj()?.weekly?.schedule||[]).find(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG')&&(String(g.home_team).toUpperCase()===t||String(g.away_team).toUpperCase()===t))||null;
}
function schedulePublished(week=activeWeek(),season=activeSeason()){return (stateObj()?.weekly?.schedule||[]).some(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG'));}
function opponentForTeam(team,week=activeWeek(),season=activeSeason()){
  const g=scheduleGame(team,week,season),t=String(team||'').toUpperCase();if(g)return String(g.home_team).toUpperCase()===t?g.away_team:g.home_team;return t&&schedulePublished(week,season)?'BYE':'—';
}
async function ensureSchedule(season=activeSeason(),{force=false}={}){
  const s=Number(season);if(!Number.isFinite(s)||s<1900)return[];
  if(!force&&scheduleCache.has(s)){const rows=await scheduleCache.get(s);installSchedule(rows,s);return rows;}
  const p=(async()=>{
    try{
      const data=window.FIEDataClient;
      const text=data?.text?await data.text('/api/data/nflverse/schedule',{sourceId:`schedule-fast-${s}`,ttlMs:6*60*60*1000,persist:true,maxBytes:8*1024*1024,cache:force?'reload':'default'}):await fetch('/api/data/nflverse/schedule',{cache:force?'reload':'default'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.text();});
      const rows=parseCSV(text).filter(g=>Number(g.season)===s&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG'));
      diagnostics.scheduleLoads++;return rows;
    }catch(e){diag(e,{feature:'schedule-fast-path',season:s});return[];}
  })();scheduleCache.set(s,p);const rows=await p;installSchedule(rows,s);return rows;
}
function installSchedule(rows,season){
  const st=stateObj();if(!st)return;st.weekly=st.weekly||{};
  if(Number(activeSeason())===Number(season)&&Array.isArray(rows)&&rows.length){st.weekly.schedule=rows;st.weekly.season=Number(season);st.weekly.scheduleReady=true;window.dispatchEvent(new CustomEvent('fie:schedule-ready',{detail:{season:Number(season),games:rows.length}}));try{window.FIEDST?.render?.();window.FIEKicker?.render?.();}catch{}scheduleDomEnhance();}
}

/* ---------------------- A/C · weekly projection path ---------------------- */
function normalizeProjectionRows(rows){const m=new Map();for(const r of rows||[]){const id=String(r?.player_id||r?.player?.player_id||'');if(id)m.set(id,r);}return m;}
function governedCurrentMap(){const b=window.FIE_M5?.getCurrentBundle?.()||null;return new Map((b?.players||[]).map(r=>[String(r?.sleeper_id||''),r]).filter(([id])=>id));}
function playerId(p){return String(p?.sleeperId||p?.player_id||p?.playerId||'');}
function scoreProjectionRow(row,p){if(!row)return null;const stats=row.stats||row;try{return finite(window.scoreSleeperProjectionStats?.(stats,p));}catch{return null;}}
function repairPlayerNames(){
  const st=stateObj(),map=st?.playerMap||{};let changed=0;
  for(const p of window.PLAYERS||[]){
    const current=String(p?.name||'').trim();if(current&&current!=='undefined'&&current!=='null')continue;
    const meta=map[playerId(p)]||{};const name=String(meta.full_name||[meta.first_name,meta.last_name].filter(Boolean).join(' ')||p?.full_name||'').trim();
    if(name){p.name=name;changed++;}
  }
  return changed;
}
function applyWeekProjectionRows(rows,week,season){
  const map=normalizeProjectionRows(rows),governed=governedCurrentMap();let matched=0,governedCount=0,byeCount=0;
  repairPlayerNames();
  for(const p of window.PLAYERS||[]){
    const id=playerId(p),row=map.get(id)||null,sleeper=scoreProjectionRow(row,p),opp=opponentForTeam(p.team,week,season),bye=opp==='BYE',g=governed.get(id)||null,same=Number(g?.week)===Number(week)&&Number(g?.season)===Number(season)&&g?.weekly_activation_eligible===true,gv=same?finite(g?.decision_weekly_projection):null;
    if(sleeper!==null)matched++;if(gv!==null)governedCount++;if(bye)byeCount++;
    p.__fieWeeklyByWeek=p.__fieWeeklyByWeek||{};
    p.sleeperWeeklyProjection=sleeper;
    p.weeklyOpponent=opp;p.opponent=opp;
    if(gv!==null){
      p.weeklyProjection=gv;p.weeklyProjectionSource='FIE governed current';
      const lo=finite(g?.p10),hi=finite(g?.p90);p.weeklyFloor=lo;p.weeklyCeiling=hi;p.rangeSource=(lo!==null||hi!==null)?'FIE empirical':'Unavailable';
    }else if(bye){
      p.weeklyProjection=0;p.weeklyProjectionSource='Schedule · BYE';p.weeklyFloor=0;p.weeklyCeiling=0;p.rangeSource='Schedule';
    }else if(sleeper!==null){
      p.weeklyProjection=sleeper;p.weeklyProjectionSource=`Sleeper Week ${week}`;p.weeklyFloor=Math.max(0,sleeper*.78);p.weeklyCeiling=sleeper*1.22;p.rangeSource='Heuristic weekly interval · not calibrated';
    }else{
      p.weeklyProjection=null;p.weeklyProjectionSource='Unavailable';p.weeklyFloor=null;p.weeklyCeiling=null;p.rangeSource='Unavailable';
    }
    p.__fieWeeklyByWeek[`${season}:${week}`]={projection:finite(p.weeklyProjection),sleeper,opponent:opp,source:p.weeklyProjectionSource,low:finite(p.weeklyFloor),high:finite(p.weeklyCeiling)};
  }
  const st=stateObj();if(st){st.weekly=st.weekly||{};st.weekly.week=Number(week);st.weekly.season=Number(season);st.weekly.fastPathReady=true;st.projectionStatus=st.projectionStatus||{};st.projectionStatus.weekly=matched>0||governedCount>0||byeCount>0;st.projectionStatus.weeklyCount=matched+governedCount;st.projectionStatus.weeklyError=null;st.projectionStatus.source=governedCount?'FIE governed + Sleeper selected-week':'Sleeper selected-week';}
  try{window.assignScores?.(`V9.3.3 selected-week ${week}`);}catch(e){diag(e,{feature:'assign-weekly'});}
  return{matched,governed:governedCount,byes:byeCount,total:(window.PLAYERS||[]).length};
}
async function loadSelectedWeek(week=activeWeek(),{reason='automatic',rerunSimulation=false,force=false}={}){
  const token=++weeklyLoadToken,w=Math.max(1,Math.min(18,Number(week)||1)),s=ensureSeasonInvariant(),key=`${s}:${w}`;
  await ensureSchedule(s,{force:false});if(token!==weeklyLoadToken)return null;
  let rows;
  try{
    if(!force&&weekProjectionCache.has(key))rows=await weekProjectionCache.get(key);else{
      const p=(async()=>{const url=`/api/data/sleeper/projections/${s}/${w}`;const d=window.FIEDataClient;return d?.json?d.json(url,{sourceId:`weekly-fast-${s}-${w}`,ttlMs:15*60*1000,persist:true,cache:force?'reload':'default'}):fetch(url,{cache:force?'reload':'default'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();});})();weekProjectionCache.set(key,p);rows=await p;
    }
    if(token!==weeklyLoadToken)return null;const summary=applyWeekProjectionRows(Array.isArray(rows)?rows:[],w,s);diagnostics.weeklyProjectionLoads++;
    window.dispatchEvent(new CustomEvent('fie:weekly-fast-path-ready',{detail:{leagueId:leagueId(),season:s,week:w,reason,...summary}}));
    try{window.FIEDST?.render?.();window.FIEKicker?.render?.();}catch{}
    if(reason==='user-week-change'||recentUserInput())forceRender(()=>{try{window.updateKPIs?.();window.render?.();}catch{}});
    if(rerunSimulation&&window.FIEDecisionEngines?.runLeagueSimulation){try{await window.FIEDecisionEngines.runLeagueSimulation(true);}catch(e){diag(e,{feature:'rerun-sim'});}}
    scheduleDomEnhance();return summary;
  }catch(e){
    if(token!==weeklyLoadToken)return null;const st=stateObj();if(st){st.projectionStatus=st.projectionStatus||{};st.projectionStatus.weeklyError=String(e?.message||e);}diag(e,{feature:'weekly-fast-path',week:w,season:s});return null;
  }
}
function setWeek(w,{reason='user-week-change',rerunSimulation=true}={}){
  const week=Math.max(1,Math.min(18,Number(w)||1)),st=stateObj();if(st){st.weekly=st.weekly||{};st.weekly.week=week;}
  const sel=document.getElementById('weekSelect');if(sel&&Number(sel.value)!==week)sel.value=String(week);
  clearLeagueSimulationForContext();return loadSelectedWeek(week,{reason,rerunSimulation});
}

/* --------------------- A · league simulation isolation -------------------- */
function defaultSim(lid=leagueId(),week=activeWeek()){return{loading:false,error:null,data:null,leagueId:String(lid||''),week:Number(week)||1};}
function installLeagueSimGuard(){
  const eng=window.FIEDecisionEngines;if(!eng||leagueSimGuardInstalled)return !!eng;let backing=eng.leagueSim||defaultSim();
  try{
    Object.defineProperty(eng,'leagueSim',{configurable:true,enumerable:true,get(){return backing;},set(next){
      const n=next&&typeof next==='object'?next:defaultSim(),intended=String(switchingLeagueId||leagueId()||''),candidate=String(n.leagueId||''),candidateWeek=finite(n.week),nowWeek=activeWeek();
      if(candidate&&intended&&candidate!==intended){diagnostics.staleSimulationRejects++;return;}
      if(!switchingLeagueId&&n.data&&candidate&&candidate===leagueId()&&candidateWeek!==null&&Number(candidateWeek)!==Number(nowWeek)){diagnostics.staleSimulationRejects++;return;}
      backing=n;
    }});leagueSimGuardInstalled=true;eng.__fie933LeagueSimGuard=true;return true;
  }catch(e){diag(e,{feature:'league-sim-guard'});return false;}
}
function clearLeagueSimulationForContext(target=leagueId()){
  const eng=window.FIEDecisionEngines;if(!eng)return;try{eng.cancelDraftMonteCarlo?.('league/week context changed');eng.leagueSim=defaultSim(target,activeWeek());}catch(e){diag(e,{feature:'clear-league-sim'});}
}

/* ----------------------- B · snapshot-first switching --------------------- */
function sleeperRoute(url){let u;try{u=new URL(String(url),location.href);}catch{return null;}if(!/(?:^|\.)sleeper\.(?:app|com)$/i.test(u.hostname))return null;const m=u.pathname.match(/^\/v1\/league\/(\d{6,32})(?:\/(rosters|users))?\/?$/);return m?{leagueId:m[1],part:m[2]||'league'}:null;}
function snapshotPart(core,part){const v=core?.sleeper?.[part];if(part==='league'&&v&&typeof v==='object')return clone(v);if((part==='rosters'||part==='users')&&Array.isArray(v))return clone(v);return null;}
function snapshotRefreshKey(id){return`fie933:snapshot-refresh:${id}`;}
function shouldForceSnapshot(id){try{return Date.now()-Number(localStorage.getItem(snapshotRefreshKey(id))||0)>DAY;}catch{return false;}}
function markSnapshotRefresh(id){try{localStorage.setItem(snapshotRefreshKey(id),String(Date.now()));}catch{}}
function installDataClientFastPath(){
  const client=window.FIEDataClient;if(!client||dataClientWrapped||client.__fie933FastPath)return !!client;const original=client.json.bind(client);
  client.json=async function(url,opts={}){
    const route=sleeperRoute(url);if(route&&opts.snapshot!==false&&opts.live!==true&&opts.cache!=='no-store'&&typeof client.loadLeagueSnapshot==='function'){
      try{
        const force=shouldForceSnapshot(route.leagueId),core=await client.loadLeagueSnapshot(route.leagueId,{force}),value=snapshotPart(core,route.part);
        if(value!==null){if(force)markSnapshotRefresh(route.leagueId);diagnostics.snapshotFastHits++;return value;}
      }catch(e){diagnostics.snapshotFastMisses++;}
    }
    return original(url,opts);
  };
  client.__fie933FastPath=true;dataClientWrapped=true;return true;
}
function simpleFingerprint(value){try{return JSON.stringify(value);}catch{return String(value);}}
function applyLiveOverlay(detail){
  const st=stateObj();if(!st||String(detail?.leagueId||'')!==String(leagueId()))return;const part=detail.part,value=detail.value;if(!['league','rosters','users'].includes(part))return;
  const k=`${detail.leagueId}:${part}`,fp=simpleFingerprint(value);if(liveFingerprints.get(k)===fp)return;liveFingerprints.set(k,fp);
  let changed=false;
  if(part==='league'&&value&&typeof value==='object'){const before=simpleFingerprint(st.league);if(st.league&&typeof st.league==='object')Object.assign(st.league,value);else st.league=value;changed=before!==simpleFingerprint(st.league);}
  if(part==='rosters'&&Array.isArray(value)){const before=simpleFingerprint(st.rosters);st.rosters=clone(value);changed=before!==simpleFingerprint(st.rosters);}
  if(part==='users'&&Array.isArray(value)){const before=simpleFingerprint(st.users);st.users=clone(value);changed=before!==simpleFingerprint(st.users);}
  if(!changed)return;diagnostics.liveOverlayChanges++;
  clearTimeout(applyLiveOverlay._t);applyLiveOverlay._t=setTimeout(async()=>{if(String(detail.leagueId)!==String(leagueId()))return;await idle(800);try{window.buildPlayerUniverse?.();repairPlayerNames();window.populateRosterPicker?.();window.populateIntelligencePickers?.();window.assignScores?.('V9.3.3 live league overlay');if(!enrichmentActive&&!recentUserInput())window.render?.();}catch(e){diag(e,{feature:'live-overlay-rebuild'});}},120);
}

/* ------------------ B · non-blocking enrichment rendering ---------------- */
function forceRender(fn){renderBypass++;try{return fn();}finally{renderBypass--;}}
function installRenderCoalescing(){
  if(renderWrapped||typeof window.render!=='function')return false;originalRender=window.render;originalUpdateKPIs=typeof window.updateKPIs==='function'?window.updateKPIs:null;
  function wrappedRender(){if(enrichmentActive&&!renderBypass&&!recentUserInput()){pendingRender=true;diagnostics.automaticRendersSuppressed++;return;}const r=originalRender.apply(this,arguments);scheduleDomEnhance();return r;}wrappedRender.__fie933Wrapped=true;
  window.render=wrappedRender;
  if(originalUpdateKPIs){window.updateKPIs=function(){if(enrichmentActive&&!renderBypass&&!recentUserInput()){pendingKpis=true;return;}return originalUpdateKPIs.apply(this,arguments);};window.updateKPIs.__fie933Wrapped=true;}
  renderWrapped=true;return true;
}
function renderCoreOnce(){forceRender(()=>{try{originalUpdateKPIs?.();originalRender?.();scheduleDomEnhance();}catch(e){diag(e,{feature:'core-render'});}});}
function flushAutomaticRender(){const doKpi=pendingKpis,doRender=pendingRender;pendingKpis=false;pendingRender=false;forceRender(()=>{try{if(doKpi||doRender)originalUpdateKPIs?.();if(doRender||doKpi)originalRender?.();scheduleDomEnhance();}catch(e){diag(e,{feature:'enhanced-render-flush'});}});}
function installEnrichmentYield(){
  if(enrichmentYieldWrapped||typeof window.loadPublicEnrichment!=='function')return false;const original=window.loadPublicEnrichment;
  window.loadPublicEnrichment=async function(){await idle(700);return original.apply(this,arguments);};window.loadPublicEnrichment.__fie933Yield=true;enrichmentYieldWrapped=true;return true;
}

/* --------------------------- C · visible controls ------------------------- */
function weekOptions(selected){return Array.from({length:18},(_,i)=>`<option value="${i+1}" ${Number(selected)===i+1?'selected':''}>Week ${i+1}</option>`).join('');}
function injectMatchupWeekControl(){
  const host=document.getElementById('matchupSimContent');if(!host||stateObj()?.activeTab!=='matchupsim')return;
  let wrap=host.querySelector('.fie933-matchup-week');if(!wrap){wrap=document.createElement('div');wrap.className='fie933-matchup-week';wrap.style.cssText='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:8px 0 12px';wrap.innerHTML=`<span class="filter-label">Matchup / playoffs week</span><select id="fie933MatchupWeek">${weekOptions(activeWeek())}</select><span class="muted" style="font-size:11px">Changes opponent, selected-week projections and the simulation start week.</span>`;const h=host.querySelector('h2');if(h)h.insertAdjacentElement('afterend',wrap);else host.prepend(wrap);wrap.querySelector('select').onchange=e=>setWeek(Number(e.target.value),{reason:'user-week-change',rerunSimulation:true});}
  const sel=wrap.querySelector('select');if(sel&&Number(sel.value)!==activeWeek())sel.value=String(activeWeek());
}
function relabelNext3(){for(const th of document.querySelectorAll('#dstSummary th,#kickerSummary th'))if(th.textContent.trim()==='Next 3')th.textContent='Next 3 Avg';}
function addRangeNote(rootId){const root=document.getElementById(rootId);if(!root||root.querySelector('.fie933-range-note'))return;const n=document.createElement('div');n.className='notice fie933-range-note';n.style.marginTop='8px';n.innerHTML='<b>Low / High:</b> empirical only when a governed calibrated interval exists. Otherwise it is a clearly heuristic range around the selected-week projection, not P10/P90.';root.appendChild(n);}
function repairSeasonZeroText(){if(!stateObj()?.league)return;const s=activeSeason(),walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while((node=walker.nextNode())){if(node.nodeValue&&/Season\s+0\b/.test(node.nodeValue))node.nodeValue=node.nodeValue.replace(/Season\s+0\b/g,`Season ${s}`);}}
function enhanceDiagnosticsVersion(){const tag=document.querySelector('#fieRuntimeDiagnosticsV9 .tag');if(tag)tag.textContent='V9.3.3';}
function enhanceDom(){domTimer=null;try{ensureSeasonInvariant();repairPlayerNames();injectMatchupWeekControl();relabelNext3();addRangeNote('dstSummary');addRangeNote('kickerSummary');repairSeasonZeroText();enhanceDiagnosticsVersion();}catch(e){diag(e,{feature:'dom-enhance'});}}
function scheduleDomEnhance(){if(domTimer)return;domTimer=setTimeout(enhanceDom,40);}
function installObserver(){if(observer||!document.body)return;observer=new MutationObserver(scheduleDomEnhance);observer.observe(document.body,{childList:true,subtree:true});scheduleDomEnhance();}

/* ----------------------------- event wiring ------------------------------- */
window.addEventListener('fie:league-changing',e=>{
  switchingLeagueId=String(e?.detail?.leagueId||'');enrichmentActive=true;pendingRender=false;pendingKpis=false;weeklyLoadToken++;
  clearLeagueSimulationForContext(switchingLeagueId);scheduleDomEnhance();
});
window.addEventListener('fie:league-loaded',e=>{
  const stage=e?.detail?.stage,id=String(e?.detail?.leagueId||'');if(stage==='core'){
    switchingLeagueId=null;ensureSeasonInvariant();repairPlayerNames();clearLeagueSimulationForContext(id);renderCoreOnce();enrichmentActive=true;
    Promise.allSettled([ensureSchedule(activeSeason()),loadSelectedWeek(activeWeek(),{reason:'core',rerunSimulation:false})]).then(scheduleDomEnhance);
  }else if(stage==='enhanced'){
    switchingLeagueId=null;enrichmentActive=false;repairPlayerNames();flushAutomaticRender();scheduleDomEnhance();
  }
});
window.addEventListener('fie:league-live-update',e=>applyLiveOverlay(e?.detail||{}));
window.addEventListener('fie:schedule-ready',()=>{try{window.FIEDST?.render?.();window.FIEKicker?.render?.();}catch{}scheduleDomEnhance();});
document.addEventListener('change',e=>{if(e.target?.id==='weekSelect'){const w=Number(e.target.value)||1;setWeek(w,{reason:'user-week-change',rerunSimulation:stateObj()?.activeTab==='matchupsim'});}},true);

function install(){
  installAttempts++;installDataClientFastPath();installLeagueSimGuard();installEnrichmentYield();installRenderCoalescing();installObserver();ensureSeasonInvariant();
  // Prime the small, league-neutral schedule before a user opens a weekly view.
  setTimeout(()=>ensureSchedule(activeSeason()).catch(()=>{}),50);
  const complete=dataClientWrapped&&leagueSimGuardInstalled&&renderWrapped;
  if(!complete&&installAttempts<80)setTimeout(install,100);else scheduleDomEnhance();
}

window.FIE933ABC={installed:true,VERSION,RELEASE,diagnostics,ensureSchedule,loadSelectedWeek,setWeek,opponentForTeam,currentContext,repairPlayerNames,flushAutomaticRender};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();

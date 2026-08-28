/* Fantasy Intelligence Engine V9.3.4A-B performance rescue + correctness patch.
 * A: compact prebuilt player catalog on the cold-load critical path, cooperative
 *    enhancement staging, off-main-thread CSV parsing, cheap week switches and
 *    one coherent enhancement publication.
 * B: canonical NFL team aliases, first-render D/ST/K next-three preloading,
 *    Start/Sit panel isolation and league-capability position filters.
 *
 * The file name stays stable so the generated shell does not need another large
 * loader edit. FIE933ABC remains a compatibility alias for older diagnostics.
 */
(function(){
'use strict';
if(window.FIE934AB?.installed)return;

const VERSION='9.3.4A-B';
const RELEASE='performance-rescue-correctness-quickwins';
const DAY=24*60*60*1000;
const PLAYER_CATALOG_URL='/data/research/app/player-catalog.json';
const PLAYER_CATALOG_TTL=6*60*60*1000;
const PLAYER_CATALOG_GATE_MS=7000;
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
let deferredScoreToken=0;
let playerCatalogPromise=null;
let playerCatalogGateWrapped=false;
let cooperativeEnhancementsWrapped=false;
let optimizedPublicEnrichmentWrapped=false;
let csvFastPathWrapped=false;
let csvWorker=null;
let csvWorkerFailed=false;
let csvJobSeq=0;
const csvJobs=new Map();
let userRenderTickets=0;
let lastRenderedTab=null;
let specialTeamsWrapped=false;
const specialTeamsReady=new Set();
const specialTeamsInflight=new Map();
const diagnostics={staleSimulationRejects:0,snapshotFastHits:0,snapshotFastMisses:0,scheduleLoads:0,weeklyProjectionLoads:0,automaticRendersSuppressed:0,liveOverlayChanges:0,playerCatalogHits:0,playerCatalogMisses:0,playerCatalogPlayers:0,playerCatalogGateMs:0,csvWorkerParses:0,csvWorkerFallbacks:0,deferredScoreRecomputes:0,specialTeamsPreloads:0,publicEnrichmentRuns:0,publicEnrichmentYields:0,atomicPlayerPublishes:0,deferredAssignScoreCalls:0,enhancementStages:{}};

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
function diag(error,meta={}){try{core().Diagnostics?.capture?.(error,{domain:'v9.3.4-runtime',...meta});}catch{} }
function markUserInput(ev){lastUserInput=Date.now();const t=ev?.target;if(t?.closest?.('button,a,select,input,[data-tab],[role=\"tab\"],.tab,.subtab'))userRenderTickets=Math.min(3,userRenderTickets+2);}
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
const NFL_TEAM_ALIASES=Object.freeze({LA:'LAR',LAR:'LAR',STL:'LAR',JAC:'JAX',JAX:'JAX',WSH:'WAS',WAS:'WAS',OAK:'LV',LV:'LV',SD:'LAC',LAC:'LAC',SFO:'SF',SF:'SF',GBP:'GB',GB:'GB',KCC:'KC',KC:'KC',NEP:'NE',NE:'NE',NOS:'NO',NO:'NO',TBB:'TB',TB:'TB'});
function normalizeNFLTeam(team){const raw=String(team||'').trim().toUpperCase();return raw?NFL_TEAM_ALIASES[raw]||raw:'';}
function scheduleGame(team,week=activeWeek(),season=activeSeason()){
  const t=normalizeNFLTeam(team);if(!t)return null;
  return (stateObj()?.weekly?.schedule||[]).find(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG')&&(normalizeNFLTeam(g.home_team)===t||normalizeNFLTeam(g.away_team)===t))||null;
}
function schedulePublished(week=activeWeek(),season=activeSeason()){return (stateObj()?.weekly?.schedule||[]).some(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG'));}
function opponentForTeam(team,week=activeWeek(),season=activeSeason()){
  const g=scheduleGame(team,week,season),t=normalizeNFLTeam(team);if(g)return normalizeNFLTeam(g.home_team)===t?normalizeNFLTeam(g.away_team):normalizeNFLTeam(g.home_team);return t&&schedulePublished(week,season)?'BYE':'—';
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
function sameContext(c){const n=currentContext();return String(c?.leagueId||'')===String(n.leagueId||'')&&Number(c?.season)===Number(n.season)&&Number(c?.week)===Number(n.week);}
function scheduleDeferredScoreRecompute(reason){
  const token=++deferredScoreToken,c=currentContext();setTimeout(async()=>{await idle(1200);if(token!==deferredScoreToken||!sameContext(c)||enrichmentActive)return;const started=performance.now();try{window.assignScores?.(reason);diagnostics.deferredScoreRecomputes++;window.FIEPerformance?.push?.('934:deferred-week-score',performance.now()-started,{leagueId:c.leagueId,week:c.week});}catch(e){diag(e,{feature:'deferred-week-score'});}},0);
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
  scheduleDeferredScoreRecompute(`V9.3.4 selected-week ${week}`);
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
function setWeek(w,{reason='user-week-change',rerunSimulation=false}={}){
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
function playerCatalogFresh(){const map=window.__FIE_PLAYER_MAP_CACHE,at=Number(window.__FIE_PLAYER_MAP_CACHE_AT||0);return !!map&&typeof map==='object'&&Object.keys(map).length>=500&&Date.now()-at<DAY;}
async function primePlayerCatalog({force=false}={}){
  if(!force&&playerCatalogFresh()){diagnostics.playerCatalogHits++;diagnostics.playerCatalogPlayers=Object.keys(window.__FIE_PLAYER_MAP_CACHE||{}).length;return window.__FIE_PLAYER_MAP_CACHE;}
  if(!force&&playerCatalogPromise)return playerCatalogPromise;
  const load=(async()=>{try{const d=window.FIEDataClient,obj=d?.json?await d.json(PLAYER_CATALOG_URL,{sourceId:'player-catalog-fast',ttlMs:PLAYER_CATALOG_TTL,persist:true,maxBytes:8*1024*1024,cache:force?'reload':'default'}):await fetch(PLAYER_CATALOG_URL,{cache:force?'reload':'default'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();});const rows=obj?.players;if(obj?.schema!=='fie-player-catalog-v1'||!rows||typeof rows!=='object'||Array.isArray(rows)||Object.keys(rows).length<500)throw new Error('Invalid compact player catalog');window.__FIE_PLAYER_MAP_CACHE=rows;window.__FIE_PLAYER_MAP_CACHE_AT=Date.now();try{localStorage.setItem('fiePlayerMapStoredAt',String(window.__FIE_PLAYER_MAP_CACHE_AT));}catch{}diagnostics.playerCatalogHits++;diagnostics.playerCatalogPlayers=Object.keys(rows).length;window.dispatchEvent(new CustomEvent('fie:player-catalog-ready',{detail:{players:diagnostics.playerCatalogPlayers}}));return rows;}catch(e){diagnostics.playerCatalogMisses++;diag(e,{feature:'player-catalog'});return null;}})();playerCatalogPromise=load;try{return await load;}finally{playerCatalogPromise=null;}
}
function installPlayerCatalogGate(){
  const ctl=window.FIELeagueController;if(!ctl||playerCatalogGateWrapped||ctl.switchLeague?.__fie934PlayerCatalogGate)return !!ctl;const original=ctl.switchLeague;
  ctl.switchLeague=async function(){const started=performance.now();if(!playerCatalogFresh()){const gate=primePlayerCatalog();await Promise.race([gate,new Promise(resolve=>setTimeout(resolve,PLAYER_CATALOG_GATE_MS))]);}diagnostics.playerCatalogGateMs=Math.round((performance.now()-started)*10)/10;window.FIEPerformance?.push?.('934:player-catalog-gate',diagnostics.playerCatalogGateMs,{players:diagnostics.playerCatalogPlayers});return original.apply(this,arguments);};ctl.switchLeague.__fie934PlayerCatalogGate=true;ctl.__fie934OriginalSwitchLeague=original;playerCatalogGateWrapped=true;return true;
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
  function wrappedRender(){const tab=String(stateObj()?.activeTab||''),tabChanged=lastRenderedTab!==null&&tab!==lastRenderedTab,userRender=userRenderTickets>0||tabChanged;if(enrichmentActive&&!renderBypass&&!userRender){pendingRender=true;diagnostics.automaticRendersSuppressed++;return;}const r=originalRender.apply(this,arguments);lastRenderedTab=tab;if(userRenderTickets>0)userRenderTickets--;scheduleDomEnhance();return r;}wrappedRender.__fie934Wrapped=true;
  window.render=wrappedRender;
  if(originalUpdateKPIs){window.updateKPIs=function(){if(enrichmentActive&&!renderBypass&&userRenderTickets<=0){pendingKpis=true;return;}return originalUpdateKPIs.apply(this,arguments);};window.updateKPIs.__fie934Wrapped=true;}
  renderWrapped=true;return true;
}
function renderCoreOnce(){forceRender(()=>{try{originalUpdateKPIs?.();originalRender?.();lastRenderedTab=String(stateObj()?.activeTab||'');scheduleDomEnhance();}catch(e){diag(e,{feature:'core-render'});}});}
function flushAutomaticRender(){const doKpi=pendingKpis,doRender=pendingRender;pendingKpis=false;pendingRender=false;forceRender(()=>{try{if(doKpi||doRender)originalUpdateKPIs?.();if(doRender||doKpi)originalRender?.();lastRenderedTab=String(stateObj()?.activeTab||'');scheduleDomEnhance();}catch(e){diag(e,{feature:'enhanced-render-flush'});}});}
function installEnrichmentYield(){
  if(enrichmentYieldWrapped||typeof window.loadPublicEnrichment!=='function')return false;const original=window.loadPublicEnrichment;
  window.loadPublicEnrichment=async function(){await idle(900);return original.apply(this,arguments);};window.loadPublicEnrichment.__fie934Yield=true;window.loadPublicEnrichment.__fie934Original=original;enrichmentYieldWrapped=true;return true;
}
function csvWorkerInstance(){
  if(csvWorkerFailed||typeof Worker==='undefined')return null;if(csvWorker)return csvWorker;try{const url=new URL('app/workers/csv-parse-worker.js?v=9.3.4',document.baseURI).href;csvWorker=new Worker(url);csvWorker.onmessage=e=>{const id=Number(e.data?.id),job=csvJobs.get(id);if(!job)return;csvJobs.delete(id);clearTimeout(job.timer);if(e.data?.error)job.reject(new Error(e.data.error));else job.resolve(e.data?.rows||[]);};csvWorker.onerror=e=>{csvWorkerFailed=true;try{csvWorker?.terminate?.();}catch{}csvWorker=null;for(const [id,job] of csvJobs){clearTimeout(job.timer);job.reject(new Error(e?.message||'CSV worker failed'));csvJobs.delete(id);}};return csvWorker;}catch(e){csvWorkerFailed=true;diag(e,{feature:'csv-worker-create'});return null;}
}
async function parseCSVOffMain(text){const raw=String(text||'');if(raw.length<120000)return parseCSV(raw);const worker=csvWorkerInstance();if(!worker){diagnostics.csvWorkerFallbacks++;await idle(400);return parseCSV(raw);}const id=++csvJobSeq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{csvJobs.delete(id);reject(new Error('CSV worker timeout'));},90000);csvJobs.set(id,{resolve,reject,timer});try{worker.postMessage({id,text:raw});diagnostics.csvWorkerParses++;}catch(e){clearTimeout(timer);csvJobs.delete(id);reject(e);}}).catch(async e=>{diagnostics.csvWorkerFallbacks++;diag(e,{feature:'csv-worker-parse'});await idle(400);return parseCSV(raw);});}
function installCsvFastPath(){
  if(csvFastPathWrapped||typeof window.fetchCSV!=='function')return false;const original=window.fetchCSV;window.fetchCSV=async function(url){const started=performance.now(),u=String(url||'');try{const d=window.FIEDataClient;if(!d?.text)return original.apply(this,arguments);const text=await d.text(u,{sourceId:'public-csv-worker',ttlMs:6*60*60*1000,persist:true,maxBytes:50*1024*1024});const rows=await parseCSVOffMain(text);window.FIEPerformance?.push?.('934:csv-fetch-parse',performance.now()-started,{url:d.sanitizeUrl?.(u)||u,rows:rows.length});try{window.recordSourceHealthV7?.(d.sanitizeUrl?.(u)||u,{ok:true,status:200,headers:{get:k=>String(k||'').toLowerCase()==='x-fie-cache'?'FIE_CACHE':null}},performance.now()-started);}catch{}return rows;}catch(e){try{window.recordSourceFailureV7?.(u,e,performance.now()-started);}catch{}throw e;}};window.fetchCSV.__fie934Worker=true;window.fetchCSV.__fie934Original=original;csvFastPathWrapped=true;return true;
}

function publicNormName(value){return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\b(jr|sr|ii|iii|iv)\b\.?/g,'').replace(/[^a-z0-9]/g,'');}
function publicNumber(row,...keys){for(const key of keys){const v=finite(row?.[key]);if(v!==null)return v;}return null;}
async function cooperativeRows(rows,fn,{chunk=180,current=()=>true}={}){for(let i=0;i<(rows||[]).length;i++){if(!current())return false;fn(rows[i],i);if(i&&i%chunk===0){diagnostics.publicEnrichmentYields++;await idle(80);}}return current();}
function applyPositionPercentile(rows,key){const groups={};for(const p of rows||[]){const v=finite(p?.[key]);if(v===null)continue;(groups[p.position]??=[]).push(v);}for(const xs of Object.values(groups))xs.sort((a,b)=>a-b);for(const p of rows||[]){const v=finite(p?.[key]),xs=groups[p.position];if(v===null||!xs?.length){p[`${key}Percentile`]=null;continue;}let lo=0,hi=xs.length;while(lo<hi){const m=(lo+hi)>>1;if(xs[m]<=v)lo=m+1;else hi=m;}p[`${key}Percentile`]=Math.round((25+70*(lo/xs.length))*10)/10;}}
function bestContractIndex(rows){const byOtc=new Map(),byName=new Map(),push=(m,k,r)=>{if(!k)return;(m.get(k)??(m.set(k,[]),m.get(k))).push(r);};for(const r of rows||[]){push(byOtc,String(r?.otc_id||''),r);push(byName,publicNormName(r?.player),r);}const best=xs=>{if(!xs?.length)return null;const active=xs.filter(r=>String(r?.is_active).toLowerCase()==='true'||String(r?.is_active)==='1'),pool=active.length?active:xs;return pool.reduce((a,b)=>!a||Number(b?.year_signed||0)>Number(a?.year_signed||0)?b:a,null);};return p=>best(byOtc.get(String(p?.otcId||'')))||best(byName.get(publicNormName(p?.name)));}
async function optimizedPublicEnrichment(){
  const st=stateObj(),startLeague=leagueId();if(!st||!startLeague)return null;const current=()=>String(leagueId())===String(startLeague),prior=Math.max(2000,activeSeason()-1),urls={players:'/api/data/nflverse/players',contracts:'/api/data/nflverse/contracts',stats:`/api/data/nflverse/stats-regpost-${prior}`,snaps:`/api/data/nflverse/snaps-${prior}`};
  st.publicErrors=[];st.publicStatus={players:false,contracts:false,stats:false,snaps:false};const settled=await Promise.allSettled(Object.entries(urls).map(async([k,u])=>[k,await window.fetchCSV(u)]));if(!current())return null;const data={};for(const x of settled){if(x.status==='fulfilled'){data[x.value[0]]=x.value[1]||[];st.publicStatus[x.value[0]]=true;}else st.publicErrors.push(String(x.reason?.message||x.reason));}
  const pool=window.PLAYERS||[],playerRows=data.players||[],byGsis=new Map(),byName=new Map();await cooperativeRows(playerRows,r=>{if(r?.gsis_id)byGsis.set(String(r.gsis_id),r);const z=publicNormName(r?.display_name||r?.full_name||r?.player_name||r?.name);if(z&&!byName.has(z))byName.set(z,r);},{chunk:1800,current});if(!current())return null;
  await cooperativeRows(pool,p=>{const r=byGsis.get(String(p?.gsisId||''))||byName.get(publicNormName(p?.name));if(!r)return;p.publicPlayerId=r.gsis_id||null;p.pfrId=r.pfr_id||null;p.otcId=r.otc_id||null;p.draftYear=finite(r.draft_year);p.draftRound=finite(r.draft_round);p.draftPick=finite(r.draft_pick);if(typeof window.draftCapitalScore==='function')p.draftScore=window.draftCapitalScore(p.draftRound,p.draftPick,p.yearsExp);if(!p.age&&r.birth_date){const d=new Date(r.birth_date);if(!Number.isNaN(d.getTime()))p.age=Math.floor((new Date(`${activeSeason()}-09-01`)-d)/(365.2425*864e5));}if(typeof window.ageCurveScore==='function')p.ageCurveScore=window.ageCurveScore(p.position,p.age);},{current});if(!current())return null;
  const contractFor=bestContractIndex(data.contracts||[]);await cooperativeRows(pool,p=>{const c=contractFor(p);if(!c)return;if(typeof window.contractScoreFrom==='function')p.contractScore=window.contractScoreFrom(c);const signed=finite(c.year_signed),years=finite(c.years);p.contractEnd=signed!==null&&years!==null?signed+years-1:null;p.contractApy=finite(c.apy);p.contractGuaranteed=finite(c.guaranteed);p.contractYears=years;p.contractSource='OverTheCap via nflverse';},{current});if(!current())return null;
  const statById=new Map();await cooperativeRows(data.stats||[],r=>{const id=String(r?.player_id||r?.gsis_id||'');if(id)statById.set(id,r);},{chunk:2200,current});if(!current())return null;await cooperativeRows(pool,p=>{const r=statById.get(String(p?.gsisId||p?.publicPlayerId||''));if(!r)return;const pts=typeof window.scorePublicStats==='function'?finite(window.scorePublicStats(r,p)):null;p.publicFantasyPoints=pts;const games=publicNumber(r,'games','games_played','player_game_count');p.publicFantasyPPG=pts!==null&&games!==null&&games>0?pts/games:null;},{current});applyPositionPercentile(pool,'publicFantasyPPG');for(const p of pool)p.productionScore=p.publicFantasyPPGPercentile??null;
  const snapAgg=new Map();await cooperativeRows(data.snaps||[],r=>{const id=String(r?.pfr_player_id||r?.pfr_id||'');if(!id)return;const vals=[publicNumber(r,'offense_pct','off_pct'),publicNumber(r,'defense_pct','def_pct'),publicNumber(r,'st_pct','special_teams_pct')].filter(v=>v!==null),val=vals.length?Math.max(...vals):null;if(val===null)return;const a=snapAgg.get(id)||{sum:0,n:0};a.sum+=val;a.n++;snapAgg.set(id,a);},{chunk:2200,current});if(!current())return null;await cooperativeRows(pool,p=>{const a=snapAgg.get(String(p?.pfrId||''));if(!a)return;p.snapShare=Math.round((a.sum/a.n)*10)/10;if(finite(p.productionScore)!==null){const rel=Math.max(0,Math.min(1,p.snapShare>1?p.snapShare/100:p.snapShare));p.productionScore=Math.round((50+(p.productionScore-50)*(.45+.55*Math.sqrt(rel)))*10)/10;}},{current});
  const ctp={};for(const p of pool)ctp[`${p.team}|${p.position}|${p.depthOrder}`]=p;if(typeof window.incumbentPathAdjust==='function')await cooperativeRows(pool,p=>{const adj=finite(window.incumbentPathAdjust(p,ctp));if(adj){p.futureOpportunity=Math.max(10,Math.min(98,(finite(p.futureOpportunity)??50)+adj));p.contractPathAdjustment=adj;}},{current});if(!current())return null;diagnostics.publicEnrichmentRuns++;return{leagueId:startLeague,sourceRows:Object.fromEntries(Object.entries(data).map(([k,v])=>[k,v.length]))};
}
function installOptimizedPublicEnrichment(){if(optimizedPublicEnrichmentWrapped||typeof window.loadPublicEnrichment!=='function')return false;const original=window.loadPublicEnrichment;window.loadPublicEnrichment=optimizedPublicEnrichment;window.loadPublicEnrichment.__fie934Optimized=true;window.loadPublicEnrichment.__fie934Original=original;optimizedPublicEnrichmentWrapped=true;enrichmentYieldWrapped=true;return true;}
function isVolatilePlayerField(key){return /^(?:weekly|sleeperWeekly|opponent$|availability$|owner(?:RosterId)?$|roster|isStarter$|isTaxi$|isReserve$|matchup)/i.test(String(key||''))||['rangeSource','weeklyFloor','weeklyCeiling','weeklyProjectionSource','__fieWeeklyByWeek'].includes(String(key||''));}
function capturePlayerState(){return new Map((window.PLAYERS||[]).map(p=>[playerId(p)||String(p?.name||''),clone(p)]));}
function mergePlayerDiff(staging,published,result){for(const [id,row] of result){const base=published.get(id)||{},target=staging.get(id)||clone(base),keys=new Set([...Object.keys(base),...Object.keys(row)]);for(const key of keys){if(isVolatilePlayerField(key))continue;let a,b;try{a=JSON.stringify(base[key]);b=JSON.stringify(row[key]);}catch{a=base[key];b=row[key];}if(a!==b){if(!(key in row))delete target[key];else target[key]=clone(row[key]);}}staging.set(id,target);}return staging;}
function restorePlayerState(snapshot){const byId=new Map((window.PLAYERS||[]).map(p=>[playerId(p)||String(p?.name||''),p]));for(const [id,row] of snapshot){const p=byId.get(id);if(!p)continue;for(const key of Object.keys(p))if(!isVolatilePlayerField(key)&&!(key in row))delete p[key];for(const [key,value] of Object.entries(row))if(!isVolatilePlayerField(key))p[key]=clone(value);}}
async function enhancementStage(name,id,current,fn){if(!current())return null;await idle(1100);if(!current())return null;const started=performance.now();try{return await fn();}catch(e){if(e?.name!=='AbortError')diag(e,{feature:`enhancement-${name}`,leagueId:id});return null;}finally{const ms=performance.now()-started;diagnostics.enhancementStages[name]={ms:Math.round(ms*10)/10,at:Date.now(),leagueId:id};window.FIEPerformance?.push?.(`934:${name}`,ms,{leagueId:id});await idle(700);}}
function installCooperativeEnhancements(){
  const ctl=window.FIELeagueController;if(!ctl||cooperativeEnhancementsWrapped||ctl.loadEnhancements?.__fie934Cooperative)return !!ctl;const original=ctl.loadEnhancements;
  ctl.loadEnhancements=async function(scope){
    const id=String(scope?.leagueId||''),signal=scope?.signal,current=()=>!!scope?.isCurrent?.(),st=stateObj(),status=document.getElementById('status'),base='https://api.sleeper.app/v1';enrichmentActive=true;
    const published=capturePlayerState(),staging=new Map([...published].map(([k,v])=>[k,clone(v)])),publishedReplacement=clone(st?.projectedReplacementLevels||{}),publishedReplacement2=clone(st?.replacementLevels||{}),originalAssign=typeof window.assignScores==='function'?window.assignScores:null;let queuedScoreReason='';
    if(originalAssign)window.assignScores=function(reason){queuedScoreReason=String(reason||queuedScoreReason||'enhancement');diagnostics.deferredAssignScoreCalls++;return null;};
    const trend=(async()=>{try{const rows=await window.FIEDataClient?.json?.(`${base}/players/nfl/trending/add?lookback_hours=24&limit=100`,{signal,sourceId:'sleeper-trending'});if(current()&&st)st.trending=Object.fromEntries((rows||[]).map(x=>[x.player_id,Number(x.count)||0]));}catch(e){if(e?.name!=='AbortError')diag(e,{feature:'enhancement-trending',leagueId:id});}})();
    const staged=async(name,fn)=>{restorePlayerState(published);if(st){st.projectedReplacementLevels=clone(publishedReplacement);st.replacementLevels=clone(publishedReplacement2);}await enhancementStage(name,id,current,fn);if(!current())return false;const result=capturePlayerState();mergePlayerDiff(staging,published,result);restorePlayerState(published);if(st){st.projectedReplacementLevels=clone(publishedReplacement);st.replacementLevels=clone(publishedReplacement2);}return true;};
    try{
      if(!await staged('season-projections',async()=>{if(typeof window.loadSleeperSeasonProjections==='function')await window.loadSleeperSeasonProjections();}))return null;
      if(!await staged('research',async()=>{await Promise.allSettled([window.FIE_M5?.loadMilestone5Research?.(),window.FIE_M5?.loadM5Current?.(),window.FIE_M6?.loadM6?.()]);if(current())window.FIECurrentFeatures?.apply?.();}))return null;
      if(!await staged('public-enrichment',async()=>{if(typeof window.loadPublicEnrichment==='function')await window.loadPublicEnrichment();}))return null;
      await trend;if(!current())return null;restorePlayerState(staging);if(originalAssign){window.assignScores=originalAssign;const started=performance.now();originalAssign(`V9.3.4 atomic enhancement publish${queuedScoreReason?` · ${queuedScoreReason}`:''}`);window.FIEPerformance?.push?.('934:atomic-score-publish',performance.now()-started,{leagueId:id});}try{window.FIEDraftBaseValueService?.invalidate?.();window.FIE_VALUE_FINDER?.invalidate?.('V9.3.4 atomic enhancement publish');}catch{}diagnostics.atomicPlayerPublishes++;
      const pub=st?.publicStatus||{},labels={players:'identity',contracts:'contracts',stats:'production',snaps:'snaps'},publicText=Object.keys(labels).map(k=>`${labels[k]} ${pub[k]?'✓':'✕'}`).join(' · ');if(status)status.textContent=`Loaded ${st?.league?.name||id}: ${(window.PLAYERS||[]).length} active players. Public data: ${publicText}. Season projections ${st?.projectionStatus?.season?`${st.projectionStatus.seasonCount||0} matched`:'fallback active'}.`;window.dispatchEvent(new CustomEvent('fie:league-loaded',{detail:{leagueId:id,generation:scope?.generation,stage:'enhanced'}}));return true;
    }finally{if(originalAssign&&window.assignScores!==originalAssign)window.assignScores=originalAssign;if(!current())restorePlayerState(published);}
  };
  ctl.loadEnhancements.__fie934Cooperative=true;ctl.__fie934OriginalLoadEnhancements=original;cooperativeEnhancementsWrapped=true;return true;
}

/* ------------------------- B · correctness quick wins -------------------- */
function specialTeamsKey(w=activeWeek(),s=activeSeason()){return `${s}:${w}`;}
async function preloadSpecialTeamsWindow(w=activeWeek(),s=activeSeason()){
  const week=Math.max(1,Math.min(18,Number(w)||1)),key=specialTeamsKey(week,s);if(specialTeamsReady.has(key))return true;if(specialTeamsInflight.has(key))return specialTeamsInflight.get(key);const svc=window.FIESpecialTeamsSeries;if(!svc?.preloadWeeks)return false;const p=(async()=>{await ensureSchedule(s);await svc.preloadWeeks([week,week+1,week+2].filter(x=>x<=18),s);specialTeamsReady.add(key);diagnostics.specialTeamsPreloads++;return true;})().catch(e=>{diag(e,{feature:'special-teams-preload',week,season:s});return false;}).finally(()=>specialTeamsInflight.delete(key));specialTeamsInflight.set(key,p);return p;
}
function installSpecialTeamsOverrides(){
  const series=window.FIESpecialTeamsSeries;if(series)series.opponent=(team,w,s)=>opponentForTeam(team,w,s);if(specialTeamsWrapped)return true;let wrapped=0;for(const [name,statusId] of [['FIEDST','dstStatus'],['FIEKicker','kickerStatus']]){const svc=window[name];if(!svc||svc.render?.__fie934Preload){if(svc?.render?.__fie934Preload)wrapped++;continue;}const original=svc.render.bind(svc);svc.render=function(){const w=activeWeek(),s=activeSeason(),key=specialTeamsKey(w,s);if(specialTeamsReady.has(key))return original(...arguments);const status=document.getElementById(statusId);if(status)status.textContent='Loading selected week + next two weeks…';preloadSpecialTeamsWindow(w,s).then(()=>{if(Number(activeWeek())===Number(w)&&Number(activeSeason())===Number(s))original();});};svc.render.__fie934Preload=true;svc.render.__fie934Original=original;wrapped++;}specialTeamsWrapped=wrapped===2;return wrapped>0;
}
const POSITION_ORDER=['QB','RB','WR','TE','K','DEF','DL','LB','DB','P','OL'];
function syncLeaguePositionFilter(){const el=document.getElementById('posFilter'),c=window.FIELeagueContext?.current?.();if(!el||!c)return;const canon=x=>window.FIECore?.PositionRegistry?.canonical?.(x)||String(x||'').toUpperCase(),legal=[...new Set((c.legalPositions||[]).map(canon).filter(Boolean))],present=new Set((window.PLAYERS||[]).map(p=>canon(p?.position))),usable=legal.filter(x=>POSITION_ORDER.includes(x)&&(present.has(x)||['QB','RB','WR','TE','K','DEF','DL','LB','DB'].includes(x))).sort((a,b)=>POSITION_ORDER.indexOf(a)-POSITION_ORDER.indexOf(b)),sig=usable.join('|');if(el.dataset.fie934Positions===sig)return;const old=canon(el.value),label=x=>x==='DEF'?'D/ST':x;el.innerHTML='<option value="ALL">All</option>'+usable.map(x=>`<option value="${x}">${label(x)}</option>`).join('');el.value=usable.includes(old)?old:'ALL';el.dataset.fie934Positions=sig;}
function syncWeeklyPanelVisibility(){const panel=document.getElementById('fie93WeeklyPanel');if(!panel)return;const show=String(stateObj()?.activeTab||'')==='startsit';panel.hidden=!show;panel.classList.toggle('fie93-hidden',!show);}

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
function enhanceDiagnosticsVersion(){const tag=document.querySelector('#fieRuntimeDiagnosticsV9 .tag');if(tag)tag.textContent='V9.3.4';}
function enhanceDom(){domTimer=null;try{ensureSeasonInvariant();repairPlayerNames();installSpecialTeamsOverrides();syncWeeklyPanelVisibility();syncLeaguePositionFilter();injectMatchupWeekControl();relabelNext3();addRangeNote('dstSummary');addRangeNote('kickerSummary');repairSeasonZeroText();enhanceDiagnosticsVersion();}catch(e){diag(e,{feature:'dom-enhance'});}}
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
    Promise.allSettled([ensureSchedule(activeSeason()),loadSelectedWeek(activeWeek(),{reason:'core',rerunSimulation:false})]).then(()=>{preloadSpecialTeamsWindow(activeWeek()).catch(()=>{});scheduleDomEnhance();});
  }else if(stage==='enhanced'){
    switchingLeagueId=null;enrichmentActive=false;repairPlayerNames();flushAutomaticRender();scheduleDomEnhance();
  }
});
window.addEventListener('fie:league-live-update',e=>applyLiveOverlay(e?.detail||{}));
window.addEventListener('fie:schedule-ready',()=>{installSpecialTeamsOverrides();preloadSpecialTeamsWindow(activeWeek()).catch(()=>{});try{window.FIEDST?.render?.();window.FIEKicker?.render?.();}catch{}scheduleDomEnhance();});
document.addEventListener('change',e=>{if(e.target?.id==='weekSelect'){const w=Number(e.target.value)||1;setWeek(w,{reason:'user-week-change',rerunSimulation:stateObj()?.activeTab==='matchupsim'});preloadSpecialTeamsWindow(w).catch(()=>{});}},true);

function install(){
  installAttempts++;installDataClientFastPath();installPlayerCatalogGate();installLeagueSimGuard();installEnrichmentYield();installCsvFastPath();installOptimizedPublicEnrichment();installCooperativeEnhancements();installRenderCoalescing();installSpecialTeamsOverrides();installObserver();ensureSeasonInvariant();
  // Prime small shared inputs before the user asks for a league or weekly view.
  if(installAttempts===1)primePlayerCatalog().catch(()=>{});
  setTimeout(()=>ensureSchedule(activeSeason()).catch(()=>{}),50);
  const complete=dataClientWrapped&&leagueSimGuardInstalled&&renderWrapped&&playerCatalogGateWrapped&&csvFastPathWrapped&&optimizedPublicEnrichmentWrapped&&cooperativeEnhancementsWrapped;
  if(!complete&&installAttempts<80)setTimeout(install,100);else scheduleDomEnhance();
}

const API={installed:true,VERSION,RELEASE,diagnostics,ensureSchedule,loadSelectedWeek,setWeek,opponentForTeam,normalizeNFLTeam,currentContext,repairPlayerNames,flushAutomaticRender,primePlayerCatalog,preloadSpecialTeamsWindow,syncLeaguePositionFilter};
window.FIE934AB=API;window.FIE933ABC=API;
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();

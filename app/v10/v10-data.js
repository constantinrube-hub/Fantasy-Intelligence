/* FIE UI v10 data layer (R1 · WP1.3/WP1.5) — the "light pass".
 *
 * Loads the explicit inputs a WeekModel needs, for any managed league, WITHOUT loading the
 * league into the classic runtime: Sleeper league/rosters/users/matchups (live, never the
 * research snapshot), the Sleeper weekly projection feed (shared across leagues), the nflverse
 * schedule (shared) and the player catalog (shared). Every request goes through FIEDataClient
 * (CHANGE_GUIDE rule 4). Overview and league views both call model(), so they show identical
 * numbers by construction (A-03).
 *
 * Cache lifetimes come from config/ui-decision-policy.json › cache_seconds; refresh() forces a
 * re-read of everything league-specific plus the projection feed.
 */
(function(){
'use strict';
const VERSION='10.2.0';
const SLEEPER='https://api.sleeper.app/v1';
const W=()=>window;
const P=()=>W().FIE_UI_POLICY||{};
const ttl=(k,d)=>1000*(Number(P().cache_seconds?.[k])||d);
const shared={catalog:null,schedule:null,proj:new Map(),state:null,adp:new Map()};
const fetchedAt=new Map();   // url → time of our last successful network-or-cache read
const models=new Map();      // `${leagueId}:${week}` → {at, wm, inputs}
let forceGen=0;              // refresh() bumps this; each URL then bypasses caches exactly once
const forcedAt=new Map();    // url → forceGen it was last re-read at
function client(){const c=W().FIEDataClient;if(!c)throw new Error('FIEDataClient missing');return c;}
async function json(url,{ttlMs,sourceId,live=false,persist}={}){
  const f=forceGen>0&&forcedAt.get(url)!==forceGen;if(f)forcedAt.set(url,forceGen);
  const value=await client().json(url,{sourceId,ttlMs:f?0:ttlMs,live,persist,cache:f?'no-store':'default'});
  fetchedAt.set(url,Date.now());return value;
}
async function nflState(){
  try{const s=await json(`${SLEEPER}/state/nfl`,{ttlMs:ttl('nfl_state',600),sourceId:'v10-nfl-state',live:true});shared.state=s;return s;}catch{return shared.state;}
}
async function catalog(){
  if(shared.catalog)return shared.catalog;
  shared.catalog=(async()=>{const c=await json('/data/research/app/player-catalog.json',{sourceId:'v10-player-catalog',ttlMs:6*3600e3});return new Map(Object.entries({...(c?.identity_only_players||{}),...(c?.players||{})}));})();
  try{return await shared.catalog;}catch(e){shared.catalog=null;throw e;}
}
async function schedule(){
  if(shared.schedule)return shared.schedule;
  shared.schedule=(async()=>{const t=await client().text('/api/data/nflverse/schedule',{sourceId:'v10-schedule',ttlMs:6*3600e3});return W().FIEGameState.index(t);})();
  try{return await shared.schedule;}catch(e){shared.schedule=null;throw e;}
}
async function projections(season,week){
  const key=`${season}:${week}`,url=`/api/data/sleeper/projections/${season}/${week}`;
  if(shared.proj.has(key))return shared.proj.get(key);
  const p=(async()=>{const rows=await json(url,{sourceId:'v10-week-projections',ttlMs:15*60e3});const m=new Map();for(const r of rows||[]){const id=String(r?.player_id||'');if(id)m.set(id,r);}return{rows:m,at:fetchedAt.get(url)||Date.now()};})();
  shared.proj.set(key,p);
  try{return await p;}catch(e){shared.proj.delete(key);throw e;}
}
/** Projection maps for week … week+n−1 (≤ 18). A week that fails to load is an empty map. */
async function horizon(season,week,n){
  const weeks=[];for(let i=0;i<n&&week+i<=18;i++)weeks.push(week+i);
  return Promise.all(weeks.map(async w=>({week:w,projRows:(await projections(season,w).catch(()=>({rows:new Map()}))).rows})));
}
/** Sleeper season projections per player: ADP (dynasty drop protection, redraft tie-break) and the season stat line (rest-of-season proxy for unpublished weeks). */
async function seasonAdp(season){
  if(shared.adp.has(season))return shared.adp.get(season);
  const p=(async()=>{const rows=await json(`/api/data/sleeper/projections/${season}`,{sourceId:'v10-season-adp',ttlMs:6*3600e3});const m=new Map();
    for(const r of rows||[]){const id=String(r?.player_id||''),st=r?.stats||{};if(id)m.set(id,{dynasty:st.adp_dynasty_ppr??st.adp_dynasty,dynasty2qb:st.adp_dynasty_2qb,redraft:st.adp_ppr,stats:st});}return m;})();
  shared.adp.set(season,p);try{return await p;}catch(e){shared.adp.delete(season);return new Map();}
}
/** All transactions of weeks 1…upTo (past weeks cached 6 h, the current week 10 min). */
async function transactions(id,upTo){
  const ws=[];for(let w=1;w<=Math.min(18,upTo);w++)ws.push(w);
  const parts=await Promise.all(ws.map(w=>json(`${SLEEPER}/league/${id}/transactions/${w}`,{sourceId:'v10-transactions',ttlMs:w<upTo?6*3600e3:ttl('matchups',600),live:true}).catch(()=>[])));
  return parts.flat().filter(Boolean);
}
/** Transactions of selected weeks only (changes feed: current and previous week). */
async function txWeeks(id,weeks){
  const parts=await Promise.all(weeks.filter(w=>w>=1&&w<=18).map(w=>json(`${SLEEPER}/league/${id}/transactions/${w}`,{sourceId:'v10-transactions',ttlMs:ttl('matchups',600),live:true}).catch(()=>[])));
  return parts.flat().filter(Boolean);
}
function constraintsFor(id){try{return W().FIEPortfolioConfig?.constraintsFor?.(String(id))||[];}catch{return [];}}
/** Waiver ranking (and optionally the FAAB market) for one league, from the same WeekModel. */
async function waivers(entry,{week=null,market=false,limit=null,pids=null}={}){
  const wm=await model(entry,{week}),id=wm.key.leagueId,base=`${SLEEPER}/league/${id}`;
  const [league,rosters,users]=await Promise.all([json(base,{ttlMs:ttl('league',3600),sourceId:'v10-league',live:true}),json(`${base}/rosters`,{ttlMs:ttl('rosters',300),sourceId:'v10-rosters',live:true}),json(`${base}/users`,{ttlMs:ttl('league',3600),sourceId:'v10-users',live:true})]);
  const n=Number(P().waivers?.horizon_weeks)||3;
  const [hz,sched,cat,adp]=await Promise.all([horizon(wm.key.season,wm.key.week,n),schedule(),catalog(),seasonAdp(wm.key.season)]);
  const result=W().FIEWaivers.build({wm,league,rosters,managedRosterId:wm.key.rosterId,horizon:hz,schedule:sched,season:wm.key.season,now:Date.now(),catalog:cat,adp,seasonRows:adp,policy:P(),constraints:constraintsFor(id),limit,...(pids?{pids}:{})});
  let mkt=null;
  if(market){const tx=await transactions(id,wm.key.week);mkt=W().FIEWaivers.market({league,rosters,users,transactions:tx,positionOf:pid=>wm.player(pid)?.position||cat.get(String(pid))?.position,nameOf:pid=>wm.player(pid)?.name||cat.get(String(pid))?.full_name||pid,managedRosterId:wm.key.rosterId});}
  return{wm,result,market:mkt};
}
function savedLeagues(){try{const x=JSON.parse(localStorage.getItem('fieSavedLeaguesV71')||'[]');return Array.isArray(x)?x:[];}catch{return [];}}
async function leagues(){
  const cfg=W().FIEPortfolioConfig;
  if(cfg&&!cfg.loaded){try{await cfg.load();}catch{}}
  const saved=new Map(savedLeagues().map(s=>[String(s.id||''),s]));
  const nice=(id,name)=>{const n=String(name||'').trim();if(n&&n!==String(id)&&!/^\d{6,}$/.test(n))return n;const alt=cfg?.statusFor?.(id)?.league_name||saved.get(String(id))?.name;return alt&&!/^\d{6,}$/.test(String(alt))?alt:(n||String(id));};
  const managed=(cfg?.managedLeagues?.()||[]).map(m=>({...m,name:nice(m.id,m.name)})),by=new Map(managed.map(m=>[String(m.id),m]));
  for(const s of savedLeagues()){const id=String(s.id||'');if(id&&!by.has(id))by.set(id,{id,name:s.name||id,formatOverride:s.formatOverride||'AUTO',priority:s.priority||'MEDIUM',managed:false});}
  const order={VERY_HIGH:0,HIGH:1,MEDIUM:2,LOW:3};
  return [...by.values()].sort((a,b)=>(order[a.priority]??2)-(order[b.priority]??2)||String(a.name).localeCompare(String(b.name)));
}
function username(){return String(W().FIEPortfolioConfig?.config?.sleeper_username||'').toLowerCase();}
function managedRoster(rosters,users){
  const u=username(),me=(users||[]).find(x=>[x.username,x.display_name].some(v=>String(v||'').toLowerCase()===u));
  if(!me)return null;const r=(rosters||[]).find(r=>String(r.owner_id)===String(me.user_id)||(r.co_owners||[]).map(String).includes(String(me.user_id)));
  return r?Number(r.roster_id):null;
}
function formatFor(league,entry){
  const res=W().FIELeagueProfileResolver?.resolve?.(league,entry?.formatOverride||'AUTO');
  const key=res?.format||(entry?.formatOverride&&entry.formatOverride!=='AUTO'?entry.formatOverride:'REDRAFT');
  return{...W().FIECore.FormatRegistry.profile(key),key};
}
function currentWeek(st,league){const w=Number(st?.week||st?.display_week);if(Number.isFinite(w)&&w>=1&&w<=18)return w;const l=Number(league?.settings?.leg);return Number.isFinite(l)&&l>=1?l:1;}
/** Build (or reuse) the WeekModel of one league. */
async function model(entry,{week=null}={}){
  const id=String(entry.id||entry.league_id||entry);
  const base=`${SLEEPER}/league/${id}`;
  const [league,rosters,users,st]=await Promise.all([
    json(base,{ttlMs:ttl('league',3600),sourceId:'v10-league',live:true}),
    json(`${base}/rosters`,{ttlMs:ttl('rosters',300),sourceId:'v10-rosters',live:true}),
    json(`${base}/users`,{ttlMs:ttl('league',3600),sourceId:'v10-users',live:true}),
    nflState()]);
  const wk=week||currentWeek(st,league),season=Number(league?.season)||Number(st?.season)||new Date().getUTCFullYear();
  const key=`${id}:${wk}`,cached=models.get(key);
  const [matchups,proj,sched,cat]=await Promise.all([
    json(`${base}/matchups/${wk}`,{ttlMs:ttl('matchups_live',120),sourceId:'v10-matchups',live:true}).catch(()=>[]),
    projections(season,wk),schedule(),catalog()]);
  const now=Date.now(),format=formatFor(league,typeof entry==='object'?entry:null);
  const inputsAt=Math.min(...[base,`${base}/rosters`,`${base}/matchups/${wk}`].map(u=>fetchedAt.get(u)||now));
  if(cached&&cached.inputsAt===inputsAt&&cached.projAt===proj.at&&now-cached.at<60e3)return cached.wm;
  const wm=W().FIEWeekModel.build({league,rosters,users,matchups,projRows:proj.rows,catalog:cat,schedule:sched,week:wk,season,now,fetchedAt:proj.at,
    managedRosterId:managedRoster(rosters,users),format,policy:P()});
  const given=String(entry.name||'').trim();
  wm.entry={id,name:(given&&given!==id&&!/^\d{6,}$/.test(given))?given:(league?.name||given||id),priority:entry.priority||'MEDIUM',managed:entry.managed!==false};
  wm.dataAt=inputsAt;wm.projectionsAt=proj.at;
  models.set(key,{at:now,inputsAt,projAt:proj.at,wm});
  return wm;
}
/** Points of a completed week (latest results): my score vs opponent / chopped survival. */
async function results(entry,week){
  if(!(week>=1))return null;const id=String(entry.id);
  try{const [rosters,users,mm]=await Promise.all([json(`${SLEEPER}/league/${id}/rosters`,{ttlMs:ttl('rosters',300),sourceId:'v10-rosters',live:true}),json(`${SLEEPER}/league/${id}/users`,{ttlMs:ttl('league',3600),sourceId:'v10-users',live:true}),json(`${SLEEPER}/league/${id}/matchups/${week}`,{ttlMs:ttl('matchups',600),sourceId:'v10-matchups-final',live:true})]);
    const rid=managedRoster(rosters,users),me=(mm||[]).find(m=>Number(m.roster_id)===rid);if(!me)return null;
    const opp=me.matchup_id!==null&&me.matchup_id!==undefined?(mm||[]).find(m=>m.matchup_id===me.matchup_id&&Number(m.roster_id)!==rid):null;
    const all=(mm||[]).map(m=>Number(m.points)||0).sort((a,b)=>b-a);
    return{week,points:Number(me.points)||0,oppPoints:opp?Number(opp.points)||0:null,rank:all.indexOf(Number(me.points)||0)+1,teams:all.length,median:all.length?all[Math.floor(all.length/2)]:null};
  }catch{return null;}
}
/** Light pass over all leagues with limited concurrency; onEach(i, result) streams rows. */
async function portfolio({week=null,limit=4,onEach,withWaivers=true,withTx=true}={}){
  const list=await leagues(),out=new Array(list.length);let next=0;
  async function worker(){while(next<list.length){const i=next++,e=list[i];
    try{const wm=await model(e,{week});let wv=null;
      if(withWaivers&&!wm.field?.meEliminated){try{wv=(await waivers(e,{week,limit:Number(P().waivers?.overview_candidates)||30})).result;}catch(err){wv=null;}}
      const tx=withTx?await txWeeks(wm.key.leagueId,[wm.key.week-1,wm.key.week]).catch(()=>[]):null;
      out[i]={entry:e,wm,waivers:wv,tx,alerts:W().FIEAlerts.forLeague(wm,{leagueId:e.id,leagueName:wm.entry.name,priority:e.priority,waivers:wv})};}
    catch(err){out[i]={entry:e,wm:null,error:String(err?.message||err),alerts:[{code:'DATA_ISSUE',tier:'urgent',quiet:true,leagueId:String(e.id),leagueName:e.name||e.id,priority:e.priority,title:`Could not load: ${String(err?.message||err).slice(0,120)}`,dedupKey:`${e.id}:load`,route:'home'}]};}
    onEach?.(i,out[i]);}}
  await Promise.all(Array.from({length:Math.min(limit,list.length)},worker));
  return out;
}
function refresh(){forceGen++;models.clear();shared.proj.clear();}
/** Matchups of any week for one league (review, results). */
async function matchups(id,week){return json(`${SLEEPER}/league/${id}/matchups/${week}`,{ttlMs:ttl('matchups',600),sourceId:'v10-matchups',live:true}).catch(()=>[]);}
function lastFetch(){return Math.max(0,...fetchedAt.values());}
window.FIEV10Data={VERSION,leagues,model,portfolio,results,waivers,horizon,seasonAdp,transactions,txWeeks,matchups,projections,schedule,catalog,nflState,refresh,lastFetch,managedRoster,currentWeek,constraintsFor,_models:models};
})();

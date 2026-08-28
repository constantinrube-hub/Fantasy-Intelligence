/* Fantasy Intelligence Engine V9.3.4C · lightweight selected-week matchup context.
 *
 * Purpose:
 *  - make Start/Sit and Matchup useful immediately for the selected week
 *  - calculate projected lineups/totals and an analytic win probability without
 *    starting the full league Monte Carlo simulation
 *  - preserve the existing full FIEDecisionEngines simulation as the optional,
 *    richer path when the user explicitly requests it
 */
(function(){
'use strict';
if(window.FIE934C?.installed)return;

const VERSION='9.3.4C';
const RELEASE='lightweight-selected-week-matchup-context';
const CACHE_TTL_MS=5*60*1000;
const FLEX_SLOTS=new Set(['FLEX','RB_WR','WRRB_FLEX','REC_FLEX','WR_TE','SUPER_FLEX','OP','IDP_FLEX']);
const IGNORED_SLOTS=new Set(['BN','BENCH','IR','TAXI','RESERVE']);
const POS_CV={QB:.30,RB:.45,WR:.52,TE:.48,DL:.58,LB:.32,DB:.42,K:.45,DEF:.42};
const cache=new Map();
let refreshTimer=null;
let requestSeq=0;

const diagnostics={
  contextRuns:0,
  cacheHits:0,
  fetches:0,
  fetchMs:[],
  modelMs:[],
  uiPatches:0,
  staleDrops:0,
  lastContext:null,
  errors:[]
};

function now(){return typeof performance!=='undefined'&&performance.now?performance.now():Date.now();}
function stateObj(){try{return window.state||(typeof state!=='undefined'?state:null);}catch{return window.state||null;}}
function players(){try{return Array.isArray(PLAYERS)?PLAYERS:(Array.isArray(window.PLAYERS)?window.PLAYERS:[]);}catch{return Array.isArray(window.PLAYERS)?window.PLAYERS:[];}}
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round1(v){const n=finite(v);return n===null?null:Math.round(n*10)/10;}
function clamp(n,a=0,b=1){n=Number(n);return Math.max(a,Math.min(b,Number.isFinite(n)?n:a));}
function leagueId(){const s=stateObj();return String(s?.league?.league_id||s?.activeLeagueId||window.FIELeagueController?.activeLeagueId||'');}
function generation(){return Number(window.FIELeagueController?.generation||0);}
function contextStamp(){return{leagueId:leagueId(),generation:generation(),request:++requestSeq};}
function stillCurrent(ctx){return !!ctx&&String(ctx.leagueId)===leagueId()&&Number(ctx.generation)===generation();}
function reportError(e,where){diagnostics.errors.push({at:new Date().toISOString(),where,message:String(e?.message||e)});if(diagnostics.errors.length>20)diagnostics.errors.shift();try{window.FIECore?.Diagnostics?.capture?.(e,{domain:'v9.3.4c',feature:where});}catch{}}
function pushPerf(name,ms,meta={}){try{window.FIEPerformance?.push?.(`934c:${name}`,ms,{leagueId:leagueId(),...meta});}catch{}}

function selectedWeek(){
  const s=stateObj();
  for(const id of ['weekSelectStartSit','weeklyWeekSelect','weekSelectMatchup','matchupWeekSelect','weekSelect']){
    const n=finite(document.getElementById(id)?.value);if(n!==null&&n>=1&&n<=18)return Math.round(n);
  }
  for(const v of [s?.weekly?.week,s?.week,s?.selectedWeek,s?.league?.settings?.leg]){const n=finite(v);if(n!==null&&n>=1&&n<=18)return Math.round(n);}
  return 1;
}
function selectedRosterId(){
  const s=stateObj();let fromEl=null;
  for(const id of ['teamSelect','rosterSelect','matchupTeamSelect']){const v=document.getElementById(id)?.value;if(v!==null&&v!==undefined&&String(v)!==''){fromEl=v;break;}}
  return String(s?.selectedRoster??fromEl??s?.selectedRosterId??s?.myRosterId??s?.rosters?.[0]?.roster_id??'');
}
function normPos(v){const p=String(v||'').toUpperCase();if(['DST','D/ST'].includes(p))return'DEF';if(['DE','DT','EDGE','IDL'].includes(p))return'DL';if(['CB','S','FS','SS'].includes(p))return'DB';return p;}
function eligible(pos,slot){
  pos=normPos(pos);slot=String(slot||'').toUpperCase();
  if(normPos(slot)===pos)return true;
  if(slot==='FLEX'&&['RB','WR','TE'].includes(pos))return true;
  if((slot==='WRRB_FLEX'||slot==='RB_WR')&&['RB','WR'].includes(pos))return true;
  if((slot==='REC_FLEX'||slot==='WR_TE')&&['WR','TE'].includes(pos))return true;
  if((slot==='SUPER_FLEX'||slot==='OP')&&['QB','RB','WR','TE'].includes(pos))return true;
  if(slot==='IDP_FLEX'&&['DL','LB','DB'].includes(pos))return true;
  if(slot==='DL'&&pos==='DL')return true;
  if(slot==='DB'&&pos==='DB')return true;
  if(slot==='DEF'&&pos==='DEF')return true;
  return false;
}
function playerId(p){return String(p?.sleeperId||p?.sleeper_id||p?.player_id||p?.id||'');}
function playerPosition(p){return normPos(p?.position||p?.fantasy_position||p?.position_model);}
function playerMap(){const m=new Map();for(const p of players()){const id=playerId(p);if(id)m.set(id,p);}return m;}
function nestedWeekValue(obj,week){
  if(!obj||typeof obj!=='object')return null;const r=obj[week]??obj[String(week)];if(r===null||r===undefined)return null;
  if(typeof r==='number'||typeof r==='string')return finite(r);
  for(const k of ['decision_weekly_projection','weeklyProjection','projection','projected_points','proj','points']){const n=finite(r?.[k]);if(n!==null)return n;}return null;
}
function weeklyProjection(p,week=selectedWeek()){
  for(const obj of [p?.__fieWeeklyByWeek,p?.weeklyByWeek,p?.weeklyProjectionByWeek,p?.projectionsByWeek]){const n=nestedWeekValue(obj,week);if(n!==null)return n;}
  for(const k of ['weeklyProjection','decision_weekly_projection','decisionWeeklyProjection','sleeperWeeklyProjection','sleeper_weekly_projection','proj']){const n=finite(p?.[k]);if(n!==null)return n;}
  return null;
}
function orderedStarterSlots(){
  const raw=(stateObj()?.league?.roster_positions||[]).map(x=>String(x||'').toUpperCase()).filter(x=>!IGNORED_SLOTS.has(x));
  return raw.slice().sort((a,b)=>Number(FLEX_SLOTS.has(a))-Number(FLEX_SLOTS.has(b)));
}
function projectedLineup(roster,week=selectedWeek()){
  const map=playerMap(),ids=[...new Set([...(roster?.players||[]),...(roster?.starters||[])].filter(x=>x&&String(x)!=='0').map(String))];
  const pool=ids.map(id=>map.get(id)).filter(Boolean).map(p=>({p,id:playerId(p),pos:playerPosition(p),projection:weeklyProjection(p,week)}));
  const slots=orderedStarterSlots(),used=new Set(),lineup=[];
  for(const slot of slots){
    let best=null;
    for(const c of pool){if(used.has(c.id)||!eligible(c.pos,slot)||c.projection===null)continue;if(!best||c.projection>best.projection)best=c;}
    if(best){used.add(best.id);lineup.push({slot,playerId:best.id,name:best.p?.name||best.p?.full_name||best.id,position:best.pos,projection:round1(best.projection),player:best.p});}
    else lineup.push({slot,playerId:null,name:null,position:null,projection:null,player:null});
  }
  const projected=lineup.filter(x=>x.projection!==null),required=slots.length,filled=projected.length,coverage=required?filled/required:0;
  const mean=filled?projected.reduce((s,x)=>s+Number(x.projection||0),0):null;
  let variance=0,uncertaintySources=new Set();
  for(const x of projected){const p=x.player,mu=Number(x.projection)||0;let sigma=null;const lo=finite(p?.weeklyFloor??p?.p10),hi=finite(p?.weeklyCeiling??p?.p90);if(lo!==null&&hi!==null&&hi>=lo){sigma=(hi-lo)/(2*1.281551565545);uncertaintySources.add('player interval');}else{const cv=finite(p?.weeklyCV);if(cv!==null&&cv>0){sigma=Math.abs(mu*cv);uncertaintySources.add('player CV');}else{sigma=Math.abs(mu*(POS_CV[x.position]||.50));uncertaintySources.add('position-CV fallback');}}variance+=Math.max(.25,Number(sigma)||0)**2;}
  return{week,rosterId:String(roster?.roster_id||''),lineup:lineup.map(({player,...x})=>x),requiredSlots:required,filledSlots:filled,coverage:Math.round(coverage*1000)/1000,mean:coverage>=.70?round1(mean):null,sigma:filled?round1(Math.sqrt(variance)):null,uncertaintySource:[...uncertaintySources].join(' + ')||null};
}
function erf(x){const sign=x<0?-1:1,a=Math.abs(x),t=1/(1+.3275911*a),y=1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-a*a);return sign*y;}
function normalWinProbability(myMean,oppMean,mySigma,oppSigma){
  const a=finite(myMean),b=finite(oppMean);if(a===null||b===null)return null;const s=Math.sqrt(Math.max(.25,(finite(mySigma)??0)**2+(finite(oppSigma)??0)**2));return clamp(.5*(1+erf((a-b)/(s*Math.SQRT2))),.01,.99);
}
async function fetchMatchups(id,week,{force=false}={}){
  if(!id)return[];const key=`${id}:${week}`,hit=cache.get(key),ts=Date.now();
  if(!force&&hit&&ts-hit.at<CACHE_TTL_MS){diagnostics.cacheHits++;return hit.promise;}
  const url=`https://api.sleeper.app/v1/league/${encodeURIComponent(id)}/matchups/${Number(week)}`;diagnostics.fetches++;const started=now();
  const promise=(async()=>{const opts={cache:'no-store',sourceId:'sleeper-weekly-matchups',ttlMs:CACHE_TTL_MS,persist:false};const r=window.FIEDataClient?.response?await window.FIEDataClient.response(url,opts):await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(`Sleeper matchups HTTP ${r.status}`);const rows=await r.json();return Array.isArray(rows)?rows:[];})();
  cache.set(key,{at:ts,promise});
  try{const rows=await promise;const ms=now()-started;diagnostics.fetchMs.push(Math.round(ms*10)/10);if(diagnostics.fetchMs.length>30)diagnostics.fetchMs.shift();pushPerf('matchup-fetch',ms,{week});return rows;}catch(e){cache.delete(key);throw e;}
}
function opponentRow(rows,rid){const mine=(rows||[]).find(r=>String(r?.roster_id)===String(rid));if(!mine)return{mine:null,opp:null};const mid=String(mine?.matchup_id??'');if(!mid)return{mine,opp:null};const opp=(rows||[]).find(r=>String(r?.matchup_id??'')===mid&&String(r?.roster_id)!==String(rid))||null;return{mine,opp};}
function rosterById(id){return(stateObj()?.rosters||[]).find(r=>String(r?.roster_id)===String(id))||null;}
async function getContext({force=false,week=selectedWeek(),rosterId=selectedRosterId()}={}){
  const ctx=contextStamp(),id=ctx.leagueId;if(!id||!rosterId)return null;diagnostics.contextRuns++;const started=now();
  try{
    const rows=await fetchMatchups(id,week,{force});if(!stillCurrent(ctx)){diagnostics.staleDrops++;return null;}
    const pair=opponentRow(rows,rosterId),mineRoster=rosterById(rosterId),oppRoster=pair.opp?rosterById(pair.opp.roster_id):null;
    const my=mineRoster?projectedLineup(mineRoster,week):null,opp=oppRoster?projectedLineup(oppRoster,week):null;
    const win=my&&opp?normalWinProbability(my.mean,opp.mean,my.sigma,opp.sigma):null;
    const out={version:VERSION,leagueId:id,generation:ctx.generation,week:Number(week),rosterId:String(rosterId),opponentRosterId:pair.opp?String(pair.opp.roster_id):null,matchupId:pair.mine?.matchup_id??null,my,opponent:opp,myMean:my?.mean??null,oppMean:opp?.mean??null,winProbability:win===null?null:Math.round(win*1000)/1000,method:'selected-week projected lineups + analytic normal approximation',fullSimulationRequired:false,createdAt:new Date().toISOString()};
    const ms=now()-started;diagnostics.modelMs.push(Math.round(ms*10)/10);if(diagnostics.modelMs.length>30)diagnostics.modelMs.shift();diagnostics.lastContext={leagueId:id,week:Number(week),rosterId:String(rosterId),opponentRosterId:out.opponentRosterId,myMean:out.myMean,oppMean:out.oppMean,winProbability:out.winProbability,ms:Math.round(ms*10)/10};pushPerf('context',ms,{week});
    if(window.FIEDecisionEngines){window.FIEDecisionEngines.weeklyContext=out;window.FIEDecisionEngines.weeklyContextService=API;}
    window.dispatchEvent?.(new CustomEvent('fie:weekly-context',{detail:out}));return out;
  }catch(e){reportError(e,'get-context');return null;}
}
function metricText(kind,v){if(v===null||v===undefined)return'—';if(kind==='win')return`${Math.round(Number(v)*100)}%`;return Number(v).toFixed(1);}
function patchMetric(panel,label,value){
  if(!panel||value===null||value===undefined)return false;const target=String(label).trim().toLowerCase(),nodes=panel.querySelectorAll('span,div,td,th,small,label');
  for(const el of nodes){if(String(el.textContent||'').trim().toLowerCase()!==target)continue;const parent=el.parentElement;if(!parent)continue;let valueEl=el.nextElementSibling;
    if(!valueEl&&parent.firstElementChild!==el)valueEl=parent.firstElementChild;
    if(!valueEl){for(const c of parent.children){if(c!==el&&/^(?:—|-|n\/a|\d+(?:\.\d+)?%?)$/i.test(String(c.textContent||'').trim())){valueEl=c;break;}}}
    if(valueEl&&valueEl!==el){const current=String(valueEl.textContent||'').trim();const placeholder=!current||/^(?:—|-|n\/a)$/i.test(current);if(!placeholder&&!valueEl.dataset.fie934c)return true;valueEl.textContent=value;valueEl.dataset.fie934c='1';return true;}
  }return false;
}
function contextCard(container,ctx){
  if(!container||!ctx)return false;let card=container.querySelector(':scope > [data-fie934c-context]');if(!card){card=document.createElement('div');card.dataset.fie934cContext='1';card.style.cssText='margin:8px 0;padding:8px 10px;border:1px solid rgba(127,127,127,.25);border-radius:8px;font-size:12px;opacity:.92';container.prepend(card);}const opp=ctx.opponentRosterId?`Opponent ${metricText('points',ctx.oppMean)}`:'No opponent';card.textContent=`Quick Week ${ctx.week} context · You ${metricText('points',ctx.myMean)} · ${opp} · Win ${metricText('win',ctx.winProbability)}`;card.title='Lightweight matchup context. Full simulation remains available on demand.';return true;
}
function visibleMatchupRoot(){for(const sel of ['#matchupSimPanel','#matchupPanel','#matchupView','#matchupSection','#weeklyMatchup','#weeklyMatchupPanel','[data-panel="matchup"]','[data-tab-panel="matchup"]']){const el=document.querySelector(sel);if(el&&el.offsetParent!==null)return el;}return null;}
function applyContextToUI(ctx){
  if(!ctx||String(ctx.leagueId)!==leagueId()||Number(ctx.week)!==selectedWeek())return;let changed=false;const panel=document.getElementById('fie93WeeklyPanel');
  if(panel){const a=patchMetric(panel,'Modeled win probability',metricText('win',ctx.winProbability))||patchMetric(panel,'Win probability',metricText('win',ctx.winProbability)),b=patchMetric(panel,'Opponent projected total',metricText('points',ctx.oppMean)),c=patchMetric(panel,'Your projected total',metricText('points',ctx.myMean));changed=a||b||c;if(!a&&!b&&!c)changed=contextCard(panel,ctx)||changed;}
  const match=visibleMatchupRoot();if(match&&match!==panel)changed=contextCard(match,ctx)||changed;
  if(changed)diagnostics.uiPatches++;
}
function refreshUI({force=false}={}){clearTimeout(refreshTimer);refreshTimer=setTimeout(async()=>{const ctx=await getContext({force});if(ctx)applyContextToUI(ctx);},20);}
function invalidate(){cache.clear();diagnostics.lastContext=null;if(window.FIEDecisionEngines)window.FIEDecisionEngines.weeklyContext=null;}
function report(){return{version:VERSION,release:RELEASE,leagueId:leagueId(),week:selectedWeek(),diagnostics:{...diagnostics,fetchMs:[...diagnostics.fetchMs],modelMs:[...diagnostics.modelMs],errors:[...diagnostics.errors]}};}

const API={installed:true,VERSION,RELEASE,get:getContext,refresh:refreshUI,invalidate,report,selectedWeek,selectedRosterId,projectedLineup,normalWinProbability,weeklyProjection,eligible};
window.FIE934C=API;window.FIEWeeklyMatchupContext=API;if(window.FIEDecisionEngines)window.FIEDecisionEngines.weeklyContextService=API;

window.addEventListener('fie:league-changing',()=>{invalidate();clearTimeout(refreshTimer);});
for(const evt of ['fie:core-interactive','fie:score-published','fie:enhanced'])window.addEventListener(evt,()=>refreshUI());
document.addEventListener('change',e=>{if(['teamSelect','rosterSelect','matchupTeamSelect','weekSelect','weekSelectStartSit','weeklyWeekSelect','weekSelectMatchup','matchupWeekSelect'].includes(e.target?.id)){invalidate();refreshUI({force:true});}},true);
document.addEventListener('click',e=>{const el=e.target?.closest?.('button,a,[data-tab],[data-route],[role="tab"]');if(!el)return;const sig=[el.id,el.dataset?.tab,el.dataset?.route,el.getAttribute?.('href'),el.textContent].filter(Boolean).join(' ').toLowerCase();if(sig.includes('matchup')||sig.includes('start/sit')||sig.includes('start sit'))setTimeout(()=>refreshUI(),30);},true);
setTimeout(()=>{if(leagueId())refreshUI();},80);
})();

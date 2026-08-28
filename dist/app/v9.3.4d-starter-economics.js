/* Fantasy Intelligence Engine V9.3.4D · universal starter-slot economics.
 *
 * Applies to every league format. Starter demand is derived from league size,
 * concrete starting slots, FLEX/SF/OP/IDP eligibility and the live player pool.
 * Player value is then expressed relative to the marginal starter/replacement
 * frontier, with starter probability, scarcity and downside exposed explicitly.
 */
(function(){
'use strict';
if(window.FIE934D?.installed)return;

const VERSION='9.3.4D';
const RELEASE='universal-starter-slot-economics';
const INSTALL_LIMIT=120;
const POSITIONS=['QB','RB','WR','TE','K','DEF','DL','LB','DB','P','OL'];
const IGNORE=new Set(['BN','BENCH','IR','TAXI','RESERVE']);
const SLOT_ELIG={
  QB:['QB'],RB:['RB'],WR:['WR'],TE:['TE'],K:['K'],DEF:['DEF'],DST:['DEF'],
  DL:['DL'],DE:['DL'],DT:['DL'],EDGE:['DL'],IDL:['DL'],LB:['LB'],DB:['DB'],CB:['DB'],S:['DB'],FS:['DB'],SS:['DB'],P:['P'],OL:['OL'],T:['OL'],G:['OL'],C:['OL'],
  FLEX:['RB','WR','TE'],RB_WR:['RB','WR'],WRRB_FLEX:['RB','WR'],REC_FLEX:['WR','TE'],WR_TE:['WR','TE'],
  SUPER_FLEX:['QB','RB','WR','TE'],OP:['QB','RB','WR','TE'],IDP_FLEX:['DL','LB','DB']
};
const DIRECT={QB:'QB',RB:'RB',WR:'WR',TE:'TE',K:'K',DEF:'DEF',DST:'DEF',DL:'DL',DE:'DL',DT:'DL',EDGE:'DL',IDL:'DL',LB:'LB',DB:'DB',CB:'DB',S:'DB',FS:'DB',SS:'DB',P:'P',OL:'OL',T:'OL',G:'OL',C:'OL'};
let installAttempts=0;
let computeTimer=null;
let renderTimer=null;
let runSeq=0;

const diagnostics={
  installs:0,
  runs:0,
  totalMs:[],
  lastTotalMs:null,
  playerCount:0,
  eligibleCount:0,
  teams:0,
  totalStarterSlots:0,
  effectiveDemand:{},
  perTeamDemand:{},
  replacement:{},
  slotAllocations:{},
  reranks:0,
  renderRequests:0,
  errors:[],
  targetMs:50,
  universal:true
};

function now(){return typeof performance!=='undefined'&&performance.now?performance.now():Date.now();}
function stateObj(){try{return window.state||(typeof state!=='undefined'?state:null);}catch{return window.state||null;}}
function players(){try{return Array.isArray(PLAYERS)?PLAYERS:(Array.isArray(window.PLAYERS)?window.PLAYERS:[]);}catch{return Array.isArray(window.PLAYERS)?window.PLAYERS:[];}}
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round1(v){const n=finite(v);return n===null?null:Math.round(n*10)/10;}
function clamp(n,a=0,b=100){n=Number(n);return Math.max(a,Math.min(b,Number.isFinite(n)?n:a));}
function leagueId(){const s=stateObj();return String(s?.league?.league_id||s?.activeLeagueId||'');}
function normPos(v){const p=String(v||'').toUpperCase();if(['DST','D/ST'].includes(p))return'DEF';if(['DE','DT','EDGE','IDL'].includes(p))return'DL';if(['CB','S','FS','SS'].includes(p))return'DB';if(['T','G','C'].includes(p))return'OL';return p;}
function recordError(e,where){diagnostics.errors.push({at:new Date().toISOString(),where,message:String(e?.message||e)});if(diagnostics.errors.length>20)diagnostics.errors.shift();try{window.FIECore?.Diagnostics?.capture?.(e,{domain:'v9.3.4d',feature:where});}catch{}}
function perf(name,ms,meta={}){try{window.FIEPerformance?.push?.(`934d:${name}`,ms,{leagueId:leagueId(),...meta});}catch{}}
function quantile(sorted,q){if(!sorted.length)return null;const i=(sorted.length-1)*q,l=Math.floor(i),h=Math.ceil(i);return l===h?sorted[l]:sorted[l]*(h-i)+sorted[h]*(i-l);}
function sigmoid(x){if(x>35)return 1;if(x<-35)return 0;return 1/(1+Math.exp(-x));}
function rosterSlots(league=stateObj()?.league||{}){return(league?.roster_positions||[]).map(x=>String(x||'').toUpperCase()).filter(x=>!IGNORE.has(x));}
function slotEligible(pos,slot){pos=normPos(pos);return(SLOT_ELIG[String(slot||'').toUpperCase()]||[]).includes(pos);}
function playerValue(p){const w=weeklyProjection(p);if(w!==null)return w;const season=seasonProjection(p);if(season!==null)return season/17;const ppg=finite(p?.publicFantasyPPG);if(ppg!==null)return ppg;const decision=typeof window.FIE89?.playerDecisionValue==='function'?finite(window.FIE89.playerDecisionValue(p)):null;if(decision!==null)return decision/5;for(const k of ['seasonScore','modelScore','tfgModelScore','targetScore']){const n=finite(p?.[k]);if(n!==null)return n/5;}return 0;}
function seasonProjection(p){for(const k of ['engineSeasonProjection','decisionSeasonProjection','sleeperSeasonProjection','sleeper_season_projection']){const n=finite(p?.[k]);if(n!==null)return n;}return null;}
function weeklyProjection(p){for(const k of ['weeklyProjection','decision_weekly_projection','decisionWeeklyProjection','sleeperWeeklyProjection','sleeper_weekly_projection']){const n=finite(p?.[k]);if(n!==null)return n;}return null;}
function floorProjection(p){for(const k of ['weeklyFloor','p10']){const n=finite(p?.[k]);if(n!==null)return n;}return null;}
function poolByPosition(ps=players()){
  const out=Object.fromEntries(POSITIONS.map(p=>[p,[]]));
  for(const p of ps){const pos=normPos(p?.position);if(!out[pos])out[pos]=[];out[pos].push(p);}
  for(const a of Object.values(out))a.sort((x,y)=>playerValue(y)-playerValue(x));return out;
}
function computeDemand(ps=players(),league=stateObj()?.league||{},rosters=stateObj()?.rosters||[]){
  const teams=Math.max(1,Number(league?.total_rosters||rosters?.length||12)||12),slots=rosterSlots(league),pools=poolByPosition(ps);
  const used=Object.fromEntries(POSITIONS.map(p=>[p,0])),demand=Object.fromEntries(POSITIONS.map(p=>[p,0])),fixed=Object.fromEntries(POSITIONS.map(p=>[p,0])),slotAllocations={};
  const allocate=(pos,n,slot)=>{if(!pos||!pools[pos])return 0;const can=Math.min(Math.max(0,Number(n)||0),Math.max(0,pools[pos].length-used[pos]));used[pos]+=can;demand[pos]+=can;if(slot){slotAllocations[slot]=slotAllocations[slot]||{};slotAllocations[slot][pos]=(slotAllocations[slot][pos]||0)+can;}return can;};
  const counts={};for(const slot of slots)counts[slot]=(counts[slot]||0)+teams;
  for(const [slot,n] of Object.entries(counts)){const pos=DIRECT[slot];if(pos){const got=allocate(pos,n,slot);fixed[pos]+=got;}}
  const flexOrder=['RB_WR','WRRB_FLEX','REC_FLEX','WR_TE','FLEX','IDP_FLEX','SUPER_FLEX','OP'];
  for(const slot of flexOrder){let n=counts[slot]||0;const elig=SLOT_ELIG[slot]||[];while(n-->0){let bestPos=null,bestValue=-Infinity;for(const pos of elig){const cand=pools[pos]?.[used[pos]];if(!cand)continue;const v=playerValue(cand);if(v>bestValue){bestValue=v;bestPos=pos;}}if(!bestPos)break;allocate(bestPos,1,slot);}}
  const perTeam={};for(const pos of POSITIONS)perTeam[pos]=Math.round(((demand[pos]||0)/teams)*1000)/1000;
  return{teams,slots,pools,used,effectiveDemand:demand,fixedDemand:fixed,perTeamDemand:perTeam,slotAllocations,totalStarterSlots:slots.length*teams};
}
function replacementContext(pos,pool,demand){
  const n=pool.length,d=Math.max(0,Number(demand)||0);if(!n)return{demand:d,starterCutoff:null,replacement:null,replacementRank:null,scarcityMultiplier:1,depthPressure:0};
  if(d<=0)return{demand:0,starterCutoff:null,replacement:pool[0],replacementRank:1,scarcityMultiplier:.8,depthPressure:0};
  const starterIdx=Math.min(n-1,Math.max(0,Math.ceil(d)-1)),replacementIdx=Math.min(n-1,Math.max(0,Math.floor(d))),starter=pool[starterIdx]||null,repl=pool[replacementIdx]||pool[n-1]||null;
  const values=pool.map(playerValue).filter(Number.isFinite).sort((a,b)=>a-b),q25=quantile(values,.25)??0,q75=quantile(values,.75)??100,scale=Math.max(5,q75-q25),gap=Math.max(0,playerValue(starter)-playerValue(repl)),depthPressure=Math.min(1,d/Math.max(1,n));
  const scarcity=clamp(1+.55*(gap/scale)+.15*depthPressure,.8,1.5);
  return{demand:d,starterCutoff:starter,replacement:repl,replacementRank:replacementIdx+1,scarcityMultiplier:Math.round(scarcity*1000)/1000,depthPressure:Math.round(depthPressure*1000)/1000};
}
function computeEconomics(ps=players(),league=stateObj()?.league||{},rosters=stateObj()?.rosters||[]){
  const demandCtx=computeDemand(ps,league,rosters),byPos=demandCtx.pools,replByPos={},econRows=[];
  for(const pos of Object.keys(byPos))replByPos[pos]=replacementContext(pos,byPos[pos],demandCtx.effectiveDemand[pos]||0);
  for(const [pos,pool] of Object.entries(byPos)){
    const rc=replByPos[pos],d=Number(rc.demand)||0,rankScale=Math.max(1.5,d*.07),replValue=rc.replacement?playerValue(rc.replacement):0,replSeason=rc.replacement?seasonProjection(rc.replacement):null,replWeek=rc.replacement?weeklyProjection(rc.replacement):null;
    pool.forEach((p,i)=>{
      const rank=i+1,starterProbability=d<=0?0:sigmoid(((d+.5)-rank)/rankScale),value=playerValue(p),rawGap=value-replValue,season=seasonProjection(p),week=weeklyProjection(p),floor=floorProjection(p),projectionGap=season!==null&&replSeason!==null?season-replSeason:null,weeklyGap=week!==null&&replWeek!==null?week-replWeek:null,downside=week!==null&&floor!==null?Math.max(0,week-floor):null,floorAboveReplacement=floor!==null&&replWeek!==null?floor-replWeek:null,marginal=Math.max(0,rawGap)*starterProbability*Number(rc.scarcityMultiplier||1);
      const row={version:VERSION,leagueId:leagueId(),position:pos,eligibleSlots:Object.entries(SLOT_ELIG).filter(([,xs])=>xs.includes(pos)).map(([slot])=>slot),positionRank:rank,effectiveStarterDemand:Math.round(d*1000)/1000,effectiveStarterDemandPerTeam:Math.round((d/demandCtx.teams)*1000)/1000,replacementRank:rc.replacementRank,replacementPlayerId:String(rc.replacement?.sleeperId||rc.replacement?.sleeper_id||''),replacementPlayer:rc.replacement?.name||null,replacementValue:round1(replValue),replacementProjection:round1(replSeason),replacementWeeklyProjection:round1(replWeek),replacementAdjustedValue:round1(rawGap),projectionAboveReplacement:round1(projectionGap),weeklyProjectionAboveReplacement:round1(weeklyGap),starterProbability:Math.round(starterProbability*1000)/1000,scarcityMultiplier:rc.scarcityMultiplier,depthPressure:rc.depthPressure,floor:round1(floor),floorDownside:round1(downside),floorAboveReplacement:round1(floorAboveReplacement),marginalLineupUtility:round1(marginal)};
      p.starterEconomics=row;p.starter_probability=row.starterProbability;p.replacement_adjusted_value=row.replacementAdjustedValue;p.marginal_lineup_utility=row.marginalLineupUtility;p.scarcity_multiplier=row.scarcityMultiplier;p.floor_downside=row.floorDownside;econRows.push({p,row});
    });
  }
  return{...demandCtx,replacementByPosition:replByPos,econRows};
}
function economicsAwareRerank(ctx){
  const fie=window.FIE89||{},legacyValue=typeof fie.playerDecisionValue==='function'?fie.playerDecisionValue:(p=>finite(p?.projectedVOR)??finite(p?.seasonVOR)??finite(p?.seasonScore)??finite(p?.modelScore)??0),edgeFn=typeof fie.marketEdgeValue==='function'?fie.marketEdgeValue:(p=>finite(p?.marketEdgeValue));
  const rows=ctx.econRows.filter(x=>x.p?.leagueEligible!==false),legacy=rows.map(x=>Number(legacyValue(x.p))||0).sort((a,b)=>a-b),span=Math.max(10,(quantile(legacy,.90)??100)-(quantile(legacy,.10)??0));
  const econSorted=rows.map(x=>Number(x.row.marginalLineupUtility)||0).sort((a,b)=>a-b),percentile=v=>{let lo=0,hi=econSorted.length;while(lo<hi){const m=(lo+hi)>>1;if(econSorted[m]<v)lo=m+1;else hi=m;}const less=lo;lo=0;hi=econSorted.length;while(lo<hi){const m=(lo+hi)>>1;if(econSorted[m]<=v)lo=m+1;else hi=m;}const upper=lo;return econSorted.length?(less+(upper-less)*.5)/econSorted.length:.5;};
  const valueMap=new Map();for(const {p,row} of rows){const base=Number(legacyValue(p))||0,pct=percentile(Number(row.marginalLineupUtility)||0),adjustment=(pct-.5)*span*.35,adjusted=base+adjustment;row.economicsPercentile=Math.round(pct*1000)/10;row.decisionValueBeforeEconomics=round1(base);row.decisionEconomicsAdjustment=round1(adjustment);row.decisionValueWithEconomics=round1(adjusted);p.starterEconomicsScore=row.economicsPercentile;p.starterEconomicsDecisionValue=row.decisionValueWithEconomics;valueMap.set(p,adjusted);}
  const eligible=rows.map(x=>x.p).slice().sort((a,b)=>(valueMap.get(b)||0)-(valueMap.get(a)||0)),n=eligible.length;eligible.forEach((p,i)=>{const edge=finite(edgeFn(p)),base=n>1?100-i*100/(n-1):50;p.preStarterEconomicsSeasonScore=round1(p.seasonScore);p.seasonScore=round1(clamp(base+(edge!==null?edge*.8:0),0,100));if(p.availability==='FA'&&p.leagueEligible!==false){const momentum=(Number(p.roleMomentum)||50)-50,shock=(Number(p.opportunityShock)||50)-50;p.waiverScore=round1(clamp((valueMap.get(p)||0)*.75+momentum*.18+shock*.22,0,100));}});
  diagnostics.reranks++;diagnostics.eligibleCount=n;return n;
}
function compute({rerank=true,render=true}={}){
  const seq=++runSeq,started=now(),ps=players(),s=stateObj();if(!s?.league||!ps.length)return null;diagnostics.runs++;diagnostics.playerCount=ps.length;
  try{
    const ctx=computeEconomics(ps,s.league,s.rosters||[]);if(seq!==runSeq)return null;if(rerank)economicsAwareRerank(ctx);
    diagnostics.teams=ctx.teams;diagnostics.totalStarterSlots=ctx.totalStarterSlots;diagnostics.effectiveDemand={...ctx.effectiveDemand};diagnostics.perTeamDemand={...ctx.perTeamDemand};diagnostics.slotAllocations=JSON.parse(JSON.stringify(ctx.slotAllocations||{}));diagnostics.replacement={};for(const [pos,r] of Object.entries(ctx.replacementByPosition||{}))diagnostics.replacement[pos]={demand:r.demand,replacementRank:r.replacementRank,replacement:r.replacement?.name||null,replacementValue:round1(r.replacement?playerValue(r.replacement):null),scarcityMultiplier:r.scarcityMultiplier};
    const ms=now()-started;diagnostics.lastTotalMs=Math.round(ms*10)/10;diagnostics.totalMs.push(diagnostics.lastTotalMs);if(diagnostics.totalMs.length>30)diagnostics.totalMs.shift();perf('economics',ms,{players:ps.length,teams:ctx.teams});
    window.dispatchEvent?.(new CustomEvent('fie:starter-economics',{detail:{version:VERSION,leagueId:leagueId(),ms:diagnostics.lastTotalMs,effectiveDemand:{...ctx.effectiveDemand},perTeamDemand:{...ctx.perTeamDemand}}}));
    if(render){clearTimeout(renderTimer);renderTimer=setTimeout(()=>{try{diagnostics.renderRequests++;window.render?.();}catch(e){recordError(e,'render');}},0);}return ctx;
  }catch(e){recordError(e,'compute');return null;}
}
function schedule(opts={}){clearTimeout(computeTimer);computeTimer=setTimeout(()=>compute(opts),0);}
function clearPlayerEconomics(){for(const p of players()){delete p.starterEconomics;delete p.starter_probability;delete p.replacement_adjusted_value;delete p.marginal_lineup_utility;delete p.scarcity_multiplier;delete p.floor_downside;delete p.starterEconomicsScore;delete p.starterEconomicsDecisionValue;}}
function report(){return{version:VERSION,release:RELEASE,leagueId:leagueId(),diagnostics:{...diagnostics,totalMs:[...diagnostics.totalMs],effectiveDemand:{...diagnostics.effectiveDemand},perTeamDemand:{...diagnostics.perTeamDemand},replacement:{...diagnostics.replacement},slotAllocations:JSON.parse(JSON.stringify(diagnostics.slotAllocations||{})),errors:[...diagnostics.errors]}};}
function install(){
  installAttempts++;if(!window.FIE934A3?.installed){if(installAttempts<INSTALL_LIMIT)setTimeout(install,100);else console.warn('FIE V9.3.4D could not find A3 baseline.');return;}diagnostics.installs++;
  window.addEventListener('fie:score-published',()=>schedule({rerank:true,render:true}));
  window.addEventListener('fie:league-changing',()=>{runSeq++;clearTimeout(computeTimer);clearTimeout(renderTimer);clearPlayerEconomics();diagnostics.effectiveDemand={};diagnostics.replacement={};});
  window.addEventListener('fie:core-interactive',()=>{if(players().some(p=>finite(p?.modelScore)!==null))schedule({rerank:true,render:false});});
  if(players().length&&stateObj()?.league)schedule({rerank:true,render:false});
}

const API={installed:true,VERSION,RELEASE,diagnostics,report,compute,schedule,computeDemand,computeEconomics,slotEligible,normPos,playerValue};
window.FIE934D=API;window.FIEStarterEconomics=API;
install();
})();

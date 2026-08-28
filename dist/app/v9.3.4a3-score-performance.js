/* Fantasy Intelligence Engine V9.3.4A3 · scoring hot-path acceleration.
 *
 * Browser QA on V9.3.4A2 isolated the remaining navigation freeze to the
 * synchronous score publication: ~19.6s in Genesis and ~7.1s in Chopped,
 * while the league shell itself was already interactive in <0.4s.
 *
 * A3 preserves the V8.9/V9 scoring formulas but removes repeated full-pool
 * work from the hot path:
 *   - marginal starter demand is allocated once per score cycle
 *   - ownership / replacement pools are indexed once by position
 *   - prediction features are evaluated once per player with shared caches
 *   - risk residual quantiles are calculated once per position
 *   - decision ranks use one O(N log N) sort instead of one sort per player
 *   - retrospective feature training is not recomputed inside every score pass
 *
 * The previous assignScores implementation remains a fail-safe fallback.
 */
(function(){
'use strict';
if(window.FIE934A3?.installed)return;

const VERSION='9.3.4A3';
const RELEASE='scoring-hot-path-linearized-contracts-repair';
const INSTALL_LIMIT=120;
const POSITIONS=['QB','RB','WR','TE','DL','LB','DB','K','P','OL','DEF'];
const SLOT_ELIG={QB:['QB'],RB:['RB'],WR:['WR'],TE:['TE'],FLEX:['RB','WR','TE'],WRRB_FLEX:['WR','RB'],REC_FLEX:['WR','TE'],SUPER_FLEX:['QB','RB','WR','TE'],DL:['DL'],DE:['DL'],DT:['DL'],LB:['LB'],DB:['DB'],CB:['DB'],S:['DB'],IDP_FLEX:['DL','LB','DB'],DEF:['DEF'],DST:['DEF'],K:['K'],P:['P'],OL:['OL'],T:['OL'],G:['OL'],C:['OL']};
const DIRECT_SLOT_MAP={QB:'QB',RB:'RB',WR:'WR',TE:'TE',DL:'DL',DE:'DL',DT:'DL',LB:'LB',DB:'DB',CB:'DB',S:'DB',DEF:'DEF',DST:'DEF',K:'K',P:'P',OL:'OL',T:'OL',G:'OL',C:'OL'};
let installAttempts=0;
let installed=false;
let scoreEpoch=0;
let demandMemo=null;
let demandMemoKey='';
let featureLearningScheduled=false;
let legacyAssign=null;
let legacyComputePrediction=null;
let legacyDemand=null;
let legacyReplacement=null;
let legacyProjectedReplacement=null;
let legacyProjectionRanks=null;

const diagnostics={
  installs:0,
  scoreRuns:0,
  fallbacks:0,
  predictionRuns:0,
  playerCount:0,
  eligibleCount:0,
  featureLearningDeferred:0,
  lastReason:'',
  lastTotalMs:null,
  maxTotalMs:0,
  phaseMs:{},
  totals:[],
  errors:[],
  demand:{},
  contractRoute:'gzip->csv Pages Function',
  targetMs:500
};

function now(){return typeof performance!=='undefined'&&performance.now?performance.now():Date.now();}
function arr(){try{return Array.isArray(PLAYERS)?PLAYERS:[];}catch{return Array.isArray(window.PLAYERS)?window.PLAYERS:[];}}
function st(){try{return window.state||(typeof state!=='undefined'?state:null);}catch{return window.state||null;}}
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function clamp(n,a=0,b=100){n=Number(n);return Math.max(a,Math.min(b,Number.isFinite(n)?n:a));}
function round1(n){return Math.round(Number(n)*10)/10;}
function mean(xs){const z=(xs||[]).map(Number).filter(Number.isFinite);return z.length?z.reduce((a,b)=>a+b,0)/z.length:null;}
function sd(xs){const z=(xs||[]).map(Number).filter(Number.isFinite);if(z.length<2)return null;const m=mean(z);return Math.sqrt(z.reduce((a,b)=>a+(b-m)*(b-m),0)/(z.length-1));}
function activeLeagueId(){return String(st()?.league?.league_id||st()?.activeLeagueId||'');}
function currentWeek(){const el=document.getElementById('weekSelect');return Math.max(1,Math.min(18,Number(el?.value||st()?.weekly?.week||1)||1));}
function activeSeason(){const x=Number(st()?.league?.season||document.getElementById('seasonSelect')?.value||st()?.weekly?.season);if(Number.isFinite(x)&&x>1900)return x;const d=new Date();return d.getUTCFullYear()-(d.getUTCMonth()<=1?1:0);}
function countSlot(name){return (st()?.league?.roster_positions||[]).filter(x=>String(x)===String(name)).length;}
function timed(name,fn){const t=now();const out=fn();const ms=now()-t;diagnostics.phaseMs[name]=round1(ms);try{window.FIEPerformance?.push?.(`934a3:${name}`,ms,{leagueId:activeLeagueId(),players:arr().length});}catch{}return out;}
function recordError(e,where){diagnostics.errors.push({at:new Date().toISOString(),where,message:String(e?.message||e)});if(diagnostics.errors.length>20)diagnostics.errors.shift();try{window.FIECore?.Diagnostics?.capture?.(e,{domain:'v9.3.4a3',feature:where});}catch{}}
function required(name){return typeof window[name]==='function';}

function demandValue(p){const a=finite(p?.engineSeasonProjection);if(a!==null)return a;const b=finite(p?.sleeperSeasonProjection);if(b!==null)return b;return finite(p?.modelScore)??0;}
function demandFingerprint(){const league=st()?.league||{},slots=(league.roster_positions||[]).join('|'),teams=Number(league.total_rosters||st()?.rosters?.length||1),ps=arr();let sig=0;for(let i=0;i<ps.length;i+=Math.max(1,Math.floor(ps.length/32))){const p=ps[i];sig=(sig+Math.round(demandValue(p)*10)+(String(p?.position||'').charCodeAt(0)||0)*17)>>>0;}return `${activeLeagueId()}|${teams}|${slots}|${ps.length}|${scoreEpoch}|${sig}`;}
function computeMarginalDemand(){
  const state=st(),players=arr();if(!state?.league)return {};
  const teams=Math.max(1,Number(state.league.total_rosters||state.rosters?.length||1)||1),slots=state.league.roster_positions||[],counts={};
  for(const s of slots)counts[s]=(counts[s]||0)+teams;
  const pools=Object.fromEntries(POSITIONS.map(pos=>[pos,players.filter(p=>p?.position===pos).slice().sort((a,b)=>demandValue(b)-demandValue(a))]));
  const used=Object.fromEntries(POSITIONS.map(pos=>[pos,0])),out=Object.fromEntries(POSITIONS.map(pos=>[pos,0]));
  const take=(pos,n)=>{if(!pos||!pools[pos])return;const k=Math.min(Number(n)||0,Math.max(0,pools[pos].length-used[pos]));used[pos]+=k;out[pos]+=k;};
  for(const [slot,n] of Object.entries(counts)){const pos=DIRECT_SLOT_MAP[slot];if(pos)take(pos,n);}
  for(const slot of ['WRRB_FLEX','REC_FLEX','FLEX','IDP_FLEX','SUPER_FLEX']){
    let n=counts[slot]||0;const elig=SLOT_ELIG[slot]||[];
    while(n-->0){let best=null,bestPos=null;for(const pos of elig){const cand=pools[pos]?.[used[pos]];if(cand&&(!best||demandValue(cand)>demandValue(best))){best=cand;bestPos=pos;}}if(bestPos){used[bestPos]++;out[bestPos]++;}}
  }
  const perTeam={};for(const pos of POSITIONS)perTeam[pos]=(out[pos]||0)/teams;
  diagnostics.demand={...perTeam};return perTeam;
}
function invalidateDemand(){scoreEpoch++;demandMemo=null;demandMemoKey='';}
function demandMap(){const key=demandFingerprint();if(!demandMemo||demandMemoKey!==key){demandMemo=computeMarginalDemand();demandMemoKey=key;}return demandMemo;}
function fastLeaguePositionDemand(pos){const d=demandMap();return Number.isFinite(Number(d[pos]))?Number(d[pos]):0;}

function ownershipByPosition(){const out={};for(const p of arr())if(p?.availability==='OWNED')out[p.position]=(out[p.position]||0)+1;return out;}
function lowerBound(a,x){let lo=0,hi=a.length;while(lo<hi){const m=(lo+hi)>>1;if(a[m]<x)lo=m+1;else hi=m;}return lo;}
function upperBound(a,x){let lo=0,hi=a.length;while(lo<hi){const m=(lo+hi)>>1;if(a[m]<=x)lo=m+1;else hi=m;}return lo;}
function fastNormalizeTFG(){
  const groups={};for(const p of arr()){const v=finite(p?.tfgGrade);if(v===null)continue;(groups[p.position]??=[]).push(v);}for(const a of Object.values(groups))a.sort((x,y)=>x-y);
  for(const p of arr()){const v=finite(p?.tfgGrade),a=groups[p.position];if(v===null||!a?.length){p.tfgModelScore=null;continue;}const less=lowerBound(a,v),equal=upperBound(a,v)-less;p.tfgModelScore=round1(clamp(((less+equal*.5)/a.length)*100,1,99));}
}
function fastLeagueFit(p,demand,owned,teams){
  const d=Number(demand[p.position]||0);if(d<=0)return round1((Number(window.scoringFit?.(p))||10)*.68+10*.32);
  const pressure=(Number(owned[p.position]||0)/Math.max(1,teams*d));const scarcity=clamp(45+d*7+Math.min(20,pressure*7),20,95),fit=Number(window.scoringFit?.(p));return round1((Number.isFinite(fit)?fit:50)*.68+scarcity*.32);
}
function replacementIndex(effective,n){const rank=Math.max(1,Math.round(Number(effective)||1));return Math.max(0,Math.min(n-1,rank-1));}
function fastReplacementLevels(){
  const state=st(),players=arr();state.replacementLevels={};if(!state.league)return state.replacementLevels;
  const d=demandMap(),owned=ownershipByPosition(),teams=Math.max(1,Number(state.league.total_rosters||state.rosters?.length||1)||1),ownW=Number(state.replacement?.ownershipInfluence||0)/100,totalDemand=Math.max(1,Object.values(d).reduce((a,b)=>a+(Number(b)||0),0)),bench=countSlot('BN'),benchShare=(bench/totalDemand)*(Number(state.replacement?.benchInfluence||0)/100),byPos={};
  for(const p of players){if(!p.leagueEligible||finite(p.modelScore)===null)continue;(byPos[p.position]??=[]).push(p);}for(const xs of Object.values(byPos))xs.sort((a,b)=>Number(b.modelScore)-Number(a.modelScore));
  for(const [pos,pool] of Object.entries(byPos)){if(!pool.length)continue;const actual=Number(owned[pos]||0),projected=teams*Number(d[pos]||0)*(1+benchShare),effective=actual*ownW+projected*(1-ownW),idx=replacementIndex(effective,pool.length),repl=pool[idx];state.replacementLevels[pos]={score:round1(repl.modelScore),player:repl.name,effectiveOwned:round1(effective),actualOwned:actual,projectedOwned:round1(projected),slotsPerTeam:Math.round(Number(d[pos]||0)*100)/100,cutoff:idx+1,method:'marginal starter allocation · A3 cached'};}
  return state.replacementLevels;
}
function fastProjectedReplacementLevels(){
  const state=st(),players=arr();state.projectedReplacementLevels={};if(!state.league)return state.projectedReplacementLevels;
  const byPos={};for(const p of players){if(!p.leagueEligible||finite(p.engineSeasonProjection)===null)continue;(byPos[p.position]??=[]).push(p);}for(const xs of Object.values(byPos))xs.sort((a,b)=>Number(b.engineSeasonProjection)-Number(a.engineSeasonProjection));
  for(const [pos,r] of Object.entries(state.replacementLevels||{})){const xs=byPos[pos]||[];if(!xs.length)continue;const idx=replacementIndex(r.effectiveOwned,xs.length),rp=xs[idx];state.projectedReplacementLevels[pos]={points:Number(rp.engineSeasonProjection),player:rp.name,cutoff:idx+1,method:'canonical cutoff · A3 cached'};}
  for(const p of players){const r=state.projectedReplacementLevels[p.position];p.projectedReplacementPoints=r?.points??null;p.projectedVOR=(r&&finite(p.engineSeasonProjection)!==null)?round1(Number(p.engineSeasonProjection)-r.points):null;}
  return state.projectedReplacementLevels;
}
function fastProjectionRanksAndEdges(){
  const players=arr(),eligible=players.filter(p=>p.leagueEligible&&finite(p.engineSeasonProjection)!==null).slice().sort((a,b)=>Number(b.engineSeasonProjection)-Number(a.engineSeasonProjection)),rank=new Map();eligible.forEach((p,i)=>rank.set(p,i+1));
  for(const p of players){p.projectionRank=rank.get(p)??null;const adp=finite(p.marketADP);p.marketEdge=(adp!==null&&adp>0&&adp<999&&p.projectionRank!==null)?round1(adp-p.projectionRank):null;}return eligible;
}

function rowsAll(){const w=st()?.weekly||{};return [...(w.weekly2025||[]),...(w.weekly2026||[])];}
function regularRow(r){return String(r?.season_type||r?.game_type||'REG').toUpperCase().startsWith('REG');}
function playerPublicId(p){return String(p?.gsisId||p?.publicPlayerId||'');}
function buildCycleCaches(){
  const state=st(),players=arr(),weekly=rowsAll(),byPlayer=new Map(),snapsByPfr=new Map(),teamRows=[...(state?.weekly?.team2025||[]),...(state?.weekly?.team2026||[])],teamByKey=new Map(),depthGroups=new Map(),starterByKey=new Map();
  for(const r of weekly){if(!regularRow(r))continue;const id=String(r?.player_id||r?.gsis_id||'');if(id)(byPlayer.get(id)??(byPlayer.set(id,[]),byPlayer.get(id))).push(r);}for(const xs of byPlayer.values())xs.sort((a,b)=>Number(a.season)-Number(b.season)||Number(a.week)-Number(b.week));
  for(const r of state?.weekly?.snaps2026||[]){const id=String(r?.pfr_player_id||'');if(id)(snapsByPfr.get(id)??(snapsByPfr.set(id,[]),snapsByPfr.get(id))).push(r);}for(const xs of snapsByPfr.values())xs.sort((a,b)=>Number(a.week)-Number(b.week));
  for(const r of teamRows){const team=String(r?.team||r?.recent_team||r?.posteam||r?.team_abbr||'');if(team)(teamByKey.get(team)??(teamByKey.set(team,[]),teamByKey.get(team))).push(r);}
  for(const p of players){const key=`${p.team||''}|${p.position||''}`;(depthGroups.get(key)??(depthGroups.set(key,[]),depthGroups.get(key))).push(p);if(Number(p.depthOrder)===1)starterByKey.set(key,p);}for(const xs of depthGroups.values())xs.sort((a,b)=>(Number(a.depthOrder)||99)-(Number(b.depthOrder)||99));
  return{weekly,byPlayer,snapsByPfr,teamByKey,depthGroups,starterByKey,recent:new Map(),snap:new Map(),usage:new Map(),matchup:new Map(),teamEnv:new Map(),market:new Map(),weather:new Map()};
}
function scoreRow(r,p){try{return finite(window.scorePublicStats?.(r,p));}catch{return null;}}
function recentFormCached(p,c){if(c.recent.has(p))return c.recent.get(p);const rows=c.byPlayer.get(playerPublicId(p))||[],hist=rows.map(r=>({season:Number(r.season),week:Number(r.week),pts:scoreRow(r,p)})).filter(x=>x.pts!==null),s=activeSeason();if(!hist.length){const z={recent:null,season:null,trend:50,vol:null,games:0};c.recent.set(p,z);return z;}const current=hist.filter(x=>x.season===s&&x.week<currentWeek()),base=current.length?current:hist.filter(x=>x.season===s-1),last=base.slice(-4),prior=base.slice(-8,-4),recent=mean(last.map(x=>x.pts)),season=mean(base.map(x=>x.pts));let trend=50;if(recent!==null&&season!==null&&season>0)trend=clamp(50+(recent/season-1)*55,20,85);if(prior.length&&recent!==null){const pm=mean(prior.map(x=>x.pts));if(pm>0)trend=clamp(trend+(recent/pm-1)*25,15,92);}const z={recent,season,trend,vol:sd(last.map(x=>x.pts)),games:base.length};c.recent.set(p,z);return z;}
function snapMomentumCached(p,c){if(c.snap.has(p))return c.snap.get(p);const rows=c.snapsByPfr.get(String(p?.pfrId||''))||[],vals=rows.filter(r=>Number(r.season||activeSeason())===activeSeason()).map(r=>Math.max(Number(r.offense_pct||r.off_pct||0),Number(r.defense_pct||r.def_pct||0))).map(v=>v>1?v/100:v).filter(v=>v>0);let z=null;if(vals.length){const last=mean(vals.slice(-2)),prev=mean(vals.slice(-5,-2));z=prev===null?clamp(35+last*55,25,92):clamp(50+(last-prev)*90,15,95);}c.snap.set(p,z);return z;}
function usageProfileCached(p,c){if(c.usage.has(p))return c.usage.get(p);let z;try{z=window.usageProfile?.(p);}catch{}if(!z)z={games:0,recent:null,base:null,ratio:null,score:50,component:'No weekly usage history'};c.usage.set(p,z);return z;}
function usageAdjustmentFrom(up,p){const learn=st()?.featureLearning?.byPosition?.[p.position];if(!learn?.active||!Number.isFinite(Number(up?.ratio)))return 0;return clamp(Number(learn.beta)*(Number(up.ratio)-1),-.05,.05);}
function rawMatchupCached(p,c){if(c.matchup.has(p))return c.matchup.get(p);let z;try{z=window.rawMatchupFactor?.(p);}catch{}if(!z)z={factor:1,defense:null,volume:null,n:0};c.matchup.set(p,z);return z;}
function matchupAdjustmentFrom(raw,p){const learn=st()?.featureLearning?.matchupByPosition?.[p.position];if(!learn?.active)return 0;return clamp(Number(learn.beta)*(Number(raw?.factor||1)-1),-.08,.08);}
function roleMomentumCached(p,c){const sm=snapMomentumCached(p,c),rf=recentFormCached(p,c).trend;return round1(sm===null?rf:sm*.7+rf*.3);}
function teammateBoostCached(p,c){if(Number(p.depthOrder)!==2)return 0;const inc=c.starterByKey.get(`${p.team||''}|${p.position||''}`);if(!inc)return 0;const x=String(inc.injuryStatus||'').toLowerCase();if(['out','ir','pup','suspended'].some(k=>x.includes(k)))return 24;if(x.includes('doubt'))return 15;if(x.includes('question'))return 8;return 0;}
function competitionCached(p,c){if(!p.team||!p.position)return 50;const xs=c.depthGroups.get(`${p.team}|${p.position}`)||[],order=Number(p.depthOrder||99),ahead=xs.filter(x=>Number(x.depthOrder)>0&&Number(x.depthOrder)<order);if(!ahead.length)return 20;return clamp(mean(ahead.map(x=>finite(x.modelScore)??finite(x.pffScore)??finite(x.tfgGrade)??60))??60,20,95);}
function teamEnvironmentCached(p,c){const key=`${p.team||''}|${p.position||''}`;if(c.teamEnv.has(key))return c.teamEnv.get(key);let z=50;try{z=Number(window.teamEnvironment?.(p));if(!Number.isFinite(z))z=50;}catch{}c.teamEnv.set(key,z);return z;}
function marketContextCached(p,c){const key=`${p.team||''}|${p.position||''}`;if(c.market.has(key))return c.market.get(key);let z={score:50,total:null,spread:null,implied:null};try{z=window.marketContext?.(p)||z;}catch{}c.market.set(key,z);return z;}
function weatherAdjustmentCached(p,c){const key=`${p.team||''}|${p.position||''}`;if(c.weather.has(key))return c.weather.get(key);let z=0;try{z=Number(window.weatherAdjustment?.(p))||0;}catch{}c.weather.set(key,z);return z;}
function injuryAdjustmentLocal(p){const x=String(p?.injuryStatus||'').toLowerCase();if(!x)return 0;if(x.includes('out')||x.includes('ir')||x.includes('pup'))return -100;if(x.includes('doubt'))return -45;if(x.includes('question'))return -18;return -5;}
function boundedAdjustment(p){try{const v=Number(window.boundedProjectionAdjustment?.(p));return Number.isFinite(v)?v:0;}catch{return 0;}}
function baselinePPGCached(p,c){const f=recentFormCached(p,c);if(f.recent!==null&&f.season!==null)return f.recent*.55+f.season*.45;if(f.season!==null)return f.season;if(finite(p.publicFantasyPPG)!==null)return Number(p.publicFantasyPPG);const repl=st()?.replacementLevels?.[p.position]?.score??55,posBase={QB:13,RB:7.5,WR:7.5,TE:5.5,DL:5.5,LB:7.5,DB:6.5,K:7,P:4};return (posBase[p.position]||5)*clamp((Number(p.modelScore)||Number(repl)||55)/60,.45,1.5);}
function weeklyProjectionCached(p,c,up,raw,role,teamEnv,boost){const sleeper=finite(p.sleeperWeeklyProjection),alpha=finite(st()?.calibration?.alpha)??1,adj=clamp(boundedAdjustment(p)*alpha,-.08,.08),uAdj=usageAdjustmentFrom(up,p),mAdj=matchupAdjustmentFrom(raw,p),market=marketContextCached(p,c),weather=weatherAdjustmentCached(p,c),inj=injuryAdjustmentLocal(p);let proj;if(sleeper!==null&&sleeper>=0){proj=sleeper*(1+adj)*(1+uAdj)*(1+mAdj)*(1+(Number(market.score||50)-50)/100*.08)*(1+weather/100)*(1+inj/100);if(inj<=-100)proj=0;return Math.max(0,proj);}const base=baselinePPGCached(p,c),roleAdj=clamp((Number(p.currentOpportunity||0)-60)/100,-.25,.30),match=(clamp(50+(Number(raw.factor||1)-1)*75+mAdj*100,20,90)-50)/100*.20,team=(teamEnv-50)/100*.10,marketAdj=(Number(market.score||50)-50)/100*.12,shock=boost/100*.30;proj=base*(1+roleAdj+match+team+marketAdj+weather/100+inj/100+shock+uAdj+mAdj);if(inj<=-100)proj=0;return Math.max(0,proj);}
function uncertaintyCached(p,c){const f=recentFormCached(p,c);let cv={QB:.30,RB:.45,WR:.52,TE:.48,DL:.58,LB:.32,DB:.42,K:.45}[p.position]||.50;if(Number(p.currentOpportunity||0)<70)cv+=.12;if(Number(p.pffReliability??1)<.4)cv+=.08;if(p.injuryStatus)cv+=.10;if(finite(p.sleeperWeeklyProjection)===null)cv+=.07;if(f.games>=3&&f.vol!==null&&f.season>0)cv=(cv+(f.vol/f.season))/2;return clamp(cv,.18,.85);}
function confidenceCached(p,c){const f=recentFormCached(p,c);let x=42;if(finite(p.sleeperWeeklyProjection)!==null)x+=22;if(Number(p.currentOpportunity||0)>=82)x+=10;else if(Number(p.currentOpportunity||0)<60)x-=8;if(finite(p.pffScore)!==null)x+=Math.round(10*(Number(p.pffReliability??.5)));if(finite(p.tfgModelScore)!==null)x+=5;if(f.games>=4)x+=8;else if(f.games===0)x-=5;if(p.injuryStatus)x-=12;if(Number(p.depthOrder)>1)x-=6;return clamp(Math.round(x),10,95);}

function quantileSorted(a,q){if(!a.length)return null;const i=(a.length-1)*q,l=Math.floor(i),h=Math.ceil(i);return l===h?a[l]:a[l]*(h-i)+a[h]*(i-l);}
function fastRiskBands(c){
  const state=st(),players=arr();try{window.loadValidationSnapshots?.();}catch{}
  const forward={};const weeklyBySW=new Map();for(const r of c.weekly){const k=`${Number(r.season)}:${Number(r.week)}`;let m=weeklyBySW.get(k);if(!m){m=new Map();weeklyBySW.set(k,m);}m.set(String(r.player_id||r.gsis_id||''),r);}
  for(const snap of Object.values(state?.validation?.snapshots||{})){const m=weeklyBySW.get(`${Number(snap.season)}:${Number(snap.week)}`);if(!m)continue;for(const p of players){const pr=snap?.players?.[p.sleeperId],row=m.get(playerPublicId(p));if(!pr||!row||finite(pr.engine)===null)continue;const actual=scoreRow(row,p);if(actual!==null)(forward[p.position]??=[]).push(actual-Number(pr.engine));}}
  const needHistorical=new Set(players.map(p=>p.position).filter(pos=>(forward[pos]||[]).length<40)),historical={};
  if(c.weekly.length){for(const p of players){if(!needHistorical.has(p.position))continue;const rows=c.byPlayer.get(playerPublicId(p))||[],pts=rows.map(r=>({r,pts:scoreRow(r,p)}));for(let i=3;i<pts.length;i++){const prior=pts.slice(Math.max(0,i-6),i).map(x=>x.pts).filter(Number.isFinite),actual=pts[i].pts,base=mean(prior.slice(-4));if(prior.length>=3&&Number.isFinite(actual)&&Number.isFinite(base))(historical[p.position]??=[]).push(actual-base);}}}
  const bands={};for(const pos of new Set(players.map(p=>p.position))){let res=forward[pos]||[],source='forward residual';if(res.length<40){res=historical[pos]||[];source='historical residual fallback';}if(res.length>=40){const sorted=res.filter(Number.isFinite).sort((a,b)=>a-b);bands[pos]={q10:quantileSorted(sorted,.10),q90:quantileSorted(sorted,.90),source};}}
  for(const p of players){if(p.m5WeeklyActive&&finite(p.m5LegacyWeeklyProjection)!==null){p.rangeSource='M6/M5 empirical calibrated';p.modelSource='M6 governed empirical';continue;}const meanP=Number(p.weeklyProjection)||0,b=bands[p.position];if(b){p.weeklyFloor=round1(Math.max(0,meanP+b.q10));p.weeklyCeiling=round1(Math.max(meanP,meanP+b.q90));p.rangeSource=b.source;p.weeklyCV=null;}else{const cv=uncertaintyCached(p,c);p.weeklyFloor=round1(Math.max(0,meanP*(1-1.2816*cv)));p.weeklyCeiling=round1(Math.max(meanP,meanP*(1+1.2816*cv)));p.rangeSource='heuristic low/high, not calibrated P10/P90';}p.modelSource=finite(p.sleeperWeeklyProjection)!==null?'Sleeper baseline + validated overlays':'heuristic fallback';}
}
function fastDecisionScores(){
  const players=arr(),fie=window.FIE89||{},valueFn=typeof fie.playerDecisionValue==='function'?fie.playerDecisionValue:(p=>Number(p.projectedVOR)||0),edgeFn=typeof fie.marketEdgeValue==='function'?fie.marketEdgeValue:(()=>null),values=new Map();for(const p of players)values.set(p,Number(valueFn(p))||0);const eligible=players.filter(p=>p.leagueEligible).slice().sort((a,b)=>values.get(b)-values.get(a)),rank=new Map();eligible.forEach((p,i)=>rank.set(p,i));const n=eligible.length;
  for(const p of players){const edge=finite(edgeFn(p));p.marketEdgeValue=edge;const r=rank.get(p),base=r!==undefined&&n>1?100-r*100/(n-1):50;p.seasonScore=round1(clamp(base+(edge!==null?edge*.8:0),0,100));if(p.availability!=='FA'||!p.leagueEligible)p.waiverScore=0;else{const momentum=(Number(p.roleMomentum)||50)-50,shock=(Number(p.opportunityShock)||50)-50;p.waiverScore=round1(clamp(values.get(p)*.75+momentum*.18+shock*.22,0,100));}}
  diagnostics.eligibleCount=n;
}
function scheduleFeatureLearning(){
  const state=st(),hasWeekly=(state?.weekly?.weekly2025?.length||0)+(state?.weekly?.weekly2026?.length||0)>0;if(!hasWeekly||featureLearningScheduled)return;if(state.featureLearning?.lastComputed&&state.featureLearning?.matchupLastComputed)return;
  featureLearningScheduled=true;diagnostics.featureLearningDeferred++;
  const run=()=>{featureLearningScheduled=false;/* Deliberately do not train inside the score publication. The existing Features view / explicit weekly workflow can run the OOS backtest. */};
  if(typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout:4000});else setTimeout(run,800);
}
function fastComputePredictionScores(){
  diagnostics.predictionRuns++;const c=timed('prediction-indexes',buildCycleCaches),players=arr();
  timed('prediction-player-pass',()=>{for(const p of players){const up=usageProfileCached(p,c),uAdj=usageAdjustmentFrom(up,p),role=roleMomentumCached(p,c),boost=teammateBoostCached(p,c),prior=p.snapShare===null||p.snapShare===undefined?50:clamp((Number(p.snapShare)>1?Number(p.snapShare):Number(p.snapShare)*100),0,100),shock=clamp(50+(Number(p.currentOpportunity||0)-prior)*.55+boost+(role-50)*.25,10,98),eff=(finite(p.pffScore)===null||finite(p.productionScore)===null)?50:clamp(50+(Number(p.pffScore)-Number(p.productionScore))*.75,15,90),raw=rawMatchupCached(p,c),mAdj=matchupAdjustmentFrom(raw,p),mScore=(Number(raw.factor||1)===1&&raw.defense==null&&raw.volume==null)?50:clamp(50+(Number(raw.factor||1)-1)*75+mAdj*100,20,90),teamEnv=teamEnvironmentCached(p,c);p.usageScore=round1(Number(up.score)||50);p.usageRatio=Number.isFinite(Number(up.ratio))?Math.round(Number(up.ratio)*1000)/1000:null;p.usageAdjustment=Math.round(uAdj*10000)/10000;p.roleMomentum=role;p.opportunityShock=shock;p.efficiencyRegression=eff;p.competitionStrength=competitionCached(p,c);p.matchupScore=mScore;p.matchupAdjustment=Math.round(mAdj*10000)/10000;p.matchupFactor=Math.round(Number(raw.factor||1)*1000)/1000;p.matchupDefenseFactor=raw.defense==null?null:Math.round(Number(raw.defense)*1000)/1000;p.matchupVolumeFactor=raw.volume==null?null:Math.round(Number(raw.volume)*1000)/1000;p.teamEnvironmentScore=teamEnv;p.weeklyProjection=round1(weeklyProjectionCached(p,c,up,raw,role,teamEnv,boost));const cv=uncertaintyCached(p,c);p.weeklyFloor=round1(Math.max(0,p.weeklyProjection*(1-1.2816*cv)));p.weeklyCeiling=round1(Math.max(p.weeklyProjection,p.weeklyProjection*(1+1.2816*cv)));p.weeklyConfidence=confidenceCached(p,c);p.weeklyCV=Math.round(cv*1000)/1000;p.startDecision='WATCH';}});
  timed('risk-bands',()=>fastRiskBands(c));timed('decision-rank',fastDecisionScores);return players;
}

function fastAssignScores(reason='model input changed'){
  const started=now(),state=st(),players=arr();diagnostics.scoreRuns++;diagnostics.playerCount=players.length;diagnostics.lastReason=String(reason||'');invalidateDemand();
  try{
    if(!state)throw new Error('state unavailable');state.modelHealth=state.modelHealth||{};state.modelHealth.recomputeCount=(Number(state.modelHealth.recomputeCount)||0)+1;state.modelHealth.lastReason=reason;
    timed('normalize-tfg',fastNormalizeTFG);
    const d=timed('starter-demand',demandMap),owned=ownershipByPosition(),teams=Math.max(1,Number(state.league?.total_rosters||state.rosters?.length||1)||1);
    timed('model-pass',()=>{for(const p of players){p.leagueEligible=Number(d[p.position]||0)>0;p.leagueFit=fastLeagueFit(p,d,owned,teams);const v=Number(window.weightedModel?.(p));p.modelScore=round1(Number.isFinite(v)?v:0);}});
    timed('replacement',fastReplacementLevels);
    timed('projected-replacement',fastProjectedReplacementLevels);
    if(state.projectionStatus?.season)timed('projection-ranks',fastProjectionRanksAndEdges);
    timed('target-pass',()=>{for(const p of players){const rep=window.replacementScoreFor?.(p)||{level:null,advantage:null,score:null,adjustment:0};p.replacementLevel=rep.level;p.replacementAdvantage=rep.advantage;p.replacementScore=rep.score;p.replacementAdjustment=rep.adjustment;const addBonus=p.availability==='FA'&&p.leagueEligible?Number(state.weights?.fa||0):0,trend=p.sleeperId&&state.trending?.[p.sleeperId]?Math.min(3,Math.log10(1+Number(state.trending[p.sleeperId]||0))*1.3):0;p.trendBonus=round1(trend);p.targetScore=round1(clamp(Number(p.modelScore||0)+addBonus+trend+Number(rep.adjustment||0),0,100));}});
    try{window.renderReplacementSummary?.();}catch(e){recordError(e,'render-replacement-summary');}
    scheduleFeatureLearning();timed('prediction',fastComputePredictionScores);timed('lineup',()=>window.optimizeLineup?.());
    state.modelHealth.lastMs=round1(now()-started);state.modelHealth.lastAt=new Date().toISOString();try{window.renderHealthDiagnostics?.();}catch(e){recordError(e,'render-health-diagnostics');}
    const total=now()-started;diagnostics.lastTotalMs=round1(total);diagnostics.maxTotalMs=Math.max(diagnostics.maxTotalMs,diagnostics.lastTotalMs);diagnostics.totals.push(diagnostics.lastTotalMs);if(diagnostics.totals.length>30)diagnostics.totals.shift();try{window.FIEPerformance?.push?.('934a3:assign-total',total,{leagueId:activeLeagueId(),reason:String(reason||''),players:players.length});}catch{}window.dispatchEvent?.(new CustomEvent('fie:score-published',{detail:{version:VERSION,leagueId:activeLeagueId(),ms:diagnostics.lastTotalMs,players:players.length}}));return players;
  }catch(e){recordError(e,'fast-assign');diagnostics.fallbacks++;if(typeof legacyAssign==='function'&&legacyAssign!==fastAssignScores)return legacyAssign(reason);throw e;}
}
function report(){return{version:VERSION,release:RELEASE,leagueId:activeLeagueId(),diagnostics:{...diagnostics,phaseMs:{...diagnostics.phaseMs},demand:{...diagnostics.demand}},performance:window.FIEPerformance?.snapshot?.()||null};}
function install(){
  installAttempts++;const deps=window.FIE934A2?.installed&&window.FIE89&&required('weightedModel')&&required('scoringFit')&&required('replacementScoreFor')&&required('optimizeLineup');if(!deps){if(installAttempts<INSTALL_LIMIT)setTimeout(install,100);else console.warn('FIE V9.3.4A3 dependencies unavailable.');return;}
  if(installed)return;installed=true;diagnostics.installs++;
  legacyAssign=window.assignScores;legacyComputePrediction=window.computePredictionScores;legacyDemand=window.leaguePositionDemand;legacyReplacement=window.computeReplacementLevels;legacyProjectedReplacement=window.computeProjectedReplacementLevels;legacyProjectionRanks=window.computeProjectionRanksAndEdges;
  window.leaguePositionDemand=fastLeaguePositionDemand;window.computeReplacementLevels=fastReplacementLevels;window.computeProjectedReplacementLevels=fastProjectedReplacementLevels;window.computeProjectionRanksAndEdges=fastProjectionRanksAndEdges;window.computePredictionScores=fastComputePredictionScores;window.assignScores=fastAssignScores;
  fastAssignScores.__fie934a3Fast=true;fastAssignScores.__legacy=legacyAssign;fastComputePredictionScores.__fie934a3Fast=true;fastLeaguePositionDemand.__fie934a3Fast=true;
  const a2=window.FIE934A2;if(a2&&typeof a2.report==='function'&&!a2.report.__fie934a3Augmented){const old=a2.report.bind(a2),wrapped=()=>{const base=old();return{...base,a3:report()};};wrapped.__fie934a3Augmented=true;a2.report=wrapped;}
  window.addEventListener('fie:league-changing',()=>{invalidateDemand();featureLearningScheduled=false;});
}

window.FIE934A3={installed:true,VERSION,RELEASE,diagnostics,report,invalidateDemand,computeMarginalDemand,fastAssignScores,fastComputePredictionScores,legacy:{get assignScores(){return legacyAssign;},get computePredictionScores(){return legacyComputePrediction;},get leaguePositionDemand(){return legacyDemand;},get computeReplacementLevels(){return legacyReplacement;},get computeProjectedReplacementLevels(){return legacyProjectedReplacement;},get computeProjectionRanksAndEdges(){return legacyProjectionRanks;}}};
install();
})();

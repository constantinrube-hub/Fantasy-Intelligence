/* Fantasy Intelligence Engine core services.
 * Canonical football/runtime semantics shared by Draft, Value Finder, Monte Carlo,
 * Start/Sit, trades, and future D/ST integration.
 */
(function(){
'use strict';
const C=window.FIERuntimeContracts||{};
const SLOT=C.roster_slots||{};
const ALIAS=C.position_aliases||{};
function finite(x){const n=Number(x);return Number.isFinite(n)?n:null;}
function canonicalPos(p){const x=String(p||'').toUpperCase();return ALIAS[x]||x;}
function playerId(p){const id=p?.sleeperId??p?.player_id??p?.playerId??p?.id;if(id!==undefined&&id!==null&&String(id).trim())return String(id);const name=String(p?.name||p?.full_name||'unknown').trim().toLowerCase(),team=String(p?.team||'FA').toUpperCase(),pos=canonicalPos(p?.position||p?.fantasy_positions?.[0]||'UNK');return `synthetic:${pos}:${team}:${name}`;}
function fnv(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}
function stable(value){if(value===null||typeof value!=='object')return JSON.stringify(value);if(Array.isArray(value))return '['+value.map(stable).join(',')+']';return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';}

const PositionRegistry={
  canonical:canonicalPos,
  slot(slot){return SLOT[String(slot||'').toUpperCase()]||null;},
  eligible(position,slot){const s=this.slot(slot);return !!s&&s.positions.includes(canonicalPos(position));},
  starterSlots(rosterPositions){return (rosterPositions||[]).map(String).filter(s=>this.slot(s)?.starter===true);},
  rosterablePositions(rosterPositions){const out=new Set();for(const s of rosterPositions||[]){for(const p of this.slot(s)?.positions||[])out.add(canonicalPos(p));}return out;},
  slotPositions(slot){return [...(this.slot(slot)?.positions||[])];},
  isStarter(slot){return this.slot(slot)?.starter===true;},
  contractsSha:C.contract_sha256||null
};

function hungarianMin(cost){const n=cost.length,m=cost[0]?.length||0;if(!n||!m)return[];const u=Array(n+1).fill(0),v=Array(m+1).fill(0),p=Array(m+1).fill(0),way=Array(m+1).fill(0);for(let i=1;i<=n;i++){p[0]=i;let j0=0;const minv=Array(m+1).fill(Infinity),used=Array(m+1).fill(false);do{used[j0]=true;const i0=p[j0];let delta=Infinity,j1=0;for(let j=1;j<=m;j++)if(!used[j]){const cur=cost[i0-1][j-1]-u[i0]-v[j];if(cur<minv[j]){minv[j]=cur;way[j]=j0;}if(minv[j]<delta){delta=minv[j];j1=j;}}for(let j=0;j<=m;j++)if(used[j]){u[p[j]]+=delta;v[j]-=delta;}else minv[j]-=delta;j0=j1;}while(p[j0]!==0);do{const j1=way[j0];p[j0]=p[j1];j0=j1;}while(j0!==0);}const ans=Array(n).fill(-1);for(let j=1;j<=m;j++)if(p[j])ans[p[j]-1]=j-1;return ans;}

const LineupOptimizer={
  optimize(players,rosterPositions,valueFn){const slots=PositionRegistry.starterSlots(rosterPositions),pool=(players||[]).filter(Boolean);if(!slots.length)return{total:0,assignment:[],selectedPlayerIds:[],benchPlayerIds:pool.map(playerId),unfilledSlots:[]};const m=Math.max(pool.length,slots.length),NEG=-1e12;const matrix=slots.map(slot=>Array.from({length:m},(_,j)=>{if(j>=pool.length)return 0;const p=pool[j],v=finite(valueFn(p));return PositionRegistry.eligible(p.position,slot)&&v!==null?v:NEG;}));const maxVal=Math.max(0,...matrix.flat().filter(x=>x>NEG/2)),cost=matrix.map(r=>r.map(x=>x<=NEG/2?maxVal+1e9:maxVal-x)),assign=hungarianMin(cost),assignment=[],selected=new Set(),unfilled=[];let total=0;for(let i=0;i<slots.length;i++){const j=assign[i],valid=j>=0&&j<pool.length&&matrix[i][j]>NEG/2;if(!valid){unfilled.push(slots[i]);continue;}const p=pool[j],v=matrix[i][j],id=playerId(p);total+=v;selected.add(id);assignment.push({slot:slots[i],playerId:id,player:p,value:v});}return{total,assignment,selectedPlayerIds:[...selected],benchPlayerIds:pool.map(playerId).filter(id=>!selected.has(id)),unfilledSlots:unfilled};},
  objectiveForFormat(format){const f=String(format||'REDRAFT').toUpperCase();if(f==='CHOPPED')return p=>.55*(finite(p.__fie_mean)??0)+.45*(finite(p.__fie_floor)??finite(p.__fie_mean)??0);if(f.includes('BESTBALL'))return p=>.45*(finite(p.__fie_mean)??0)+.55*(finite(p.__fie_ceiling)??finite(p.__fie_mean)??0);if(f.includes('DYNASTY'))return p=>finite(p.__fie_utility)??finite(p.__fie_mean)??0;return p=>finite(p.__fie_mean)??0;},
  rosterUtility(players,{format='REDRAFT',rosterPositions=[]}={}){const vf=this.objectiveForFormat(format),opt=this.optimize(players,rosterPositions,vf),bench=(players||[]).filter(p=>opt.benchPlayerIds.includes(playerId(p))),benchBonus=bench.map(p=>Math.max(0,finite(p.__fie_vor)??0)).sort((a,b)=>b-a).slice(0,Math.max(0,(rosterPositions||[]).filter(s=>!PositionRegistry.isStarter(s)).length)).reduce((a,b)=>a+b,0)*.12;return{...opt,starterTotal:opt.total,benchBonus,total:opt.total+benchBonus,method:'canonical exact slot assignment'};}
};

const LeagueDemandService={
  starterDemand({league,players,valueFn}){const teams=Math.max(1,finite(league?.total_rosters)||finite(league?.settings?.teams)||1),slots=league?.roster_positions||[],pool=(players||[]).filter(Boolean),posSet=new Set(pool.map(p=>canonicalPos(p.position))),counts=Object.fromEntries([...posSet].map(p=>[p,0])),used=Object.fromEntries([...posSet].map(p=>[p,0])),byPos={};for(const pos of posSet)byPos[pos]=pool.filter(p=>canonicalPos(p.position)===pos).sort((a,b)=>(finite(valueFn(b))??-Infinity)-(finite(valueFn(a))??-Infinity));
    const slotCounts={};for(const s of slots)if(PositionRegistry.isStarter(s))slotCounts[s]=(slotCounts[s]||0)+teams;
    // Allocate single-position slots first.
    for(const [slot,n] of Object.entries(slotCounts)){const elig=PositionRegistry.slotPositions(slot);if(elig.length!==1)continue;const pos=elig[0];counts[pos]=(counts[pos]||0)+n;used[pos]=(used[pos]||0)+n;}
    // Allocate flexible slots one league starter at a time to the best marginal player.
    for(const [slot,n0] of Object.entries(slotCounts)){const elig=PositionRegistry.slotPositions(slot);if(elig.length<=1)continue;let n=n0;while(n-->0){let bestPos=null,bestVal=-Infinity;for(const pos of elig){const cand=byPos[pos]?.[used[pos]||0],v=cand?finite(valueFn(cand)):null;if(v!==null&&v>bestVal){bestVal=v;bestPos=pos;}}if(bestPos===null)break;counts[bestPos]=(counts[bestPos]||0)+1;used[bestPos]=(used[bestPos]||0)+1;}}
    return{teams,leagueStarterDemand:counts,perTeam:Object.fromEntries(Object.entries(counts).map(([p,n])=>[p,n/teams])),starterSlotsPerTeam:PositionRegistry.starterSlots(slots).length};
  }
};

const ReplacementService={
  profile(position,{league=window.state?.league,players=(typeof PLAYERS!=='undefined'?PLAYERS:window.PLAYERS||[]),state=window.state,valueFn=p=>finite(p.engineSeasonProjection)??finite(p.sleeperSeasonProjection)??finite(p.modelScore)??0}={}){const pos=canonicalPos(position),pool=(players||[]).filter(Boolean),demandProfile=LeagueDemandService.starterDemand({league,players:pool,valueFn}),starterDemand=Math.max(0,finite(demandProfile.leagueStarterDemand[pos])??0),starterSlots=Math.max(1,demandProfile.starterSlotsPerTeam||PositionRegistry.starterSlots(league?.roster_positions||[]).length||1),benchSlots=(league?.roster_positions||[]).filter(s=>!PositionRegistry.isStarter(s)).length,benchInfluence=Math.max(0,Math.min(1,(finite(state?.replacement?.benchInfluence)??0)/100)),benchShare=(benchSlots/starterSlots)*benchInfluence,structuralDemand=starterDemand*(1+benchShare),actualOwned=pool.filter(p=>canonicalPos(p.position)===pos&&(p.availability==='OWNED'||finite(p.ownerRosterId)!==null)).length,cutoff=Math.max(1,Math.round(structuralDemand||starterDemand||1));return{position:pos,teams:demandProfile.teams,starterDemand,perTeam:finite(demandProfile.perTeam?.[pos])??0,benchSlots,starterSlotsPerTeam:starterSlots,benchInfluence,benchShare,projectedOwned:structuralDemand,effectiveOwned:structuralDemand,actualOwned,cutoff,method:'canonical structural starter-slot demand'};},
  cutoff(position,opts={}){return this.profile(position,opts).cutoff;},
  row(position,rows,key,{league=window.state?.league,state=window.state}={}){const pos=canonicalPos(position),xs=(rows||[]).filter(x=>canonicalPos(x?.p?.position??x?.position)===pos).sort((a,b)=>(finite(b[key])??-Infinity)-(finite(a[key])??-Infinity));if(!xs.length)return{cutoff:1,value:0,row:null};const cutoff=this.cutoff(pos,{league,state,players:(rows||[]).map(x=>x.p||x),valueFn:p=>finite(p.engineSeasonProjection)??finite(p.sleeperSeasonProjection)??finite(p.modelScore)??0}),idx=Math.min(xs.length-1,Math.max(0,cutoff-1)),r=xs[idx];return{cutoff,value:finite(r[key])??0,row:r};}
};

const RosterValueService={
  decorate(p,format){const season=finite(p.engineSeasonProjection)??finite(p.sleeperSeasonProjection)??finite(p.seasonScore)??0,weekly=finite(p.weeklyProjection)??finite(p.sleeperWeeklyProjection)??season/17;return Object.assign({},p,{__fie_mean:String(format).includes('CHOPPED')||String(format).includes('BESTBALL')?weekly:season,__fie_floor:String(format).includes('CHOPPED')?(finite(p.weeklyFloor)??weekly):season,__fie_ceiling:String(format).includes('BESTBALL')?(finite(p.weeklyCeiling)??weekly):season,__fie_utility:finite(p.m5DraftUtility)??finite(p.targetScore)??season,__fie_vor:finite(p.projectedVOR)??0});},
  marginal(player,rosterPool,{format='REDRAFT',rosterPositions=[]}={}){const base=(rosterPool||[]).map(p=>this.decorate(p,format)),candidate=this.decorate(player,format),before=LineupOptimizer.rosterUtility(base,{format,rosterPositions}),after=LineupOptimizer.rosterUtility(base.concat(candidate),{format,rosterPositions});return{gain:after.total-before.total,starterGain:after.starterTotal-before.starterTotal,before,after,method:'exact legal lineup marginal'};}
};

const ContextFingerprint={
  build(extra={}){const st=window.state||{},manifest=window.FIE_BUILD_MANIFEST||{},research=window.FIE_M5?.getCurrentBundle?.()||{};return fnv(stable({leagueId:st.league?.league_id||null,profile:st.league?.__fieProfileFingerprint||null,scoring:st.league?.scoring_settings||{},roster:(st.rosters||[]).map(r=>({id:r.roster_id,players:(r.players||[]).map(String).sort()})),draft:(st.draftIntel?.picks||[]).map(p=>String(p.player_id||p.playerId||'')),season:window.FIESeasonContext?.snapshot?.()||null,projection:{season:st.projectionStatus?.season,seasonCount:st.projectionStatus?.seasonCount,weekly:st.projectionStatus?.weekly,weeklyCount:st.projectionStatus?.weeklyCount},research:research.generated_at||research.snapshot_id||null,model:manifest.draft_model_version||window.FIEModelV9?.VERSION||null,contracts:C.contract_sha256||null,...extra}));}
};

const Diagnostics={buffer:[],max:200,redact(value){let s=String(value??'');s=s.replace(/([?&](?:api_?key|key|token|secret|authorization)=)[^&#\s]*/gi,'$1[REDACTED]');s=s.replace(/(Bearer\s+)[A-Za-z0-9._~+\/-]+/gi,'$1[REDACTED]');return s;},capture(error,context={}){const row={at:new Date().toISOString(),message:this.redact(error?.message||error),stack:this.redact(error?.stack||''),leagueId:window.state?.league?.league_id||null,release:window.FIE_BUILD_MANIFEST?.app_version||window.FIE?.VERSION||null,...context};this.buffer.push(row);if(this.buffer.length>this.max)this.buffer.splice(0,this.buffer.length-this.max);return row;},snapshot(){return this.buffer.slice();}};

window.FIECore={version:'9.3.1-consolidation',PositionRegistry,PlayerIdentity:{id:playerId,canonicalPosition:canonicalPos},LineupOptimizer,LeagueDemandService,ReplacementService,RosterValueService,ContextFingerprint,Diagnostics};
})();

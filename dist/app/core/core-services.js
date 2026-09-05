/* Fantasy Intelligence Engine core services.
 * Canonical football/runtime semantics shared by Draft, Value Finder, Monte Carlo,
 * Start/Sit, trades, and future D/ST integration.
 */
(function(){
'use strict';
const C=window.FIERuntimeContracts||{};
const SLOT=C.roster_slots||{};
const ALIAS=C.position_aliases||{};
const FORMAT=C.league_formats||{};
function finite(x){if(x===null||x===undefined||(typeof x==='string'&&x.trim()===''))return null;const n=Number(x);return Number.isFinite(n)?n:null;}
function canonicalPos(p){const x=String(p||'').toUpperCase();return ALIAS[x]||x;}
const IDENTITY_RULES=Object.freeze([
  {field:'sleeperId',namespace:'sleeper',output:'raw'},
  {field:'sleeper_id',namespace:'sleeper',output:'raw'},
  {field:'player_id',namespace:'legacy',output:'raw'},
  {field:'playerId',namespace:'legacy',output:'raw'},
  {field:'canonical_player_id',namespace:'canonical',output:'canonical'},
  {field:'internal_id',namespace:'canonical',output:'canonical'},
  {field:'gsis_id',namespace:'gsis',output:'gsis'},
  {field:'pfr_id',namespace:'pfr',output:'pfr'},
  {field:'fantasypros_id',namespace:'fantasypros',output:'fantasypros'},
  {field:'id',namespace:'legacy',output:'raw'}
]);
function identityRaw(v){if(v===undefined||v===null)return null;const s=String(v).trim();return s||null;}
function identityName(p){return String(p?.name||p?.full_name||'').trim().toLowerCase().replace(/\s+/g,' ');}
function identityOutput(ns,v){if(ns==='sleeper'||ns==='legacy')return v;if(ns==='canonical')return `canonical:${v}`;return `${ns}:${v}`;}
function identityAliases(p){if(!p||typeof p!=='object')return[];const out=[],seen=new Set();for(const r of IDENTITY_RULES){const v=identityRaw(p?.[r.field]);if(!v)continue;const keys=[];if(r.namespace==='sleeper')keys.push(`sleeper:${v}`,`legacy:${v}`);else keys.push(`${r.namespace}:${v}`);const token=identityOutput(r.namespace,v),sig=`${r.namespace}|${v}`;if(seen.has(sig))continue;seen.add(sig);out.push({field:r.field,namespace:r.namespace,value:v,id:token,keys});}
  const pos=canonicalPos(p?.position||p?.position_model||p?.fantasy_positions?.[0]||'UNK'),team=identityRaw(p?.team??(pos==='DEF'?(p?.sleeperId??p?.sleeper_id):null));if(pos==='DEF'&&team){const v=team.toUpperCase(),sig=`teamdef|${v}`;if(!seen.has(sig)){seen.add(sig);out.push({field:'team',namespace:'teamdef',value:v,id:`teamdef:${v}`,keys:[`teamdef:${v}`]});}}
  for(const a of [...out])if(a.namespace==='canonical'&&/^DST:/i.test(a.value)){const v=a.value.replace(/^DST:/i,'').toUpperCase(),sig=`teamdef|${v}`;if(!seen.has(sig)){seen.add(sig);out.push({field:a.field,namespace:'teamdef',value:v,id:`teamdef:${v}`,keys:[`teamdef:${v}`]});}}
  return out;}
function identityLookupKeys(subject){if(subject&&typeof subject==='object')return [...new Set(identityAliases(subject).flatMap(a=>a.keys))];const raw=identityRaw(subject);if(!raw)return[];const m=/^(canonical|gsis|pfr|fantasypros|teamdef):(.*)$/i.exec(raw);if(m)return[`${m[1].toLowerCase()}:${m[2]}`];return[`sleeper:${raw}`,`legacy:${raw}`];}
function governedIdentityId(p){return identityAliases(p)[0]?.id??null;}
function syntheticIdentityId(p){const name=identityName(p)||'unknown',team=String(p?.team||'FA').toUpperCase(),pos=canonicalPos(p?.position||p?.fantasy_positions?.[0]||'UNK');return `synthetic:${pos}:${team}:${name}`;}
function playerId(p){return PlayerIdentity.id(p);}
function fnv(str){let h=2166136261>>>0;for(let i=0;i<str.length;i++){h^=str.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}
function stable(value){if(value===null||typeof value!=='object')return JSON.stringify(value);if(Array.isArray(value))return '['+value.map(stable).join(',')+']';return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';}

const Numeric={finiteOrNull:finite,optionalCap(x){const n=finite(x);return n!==null&&n>=0?Math.trunc(n):null;},positiveIntOrNull(x){const n=finite(x);return n!==null&&n>0?Math.trunc(n):null;}};

const PlayerIdentity={
  source:'FIECore.PlayerIdentity',
  aliases(subject){return identityAliases(subject).map(a=>({...a,keys:[...a.keys]}));},
  governedId(subject){return governedIdentityId(subject);},
  id(subject,{allowSynthetic=true}={}){const stable=governedIdentityId(subject);return stable??(allowSynthetic?syntheticIdentityId(subject):null);},
  index(players=(window.PLAYERS||[])){const map=new Map();for(const p of players||[])for(const key of identityLookupKeys(p)){if(!map.has(key))map.set(key,new Set());map.get(key).add(p);}return{players:[...(players||[])],map};},
  resolve(subject,{players=(window.PLAYERS||[]),index=null}={}){const idx=index?.map instanceof Map?index:this.index(players),keys=identityLookupKeys(subject),candidates=new Set();for(const key of keys)for(const p of idx.map.get(key)||[])candidates.add(p);const xs=[...candidates];if(xs.length===1){const player=xs[0],id=this.governedId(player);return{status:'resolved',id,player,source:this.source,matchedKeys:keys.filter(k=>idx.map.get(k)?.has(player)),aliases:this.aliases(player)};}if(xs.length>1)return{status:'ambiguous',id:null,player:null,source:this.source,reason:'canonical_alias_collision',candidateIds:xs.map(p=>this.governedId(p)).filter(Boolean),matchedKeys:keys};if(!keys.length){const name=identityName(subject),nameMatches=name?(players||[]).filter(p=>identityName(p)===name):[];if(nameMatches.length>1)return{status:'ambiguous',id:null,player:null,source:this.source,reason:'display_name_collision_not_identity',candidateIds:nameMatches.map(p=>this.governedId(p)).filter(Boolean),matchedKeys:[]};return{status:'unavailable',id:null,player:null,source:this.source,reason:nameMatches.length===1?'display_name_not_canonical':'no_stable_identity',candidateIds:[],matchedKeys:[]};}return{status:'unavailable',id:null,player:null,source:this.source,reason:'no_canonical_match',candidateIds:[],matchedKeys:keys};},
  byId(id){const r=this.resolve(id);return r.status==='resolved'?r.player:null;},
  positionForId(id){const p=this.byId(id);return p?canonicalPos(p.position):'UNK';}
};

const FormatRegistry={
  key(format){const f=String(format||'REDRAFT').toUpperCase();return FORMAT[f]?f:'REDRAFT';},
  profile(format){const key=this.key(format),p=FORMAT[key]||{};return Object.freeze({key,label:String(p.label||key),dynasty:p.dynasty===true,bestBall:p.best_ball===true,chopped:p.chopped===true});},
  isDynasty(format){return this.profile(format).dynasty;},
  isBestBall(format){return this.profile(format).bestBall;},
  isChopped(format){return this.profile(format).chopped;},
  contractsSha:C.contract_sha256||null
};

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
  objectiveForFormat(format){const fp=FormatRegistry.profile(format);if(fp.chopped&&fp.bestBall)return p=>.50*(finite(p.__fie_mean)??0)+.225*(finite(p.__fie_floor)??finite(p.__fie_mean)??0)+.275*(finite(p.__fie_ceiling)??finite(p.__fie_mean)??0);if(fp.chopped)return p=>.55*(finite(p.__fie_mean)??0)+.45*(finite(p.__fie_floor)??finite(p.__fie_mean)??0);if(fp.bestBall)return p=>.45*(finite(p.__fie_mean)??0)+.55*(finite(p.__fie_ceiling)??finite(p.__fie_mean)??0);if(fp.dynasty)return p=>finite(p.__fie_utility)??finite(p.__fie_mean)??0;return p=>finite(p.__fie_mean)??0;},
  rosterUtility(players,{format='REDRAFT',rosterPositions=[]}={}){const vf=this.objectiveForFormat(format),opt=this.optimize(players,rosterPositions,vf),bench=(players||[]).filter(p=>opt.benchPlayerIds.includes(playerId(p))),benchBonus=bench.map(p=>Math.max(0,finite(p.__fie_vor)??0)).sort((a,b)=>b-a).slice(0,Math.max(0,(rosterPositions||[]).filter(s=>!PositionRegistry.isStarter(s)).length)).reduce((a,b)=>a+b,0)*.12;return{...opt,starterTotal:opt.total,benchBonus,total:opt.total+benchBonus,method:'canonical exact slot assignment'};}
};

function defaultDemandValue(p){return finite(p?.engineSeasonProjection)??finite(p?.sleeperSeasonProjection)??finite(p?.modelScore)??0;}

const LeagueDemandService={
  defaultValue:defaultDemandValue,
  starterDemand({league,players,valueFn=defaultDemandValue}){const teams=Math.max(1,finite(league?.total_rosters)||finite(league?.settings?.teams)||finite(league?.settings?.num_teams)||1),slots=league?.roster_positions||[],pool=(players||[]).filter(Boolean),posSet=new Set(pool.map(p=>canonicalPos(p.position))),counts=Object.fromEntries([...posSet].map(p=>[p,0])),used=Object.fromEntries([...posSet].map(p=>[p,0])),fixed=Object.fromEntries([...posSet].map(p=>[p,0])),byPos={},slotAllocations={};for(const pos of posSet)byPos[pos]=pool.filter(p=>canonicalPos(p.position)===pos).sort((a,b)=>(finite(valueFn(b))??-Infinity)-(finite(valueFn(a))??-Infinity));
    const slotCounts={};for(const s of slots)if(PositionRegistry.isStarter(s))slotCounts[s]=(slotCounts[s]||0)+teams;
    const allocate=(pos,n,slot)=>{if(!pos||!byPos[pos])return 0;const can=Math.min(Math.max(0,Number(n)||0),Math.max(0,byPos[pos].length-(used[pos]||0)));used[pos]=(used[pos]||0)+can;counts[pos]=(counts[pos]||0)+can;if(slot){slotAllocations[slot]=slotAllocations[slot]||{};slotAllocations[slot][pos]=(slotAllocations[slot][pos]||0)+can;}return can;};
    for(const [slot,n] of Object.entries(slotCounts)){const elig=PositionRegistry.slotPositions(slot);if(elig.length!==1)continue;const pos=elig[0],got=allocate(pos,n,slot);fixed[pos]=(fixed[pos]||0)+got;}
    for(const [slot,n0] of Object.entries(slotCounts)){const elig=PositionRegistry.slotPositions(slot);if(elig.length<=1)continue;let n=n0;while(n-->0){let bestPos=null,bestVal=-Infinity;for(const pos of elig){const cand=byPos[pos]?.[used[pos]||0],v=cand?finite(valueFn(cand)):null;if(v!==null&&v>bestVal){bestVal=v;bestPos=pos;}}if(bestPos===null)break;allocate(bestPos,1,slot);}}
    return{teams,leagueStarterDemand:counts,effectiveDemand:counts,fixedDemand:fixed,perTeam:Object.fromEntries(Object.entries(counts).map(([p,n])=>[p,n/teams])),starterSlotsPerTeam:PositionRegistry.starterSlots(slots).length,slotAllocations,used};
  }
};

function replacementRankForDemand(demand,poolLength=null){const d=Math.max(0,finite(demand)??0),raw=Math.max(1,Math.floor(d)+1),n=finite(poolLength);return n!==null&&n>0?Math.min(Math.trunc(n),raw):raw;}
function replacementProfileFromDemand(position,{league,players,state,demandProfile}){const pos=canonicalPos(position),pool=(players||[]).filter(Boolean),starterDemand=Math.max(0,finite(demandProfile?.leagueStarterDemand?.[pos])??0),starterSlots=Math.max(1,demandProfile?.starterSlotsPerTeam||PositionRegistry.starterSlots(league?.roster_positions||[]).length||1),benchSlots=(league?.roster_positions||[]).filter(s=>!PositionRegistry.isStarter(s)).length,benchInfluence=Math.max(0,Math.min(1,(finite(state?.replacement?.benchInfluence)??0)/100)),benchShare=(benchSlots/starterSlots)*benchInfluence,structuralDemand=starterDemand*(1+benchShare),positionPool=pool.filter(p=>canonicalPos(p.position)===pos),actualOwned=positionPool.filter(p=>p.availability==='OWNED'||finite(p.ownerRosterId)!==null).length,cutoff=replacementRankForDemand(structuralDemand,positionPool.length),structuralPressure=positionPool.length?Math.min(1,structuralDemand/positionPool.length):0;return{position:pos,teams:demandProfile?.teams??1,starterDemand,structuralDemand,perTeam:finite(demandProfile?.perTeam?.[pos])??0,benchSlots,starterSlotsPerTeam:starterSlots,benchInfluence,benchShare,projectedOwned:structuralDemand,effectiveOwned:structuralDemand,actualOwned,positionPoolSize:positionPool.length,structuralPressure,cutoff,structuralCutoff:cutoff,sourceCutoff:cutoff,source:'FIECore.ReplacementService',cutoffConvention:'replacement_player_rank_1_based',ownershipAffectsCutoff:false,method:'canonical structural replacement-player rank'};}

const ReplacementService={
  source:'FIECore.ReplacementService',
  cutoffConvention:'replacement_player_rank_1_based',
  rankForDemand:replacementRankForDemand,
  profile(position,{league=window.state?.league,players=(typeof PLAYERS!=='undefined'?PLAYERS:window.PLAYERS||[]),state=window.state,valueFn=defaultDemandValue}={}){const pool=(players||[]).filter(Boolean),demandProfile=LeagueDemandService.starterDemand({league,players:pool,valueFn});return replacementProfileFromDemand(position,{league,players:pool,state,demandProfile});},
  profiles({league=window.state?.league,players=(typeof PLAYERS!=='undefined'?PLAYERS:window.PLAYERS||[]),state=window.state,valueFn=defaultDemandValue,positions=null}={}){const pool=(players||[]).filter(Boolean),demandProfile=LeagueDemandService.starterDemand({league,players:pool,valueFn}),posSet=new Set((positions||[]).map(canonicalPos));for(const p of pool)posSet.add(canonicalPos(p.position));for(const p of Object.keys(demandProfile.leagueStarterDemand||{}))posSet.add(canonicalPos(p));const out={};for(const pos of posSet)out[pos]=replacementProfileFromDemand(pos,{league,players:pool,state,demandProfile});Object.defineProperty(out,'__demand',{value:demandProfile,enumerable:false});return out;},
  cutoff(position,opts={}){return this.profile(position,opts).cutoff;},
  levels({league=window.state?.league,players=(typeof PLAYERS!=='undefined'?PLAYERS:window.PLAYERS||[]),state=window.state,demandValueFn=defaultDemandValue,valueFn=defaultDemandValue,positions=null}={}){const pool=(players||[]).filter(Boolean),profiles=this.profiles({league,players:pool,state,valueFn:demandValueFn,positions}),out={};for(const [pos,profile] of Object.entries(profiles)){const xs=pool.filter(p=>canonicalPos(p.position)===pos&&finite(valueFn(p))!==null).sort((a,b)=>(finite(valueFn(b))??-Infinity)-(finite(valueFn(a))??-Infinity));if(!xs.length)continue;const idx=Math.min(xs.length-1,Math.max(0,profile.cutoff-1)),rp=xs[idx],value=finite(valueFn(rp))??0;out[pos]={position:pos,value,points:value,player:rp?.name||null,playerId:playerId(rp),cutoff:idx+1,structuralCutoff:profile.structuralCutoff,sourceCutoff:profile.sourceCutoff,source:this.source,cutoffConvention:this.cutoffConvention,method:'canonical replacement level from structural cutoff'};}return out;},
  projectedLevels(opts={}){return this.levels(opts);},
  applyProjectionVOR(players,levels,{projectionFn=defaultDemandValue}={}){for(const p of players||[]){const pos=canonicalPos(p?.position),level=levels?.[pos],proj=finite(projectionFn(p));p.projectedReplacementPoints=level?.points??null;p.projectedReplacementCutoff=level?.cutoff??null;p.projectedReplacementSource=level?.source??this.source;p.projectedVORSource=level?.source??this.source;p.projectedVOR=level&&proj!==null?proj-Number(level.points):null;}return players;},
  row(position,rows,key,{league=window.state?.league,state=window.state}={}){const pos=canonicalPos(position),xs=(rows||[]).filter(x=>canonicalPos(x?.p?.position??x?.position)===pos).sort((a,b)=>(finite(b[key])??-Infinity)-(finite(a[key])??-Infinity));if(!xs.length)return{cutoff:1,value:0,row:null,source:this.source};const cutoff=this.cutoff(pos,{league,state,players:(rows||[]).map(x=>x.p||x),valueFn:defaultDemandValue}),idx=Math.min(xs.length-1,Math.max(0,cutoff-1)),r=xs[idx];return{cutoff,value:finite(r[key])??0,row:r,source:this.source,sourceCutoff:cutoff,structuralCutoff:cutoff};}
};

const RosterValueService={
  decorate(p,format){const season=finite(p.engineSeasonProjection)??finite(p.sleeperSeasonProjection)??finite(p.seasonScore)??0,weekly=finite(p.weeklyProjection)??finite(p.sleeperWeeklyProjection)??season/17,fp=FormatRegistry.profile(format);return Object.assign({},p,{__fie_mean:fp.chopped||fp.bestBall?weekly:season,__fie_floor:fp.chopped?(finite(p.weeklyFloor)??weekly):season,__fie_ceiling:fp.bestBall?(finite(p.weeklyCeiling)??weekly):season,__fie_utility:finite(p.m5DraftUtility)??finite(p.targetScore)??season,__fie_vor:finite(p.projectedVOR)??0});},
  marginal(player,rosterPool,{format='REDRAFT',rosterPositions=[]}={}){const base=(rosterPool||[]).map(p=>this.decorate(p,format)),candidate=this.decorate(player,format),before=LineupOptimizer.rosterUtility(base,{format,rosterPositions}),after=LineupOptimizer.rosterUtility(base.concat(candidate),{format,rosterPositions});return{gain:after.total-before.total,starterGain:after.starterTotal-before.starterTotal,before,after,method:'exact legal lineup marginal'};}
};

const ContextFingerprint={
  build(extra={}){const st=window.state||{},manifest=window.FIE_BUILD_MANIFEST||{},research=window.FIE_M5?.getCurrentBundle?.()||{};return fnv(stable({leagueId:st.league?.league_id||null,profile:st.league?.__fieProfileFingerprint||null,scoring:st.league?.scoring_settings||{},roster:(st.rosters||[]).map(r=>({id:r.roster_id,players:(r.players||[]).map(String).sort()})),draft:(st.draftIntel?.picks||[]).map(p=>String(p.player_id||p.playerId||'')),season:window.FIESeasonContext?.snapshot?.()||null,projection:{season:st.projectionStatus?.season,seasonCount:st.projectionStatus?.seasonCount,weekly:st.projectionStatus?.weekly,weeklyCount:st.projectionStatus?.weeklyCount},research:research.generated_at||research.snapshot_id||null,model:manifest.draft_model_version||window.FIEModelV9?.VERSION||null,contracts:C.contract_sha256||null,...extra}));}
};

const Diagnostics={buffer:[],max:200,redact(value){let s=String(value??'');s=s.replace(/([?&](?:api_?key|key|token|secret|authorization)=)[^&#\s]*/gi,'$1[REDACTED]');s=s.replace(/(Bearer\s+)[A-Za-z0-9._~+\/-]+/gi,'$1[REDACTED]');return s;},capture(error,context={}){const row={at:new Date().toISOString(),message:this.redact(error?.message||error),stack:this.redact(error?.stack||''),leagueId:window.state?.league?.league_id||null,release:window.FIE_BUILD_MANIFEST?.app_version||window.FIE?.VERSION||null,...context};this.buffer.push(row);if(this.buffer.length>this.max)this.buffer.splice(0,this.buffer.length-this.max);return row;},snapshot(){return this.buffer.slice();}};

window.FIECore={version:'9.3.2-browser-qa',Numeric,FormatRegistry,PositionRegistry,PlayerIdentity:Object.assign(PlayerIdentity,{canonicalPosition:canonicalPos}),LineupOptimizer,LeagueDemandService,ReplacementService,RosterValueService,ContextFingerprint,Diagnostics};
})();

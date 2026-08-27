/* Fantasy Intelligence Engine · Draft Value Finder · V9.3
 * Pre-draft market inefficiency discovery plus live Draft Assistant integration.
 * Uses only league-eligible players, current Sleeper ADP, M5 policy evidence already
 * loaded by the app, and the app's role/depth inputs. It does not bypass M6 governance.
 */
(function(){
'use strict';

const VERSION='9.3.2-VF4';
const BAND_LABELS={
  'ALL':'All ADP',
  'LT100':'Top 100 · Pick Optimizer',
  '100_150':'ADP 100–150',
  '150_200':'ADP 150–200',
  '100_200':'ADP 100–200',
  '200_PLUS':'ADP 200+'
};
function vfPositions(){const slots=window.FIERuntimeContracts?.roster_slots||{},seen=new Set();for(const slot of state.league?.roster_positions||[])for(const p of (slots[String(slot).toUpperCase()]?.positions||[]))seen.add(p);return [...seen].filter(p=>!['OL'].includes(p));}
const VF_CACHE={baseKey:null,baseRows:null,liveKey:null,liveMap:null,builds:0,liveBuilds:0,researchAttempted:false,researchLoading:false,researchError:null};
function vfRosterFingerprint(){
  const rid=Number(document.getElementById('draftRosterPicker')?.value||state.selectedRoster||0);
  const roster=(state.rosters||[]).find(r=>Number(r.roster_id)===rid);
  return `${rid}:${(roster?.players||[]).map(String).sort().join(',')}`;
}
function vfBaseCacheKey(){return window.FIECore?.ContextFingerprint?.current?.({domain:'value-finder-base',eligibility:{allowedExperience:state.leagueRules?.allowedExperience||[],experienceCaps:state.leagueRules?.experienceCaps||{}}})||String(state.league?.league_id||'none');}
function vfLiveCacheKey(){
  const picks=(state.draftIntel?.picks||[]).map(x=>String(x.pick_no||x.pickNo||x.player_id||x.playerId||'')).join(',');
  return [vfBaseCacheKey(),vfRosterFingerprint(),String(state.draftIntel?.draft?.draft_id||'none'),picks].join('|');
}
function vfInvalidate(reason='manual'){VF_CACHE.baseKey=null;VF_CACHE.baseRows=null;VF_CACHE.liveKey=null;VF_CACHE.liveMap=null;VF_CACHE.lastInvalidation=reason;if(reason==='league-changing'||reason==='league-loaded'){VF_CACHE.researchAttempted=false;VF_CACHE.researchLoading=false;VF_CACHE.researchError=null;}}
window.addEventListener?.('fie:league-changing',()=>vfInvalidate('league-changing'));
window.addEventListener?.('fie:league-loaded',()=>vfInvalidate('league-loaded'));
window.addEventListener?.('fie:draft-updated',()=>{VF_CACHE.liveKey=null;VF_CACHE.liveMap=null;});

state.valueFinder={
  band:'100_200',position:'ALL',confidence:'ALL',snap:'ALL',experience:'ALL',
  undervaluedOnly:true,availableOnly:true,limit:10,sortKey:'strength',sortDir:-1,
  top100PlanPick:1,top100NextPick:null,top100ThirdPick:null,top100SortKey:'optimizer',top100SortDir:-1,
  ...(state.valueFinder||{})
};

function vfNow(){return typeof performance!=='undefined'&&typeof performance.now==='function'?performance.now():Date.now();}
function vfNum(v,fallback=null){const n=window.FIECore?.Numeric?.finiteOrNull?.(v);if(n!==null&&n!==undefined)return n;if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return fallback;const z=Number(v);return Number.isFinite(z)?z:fallback;}
function vfClamp(x,lo=0,hi=100){return Math.max(lo,Math.min(hi,Number(x)||0));}
function vfMean(xs){const a=xs.map(x=>vfNum(x,null)).filter(x=>x!==null);return a.length?a.reduce((x,y)=>x+y,0)/a.length:null;}
function vfPct(v,d=1){const n=vfNum(v,null);return n!==null?`${(n*100).toFixed(d)}%`:'—';}
function vfFmt(v,d=1){return Number.isFinite(Number(v))?Number(v).toFixed(d).replace(/\.0$/,''):'—';}
function vfEsc(s){return typeof esc==='function'?esc(s):String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function vfName(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');}
function vfUsableAdp(p){const n=Number(p?.marketADP);return Number.isFinite(n)&&n>0&&n<999?n:null;}
function vfBandMatch(adp,band){if(!Number.isFinite(adp))return false;if(band==='ALL')return true;if(band==='LT100')return adp<100;if(band==='100_150')return adp>=100&&adp<150;if(band==='150_200')return adp>=150&&adp<200;if(band==='100_200')return adp>=100&&adp<200;if(band==='200_PLUS')return adp>=200&&adp<999;return true;}
function vfExperience(p){const y=Number(p?.yearsExp);if(y===0)return'ROOKIE';if(y===1)return'Y2';return'VET';}
function vfEligiblePool(){
  try{const f=window.FIE_DRAFT_V71?.draftFullEligiblePool;if(typeof f==='function'){const xs=f();if(xs?.length)return xs;}}catch{}
  const legal=window.isLeagueEligible||((p)=>p.leagueEligible!==false);
  return PLAYERS.filter(p=>legal(p));
}
function vfDraftedSet(){return window.FIEDraftStateService?.state?.().pickedPlayerIds||new Set((state.draftIntel?.picks||[]).map(x=>String(x.player_id||x.playerId||'')));}
function vfAvailable(p){return !window.FIEDraftStateService?.isDrafted?.(p?.sleeperId)&&!vfDraftedSet().has(String(p?.sleeperId||''));}

function vfM5Research(){return window.FIE_M5?.getResearchBundle?.()||null;}
function vfM5Current(){return window.FIE_M5?.getCurrentBundle?.()||null;}
function vfM5CurrentMap(){
  const m=new Map();
  for(const r of vfM5Current()?.players||[]){
    if(r.sleeper_id)m.set(`s:${r.sleeper_id}`,r);
    if(r.full_name)m.set(`n:${vfName(r.full_name)}`,r);
  }
  return m;
}
function vfM5Row(p,map){return map.get(`s:${p.sleeperId}`)||map.get(`n:${vfName(p.name)}`)||null;}
function vfM5Position(p){
  const raw=String(p.rawPosition||p.depthPosition||p.position||'').toUpperCase();
  const role=String(p.roleProfile||p.role||'').toLowerCase();
  if(['QB','RB','WR','TE','LB'].includes(p.position))return p.position;
  if(p.position==='DL'){
    if(/\b(dt|di|nt)\b/.test(raw)||/interior/.test(role))return'IDL';
    if(/\b(de|edge|olb)\b/.test(raw)||/edge/.test(role))return'EDGE';
    return'IDL';
  }
  if(p.position==='DB'){
    if(/\b(cb)\b/.test(raw)||/corner/.test(role))return'CB';
    if(/\b(s|ss|fs)\b/.test(raw)||/safety|box|deep/.test(role))return'S';
    return'S';
  }
  return p.position;
}
function vfHistoricalEvidenceMap(){
  const m=new Map();
  for(const r of vfM5Research()?.draft_integration?.aggregate||[])m.set(String(r.position),r);
  return m;
}
function vfProfile(){
  const key=typeof activeFormatKey==='function'?activeFormatKey():(vfM5Research()?.league_format||'REDRAFT');
  return vfM5Research()?.format_strategy?.profiles?.[key]||null;
}
function vfPercentileMap(pool,getter){
  const a=pool.map(p=>({p,v:vfNum(getter(p),null)})).filter(x=>x.v!==null).sort((x,y)=>x.v-y.v),m=new Map();
  a.forEach((x,i)=>m.set(String(x.p.sleeperId),a.length<=1?50:100*i/(a.length-1)));
  return m;
}
function vfWeighted(weights,vals){let n=0,d=0,covered=0,total=0;for(const[k,w0]of Object.entries(weights||{})){const w=vfNum(w0,null);if(!(w>0))continue;total+=w;const v=vfNum(vals[k],null);if(v===null)continue;n+=v*w;d+=w;covered+=w;}return{score:d?n/d:null,coverage:total?covered/total:0};}
function vfHealth(p){try{const f=window.FIE_DRAFT_V71?.healthScore;if(typeof f==='function')return f(p);}catch{}const inj=String(p?.injuryStatus||'').toLowerCase();return /out|ir|pup/.test(inj)?25:/questionable|doubtful/.test(inj)?60:90;}
function vfTalent(p){return vfMean([p?.tfgModelScore,p?.pffScore])??50;}
function vfMarketGrade(p){return Number.isFinite(Number(p?.marketEdge))?vfClamp(50+Number(p.marketEdge)*1.5,5,95):50;}
function vfOpportunityResidualGrade(p){const cf=p?.currentResearchFeatures||{},trend=Number(cf.opportunity_change_score);if(window.FIEDecisionService?.researchFeatureMayAffect?.(p,'draft')===true&&Number.isFinite(trend))return vfClamp(50+trend*85,5,95);return 50;}

function vfPolicyContext(pool){
  const currentMap=vfM5CurrentMap();
  const weekly=vfPercentileMap(pool,p=>vfNum(window.FIEProjectionResolver?.week?.(p)?.value,null));
  const floor=vfPercentileMap(pool,p=>vfNum(window.FIEProjectionResolver?.range?.(p)?.low,null));
  const ceiling=vfPercentileMap(pool,p=>vfNum(window.FIEProjectionResolver?.range?.(p)?.high,null));
  return{
    currentMap,
    season:vfPercentileMap(pool,p=>vfNum(p.engineSeasonProjection,null)??vfNum(p.sleeperSeasonProjection,null)),
    vor:vfPercentileMap(pool,p=>vfNum(p.projectedVOR,null)),
    weekly,floor,ceiling
  };
}
function vfPolicyScore(p,ctx,profile){
  const id=String(p.sleeperId),r=vfM5Row(p,ctx.currentMap);
  const w=profile?.draft_weights;
  if(!w){const fallback=vfNum(p.seasonScore,vfNum(window.seasonDraftScoreFor?.(p),50));return{score:fallback,coverage:0.55,row:r};}
  const wv=ctx.weekly.get(id)??50,fv=ctx.floor.get(id)??50,cv=ctx.ceiling.get(id)??50;
  const youngRaw=vfNum(r?.young_role_probability,null),spikeRaw=vfNum(r?.spike_probability,null),bustRaw=vfNum(r?.bust_probability,null);
  const young=youngRaw!==null?vfClamp(youngRaw*100):vfNum(p.futureOpportunity,50);
  const spike=spikeRaw!==null?vfClamp(spikeRaw*100):cv;
  const bust=bustRaw!==null?vfClamp(bustRaw,0,1):null;
  const vals={
    season_projection:ctx.season.get(id)??50,
    vor:ctx.vor.get(id)??50,
    current_role:vfOpportunityResidualGrade(p),
    weekly_shape:vfMean([wv,fv,cv])??50,
    market_edge:50, // market is excluded from canonical/player-quality inputs; compared explicitly below
    future_role:young,
    age_curve:vfNum(p.ageCurveScore,50),
    talent:vfTalent(p),
    spike,
    depth_fit:vfNum(p.replacementScore,50),
    floor:bust===null?fv:(1-bust)*100,
    early_week:wv,
    health:vfHealth(p)
  };
  const z=vfWeighted(w,vals);
  return{score:Number.isFinite(z.score)?Math.round(z.score*10)/10:vfNum(p.seasonScore,50),coverage:z.coverage,row:r};
}

function vfSnapPath(p){
  const cur=vfNum(p.currentOpportunity,35),order=Number(p.depthOrder),txt=`${p.role||''} ${p.path||''} ${p.tier||''}`.toLowerCase();
  let depth=38;
  if(order===1)depth=96;else if(order===2)depth=80;else if(order===3)depth=62;else if(Number.isFinite(order)&&order>=4)depth=40;
  if(/already starting|starter|starting mix|atop|first[- ]team/.test(txt))depth=Math.max(depth,94);
  else if(/meaningful rotation|regular snaps|rotation|rb2|wr2|te2|primary backup/.test(txt))depth=Math.max(depth,78);
  else if(/direct backup|one injury|one role change|role win/.test(txt))depth=Math.max(depth,62);
  let score=cur*.68+depth*.32;
  if(String(p.opportunitySource||'').includes('Curated'))score+=4;
  const inj=String(p.injuryStatus||'').toLowerCase();if(/out|ir|pup/.test(inj))score-=30;else if(/doubtful/.test(inj))score-=15;
  score=vfClamp(score);
  const tier=score>=88?'STARTER':score>=75?'CLEAR':score>=60?'DIRECT':score>=45?'SPECULATIVE':'LONGSHOT';
  return{score:Math.round(score),tier,clear:score>=75,label:score>=88?'Starter / major role':score>=75?'Clear rotation / workload path':score>=60?'Direct backup / one-step path':score>=45?'Needs role win':'Long-shot path'};
}

function vfBuildRows(){
  const cacheKey=vfBaseCacheKey();if(VF_CACHE.baseKey===cacheKey&&VF_CACHE.baseRows)return VF_CACHE.baseRows;
  const started=vfNow();
  const pool=vfEligiblePool(),profile=vfProfile(),ctx=vfPolicyContext(pool),hist=vfHistoricalEvidenceMap();
  const base=pool.map(p=>{const policy=vfPolicyScore(p,ctx,profile),snap=vfSnapPath(p);return{p,policy,snap,adp:vfUsableAdp(p)};});
  // Canonical FIE ranks come from the one roster-neutral Draft Base Value service.
  // Value Finder may build a discovery score, but it must never redefine "FIE Pos Rank".
  const canonicalRows=window.FIEDraftBaseValueService?.rows?.()||[],canonical=new Map(canonicalRows.map(x=>[String(x.id),x]));
  const byPos=new Map();for(const x of base){const c=canonical.get(String(x.p.sleeperId||x.p.name));x.canonical=c||null;x.fiePosRank=c?.positionRank??null;x.fieLeagueRank=c?.overallRank??null;x.canonicalValue=c?.baseValue??x.policy.score;x.canonicalTier=c?.tier??null;if(!byPos.has(x.p.position))byPos.set(x.p.position,[]);byPos.get(x.p.position).push(x);}
  for(const rows of byPos.values()){
    const covered=rows.filter(x=>x.adp!==null);
    [...covered].sort((a,b)=>a.adp-b.adp).forEach((x,i)=>x.marketPosRank=i+1);
    for(const x of rows)x.posEdge=Number.isFinite(x.marketPosRank)&&Number.isFinite(x.fiePosRank)?x.marketPosRank-x.fiePosRank:null;
  }
  // Overall price comparison uses an ADP-covered comparable rank, while display retains
  // the canonical full-pool FIE League Rank.
  const overallCovered=base.filter(x=>x.adp!==null);
  [...overallCovered].sort((a,b)=>a.adp-b.adp).forEach((x,i)=>x.marketOverallRank=i+1);
  [...overallCovered].sort((a,b)=>(b.canonicalValue??-Infinity)-(a.canonicalValue??-Infinity)).forEach((x,i)=>x.fieOverallRank=i+1);
  for(const x of base)x.overallEdge=Number.isFinite(x.marketOverallRank)&&Number.isFinite(x.fieOverallRank)?x.marketOverallRank-x.fieOverallRank:null;
  for(const x of base){
    const h=hist.get(vfM5Position(x.p))||null,improve=vfNum(h?.mean_mae_improvement_vs_baseline,0),validated=/validated/i.test(String(h?.status||''));
    const edgeScore=x.posEdge===null?50:vfClamp(50+x.posEdge*2.2);
    const histScore=vfClamp(50+improve*100*(validated?1.25:.55));
    const fit=vfNum(x.p.leagueFit,50);
    const deep=x.adp!==null&&x.adp>=200;
    const canonicalScore=vfNum(x.canonicalValue,x.policy.score);
    const strength=deep?
      canonicalScore*.25+edgeScore*.20+x.snap.score*.35+histScore*.15+fit*.05:
      canonicalScore*.36+edgeScore*.26+x.snap.score*.14+histScore*.14+fit*.10;
    x.hist=h;x.histImprovement=improve;x.histValidated=validated;x.strength=Math.round(strength*10)/10;
    const meaningful=x.posEdge!==null&&x.posEdge>=4 || canonicalScore>=72&&x.snap.score>=75 || x.snap.score>=88&&canonicalScore>=62;
    x.meaningful=meaningful;
    if(x.snap.score>=85&&validated&&(meaningful||x.strength>=72))x.confidence='HIGH';
    else if(x.snap.score>=62&&(meaningful||x.strength>=62))x.confidence='MEDIUM';
    else x.confidence='LOW';
    const edge=Math.max(0,x.posEdge||0),lead=deep?vfClamp(15+(x.snap.score-60)*.45+edge*.45,12,42):vfClamp(6+edge*.45+(x.confidence==='HIGH'?6:x.confidence==='MEDIUM'?2:0),5,22);
    x.targetStart=x.adp===null?null:Math.max(1,Math.round(x.adp-lead));x.targetEnd=x.adp===null?null:Math.round(x.adp);
    x.window=x.targetStart===null?'—':`${x.targetStart}–${x.targetEnd}`;
  }
  VF_CACHE.baseKey=cacheKey;VF_CACHE.baseRows=base;VF_CACHE.builds++;VF_CACHE.lastBaseMs=vfNow()-started;
  return base;
}

function vfLiveDraftMap(){
  try{
    if(!state.draftIntel?.draft)return new Map();
    const cacheKey=vfLiveCacheKey();if(VF_CACHE.liveKey===cacheKey&&VF_CACHE.liveMap)return VF_CACHE.liveMap;
    const rid=Number($('draftRosterPicker')?.value||state.selectedRoster);
    const rows=window.FIEDecisionService?.draftRows?.(rid)||[];
    const out=new Map(rows.map(x=>[String(window.FIECore?.PlayerIdentity?.id?.(x.p)||x.p?.sleeperId||''),x]));VF_CACHE.liveKey=cacheKey;VF_CACHE.liveMap=out;VF_CACHE.liveBuilds++;return out;
  }catch{return new Map();}
}
function vfTargetState(x,live=null){
  if(!vfAvailable(x.p))return'DRAFTED';
  if(!state.draftIntel?.draft)return'WATCH';
  const cur=(state.draftIntel.picks||[]).length+1;
  if(live?.survive!==null&&live?.survive!==undefined&&live.survive<28&&x.strength>=64)return'TAKE NOW';
  if(x.targetEnd!==null&&cur>=x.targetEnd&&x.strength>=58)return'TAKE NOW';
  if(x.targetStart!==null&&cur>=x.targetStart)return'TARGET';
  const next=live?.nextOwn?.pickNo;
  if(Number.isFinite(Number(next))&&x.targetStart!==null&&Number(next)<=x.targetStart)return'WAIT';
  return'WATCH';
}
function vfWhy(x){
  const bits=[];
  if((x.posEdge||0)>=4)bits.push(`FIE ${x.p.position}${x.fiePosRank} vs market ${x.p.position}${x.marketPosRank} (+${x.posEdge})`);
  if(x.snap.score>=75)bits.push(x.snap.label);
  else if(x.snap.score>=60)bits.push('direct workload path');
  if(Number.isFinite(x.histImprovement)&&x.histImprovement>0)bits.push(`${vfPct(x.histImprovement)} historical ${vfM5Position(x.p)} draft improvement${x.histValidated?' · validated':' · diagnostic'}`);
  if(Number.isFinite(Number(x.p.currentOpportunity))&&Number(x.p.currentOpportunity)>=75)bits.push(`role ${Math.round(Number(x.p.currentOpportunity))}/100`);
  if(Number.isFinite(Number(x.p.futureOpportunity))&&Number(x.p.futureOpportunity)>=80)bits.push(`future role ${Math.round(Number(x.p.futureOpportunity))}/100`);
  if(Number.isFinite(Number(x.p.leagueFit))&&Number(x.p.leagueFit)>=65)bits.push(`league fit ${Math.round(Number(x.p.leagueFit))}/100`);
  return bits.slice(0,4).join(' · ')||'Late market cost with a usable league-specific profile.';
}
function vfEvidenceChips(x){
  const chips=[];
  chips.push(`<span class="vf-chip ${x.snap.score>=75?'good':x.snap.score>=60?'mid':'low'}">Snap ${x.snap.score}</span>`);
  if(x.posEdge!==null)chips.push(`<span class="vf-chip ${x.posEdge>=4?'good':x.posEdge<0?'low':'mid'}">${x.posEdge>=0?'+':''}${x.posEdge} pos</span>`);
  chips.push(`<span class="vf-chip ${x.histValidated?'good':'mid'}">${x.histValidated?'Validated':'Diagnostic'} ${vfM5Position(x.p)}</span>`);
  if(x.policy.coverage>=.75)chips.push(`<span class="vf-chip good">Policy ${Math.round(x.policy.coverage*100)}%</span>`);
  else chips.push(`<span class="vf-chip mid">Policy ${Math.round(x.policy.coverage*100)}%</span>`);
  return chips.join('');
}
function vfStateClass(s){return s==='TAKE NOW'?'take':s==='TARGET'?'target':s==='WAIT'?'wait':s==='DRAFTED'?'drafted':s==='PASS AT ADP'?'drafted':'watch';}


function vfEvidenceScore(x){
  const histBase=x.histValidated?70:44,hist=vfClamp(histBase+Math.max(0,Number(x.histImprovement)||0)*115),coverage=vfClamp((Number(x.policy?.coverage)||0)*100);
  return Math.round((hist*.65+coverage*.35)*10)/10;
}
function vfTop100DraftContext(liveMap){
  const f=state.valueFinder,teams=Number(state.league?.total_rosters)||Number(state.rosters?.length)||12;
  const liveDraft=!!state.draftIntel?.draft&&!/complete/i.test(String(state.draftIntel?.draft?.status||''));
  if(liveDraft&&liveMap?.size){
    const first=liveMap.values().next().value,current=(state.draftIntel.picks||[]).length+1;
    const plan=Number(first?.nextOwn?.pickNo)||current,next=Number(first?.following?.pickNo)||null;
    let third=null;
    try{const rid=Number($('draftRosterPicker')?.value||state.selectedRoster),z=next&&typeof subsequentPickForRoster==='function'?subsequentPickForRoster(rid,next):null;third=Number(z?.pickNo)||null;}catch{}
    return{live:true,currentPick:current,planPick:plan,nextPick:next,thirdPick:third,teams};
  }
  const plan=Math.max(1,Number(f.top100PlanPick)||1),next=Math.max(plan+1,Number(f.top100NextPick)||plan+teams),third=Math.max(next+1,Number(f.top100ThirdPick)||next+teams);
  return{live:false,currentPick:plan,planPick:plan,nextPick:next,thirdPick:third,teams};
}
function vfSurvivalTo(x,targetPick,fromPick,liveX=null,primary=false,cache=null){
  if(!Number.isFinite(Number(x?.adp))||!Number.isFinite(Number(targetPick)))return null;
  if(primary&&liveX?.survive!==null&&liveX?.survive!==undefined&&Number.isFinite(Number(liveX.survive)))return Number(liveX.survive);
  const key=`${Math.round(Number(x.adp)*10)/10}|${targetPick}|${fromPick}`;
  if(cache?.has(key))return cache.get(key);
  let out=null;
  try{const fn=window.FIE89?.survivalProbability||window.survivalProbability;if(typeof fn==='function')out=fn(Number(x.adp),Number(targetPick),Number(fromPick));}catch{}
  if(!Number.isFinite(Number(out))){const sigma=Math.max(7,Math.min(18,7+Math.max(1,targetPick-fromPick)*.25)),z=(Number(x.adp)-Number(targetPick))/sigma;out=Math.round(vfClamp(100/(1+Math.exp(-z)),1,99));}
  out=Math.round(vfClamp(out,1,99));if(cache)cache.set(key,out);return out;
}
function vfTop100Rows(opts={}){
  const base=opts.baseRows||vfBuildRows(),liveMap=opts.liveMap||vfLiveDraftMap(),ctx=vfTop100DraftContext(liveMap),cache=new Map();
  const available=base.filter(x=>x.adp!==null&&vfAvailable(x.p));
  const top=available.filter(x=>x.adp<100);
  const proxyScore=y=>{const evidence=vfEvidenceScore(y),edgeScore=y.overallEdge===null?50:vfClamp(50+y.overallEdge*2),roster=vfNum(liveMap.get(String(y.p.sleeperId))?.components?.roster,vfNum(y.p.leagueFit,50)),vor=vfClamp(50+(vfNum(y.p.projectedVOR,0))*1.8);return y.policy.score*.48+roster*.17+evidence*.15+edgeScore*.12+vor*.08;};
  for(const x of top){
    x.live=liveMap.get(String(x.p.sleeperId))||null;x.evidenceScore=vfEvidenceScore(x);x.rosterFit=vfNum(x.live?.components?.roster,vfNum(x.p.leagueFit,50));x.vorScore=vfClamp(50+vfNum(x.p.projectedVOR,0)*1.8);x.edgeScore=x.overallEdge===null?50:vfClamp(50+x.overallEdge*2);x.basePickScore=Math.round((x.policy.score*.42+x.rosterFit*.18+x.evidenceScore*.15+x.edgeScore*.15+x.vorScore*.10)*10)/10;
    x.survive=vfSurvivalTo(x,ctx.nextPick,ctx.planPick,x.live,true,cache);x.opponentPressure=vfNum(x.live?.managerPressure?.adj,0);x.pressureN=vfNum(x.live?.managerPressure?.n,0);
  }
  function expectedReplacement(x,target){
    const same=available.filter(y=>y!==x&&y.p.position===x.p.position),likely=same.map(y=>({y,s:vfSurvivalTo(y,target,ctx.planPick,liveMap.get(String(y.p.sleeperId)),target===ctx.nextPick,cache)})).filter(z=>Number(z.s)>=45).sort((a,b)=>proxyScore(b.y)-proxyScore(a.y));
    if(likely.length)return likely[0].y;
    return same.filter(y=>y.policy.score<=x.policy.score).sort((a,b)=>b.policy.score-a.policy.score)[0]||same.sort((a,b)=>b.policy.score-a.policy.score)[0]||null;
  }
  function bestFuture(target,exclude=new Set()){
    const cand=available.filter(y=>!exclude.has(String(y.p.sleeperId))).map(y=>({y,s:vfSurvivalTo(y,target,ctx.planPick,liveMap.get(String(y.p.sleeperId)),target===ctx.nextPick,cache)})).filter(z=>Number(z.s)>=48).sort((a,b)=>proxyScore(b.y)-proxyScore(a.y));return cand[0]?.y||null;
  }
  for(const x of top){
    const rep=expectedReplacement(x,ctx.nextPick),drop=rep?Math.max(0,x.policy.score-rep.policy.score):0;
    const sameTier=available.filter(y=>y!==x&&y.p.position===x.p.position&&Math.abs(y.policy.score-x.policy.score)<=2.5&&vfSurvivalTo(y,ctx.nextPick,ctx.planPick,liveMap.get(String(y.p.sleeperId)),true,cache)>=35).length;
    x.replacement=rep;x.replacementDrop=Math.round(drop*10)/10;x.sameTierRemaining=sameTier;x.tierRisk=Math.round(vfClamp(drop*12+(sameTier===0?25:sameTier===1?14:0)+(x.vorScore>=75?8:0)));
    const disc=Number(x.adp)-Number(x.fieLeagueRank),rawCapture=disc>0?(Number(ctx.planPick)-Number(x.fieLeagueRank))/disc:null;
    x.valueCapture=rawCapture===null?null:Math.round(vfClamp(rawCapture*100,0,100));
    x.reachCost=Math.round(Math.max(0,Number(x.adp)-Number(ctx.planPick))*((Number(x.survive)||0)/100)*10)/10;
    x.waitCost=Math.round(drop*(1-(Number(x.survive)||0)/100)*10)/10;
  }
  const rankedCurrent=[...top].sort((a,b)=>b.basePickScore-a.basePickScore);
  for(const x of top){
    const excl=new Set([String(x.p.sleeperId)]),n1=ctx.nextPick?bestFuture(ctx.nextPick,excl):null;if(n1)excl.add(String(n1.p.sleeperId));const n2=ctx.thirdPick?bestFuture(ctx.thirdPick,excl):null;
    const takePath=x.basePickScore+(n1?proxyScore(n1)*.72:0)+(n2?proxyScore(n2)*.52:0);
    const alt=rankedCurrent.find(y=>y!==x)||null,rep=x.replacement,s=(Number(x.survive)||0)/100,futureX=s*x.basePickScore+(1-s)*(rep?proxyScore(rep):x.basePickScore*.72),waitPath=(alt?alt.basePickScore:0)+futureX*.72+(n2?proxyScore(n2)*.52:0);
    x.pathTake=Math.round(takePath*10)/10;x.pathWait=Math.round(waitPath*10)/10;x.pathDelta=Math.round((takePath-waitPath)*10)/10;
    const labels=[];if((x.overallEdge||0)>=8)labels.push('MARKET VALUE');if(x.tierRisk>=60||x.vorScore>=78)labels.push('STRUCTURAL');if(vfNum(x.p.leagueFit,50)>=70)labels.push('FORMAT');if(x.rosterFit>=72)labels.push('ROSTER');if(x.tierRisk>=65)labels.push('TIER');if((x.survive||0)>=70&&x.reachCost>=4)labels.push('WAIT VALUE');x.opportunityTypes=labels.slice(0,3);
    if((x.overallEdge||0)<=-10&&x.policy.score<65&&x.tierRisk<55)x.optimizerAction='PASS AT ADP';
    else if(x.pathDelta>=4||(x.survive!==null&&x.survive<30&&((x.overallEdge||0)>=0||x.tierRisk>=55))||(x.tierRisk>=75&&(x.survive||100)<52))x.optimizerAction='TAKE NOW';
    else if(x.pathDelta>=1||((x.survive||100)<58&&(x.overallEdge||0)>=5)||((x.valueCapture||0)>=65&&(x.overallEdge||0)>=5))x.optimizerAction='TARGET';
    else if((x.survive||0)>=70&&x.reachCost>=4&&x.tierRisk<65)x.optimizerAction='WAIT';
    else x.optimizerAction='CONSIDER';
    x.optimizerScore=Math.round((x.basePickScore+x.tierRisk*.10+Math.max(-10,Math.min(10,x.pathDelta))*1.2-x.reachCost*.20)*10)/10;
  }
  top.sort((a,b)=>b.optimizerScore-a.optimizerScore);
  top.context=ctx;return top;
}
function vfRiskClass(n){return n>=65?'vf-risk-high':n>=35?'vf-risk-mid':'vf-risk-low';}
function vfTop100ControlsHTML(ctx){
  if(ctx.live)return `<div class="notice" style="margin-top:10px"><b>Live pick context:</b> optimizing your upcoming pick <b>#${ctx.planPick}</b> against following own picks ${ctx.nextPick?`#${ctx.nextPick}`:'—'} and ${ctx.thirdPick?`#${ctx.thirdPick}`:'—'}. Opponent-adjusted survival uses saved draft tendencies where available.</div>`;
  return `<div class="notice" style="margin-top:10px"><b>Pre-draft planning mode:</b> enter the pick you are optimizing and your following selections. Live Sleeper draft state will replace these automatically once a draft is active.<div class="vf-plan-inputs"><label><span class="filter-label">Planning pick</span><input id="vfPlanPick" type="number" min="1" value="${ctx.planPick}"></label><label><span class="filter-label">Following own pick</span><input id="vfNextPick" type="number" min="2" value="${ctx.nextPick}"></label><label><span class="filter-label">Third own pick</span><input id="vfThirdPick" type="number" min="3" value="${ctx.thirdPick}"></label></div></div>`;
}
function vfTop100RowHTML(x,i){
  const fiePos=x.fiePosRank?`${x.p.position}${x.fiePosRank}`:'—',marketPos=x.marketPosRank?`${x.p.position}${x.marketPosRank}`:'—';
  const edge=x.posEdge===null?'—':`${x.posEdge>=0?'+':''}${x.posEdge}`,cap=x.valueCapture===null?'—':`${x.valueCapture}%`,window=x.window&&x.window!=='—'?x.window:'market dependent';
  return `<tr data-vf-id="${vfEsc(x.p.sleeperId||x.p.name)}"><td><b>${i+1}</b></td><td><div class="vf-player">${vfEsc(x.p.name)}</div><div class="muted">${vfEsc(x.p.position)} · ${vfEsc(x.p.team)}</div></td><td><b>${fiePos}</b></td><td><b>${marketPos}</b></td><td class="${(x.posEdge||0)>=4?'vf-rankedge':''}"><b>${edge}</b><br><span class="muted">positional spots</span></td><td><b>${vfFmt(x.adp,0)}</b></td><td><b>${cap}</b><br><span class="muted">reach cost ${vfFmt(x.reachCost)} picks</span></td><td><b>${vfFmt(x.waitCost)}</b><br><span class="muted">Estimate · policy cost</span></td><td><span class="vf-state ${vfStateClass(x.optimizerAction)}">${vfEsc(x.optimizerAction)}</span><div class="vf-draft-mini">window ${vfEsc(window)} · next-pick ${x.survive??'—'}${x.survive!==null?'%':''} Estimate</div></td></tr>`;
}
function renderTop100Optimizer(){
  const box=$('valueFinderSummary'),status=$('valueFinderStatus');if(!box||!status)return;
  const all=vfTop100Rows(),ctx=all.context||vfTop100DraftContext(new Map()),f=state.valueFinder;
  let rows=all;if(f.position!=='ALL')rows=rows.filter(x=>x.p.position===f.position);if(f.experience!=='ALL')rows=rows.filter(x=>vfExperience(x.p)===f.experience);if(f.confidence!=='ALL')rows=rows.filter(x=>x.confidence===f.confidence);if(f.availableOnly)rows=rows.filter(x=>vfAvailable(x.p));if(f.undervaluedOnly)rows=rows.filter(x=>(x.overallEdge||0)>=0||x.optimizerAction==='TAKE NOW'||x.optimizerAction==='TARGET');
  const key=f.top100SortKey||'optimizer',dir=Number(f.top100SortDir)||-1,get=x=>key==='adp'?x.adp:key==='edge'?x.overallEdge:key==='tier'?x.tierRisk:key==='survive'?x.survive:key==='capture'?x.valueCapture:key==='path'?x.pathDelta:key==='player'?x.p.name:x.optimizerScore;
  rows=[...rows].sort((a,b)=>{const av=get(a),bv=get(b);if(typeof av==='string')return av.localeCompare(String(bv))*dir;if(av===null||av===undefined)return 1;if(bv===null||bv===undefined)return-1;return(Number(av)-Number(bv))*dir;});
  const shown=rows.slice(0,Number(f.limit)||10),take=rows.filter(x=>x.optimizerAction==='TAKE NOW').length,wait=rows.filter(x=>x.optimizerAction==='WAIT').length,cliffs=rows.filter(x=>x.tierRisk>=65).length,avgCap=Math.round(vfMean(rows.map(x=>x.valueCapture).filter(Number.isFinite))||0);
  status.innerHTML=`<b>${vfEsc(state.league.name||state.league.league_id)}</b> · Top 100 Pick Optimizer · planning pick #${ctx.planPick} · ${rows.length} available candidates. This mode optimizes <b>price and timing</b> around the canonical FIE player rank. ${vfEsc(window.FIEDraftStateService?.label?.()||'Draft state unavailable')}.`;
  const rowHtml=shown.map(vfTop100RowHTML).join('')||'<tr><td colspan="9"><div class="empty">No Top-100 candidates meet the current filters.</div></td></tr>';
  box.innerHTML=`${vfControlsHTML()}${vfTop100ControlsHTML(ctx)}<div class="vf-opt-grid"><div class="vf-opt-card"><span class="filter-label">TAKE NOW</span><div class="big">${take}</div><div class="tiny">waiting has meaningful EV cost</div></div><div class="vf-opt-card"><span class="filter-label">WAIT</span><div class="big">${wait}</div><div class="tiny">good player, price can improve</div></div><div class="vf-opt-card"><span class="filter-label">Tier cliffs</span><div class="big">${cliffs}</div><div class="tiny">Tier Drop Risk 65+</div></div><div class="vf-opt-card"><span class="filter-label">Avg value captured</span><div class="big">${avgCap}%</div><div class="tiny">of available FIE→market discount</div></div><div class="vf-opt-card"><span class="filter-label">Path horizon</span><div class="big">3 picks</div><div class="tiny">take-now vs wait proxy</div></div></div><div class="scroll" style="max-height:62vh"><table class="vf-table"><thead><tr><th>#</th><th data-vf100-sort="player">Player</th><th>FIE Pos</th><th>Market Pos</th><th data-vf100-sort="edge">Pos Edge</th><th data-vf100-sort="adp">ADP</th><th data-vf100-sort="capture">Value Capture</th><th>Wait Cost</th><th data-vf100-sort="optimizer">Action / Target window</th></tr></thead><tbody>${rowHtml}</tbody></table></div><div class="notice" style="margin-top:10px"><b>Top-100 logic:</b> this is a timing surface, not a second Draft Board. Positional FIE-vs-market disagreement is shown directly; Value Capture and Wait Cost determine whether a good player is also worth taking now. Next-pick availability, wait cost and the three-pick planning path are explicitly <b>Estimate</b> signals until calibrated.</div>`;
  bindValueFinderControls();bindTop100Controls();box.querySelectorAll('tr[data-vf-id]').forEach(tr=>tr.onclick=e=>{if(e.target.closest('select,input,button'))return;window.openDrawer?.(tr.dataset.vfId);});box.querySelectorAll('th[data-vf100-sort]').forEach(th=>{th.style.cursor='pointer';th.onclick=()=>{const k=th.dataset.vf100Sort;f.top100SortDir=f.top100SortKey===k?-f.top100SortDir:(k==='player'?1:-1);f.top100SortKey=k;renderTop100Optimizer();};});
}
function bindTop100Controls(){const f=state.valueFinder,bind=(id,key)=>{const el=$(id);if(el)el.onchange=()=>{f[key]=Math.max(1,Number(el.value)||1);renderTop100Optimizer();};};bind('vfPlanPick','top100PlanPick');bind('vfNextPick','top100NextPick');bind('vfThirdPick','top100ThirdPick');}

function vfFilteredRows(baseRows=null){
  const f=state.valueFinder,live=vfLiveDraftMap();
  let rows=(baseRows||vfBuildRows()).filter(x=>vfBandMatch(x.adp,f.band));
  if(f.position!=='ALL')rows=rows.filter(x=>x.p.position===f.position);
  if(f.experience!=='ALL')rows=rows.filter(x=>vfExperience(x.p)===f.experience);
  if(f.snap==='CLEAR')rows=rows.filter(x=>x.snap.score>=75);else if(f.snap==='STARTER')rows=rows.filter(x=>x.snap.score>=88);
  if(f.confidence!=='ALL')rows=rows.filter(x=>x.confidence===f.confidence);
  if(f.availableOnly)rows=rows.filter(x=>vfAvailable(x.p));
  if(f.undervaluedOnly)rows=rows.filter(x=>x.meaningful&&x.strength>=58&&(f.band!=='200_PLUS'||x.snap.score>=60));
  rows.forEach(x=>{x.live=live.get(String(x.p.sleeperId))||null;x.state=vfTargetState(x,x.live);});
  const k=f.sortKey||'strength',d=Number(f.sortDir)||-1;
  const get=x=>k==='adp'?x.adp:k==='edge'?x.posEdge:k==='snap'?x.snap.score:k==='policy'?x.policy.score:k==='player'?x.p.name:x.strength;
  rows.sort((a,b)=>{const av=get(a),bv=get(b);if(typeof av==='string')return av.localeCompare(String(bv))*d;if(av===null||av===undefined)return 1;if(bv===null||bv===undefined)return-1;return (Number(av)-Number(bv))*d;});
  return rows;
}

function vfInjectStyles(){if(document.getElementById('vfStyles'))return;const s=document.createElement('style');s.id='vfStyles';s.textContent=`
.value-finder-toolbar{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:9px;margin-top:12px;align-items:end}.value-finder-toolbar label{display:block}.vf-check{display:flex;gap:7px;align-items:center;padding:9px 10px;border:1px solid var(--line);border-radius:10px;background:#091425;min-height:39px}.vf-check input{accent-color:#60a5fa}.vf-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:12px 0}.vf-card{border:1px solid #253b57;background:#0a1627;border-radius:12px;padding:12px}.vf-card .big{font-size:22px;font-weight:900}.vf-card .tiny{color:var(--muted);font-size:10px;margin-top:3px}.vf-table{width:100%;border-collapse:collapse;font-size:11px}.vf-table th{position:sticky;top:0;background:#10213a;color:#bcd0e8;text-align:left;padding:8px;border-bottom:1px solid #29415e;white-space:nowrap;z-index:1}.vf-table td{padding:8px;border-bottom:1px solid #1b2e46;vertical-align:top}.vf-player{font-weight:900;font-size:12px}.vf-chip{display:inline-flex;border:1px solid #35506f;border-radius:999px;padding:2px 6px;margin:1px 3px 1px 0;font-size:9px;background:#0d1c30;color:#c8d7e8}.vf-chip.good{border-color:#236a4d;color:#86efac}.vf-chip.mid{border-color:#786522;color:#fde68a}.vf-chip.low{border-color:#743647;color:#fda4af}.vf-state{display:inline-flex;border-radius:999px;padding:4px 8px;font-weight:950;font-size:9px;letter-spacing:.03em}.vf-state.take{background:#5b1d2d;color:#fecdd3}.vf-state.target{background:#164e3b;color:#bbf7d0}.vf-state.wait{background:#4b3d12;color:#fde68a}.vf-state.watch{background:#17365d;color:#bfdbfe}.vf-state.drafted{background:#303744;color:#cbd5e1}.vf-why{max-width:340px;line-height:1.4;color:#c3d0df}.vf-rankedge{font-weight:900;color:#86efac}.vf-draft-mini{font-size:9px;color:var(--muted);line-height:1.35}.vf-da-cell{min-width:125px}.vf-da-plan{min-width:100px}.vf-warning{color:#fde68a}.vf-source{font-size:9px;color:var(--muted)}.vf-opt-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin:12px 0}.vf-opt-card{border:1px solid #2b4667;background:#0a1729;border-radius:12px;padding:10px}.vf-opt-card .big{font-size:19px;font-weight:950}.vf-risk-high{color:#fda4af;font-weight:900}.vf-risk-mid{color:#fde68a;font-weight:900}.vf-risk-low{color:#86efac;font-weight:900}.vf-type{display:inline-flex;border:1px solid #3c5878;border-radius:999px;padding:2px 6px;margin:1px 2px;font-size:8px;font-weight:800}.vf-type.take{border-color:#8b3047;color:#fecdd3}.vf-type.wait{border-color:#786522;color:#fde68a}.vf-type.value{border-color:#236a4d;color:#86efac}.vf-plan-inputs{display:grid;grid-template-columns:repeat(3,minmax(100px,1fr));gap:8px;max-width:560px;margin-top:9px}.vf-plan-inputs input{width:100%;background:#091425;border:1px solid #2a4263;color:var(--text);border-radius:9px;padding:8px}.vf-path-positive{color:#86efac;font-weight:900}.vf-path-negative{color:#fda4af;font-weight:900}
@media(max-width:1100px){.value-finder-toolbar{grid-template-columns:repeat(3,minmax(120px,1fr))}.vf-summary{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.vf-opt-grid{grid-template-columns:1fr 1fr}.vf-plan-inputs{grid-template-columns:1fr}.value-finder-toolbar{grid-template-columns:1fr 1fr}.vf-summary{grid-template-columns:1fr 1fr}.vf-table{font-size:10px}.vf-table th,.vf-table td{padding:6px}.vf-hide-mobile{display:none}}
`;document.head.appendChild(s);}

function vfControlsHTML(){const f=state.valueFinder;return`<div class="value-finder-toolbar">
<label><span class="filter-label">Market range</span><select id="vfBand">${Object.entries(BAND_LABELS).map(([v,l])=>`<option value="${v}" ${f.band===v?'selected':''}>${l}</option>`).join('')}</select></label>
<label><span class="filter-label">Position</span><select id="vfPosition"><option value="ALL">All positions</option>${vfPositions().map(p=>`<option value="${p}" ${f.position===p?'selected':''}>${p}</option>`).join('')}</select></label>
<label><span class="filter-label">Snap path</span><select id="vfSnap"><option value="ALL" ${f.snap==='ALL'?'selected':''}>All paths</option><option value="CLEAR" ${f.snap==='CLEAR'?'selected':''}>Clear path 75+</option><option value="STARTER" ${f.snap==='STARTER'?'selected':''}>Starter / major 88+</option></select></label>
<label><span class="filter-label">Experience</span><select id="vfExperience"><option value="ALL" ${f.experience==='ALL'?'selected':''}>All</option><option value="ROOKIE" ${f.experience==='ROOKIE'?'selected':''}>Rookies</option><option value="Y2" ${f.experience==='Y2'?'selected':''}>Year 2</option><option value="VET" ${f.experience==='VET'?'selected':''}>Veterans</option></select></label>
<label><span class="filter-label">Confidence</span><select id="vfConfidence"><option value="ALL" ${f.confidence==='ALL'?'selected':''}>All</option><option value="HIGH" ${f.confidence==='HIGH'?'selected':''}>High only</option><option value="MEDIUM" ${f.confidence==='MEDIUM'?'selected':''}>Medium only</option></select></label>
<label><span class="filter-label">Show</span><select id="vfLimit"><option value="10" ${f.limit===10?'selected':''}>Top 10</option><option value="20" ${f.limit===20?'selected':''}>Top 20</option><option value="50" ${f.limit===50?'selected':''}>Top 50</option><option value="999" ${f.limit===999?'selected':''}>All</option></select></label>
<div class="vf-check"><input type="checkbox" id="vfUnder" ${f.undervaluedOnly?'checked':''}><label for="vfUnder">FIE undervalued only</label></div>
<div class="vf-check"><input type="checkbox" id="vfAvailable" ${f.availableOnly?'checked':''}><label for="vfAvailable">Undrafted only</label></div>
</div>`;}


function vfRowHTML(x,i){
  const fieRank=x.fiePosRank?`${x.p.position}${x.fiePosRank}`:'—',marketRank=x.marketPosRank?`${x.p.position}${x.marketPosRank}`:'—';
  const edge=x.posEdge===null?'—':`${x.posEdge>=0?'+':''}${x.posEdge}`;
  const deep=state.valueFinder.band==='200_PLUS';
  const evidence=`${x.confidence} · ${x.histValidated?'Validated':'Diagnostic'} ${vfM5Position(x.p)} · strength ${vfFmt(x.strength)}`;
  return `<tr data-vf-id="${vfEsc(x.p.sleeperId||x.p.name)}"><td><b>${i+1}</b></td><td><div class="vf-player">${vfEsc(x.p.name)}</div><div class="muted">${vfEsc(x.p.position)} · ${vfEsc(x.p.team)} · ${vfEsc(vfExperience(x.p))}</div></td><td class="${(x.posEdge||0)>=4?'vf-rankedge':''}"><b>${fieRank} vs ${marketRank}</b><br><span class="muted">${edge} positional spots</span></td><td><b>${vfFmt(x.adp,0)}</b></td><td><b>${x.snap.score}</b><br><span class="muted">${vfEsc(x.snap.label)}</span></td><td><b>${vfEsc(evidence)}</b><br><span class="muted">${deep?'deep-market role path weighted most heavily':`${Math.round(x.policy.coverage*100)}% policy inputs`}</span></td><td><b>${vfEsc(x.window)}</b><br><span class="muted">market ${vfFmt(x.adp,0)}</span></td><td><span class="vf-state ${vfStateClass(x.state)}">${vfEsc(x.state)}</span>${x.live?.survive!==null&&x.live?.survive!==undefined?`<div class="vf-draft-mini">${x.live.survive}% next-pick availability · Estimate</div>`:''}</td></tr>`;
}

function renderValueFinderInner(){
  const box=$('valueFinderSummary'),status=$('valueFinderStatus');if(!box||!status)return;
  if(!state.league){status.textContent='Load a Sleeper league first. Value Finder needs its scoring, roster rules and eligible player universe.';box.innerHTML='';return;}
  if(!state.matched||!state.projectionStatus?.season){status.textContent='Loading player universe and Sleeper ADP…';box.innerHTML='<div class="notice">Value Finder activates after the league player universe and season ADP feed are available.</div>';return;}
  const research=vfM5Research();
  if(!research&&window.FIE_M5?.loadMilestone5Research&&!VF_CACHE.researchAttempted&&!VF_CACHE.researchLoading){
    VF_CACHE.researchAttempted=true;VF_CACHE.researchLoading=true;status.textContent='Loading M5 draft evidence…';
    Promise.resolve(window.FIE_M5.loadMilestone5Research()).then(()=>{VF_CACHE.researchLoading=false;VF_CACHE.researchError=null;renderValueFinder();}).catch(e=>{VF_CACHE.researchLoading=false;VF_CACHE.researchError=String(e?.message||e||'M5 unavailable');renderValueFinder();});
  }
  if(state.valueFinder.band==='LT100'){renderTop100Optimizer();return;}
  const all=vfBuildRows(),rows=vfFilteredRows(all),shown=rows.slice(0,Number(state.valueFinder.limit)||10),band=BAND_LABELS[state.valueFinder.band]||state.valueFinder.band;
  const high=rows.filter(x=>x.confidence==='HIGH').length,clear=rows.filter(x=>x.snap.score>=75).length,big=rows.filter(x=>(x.posEdge||0)>=10).length;
  status.innerHTML=`<b>${vfEsc(state.league.name||state.league.league_id)}</b> · ${vfEsc(band)} · ${rows.length} qualifying target${rows.length===1?'':'s'} · market ranks are recalculated inside this league's legal player pool. ${research?'M5 historical evidence loaded.':VF_CACHE.researchError?`M5 unavailable (${vfEsc(VF_CACHE.researchError)}); safe fallback evidence shown.`:'M5 evidence pending; safe fallback evidence shown.'}`;
  const rowHtml=shown.map(vfRowHTML).join('')||'<tr><td colspan="8"><div class="empty">No players meet the current Value Finder filters. Broaden the ADP band, snap path or confidence filter.</div></td></tr>';
  box.innerHTML=`${vfControlsHTML()}<div class="vf-summary"><div class="vf-card"><span class="filter-label">Targets found</span><div class="big">${rows.length}</div><div class="tiny">after current filters</div></div><div class="vf-card"><span class="filter-label">High confidence</span><div class="big">${high}</div><div class="tiny">role + evidence support</div></div><div class="vf-card"><span class="filter-label">Clear snap path</span><div class="big">${clear}</div><div class="tiny">Snap Path 75+</div></div><div class="vf-card"><span class="filter-label">10+ positional edge</span><div class="big">${big}</div><div class="tiny">vs eligible Sleeper market</div></div></div>
  <div class="scroll" style="max-height:62vh"><table class="vf-table"><thead><tr><th>#</th><th data-vf-sort="player">Player</th><th data-vf-sort="edge">FIE Pos vs Market Pos</th><th data-vf-sort="adp">ADP</th><th data-vf-sort="snap">Role / Snap Path</th><th data-vf-sort="strength">Evidence</th><th>Target Window</th><th>Action</th></tr></thead><tbody>${rowHtml}</tbody></table></div>
  <div class="notice" style="margin-top:10px"><b>How to read this:</b> Value Finder is a discovery layer, not a replacement for Draft Assistant. <b>100–200</b> emphasizes league/model mispricing and role path; <b>200+</b> weights snap-path certainty most heavily. Every state is explicit. Missing optional research degrades evidence confidence instead of crashing the feature.</div>`;
  bindValueFinderControls();
  box.querySelectorAll('tr[data-vf-id]').forEach(tr=>tr.onclick=e=>{if(e.target.closest('select,input,button'))return;window.openDrawer?.(tr.dataset.vfId);});
  box.querySelectorAll('th[data-vf-sort]').forEach(th=>{th.style.cursor='pointer';th.onclick=()=>{const key=th.dataset.vfSort,f=state.valueFinder;f.sortDir=f.sortKey===key?-f.sortDir:(key==='player'?1:-1);f.sortKey=key;renderValueFinder();};});
}
function renderValueFinder(){
  try{return renderValueFinderInner();}
  catch(e){
    const box=$('valueFinderSummary'),status=$('valueFinderStatus');
    try{window.FIECore?.Diagnostics?.capture?.(e,{domain:'value-finder',league_id:state.league?.league_id,band:state.valueFinder?.band});}catch{}
    console.error('Value Finder recovered from render failure',e);
    if(status)status.textContent='Value Finder recovered from an unavailable evidence path.';
    if(box)box.innerHTML=`<div class="notice"><b>Value Finder is temporarily degraded, not crashed.</b><br>${vfEsc(e?.message||e||'Unknown optional-data error')}<br><span class="muted">Draft Board and Draft Assistant remain available. Switch the market range or retry after background data finishes loading.</span><br><button class="btn ghost" id="vfRetrySafe" style="margin-top:8px">Retry Value Finder</button></div>`;
    const retry=$('vfRetrySafe');if(retry)retry.onclick=()=>{vfInvalidate('manual-retry');renderValueFinder();};
    return null;
  }
}

function bindValueFinderControls(){
  const rerender=()=>renderValueFinder(),f=state.valueFinder;
  const bind=(id,key,parser=v=>v)=>{const el=$(id);if(!el)return;el.onchange=()=>{f[key]=parser(el.value);rerender();};};
  bind('vfBand','band');bind('vfPosition','position');bind('vfSnap','snap');bind('vfExperience','experience');bind('vfConfidence','confidence');bind('vfLimit','limit',Number);
  const band=$('vfBand');if(band)band.onchange=()=>{f.band=band.value;if(f.band==='200_PLUS'&&f.snap==='ALL')f.snap='CLEAR';if(f.band==='LT100')f.undervaluedOnly=false;rerender();};
  const under=$('vfUnder');if(under)under.onchange=()=>{f.undervaluedOnly=under.checked;rerender();};
  const avail=$('vfAvailable');if(avail)avail.onchange=()=>{f.availableOnly=avail.checked;rerender();};
}

function augmentDraftAssistant(){
  const table=$('draftAssistantSummary')?.querySelector('.draft-assistant-table');if(!table||table.dataset.vfAugmented==='1')return;
  const finder=vfBuildRows(),finderMap=new Map(finder.map(x=>[String(x.p.sleeperId),x])),live=vfLiveDraftMap(),top100=vfTop100Rows({baseRows:finder,liveMap:live}),top100Map=new Map(top100.map(x=>[String(x.p.sleeperId),x]));
  finder.forEach(x=>{x.live=live.get(String(x.p.sleeperId))||null;x.state=vfTargetState(x,x.live);});
  const head=table.querySelector('thead tr');if(!head)return;
  const whyHead=[...head.children].find(x=>x.textContent.trim()==='Why')||head.lastElementChild;
  for(const label of ['Value Finder','Target plan']){const th=document.createElement('th');th.dataset.vfDa='1';th.textContent=label;head.insertBefore(th,whyHead);}
  for(const tr of table.querySelectorAll('tbody tr')){
    const rowId=tr.dataset.playerId,name=(tr.children[1]?.querySelector('b')?.textContent||'').trim(),p=PLAYERS.find(x=>rowId&&String(x.sleeperId)===String(rowId))||PLAYERS.find(x=>x.name===name);if(!p)continue;
    const x=finderMap.get(String(p.sleeperId));const why=tr.lastElementChild;
    const td1=document.createElement('td');td1.dataset.vfDa='1';td1.className='vf-da-cell';
    const td2=document.createElement('td');td2.dataset.vfDa='1';td2.className='vf-da-plan';
    const opt=top100Map.get(String(p.sleeperId));
    if(opt){td1.innerHTML=`<span class="vf-chip good">TOP100</span><span class="vf-chip ${opt.tierRisk>=65?'low':opt.tierRisk>=35?'mid':'good'}">Tier ${opt.tierRisk}</span><br><span class="vf-draft-mini">FIE #${opt.fieLeagueRank??'—'} · market #${opt.marketOverallRank??'—'} · capture ${opt.valueCapture??'—'}%</span>`;td2.innerHTML=`<span class="vf-state ${vfStateClass(opt.optimizerAction)}">${vfEsc(opt.optimizerAction)}</span><div class="vf-draft-mini">${opt.survive??'—'}% survives · path ${opt.pathDelta>=0?'+':''}${vfFmt(opt.pathDelta)}</div>`;}else if(x&&x.adp!==null&&x.adp>=100&&x.meaningful){td1.innerHTML=`<span class="vf-chip ${x.adp>=200?'mid':'good'}">${x.adp>=200?'DEEP':'VALUE'}</span><span class="vf-chip ${x.snap.score>=75?'good':'mid'}">Snap ${x.snap.score}</span><br><span class="vf-draft-mini">${x.p.position}${x.fiePosRank??'—'} vs ${x.p.position}${x.marketPosRank??'—'} · target ${vfEsc(x.window)}</span>`;td2.innerHTML=`<span class="vf-state ${vfStateClass(x.state)}">${vfEsc(x.state)}</span>${x.live?.survive!==null&&x.live?.survive!==undefined?`<div class="vf-draft-mini">${x.live.survive}% survives</div>`:''}`;}else{const adp=vfUsableAdp(p),reason=!vfAvailable(p)?'DRAFTED':adp===null?'NO USABLE ADP':adp<100?'TOP-100 TIMING ONLY':adp>=999?'OUTSIDE RANGE':x&&!x.meaningful?'FAIR / INSUFFICIENT EDGE':'OUTSIDE VF RANGE';td1.innerHTML=`<span class="vf-chip mid">${vfEsc(reason)}</span>`;td2.innerHTML=`<span class="vf-state watch">${!vfAvailable(p)?'DRAFTED':'WATCH'}</span>`;}
    tr.insertBefore(td1,why);tr.insertBefore(td2,why);
  }
  table.dataset.vfAugmented='1';
  const note=$('draftAssistantSummary')?.querySelector('.notice');if(note&&!note.dataset.valueFinder){note.dataset.valueFinder='1';note.innerHTML+=`<br><b>Value Finder:</b> Top-100 players now carry Pick Optimizer timing (tier risk, value capture, survival and 3-pick path proxy); late-round targets retain ADP band, snap path, positional edge and WATCH → WAIT → TARGET → TAKE NOW planning. The original Draft Assistant recommendation remains visible separately.`;}
}

const PRE_RENDER_DRAFT=window.renderDraftAssistant;
window.renderDraftAssistant=function(){const r=PRE_RENDER_DRAFT?.();try{augmentDraftAssistant();}catch(e){console.warn('Value Finder Draft Assistant integration skipped',e);}return r;};

function bind(){
  vfInjectStyles();
  if(typeof SECTION_CONFIG!=='undefined'&&SECTION_CONFIG.draft&&!SECTION_CONFIG.draft.tabs.some(x=>x[0]==='valuefinder'))SECTION_CONFIG.draft.tabs.splice(1,0,['valuefinder','Value Finder']);
  if(window.FIE){window.FIE.COMPONENTS=window.FIE.COMPONENTS||{};window.FIE.COMPONENTS.valueFinder=VERSION;}
  window.renderValueFinder=renderValueFinder;
  window.FIE_VALUE_FINDER={VERSION,buildRows:vfBuildRows,filteredRows:vfFilteredRows,invalidate:vfInvalidate,cacheStats:()=>({...VF_CACHE,baseRows:VF_CACHE.baseRows?.length||0,liveMap:VF_CACHE.liveMap?.size||0}),top100Rows:vfTop100Rows,top100Context:vfTop100DraftContext,snapPathScore:vfSnapPath,policyScore:(p)=>{const pool=vfEligiblePool(),ctx=vfPolicyContext(pool);return vfPolicyScore(p,ctx,vfProfile());},render:renderValueFinder,targetState:vfTargetState};
  window.render?.();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
})();

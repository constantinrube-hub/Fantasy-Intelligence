/* FIE V9.3.2 canonical roster-neutral player valuation.
 * This is the one FIE player-quality ranking foundation used by Draft Board,
 * Players, Value Finder and Draft Assistant. Market price is excluded by design.
 */
(function(){
'use strict';
const N=()=>window.FIECore?.Numeric;
const num=v=>N()?.finiteOrNull?.(v)??null;
const clamp=(x,a=0,b=100)=>Math.max(a,Math.min(b,Number(x)||0));
const pid=p=>String(p?.sleeperId||p?.player_id||p?.name||'');
const pos=p=>window.FIECore?.PositionRegistry?.canonical?.(p?.position)||String(p?.position||'').toUpperCase();
const legal=p=>{try{return !!(window.isLeagueEligible?.(p)??(p?.leagueEligible!==false));}catch{return p?.leagueEligible!==false;}};
function format(){try{return String(window.activeFormatKey?.()||window.FIELeagueContext?.current?.()?.format||'REDRAFT').toUpperCase();}catch{return'REDRAFT';}}
function percentileMap(rows,getter){const vals=rows.map(p=>({id:pid(p),v:num(getter(p))})).filter(x=>x.v!==null).sort((a,b)=>a.v-b.v),m=new Map();vals.forEach((x,i)=>m.set(x.id,vals.length<=1?50:100*i/(vals.length-1)));return m;}
function inversePctMap(rows,getter){const vals=rows.map(p=>({id:pid(p),v:num(getter(p))})).filter(x=>x.v!==null).sort((a,b)=>a.v-b.v),m=new Map();vals.forEach((x,i)=>m.set(x.id,vals.length<=1?50:100*(vals.length-1-i)/(vals.length-1)));return m;}
function mean(xs){const a=xs.filter(x=>num(x)!==null).map(Number);return a.length?a.reduce((x,y)=>x+y,0)/a.length:null;}
function season(p){return num(p?.engineSeasonProjection)??num(p?.sleeperSeasonProjection);}
function weekShape(p){
  try{const s=window.FIE_DRAFT_V71?.earlyWeeksFor?.(p);if(s)return{mean:num(s.mean),floor:num(s.floor),ceiling:num(s.ceiling),n:Number(s.n)||0};}catch{}
  const w=window.FIEProjectionResolver?.week?.(p)||{},r=window.FIEProjectionResolver?.range?.(p)||{};return{mean:num(w.value),floor:num(r.low),ceiling:num(r.high),n:w.value===null?0:1};
}
function dynastyRaw(p){const cur=mean([p?.currentOpportunity,p?.targetScore,p?.leagueFit]),future=mean([p?.futureOpportunity,p?.ageCurveScore,p?.tfgModelScore,p?.pffScore]);return mean([cur,future]);}
function health(p){const x=String(p?.injuryStatus||p?.sleeperStatus||'').toLowerCase();if(/ir|pup|out/.test(x))return 25;if(/doubtful/.test(x))return 50;if(/questionable/.test(x))return 75;return 90;}
function scarcityForPosition(rows,position){const svc=window.FIECore?.ReplacementService;if(!svc?.profile)return 50;const pr=svc.profile(position,{league:window.state?.league,players:rows,state:window.state,valueFn:x=>season(x)??weekShape(x).mean??0}),teams=Math.max(1,num(pr?.teams)??12),per=num(pr?.perTeam)??0,bench=num(pr?.benchShare)??0;return clamp(35+per*18+bench*10+(teams>=14?5:0),20,95);}
function weighted(parts){let n=0,d=0;for(const [v,w] of parts){if(num(v)===null||!(w>0))continue;n+=Number(v)*w;d+=w;}return d?n/d:null;}
function confidence(p,shape){let c=0;if(season(p)!==null)c+=35;if(shape.mean!==null)c+=25;if(shape.floor!==null||shape.ceiling!==null)c+=15;if(num(p?.projectedVOR)!==null)c+=15;if(num(p?.currentOpportunity)!==null)c+=5;if(num(p?.pffScore)!==null||num(p?.tfgModelScore)!==null)c+=5;return c>=80?'HIGH':c>=55?'MEDIUM':'LOW';}
function compute(rows=(window.PLAYERS||[]).filter(legal),fmt=format()){
  const f=String(fmt).toUpperCase(),pool=rows.filter(legal),seasonPct=percentileMap(pool,season),vorPct=percentileMap(pool,p=>p?.projectedVOR),dynPct=percentileMap(pool,dynastyRaw),healthPct=percentileMap(pool,health),shapes=new Map(pool.map(p=>[pid(p),weekShape(p)])),meanPct=percentileMap(pool,p=>shapes.get(pid(p))?.mean),floorPct=percentileMap(pool,p=>shapes.get(pid(p))?.floor),ceilPct=percentileMap(pool,p=>shapes.get(pid(p))?.ceiling),spikePct=percentileMap(pool,p=>{const s=shapes.get(pid(p));return s?.mean!==null&&s?.ceiling!==null?s.ceiling-s.mean:null;}),scarcityByPos=new Map([...new Set(pool.map(pos))].map(position=>[position,scarcityForPosition(pool,position)]));
  const out=pool.map(p=>{const id=pid(p),shape=shapes.get(id)||{},sc=scarcityByPos.get(pos(p))??50,sP=seasonPct.get(id),vP=vorPct.get(id),dP=dynPct.get(id),mP=meanPct.get(id),fP=floorPct.get(id),cP=ceilPct.get(id),spP=spikePct.get(id),hP=healthPct.get(id)??50;let base=null,architecture='';
    if(f==='DYNASTY'){base=weighted([[dP,55],[sP,18],[vP,12],[sc,10],[hP,5]]);architecture='dynasty asset + current production + scarcity';}
    else if(f==='DYNASTY_BESTBALL'){base=weighted([[dP,43],[sP,13],[vP,10],[cP,14],[spP,10],[sc,7],[hP,3]]);architecture='dynasty asset + normalized best-ball ceiling/spike + scarcity';}
    else if(f==='CHOPPED'){base=weighted([[mP,38],[fP,30],[sP,12],[vP,8],[sc,8],[hP,4]]);architecture='early-week mean + downside protection + scarcity';}
    else if(f==='REDRAFT_BESTBALL'){base=weighted([[sP,30],[vP,22],[cP,22],[spP,14],[sc,8],[hP,4]]);architecture='season value + normalized ceiling/spike + scarcity';}
    else{base=weighted([[sP,46],[vP,34],[sc,15],[hP,5]]);architecture='season projection + VOR + structural scarcity';}
    const primaryAvailable=season(p)!==null||shape.mean!==null,dataCoverage=[season(p),num(p?.projectedVOR),shape.mean,shape.floor,shape.ceiling,num(p?.currentOpportunity),num(p?.pffScore)??num(p?.tfgModelScore)].filter(x=>x!==null).length/7,hasTeam=!!String(p?.team||'').trim();
    let adjusted=base??0,lowData=false;
    if(!hasTeam){adjusted=Math.min(adjusted,20);lowData=true;}
    if(!f.includes('DYNASTY')&&!primaryAvailable){adjusted=Math.min(adjusted,32);lowData=true;}
    if(f==='CHOPPED'&&shape.mean===null){adjusted=Math.min(adjusted,34);lowData=true;}
    if(f.includes('BESTBALL')&&shape.ceiling===null&&season(p)===null){adjusted=Math.min(adjusted,34);lowData=true;}
    const conf=lowData?'LOW':confidence(p,shape);
    return{p,id,position:pos(p),baseValue:adjusted,rawBaseValue:base??0,seasonProjection:season(p),vor:num(p?.projectedVOR),shape,scarcity:sc,confidence:conf,dataCoverage,lowData,primaryAvailable,architecture,format:f};});
  const overall=[...out].sort((a,b)=>b.baseValue-a.baseValue||String(a.p.name).localeCompare(String(b.p.name)));overall.forEach((x,i)=>x.overallRank=i+1);
  const byPos={};for(const x of out)(byPos[x.position]??=[]).push(x);for(const xs of Object.values(byPos)){xs.sort((a,b)=>b.baseValue-a.baseValue||String(a.p.name).localeCompare(String(b.p.name))).forEach((x,i)=>x.positionRank=i+1);}
  assignTiers(overall,Math.max(1,num(window.state?.league?.total_rosters)??num(window.state?.rosters?.length)??12));return out;
}
function assignTiers(sorted,teams){if(!sorted.length)return;const vals=sorted.map(x=>x.baseValue),gaps=vals.slice(0,-1).map((v,i)=>v-vals[i+1]).filter(Number.isFinite).sort((a,b)=>a-b),med=gaps.length?gaps[Math.floor(gaps.length/2)]:0,mad=gaps.length?gaps.map(x=>Math.abs(x-med)).sort((a,b)=>a-b)[Math.floor(gaps.length/2)]:0,threshold=Math.max(1.25,med+2.3*Math.max(.35,mad)),tier1Max=Math.max(8,Math.round(teams*2));let tier=1,last=0,start=vals[0];for(let i=0;i<sorted.length;i++){if(i>0){const gap=vals[i-1]-vals[i],decay=start-vals[i],size=i-last;const hardTier1=tier===1&&i>=tier1Max,localBreak=size>=4&&gap>=threshold,decayBreak=size>=6&&decay>=Math.max(6,tier*4.5);if(hardTier1||localBreak||decayBreak){tier++;last=i;start=vals[i];}}sorted[i].tier=tier;}}
let cache={key:null,rows:[]};
function fingerprint(){const s=window.state||{},f=format(),players=window.PLAYERS||[],sample=players.slice(0,120).map(p=>[pid(p),season(p),num(p.projectedVOR),num(p.weeklyProjection),num(p.weeklyFloor),num(p.weeklyCeiling)]);return JSON.stringify([s.league?.league_id,f,s.league?.roster_positions,s.rosters?.length,players.length,s.modelHealth?.recomputeCount||0,s.projectionStatus?.seasonCount||0,s.projectionStatus?.weeklyCount||0,s.weekly?.week||1,sample]);}
function rows(force=false){const k=fingerprint();if(force||k!==cache.key)cache={key:k,rows:compute()};return cache.rows;}
function rowFor(p){return rows().find(x=>x.id===pid(p))||null;}
function invalidate(){cache={key:null,rows:[]};}
window.addEventListener?.('fie:league-changing',invalidate);window.addEventListener?.('fie:league-loaded',invalidate);window.addEventListener?.('fie:draft-updated',invalidate);
window.FIEDraftBaseValueService={VERSION:'9.3.2',rows,rowFor,compute,invalidate,format,marketIndependent:true};
})();

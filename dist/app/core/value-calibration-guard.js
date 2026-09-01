/* FIE 9.3.3 cross-position calibration guard.
 * VOR already measures value above a league-specific replacement baseline.
 * When VOR is present, a second structural-scarcity term is correlated with
 * that same replacement signal. This guard removes only that duplicate term.
 * If VOR is unavailable, structural scarcity remains the fallback signal.
 */
(function(){
'use strict';
const VERSION='9.3.3-cross-position-calibration';
const WEIGHT={REDRAFT:15,DYNASTY:10,CHOPPED:8,REDRAFT_BESTBALL:8,DYNASTY_BESTBALL:7,CHOPPED_BESTBALL:8};
const finite=x=>{if(x===null||x===undefined||(typeof x==='string'&&x.trim()===''))return null;const n=Number(x);return Number.isFinite(n)?n:null;};
function adjust(row){
  if(!row||row.__fieCalibration===VERSION)return row;
  const raw=finite(row.baseValue),vor=finite(row.vor),scarcity=finite(row.scarcity),w=WEIGHT[String(row.format||'').toUpperCase()]||0;
  if(raw===null||vor===null||scarcity===null||!(w>0)||w>=100)return {...row,__fieCalibration:VERSION,duplicateScarcityRemoved:false};
  // Canonical base is a normalized weighted mean. Remove the explicit scarcity
  // term and renormalize the remaining components. VOR stays untouched.
  const calibrated=(raw*100-scarcity*w)/(100-w);
  return {...row,rawCanonicalBaseValue:raw,baseValue:calibrated,duplicateScarcityRemoved:true,__fieCalibration:VERSION};
}
function assignTiers(sorted,teams){
  if(!sorted.length)return;const vals=sorted.map(x=>Number(x.baseValue)||0),gaps=vals.slice(0,-1).map((v,i)=>v-vals[i+1]).filter(Number.isFinite).sort((a,b)=>a-b),med=gaps.length?gaps[Math.floor(gaps.length/2)]:0,mad=gaps.length?gaps.map(x=>Math.abs(x-med)).sort((a,b)=>a-b)[Math.floor(gaps.length/2)]:0,threshold=Math.max(1.25,med+2.3*Math.max(.35,mad)),tier1Max=Math.max(8,Math.round(teams*2));let tier=1,last=0,start=vals[0];for(let i=0;i<sorted.length;i++){if(i>0){const gap=vals[i-1]-vals[i],decay=start-vals[i],size=i-last;if((tier===1&&i>=tier1Max)||(size>=4&&gap>=threshold)||(size>=6&&decay>=Math.max(6,tier*4.5))){tier++;last=i;start=vals[i];}}sorted[i].tier=tier;}
}
function calibratedRows(rows){
  const out=(rows||[]).map(adjust),overall=[...out].sort((a,b)=>(Number(b.baseValue)||0)-(Number(a.baseValue)||0)||String(a.p?.name||'').localeCompare(String(b.p?.name||'')));
  overall.forEach((x,i)=>x.overallRank=i+1);const by={};for(const x of out)(by[x.position]??=[]).push(x);for(const xs of Object.values(by))xs.sort((a,b)=>(Number(b.baseValue)||0)-(Number(a.baseValue)||0)).forEach((x,i)=>x.positionRank=i+1);
  const teams=Math.max(1,Number(window.state?.league?.total_rosters||window.state?.rosters?.length||12));assignTiers(overall,teams);return out;
}
function install(){
  const svc=window.FIEDraftBaseValueService;if(!svc||svc.__fieCalibrationInstalled)return false;
  const originalRows=svc.rows.bind(svc);let cacheKey=null,cache=[];
  function key(){const s=window.state||{};return [s.league?.league_id,s.modelHealth?.recomputeCount,s.projectionStatus?.seasonCount,s.projectionStatus?.weeklyCount,s.weekly?.week,window.PLAYERS?.length].join('|');}
  svc.rows=function(force=false){const k=key();if(force||k!==cacheKey){cache=calibratedRows(originalRows(force));cacheKey=k;}return cache;};
  svc.rowFor=function(p){const id=String(p?.sleeperId||p?.player_id||p?.name||'');return svc.rows().find(x=>String(x.id)===id)||null;};
  const oldInvalidate=typeof svc.invalidate==='function'?svc.invalidate.bind(svc):null;svc.invalidate=function(){cacheKey=null;cache=[];oldInvalidate?.();};
  svc.calibration={version:VERSION,rule:'remove explicit scarcity term when valid VOR already carries replacement-level scarcity',fallback:'retain scarcity when VOR is unavailable'};
  svc.__fieCalibrationInstalled=true;return true;
}
function boot(){if(install())return;let n=0;const timer=setInterval(()=>{if(install()||++n>80)clearInterval(timer);},50);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.FIECrossPositionCalibration={VERSION,WEIGHT,adjust,calibratedRows,install};
})();

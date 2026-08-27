/* FIE V9.3.2 canonical projection resolver.
 * Distinguishes unavailable data from a real zero and exposes source/confidence.
 */
(function(){
'use strict';
const N=()=>window.FIECore?.Numeric;
function n(v){return N()?.finiteOrNull?.(v)??(v===null||v===undefined||String(v).trim()===''?null:(Number.isFinite(Number(v))?Number(v):null));}
let currentBundleRef=null,currentBundleMap=new Map();
function currentMap(){const b=window.FIE_M5?.getCurrentBundle?.()||null;if(b!==currentBundleRef){currentBundleRef=b;currentBundleMap=new Map((b?.players||[]).map(r=>[String(r.sleeper_id||''),r]).filter(([id])=>id));}return currentBundleMap;}
function currentRow(p){return currentMap().get(String(p?.sleeperId||''))||null;}
function scheduleGame(team,week,season){
  const rows=window.state?.weekly?.schedule||[];return rows.find(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG')&&(g.home_team===team||g.away_team===team))||null;
}
function schedulePublished(week,season){return (window.state?.weekly?.schedule||[]).some(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG'));}
function isVerifiedBye(p,week,season){return !!p?.team&&schedulePublished(week,season)&&!scheduleGame(p.team,week,season);}
function week(p,{week=window.currentWeek?.()||1,season=window.FIECore?.SeasonResolver?.resolve?.()||window.state?.league?.season}={}){
  const cur=currentRow(p),sameWeek=Number(cur?.week)===Number(week)&&Number(cur?.season)===Number(season);
  if(sameWeek&&cur?.weekly_activation_eligible===true){const v=n(cur.decision_weekly_projection);if(v!==null)return{value:v,source:'FIE governed current',availability:'available',confidence:cur.confidence||'governed',governed:true,week,season,isBye:false};}
  const direct=n(p?.weeklyProjection);if(direct!==null&&String(p?.weeklyProjectionSource||'').toLowerCase().includes('fie'))return{value:direct,source:p.weeklyProjectionSource||'FIE weekly',availability:'available',confidence:'governed',governed:true,week,season,isBye:false};
  const sleeper=n(p?.sleeperWeeklyProjection);if(sleeper!==null)return{value:sleeper,source:'Sleeper weekly',availability:'available',confidence:'baseline',governed:false,week,season,isBye:false};
  if(isVerifiedBye(p,week,season))return{value:0,source:'Schedule',availability:'available',confidence:'exact schedule',governed:false,week,season,isBye:true,reason:'BYE'};
  if(direct!==null)return{value:direct,source:p?.weeklyProjectionSource||'Weekly fallback',availability:'available',confidence:'estimate',governed:false,week,season,isBye:false,estimate:true};
  const seasonV=n(p?.engineSeasonProjection)??n(p?.sleeperSeasonProjection);if(seasonV!==null)return{value:seasonV/17,source:'Season baseline',availability:'available',confidence:'estimate',governed:false,week,season,isBye:false,estimate:true};
  return{value:null,source:'Unavailable',availability:'unavailable',confidence:'none',governed:false,week,season,isBye:false};
}
function range(p,opts={}){
  const w=week(p,opts),cur=currentRow(p),same=Number(cur?.week)===Number(w.week)&&Number(cur?.season)===Number(w.season);
  if(same&&cur?.weekly_activation_eligible===true){const lo=n(cur.p10),hi=n(cur.p90);if(lo!==null||hi!==null)return{low:lo,high:hi,source:'FIE empirical',calibrated:true,estimate:false};}
  const src=String(p?.rangeSource||'').toLowerCase(),lo=n(p?.weeklyFloor),hi=n(p?.weeklyCeiling);
  if((src.includes('empirical')||src.includes('calibrat'))&&(lo!==null||hi!==null))return{low:lo,high:hi,source:p.rangeSource,calibrated:true,estimate:false};
  if(w.value!==null){return{low:lo??Math.max(0,w.value*.78),high:hi??w.value*1.22,source:lo!==null||hi!==null?(p.rangeSource||'Heuristic range'):'Heuristic fallback',calibrated:false,estimate:true};}
  return{low:null,high:null,source:'Unavailable',calibrated:false,estimate:false};
}
function opponent(p,{week:W=window.currentWeek?.()||1,season=window.FIECore?.SeasonResolver?.resolve?.()}={}){const g=scheduleGame(p?.team,W,season);if(!g)return isVerifiedBye(p,W,season)?'BYE':'—';return g.home_team===p.team?g.away_team:g.home_team;}
window.FIEProjectionResolver={VERSION:'9.3.2',week,range,opponent,isVerifiedBye,schedulePublished};
})();

/* FIE V9.3.2 week-series helper for D/ST and Kicker.
 * Future weeks prefer Sleeper's published week projection when available and
 * otherwise remain explicitly labelled baseline estimates. Unknown schedules
 * are never treated as byes.
 */
(function(){'use strict';
const n=v=>window.FIECore?.Numeric?.finiteOrNull?.(v)??null;
const rawWeekCache=new Map(),loading=new Map();
function game(team,week,season){return (window.state?.weekly?.schedule||[]).find(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG')&&(g.home_team===team||g.away_team===team))||null;}
function weekHasSchedule(week,season){return (window.state?.weekly?.schedule||[]).some(g=>Number(g.season)===Number(season)&&Number(g.week)===Number(week)&&String(g.game_type||g.season_type||'REG').toUpperCase().startsWith('REG'));}
function opponent(team,week,season){const g=game(team,week,season);if(g)return g.home_team===team?g.away_team:g.home_team;return weekHasSchedule(week,season)?'BYE':'—';}
function key(week,season){return `${season}:${week}`;}
function normalizeRows(rows){const m=new Map();for(const r of rows||[]){const id=String(r?.player_id||r?.player?.player_id||'');if(id)m.set(id,r);}return m;}
async function loadSleeperWeek(week,season=window.FIECore?.SeasonResolver?.resolve?.()){
  const w=Math.max(1,Math.min(18,Number(week)||1)),s=Number(season);if(!Number.isFinite(s)||s<1900)return null;const k=key(w,s);if(rawWeekCache.has(k))return rawWeekCache.get(k);if(loading.has(k))return loading.get(k);
  const url=`/api/data/sleeper/projections/${s}/${w}`;
  const p=(async()=>{try{const rows=window.FIEDataClient?.json?await window.FIEDataClient.json(url,{sourceId:`special-teams-week-${w}`,ttlMs:30*60*1000}):await fetch(url).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();});const map=normalizeRows(rows);rawWeekCache.set(k,map);return map;}catch(e){rawWeekCache.set(k,null);return null;}finally{loading.delete(k);}})();loading.set(k,p);return p;
}
function rawFor(p,week,season){const map=rawWeekCache.get(key(week,season));if(!(map instanceof Map))return null;return map.get(String(p?.sleeperId||p?.player_id||''))||null;}
function sleeperProjection(p,week,season){const row=rawFor(p,week,season);if(!row)return null;const stats=row.stats||row;try{const v=window.scoreSleeperProjectionStats?.(stats,p);return n(v);}catch{return null;}}
async function preloadWeeks(weeks,season=window.FIECore?.SeasonResolver?.resolve?.()){return Promise.allSettled([...new Set((weeks||[]).map(Number).filter(w=>w>=1&&w<=18))].map(w=>loadSleeperWeek(w,season)));}
function baseline(value,currentWeek,targetWeek){const v=n(value);if(v===null)return null;return v;}
function weeks({player=null,team,currentWeek=window.currentWeek?.()||1,season=window.FIECore?.SeasonResolver?.resolve?.(),projection=null,low=null,high=null,replacement=null}={}){const out=[];for(let w=1;w<=18;w++){const opp=opponent(team,w,season),bye=opp==='BYE',published=sleeperProjection(player,w,season),mean=bye?0:(published??baseline(projection,currentWeek,w)),lo=bye?0:(published!==null?Math.max(0,published*.78):baseline(low,currentWeek,w)),hi=bye?0:(published!==null?published*1.22:baseline(high,currentWeek,w)),source=bye?'Schedule':published!==null?`Sleeper Week ${w}`:w===Number(currentWeek)?'Current-week source':'Baseline Estimate';out.push({week:w,opponent:opp,projection:mean,low:lo,high:hi,replacement:n(replacement),vsReplacement:mean!==null&&n(replacement)!==null?mean-n(replacement):null,source,confidence:bye?'exact schedule':published!==null?'baseline':'estimate',estimate:!bye&&published===null&&w!==Number(currentWeek),bye});}return out;}
function reset(){rawWeekCache.clear();loading.clear();}
window.addEventListener?.('fie:league-changing',()=>{}); // raw Sleeper week data is league-neutral; scoring happens at read time.
window.FIESpecialTeamsSeries={VERSION:'9.3.2',weeks,opponent,weekHasSchedule,loadSleeperWeek,preloadWeeks,sleeperProjection,rawFor,reset};
})();

/* FIE Research Lab computations (UI v10 R3 · WP3.1) — UI contract §7.3.
 *
 * Pure and display-only. Nothing here feeds totals, the optimiser or recommendations (guide §3.2: research outputs
 * are read-only, labelled "research").
 *
 *   evaluate({projRows, matchups, scoring, positionOf, nameOf, minProjection})
 *     Projection error of one completed week for every player rostered in the league, in LEAGUE scoring:
 *     projection = Sleeper's weekly stat line for that week re-scored (FIEScoringCore), actual = Sleeper's
 *     players_points from the league's matchup payload. Players with projection < minProjection (default 3) are
 *     skipped (bench filler); a projected player with 0 points counts (did not play = 0, as in WP-V1).
 *     → {byPosition:[{position, n, mae, bias, rmse}], overall, misses:[top 10 by |error|], n}
 *   lastN({weeks:[{week, matchups}], pids, n}) → Map(pid → {avg, games, weeks}) from players_points (league scoring);
 *     a week counts only when the player was in a matchup's `players` that week (rostered); 0-point weeks count;
 *     unscored weeks (pregame payloads, all zeros) are skipped.
 *   modelState({wms, readiness, researchView, governance}) → per league: active source class counts by position,
 *     governed rows, the research pipeline's per-position decision, the weekly research view status/blockers.
 */
(function(){
'use strict';
const VERSION='10.3.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
const isTeamCode=pid=>/^[A-Z]{2,3}$/.test(String(pid||''));
function evaluate({projRows,matchups,scoring,positionOf,nameOf,minProjection=3}){
  // A week counts as scored only when the league has points (a pregame payload carries zeros — same rule as FIEReview).
  if(!(matchups||[]).some(m=>num(m.points)>0||Object.values(m.players_points||{}).some(v=>num(v)>0)))return{VERSION,scored:false,byPosition:[],overall:{n:0,mae:null,bias:null,rmse:null},misses:[],n:0,minProjection};
  const actual=new Map();for(const m of matchups||[])for(const pid of m.players||[]){const a=num(m.players_points?.[pid]);if(a!==null)actual.set(String(pid),a);}
  const rows=[];
  for(const [pid,a] of actual){const r=projRows?.get?.(pid);if(!r)continue;const pos=positionOf(pid)||String(r.player?.position||(isTeamCode(pid)?'DEF':'')).toUpperCase();
    const p=W().FIEScoringCore.score(r.stats||{},scoring,pos);if(p===null||p<minProjection)continue;rows.push({pid,name:nameOf(pid),position:pos,projected:round(p),actual:round(a),error:round(a-p)});}
  const agg=xs=>{const n=xs.length;if(!n)return{n:0,mae:null,bias:null,rmse:null};return{n,mae:round(xs.reduce((s,x)=>s+Math.abs(x.error),0)/n),bias:round(xs.reduce((s,x)=>s+x.error,0)/n),rmse:round(Math.sqrt(xs.reduce((s,x)=>s+x.error*x.error,0)/n))};};
  const by=new Map();for(const r of rows){if(!by.has(r.position))by.set(r.position,[]);by.get(r.position).push(r);}
  const order=['QB','RB','WR','TE','K','DEF','DL','LB','DB'];
  const byPosition=[...by.entries()].map(([position,xs])=>({position,...agg(xs)})).sort((a,b)=>((order.indexOf(a.position)+99)%99)-((order.indexOf(b.position)+99)%99));
  const misses=[...rows].sort((a,b)=>Math.abs(b.error)-Math.abs(a.error)).slice(0,10);
  return{VERSION,scored:true,byPosition,overall:agg(rows),misses,n:rows.length,minProjection};
}
function lastN({weeks,pids,n=4}){
  const out=new Map(),want=pids?new Set([...pids].map(String)):null;
  const sorted=[...(weeks||[])].sort((a,b)=>b.week-a.week);
  const scored=mm=>(mm||[]).some(m=>num(m.points)>0||Object.values(m.players_points||{}).some(v=>num(v)>0));
  for(const {week,matchups} of sorted){if(!scored(matchups))continue;for(const m of matchups||[])for(const pid0 of m.players||[]){const pid=String(pid0);if(want&&!want.has(pid))continue;
    const x=out.get(pid)||{sum:0,games:0,weeks:[]};if(x.games>=n)continue;const a=num(m.players_points?.[pid0]);if(a===null)continue;x.sum+=a;x.games++;x.weeks.push(week);out.set(pid,x);}}
  for(const [pid,x] of out)out.set(pid,{avg:round(x.sum/x.games),games:x.games,weeks:x.weeks});
  return out;
}
function modelState({wms,readiness,researchView}){
  const rv=new Map(((researchView?.leagues)||[]).map(l=>[String(l.league_id),l]));
  return (wms||[]).filter(Boolean).map(wm=>{
    const counts={};
    const seen=new Set(),ps=[...wm.me.submitted.map(e=>e.p),...wm.me.bench].filter(p=>p&&!seen.has(p.pid)&&seen.add(p.pid));
    for(const p of ps){const c=counts[p.position]||(counts[p.position]={});const k=p.active?.tier||'UNAVAILABLE';c[k]=(c[k]||0)+1;}
    const rd=readiness?.get?.(wm.key.leagueId)||null,v=rv.get(wm.key.leagueId)||null;
    const decisions=rd?.positions?Object.fromEntries(Object.entries(rd.positions).map(([pos,x])=>[pos,{model:x.selected_production_model||null,decision:x.decision||null,challenger:x.best_research_challenger||null,reason:x.reason||null}])):null;
    return{leagueId:wm.key.leagueId,name:wm.entry?.name||wm.league.name,week:wm.key.week,counts,
      governed:ps.filter(p=>['FIE_GOVERNED','FIE_WEEKLY'].includes(p.active?.tier)).length,players:ps.length,
      pipeline:rd?{status:rd.pipeline?.status||null,generatedAt:rd.pipeline?.generated_at||null,decisions}:null,
      research:v?{status:v.status,blockers:v.blockers||[],forecasts:(v.forecasts||[]).length,eligible:!!v.forecast_eligible}:null};});
}
window.FIELab={VERSION,evaluate,lastN,modelState};
})();

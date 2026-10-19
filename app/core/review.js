/* FIE completed-week review (UI v10 R2 · WP2.3) — UI contract §5.13.
 *
 * Pure. For a finished week of one league (WeekModel built for that week + Sleeper matchups of that
 * week with players_points), compares three lineups on ACTUAL points:
 *   1. Submitted        — what you started (Sleeper's official matchup points);
 *   2. Projection best  — the best legal lineup by the projection the app had (Sleeper weekly
 *                         projection, league scoring, status-adjusted), scored with actual points;
 *   3. Hindsight best   — the best legal lineup by actual points (unattainable upper bound).
 * Plus per-player projected vs actual. Pool = the players on your roster that week (matchup
 * `players`), without current reserve/taxi players (an approximation for mid-season moves).
 * Best Ball: Sleeper already scores the best lineup, so Submitted = Hindsight by definition.
 */
(function(){
'use strict';
const VERSION='10.2.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
function build({wm,matchups}){
  const O=W().FIECore.LineupOptimizer,rid=Number(wm.key.rosterId);
  const mm=(matchups||[]).find(m=>Number(m.roster_id)===rid)||null;
  if(!mm)return{available:false,reason:'No Sleeper matchup for this week.'};
  // Pregame payloads carry players_points keys with zeros; a week counts as scored once any point is non-zero.
  const pts=mm.players_points||{},hasPoints=Object.values(pts).some(v=>num(v))||num(mm.points)>0;
  if(!hasPoints)return{available:false,reason:'This week has no scored points yet.'};
  const slots=wm.slots,excluded=new Set([...wm.me.reserve,...wm.me.taxi].map(p=>p.pid));
  const pool=(mm.players||[]).map(String).filter(id=>!excluded.has(id)).map(id=>wm.player(id)).filter(Boolean);
  const actual=pid=>num(pts[pid])??0,proj=p=>p.recValue??0;
  const lineup=(opt,valueOf)=>opt.assignment.map(a=>{const p=wm.player(String(a.playerId));return{slot:a.slot,pid:p.pid,name:p.name,position:p.position,projected:round(proj(p)),actual:round(actual(p.pid)),value:round(valueOf(p))};});
  const starters=(mm.starters||[]).map(String),sp=mm.starters_points||[];
  const submitted={points:round(num(mm.points)??starters.reduce((s,id,i)=>s+(num(sp[i])??actual(id)),0)),
    projected:round(starters.reduce((s,id)=>{const p=wm.player(id);return s+(p?proj(p):0);},0)),
    starters:starters.map((id,i)=>{const p=wm.player(id);return{slot:slots[i],pid:id&&id!=='0'?id:null,name:p?.name||'Empty',position:p?.position||'',projected:round(p?proj(p):0),actual:round(num(sp[i])??actual(id))};})};
  const hOpt=O.optimize(pool,slots,p=>actual(p.pid)),pOpt=O.optimize(pool,slots,proj);
  const hindsight={points:round(hOpt.total),starters:lineup(hOpt,p=>actual(p.pid))};
  const pStarters=lineup(pOpt,proj),projectionBest={projected:round(pOpt.total),points:round(pStarters.reduce((s,x)=>s+(x.actual||0),0)),starters:pStarters};
  if(wm.format?.bestBall){submitted.points=hindsight.points;submitted.starters=hindsight.starters;}
  const started=new Set(submitted.starters.map(s=>s.pid).filter(Boolean)),best=new Set(hindsight.starters.map(s=>s.pid));
  const players=pool.map(p=>({pid:p.pid,name:p.name,position:p.position,started:started.has(p.pid),inHindsight:best.has(p.pid),projected:round(proj(p)),actual:round(actual(p.pid)),diff:round(actual(p.pid)-proj(p)),status:p.status?.code||null}))
    .sort((a,b)=>(b.started-a.started)||(b.actual-a.actual));
  const opp=mm.matchup_id!==null&&mm.matchup_id!==undefined?(matchups||[]).find(m=>m.matchup_id===mm.matchup_id&&Number(m.roster_id)!==rid):null;
  const all=(matchups||[]).map(m=>num(m.points)??0).sort((a,b)=>b-a);
  const missedStarts=players.filter(p=>!p.started&&p.inHindsight).map(p=>p.name),wrongStarts=players.filter(p=>p.started&&!p.inHindsight).map(p=>p.name);
  return{VERSION,available:true,week:wm.key.week,bestBall:!!wm.format?.bestBall,submitted,projectionBest,hindsight,
    efficiency:hindsight.points>0?round(submitted.points/hindsight.points,3):null,leftOnBench:round(hindsight.points-submitted.points),
    projectionVsSubmitted:round(projectionBest.points-submitted.points),players,missedStarts,wrongStarts,
    opponent:opp?{rosterId:Number(opp.roster_id),name:wm.opponent?.name||null,points:round(num(opp.points))}:null,
    weekRank:all.length?all.indexOf(num(mm.points)??0)+1:null,teams:all.length};
}
window.FIEReview={VERSION,build};
})();

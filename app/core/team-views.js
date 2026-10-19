/* FIE team views (UI v10 R3 · WP3.2 Players, WP3.3 Team / Roster) — UI contract §7.2.
 *
 * Pure: aggregates the WeekModel (league-scored Sleeper projections after status policy) and the waiver
 * horizon (Sleeper's projection for each later week, byes from the schedule) for one league. No projection,
 * ranking or value model is created here — only sums, ranks and lineup re-optimisations of existing values.
 *
 *   players({wm, rosters, projRows, horizon, schedule, catalog, season})
 *     → every projected player the league can start, with owner (me / team / FA), this week's value
 *       (status-adjusted, same as Lineup) and the horizon sum.
 *   team({wm, rosters, horizon, schedule, catalog, season, seasonRows, adp})
 *     → position strength (your optimal-lineup points per position, rank among active teams, league median),
 *       depth per starter (share of his points your bench recovers if he is out, full re-optimisation, and the share
 *       the best free agent at his position would recover), thin positions = neither the bench nor the best free agent
 *       recovers policy team.thin_recovery (25 %, R3 tuning 19 Oct), byes in the horizon (points lost to byes,
 *       using this week's values so it works before Sleeper publishes the week), and the roster with real
 *       Sleeper slots, value vs the best free agent at the position ("replacement gap", a VOR proxy).
 */
(function(){
'use strict';
const VERSION='10.3.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
const isTeamCode=pid=>/^[A-Z]{2,3}$/.test(String(pid||''));
function median(xs){const a=xs.filter(x=>x!==null&&Number.isFinite(x)).sort((x,y)=>x-y);if(!a.length)return null;const m=Math.floor(a.length/2);return a.length%2?a[m]:(a[m-1]+a[m])/2;}
function startable(wm){const PR=W().FIECore.PositionRegistry,c=new Map();return pos=>{if(!c.has(pos))c.set(pos,!!pos&&wm.slots.some(s=>PR.eligible(pos,s)));return c.get(pos);};}
/** Values of a player for every horizon week: [0] = WeekModel (status-adjusted), later = Sleeper's projection for that week. */
function horizonValuer({wm,horizon,schedule,catalog,season,now=Date.now()}){
  const vals=(horizon||[]).map((h,i)=>i===0&&h.week===wm.key.week?null:W().FIEWaivers.futureValuer({projRows:h.projRows,scoring:wm.league.scoring,schedule,week:h.week,season,now,catalog,longTermOut:()=>false}));
  const published=(horizon||[]).map(h=>!!h.projRows&&h.projRows.size>0);
  return pid=>(horizon||[]).map((h,k)=>{if(!vals[k]){const p=wm.player(pid);return p?(p.status.unavailable?0:(p.active.value??0)):0;}return published[k]?(vals[k](pid).value??0):null;});
}
function owners(wm,rosters){const m=new Map();for(const r of rosters||[])for(const k of ['players','reserve','taxi'])for(const id of r[k]||[])if(!m.has(String(id)))m.set(String(id),{...wm.ownerOf(id)});return m;}

function players(input){
  const {wm,rosters,projRows}=input,can=startable(wm),hv=horizonValuer(input),own=owners(wm,rosters);
  const ids=new Set([...(projRows?.keys?.()||[])].map(String));for(const id of own.keys())ids.add(id);
  const rows=[];
  for(const id of ids){const p=wm.player(id);if(!p||!p.position||!can(p.position))continue;
    if(!p.team&&!isTeamCode(id))continue;
    const values=hv(id),o=own.get(id)||null,week=values[0]??0,next=values.reduce((s,v)=>s+(v??0),0);
    if(!(week>0)&&!(next>0)&&!o)continue;
    rows.push({pid:id,name:p.name,position:p.position,team:p.team,status:p.status,game:p.game,owner:o,mine:!!o?.me,fa:!o,week:round(week),values:values.map(v=>v===null?null:round(v)),next:round(next)});}
  return{VERSION,rows,weeks:(input.horizon||[]).map(h=>h.week),published:(input.horizon||[]).map(h=>!!h.projRows&&h.projRows.size>0)};
}

function team(input){
  const {wm,rosters,schedule,season}=input,pol=W().FIE_UI_POLICY?.team||{},thinAt=num(pol.thin_recovery)??0.25;
  const O=W().FIECore.LineupOptimizer,can=startable(wm),slots=wm.slots;
  const active=(rosters||[]).filter(r=>(r.players||[]).length);
  // 1 · Position strength: every active team's optimal lineup this week (recValue = status-adjusted, same as Lineup).
  const perTeam=active.map(r=>{const off=new Set([...(r.reserve||[]),...(r.taxi||[])].map(String));
    const pool=(r.players||[]).map(String).filter(id=>!off.has(id)).map(id=>wm.player(id)).filter(p=>p&&can(p.position));
    const o=O.optimize(pool,slots,p=>p.recValue),by={};
    for(const a of o.assignment||[]){const p=wm.player(a.playerId);if(!p)continue;by[p.position]=(by[p.position]||0)+(a.value??p.recValue??0);}
    return{rosterId:Number(r.roster_id),me:Number(r.roster_id)===Number(wm.key.rosterId),total:o.total,by};});
  const positions=[...new Set(perTeam.flatMap(t=>Object.keys(t.by)))].sort((a,b)=>{const ord=['QB','RB','WR','TE','K','DEF','DL','LB','DB'];return (ord.indexOf(a)+99)%99-(ord.indexOf(b)+99)%99;});
  const mine=perTeam.find(t=>t.me)||null;
  const strength=positions.map(pos=>{const xs=perTeam.map(t=>t.by[pos]||0),my=mine?(mine.by[pos]||0):null;
    return{position:pos,points:round(my),rank:my===null?null:1+xs.filter(x=>x>my+1e-9).length,of:xs.length,median:round(median(xs)),best:round(Math.max(...xs))};});
  const totalRank=mine?1+perTeam.filter(t=>t.total>mine.total+1e-9).length:null;
  // 2 · Depth per starter (current week, locks respected by WeekModel.lineupContext)
  const myPool=[...wm.me.submitted.map(e=>e.p),...wm.me.bench].filter(Boolean),uniq=[...new Map(myPool.map(p=>[p.pid,p])).values()];
  const best=O.optimize(uniq.filter(p=>can(p.position)),slots,p=>p.recValue),starters=(best.assignment||[]).map(a=>({slot:a.slot,p:wm.player(a.playerId)})).filter(x=>x.p);
  // Best free agent per position this week (also the replacement-gap reference of the roster table, §4).
  const own=owners(wm,rosters),faBest={};
  for(const [id] of input.projRows||[]){const pid=String(id);if(own.has(pid))continue;const p=wm.player(pid);if(!p||!can(p.position))continue;const v=p.recValue||0;if(v>(faBest[p.position]?.v??-1))faBest[p.position]={v,name:p.name,pid};}
  // Thin = neither your bench nor the waiver wire replaces him: with one rostered TE/QB/K/D-ST the bench recovers 0 %
  // by design, so a bench-only rule flagged ~2.6 positions per league (R3 first cut); counting the best free agent
  // leaves real scarcity (0.1 per league at 25 % on the Week 6 captures). Adding the free agent needs a roster spot.
  const depth=starters.map(({slot,p})=>{const c=wm.lineupContext(p.pid),v=p.recValue||0;
    const loss=c&&c.role==='starter'?-c.delta:null,recovered=loss===null||!(v>0)?null:Math.max(0,Math.min(1,(v-loss)/v));
    const fb=faBest[p.position],faRecovered=fb&&v>0?Math.max(0,Math.min(1,fb.v/v)):0;
    return{pid:p.pid,name:p.name,position:p.position,slot,value:round(v),loss:round(loss),recovered:round(recovered,3),nextBest:c?.nextBest||null,faRecovered:round(faRecovered,3),bestFa:fb?{name:fb.name,value:round(fb.v)}:null};});
  const isThin=d=>d.recovered!==null&&d.value>=1&&Math.max(d.recovered,d.faRecovered)<thinAt;
  const thin=[...new Set(depth.filter(isThin).map(d=>d.position))].map(pos=>({position:pos,starters:depth.filter(d=>d.position===pos&&isThin(d)).map(d=>({name:d.name,recovered:d.recovered,nextBest:d.nextBest,faRecovered:d.faRecovered,bestFa:d.bestFa}))}));
  // 3 · Byes in the horizon: points lost if this week's values held (bye players → 0) — works before a week is published.
  const pv=p=>p.recValue||0,base=O.optimize(uniq.filter(p=>can(p.position)),slots,pv).total;
  const byes=(input.horizon||[]).slice(1).map(h=>{const on=uniq.filter(p=>W().FIEGameState.forTeam(schedule,p.team,{week:h.week,season,now:Date.now()}).bye);
    const set=new Set(on.map(p=>p.pid)),t=O.optimize(uniq.filter(p=>can(p.position)),slots,p=>set.has(p.pid)?0:pv(p)).total;
    return{week:h.week,players:on.map(p=>({pid:p.pid,name:p.name,position:p.position,starter:starters.some(s=>s.p.pid===p.pid)})),cost:round(base-t),published:!!h.projRows&&h.projRows.size>0};});
  // 4 · Roster with real Sleeper slots; replacement gap = value − best free agent at the position this week.
  const hv=horizonValuer(input),sf=slots.some(s=>/SUPER/.test(s));
  const ros=pid=>{if(wm.player(pid)?.position==='DEF'||isTeamCode(pid))return null; // bucket scoring: not valid on season totals
    const r=input.seasonRows?.get?.(String(pid));if(!r?.stats||!Object.keys(r.stats).some(k=>!/^(adp|pos_adp|gp)/.test(k)))return null;const p=wm.player(pid);const t=W().FIEScoringCore.score(r.stats,wm.league.scoring,p?.position);const gp=num(r.stats.gp)||17;return t===null?null:round(t/gp);};
  const adpOf=pid=>{const a=input.adp?.get?.(String(pid));if(!a)return null;return wm.format?.dynasty?(num(sf?a.dynasty2qb:a.dynasty)??num(a.dynasty)):num(a.redraft);};
  const entry=(slot,p)=>{const v=p.status.unavailable?0:(p.active.value??0),fb=faBest[p.position];
    return{slot,pid:p.pid,name:p.name,position:p.position,team:p.team,status:p.status,game:p.game,value:round(v),values:hv(p.pid).map(x=>x===null?null:round(x)),ros:ros(p.pid),adp:adpOf(p.pid),
      gap:fb?round(v-fb.v):null,bestFa:fb?{name:fb.name,value:round(fb.v)}:null,inBest:starters.some(s=>s.p.pid===p.pid)};};
  const roster=[...wm.me.submitted.filter(e=>e.p).map(e=>entry(e.slot,e.p)),...wm.me.bench.filter(p=>!wm.me.submitted.some(e=>e.pid===p.pid)).map(p=>entry('BN',p)),
    ...wm.me.reserve.map(p=>entry('IR',p)),...wm.me.taxi.map(p=>entry('TAXI',p))];
  return{VERSION,strength,totalRank,teams:perTeam.length,myTotal:round(mine?.total),medianTotal:round(median(perTeam.map(t=>t.total))),depth,thin,thinAt,byes,roster,
    weeks:(input.horizon||[]).map(h=>h.week),faBest:Object.fromEntries(Object.entries(faBest).map(([k,v])=>[k,{name:v.name,value:round(v.v)}]))};
}
window.FIETeamViews={VERSION,players,team,horizonValuer};
})();

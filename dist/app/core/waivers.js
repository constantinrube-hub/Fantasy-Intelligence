/* FIE waivers (UI v10 R2 · WP2.4) — UI contract §5.12.
 *
 * Pure: ranks free agents for the managed roster of one league by the FULL legal re-optimisation
 * gain (FIECore.LineupOptimizer) this week and over a short horizon (policy waivers.horizon_weeks),
 * with the legal drop that loses the least. No projection is created here: values are the same
 * league-scored Sleeper weekly projections the WeekModel uses (FIEScoringCore), byes from the
 * schedule (FIEGameState), status from FIEStatus via the WeekModel.
 *
 * Rules
 *   · Current week: players whose game has started are locked — a locked free agent adds nothing
 *     this week, locked starters keep their slots, locked players are never dropped.
 *   · Status: this week the WeekModel's recValue applies (Doubtful = tie-break, Out/IR/… = 0; a designation
 *     left over from the last game is monitored at full value, WeekModel carry-over rule).
 *     Later weeks (R3 WP3.7): Sleeper's published projection for that week decides — Sleeper projects 0 for
 *     players it expects to miss the game and a value once it expects them back. waivers.long_term_zero
 *     (default empty) can still force statuses to 0 for every week.
 *   · Returning players: your injured players count again in the first week Sleeper projects them, including
 *     players in an IR slot (activating them then needs a roster spot). An add whose gain disappears when one
 *     of them returns is labelled a fill-in (`fillIn`), and `ifOut` gives the horizon gain if they stay out.
 *     Unavailable candidates are never "add" rows: they go to `watch` with WATCH, or STASH in
 *     dynasty when a legal reserve slot is free (same rule as R0 FIEStatus.addPolicy).
 *   · Drops: only active-roster players (not reserve/taxi), not locked; a free roster spot means no
 *     drop. Dynasty: players with dynasty ADP ≤ waivers.dynasty_protect_adp are never suggested. An injured
 *     player who is a starter when healthy (season projection per game ≥ your weakest starter) is never
 *     suggested either (`protectedDrops` reason "injured").
 *     Among drops that do not change any week's optimal lineup, the lowest horizon value goes.
 *   · Future weeks without published projections are skipped (weeksAvailable tells how many).
 * Market (FAAB): median / p75 / max winning bid by position from completed waiver transactions,
 * the latest processed run, and remaining budgets.
 */
(function(){
'use strict';
const VERSION='10.4.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
function pol(p){const x=p||W().FIE_UI_POLICY||{},w=x.waivers||{};return{horizon:w.horizon_weeks??3,weekGain:w.alert_week_gain??1,horizonGain:w.alert_horizon_gain??3,perPos:w.candidates_per_position??12,overview:w.overview_candidates??30,protectAdp:w.dynasty_protect_adp??150,longTerm:new Set(w.long_term_zero||['IR','PUP','NA','Suspended']),status:x.status||{},addPolicy:x.status?.waiver_add_policy||{unavailable_action:'WATCH',dynasty_stash_action:'STASH'}};}
const isTeamCode=pid=>/^[A-Z]{2,3}$/.test(String(pid||''));

/** Value of any player in a future week of the horizon (no lock logic: games not started). */
function futureValuer({projRows,scoring,schedule,week,season,now,catalog,longTermOut}){
  const cache=new Map();
  return pid=>{pid=String(pid);if(cache.has(pid))return cache.get(pid);
    const row=projRows?.get?.(pid)||null,rp=row?.player||{},cat=catalog?.get?.(pid)||null;
    const position=String(rp.position||cat?.position||(isTeamCode(pid)?'DEF':'')).toUpperCase(),team=String(row?.team||rp.team||cat?.team||(isTeamCode(pid)?pid:'')||'')||null;
    let v=null;
    if(longTermOut(pid))v=0;
    else{const g=W().FIEGameState.forTeam(schedule,team,{week,season,now});if(g.bye)v=0;else if(row)v=W().FIEScoringCore.score(row.stats||{},scoring,position)??0;}
    const out={value:v,available:row!==null||v===0};cache.set(pid,out);return out;};
}
function quantile(xs,q){if(!xs.length)return null;const s=[...xs].sort((a,b)=>a-b),i=(s.length-1)*q,lo=Math.floor(i),hi=Math.ceil(i);return s[lo]+(s[hi]-s[lo])*(i-lo);}

/**
 * build({wm, league, rosters, managedRosterId, horizon:[{week, projRows}], schedule, season, now,
 *        catalog, adp:Map(pid → {dynasty, dynasty2qb}), policy, limit})
 * horizon[0] must be the WeekModel's week.
 */
function build(input){
  const P=pol(input.policy),{wm,league,rosters,managedRosterId,schedule,season,now=Date.now(),catalog,adp}=input;
  const O=W().FIECore.LineupOptimizer,PR=W().FIECore.PositionRegistry;
  const slots=wm.slots,scoring=league?.scoring_settings||{},fmt=wm.format||{};
  const horizon=(input.horizon||[]).slice(0,P.horizon),weeks=horizon.map(h=>h.week);
  const roster=(rosters||[]).find(r=>Number(r.roster_id)===Number(managedRosterId))||null;
  const empty={VERSION,rows:[],watch:[],byPosition:{},baseline:[],freeSpots:0,rosterLimit:0,protectedDrops:[],weeks,weeksAvailable:0,issues:[]};
  if(!roster||!slots.length){empty.issues.push('Your roster was not found in this league.');return empty;}
  if(!(roster.players||[]).length){empty.eliminated=true;empty.issues.push('Your team has been eliminated in this league — no waiver moves to make.');return empty;}
  // R4.3 · Sleeper "disable_adds" (BestBall – Pro / – Prime, Stoned Lack Bestball Dynasty 3): no waiver claims and no
  // free-agent adds are possible, so nothing is recommended (the research pipeline marks these NOT_APPLICABLE_ADDS_DISABLED).
  if(Number(league?.settings?.disable_adds)===1){empty.addsDisabled=true;empty.issues.push('Adds are disabled in this league (Sleeper setting) — no waiver claims or free-agent adds possible.');return empty;}
  // League roster rules (config/league-portfolio.json › research_constraints, same rules as FIEPortfolioConfig):
  // nfl_entry_cohort_floor → only NFL entry class ≥ minimum; cohort_floor_with_legacy_cap → at the cap,
  // adding a legacy player (entry ≤ legacy_entry_season_max) requires dropping a legacy player.
  const cons=input.constraints||[],entryOf=pid=>{const c=catalog?.get?.(String(pid));const y=num(c?.years_exp);return y===null?null:Number(season)-y;};
  const floor=cons.find(c=>c.type==='nfl_entry_cohort_floor'),legacyC=cons.find(c=>c.type==='cohort_floor_with_legacy_cap');
  const isLegacy=pid=>{const e=entryOf(pid);return e===null||e<=Number(legacyC.legacy_entry_season_max??Number(legacyC.unlimited_entry_season_min)-1);};
  const legacyCap=legacyC?(num(legacyC.legacy_cap_by_season?.[String(season)])??num(legacyC.legacy_cap_after_2030)):null;
  const legacyCount=legacyC?[...(roster.players||[])].filter(isLegacy).length:0;
  const eligibleAdd=pid=>{if(!floor)return true;const e=entryOf(pid);return e!==null&&e>=Number(floor.minimum_entry_season);};
  const rostered=new Set();for(const r of rosters||[])for(const k of ['players','reserve','taxi'])for(const id of r[k]||[])rostered.add(String(id));
  const reserve=new Set((roster.reserve||[]).map(String)),taxi=new Set((roster.taxi||[]).map(String));
  const active=(roster.players||[]).map(String).filter(id=>!reserve.has(id)&&!taxi.has(id));
  const rosterLimit=(league?.roster_positions||[]).filter(x=>!['IR','TAXI','RES'].includes(String(x).toUpperCase())).length;
  const freeSpots=Math.max(0,rosterLimit-active.length);
  const current=wm.player,status=pid=>current(pid)?.status||{code:null};
  const longTermOut=pid=>P.longTerm.has(status(pid).code);
  // Week valuers. Index 0 = WeekModel week (lock-aware), others = future weeks.
  const valuers=horizon.map((h,i)=>i===0&&h.week===wm.key.week?null:futureValuer({projRows:h.projRows,scoring,schedule,week:h.week,season,now,catalog,longTermOut}));
  const hasRows=horizon.map(h=>!!h.projRows&&h.projRows.size>0),weeksAvailable=hasRows.filter(Boolean).length;
  const curIsWeek=horizon.length&&horizon[0].week===wm.key.week;
  const lockedSlots=new Set(),lockedIds=new Set();
  if(curIsWeek)wm.me.submitted.forEach((e,i)=>{if(e.p&&e.p.game.locked){lockedSlots.add(i);lockedIds.add(e.pid);}});
  for(const id of active){const p=current(id);if(p?.game?.locked)lockedIds.add(id);}
  const openSlots=slots.filter((_,i)=>!lockedSlots.has(i));
  const val=(k,pid)=>{if(k===0&&curIsWeek){const p=current(pid);if(!p||p.game.locked)return 0;return p.recValue;}return valuers[k]?.(pid)?.value??0;};
  const future=k=>!(k===0&&curIsWeek);
  const mk=(k,pid,vf)=>({pid:String(pid),sleeperId:String(pid),player_id:String(pid),position:(current(pid)?.position)||'',v:vf(k,pid)});
  // Future weeks: players in your IR slot rejoin the pool in every week Sleeper projects them (they return).
  const reserveIds=[...reserve];
  const poolFor=(k,ids,vf)=>{const base=ids.filter(id=>!(k===0&&curIsWeek&&lockedIds.has(id)));if(future(k))for(const r of reserveIds)if(!base.includes(r)&&vf(k,r)>0)base.push(r);return base.map(id=>mk(k,id,vf));};
  const slotsFor=k=>k===0&&curIsWeek?openSlots:slots;
  const opt=(k,ids,vf=val)=>hasRows[k]?O.optimize(poolFor(k,ids,vf),slotsFor(k),p=>p.v):{total:0,selectedPlayerIds:[]};
  const baseOpt=horizon.map((h,k)=>opt(k,active)),baseSel=baseOpt.map(o=>new Set((o.selectedPlayerIds||[]).map(String)));
  const baseline=horizon.map((h,k)=>({week:h.week,total:round(baseOpt[k].total),published:hasRows[k]}));
  const H=pid=>horizon.reduce((s,_,k)=>s+(hasRows[k]?val(k,pid):0),0);
  // Drops
  // ADP from Sleeper season projections: dynasty ADP (2QB variant in superflex) protects dynasty drops;
  // in redraft the redraft ADP only breaks ties between equally valued drops.
  const sf=slots.some(s=>/SUPER/.test(s));
  const adpOf=pid=>{const a=adp?.get?.(String(pid));if(!a)return null;const d=num(sf?a.dynasty2qb:a.dynasty)??num(a.dynasty);return fmt.dynasty?d:num(a.redraft)??d;};
  // Rest-of-season proxy per week for horizon weeks without published projections: Sleeper season
  // projection, league scoring, ÷ games (only when the season row carries a stat line).
  const rosCache=new Map(),seasonRows=input.seasonRows;
  // D/ST is excluded: its scoring uses points-/yards-allowed buckets that cannot be applied to season totals
  // (R2 gave e.g. JAX D/ST 91 pts/game, which made a D/ST practically undroppable — fixed in R3).
  const rosProxy=pid=>{pid=String(pid);if(rosCache.has(pid))return rosCache.get(pid);let v=null;const r=current(pid)?.position==='DEF'||isTeamCode(pid)?null:seasonRows?.get?.(pid);
    if(r?.stats&&Object.keys(r.stats).some(k=>!/^(adp|pos_adp|gp)/.test(k))){const p=current(pid);const t=W().FIEScoringCore.score(r.stats,scoring,p?.position);const gp=num(r.stats.gp)||17;if(t!==null)v=t/gp;}
    if(longTermOut(pid))v=0;rosCache.set(pid,v);return v;};
  const unpublished=horizon.filter((_,k)=>!hasRows[k]).length;
  // Exact pruning: adding one player changes an optimal assignment by one augmenting path, so
  // gain_k ≤ v_k(x) − (lowest starter value in week k), or ≤ v_k(x) when a slot is unfilled.
  const floorK=horizon.map((_,k)=>{if(!hasRows[k])return Infinity;const o=opt(k,active),vals=(o.assignment||[]).map(a=>a.value??0);return (o.unfilledSlots||[]).length||vals.length<slotsFor(k).length?0:Math.min(...vals);});
  // Your injured players (unavailable now, not a bye) and the first horizon week Sleeper has them back in your best lineup.
  const injured=[...active,...reserveIds].filter(id=>{const s=status(id);return s.unavailable&&s.code!=='BYE';});
  const returning=injured.map(id=>{const k=horizon.findIndex((_,j)=>future(j)&&hasRows[j]&&val(j,id)>0&&baseSel[j].has(id));
    return{pid:id,name:current(id)?.name||id,position:current(id)?.position||'',code:status(id).code,inReserve:reserve.has(id),k:k<0?null:k,week:k<0?null:weeks[k]};});
  const starterFloor=floorK.find(f=>Number.isFinite(f)&&f>0)??null;
  const healthyValue=id=>Math.max(rosProxy(id)??0,...horizon.map((_,k)=>future(k)&&hasRows[k]?val(k,id):0));
  const protectedDrops=[],drops=[];
  for(const id of active){if(lockedIds.has(id))continue;
    if(fmt.dynasty){const a=adpOf(id);if(a!==null&&a<=P.protectAdp){protectedDrops.push({pid:id,name:current(id)?.name||id,adp:a,reason:'adp'});continue;}}
    if(injured.includes(id)&&starterFloor!==null&&healthyValue(id)>=starterFloor){protectedDrops.push({pid:id,name:current(id)?.name||id,adp:adpOf(id),reason:'injured',healthy:round(healthyValue(id))});continue;}
    drops.push(id);}
  const keep=id=>H(id)+unpublished*(rosProxy(id)??0)+((adpOf(id)??999)<999?(1000-adpOf(id))/1e6:0);
  const weakDrops=[...drops].sort((a,b)=>keep(a)-keep(b)).slice(0,4); // exhaustive drop search only among the 4 least valuable
  // Candidates: unrostered, eligible for a starting slot, with an NFL team (or D/ST), projected in the horizon
  // Cheap preselection on Sleeper's published totals (no league scoring yet): top 40 per position.
  const fk=W().FIEScoringCore.fallbackKey(scoring),elig=new Map(),pre=new Map();
  const eligible=pos=>{if(!elig.has(pos))elig.set(pos,slots.some(s=>PR.eligible(pos,s)));return elig.get(pos);};
  for(const h of horizon)for(const [k,row] of h.projRows||[]){const id=String(k);if(rostered.has(id))continue;
    const pos=String(row?.player?.position||catalog?.get?.(id)?.position||(isTeamCode(id)?'DEF':'')).toUpperCase();if(!pos||!eligible(pos))continue;
    if(!(row?.team||row?.player?.team)&&!isTeamCode(id))continue;if(!eligibleAdd(id))continue;
    const x=pre.get(id)||{id,pos,v:0};x.v+=num(row?.stats?.[fk])??0;pre.set(id,x);}
  const preBy=new Map();for(const x of pre.values()){if(!preBy.has(x.pos))preBy.set(x.pos,[]);preBy.get(x.pos).push(x);}
  let ids=[];for(const [,xs] of preBy){xs.sort((a,b)=>b.v-a.v);ids.push(...xs.slice(0,40).map(x=>x.id));}
  // Compare tray / reader: value exactly these players as if added (rostered elsewhere or not); own players are skipped.
  const exact=Array.isArray(input.pids);if(exact)ids=input.pids.map(String).filter(id=>!active.includes(id));
  const byPos=new Map();
  for(const id of ids){const p=current(id);if(!p||!p.position)continue;if(exact){if(!byPos.has(p.position))byPos.set(p.position,[]);byPos.get(p.position).push({id,h:H(id)});continue;}
    if(!slots.some(s=>PR.eligible(p.position,s)))continue;const h=H(id);if(!(h>0))continue; // long-term out (IR/PUP/NA/SUS) has h = 0 and never appears
    if(!byPos.has(p.position))byPos.set(p.position,[]);byPos.get(p.position).push({id,h});}
  let cands=[];for(const [,xs] of byPos){xs.sort((a,b)=>b.h-a.h);cands.push(...(exact?xs:xs.slice(0,P.perPos)));}
  cands.sort((a,b)=>b.h-a.h);if(input.limit)cands=cands.slice(0,input.limit);
  const rows=[],watch=[];
  const settings=league?.settings||{},stashFree=W().FIEStatus?.freeReserveSlots?.(roster,settings)??0;
  const toWatch=(row,st)=>{const legal=W().FIEStatus?.irEligible?.(st.code,settings)&&stashFree>0;
    row.action=fmt.dynasty&&legal?P.addPolicy.dynasty_stash_action:P.addPolicy.unavailable_action;row.reason=`${st.code}${legal?' · reserve (IR) slot free':''}`;row.tier='none';watch.push(row);};
  for(const {id} of cands){
    const p=current(id),st=p.status||{};
    const canGain=input.exhaustive||exact||horizon.some((_,k)=>hasRows[k]&&val(k,id)>floorK[k]+1e-9);
    if(!canGain){const pr={pid:id,name:p.name,position:p.position,team:p.team,status:st,game:p.game,values:horizon.map((_,k)=>hasRows[k]?round(val(k,id)):null),gains:horizon.map((_,k)=>hasRows[k]?0:null),gainWeek:curIsWeek?0:null,gainHorizon:0,freeSpot:freeSpots>0,noDrop:false,drop:null,adp:adpOf(id),tier:'none',pruned:true};
      if(st.unavailable&&st.code!=='BYE')toWatch(pr,st);else rows.push(pr);continue;}
    const L=horizon.map((_,k)=>opt(k,[...active,id]));
    let drop=null,noDrop=false,totals=L.map(x=>x.total),rule=null,finalOpt=L;
    const mustDropLegacy=legacyC&&legacyCap!==null&&isLegacy(id)&&legacyCount>=legacyCap;
    const dropsX=mustDropLegacy?drops.filter(isLegacy):drops,weakX=mustDropLegacy?[...dropsX].sort((a,b)=>keep(a)-keep(b)).slice(0,4):weakDrops;
    if(mustDropLegacy)rule=`Legacy cap ${legacyCount}/${legacyCap}: adding a pre-${Number(legacyC.unlimited_entry_season_min)} player requires dropping one`;
    if(freeSpots<=0||mustDropLegacy){
      const sel=L.map(x=>new Set((x.selectedPlayerIds||[]).map(String)));
      const free=dropsX.filter(d=>sel.every(s=>!s.has(d))).sort((a,b)=>keep(a)-keep(b));
      if(free.length)drop=free[0];
      else if(weakX.length){let best=null;for(const d of weakX){const os=horizon.map((_,k)=>opt(k,[...active.filter(x=>x!==d),id])),ts=os.map(o=>o.total),s=ts.reduce((a,b)=>a+b,0);if(!best||s>best.s+1e-9||(Math.abs(s-best.s)<1e-9&&keep(d)<keep(best.d)))best={d,s,ts,os};}drop=best.d;totals=best.ts;finalOpt=best.os;}
      else noDrop=true;
    }
    const gains=totals.map((t,k)=>hasRows[k]?round(t-baseline[k].total):null);
    const gainWeek=curIsWeek?gains[0]:null,gainHorizon=round(gains.reduce((s,g)=>s+(g??0),0));
    const values=horizon.map((_,k)=>hasRows[k]?round(val(k,id)):null);
    // Who the add replaces in each week's optimal lineup (one augmenting path → at most one leaver)
    const replaces=horizon.map((_,k)=>{if(!hasRows[k]||!(gains[k]>0))return null;const ns=new Set((finalOpt[k].selectedPlayerIds||[]).map(String));const out=[...baseSel[k]].filter(p=>!ns.has(p));
      return out.length?out.map(p=>({pid:p,name:current(p)?.name||p})):[{pid:null,name:'an empty slot'}];});
    // Fill-in: the add helps only until one of your injured players is back (per Sleeper's projections). Causal check:
    // in the return week, holding that player out must raise the add's gain by ≥ 0.5 (a D/ST is never a fill-in for an RB).
    let fillIn=null;for(const r of returning){if(r.k===null||r.k===0||(fillIn&&r.k>=fillIn.k))continue;const before=gains.slice(0,r.k).reduce((a,g)=>a+(g??0),0),after=gains.slice(r.k);
      if(!(before>=0.25&&after.every(g=>g===null||g<=0.25)))continue;
      const one=(k,pid)=>String(pid)===r.pid?0:val(k,pid),ids1=drop?[...active.filter(x=>x!==drop),id]:[...active,id];
      const gOut=opt(r.k,ids1,one).total-opt(r.k,active,one).total;
      if(gOut-(gains[r.k]??0)>=0.5)fillIn={pid:r.pid,name:r.name,week:r.week,k:r.k,gainIfOut:round(gOut)};}
    const row={pid:id,name:p.name,position:p.position,team:p.team,status:st,game:p.game,values,gains,replaces,gainWeek,gainHorizon,fillIn,_drop:drop,freeSpot:freeSpots>0,noDrop,
      drop:drop?{pid:drop,name:current(drop)?.name||drop,position:current(drop)?.position||'',values:horizon.map((_,k)=>hasRows[k]?round(val(k,drop)):null),adp:adpOf(drop),ros:round(rosProxy(drop)),costly:(adpOf(drop)??999)<=P.protectAdp}:null,adp:adpOf(id),rule,entry:entryOf(id)};
    if(st.unavailable&&st.code!=='BYE'){toWatch(row,st);continue;}
    row.tier=!noDrop&&((gainWeek??0)>=P.weekGain||gainHorizon>=P.horizonGain)?'recommended':'none';
    rows.push(row);
  }
  const order=(a,b)=>(b.gainHorizon-a.gainHorizon)||((b.gainWeek??0)-(a.gainWeek??0))||String(a.name).localeCompare(String(b.name));
  rows.sort(order);watch.sort(order);
  // "If they stay out": horizon gain with your returning injured players held at 0 in every week (top rows only).
  const back=returning.filter(r=>r.k!==null);
  if(back.length){const outSet=new Set(back.map(r=>r.pid)),vOut=(k,pid)=>outSet.has(String(pid))?0:val(k,pid);
    const baseOut=horizon.map((_,k)=>hasRows[k]?opt(k,active,vOut).total:0);
    const top=new Set(rows.filter(x=>!x.pruned&&x.gainHorizon>0).slice(0,input.limit||20));for(const x of rows)if(x.fillIn)top.add(x);
    for(const r of top){const ids=r._drop?[...active.filter(x=>x!==r._drop),r.pid]:[...active,r.pid];
      r.ifOut={names:back.map(b=>b.name),gainHorizon:round(horizon.reduce((s,_,k)=>s+(hasRows[k]?opt(k,ids,vOut).total-baseOut[k]:0),0))};}}
  for(const r of [...rows,...watch])delete r._drop;
  const best={};for(const r of rows)if(!best[r.position]&&r.gainHorizon>0)best[r.position]=r;
  const rules=[floor?`Only NFL entry class ${floor.minimum_entry_season} or newer can be added.`:null,legacyC&&legacyCap!==null?`Legacy players (entry ≤ ${Number(legacyC.unlimited_entry_season_min)-1}): ${legacyCount}/${legacyCap} on your roster.`:null].filter(Boolean);
  return{VERSION,rows,watch,byPosition:best,baseline,freeSpots,rosterLimit,protectedDrops,returning:returning.map(({k,...r})=>r),weeks,weeksAvailable,rules,issues:[]};
}

/** FAAB market and budgets from Sleeper transactions (all weeks so far) and rosters. */
function market({league,rosters,users,transactions,positionOf,nameOf,managedRosterId,lastWeek=null}){
  const s=league?.settings||{},faab=Number(s.waiver_type)===2,budget=num(s.waiver_budget)??0;
  const names={};const u=new Map((users||[]).map(x=>[String(x.user_id),x]));for(const r of rosters||[]){const x=u.get(String(r.owner_id));names[r.roster_id]=x?.metadata?.team_name||x?.display_name||x?.username||`Roster ${r.roster_id}`;}
  const tx=(transactions||[]).filter(Boolean);
  const won=tx.filter(t=>t.type==='waiver'&&t.status==='complete');
  const bids={};for(const t of won){const b=num(t.settings?.waiver_bid)??0;for(const pid of Object.keys(t.adds||{})){const pos=positionOf(pid)||'?';(bids[pos]=bids[pos]||[]).push(b);}}
  const byPosition=Object.fromEntries(Object.entries(bids).map(([pos,xs])=>[pos,{n:xs.length,median:round(quantile(xs,.5),1),p75:round(quantile(xs,.75),1),max:Math.max(...xs)}]));
  const lastAt=Math.max(0,...won.map(t=>num(t.status_updated)||0)),runWindow=6*3600e3;
  const run=lastAt?tx.filter(t=>t.type==='waiver'&&Math.abs((num(t.status_updated)||0)-lastAt)<=runWindow):[];
  const lastRun=run.sort((a,b)=>(a.status==='complete'?0:1)-(b.status==='complete'?0:1)||(num(b.settings?.waiver_bid)??0)-(num(a.settings?.waiver_bid)??0)).map(t=>({
    rosterId:Number(t.roster_ids?.[0]),team:names[t.roster_ids?.[0]]||'',status:t.status,bid:num(t.settings?.waiver_bid),mine:(t.roster_ids||[]).map(Number).includes(Number(managedRosterId)),
    adds:Object.keys(t.adds||{}).map(pid=>({pid,name:nameOf(pid),position:positionOf(pid)})),drops:Object.keys(t.drops||{}).map(pid=>({pid,name:nameOf(pid),position:positionOf(pid)})),at:num(t.status_updated)}));
  // R4.7 · Budget table context: average points per scored week (Sleeper fpts ÷ weeks the team played) and last week's
  // rank among teams that played (chopped: active that week) — who is strong / desperate and may bid big.
  const scored=num(s.last_scored_leg)??0,lw=(lastWeek?.matchups||[]).filter(m=>(m.players||[]).length>0),lwSorted=lw.map(m=>num(m.points)??0).sort((a,b)=>b-a);
  const lwRank=rid=>{const m=lw.find(x=>Number(x.roster_id)===Number(rid));return m?lwSorted.indexOf(num(m.points)??0)+1:null;};
  const budgets=(rosters||[]).map(r=>{const used=num(r.settings?.waiver_budget_used)??0,st=r.settings||{},pf=(num(st.fpts)??0)+(num(st.fpts_decimal)??0)/100,gp=(num(st.wins)??0)+(num(st.losses)??0)+(num(st.ties)??0);
    const weeks=s.league_average_match===1&&gp?gp/2:gp||scored;
    return{rosterId:Number(r.roster_id),team:names[r.roster_id],used,remaining:Math.max(0,budget-used),active:(r.players||[]).length>0,mine:Number(r.roster_id)===Number(managedRosterId),
      avgPoints:weeks>0?round(pf/weeks,1):null,lastWeekRank:lwRank(r.roster_id),lastWeekTeams:lw.length||null};}).sort((a,b)=>b.remaining-a.remaining);
  const mine=budgets.find(b=>b.mine)||null,actives=budgets.filter(b=>b.active).map(b=>b.remaining);
  return{faab,budget,byPosition,lastRun,lastRunAt:lastAt||null,budgets,mine,medianRemaining:round(quantile(actives,.5),0),waiverType:num(s.waiver_type)};
}
window.FIEWaivers={VERSION,build,market,quantile,futureValuer};
})();

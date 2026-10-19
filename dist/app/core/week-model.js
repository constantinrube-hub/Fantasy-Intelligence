/* FIE WeekModel (UI v10 R1) — the single source of every displayed week number.
 * UI contract §5 / implementation guide §6.2.
 *
 * Pure: builds from explicit provider inputs (Sleeper league/rosters/users/matchups, Sleeper
 * weekly projection rows, nflverse schedule index, player catalog) plus the policy. The Overview
 * light pass and every v10 league view call the same function, so their numbers are identical
 * by construction (acceptance A-03/A-06).
 *
 * Owners reused (CHANGE_GUIDE): FIECore.LineupOptimizer / PositionRegistry (legal lineup),
 * FIEScoringCore (league scoring), FIEStatus (availability policy), FIEDistribution (spread),
 * FIEGameState (kickoff/lock). No projection is created here: the active value is the league-scored
 * Sleeper projection (primary source today); a verified bye is 0; anything else is unavailable.
 */
(function(){
'use strict';
const VERSION='10.1.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
function policy(p){const x=p||W().FIE_UI_POLICY||{};return{variance:x.variance||{mode:'rule_of_thumb'},thresholds:{urgent:3,recommend:1,close_call:.25,...(x.thresholds||{})},escalation:{chopped_cut_margin:10,h2h_margin:null,...(x.escalation||{})},freshness:{projection_stale:720,...(x.freshness_minutes||{})},primary:x.primary_source||{'*':{'*':'SLEEPER'}},status:x.status||{}};}
function primaryFor(pol,format,pos){const f=pol.primary[format]||pol.primary['*']||{};return f[pos]||f['*']||'SLEEPER';}
const TIER_RANK={FIE_GOVERNED:1,FIE_WEEKLY:2,SLEEPER:3,BYE:4,ESTIMATE:5,UNAVAILABLE:6};
function tierFor(gain,pol){const t=pol.thresholds;return gain>=t.urgent?'urgent':gain>=t.recommend?'recommended':gain>=t.close_call?'close':'none';}
function hash(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(16);}
function isTeamCode(pid){return /^[A-Z]{2,3}$/.test(String(pid||''));}

function buildPlayers(input,pol){
  const {league,projRows,catalog,schedule,week,season,now,fetchedAt,format}=input,scoring=league?.scoring_settings||{},cache=new Map();
  return function player(pid){
    pid=String(pid||'');if(!pid||pid==='0')return null;if(cache.has(pid))return cache.get(pid);
    const row=projRows?.get?.(pid)||null,cat=catalog?.get?.(pid)||null,rp=row?.player||{};
    const position=String(rp.position||cat?.position||(isTeamCode(pid)?'DEF':'')).toUpperCase();
    const team=String(row?.team||rp.team||cat?.team||(isTeamCode(pid)?pid:'')||'')||null;
    const name=cat?.full_name||[rp.first_name,rp.last_name].filter(Boolean).join(' ')||(isTeamCode(pid)?`${pid} D/ST`:pid);
    const game=W().FIEGameState.forTeam(schedule,team,{week,season,now});
    const statusP={sleeperId:pid,team,injuryStatus:cat?.injury_status??null,weeklyStatusFeed:row?{status:rp.injury_status??null,week,season,at:fetchedAt}:null};
    let status=W().FIEStatus.resolve(statusP,{week,season,now,scheduleBye:false}); // bye comes from this model's schedule (below)
    if(game.bye)status={...status,code:'BYE',short:'BYE',label:'BYE',source:'schedule',unavailable:true,monitor:false};
    let active;
    if(game.bye)active={value:0,tier:'BYE',sourceClass:'BYE'};
    else if(row){const v=W().FIEScoringCore.score(row.stats||{},scoring,position);active=v===null?{value:null,tier:'UNAVAILABLE',sourceClass:'UNAVAILABLE'}:{value:v,tier:'SLEEPER',sourceClass:'SLEEPER'};}
    else active={value:null,tier:'UNAVAILABLE',sourceClass:'UNAVAILABLE'};
    const ageMin=fetchedAt?Math.max(0,Math.round((now-fetchedAt)/60000)):null,primary=primaryFor(pol,format?.key||'*',position);
    let dot=null;
    if(active.tier==='SLEEPER'||active.tier==='FIE_GOVERNED'||active.tier==='FIE_WEEKLY'||active.tier==='ESTIMATE'){
      const rank=TIER_RANK[active.tier],prank=TIER_RANK[primary]||3;
      dot=rank<prank?'green':rank>prank?'amber':(ageMin!==null&&ageMin>pol.freshness.projection_stale?'amber':null);
    }
    const v=active.value,unavail=status.unavailable;
    const recValue=v===null?0:unavail?(status.code==='Doubtful'?v*(num(pol.status.doubtful_tiebreak_factor)??.01):0):v;
    const published=row?W().FIEScoringCore.published(row.stats||{},scoring):null;
    const alternatives=[];if(published&&v!==null&&Math.abs(published.value-v)>=.1)alternatives.push({label:published.label,value:published.value});
    // Range (UI contract §5.3): rule of thumb ×0.78–×1.22 unless policy variance.mode = "calibrated" and the
    // position has a WP-V1 calibration; then P10–P90 = projection × measured outcome ratios. The spread used by the
    // win estimate follows automatically (FIEDistribution derives σ from the range).
    const cal=pol.variance?.mode==='calibrated'?pol.variance?.calibration?.positions?.[position]:null;
    const range=v===null?null:cal?{low:Math.max(0,v*cal.p10),high:v*cal.p90,median:v*cal.p50,calibrated:true,label:'P10–P90',n:cal.n}:{low:Math.max(0,v*.78),high:v*1.22,calibrated:false,label:'Typical range'};
    const p={pid,sleeperId:pid,player_id:pid,name,position,team,game,status,active:{...active,dot,ageMin,primary},recValue,alternatives,range,stats:row?.stats||null,opponent:row?.opponent||game.opp||null};
    cache.set(pid,p);return p;
  };
}

function lineupFrom({slots,starters,player}){
  return slots.map((slot,i)=>{const pid=starters?.[i];const p=pid&&String(pid)!=='0'?player(pid):null;return{slot,pid:p?p.pid:null,p};});
}
function partFor(e,actualOf){
  const p=e.p;if(!p)return{mu:0,sd:0,team:'FA',fixed:true,value:0,kind:'empty'};
  const a=num(actualOf(p.pid)),proj=p.status.unavailable?0:(num(p.active.value)??0);
  if(p.game.state==='final')return{mu:a??0,sd:0,team:p.team,fixed:true,value:a??0,kind:'final'};
  if(p.game.locked){const rem=Math.max(0,proj-(a??0)),d=rem>0?W().FIEDistribution.player({mu:rem,low:rem*.78,high:rem*1.22}):{sd:0};return{mu:(a??0)+rem,sd:d.sd,team:p.team,fixed:rem===0,value:(a??0)+rem,kind:'live',actual:a??0};}
  const d=W().FIEDistribution.player({mu:proj,low:p.range?.low,high:p.range?.high});return{mu:d.mu,sd:d.sd,team:p.team,fixed:false,value:proj,kind:'pregame'};
}
function totals(lineup,actualOf){
  let projected=0,banked=0,remaining=0;const parts=[];
  for(const e of lineup){const x=partFor(e,actualOf);parts.push(x);projected+=x.value;if(x.kind==='final'||x.kind==='live')banked+=num(x.actual??x.value)??0;if(x.kind==='pregame')remaining+=x.value;}
  return{projected:round(projected),banked:round(banked),remaining:round(remaining),parts};
}

function recommend({slots,submitted,benchPids,player,pol,format}){
  const empty={changes:[],gain:0,tier:'none',fallbacks:[],starters:submitted,optimizedTotal:null,submittedTotal:null};
  if(format?.bestBall)return empty;
  const openIdx=submitted.map((e,i)=>(!e.p||!e.p.game.locked)?i:-1).filter(i=>i>=0);if(!openIdx.length)return empty;
  const openSlots=openIdx.map(i=>slots[i]),submittedOpen=openIdx.map(i=>submitted[i]).filter(e=>e.p);
  const pool=[...submittedOpen.map(e=>e.p),...benchPids.map(player).filter(p=>p&&!p.game.locked)];
  const seen=new Set(),uniq=pool.filter(p=>!seen.has(p.pid)&&seen.add(p.pid));
  const opt=W().FIECore.LineupOptimizer.optimize(uniq,openSlots,p=>p.recValue);
  const submittedTotal=submittedOpen.reduce((s,e)=>s+e.p.recValue,0),gain=round(opt.total-submittedTotal);
  const tier=tierFor(gain,pol);if(tier==='none')return{...empty,optimizedTotal:round(opt.total),submittedTotal:round(submittedTotal)};
  const sel=new Set(opt.selectedPlayerIds.map(String)),sub=new Set(submittedOpen.map(e=>e.pid));
  const ins=[...sel].filter(id=>!sub.has(id)).map(player).sort((a,b)=>b.recValue-a.recValue);
  const outs=openIdx.map(i=>({i,e:submitted[i]})).filter(x=>!x.e.p||!sel.has(x.e.pid));
  const changes=[],usedOut=new Set();
  for(const pin of ins){
    let best=null;for(const o of outs){if(usedOut.has(o.i))continue;if(!W().FIECore.PositionRegistry.eligible(pin.position,slots[o.i]))continue;const d=pin.recValue-(o.e.p?.recValue??0);if(!best||d>best.d)best={o,d};}
    if(!best){best={o:outs.find(o=>!usedOut.has(o.i))||null,d:pin.recValue};}
    if(best.o)usedOut.add(best.o.i);
    changes.push({slot:best.o?slots[best.o.i]:null,inPid:pin.pid,outPid:best.o?.e.pid||null,delta:round(best.d)});
  }
  // Questionable swap-ins: the best lineup if that player is ruled out (hedge for the inactives list).
  const fallbacks=[];
  for(const c of changes){const pin=player(c.inPid);if(!pin?.status?.monitor)continue;
    const opt2=W().FIECore.LineupOptimizer.optimize(uniq.filter(p=>p.pid!==pin.pid),openSlots,p=>p.recValue),sel2=new Set(opt2.selectedPlayerIds.map(String));
    const alt=[...sel2].filter(id=>!sub.has(id)).map(player).sort((a,b)=>b.recValue-a.recValue)[0]||null;
    fallbacks.push({forPid:pin.pid,pid:alt?.pid||null,total:round(opt2.total),gain:round(opt2.total-submittedTotal)});}
  const rec=submitted.map(e=>({...e}));
  for(const a of opt.assignment){const idx=openIdx.find(i=>slots[i]===a.slot&&!rec[i].__filled);if(idx===undefined)continue;rec[idx]={slot:a.slot,pid:String(a.playerId),p:player(a.playerId),__filled:true};}
  return{changes,gain,tier,fallbacks,starters:rec.map(({__filled,...e})=>e),optimizedTotal:round(opt.total),submittedTotal:round(submittedTotal)};
}

function standings(league,rosters,users,meId,chopped=false){
  const name=rosterNames(rosters,users),rows=(rosters||[]).map(r=>{const s=r.settings||{};return{rosterId:Number(r.roster_id),name:name[r.roster_id],wins:num(s.wins)??0,losses:num(s.losses)??0,ties:num(s.ties)??0,pf:(num(s.fpts)??0)+(num(s.fpts_decimal)??0)/100,pa:(num(s.fpts_against)??0)+(num(s.fpts_against_decimal)??0)/100,active:(r.players||[]).length>0};});
  // Chopped has no wins: survivors first, then points for (Sleeper's elimination order is by weekly score).
  if(chopped)rows.sort((a,b)=>(b.active-a.active)||b.pf-a.pf);else rows.sort((a,b)=>(b.wins+b.ties*.5)-(a.wins+a.ties*.5)||b.pf-a.pf);
  rows.forEach((r,i)=>{r.rank=i+1;r.me=r.rosterId===Number(meId);});
  return{rows,chopped:!!chopped,playoffTeams:chopped?null:num(league?.settings?.playoff_teams),medianGames:Number(league?.settings?.league_average_match)===1};
}
function rosterNames(rosters,users){const u=new Map((users||[]).map(x=>[String(x.user_id),x]));const out={};for(const r of rosters||[]){const x=u.get(String(r.owner_id));out[r.roster_id]=x?.metadata?.team_name||x?.display_name||x?.username||`Roster ${r.roster_id}`;}return out;}

function build(input){
  const pol=policy(input.policy),{league,rosters,users,matchups,week,season,now=Date.now(),managedRosterId,format={}}=input;
  const issues=[];
  const player=buildPlayers({...input,now,format},pol);
  const slots=W().FIECore.PositionRegistry.starterSlots(league?.roster_positions||[]);
  const roster=(rosters||[]).find(r=>Number(r.roster_id)===Number(managedRosterId))||null;
  const mm=(matchups||[]).find(m=>Number(m.roster_id)===Number(managedRosterId))||null;
  if(!input.projRows||!input.projRows.size)issues.push({code:'NO_PROJECTIONS',text:'Weekly projections are not loaded for this week.'});
  if(!roster)issues.push({code:'NO_ROSTER',text:'Your roster was not found in this league.'});
  const reserve=(roster?.reserve||[]).map(String),taxi=(roster?.taxi||[]).map(String);
  const starterIds=(mm?.starters||roster?.starters||[]).map(String);
  const all=(mm?.players||roster?.players||[]).map(String);
  const benchPids=all.filter(id=>!starterIds.includes(id)&&!reserve.includes(id)&&!taxi.includes(id));
  const actualOf=pid=>{const v=mm?.players_points?.[pid];return num(v);};
  let submitted=lineupFrom({slots,starters:starterIds,player});
  if(format.bestBall){ // automatic optimal lineup: display it as the lineup
    const pool=all.filter(id=>!reserve.includes(id)&&!taxi.includes(id)).map(player).filter(Boolean);
    const opt=W().FIECore.LineupOptimizer.optimize(pool,slots,p=>p.recValue),used=new Set();
    submitted=slots.map(slot=>{const a=opt.assignment.find(x=>x.slot===slot&&!used.has(x.playerId));if(a)used.add(a.playerId);return{slot,pid:a?String(a.playerId):null,p:a?player(a.playerId):null};});
  }
  const rec=recommend({slots,submitted,benchPids,player,pol,format});
  const myTotals=totals(submitted,actualOf),recTotals=rec.changes.length?totals(rec.starters,actualOf):null;
  const emptySlots=submitted.filter(e=>!e.p).map(e=>e.slot);
  const names=rosterNames(rosters,users);
  // Opponent (H2H only)
  let opponent=null;
  if(!format.chopped&&mm&&mm.matchup_id!==null&&mm.matchup_id!==undefined){
    const om=(matchups||[]).find(m=>m.matchup_id===mm.matchup_id&&Number(m.roster_id)!==Number(managedRosterId));
    if(om){const oActual=pid=>num(om.players_points?.[pid]);let oLine=lineupFrom({slots,starters:(om.starters||[]).map(String),player});
      if(format.bestBall){const pool=(om.players||[]).map(player).filter(Boolean),opt=W().FIECore.LineupOptimizer.optimize(pool,slots,p=>p.recValue),used=new Set();oLine=slots.map(slot=>{const a=opt.assignment.find(x=>x.slot===slot&&!used.has(x.playerId));if(a)used.add(a.playerId);return{slot,pid:a?String(a.playerId):null,p:a?player(a.playerId):null};});}
      opponent={rosterId:Number(om.roster_id),name:names[om.roster_id],starters:oLine,totals:totals(oLine,oActual),reportedPoints:num(om.points)};}
  }
  let winEstimate=null;
  if(opponent){const a=W().FIEDistribution.team(myTotals.parts),b=W().FIEDistribution.team(opponent.totals.parts);
    const calibrated=pol.variance?.mode==='calibrated';
    winEstimate={value:W().FIEDistribution.winProbability(a,b),method:'matchup-normal',dot:'amber',calibrated,note:calibrated?`Estimate — spread calibrated on 2026 Weeks 1–5 (n=${pol.variance?.calibration?.n??'?'}, in-sample; K/D/ST still rule of thumb); normal approximation.`:'Estimate — spread not yet calibrated (WP-V1); likely overconfident.',inputsHash:hash(JSON.stringify([a,b]))};
    if(recTotals){const r=W().FIEDistribution.team(recTotals.parts);winEstimate.withRecommended=W().FIEDistribution.winProbability(r,b);}}
  // Chopped field
  let field=null;
  if(format.chopped){
    const active=(rosters||[]).filter(r=>(r.players||[]).length>0),eliminated=(rosters||[]).filter(r=>!(r.players||[]).length);
    const scored=num(league?.settings?.last_scored_leg)??Math.max(0,(num(league?.settings?.leg)??week)-1);
    const verified=eliminated.length===scored;
    const proj=active.map(r=>{const m=(matchups||[]).find(x=>Number(x.roster_id)===Number(r.roster_id));const act=pid=>num(m?.players_points?.[pid]);
      const line=lineupFrom({slots,starters:(m?.starters||r.starters||[]).map(String),player});return{rosterId:Number(r.roster_id),name:names[r.roster_id],projected:totals(line,act).projected};});
    proj.sort((a,b)=>b.projected-a.projected);proj.forEach((x,i)=>{x.rank=i+1;x.me=x.rosterId===Number(managedRosterId);});
    const me=proj.find(x=>x.me)||null,others=proj.filter(x=>!x.me),cut=others.length?Math.min(...others.map(x=>x.projected)):null;
    field={verified,activeCount:active.length,eliminatedCount:eliminated.length,scoredWeeks:scored,rows:proj,eliminated:eliminated.map(r=>({rosterId:Number(r.roster_id),name:names[r.roster_id]})),
      myRank:me?.rank??null,cutLine:cut,marginToCut:me&&cut!==null?round(me.projected-cut):null,meEliminated:!!roster&&!(roster.players||[]).length};
    if(verified&&field.marginToCut!==null&&field.marginToCut<pol.escalation.chopped_cut_margin&&rec.tier==='recommended')rec.tier='urgent';
  }else if(opponent&&pol.escalation.h2h_margin!==null){const m=myTotals.projected-opponent.totals.projected;if(Math.abs(m)<pol.escalation.h2h_margin&&rec.tier==='recommended')rec.tier='urgent';}
  // Lineup context (Advanced, R2 · WP2.1): what this player is worth to YOUR lineup this week —
  // starter: points lost if he could not play (full re-optimisation); bench: points gained if he
  // had to start (forced into the best legal slot). Locked players are fixed, as in recommendations.
  // Who rosters a player in this league (reader / compare tray).
  const owner=new Map();for(const r of rosters||[])for(const k of ['players','reserve','taxi'])for(const id of r[k]||[])owner.set(String(id),{rosterId:Number(r.roster_id),name:names[r.roster_id],me:Number(r.roster_id)===Number(managedRosterId),where:k==='players'?'roster':k});
  const ownerOf=pid=>owner.get(String(pid))||null;
  const ctxCache=new Map();
  function lineupContext(pid){pid=String(pid);if(ctxCache.has(pid))return ctxCache.get(pid);
    const O=W().FIECore.LineupOptimizer,lockedIdx=submitted.map((e,i)=>e.p&&e.p.game.locked?i:-1).filter(i=>i>=0);
    const open=slots.filter((_,i)=>!lockedIdx.includes(i)),pool=[...submitted.map(e=>e.p),...benchPids.map(player)].filter(p=>p&&!p.game.locked);
    const seen=new Set(),uniq=pool.filter(p=>!seen.has(p.pid)&&seen.add(p.pid)),me=uniq.find(p=>p.pid===pid);
    let out=null;
    if(me&&open.length){const base=O.optimize(uniq,open,p=>p.recValue),inLineup=base.selectedPlayerIds.map(String).includes(pid);
      if(inLineup){const w=O.optimize(uniq.filter(p=>p.pid!==pid),open,p=>p.recValue);const nb=w.selectedPlayerIds.map(String).find(x=>!base.selectedPlayerIds.map(String).includes(x));out={role:'starter',delta:round(w.total-base.total),nextBest:nb?player(nb)?.name:null};}
      else{const BIG=1e4,f=O.optimize(uniq,open,p=>p.recValue+(p.pid===pid?BIG:0)),a=f.assignment.find(x=>String(x.playerId)===pid);out={role:'bench',delta:round(f.total-BIG-base.total),slot:a?.slot||null};}}
    ctxCache.set(pid,out);return out;}
  // Next lock among my starters and bench
  const kick=[...submitted.map(e=>e.p),...benchPids.map(player)].filter(p=>p&&!p.game.locked&&p.game.kickoff).map(p=>p.game.kickoff);
  const nextLock=kick.length?Math.min(...kick):null;
  return{VERSION,key:{leagueId:String(league?.league_id||''),season,week,rosterId:Number(managedRosterId)||null},format,
    league:{name:league?.name||'',teams:num(league?.total_rosters)??(rosters||[]).length,status:league?.status||null,scoring:league?.scoring_settings||{}},
    slots,player,lineupContext,ownerOf,me:{rosterId:Number(managedRosterId)||null,name:names[managedRosterId]||null,submitted,bench:benchPids.map(player).filter(Boolean),reserve:reserve.map(player).filter(Boolean),taxi:taxi.map(player).filter(Boolean),
      recommended:rec,totals:myTotals,recommendedTotals:recTotals,emptySlots,reportedPoints:num(mm?.points),matchupFound:!!mm},
    opponent,winEstimate,field,standings:standings(league,rosters,users,managedRosterId,!!format.chopped),nextLock,issues,builtAt:now};
}
window.FIEWeekModel={VERSION,build,tierFor:(g,p)=>tierFor(g,policy(p))};
})();

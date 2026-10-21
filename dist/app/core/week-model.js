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
const VERSION='10.4.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
function policy(p){const x=p||W().FIE_UI_POLICY||{};return{opponents:x.opponents||{},variance:x.variance||{mode:'rule_of_thumb'},thresholds:{urgent:3,recommend:1,close_call:.25,...(x.thresholds||{})},escalation:{chopped_cut_margin:10,h2h_margin:null,...(x.escalation||{})},freshness:{projection_stale:720,...(x.freshness_minutes||{})},primary:x.primary_source||{'*':{'*':'SLEEPER'}},status:x.status||{}};}
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
    let active;
    if(game.bye)active={value:0,tier:'BYE',sourceClass:'BYE'};
    else if(row){const v=W().FIEScoringCore.score(row.stats||{},scoring,position);active=v===null?{value:null,tier:'UNAVAILABLE',sourceClass:'UNAVAILABLE'}:{value:v,tier:'SLEEPER',sourceClass:'SLEEPER'};}
    else active={value:null,tier:'UNAVAILABLE',sourceClass:'UNAVAILABLE'};
    const statusP={sleeperId:pid,team,injuryStatus:cat?.injury_status??null,weeklyStatusFeed:row?{status:rp.injury_status??null,week,season,at:fetchedAt}:null};
    let status=W().FIEStatus.resolve(statusP,{week,season,now,scheduleBye:false}); // bye comes from this model's schedule (below)
    if(game.bye)status={...status,code:'BYE',short:'BYE',label:'BYE',source:'schedule',unavailable:true,monitor:false};
    // R3 WP3.7 · last-game carry-over (UI contract §2.1): Sleeper keeps a game designation (Out/Doubtful) until the next
    // injury report, but projects 0 for every Out/Doubtful player in the week the designation is for (verified on all
    // captures). A positive Sleeper projection for THIS week next to Out/Doubtful therefore means the tag refers to the
    // previous game: the player is monitored at full value instead of being treated as out. Only before the week's first
    // injury report: kickoff more than last_game_carry_over_min_hours (108 h ≈ Wednesday morning for a Sunday game) away.
    // From the first report on every tag counts (Sleeper is not perfectly consistent: Thursday of Week 6 it still projected
    // Doubtful IDP Marques Sigle, 102 h before kickoff).
    else if((pol.status.last_game_carry_over||[]).includes(status.code)&&status.source==='projection-feed'&&num(active.value)>0&&game.state==='pregame'
      &&num(game.kickoff)!==null&&game.kickoff-now>(num(pol.status.last_game_carry_over_min_hours)??108)*3600e3)
      status={...status,unavailable:false,monitor:true,carriedOver:true,short:`${status.short}·prev`,label:`${status.code} last game — Sleeper projects him this week`};
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
    // R5.7 · Deciles P10…P90 for the Compare curve: player-level when policy variance.calibration.player_level is on and
    // the player has a block (backlog), else position × projection tier (WP-V1 Weeks 1–6). Display only: the win estimate
    // keeps the position-level P10/P90 above.
    if(range&&pol.variance?.mode==='calibrated'){const C=pol.variance.calibration||{},pl=C.player_level?C.players?.[pid]:null,ts=C.tiers?.[position]||null;
      const t=pl?null:ts?(ts.find(x=>v>=x.min&&(x.max===null||v<x.max))||(v<ts[0].min?ts[0]:ts[ts.length-1])):null;
      if(pl?.q||t)range.deciles={q:(pl?.q||t.q).map(r=>Math.max(0,v*r)),source:pl?'player':'position × projection tier',n:pl?.n??t.n,tier:t?{min:t.min,max:t.max}:null};}
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
/** R5.5 · A team's best legal lineup "until lock": locked slots keep their player, unlocked slots are re-optimised from
 *  the roster (without IR/taxi, without locked players). Used for opponents and the chopped field. */
function optimalUntilLock({slots,line,pool,player}){
  const locked=line.map((e,i)=>e.p&&e.p.game.locked?i:-1).filter(i=>i>=0),used=new Set(locked.map(i=>line[i].pid));
  const open=slots.map((s,i)=>i).filter(i=>!locked.includes(i)),cand=[...new Set(pool.map(String))].filter(id=>!used.has(id)).map(player).filter(p=>p&&!p.game.locked);
  const opt=W().FIECore.LineupOptimizer.optimize(cand,open.map(i=>slots[i]),p=>p.recValue),out=line.map(e=>({...e})),taken=new Set();
  for(const i of open){const a=opt.assignment.find(x=>x.slot===slots[i]&&!taken.has(String(x.playerId)));if(a){taken.add(String(a.playerId));out[i]={slot:slots[i],pid:String(a.playerId),p:player(a.playerId)};}else out[i]={slot:slots[i],pid:null,p:null};}
  return out;
}
/** R5.5 · Opponent lineup mode: "optimal" until policy opponents.optimal_until (default Thursday 18:00 UTC before the
 *  week's first kickoff), "asSet" after — early in the week many managers have not fixed byes/injuries yet. */
function opponentMode(pol,schedule,week,season,now){
  const cfg={weekday:4,hour_utc:18,...(pol.opponents?.optimal_until||{})};let first=null;
  for(const g of new Set(schedule?.games?.values?.()||[]))if(g.season===Number(season)&&g.week===Number(week)&&g.kickoff)first=first===null?g.kickoff:Math.min(first,g.kickoff);
  if(first===null)return{mode:'asSet',cutoff:null};
  const d=new Date(first);let c=Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate(),Number(cfg.hour_utc)||0)-((d.getUTCDay()-Number(cfg.weekday)+7)%7)*864e5;if(c>first)c-=7*864e5;
  return{mode:now<c?'optimal':'asSet',cutoff:c};
}
function totals(lineup,actualOf){
  let projected=0,banked=0,remaining=0;const parts=[];
  for(const e of lineup){const x=partFor(e,actualOf);parts.push(x);projected+=x.value;if(x.kind==='final'||x.kind==='live')banked+=num(x.actual??x.value)??0;if(x.kind==='pregame')remaining+=x.value;}
  return{projected:round(projected),banked:round(banked),remaining:round(remaining),parts};
}

function recommend({slots,submitted,benchPids,player,pol,format}){
  const empty={changes:[],moves:[],gain:0,tier:'none',fallbacks:[],starters:submitted,optimizedTotal:null,submittedTotal:null};
  if(format?.bestBall)return empty;
  const openIdx=submitted.map((e,i)=>(!e.p||!e.p.game.locked)?i:-1).filter(i=>i>=0);if(!openIdx.length)return empty;
  const openSlots=openIdx.map(i=>slots[i]),submittedOpen=openIdx.map(i=>submitted[i]).filter(e=>e.p);
  const pool=[...submittedOpen.map(e=>e.p),...benchPids.map(player).filter(p=>p&&!p.game.locked)];
  const seen=new Set(),uniq=pool.filter(p=>!seen.has(p.pid)&&seen.add(p.pid));
  const opt=W().FIECore.LineupOptimizer.optimize(uniq,openSlots,p=>p.recValue);
  const submittedTotal=submittedOpen.reduce((s,e)=>s+e.p.recValue,0),gain=round(opt.total-submittedTotal);
  const tier=tierFor(gain,pol);if(tier==='none')return{...empty,optimizedTotal:round(opt.total),submittedTotal:round(submittedTotal)};
  // R4.1 · Changes are derived per SLOT from the optimal assignment, not by set difference. The optimizer may shift a
  // starter between slots (FLEX → WR) to make room; a 1:1 "X for Y" pairing then put players into slots they are not
  // eligible for (Week 7: "Start Stevenson (RB) at WR for Boston"). Now: every open slot gets its optimal occupant,
  // same-named slots keep their current occupant where possible (no churn between WR1/WR2), and each player entering
  // from the bench is paired with the player he finally displaces by following the chain of moved starters.
  const sub=new Set(submittedOpen.map(e=>e.pid)),rec=submitted.map(e=>({...e}));
  const byName=new Map();for(const a of opt.assignment){const k=a.slot;(byName.get(k)||byName.set(k,[]).get(k)).push(String(a.playerId));}
  for(const [slotName,pids] of byName){const idx=openIdx.filter(i=>slots[i]===slotName),left=[...pids],free=[];
    for(const i of idx){const cur=submitted[i].pid,j=cur?left.indexOf(cur):-1;if(j>=0){left.splice(j,1);rec[i]={slot:slotName,pid:cur,p:player(cur)};}else free.push(i);}
    for(const i of free){const pid=left.shift()||null;rec[i]={slot:slotName,pid,p:pid?player(pid):null};}}
  for(const i of openIdx)if(!byName.has(slots[i]))rec[i]={slot:slots[i],pid:null,p:null};
  const before=new Map(openIdx.map(i=>[i,submitted[i].p?submitted[i].pid:null])),after=new Map(openIdx.map(i=>[i,rec[i].pid]));
  const slotOf=(map,pid)=>{for(const [i,x] of map)if(x===pid)return i;return -1;};
  const moves=[];
  for(const i of openIdx){const b=before.get(i),a=after.get(i);if(a===b)continue;
    if(a&&sub.has(a))moves.push({kind:'move',pid:a,from:slots[slotOf(before,a)],to:slots[i]});
    else if(a)moves.push({kind:'start',pid:a,to:slots[i]});}
  for(const i of openIdx){const b=before.get(i);if(b&&slotOf(after,b)<0)moves.push({kind:'bench',pid:b,from:slots[i]});}
  const changes=[];
  for(const m of moves.filter(x=>x.kind==='start')){
    let i=slotOf(after,m.pid),guard=0,outPid=null;
    while(i>=0&&guard++<slots.length){const b=before.get(i);if(!b)break;if(slotOf(after,b)<0){outPid=b;break;}i=slotOf(after,b);}
    const via=[];let k=slotOf(after,m.pid);guard=0;while(k>=0&&guard++<slots.length){const b=before.get(k);if(!b||b===outPid)break;via.push({pid:b,from:slots[k],to:slots[slotOf(after,b)]});k=slotOf(after,b);}
    const pin=player(m.pid),pout=outPid?player(outPid):null;
    changes.push({slot:m.to,inPid:m.pid,outPid,outSlot:outPid?slots[slotOf(before,outPid)]:null,via,delta:round((pin?.recValue??0)-(pout?.recValue??0))});}
  changes.sort((a,b)=>b.delta-a.delta);
  // Questionable swap-ins: the best lineup if that player is ruled out (hedge for the inactives list).
  const fallbacks=[];
  for(const c of changes){const pin=player(c.inPid);if(!pin?.status?.monitor)continue;
    const opt2=W().FIECore.LineupOptimizer.optimize(uniq.filter(p=>p.pid!==pin.pid),openSlots,p=>p.recValue),sel2=new Set(opt2.selectedPlayerIds.map(String));
    const alt=[...sel2].filter(id=>!sub.has(id)).map(player).sort((a,b)=>b.recValue-a.recValue)[0]||null;
    fallbacks.push({forPid:pin.pid,pid:alt?.pid||null,total:round(opt2.total),gain:round(opt2.total-submittedTotal)});}
  return{changes,moves,gain,tier,fallbacks,starters:rec,optimizedTotal:round(opt.total),submittedTotal:round(submittedTotal)};
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
  let benchPids=all.filter(id=>!starterIds.includes(id)&&!reserve.includes(id)&&!taxi.includes(id));
  const actualOf=pid=>{const v=mm?.players_points?.[pid];return num(v);};
  let submitted=lineupFrom({slots,starters:starterIds,player});
  if(format.bestBall){ // automatic optimal lineup: display it as the lineup
    const pool=all.filter(id=>!reserve.includes(id)&&!taxi.includes(id)).map(player).filter(Boolean);
    const opt=W().FIECore.LineupOptimizer.optimize(pool,slots,p=>p.recValue),used=new Set();
    submitted=slots.map(slot=>{const a=opt.assignment.find(x=>x.slot===slot&&!used.has(x.playerId));if(a)used.add(a.playerId);return{slot,pid:a?String(a.playerId):null,p:a?player(a.playerId):null};});
    // R4.2 · The bench is everyone not in the projected optimal lineup. It was "roster minus Sleeper's starters" (last
    // week's automatic lineup), so a player who started last week but not in this week's optimum appeared nowhere
    // (Among Us Guillotine 3, Week 7: Dalton Kincaid). IR/taxi stay separate.
    const inLine=new Set(submitted.filter(e=>e.pid).map(e=>e.pid));
    benchPids=all.filter(id=>!inLine.has(id)&&!reserve.includes(id)&&!taxi.includes(id));
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
      const oRoster=(rosters||[]).find(r=>Number(r.roster_id)===Number(om.roster_id)),oOff=new Set([...(oRoster?.reserve||[]),...(oRoster?.taxi||[])].map(String));
      const oOpt=format.bestBall?oLine:optimalUntilLock({slots,line:oLine,pool:(om.players||oRoster?.players||[]).map(String).filter(id=>!oOff.has(id)),player});
      opponent={rosterId:Number(om.roster_id),name:names[om.roster_id],starters:oLine,totals:totals(oLine,oActual),reportedPoints:num(om.points),optimal:{starters:oOpt,totals:totals(oOpt,oActual)}};}
  }
  const om5=opponentMode(pol,input.schedule,week,season,now);
  let winEstimate=null;
  if(opponent){const a=W().FIEDistribution.team(myTotals.parts),bSet=W().FIEDistribution.team(opponent.totals.parts),bOpt=W().FIEDistribution.team(opponent.optimal.totals.parts),b=om5.mode==='optimal'?bOpt:bSet;
    const calibrated=pol.variance?.mode==='calibrated';
    winEstimate={value:W().FIEDistribution.winProbability(a,b),method:'matchup-normal',dot:calibrated?null:'amber',calibrated,note:calibrated?`Estimate — spread calibrated on 2026 Weeks 1–5 (n=${pol.variance?.calibration?.n??'?'}, in-sample; K/D/ST still rule of thumb); normal approximation.`:'Estimate — spread not yet calibrated (WP-V1); likely overconfident.',inputsHash:hash(JSON.stringify([a,b]))};
    winEstimate.mode=om5.mode;winEstimate.asSet=W().FIEDistribution.winProbability(a,bSet);winEstimate.vsOptimal=W().FIEDistribution.winProbability(a,bOpt);
    if(recTotals){const r=W().FIEDistribution.team(recTotals.parts);winEstimate.withRecommended=W().FIEDistribution.winProbability(r,b);winEstimate.withRecommendedAsSet=W().FIEDistribution.winProbability(r,bSet);winEstimate.withRecommendedVsOptimal=W().FIEDistribution.winProbability(r,bOpt);}}
  // Chopped field
  let field=null;
  if(format.chopped){
    const active=(rosters||[]).filter(r=>(r.players||[]).length>0),eliminated=(rosters||[]).filter(r=>!(r.players||[]).length);
    const scored=num(league?.settings?.last_scored_leg)??Math.max(0,(num(league?.settings?.leg)??week)-1);
    const verified=eliminated.length===scored;
    const proj=active.map(r=>{const m=(matchups||[]).find(x=>Number(x.roster_id)===Number(r.roster_id));const act=pid=>num(m?.players_points?.[pid]);
      const line=lineupFrom({slots,starters:(m?.starters||r.starters||[]).map(String),player}),off=new Set([...(r.reserve||[]),...(r.taxi||[])].map(String));
      const isMe=Number(r.roster_id)===Number(managedRosterId),opt=isMe||format.bestBall?line:optimalUntilLock({slots,line,pool:(m?.players||r.players||[]).map(String).filter(id=>!off.has(id)),player});
      return{rosterId:Number(r.roster_id),name:names[r.roster_id],asSet:totals(line,act).projected,optimal:totals(opt,act).projected,starterPids:line.filter(e=>e.pid).map(e=>e.pid)};});
    // Ranking and cut line follow the opponent mode (R5.5): others at their optimal-until-lock lineup early in the week.
    const view=mode=>{const rows=proj.map(x=>({...x,projected:mode==='optimal'?x.optimal:x.asSet}));rows.sort((a,b)=>b.projected-a.projected);rows.forEach((x,i)=>{x.rank=i+1;x.me=x.rosterId===Number(managedRosterId);});
      const me=rows.find(x=>x.me)||null,others=rows.filter(x=>!x.me),cut=others.length?Math.min(...others.map(x=>x.projected)):null;return{rows,myRank:me?.rank??null,cutLine:cut,marginToCut:me&&cut!==null?round(me.projected-cut):null};};
    const vSet=view('asSet'),vOpt=view('optimal');proj.length=0;proj.push(...(om5.mode==='optimal'?vOpt:vSet).rows);
    const cur=om5.mode==='optimal'?vOpt:vSet;
    field={verified,activeCount:active.length,eliminatedCount:eliminated.length,scoredWeeks:scored,rows:proj,eliminated:eliminated.map(r=>({rosterId:Number(r.roster_id),name:names[r.roster_id]})),
      myRank:cur.myRank,cutLine:cur.cutLine,marginToCut:cur.marginToCut,mode:om5.mode,asSet:vSet,optimal:vOpt,meEliminated:!!roster&&!(roster.players||[]).length};
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
    opponent,winEstimate,field,opponentMode:om5,standings:standings(league,rosters,users,managedRosterId,!!format.chopped),nextLock,issues,builtAt:now};
}
window.FIEWeekModel={VERSION,build,tierFor:(g,p)=>tierFor(g,policy(p))};
})();

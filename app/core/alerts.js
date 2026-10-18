/* FIE alerts (UI v10 R1) — UI contract §5.8.
 * Turns WeekModels into actionable items for Overview and League Home.
 * Tiers: urgent > recommended > monitor. Ordering: tier, lock time, league priority, gain.
 * Best Ball leagues never produce lineup tasks (chop risk still applies to Chopped Best Ball).
 * Locked players never produce tasks.
 *
 * Lock time of an item = the earliest kickoff among the players the action touches (a bye or
 * empty slot is open until its replacement's game starts), falling back to the league's next lock.
 *
 * Portfolio grouping (deviation from the R1 guide, documented in UI_CONTRACT §5.8):
 *   · actions (urgent / recommended) are grouped per LEAGUE — the fix happens league by league in
 *     Sleeper, so one row per league with every item in its Expand is the shortest to-do list;
 *   · monitor items (Questionable) are grouped per PLAYER across leagues — it is news to follow.
 */
(function(){
'use strict';
const VERSION='10.1.1';
const TIER={urgent:0,recommended:1,monitor:2};
const PRIORITY={VERY_HIGH:0,HIGH:1,MEDIUM:2,LOW:3};
function fmt(v){const n=Number(v);return Number.isFinite(n)?n.toFixed(1):'–';}
function inactivesAt(kickoff,policy){const m=Number(policy?.status?.inactives_minutes_before_kickoff)||90;return kickoff?kickoff-m*60000:null;}
function earliest(...xs){const v=xs.flat().filter(x=>Number.isFinite(x));return v.length?Math.min(...v):null;}

function forLeague(wm,{leagueId,leagueName,priority='MEDIUM',policy=window.FIE_UI_POLICY}={}){
  const out=[],base={leagueId:String(leagueId||wm?.key?.leagueId||''),leagueName:leagueName||wm?.league?.name||'',priority};
  if(!wm)return out;
  for(const i of wm.issues||[])out.push({...base,code:'DATA_ISSUE',tier:'urgent',quiet:true,title:i.text,lockAt:wm.nextLock,dedupKey:`${base.leagueId}:data:${i.code}`,route:'home'});
  if(wm.field?.meEliminated)return out;
  if(wm.format?.bestBall){chopRisk(wm,base,policy,out);return out;} // automatic lineup: no lineup tasks
  const kick=pid=>pid?wm.player(pid)?.game?.kickoff??null:null;
  const changes=wm.me?.recommended?.changes||[],rec=wm.me?.recommended;
  const changeFor=pid=>changes.find(c=>c.outPid===pid);
  const open=(wm.me?.submitted||[]).filter(e=>!e.p||!e.p.game.locked);
  const emptySlots=open.filter(e=>!e.p).map(e=>e.slot);
  if(emptySlots.length){const fills=changes.filter(c=>!c.outPid);
    out.push({...base,code:'EMPTY_SLOT',tier:'urgent',title:`${emptySlots.length} empty starter slot${emptySlots.length>1?'s':''} (${emptySlots.join(', ')})`,
      detail:fills.length?`Start ${fills.map(c=>`${wm.player(c.inPid)?.name} (${c.slot})`).join(', ')}`:'No eligible player on the bench — check waivers',
      lockAt:earliest(fills.map(c=>kick(c.inPid)))??wm.nextLock,gain:fills.reduce((s,c)=>s+(c.delta||0),0)||null,dedupKey:`${base.leagueId}:empty`,route:'lineup'});}
  for(const e of open){if(!e.p)continue;const s=e.p.status;
    if(s.unavailable){const c=changeFor(e.pid),alt=c?wm.player(c.inPid):null,doubt=s.code==='Doubtful';
      out.push({...base,code:doubt?'STARTER_DOUBTFUL':'STARTER_UNAVAILABLE',tier:'urgent',playerId:e.pid,playerName:e.p.name,status:s.code,
        title:doubt?`${e.p.name} Doubtful — treated as out`:`${e.p.name} can't play (${s.code})`,
        detail:alt?`Start ${alt.name} instead (+${fmt(c.delta)})`:'No eligible replacement on the bench — check waivers',
        lockAt:earliest(e.p.game.kickoff,c?kick(c.inPid):null)??wm.nextLock,inactivesAt:doubt?inactivesAt(e.p.game.kickoff,policy):null,gain:c?.delta??null,dedupKey:`player:${e.pid}:${s.code}`,route:'lineup'});}
    else if(s.monitor)out.push({...base,code:'MONITOR_Q',tier:'monitor',playerId:e.pid,playerName:e.p.name,status:'Questionable',title:`${e.p.name} Questionable`,detail:`Starting at ${e.slot}`,lockAt:e.p.game.kickoff,dedupKey:`player:${e.pid}:Q`,route:'lineup'});
  }
  if(rec&&rec.tier!=='none'&&changes.length){
    const covered=new Set(out.filter(a=>a.playerId).map(a=>a.playerId));
    const swaps=changes.filter(c=>c.outPid&&!covered.has(c.outPid)); // empty-slot fills and status replacements are already listed
    if(swaps.length){const txt=swaps.map(c=>`${wm.player(c.inPid)?.name||c.inPid} over ${wm.player(c.outPid)?.name}`).join('; ');
      // A Questionable player can be recommended (policy: Q = monitor, not out) — say so in the task.
      const q=swaps.map(c=>wm.player(c.inPid)).filter(p=>p?.status?.monitor).map(p=>p.name);
      const gain=swaps.reduce((s,c)=>s+(c.delta||0),0);
      const fb=swaps.map(c=>wm.player(c.inPid)).filter(p=>p?.status?.monitor).map(p=>{const f=(rec.fallbacks||[]).find(x=>x.forPid===p.pid),alt=f?.pid?wm.player(f.pid):null;return `if ${p.name} is out: ${alt?`start ${alt.name}`:'keep current lineup'}`;});
      const detail=`+${fmt(gain)} projected pts`+(q.length?` · ${q.join(', ')} Questionable — confirm before lock (${fb.join('; ')})`:'');
      out.push({...base,code:rec.tier==='close'?'CLOSE_CALL':rec.tier==='urgent'?'SWAP_URGENT':'SWAP',tier:rec.tier==='close'?'monitor':rec.tier,title:`Start ${txt}`,detail,questionable:q,gain,
        lockAt:earliest(swaps.map(c=>[kick(c.inPid),kick(c.outPid)]))??wm.nextLock,dedupKey:`${base.leagueId}:swap`,route:'lineup'});}
  }
  chopRisk(wm,base,policy,out);
  return out;
}
function chopRisk(wm,base,policy,out){
  const f=wm.field;
  if(f&&f.verified&&f.marginToCut!==null&&f.marginToCut<(Number(policy?.escalation?.chopped_cut_margin)||10))
    out.push({...base,code:'CHOP_RISK',tier:'urgent',title:`Chop risk: projected ${f.myRank}/${f.activeCount}, ${fmt(f.marginToCut)} pts above the lowest team`,lockAt:wm.nextLock,dedupKey:`${base.leagueId}:chop`,route:'matchup'});
}
function sort(list){
  return list.slice().sort((a,b)=>(TIER[a.tier]-TIER[b.tier])||((a.lockAt??Infinity)-(b.lockAt??Infinity))||((PRIORITY[a.priority]??2)-(PRIORITY[b.priority]??2))||((b.gain??0)-(a.gain??0)));
}
/** Monitor items of many leagues, one group per player (e.g. "Q in 2 leagues"). */
function portfolio(perLeague){
  const all=perLeague.flat(),groups=new Map(),rest=[];
  for(const a of all){if(a.dedupKey?.startsWith('player:')){if(!groups.has(a.dedupKey))groups.set(a.dedupKey,[]);groups.get(a.dedupKey).push(a);}else rest.push(a);}
  const merged=[...groups.values()].map(xs=>{if(xs.length===1)return xs[0];const first=sort(xs)[0];
    return{...first,grouped:sort(xs),leagueName:`${xs.length} leagues`,title:`${first.playerName} ${first.code==='MONITOR_Q'?'Questionable':first.code==='STARTER_DOUBTFUL'?'Doubtful — treated as out':`can't play (${first.status})`} · starting in ${xs.length} leagues`};});
  return sort([...rest,...merged]);
}
/** Action items (urgent / recommended / close call) of one league folded into one row. */
function leagueTask(alerts){
  const xs=sort(alerts.filter(a=>!a.quiet&&a.code!=='MONITOR_Q'));if(!xs.length)return null;
  const first=xs[0],n=c=>xs.filter(a=>c.includes(a.code)).length;
  const out=n(['STARTER_UNAVAILABLE','STARTER_DOUBTFUL']),empty=xs.find(a=>a.code==='EMPTY_SLOT'),swap=xs.find(a=>['SWAP','SWAP_URGENT','CLOSE_CALL'].includes(a.code)),chop=xs.find(a=>a.code==='CHOP_RISK'),draft=xs.find(a=>a.code==='DRAFT');
  const parts=[out?`${out} starter${out>1?'s':''} can't play`:'',empty?empty.title:'',swap?`${swap.code==='CLOSE_CALL'?'close call':'better lineup'} ${swap.detail.split(' · ')[0]}`:'',chop?'chop risk':'',draft?draft.title:''].filter(Boolean);
  return{...first,code:'LEAGUE_TASKS',tier:first.tier==='monitor'?'monitor':first.tier,close:first.code==='CLOSE_CALL'&&xs.length===1,title:parts.join(' · '),items:xs,lockAt:earliest(xs.map(a=>a.lockAt)),gain:xs.reduce((s,a)=>s+(a.gain||0),0),dedupKey:`${first.leagueId}:tasks`};
}
/** Overview queue: one action row per league + monitor items grouped per player. */
function queue(perLeague){
  const actions=perLeague.map(leagueTask).filter(Boolean);
  const monitor=portfolio(perLeague.map(xs=>xs.filter(a=>a.code==='MONITOR_Q')));
  const quiet=perLeague.flat().filter(a=>a.quiet);
  return{actions:sort(actions),monitor,quiet};
}
window.FIEAlerts={VERSION,forLeague,portfolio,leagueTask,queue,sort};
})();

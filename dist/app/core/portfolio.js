/* FIE portfolio views (UI v10 R2 · WP2.5) — UI contract §4.1 (Overview v2).
 *
 * Pure helpers over the WeekModels of all leagues:
 *   · myPlayers(results)  — cross-league exposure: every player on your rosters, in how many leagues he
 *                           starts / sits / is on IR or taxi, with this week's status and game.
 *   · snapshot(results)   — what the changes feed compares next time (status per rostered player).
 *   · changes(prev, results, txByLeague) — since the previous visit: status changes of your players
 *                           (Urgent when he now can't play and starts somewhere), your processed waiver
 *                           claims (won / failed), trades and free-agent moves on your rosters.
 * The previous snapshot lives in the browser (localStorage) — a convenience, not shared state.
 */
(function(){
'use strict';
const VERSION='10.5.0';
function myPlayers(results){
  const by=new Map(),fieldOnly=new Map();
  for(const r of results||[]){const wm=r?.wm;if(!wm||wm.field?.meEliminated)continue;
    const add=(p,role,slot)=>{if(!p)return;const x=by.get(p.pid)||{pid:p.pid,name:p.name,position:p.position,team:p.team,status:p.status,game:p.game,leagues:[]};
      x.leagues.push({leagueId:wm.key.leagueId,leagueName:wm.entry?.name||wm.league.name,role,slot,value:role==='start'?(p.status?.unavailable?0:p.active?.value):p.active?.value,bestBall:!!wm.format?.bestBall});by.set(p.pid,x);};
    const started=new Set();for(const e of wm.me.submitted)if(e.p){add(e.p,'start',e.slot);started.add(e.pid);}
    for(const p of wm.me.bench)if(!started.has(p.pid))add(p,'bench','BN');
    for(const p of wm.me.reserve)add(p,'IR','IR');for(const p of wm.me.taxi)add(p,'taxi','TAXI');
    // R5.3 · Exposure: the H2H opponent's submitted starters ("started vs me", also for players I don't roster) and, in
    // chopped leagues, how many other active teams start the player (counted only for players listed anyway).
    for(const e of wm.opponent?.starters||[])if(e.p)add(e.p,'vs',e.slot);
    if(wm.field)for(const fr of wm.field.rows||[])if(!fr.me)for(const pid of fr.starterPids||[]){const x=by.get(pid);if(x)(x.fieldStarts=(x.fieldStarts||0)+1);else fieldOnly.set(pid,(fieldOnly.get(pid)||0)+1);}}
  for(const [pid,n] of fieldOnly){const x=by.get(pid);if(x)x.fieldStarts=(x.fieldStarts||0)+n;}
  const rows=[...by.values()].map(x=>{const starts=x.leagues.filter(l=>l.role==='start').length,vs=x.leagues.filter(l=>l.role==='vs').length;return{...x,starts,vs,fieldStarts:x.fieldStarts||0,net:starts-vs,rostered:x.leagues.filter(l=>l.role!=='vs').length};});
  rows.sort((a,b)=>(b.starts-a.starts)||(b.rostered-a.rostered)||String(a.name).localeCompare(String(b.name)));
  return{rows,players:rows.filter(r=>r.rostered).length,startSlots:rows.reduce((s,r)=>s+r.starts,0),unavailableStarters:rows.filter(r=>r.starts&&r.status?.unavailable),vsSlots:rows.reduce((s,r)=>s+r.vs,0)};
}
function snapshot(results,now=Date.now()){
  const statuses={};for(const x of myPlayers(results).rows)if(x.rostered)statuses[x.pid]=x.status?.code||null;
  return{schema:1,at:now,statuses};
}
const TX_LABEL={waiver:'Waiver',free_agent:'Free agent',trade:'Trade',commissioner:'Commissioner'};
function changes(prev,results,txByLeague={},{now=Date.now(),names={}}={}){
  if(!prev||!prev.at)return{firstVisit:true,since:null,items:[]};
  const items=[],mp=myPlayers(results);
  for(const x of mp.rows){if(!x.rostered)continue;const before=prev.statuses?.[x.pid],after=x.status?.code||null;
    // BYE is a schedule fact of one week, not an availability change (bye starters are already Urgent in To do).
    if(before===undefined||before===after||before==='BYE'||after==='BYE')continue;
    const urgent=!!x.status?.unavailable&&x.starts>0;
    items.push({kind:'status',tier:urgent?'urgent':after==='Questionable'?'monitor':'info',pid:x.pid,name:x.name,from:before||'Active',to:after||'Active',starts:x.starts,rostered:x.rostered,
      text:`${x.name}: ${before||'Active'} → ${after||'Active'}${x.starts?` · starting in ${x.starts} league${x.starts>1?'s':''}`:''}`,at:null});}
  for(const r of results||[]){const wm=r?.wm;if(!wm)continue;const lid=wm.key.leagueId,rid=Number(wm.key.rosterId);
    for(const t of txByLeague[lid]||[]){const at=Number(t.status_updated||t.created)||0;if(at<=prev.at)continue;
      if(!(t.roster_ids||[]).map(Number).includes(rid))continue;
      const nm=pid=>names[pid]||wm.player(pid)?.name||pid;
      const mineAdds=Object.entries(t.adds||{}).filter(([,r])=>Number(r)===rid).map(([p])=>nm(p)),mineDrops=Object.entries(t.drops||{}).filter(([,r])=>Number(r)===rid).map(([p])=>nm(p));
      const bid=t.settings?.waiver_bid;
      let text;if(t.type==='waiver')text=t.status==='complete'?`Waiver won: ${mineAdds.join(', ')||'–'}${bid?` ($${bid})`:''}${mineDrops.length?` · dropped ${mineDrops.join(', ')}`:''}`:`Waiver claim ${t.status}: ${Object.keys(t.adds||{}).map(nm).join(', ')}`;
      else if(t.type==='trade')text=`Trade ${t.status}: received ${mineAdds.join(', ')||'–'} · sent ${mineDrops.join(', ')||'–'}`;
      else text=`${TX_LABEL[t.type]||t.type}: ${mineAdds.length?'added '+mineAdds.join(', '):''}${mineAdds.length&&mineDrops.length?' · ':''}${mineDrops.length?'dropped '+mineDrops.join(', '):''}`;
      items.push({kind:'tx',tier:t.type==='waiver'&&t.status!=='complete'?'monitor':'info',leagueId:lid,leagueName:wm.entry?.name||wm.league.name,text,at});}}
  const rank={urgent:0,monitor:1,info:2};
  items.sort((a,b)=>(rank[a.tier]-rank[b.tier])||((b.at||0)-(a.at||0)));
  return{firstVisit:false,since:prev.at,items};
}
window.FIEPortfolioViews={VERSION,myPlayers,snapshot,changes};
})();

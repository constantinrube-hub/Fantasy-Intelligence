/* FIE trade evaluation (UI v10 R3 · WP3.4) — UI contract §7.2.
 *
 * Pure: the effect of a proposed player trade on BOTH teams' optimal legal lineups, per week of the waiver horizon
 * (this week = WeekModel values after status policy; later weeks = Sleeper's projection for that week, byes from the
 * schedule — the same values as Lineup, Waivers and Team), plus a "season rate" effect (Sleeper season projection in
 * league scoring ÷ games, optimal lineup per game; D/ST excluded because bucket scoring cannot be applied to season
 * totals). No value model, no fairness score: the asset view is Sleeper's market ADP, labelled as such.
 *
 *   evaluate({wm, rosters, partnerRosterId, send:[pid], receive:[pid], horizon, schedule, catalog, season,
 *             seasonRows, adp, constraints, now})
 *   → {weeks, me:{before, after, delta, horizonDelta, rateBefore, rateAfter, rateDelta}, partner:{…}, locked, roster, issues, assets}
 *
 * Rules: reserve/taxi players stay out of lineups (they cannot start); a player whose game has started this week is
 * locked — if any traded player is locked, this week is not counted. Roster size after the trade: the number of
 * drops needed is reported (lineups assume the weakest bench players go). League rules: entry-class floor and the
 * legacy cap are checked for the players each side receives.
 */
(function(){
'use strict';
const VERSION='10.3.0';
const W=()=>window;
function num(v){if(v===null||v===undefined||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round(v,d=2){const n=num(v);return n===null?null:Math.round(n*10**d)/10**d;}
const isTeamCode=pid=>/^[A-Z]{2,3}$/.test(String(pid||''));

function evaluate(input){
  const {wm,rosters,partnerRosterId,schedule,season,now=Date.now()}=input,O=W().FIECore.LineupOptimizer,slots=wm.slots;
  const send=(input.send||[]).map(String),receive=(input.receive||[]).map(String),issues=[];
  const mine=(rosters||[]).find(r=>Number(r.roster_id)===Number(wm.key.rosterId)),them=(rosters||[]).find(r=>Number(r.roster_id)===Number(partnerRosterId));
  if(!mine||!them)return{VERSION,issues:['Team not found.'],weeks:[]};
  const off=r=>new Set([...(r.reserve||[]),...(r.taxi||[])].map(String)),offMe=off(mine),offThem=off(them);
  const activeOf=(r,o)=>(r.players||[]).map(String).filter(id=>!o.has(id));
  for(const id of send)if(!(mine.players||[]).map(String).includes(id))issues.push(`${wm.player(id)?.name||id} is not on your roster.`);
  for(const id of receive)if(!(them.players||[]).map(String).includes(id))issues.push(`${wm.player(id)?.name||id} is not on their roster.`);
  // A traded player sitting in reserve/taxi arrives on the active roster of the other team (Sleeper moves him there).
  const meBefore=activeOf(mine,offMe),themBefore=activeOf(them,offThem);
  const meAfter=[...meBefore.filter(id=>!send.includes(id)),...receive],themAfter=[...themBefore.filter(id=>!receive.includes(id)),...send];
  // Horizon values
  const horizon=input.horizon||[],cur=horizon.length&&horizon[0].week===wm.key.week;
  const valuers=horizon.map((h,k)=>k===0&&cur?null:W().FIEWaivers.futureValuer({projRows:h.projRows,scoring:wm.league.scoring,schedule,week:h.week,season,now,catalog:input.catalog,longTermOut:()=>false}));
  const published=horizon.map(h=>!!h.projRows&&h.projRows.size>0);
  const locked=[...send,...receive].filter(id=>wm.player(id)?.game?.locked).map(id=>wm.player(id)?.name||id);
  const counted=horizon.map((_,k)=>published[k]&&!(k===0&&cur&&locked.length));
  const val=(k,pid)=>{if(k===0&&cur){const p=wm.player(pid);return p?p.recValue||0:0;}return valuers[k]?.(pid)?.value??0;};
  const mk=(pid,v)=>{const p=wm.player(pid);return p?{pid:String(pid),sleeperId:String(pid),player_id:String(pid),position:p.position,v}:null;};
  const total=(ids,vf)=>O.optimize(ids.map(id=>mk(id,vf(id))).filter(Boolean),slots,p=>p.v).total;
  const side=(before,after)=>{const b=horizon.map((_,k)=>counted[k]?round(total(before,pid=>val(k,pid))):null),a=horizon.map((_,k)=>counted[k]?round(total(after,pid=>val(k,pid))):null);
    const d=b.map((x,k)=>x===null?null:round(a[k]-x));return{before:b,after:a,delta:d,horizonDelta:round(d.reduce((s,x)=>s+(x??0),0))};};
  // Season rate: Sleeper season projection in league scoring ÷ games (none for D/ST), optimal lineup per game.
  const rate=pid=>{const p=wm.player(pid);if(!p||p.position==='DEF'||isTeamCode(pid))return 0;const r=input.seasonRows?.get?.(String(pid));
    if(!r?.stats||!Object.keys(r.stats).some(k=>!/^(adp|pos_adp|gp)/.test(k)))return 0;const t=W().FIEScoringCore.score(r.stats,wm.league.scoring,p.position);return t===null?0:t/(num(r.stats.gp)||17);};
  const rated=ids=>ids.every(id=>wm.player(id)?.position==='DEF'||rate(id)>0);
  const me=side(meBefore,meAfter),partner=side(themBefore,themAfter);
  for(const [s,b,a] of [[me,meBefore,meAfter],[partner,themBefore,themAfter]]){s.rateBefore=round(total(b,rate));s.rateAfter=round(total(a,rate));s.rateDelta=round(s.rateAfter-s.rateBefore);}
  // Roster size and league rules
  const rp=(input.rosterPositions||[]).filter(x=>!['IR','TAXI','RES'].includes(String(x).toUpperCase())).length||null;
  const drops=(before,after)=>rp===null?0:Math.max(0,after.length-Math.max(rp,before.length));
  const roster={meDrops:drops(meBefore,meAfter),partnerDrops:drops(themBefore,themAfter),limit:rp};
  const cons=input.constraints||[],floor=cons.find(c=>c.type==='nfl_entry_cohort_floor'),legacyC=cons.find(c=>c.type==='cohort_floor_with_legacy_cap');
  const entryOf=pid=>{const c=input.catalog?.get?.(String(pid));const y=num(c?.years_exp);return y===null?null:Number(season)-y;};
  if(floor)for(const id of [...receive,...send]){const e=entryOf(id);if(e===null||e<Number(floor.minimum_entry_season))issues.push(`${wm.player(id)?.name||id}: NFL entry class ${e??'?'} is below this league's floor (${floor.minimum_entry_season}).`);}
  if(legacyC){const cap=num(legacyC.legacy_cap_by_season?.[String(season)])??num(legacyC.legacy_cap_after_2030),max=Number(legacyC.legacy_entry_season_max??Number(legacyC.unlimited_entry_season_min)-1);
    const isLegacy=pid=>{const e=entryOf(pid);return e===null||e<=max;};
    if(cap!==null)for(const [who,r,inn,out] of [['You',mine,receive,send],['They',them,send,receive]]){const n=(r.players||[]).map(String).filter(id=>!out.includes(id)).filter(isLegacy).length+inn.filter(isLegacy).length;if(n>cap)issues.push(`${who} would hold ${n} legacy players (cap ${cap}).`);}}
  const sf=slots.some(s=>/SUPER/.test(s));
  const adpOf=pid=>{const a=input.adp?.get?.(String(pid));if(!a)return null;return wm.format?.dynasty?(num(sf?a.dynasty2qb:a.dynasty)??num(a.dynasty)):num(a.redraft);};
  const asset=pid=>{const p=wm.player(pid),c=input.catalog?.get?.(String(pid));return{pid,name:p?.name||pid,position:p?.position||'',team:p?.team||null,status:p?.status||null,adp:adpOf(pid),rate:round(rate(pid)),age:num(c?.age),entry:entryOf(pid),values:horizon.map((_,k)=>published[k]?round(val(k,pid)):null)};};
  if(locked.length)issues.push(`${locked.join(', ')} already played this week — Week ${wm.key.week} is not counted.`);
  return{VERSION,weeks:horizon.map(h=>h.week),counted,published,me,partner,locked,roster,issues,
    assets:{send:send.map(asset),receive:receive.map(asset)},rateComplete:rated([...send,...receive])};
}
window.FIETrades={VERSION,evaluate};
})();

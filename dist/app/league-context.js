/* FIE 9.3 authoritative league capability + preferred-owner context.
 * Converts Sleeper roster positions into one reusable capability object and
 * resolves the configured Sleeper username to the owned roster ID.
 */
(function(){
'use strict';
const VERSION='9.3-league-context';
const DEFAULT_USERNAME='C0nstant1n';
const S=()=>window.state||(typeof state!=='undefined'?state:null);
function canonical(p){return window.FIECore?.PositionRegistry?.canonical?.(p)||String(p||'').toUpperCase();}
function starterSlots(league){return window.FIECore?.PositionRegistry?.starterSlots?.(league?.roster_positions||[])||[];}
function legalPositions(league){const set=window.FIECore?.PositionRegistry?.rosterablePositions?.(league?.roster_positions||[])||new Set();return [...set];}
function profileFormat(){try{return String(window.activeFormatKey?.()||window.FIELeagueProfileResolver?.resolveFor?.(S()?.league)?.format||'REDRAFT');}catch{return'REDRAFT';}}
function build(league=S()?.league){
  if(!league)return null;
  const slots=(league.roster_positions||[]).map(String),starts=starterSlots(league),legal=legalPositions(league),counts={};
  for(const s of starts)counts[s]=(counts[s]||0)+1;
  const legalSet=new Set(legal.map(canonical)),fmt=profileFormat();
  return Object.freeze({
    version:VERSION,leagueId:String(league.league_id||''),format:fmt,teamCount:Number(league.total_rosters||S()?.rosters?.length||0),
    rosterSlots:slots,starterSlots:starts,starterSlotCounts:counts,legalPositions:legal,
    hasQB:legalSet.has('QB'),hasRB:legalSet.has('RB'),hasWR:legalSet.has('WR'),hasTE:legalSet.has('TE'),
    hasK:legalSet.has('K'),hasDST:legalSet.has('DEF'),hasIDP:['DL','LB','DB','EDGE','IDL','CB','S'].some(x=>legalSet.has(canonical(x))),
    hasDL:['DL','EDGE','IDL'].some(x=>legalSet.has(canonical(x))),hasLB:legalSet.has('LB'),hasDB:['DB','CB','S'].some(x=>legalSet.has(canonical(x))),
    hasSuperflex:slots.some(x=>['SUPER_FLEX','SF'].includes(String(x).toUpperCase()))||starts.filter(x=>String(x).toUpperCase()==='QB').length>=2,
    isDynasty:fmt.includes('DYNASTY'),isBestBall:fmt.includes('BESTBALL'),isChopped:fmt==='CHOPPED'
  });
}
function username(){return String(window.FIEPortfolioConfig?.config?.sleeper_username||DEFAULT_USERNAME);}
function rosterForUsername(name=username()){
  const target=String(name||'').trim().toLowerCase();if(!target)return null;
  const users=S()?.users||[],u=users.find(x=>[x?.username,x?.display_name].some(v=>String(v||'').trim().toLowerCase()===target));
  if(!u)return null;const r=(S()?.rosters||[]).find(x=>String(x.owner_id||'')===String(u.user_id||''));
  return r?{user:u,roster:r,rosterId:Number(r.roster_id)}:null;
}
function syncPickers(rosterId){
  if(!Number.isFinite(Number(rosterId)))return false;if(S())S().selectedRoster=Number(rosterId);
  for(const id of ['rosterPicker','weeklyRosterPicker','teamRosterPicker','draftRosterPicker','tradeRosterA']){const el=document.getElementById(id);if(el&&[...el.options].some(o=>Number(o.value)===Number(rosterId)))el.value=String(rosterId);}
  return true;
}
function selectPreferredRoster(){const found=rosterForUsername();if(!found)return null;syncPickers(found.rosterId);try{window.populateIntelligencePickers?.();}catch{}return found;}
function positionAllowed(position,league=S()?.league){const c=build(league);if(!c)return false;return new Set(c.legalPositions.map(canonical)).has(canonical(position));}
const API={VERSION,build,current:()=>build(),username,rosterForUsername,selectPreferredRoster,syncPickers,positionAllowed};
window.FIELeagueContext=API;
window.addEventListener?.('fie:league-loaded',e=>{if(e?.detail?.stage!=='core')return;const f=selectPreferredRoster();if(f){try{window.render?.();}catch{}}});
})();

/* FIE player availability status — UI contract §5.4 (docs/current/UI_CONTRACT.md).
 *
 * One owner for "can this player score this week?" used by recommendations,
 * alerts and waiver actions. It does not change projections; it decides how a
 * projection may be used in a recommendation.
 *
 * Status source order (user decision F1, 2026-10-18):
 *   1. Sleeper weekly projection feed `player.injury_status` for the selected
 *      league week (edge cache 15 min) — recorded on each player as
 *      `weeklyStatusFeed` by app/v9.3.3-runtime-integrity.js.
 *   2. Sleeper player database `injury_status` (edge cache 24 h) — `injuryStatus`.
 *   3. Verified schedule bye → BYE.
 *
 * Policy (config/ui-decision-policy.json › status):
 *   - zero-valued statuses (Doubtful, Out, IR, Suspended, PUP, NA, BYE) score 0
 *     in recommendations; Doubtful keeps a tiny tie-break so a Doubtful player
 *     still beats an empty slot or another zero.
 *   - monitor statuses (Questionable) keep their projection.
 *   - an unavailable free agent is never a CLAIM; dynasty leagues may label it
 *     STASH when a legal reserve (IR) slot is free.
 */
(function(){
'use strict';
const VERSION='10.0.0-r0';
const DEFAULTS=Object.freeze({
  zero:['Doubtful','Out','IR','Suspended','PUP','NA','BYE'],
  monitor:['Questionable'],
  doubtful_tiebreak_factor:0.01,
  projection_feed_max_age_minutes:720,
  waiver_add_policy:{unavailable_action:'WATCH',dynasty_stash_action:'STASH',never_claim_unavailable:true}
});
const ALIASES={
  q:'Questionable',questionable:'Questionable',gtd:'Questionable',
  d:'Doubtful',doubtful:'Doubtful',
  o:'Out',out:'Out',cov:'Out',covid:'Out',dnr:'Out',
  ir:'IR','injured reserve':'IR',
  sus:'Suspended',susp:'Suspended',suspended:'Suspended',
  pup:'PUP',na:'NA',
  bye:'BYE'
};
const SHORT={Questionable:'Q',Doubtful:'D',Out:'O',IR:'IR',Suspended:'SUS',PUP:'PUP',NA:'NA',BYE:'BYE'};

function policy(){const p=window.FIE_UI_POLICY?.status||{};return Object.assign({},DEFAULTS,p,{waiver_add_policy:Object.assign({},DEFAULTS.waiver_add_policy,p.waiver_add_policy||{})});}
function normalize(raw){
  if(raw===null||raw===undefined)return null;
  const s=String(raw).trim();if(!s)return null;
  return ALIASES[s.toLowerCase()]||s;
}
function finite(v){const n=Number(v);return v===null||v===undefined||v===''||!Number.isFinite(n)?null:n;}
function context(ctx={}){
  const week=finite(ctx.week)??finite(window.currentWeek?.())??finite(window.state?.weekly?.week);
  const season=finite(ctx.season)??finite(window.FIECore?.SeasonResolver?.resolve?.())??finite(window.state?.league?.season);
  return{week,season,now:finite(ctx.now)??Date.now()};
}
/** Resolve the effective status of player `p` for the selected (or given) week. */
function resolve(p,ctx={}){
  const c=context(ctx),pol=policy();
  let code=null,source='none',ageMinutes=null;
  const feed=p?.weeklyStatusFeed||null;
  const feedFresh=feed&&Number(feed.week)===Number(c.week)&&Number(feed.season)===Number(c.season)&&
    (finite(feed.at)===null||(c.now-Number(feed.at))/60000<=pol.projection_feed_max_age_minutes);
  if(feedFresh){code=normalize(feed.status);source='projection-feed';ageMinutes=finite(feed.at)===null?null:Math.max(0,Math.round((c.now-Number(feed.at))/60000));}
  else if(normalize(p?.injuryStatus)){code=normalize(p.injuryStatus);source='player-db';}
  if(!code){try{if(c.week!==null&&c.season!==null&&window.FIEProjectionResolver?.isVerifiedBye?.(p,c.week,c.season)){code='BYE';source='schedule';}}catch{}}
  const unavailable=!!code&&pol.zero.includes(code);
  const monitor=!!code&&!unavailable&&pol.monitor.includes(code);
  return{code,short:code?(SHORT[code]||code):null,label:code||'Active',source,ageMinutes,unavailable,monitor,week:c.week,season:c.season};
}
/** Value a player may carry in a recommendation (projection after status policy). */
function recommendationValue(p,value,ctx={}){
  const v=finite(value);if(v===null)return null;
  const s=resolve(p,ctx);if(!s.unavailable)return v;
  return s.code==='Doubtful'?v*policy().doubtful_tiebreak_factor:0;
}
/** Sleeper reserve (IR) eligibility for a status under the league's reserve settings. */
function irEligible(code,settings={}){
  const c=normalize(code);if(!c)return false;
  if(c==='IR'||c==='PUP')return true;
  if(c==='Out')return Number(settings.reserve_allow_out)===1;
  if(c==='Doubtful')return Number(settings.reserve_allow_doubtful)===1;
  if(c==='Suspended')return Number(settings.reserve_allow_sus)===1;
  if(c==='NA')return Number(settings.reserve_allow_na)===1;
  return false;
}
function freeReserveSlots(roster,settings={}){
  const slots=finite(settings.reserve_slots)??0;
  return Math.max(0,slots-((roster?.reserve)||[]).filter(Boolean).length);
}
/**
 * Waiver add policy for one candidate.
 * Returns { allowClaim, action:null|'WATCH'|'STASH', status, reason }.
 * `action` is null when the candidate is available (caller keeps its own action).
 */
function addPolicy(p,{rosterId=window.state?.selectedRoster,league=window.state?.league,rosters=window.state?.rosters,dynasty}={}){
  const s=resolve(p),pol=policy().waiver_add_policy;
  if(!s.unavailable||s.code==='BYE')return{allowClaim:true,action:null,status:s,reason:null};
  const roster=(rosters||[]).find(r=>Number(r.roster_id)===Number(rosterId))||null,settings=league?.settings||{};
  let isDynasty=dynasty;if(isDynasty===undefined){try{isDynasty=!!window.formatProfile?.()?.dynasty;}catch{isDynasty=false;}}
  const legalStash=irEligible(s.code,settings)&&freeReserveSlots(roster,settings)>0;
  if(isDynasty&&legalStash)return{allowClaim:false,action:pol.dynasty_stash_action,status:s,reason:`${s.code}: reserve (IR) slot free — stash only`};
  return{allowClaim:false,action:pol.unavailable_action,status:s,reason:`${s.code}: cannot play${legalStash?'':'; no legal reserve slot'}`};
}
window.FIEStatus={VERSION,policy,normalize,resolve,recommendationValue,irEligible,freeReserveSlots,addPolicy};
})();

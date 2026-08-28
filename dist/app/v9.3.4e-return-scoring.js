/* Fantasy Intelligence Engine V9.3.4E · return scoring audit and decomposition.
 *
 * Verified runtime keys supported here:
 *   player yards: kr_yd, pr_yd
 *   player TDs:   kr_td / pr_td, with st_td aggregate fallback
 *   team/DST TDs: def_kr_td / def_pr_td, with def_st_td aggregate fallback
 * Verified nflverse player-stat yard fields:
 *   kickoff_returns, kickoff_return_yards, punt_returns, punt_return_yards
 *
 * The public-stat wrapper is counterfactual: it compares the legacy scorer on
 * the real row with the same row after return fields are zeroed. It therefore
 * adds only the missing return component, preserving already-complete legacy
 * scoring and avoiding double counting.
 */
(function(){
'use strict';
if(window.FIE934E?.installed)return;

const VERSION='9.3.4E';
const RELEASE='return-scoring-audit-no-double-count';
const INSTALL_LIMIT=120;
const RETURN_FIELDS={
  kickoffYards:['kickoff_return_yards','kr_yds','kick_return_yards'],
  puntYards:['punt_return_yards','pr_yds'],
  kickoffReturns:['kickoff_returns','kr'],
  puntReturns:['punt_returns','pr'],
  kickoffTDs:['kickoff_return_tds','kickoff_return_touchdowns','kr_td'],
  puntTDs:['punt_return_tds','punt_return_touchdowns','pr_td'],
  specialTeamsTDs:['special_teams_tds']
};
const PROJECTION_FIELDS={
  kickoffYards:['projected_kickoff_return_yards','kickoff_return_yards_projection','kickoffReturnYardsProjection'],
  puntYards:['projected_punt_return_yards','punt_return_yards_projection','puntReturnYardsProjection'],
  kickoffTDs:['projected_kickoff_return_tds','kickoff_return_tds_projection','kickoffReturnTdsProjection'],
  puntTDs:['projected_punt_return_tds','punt_return_tds_projection','puntReturnTdsProjection'],
  specialTeamsTDs:['projected_special_teams_tds','special_teams_tds_projection','specialTeamsTdsProjection']
};
let installAttempts=0;
let legacyScorePublicStats=null;
let auditTimer=null;
let wrapped=false;

const diagnostics={
  installs:0,
  publicRowsAudited:0,
  playersWithActualReturnData:0,
  playersWithReturnProjectionData:0,
  legacyAlreadyComplete:0,
  legacyMissingCompleted:0,
  legacyPartialCompleted:0,
  ambiguousLegacyRows:0,
  aggregateTdAmbiguousRows:0,
  specificTdOverrides:0,
  aggregateTdFallbacks:0,
  doubleCountPrevented:0,
  projectionAdjustmentsAvailable:0,
  projectionAdjustmentsApplied:0,
  totalAddedPublicPoints:0,
  scoringKeys:{},
  dstWeights:{},
  projectionCoverage:null,
  lastAuditMs:null,
  errors:[]
};

function now(){return typeof performance!=='undefined'&&performance.now?performance.now():Date.now();}
function stateObj(){try{return window.state||(typeof state!=='undefined'?state:null);}catch{return window.state||null;}}
function players(){try{return Array.isArray(PLAYERS)?PLAYERS:(Array.isArray(window.PLAYERS)?window.PLAYERS:[]);}catch{return Array.isArray(window.PLAYERS)?window.PLAYERS:[];}}
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function round3(v){const n=finite(v);return n===null?null:Math.round(n*1000)/1000;}
function leagueId(){const s=stateObj();return String(s?.league?.league_id||s?.activeLeagueId||'');}
function recordError(e,where){diagnostics.errors.push({at:new Date().toISOString(),where,message:String(e?.message||e)});if(diagnostics.errors.length>20)diagnostics.errors.shift();try{window.FIECore?.Diagnostics?.capture?.(e,{domain:'v9.3.4e',feature:where});}catch{}}
function perf(name,ms,meta={}){try{window.FIEPerformance?.push?.(`934e:${name}`,ms,{leagueId:leagueId(),...meta});}catch{}}
function ownFinite(row,key){if(!row||!Object.prototype.hasOwnProperty.call(row,key))return null;return finite(row[key]);}
function firstField(row,keys){for(const key of keys||[]){const v=ownFinite(row,key);if(v!==null)return{key,value:v};}return{key:null,value:null};}
function firstNestedProjection(p,keys){
  for(const key of keys||[]){const v=finite(p?.[key]);if(v!==null)return{key,value:v};}
  for(const rootName of ['projection_components','projectionComponents','weekly_projection_components','weeklyProjectionComponents']){const root=p?.[rootName];if(!root||typeof root!=='object')continue;for(const key of keys||[]){const bare=key.replace(/^projected_/,'').replace(/_projection$/,'');for(const k of [key,bare]){const v=finite(root?.[k]);if(v!==null)return{key:`${rootName}.${k}`,value:v};}}}
  return{key:null,value:null};
}
function scoringSettings(){
  const s=stateObj();return s?.league?.scoring_settings||s?.scoring_settings||s?.scoringSettings||s?.research?.scoring_settings||{};
}
function weight(settings,key){const n=finite(settings?.[key]);return n===null?0:n;}
function tdWeight(settings,specific,aggregate,{team=false}={}){
  const specificValue=weight(settings,specific),aggregateValue=weight(settings,aggregate);
  if(specificValue!==0)return{value:specificValue,source:specific,team,preventedDoubleCount:aggregateValue!==0};
  if(aggregateValue!==0)return{value:aggregateValue,source:aggregate,team,preventedDoubleCount:false};
  return{value:0,source:specific,team,preventedDoubleCount:false};
}
function scoringAudit(settings=scoringSettings()){
  const player={krYd:weight(settings,'kr_yd'),prYd:weight(settings,'pr_yd'),krTd:tdWeight(settings,'kr_td','st_td'),prTd:tdWeight(settings,'pr_td','st_td')};
  const dst={krTd:tdWeight(settings,'def_kr_td','def_st_td',{team:true}),prTd:tdWeight(settings,'def_pr_td','def_st_td',{team:true}),returnYardScoring:null,returnYardReason:'No verified Sleeper DST return-yard scoring key is assumed.'};
  const weights=[player.krTd,player.prTd,dst.krTd,dst.prTd];diagnostics.specificTdOverrides=weights.filter(x=>x.value!==0&&x.source&&!x.source.endsWith('st_td')).length;diagnostics.aggregateTdFallbacks=weights.filter(x=>x.value!==0&&x.source?.endsWith('st_td')&&!['kr_td','pr_td','def_kr_td','def_pr_td'].includes(x.source)).length;diagnostics.doubleCountPrevented=weights.filter(x=>x.preventedDoubleCount).length;
  diagnostics.scoringKeys={kr_yd:player.krYd,pr_yd:player.prYd,kr_td:player.krTd.value,kr_td_source:player.krTd.source,pr_td:player.prTd.value,pr_td_source:player.prTd.source,st_td:weight(settings,'st_td')};
  diagnostics.dstWeights={def_kr_td:dst.krTd.value,def_kr_td_source:dst.krTd.source,def_pr_td:dst.prTd.value,def_pr_td_source:dst.prTd.source,def_st_td:weight(settings,'def_st_td'),returnYardScoring:null};
  return{player,dst};
}
function scoreReturnRow(row,settings=scoringSettings()){
  const audit=scoringAudit(settings),ky=firstField(row,RETURN_FIELDS.kickoffYards),py=firstField(row,RETURN_FIELDS.puntYards),kt=firstField(row,RETURN_FIELDS.kickoffTDs),pt=firstField(row,RETURN_FIELDS.puntTDs),st=firstField(row,RETURN_FIELDS.specialTeamsTDs),has=[ky,py,kt,pt,st].some(x=>x.value!==null);
  if(!has)return{available:false,points:null,kickoffYards:ky.value,puntYards:py.value,kickoffTDs:kt.value,puntTDs:pt.value,specialTeamsTDs:st.value,components:{},sourceFields:{kickoffYards:ky.key,puntYards:py.key,kickoffTDs:kt.key,puntTDs:pt.key,specialTeamsTDs:st.key}};
  const components={kickoffYards:ky.value===null?null:ky.value*audit.player.krYd,puntYards:py.value===null?null:py.value*audit.player.prYd,kickoffTDs:null,puntTDs:null,specialTeamsTDs:null};
  let aggregateTdMode=null;
  if(st.value!==null&&Math.abs(audit.player.krTd.value-audit.player.prTd.value)<1e-9){components.specialTeamsTDs=st.value*audit.player.krTd.value;aggregateTdMode='safe-equal-weight aggregate';}
  else{components.kickoffTDs=kt.value===null?null:kt.value*audit.player.krTd.value;components.puntTDs=pt.value===null?null:pt.value*audit.player.prTd.value;if(st.value!==null){const known=(kt.value||0)+(pt.value||0);if(st.value>known){aggregateTdMode='ambiguous aggregate remainder not scored';diagnostics.aggregateTdAmbiguousRows++;}}}
  const vals=Object.values(components).filter(v=>v!==null&&Number.isFinite(Number(v))),points=vals.reduce((a,b)=>a+Number(b),0);
  return{available:true,points:round3(points),kickoffYards:ky.value,puntYards:py.value,kickoffTDs:kt.value,puntTDs:pt.value,specialTeamsTDs:st.value,aggregateTdMode,components:Object.fromEntries(Object.entries(components).map(([k,v])=>[k,round3(v)])),sourceFields:{kickoffYards:ky.key,puntYards:py.key,kickoffTDs:kt.key,puntTDs:pt.key,specialTeamsTDs:st.key},weights:{kr_yd:audit.player.krYd,pr_yd:audit.player.prYd,kr_td:audit.player.krTd.value,kr_td_source:audit.player.krTd.source,pr_td:audit.player.prTd.value,pr_td_source:audit.player.prTd.source}};
}
function zeroReturnRow(row){const copy={...(row||{})};for(const keys of Object.values(RETURN_FIELDS))for(const key of keys)if(Object.prototype.hasOwnProperty.call(copy,key))copy[key]=0;return copy;}
function completionDecision(base,zero,expected){
  const b=finite(base),z=finite(zero),e=finite(expected);if(b===null||z===null||e===null)return{mode:'unavailable',result:b,legacyDelta:null,added:0};
  const delta=b-z,tol=Math.max(.05,Math.abs(e)*.02);if(Math.abs(delta-e)<=tol)return{mode:'already-complete',result:b,legacyDelta:delta,added:0};
  if(Math.abs(delta)<=tol)return{mode:'missing-completed',result:b+e,legacyDelta:delta,added:e};
  const sameDirection=(e===0)||Math.sign(delta)===Math.sign(e);if(sameDirection&&Math.abs(delta)<=Math.abs(e)+tol){const missing=e-delta;return{mode:'partial-completed',result:b+missing,legacyDelta:delta,added:missing};}
  return{mode:'ambiguous-fail-closed',result:b,legacyDelta:delta,added:0};
}
function wrapPublicStats(){
  if(wrapped)return true;const original=window.scorePublicStats;if(typeof original!=='function')return false;legacyScorePublicStats=original;
  const wrappedFn=function(row,p){
    const base=original.apply(this,arguments);let expected=null,zero=null,decision={mode:'unavailable',result:base,legacyDelta:null,added:0};
    try{const dec=scoreReturnRow(row);expected=dec.points;if(dec.available){zero=original.call(this,zeroReturnRow(row),p);decision=completionDecision(base,zero,expected);diagnostics.publicRowsAudited++;if(p){p.returnScoring={version:VERSION,leagueId:leagueId(),actual:dec,legacyFantasyPoints:round3(base),legacyWithoutReturns:round3(zero),legacyReturnDelta:round3(decision.legacyDelta),addedReturnPoints:round3(decision.added),completedFantasyPoints:round3(decision.result),completionMode:decision.mode};}if(decision.mode==='already-complete')diagnostics.legacyAlreadyComplete++;else if(decision.mode==='missing-completed')diagnostics.legacyMissingCompleted++;else if(decision.mode==='partial-completed')diagnostics.legacyPartialCompleted++;else if(decision.mode==='ambiguous-fail-closed')diagnostics.ambiguousLegacyRows++;if(decision.added){diagnostics.totalAddedPublicPoints=Math.round((diagnostics.totalAddedPublicPoints+Number(decision.added))*1000)/1000;}}}
    catch(e){recordError(e,'public-stat-return-completion');return base;}
    return decision.result;
  };
  wrappedFn.__fie934eReturn=true;wrappedFn.__legacy=original;window.scorePublicStats=wrappedFn;wrapped=true;return true;
}
function projectionReturnRow(p){
  const ky=firstNestedProjection(p,PROJECTION_FIELDS.kickoffYards),py=firstNestedProjection(p,PROJECTION_FIELDS.puntYards),kt=firstNestedProjection(p,PROJECTION_FIELDS.kickoffTDs),pt=firstNestedProjection(p,PROJECTION_FIELDS.puntTDs),st=firstNestedProjection(p,PROJECTION_FIELDS.specialTeamsTDs),row={};
  if(ky.value!==null)row.kickoff_return_yards=ky.value;if(py.value!==null)row.punt_return_yards=py.value;if(kt.value!==null)row.kickoff_return_tds=kt.value;if(pt.value!==null)row.punt_return_tds=pt.value;if(st.value!==null)row.special_teams_tds=st.value;
  return{row,available:Object.keys(row).length>0,sourceFields:{kickoffYards:ky.key,puntYards:py.key,kickoffTDs:kt.key,puntTDs:pt.key,specialTeamsTDs:st.key}};
}
function explicitReturnsExcluded(p){return p?.projection_components?.returns_included===false||p?.projectionComponents?.returnsIncluded===false||p?.weekly_projection_components?.returns_included===false||p?.weeklyProjectionComponents?.returnsIncluded===false||p?.return_projection_included===false||p?.returnProjectionIncluded===false;}
function auditPlayerProjection(p){
  const pr=projectionReturnRow(p);if(!pr.available){p.returnProjectionPoints=null;p.returnProjectionAvailable=false;p.returnProjectionApplied=false;return null;}
  const scored=scoreReturnRow(pr.row),points=scored.points;p.returnProjectionAvailable=true;p.returnProjectionPoints=points;p.returnProjectionSourceFields=pr.sourceFields;p.returnProjectionApplied=false;diagnostics.playersWithReturnProjectionData++;
  if(points!==null&&explicitReturnsExcluded(p)){const current=finite(p?.weeklyProjection??p?.decision_weekly_projection??p?.sleeperWeeklyProjection);p.weeklyProjectionWithReturns=current===null?null:round3(current+points);p.returnProjectionApplied=true;diagnostics.projectionAdjustmentsAvailable++;/* Deliberately expose the adjusted projection rather than mutate an opaque baseline. */}
  return{points,available:true,applied:p.returnProjectionApplied,weeklyProjectionWithReturns:p.weeklyProjectionWithReturns??null};
}
function auditAllPlayers(){
  const started=now(),ps=players();diagnostics.playersWithActualReturnData=ps.filter(p=>p?.returnScoring?.actual?.available).length;diagnostics.playersWithReturnProjectionData=0;diagnostics.projectionAdjustmentsAvailable=0;for(const p of ps)auditPlayerProjection(p);diagnostics.projectionCoverage=ps.length?Math.round(diagnostics.playersWithReturnProjectionData/ps.length*10000)/10000:0;diagnostics.lastAuditMs=Math.round((now()-started)*10)/10;perf('projection-audit',now()-started,{players:ps.length,coverage:diagnostics.projectionCoverage});window.dispatchEvent?.(new CustomEvent('fie:return-scoring-audited',{detail:{version:VERSION,leagueId:leagueId(),actualPlayers:diagnostics.playersWithActualReturnData,projectionPlayers:diagnostics.playersWithReturnProjectionData,projectionCoverage:diagnostics.projectionCoverage}}));return report();}
function scheduleAudit(){clearTimeout(auditTimer);auditTimer=setTimeout(auditAllPlayers,0);}
function forPlayer(p){return{actual:p?.returnScoring?.actual||null,publicCompletion:p?.returnScoring||null,projection:{available:p?.returnProjectionAvailable===true,points:p?.returnProjectionPoints??null,applied:p?.returnProjectionApplied===true,weeklyProjectionWithReturns:p?.weeklyProjectionWithReturns??null,sourceFields:p?.returnProjectionSourceFields||null}};}
function report(){const audit=scoringAudit();return{version:VERSION,release:RELEASE,leagueId:leagueId(),scoring:{player:audit.player,dst:audit.dst},diagnostics:{...diagnostics,scoringKeys:{...diagnostics.scoringKeys},dstWeights:{...diagnostics.dstWeights},errors:[...diagnostics.errors]}};}
function install(){
  installAttempts++;if(!wrapPublicStats()){if(installAttempts<INSTALL_LIMIT)setTimeout(install,100);else console.warn('FIE V9.3.4E could not wrap scorePublicStats.');return;}diagnostics.installs++;scoringAudit();
  for(const evt of ['fie:score-published','fie:enhanced','fie:starter-economics'])window.addEventListener(evt,scheduleAudit);
  window.addEventListener('fie:league-changing',()=>{clearTimeout(auditTimer);diagnostics.scoringKeys={};diagnostics.dstWeights={};});
  if(players().length)scheduleAudit();
}

const API={installed:true,VERSION,RELEASE,diagnostics,report,scoreReturnRow,scoringAudit,zeroReturnRow,completionDecision,auditAllPlayers,auditPlayerProjection,forPlayer,explicitReturnsExcluded,get legacyScorePublicStats(){return legacyScorePublicStats;}};
window.FIE934E=API;window.FIEReturnScoring=API;
install();
})();

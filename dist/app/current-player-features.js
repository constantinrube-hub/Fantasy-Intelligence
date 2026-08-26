/* Governed research-to-runtime feature bridge.
 * Research artifacts remain the source of truth.  This module only attaches
 * already-produced leakage-safe current features to live player objects and
 * exposes feature lineage/explainability helpers.
 */
(function(){
'use strict';
const VERSION='1.0.0';
const FAMILY={
  opportunity:new Set(['snap_share','offense_snap_share','defense_snap_share','target_share','carry_share','qb_rush_share','red_zone_target_share','red_zone_carry_share','inside_10_carry_share','inside_5_carry_share','pass_play_participation_proxy','end_zone_target_share_proxy','opportunity_change_score']),
  environment:new Set(['team_plays_prior4','team_pass_attempts_prior4','team_rush_attempts_prior4','team_red_zone_plays_prior4','team_goal_line_plays_prior4','opponent_team_plays_prior4','opponent_team_pass_attempts_prior4','opponent_team_rush_attempts_prior4']),
  competition:new Set(['receiving_competition_index','backfield_competition_index','tackle_competition_index','pass_rush_support_index'])
};
function familyFor(k){for(const [f,s] of Object.entries(FAMILY))if(s.has(k))return f;return 'other';}
function currentBundle(){return window.FIE_M5?.getCurrentBundle?.()||null;}
function rowsById(){const m=new Map();for(const r of currentBundle()?.players||[])if(r?.sleeper_id)m.set(String(r.sleeper_id),r);return m;}
function apply(){
  const map=rowsById();let matched=0,withFeatures=0;
  const live=(typeof PLAYERS!=='undefined'?PLAYERS:(window.PLAYERS||[]));
  for(const p of live){
    const row=map.get(String(p.sleeperId));p.currentResearchFeatures=null;p.currentFeatureFamilies={};p.currentFeatureLineage=null;
    const cf=row?.current_features;if(!cf)continue;matched++;
    const vals=cf.values&&typeof cf.values==='object'?cf.values:{};if(Object.keys(vals).length)withFeatures++;
    p.currentResearchFeatures={...vals};
    for(const [k,v] of Object.entries(vals)){const fam=familyFor(k);(p.currentFeatureFamilies[fam]??={})[k]=v;}
    p.currentFeatureLineage={schemaVersion:cf.schema_version||1,asOfCompletedWeek:cf.as_of_completed_week??null,windowGames:cf.window_games??null,source:cf.source||'research current snapshot',leakageSafe:cf.leakage_safe===true,routeParticipationIsProxy:cf.route_participation_is_proxy===true,activationEligible:row?.activation_eligible===true,weeklyActivationEligible:row?.weekly_activation_eligible===true,waiverActivationEligible:row?.waiver_activation_eligible===true};
    // Convenience mirrors for visuals/explanations only. They are not independent
    // model inputs and must never be treated as additional evidence channels.
    for(const k of ['snap_share','target_share','carry_share','red_zone_target_share','red_zone_carry_share','inside_10_carry_share','inside_5_carry_share','opportunity_change_score'])if(Number.isFinite(Number(vals[k])))p[`research_${k}`]=Number(vals[k]);
  }
  API.lastApply={leagueId:String(state?.league?.league_id||''),matched,withFeatures,at:new Date().toISOString()};return API.lastApply;
}
function lineage(p){return p?.currentFeatureLineage||null;}
function families(p){return p?.currentFeatureFamilies||{};}
function summary(p){
  const f=families(p),out=[];
  const o=f.opportunity||{};
  const pct=(k,label)=>{if(Number.isFinite(Number(o[k])))out.push({family:'Opportunity',label,value:Number(o[k]),text:`${label} ${(Number(o[k])*100).toFixed(0)}%`});};
  pct('snap_share','snap share');pct('target_share','target share');pct('carry_share','carry share');pct('red_zone_target_share','RZ target share');pct('red_zone_carry_share','RZ carry share');
  if(Number.isFinite(Number(o.opportunity_change_score)))out.push({family:'Opportunity',label:'opportunity trend',value:Number(o.opportunity_change_score),text:`opportunity trend ${Number(o.opportunity_change_score)>=0?'+':''}${Number(o.opportunity_change_score).toFixed(2)}`});
  return out;
}
function signalLineage(p){
  const lines=[{family:'Baseline',source:p?.sleeperWeeklyProjection!=null?'Sleeper weekly projection':'fallback projection',active:true}];
  if(p?.currentFeatureLineage){const governed=p.currentFeatureLineage.leakageSafe===true&&p.currentFeatureLineage.activationEligible===true&&window.FIE_M6_GOVERNANCE_ALLOW===true;lines.push({family:'Opportunity',source:p.currentFeatureLineage.source,active:governed,diagnostic:!governed,reason:governed?'governed current feature family':'diagnostic until leakage, player and M6 governance gates all pass'});}
  if(Number.isFinite(Number(p?.pffScore))||Number.isFinite(Number(p?.tfgModelScore)))lines.push({family:'Talent / efficiency',source:'PFF / TFG enrichment',active:true});
  if(Number.isFinite(Number(p?.teamEnvironmentScore)))lines.push({family:'Environment',source:'team environment model',active:true});
  if(Number.isFinite(Number(p?.matchupScore)))lines.push({family:'Matchup',source:'opponent context',active:true});
  if(p?.injuryStatus)lines.push({family:'Health',source:'Sleeper injury metadata',active:true});
  if(Number.isFinite(Number(p?.marketADP)))lines.push({family:'Market',source:'Sleeper ADP',active:true});
  return lines;
}
const API={VERSION,lastApply:null,apply,lineage,families,summary,signalLineage,familyFor};
window.FIECurrentFeatures=API;
})();

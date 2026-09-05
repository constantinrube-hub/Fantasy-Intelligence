/* FIE V9.3.2 canonical decision gateway.
 * Production authority is this service, not a version-labelled research module.
 * The canonical V9 diagnostic decision geometry is available in production and
 * is overlaid with DraftBase canonical rank/value fields. Candidate coefficient
 * promotion remains fail-closed in model-config, while governed current-feature
 * activation is a separate per-league M6/lineage decision.
 * FIE_DRAFT_V71 is compatibility-only if canonical V9 rows are unavailable.
 */
(function(){
'use strict';
const VERSION='9.3.2';
function config(){return window.FIE_MODEL_CONFIG||{};}
function productionModel(){return config()?.production?.promoted===true?'V9_PROMOTED':'V9_CANONICAL_ARCHITECTURE_RESEARCH_GATED';}
function productionAuthority(){
  const p=config()?.production||{};
  return{
    owner:p.authority||'FIEDecisionService',
    version:p.authority_version||VERSION,
    architecture:p.architecture||'V9 canonical diagnostic decision geometry + DraftBase canonical overlay',
    candidateCoefficientPromotion:p.promoted===true,
    promotionScope:p.promotion_scope||'candidate_decision_coefficients',
    currentFeatureGovernance:p.current_feature_governance||'league_scoped_m6',
    currentFeatureActivationIndependent:p.current_feature_activation_independent_of_candidate_promotion!==false,
    compatibilityFallback:'FIE_DRAFT_V71',
    fallbackIsNormalAuthority:false
  };
}
function canonicalOverlay(rows){
  const base=new Map((window.FIEDraftBaseValueService?.rows?.()||[]).map(x=>[String(x.id),x]));
  return (rows||[]).map(r=>{const id=String(window.FIECore?.PlayerIdentity?.id?.(r.p)||r.p?.sleeperId||''),c=base.get(id);return Object.assign(r,{canonicalBaseValue:c?.baseValue??null,canonicalBoardRank:c?.overallRank??null,canonicalPosRank:c?.positionRank??null,canonicalTier:c?.tier??null,canonicalConfidence:c?.confidence??null});});
}
function draftRows(rosterId){
  let rows=[];
  if(window.FIEModelV9?.buildDiagnosticRows){try{rows=window.FIEModelV9.buildDiagnosticRows(rosterId)||[];}catch{}}
  if(!rows.length&&window.FIEModelV9?.buildDraftValueRows){try{rows=window.FIEModelV9.buildDraftValueRows(rosterId)||[];}catch{}}
  if(!rows.length)rows=window.FIE_DRAFT_V71?.buildDraftValueRows?.(rosterId)||[];
  return canonicalOverlay(rows);
}
function diagnosticRows(rosterId){return draftRows(rosterId);}
function governance(){return window.FIE_M6_GOVERNANCE_STATE||window.FIE_M6?.getGovernance?.()||null;}
function researchFeatureMayAffect(p,domain='draft'){
  const l=p?.currentFeatureLineage||{},g=governance();
  if(l.leakageSafe!==true||l.activationEligible!==true)return false;
  if(window.FIE_M6_GOVERNANCE_ALLOW!==true||g?.runtime_enabled!==true)return false;
  if(domain==='weekly'&&l.weeklyActivationEligible!==true)return false;
  if(domain==='waiver'&&l.waiverActivationEligible!==true)return false;
  return true;
}
window.FIEDecisionService={VERSION,productionModel,productionAuthority,draftRows,diagnosticRows,researchFeatureMayAffect,governance,canonicalOverlay};
})();

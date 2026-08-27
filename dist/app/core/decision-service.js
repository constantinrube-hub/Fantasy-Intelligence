/* FIE V9.3.2 canonical decision gateway.
 * The roster-neutral base rank is always provided by DraftBaseValueService.
 * Research feature influence remains fail-closed; using the canonical V9 decision
 * architecture does not imply that unvalidated research signals are promoted.
 */
(function(){
'use strict';
function config(){return window.FIE_MODEL_CONFIG||{};}
function productionModel(){return config()?.production?.promoted===true?'V9_PROMOTED':'V9_CANONICAL_ARCHITECTURE_RESEARCH_GATED';}
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
window.FIEDecisionService={VERSION:'9.3.2',productionModel,draftRows,diagnosticRows,researchFeatureMayAffect,governance,canonicalOverlay};
})();

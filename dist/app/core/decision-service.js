/* Canonical production decision gateway. Feature modules must consume this
 * instead of choosing an independent valuation kernel.
 */
(function(){
'use strict';
function config(){return window.FIE_MODEL_CONFIG||{};}
function productionModel(){return config()?.production?.promoted===true?'V9':'V8.9_FALLBACK';}
function draftRows(rosterId){
  if(config()?.production?.promoted===true){const rows=window.FIEModelV9?.buildDraftValueRows?.(rosterId);if(Array.isArray(rows))return rows;}
  return window.FIE_DRAFT_V71?.buildDraftValueRows?.(rosterId)||[];
}
function diagnosticRows(rosterId){return window.FIEModelV9?.buildDiagnosticRows?.(rosterId)||draftRows(rosterId);}
function governance(){return window.FIE_M6_GOVERNANCE_STATE||window.FIE_M6?.getGovernance?.()||null;}
function researchFeatureMayAffect(p,domain='draft'){
  const l=p?.currentFeatureLineage||{},g=governance();
  if(l.leakageSafe!==true||l.activationEligible!==true)return false;
  if(window.FIE_M6_GOVERNANCE_ALLOW!==true||g?.runtime_enabled!==true)return false;
  if(domain==='weekly'&&l.weeklyActivationEligible!==true)return false;
  if(domain==='waiver'&&l.waiverActivationEligible!==true)return false;
  return true;
}
window.FIEDecisionService={VERSION:'1.0.0',productionModel,draftRows,diagnosticRows,researchFeatureMayAffect,governance};
})();

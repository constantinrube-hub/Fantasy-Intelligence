const fs=require('fs'),vm=require('vm');
const ctx={console,FIE_MODEL_CONFIG:{production:{promoted:false}},FIEModelV9:{buildDraftValueRows:()=>[{model:'v9'}],buildDiagnosticRows:()=>[{model:'diag'}]},FIE_DRAFT_V71:{buildDraftValueRows:()=>[{model:'fallback'}]},FIE_M6_GOVERNANCE_STATE:{runtime_enabled:true},FIE_M6_GOVERNANCE_ALLOW:true};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync('app/core/decision-service.js','utf8'),ctx);
if(ctx.FIEDecisionService.draftRows(1)[0].model!=='fallback')throw new Error('unpromoted V9 leaked through canonical decision service');
ctx.FIE_MODEL_CONFIG.production.promoted=true;if(ctx.FIEDecisionService.draftRows(1)[0].model!=='v9')throw new Error('promoted V9 not selected');
const p={currentFeatureLineage:{leakageSafe:true,activationEligible:true,weeklyActivationEligible:true,waiverActivationEligible:true}};if(!ctx.FIEDecisionService.researchFeatureMayAffect(p,'draft'))throw new Error('valid governed feature rejected');ctx.FIE_M6_GOVERNANCE_ALLOW=false;if(ctx.FIEDecisionService.researchFeatureMayAffect(p,'draft'))throw new Error('feature bypassed governance');
console.log('PASS integrity_decision_service_test');

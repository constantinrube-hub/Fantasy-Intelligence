#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rel=json.loads((R/'config/release.json').read_text())
model=json.loads((R/'config/model-config.json').read_text())
prod=model['production']

assert rel['schema_version'] == 2
assert rel['release'] == '9.3.4c-production-authority'
assert rel['runtime'] == '9.3.4C-modular-runtime'
assert rel['decision_model'] == model['model_version'] == '9.1-diagnostic-architecture'
assert rel['production_authority'] == 'FIEDecisionService@9.3.2'
assert rel['candidate_promotion'] == 'fail-closed'
assert rel['stage'] == 'controlled-implementation'
assert 'M1-M9' in rel['research_schema']
assert 'current-split-v1' in rel['research_schema']
assert 'unified-research-v1' in rel['research_schema']

assert prod['authority'] == 'FIEDecisionService'
assert prod['authority_version'] == '9.3.2'
assert prod['promoted'] is False
assert prod['promotion_scope'] == 'candidate_decision_coefficients'
assert prod['current_feature_governance'] == 'league_scoped_m6'
assert prod['current_feature_activation_independent_of_candidate_promotion'] is True
assert 'compatibility-only' in prod['fallback']
assert 'normal unpromoted production authority' in prod['fallback']

# Freeze the pre-2C candidate coefficients: 2C is authority/identity only.
assert model['candidate']['draft_decision_weights'] == {'league':0.65,'roster':0.25,'timing':0.1}
assert model['candidate']['chopped_utility_weights'] == {'vor':0.55,'lower_tail_surplus':0.45}
assert model['candidate']['bestball_utility_weights'] == {'vor':0.55,'spike_surplus':0.45}
assert model['candidate']['dynasty_utility_weights'] == {'current_vor_percentile':0.55,'future_percentile':0.45}

svc=(R/'app/core/decision-service.js').read_text()
assert 'function productionAuthority()' in svc
assert "compatibilityFallback:'FIE_DRAFT_V71'" in svc
assert 'fallbackIsNormalAuthority:false' in svc
assert "buildDiagnosticRows" in svc and "buildDraftValueRows" in svc
assert "researchFeatureMayAffect" in svc

assert rel['release'] in (R/'app/generated/release.js').read_text()
assert rel['release'] in (R/'functions/release.js').read_text()
assert model['model_version'] in (R/'app/generated/model-config.js').read_text()

arch=(R/'docs/current/ARCHITECTURE.md').read_text()
hand=(R/'docs/current/HANDOFF.md').read_text()
dep=(R/'docs/current/DEPLOYMENT.md').read_text()
chg=(R/'docs/current/CHANGE_GUIDE.md').read_text()
for stale in ('governed V8.9 fallback otherwise','RUNTIME_FALLBACK_ONLY'):
    assert stale not in arch+hand+dep+chg
for required in ('FIEDecisionService','compatibility fallback','candidate decision coefficients','league-scoped'):
    assert required.lower() in (arch+hand+dep+chg).lower()

print('PASS Tranche 2C production authority and release identity contract')

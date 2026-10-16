#!/usr/bin/env python3
import json, sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone2.json')
x=json.loads(p.read_text())
req=['schema_version','milestone','control_build','research_build','diagnostic_only','steps_completed','methodology','decomposition','xfp','regression_validation','opportunity_change_validation','competition_validation','vacated_opportunity']
missing=[k for k in req if k not in x]
if missing: raise SystemExit(f'Missing keys: {missing}')
if x['milestone']!='M2' or x['diagnostic_only'] is not True: raise SystemExit('Invalid M2 guardrails')
if x.get('control_build')!='V8.2.2': raise SystemExit('Control build is not frozen at V8.2.2')
if x.get('steps_completed') != [10,11,12,13,14,15]: raise SystemExit('Unexpected completed-step manifest')
if x.get('vacated_opportunity',{}).get('activation_eligible') is not False: raise SystemExit('Retrospective vacated opportunity must not activate live scoring')
if 'no proxy is relabeled as true routes' not in str(x.get('methodology',{}).get('route_guardrail','')): raise SystemExit('Route guardrail missing')
if x.get('status')=='complete':
    got={int(r['test_season']) for r in x['decomposition'].get('component_validation',[]) if r.get('test_season') is not None}
    folds=set(range(2022,max(got)+1)) if got else set()
    if got!=folds: raise SystemExit(f'Unexpected/non-contiguous decomposition folds: {sorted(got)}')
    xgot={int(r['test_season']) for r in x['xfp'].get('validation',[]) if r.get('test_season') is not None}
    if xgot!=folds: raise SystemExit(f'Unexpected/non-contiguous xFP folds: {sorted(xgot)}')
    if not x['regression_validation']: raise SystemExit('Regression validation missing')
    if not x['opportunity_change_validation']: raise SystemExit('Opportunity-change validation missing')
    if not x['competition_validation'].get('folds'): raise SystemExit('Competition validation missing')
    forbidden={'receptions','receiving_yards','receiving_tds','rushing_yards','rushing_tds','passing_yards','passing_tds','tackles_solo','def_sacks','def_interceptions'}
    for r in x['xfp'].get('validation',[]):
        bad=forbidden.intersection(r.get('opportunity_features',[]))
        if bad: raise SystemExit(f'Outcome leakage in xFP features: {sorted(bad)}')
print(f"OK: {p} status={x.get('status')} component_rows={len(x.get('decomposition',{}).get('component_validation',[]))} xfp_rows={len(x.get('xfp',{}).get('validation',[]))}")

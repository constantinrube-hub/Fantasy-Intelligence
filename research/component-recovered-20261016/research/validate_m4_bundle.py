#!/usr/bin/env python3
import json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone4.json')
x=json.loads(p.read_text())
req=['schema_version','milestone','control_build','research_build','diagnostic_only','steps_completed','methodology','position_production_lab','activation_lock','final_position_models','sleeper_benchmark','blend']
missing=[k for k in req if k not in x]
if missing:raise SystemExit(f'Missing keys: {missing}')
if x['milestone']!='M4' or x['diagnostic_only'] is not True:raise SystemExit('Invalid M4 guardrails')
if x.get('control_build')!='V8.2.2':raise SystemExit('Control build is not frozen at V8.2.2')
if x.get('steps_completed')!=[19,20,21,22,23]:raise SystemExit('Unexpected M4 completed-step manifest')
lock=x.get('activation_lock',{})
if lock.get('enabled') is not True or lock.get('live_model_overrides') not in ([],None):raise SystemExit('M4 activation lock invalid')
if x.get('position_production_lab',{}).get('live_activation_count')!=0:raise SystemExit('M4 feature registry activated live features')
for r in x.get('position_production_lab',{}).get('feature_registry',[]):
    if r.get('live_status')!='OFF':raise SystemExit(f"Feature unexpectedly live: {r.get('feature')}")
for pos,spec in x.get('final_position_models',{}).get('model_specs',{}).get('positions',{}).items():
    if spec.get('live_status')!='OFF':raise SystemExit(f'Model unexpectedly live: {pos}')
    bad={'fantasy_points','xfp_residual','opportunity_xfp_realized','opportunity_change_score'} & set(spec.get('features',[]))
    if bad:raise SystemExit(f'Same-week outcome leakage in {pos} features: {sorted(bad)}')
if x.get('blend',{}).get('live_status')!='OFF':raise SystemExit('Blend unexpectedly live')
if x.get('status')=='complete':
    got={int(r['test_season']) for r in x.get('final_position_models',{}).get('folds',[]) if r.get('test_season') is not None}
    folds=set(range(2022,max(got)+1)) if got else set()
    if got and got!=folds:raise SystemExit(f'Unexpected/non-contiguous M4 final-model folds: {sorted(got)}')
    if not x.get('final_position_models',{}).get('aggregate'):raise SystemExit('Final position aggregate missing')
    sb=x.get('sleeper_benchmark',{})
    if sb.get('status')=='complete' and not sb.get('folds'):raise SystemExit('Sleeper benchmark complete without rows')
    if x.get('blend',{}).get('status')=='complete' and not x.get('blend',{}).get('folds'):raise SystemExit('Blend complete without rows')
print(f"OK: {p} status={x.get('status')} final_rows={len(x.get('final_position_models',{}).get('folds',[]))} sleeper={x.get('sleeper_benchmark',{}).get('status')} blend={x.get('blend',{}).get('status')}")

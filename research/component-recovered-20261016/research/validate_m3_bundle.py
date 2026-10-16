#!/usr/bin/env python3
import json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone3.json')
x=json.loads(p.read_text())
req=['schema_version','milestone','control_build','research_build','diagnostic_only','steps_completed','methodology','position_specific','natural_experiments','young_player_model']
missing=[k for k in req if k not in x]
if missing:raise SystemExit(f'Missing keys: {missing}')
if x['milestone']!='M3' or x['diagnostic_only'] is not True:raise SystemExit('Invalid M3 guardrails')
if x.get('control_build')!='V8.2.2':raise SystemExit('Control build is not frozen at V8.2.2')
if x.get('steps_completed')!=[16,17,18]:raise SystemExit('Unexpected M3 completed-step manifest')
rg=str(x.get('methodology',{}).get('route_guardrail',''))
if 'not true route participation' not in rg or 'not individual pass-rush participation' not in rg:raise SystemExit('M3 participation guardrail missing')
if x.get('natural_experiments',{}).get('causal_claim') is not False:raise SystemExit('Natural experiments must not claim causality')
if x.get('status')=='complete':
    sgot={int(r['test_season']) for r in x['position_specific'].get('folds',[]) if r.get('test_season') is not None}
    folds=set(range(2022,max(sgot)+1)) if sgot else set()
    if sgot and sgot!=folds:raise SystemExit(f'Unexpected/non-contiguous specialized folds: {sorted(sgot)}')
    ygot={int(r['test_season']) for r in x['young_player_model'].get('folds',[]) if r.get('test_season') is not None}
    if ygot and not ygot.issubset(folds):raise SystemExit(f'Unexpected young-player folds: {sorted(ygot)}')
    if not x['natural_experiments'].get('results'):raise SystemExit('Natural experiment results missing')
    if 'coordinator_change' not in x['natural_experiments'].get('unsupported',{}):raise SystemExit('Coordinator-change limitation missing')
print(f"OK: {p} status={x.get('status')} specialized_rows={len(x.get('position_specific',{}).get('folds',[]))} young_rows={len(x.get('young_player_model',{}).get('folds',[]))}")

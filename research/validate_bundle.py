#!/usr/bin/env python3
import json, sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone1.json')
x=json.loads(p.read_text())
required=['schema_version','milestone','control_build','research_build','diagnostic_only','coverage','identity','metrics','team_opportunity_validation','stability','predictiveness','validation']
missing=[k for k in required if k not in x]
if missing: raise SystemExit(f'Missing keys: {missing}')
if x['milestone']!='M1' or x['diagnostic_only'] is not True: raise SystemExit('Invalid milestone guardrails')
if x.get('control_build')!='V8.2.2': raise SystemExit('Control build is not frozen at V8.2.2')
if x.get('status')=='complete':
    if x['coverage'].get('player_weeks',0)<=0: raise SystemExit('Complete bundle has no player weeks')
    if not x['validation']: raise SystemExit('Complete bundle has no validation rows')
    meth=x.get('methodology',{})
    if meth.get('no_random_split') is not True or meth.get('pregame_lagging') is not True: raise SystemExit('Time-safe validation guardrails missing')
    got={int(r['test_season']) for r in x['validation'] if not r.get('aggregate') and r.get('test_season') is not None}
    expected=set(range(2022,max(got)+1)) if got else set()
    if got!=expected: raise SystemExit(f'Unexpected/non-contiguous position-validation folds: {sorted(got)}')
    tgot={int(r['test_season']) for r in x.get('team_opportunity_validation',[]) if r.get('test_season') is not None}
    if tgot and tgot!=expected: raise SystemExit(f'Unexpected/non-contiguous team-validation folds: {sorted(tgot)}')
    scoring=x.get('scoring',{})
    if 'support' not in scoring or 'exact_replay_eligible' not in scoring['support']:
        raise SystemExit('Scoring support audit missing')
    guard=str(meth.get('route_guardrail',''))
    if 'never labeled as true_route_participation' not in guard:
        raise SystemExit('Route-proxy guardrail missing')
print(f"OK: {p} status={x.get('status')} player_weeks={x.get('coverage',{}).get('player_weeks',0)} validation_rows={len(x.get('validation',[]))}")

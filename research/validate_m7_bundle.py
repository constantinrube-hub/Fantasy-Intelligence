#!/usr/bin/env python3
import json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone7.json');b=json.loads(p.read_text())
assert b.get('schema_version')==7 and b.get('milestone')=='M7' and b.get('status')=='complete'
d=b.get('driver_research',{});assert isinstance(d.get('driver_ranking'),list);assert isinstance(d.get('family_validation',{}).get('aggregate'),list)
for r in d.get('family_validation',{}).get('aggregate',[]):
    if r.get('status')=='validated_candidate':
        assert int(r.get('folds',0))>=4;assert r.get('bootstrap_ci95_low') is not None and float(r['bootstrap_ci95_low'])>0
comp=d.get('activation_composite',{})
for pos,s in (comp.get('model_specs') or {}).items():
    gate=s.get('gate',{});assert gate.get('status')=='validated_candidate';assert int(gate.get('folds',0))>=4
    n=len(s.get('features') or []);assert n and len(s.get('ridge',{}).get('coef') or [])==n
print(f'PASS M7 bundle {p}')

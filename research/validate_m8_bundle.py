#!/usr/bin/env python3
import json,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone8.json');b=json.loads(p.read_text())
assert b.get('schema_version')==8 and b.get('milestone')=='M8' and b.get('status')=='complete'
m=b.get('matchup_validation',{});assert isinstance(m.get('aggregate'),list)
for r in m.get('aggregate',[]):
    if r.get('status')=='validated_candidate':
        assert int(r.get('folds',0))>=4;assert r.get('bootstrap_ci95_low') is not None and float(r['bootstrap_ci95_low'])>0
assert 'shifted' in str(b.get('optional_source_timing','')).lower()
ledger={r.get('analysis'):r for r in b.get('source_ledger',[])}
assert 'individual_wr_db_responsibility' in ledger and 'individual_blocker_rusher_assignment' in ledger
assert b.get('dst_bridge',{}).get('status')=='challenger_contract_ready'

seq=m.get('sequential_activation',{})
assert isinstance(seq.get('model_specs',{}),dict)
for pos,spec in (seq.get('model_specs') or {}).items():
    gate=spec.get('gate',{})
    assert gate.get('status')=='validated_candidate'
    assert int(gate.get('folds',0))>=4
    assert float(gate.get('bootstrap_ci95_low'))>0
    fs=spec.get('features') or []; comp=spec.get('component_features') or {}
    assert fs and set(comp.get('m7',[])).union(comp.get('m8',[]))==set(fs)
    assert 'do not add a separate M7 correction' in str(spec.get('semantics',''))
print(f'PASS M8 bundle {p}')

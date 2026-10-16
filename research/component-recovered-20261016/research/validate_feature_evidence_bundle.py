#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path

VALID_STATUS={"validated","horizon_specific","promising_underpowered","redundant_or_explanatory","descriptive_not_incremental","insufficient_coverage","no_incremental_evidence","mechanism_specific"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('bundle'); a=ap.parse_args(); p=Path(a.bundle)
    b=json.loads(p.read_text())
    assert b.get('schema_version')==1
    assert b.get('status')=='complete_research_only'
    gov=b.get('governance') or {}; assert gov.get('auto_activation') is False; assert gov.get('production_gate_unchanged') is True
    rows=b.get('phase1_feature_evidence_matrix'); assert isinstance(rows,list)
    for r in rows:
        assert r.get('position') in {'QB','RB','WR','TE'}
        assert r.get('evidence_status') in VALID_STATUS
        cov=float(r.get('coverage',0)); assert 0<=cov<=1
        g=r.get('weekly_gate') or {}; assert g.get('robust') in {True,False}
        if g.get('robust'):
            assert int(g.get('folds',0))>=4 and float(g.get('mean',0))>=.01 and float(g.get('ci95_low',0))>0
    expected_horizons={'next_week','next_3_games','rest_of_season','floor','ceiling','breakout'}
    hz=b.get('phase3_multi_horizon_validation',[])
    if rows: assert expected_horizons <= {r.get('horizon') for r in hz}
    for r in hz:
        assert (r.get('gate') or {}).get('robust') in {True,False}
    for r in b.get('phase2_component_validation',[]):
        assert r.get('status') in {'validated_component_signal','diagnostic_component_signal'}
    for r in b.get('phase4_regularized_challengers',[]):
        elig=str(r.get('production_eligibility',''))
        if elig.startswith('eligible'):
            assert (r.get('gate') or {}).get('robust') is True
    assert b.get('phase7_production_gate',{}).get('rule')
    print(f"PASS feature evidence bundle: {len(rows)} features; no auto-activation")
if __name__=='__main__': main()

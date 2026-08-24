#!/usr/bin/env python3
import json,tempfile
from argparse import Namespace
from pathlib import Path
from fie_research import run as run_m1
from fie_m2 import run as run_m2
from fie_m3 import run as run_m3
from fie_m4 import run as run_m4

with tempfile.TemporaryDirectory() as td:
    td=Path(td); der=td/'derived'; der.mkdir()
    m1=run_m1(Namespace(fixture=True,seasons=list(range(2019,2026)),extended_seasons=list(range(2016,2026)),output=str(td/'m1.json'),derived_dir=str(der),cache_dir=str(td/'cache'),league_id=None,scoring_json=None,full_raw_cache=False))
    (td/'m1.json').write_text(json.dumps(m1))
    m2=run_m2(Namespace(fixture=True,m1_derived_dir=str(der),m1_bundle=str(td/'m1.json'),derived_dir=str(der),output=str(td/'m2.json')))
    (td/'m2.json').write_text(json.dumps(m2))
    m3=run_m3(Namespace(fixture=True,derived_dir=str(der),m1_bundle=str(td/'m1.json'),m2_bundle=str(td/'m2.json'),cache_dir=str(td/'cache'),seasons=list(range(2019,2026))))
    (td/'m3.json').write_text(json.dumps(m3))
    b=run_m4(Namespace(fixture=True,derived_dir=str(der),m1_bundle=str(td/'m1.json'),m2_bundle=str(td/'m2.json'),m3_bundle=str(td/'m3.json'),cache_dir=str(td/'cache'),sleeper_archive=str(td/'market'),seasons=list(range(2019,2026))))
    assert b['diagnostic_only'] is True
    assert b['control_build']=='V8.2.2'
    assert b['steps_completed']==[19,20,21,22,23]
    assert b['activation_lock']['enabled'] is True and b['activation_lock']['live_model_overrides']==[]
    assert b['position_production_lab']['live_activation_count']==0
    assert len(b['position_production_lab']['feature_registry'])>20
    got={r['test_season'] for r in b['final_position_models']['folds']}
    assert got=={2022,2023,2024,2025},got
    assert len(b['final_position_models']['aggregate'])>=5
    assert len(b['final_position_models']['raw_target_metrics'])>20
    assert all(v['live_status']=='OFF' for v in b['final_position_models']['model_specs']['positions'].values())
    stab=b['final_position_models']['model_specs'].get('feature_stability',[])
    assert stab and all(r.get('activation_effect')=='diagnostic_only' for r in stab)
    assert {r.get('classification') for r in stab} <= {'stable_direction','low_weight','direction_unstable'}
    assert b['sleeper_benchmark']['status']=='complete'
    assert len(b['sleeper_benchmark']['folds'])>0
    assert b['blend']['status']=='complete'
    assert len(b['blend']['folds'])>0
    assert b['blend']['live_status']=='OFF'
print('OK: M4 governance + raw-stat models + immutable Sleeper benchmark + time-safe blend')

#!/usr/bin/env python3
import tempfile
from argparse import Namespace
from fie_m3 import run

with tempfile.TemporaryDirectory() as td:
    b=run(Namespace(fixture=True,derived_dir=td,m1_bundle='',m2_bundle='',cache_dir=td,seasons=list(range(2019,2026))))
    assert b['diagnostic_only'] is True
    assert b['control_build']=='V8.2.2'
    assert b['steps_completed']==[16,17,18]
    folds={2022,2023,2024,2025}
    got={r['test_season'] for r in b['position_specific']['folds']}
    assert got==folds,got
    assert len(b['position_specific']['aggregate'])>=5
    assert len(b['natural_experiments']['results'])>=5
    assert b['natural_experiments']['causal_claim'] is False
    assert b['natural_experiments']['unsupported']['coordinator_change']['status'].startswith('blocked')
    assert b['young_player_model']['coverage']['rows']>0
    assert len(b['young_player_model']['folds'])>0
    assert b['derived_tables']['written'] is True
print('OK: M3 position-specific + natural experiments + Y1/Y2 opportunity model')

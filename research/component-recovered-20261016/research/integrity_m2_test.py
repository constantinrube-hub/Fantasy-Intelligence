#!/usr/bin/env python3
import json, tempfile
from argparse import Namespace
from pathlib import Path
from fie_m2 import run

with tempfile.TemporaryDirectory() as td:
    b=run(Namespace(fixture=True,m1_derived_dir='',m1_bundle='',derived_dir=td))
    assert b['diagnostic_only'] is True
    assert b['control_build']=='V8.2.2'
    assert b['steps_completed']==[10,11,12,13,14,15]
    folds={2022,2023,2024,2025}
    assert {r['test_season'] for r in b['decomposition']['component_validation']}==folds
    assert {r['test_season'] for r in b['xfp']['validation']}==folds
    assert len(b['regression_validation'])>=5
    assert len(b['opportunity_change_validation'])>=5
    assert len(b['competition_validation']['folds'])>0
    assert b['vacated_opportunity']['activation_eligible'] is False
    assert any(s['kind']=='receiving' for s in b['vacated_opportunity']['summary'])
    forbidden={'receptions','receiving_yards','receiving_tds','rushing_yards','rushing_tds','passing_yards','passing_tds','tackles_solo','def_sacks','def_interceptions'}
    for r in b['xfp']['validation']:
        assert not forbidden.intersection(r['opportunity_features'])
print('OK: M2 decomposition + xFP + regression + role change + competition + vacated opportunity')

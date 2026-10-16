#!/usr/bin/env python3
"""Static/runtime-contract test for V9.6 controlled integration."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
import fie_runtime_v96 as v96

v96.self_test()
src=(ROOT/'research'/'fie_runtime_v96.py').read_text()
assert 'WR' not in repr(v96.PRIMARY_WEEKLY)
assert v96.PRIMARY_WEEKLY == {'QB':'histgb','RB':'histgb'}
assert 'waiver_next3_projection' in src
assert 'next_season_enabled' in src
print('PASS V9.6 static governance')

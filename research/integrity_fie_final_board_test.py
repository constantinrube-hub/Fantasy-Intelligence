#!/usr/bin/env python3
"""Static contract guard: the final board must delegate value/scarcity to the existing stack."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/'research/build_fie_final_league_board.py').read_text(encoding='utf-8')
assert 'from fie_strategy_stack import build_league_value_board' in p
assert 'build_league_value_board(m9, profile' in p
assert 'V9.7 shadow' in p or 'challenger' in p
assert 'automatic_promotion": False' in p
assert 'projection_scope": "WEEKLY_CURRENT"' in p
print('PASS final board delegation/governance contract')

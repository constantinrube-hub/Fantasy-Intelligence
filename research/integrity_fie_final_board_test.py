#!/usr/bin/env python3
"""Contract guards for final-board delegation and unavailable-row semantics."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/'research/build_fie_final_league_board.py').read_text(encoding='utf-8')
assert 'from fie_strategy_stack import build_league_value_board' in p
assert 'build_league_value_board(m9, profile' in p
assert 'V9.7 shadow' in p or 'challenger' in p
assert 'automatic_promotion": False' in p
assert 'projection_scope": "WEEKLY_CURRENT"' in p

# Dynamic validator contract: unprojected catalog players may remain only when
# explicitly unavailable and non-actionable; usable/draft rows must be projected.
try:
    from validate_fie_research_pipeline import validate_offense_projection_contract
except ImportError:
    from research.validate_fie_research_pipeline import validate_offense_projection_contract

ok=pd.DataFrame([
    {'model_selected':'M9','projection_points':250.0,'value_label':'VALUE','draft_relevant':True,'actionable_signal':True},
    {'model_selected':'M9','projection_points':None,'value_label':'UNAVAILABLE','draft_relevant':False,'actionable_signal':False},
])
validate_offense_projection_contract(ok)

bad=ok.copy(); bad.loc[1,'draft_relevant']=True
try:
    validate_offense_projection_contract(bad)
except AssertionError:
    pass
else:
    raise AssertionError('validator allowed missing projection on draft-relevant row')

bad2=ok.copy(); bad2.loc[1,'value_label']='FAIR'
try:
    validate_offense_projection_contract(bad2)
except AssertionError:
    pass
else:
    raise AssertionError('validator allowed missing projection on non-UNAVAILABLE row')

print('PASS final board delegation/governance + unavailable-row projection contract')

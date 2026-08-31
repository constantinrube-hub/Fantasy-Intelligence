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

# Projection point estimate and uncertainty interval must come from the same M9
# view.  Diagnostic market-anchored rows use diagnostic quantiles; validated
# production rows use the base/production quantiles.
try:
    from build_fie_final_league_board import _projection_view
except ImportError:
    from research.build_fie_final_league_board import _projection_view

diag=_projection_view({
    'fie_value_projection':200.0,'fie_production_mean':None,'fie_diagnostic_mean':200.0,
    'fie_season_mean':170.0,'fie_ppg':10.0,
    'p10':130.0,'p25':145.0,'p50':165.0,'p75':185.0,'p90':205.0,
    'diagnostic_p10':160.0,'diagnostic_p25':175.0,'diagnostic_p50':195.0,
    'diagnostic_p75':215.0,'diagnostic_p90':235.0,
})
assert diag['projection_basis']=='DIAGNOSTIC_MARKET_ANCHORED'
assert diag['projection_points']==200.0
assert diag['p10']==160.0 and diag['p90']==235.0
assert abs(diag['projection_ppg']-(200.0/17.0))<1e-9

prod=_projection_view({
    'fie_value_projection':220.0,'fie_production_mean':220.0,'fie_diagnostic_mean':210.0,
    'fie_season_mean':220.0,'fie_ppg':220.0/17.0,
    'p10':180.0,'p25':195.0,'p50':215.0,'p75':235.0,'p90':250.0,
    'diagnostic_p10':170.0,'diagnostic_p90':240.0,
    'projection_source':'FIE_M9_VALIDATED_PRESEASON',
})
assert prod['projection_basis']=='PRODUCTION'
assert prod['p10']==180.0 and prod['p90']==250.0

print('PASS final board delegation/governance + unavailable-row + projection-distribution contracts')

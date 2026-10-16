#!/usr/bin/env python3
"""Regression guards for report market boundaries and presentation contracts."""
from build_fie_league_research_report import _fmt, _replacement_from_board, _top100_outliers

base={
    'player_id':'1','name':'A Player','team':'X','position':'WR','projection_points':200,
    'current_active':True,'vorp':20,'market_position_rank':20,'position_rank':10,
    'value_label':'VALUE','replacement_points':170.0,
}
a=dict(base,adp=99,rank_edge_position=10)
b=dict(base,player_id='2',name='B Player',adp=101,rank_edge_position=20)
c=dict(base,player_id='3',name='C Player',adp=50,rank_edge_position=-10,value_label='OVERPRICED')
x=_top100_outliers([a,b,c])
assert [r['player_id'] for r in x['positive']]==['1']
assert [r['player_id'] for r in x['negative']]==['3']

# Integer rendering must preserve significant zeroes.
assert _fmt(10,0)=='10'
assert _fmt(20,0)=='20'
assert _fmt(30,0)=='30'
assert _fmt(-10,0)=='-10'

# Human report replacement must come from the canonical final board and fail
# closed when that board is internally inconsistent.
assert _replacement_from_board([a,b], 'WR') == 170.0
bad=[dict(a),dict(b,replacement_points=171.0)]
try:
    _replacement_from_board(bad, 'WR')
except RuntimeError:
    pass
else:
    raise AssertionError('conflicting canonical replacement points were accepted')

print('PASS report ADP boundary + integer formatting + canonical replacement contract')

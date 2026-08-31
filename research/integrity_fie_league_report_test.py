#!/usr/bin/env python3
from build_fie_league_research_report import _top100_outliers
base={'player_id':'1','name':'A Player','team':'X','position':'WR','projection_points':200,'current_active':True,'vorp':20,'market_position_rank':20,'position_rank':10,'value_label':'VALUE'}
a=dict(base,adp=99,rank_edge_position=10);b=dict(base,player_id='2',name='B Player',adp=101,rank_edge_position=20);c=dict(base,player_id='3',name='C Player',adp=50,rank_edge_position=-10,value_label='OVERPRICED')
x=_top100_outliers([a,b,c]);assert [r['player_id'] for r in x['positive']]==['1'];assert [r['player_id'] for r in x['negative']]==['3']
print('PASS report ADP boundary/outlier grouping')

#!/usr/bin/env python3
"""League isolation: same player projections, different roster structures => different replacement/VORP."""
import pandas as pd
from fie_strategy_stack import replacement_levels
from fie_research_pipeline_contract import short_hash, roster_signature
rows=[]
for pos,n,base in [('QB',30,300),('RB',70,250),('WR',80,240),('TE',35,180)]:
    for i in range(n): rows.append({'position_model':pos,'fie_season_mean':base-i,'canonical_player_id':f'{pos}{i}'})
board=pd.DataFrame(rows)
a={'league_id':'A','format':'REDRAFT','total_rosters':10,'roster_positions':['QB','RB','RB','WR','WR','TE','FLEX','BN','BN']}
b={'league_id':'B','format':'REDRAFT','total_rosters':14,'roster_positions':['QB','QB','RB','RB','RB','WR','WR','WR','TE','FLEX','SUPER_FLEX','BN','BN','BN']}
ra,sa=replacement_levels(board,a);rb,sb=replacement_levels(board,b)
assert roster_signature(a)!=roster_signature(b)
assert ra!=rb and ra['QB']!=rb['QB'] and (ra['RB']!=rb['RB'] or ra['WR']!=rb['WR'])
# Identical scoring can share football projections, never final scarcity decisions.
assert short_hash({'rec':1,'pass_td':4})==short_hash({'rec':1,'pass_td':4})
print('PASS league isolation: identical player projections/scoring, different roster => different replacement')

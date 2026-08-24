#!/usr/bin/env python3
"""Small deterministic M5 policy integrity checks."""
from fie_m5 import format_strategy

# Format policy weights must remain normalized and strategy-specific.
obj=format_strategy(
    [{'position':'WR','status':'validated_candidate'}]*4,
    [{'position':'WR','status':'validated_candidate'}]*4,
    {'young_player_model':{'aggregate':[{'variant':'preseason','status':'validated_candidate'}]}},
    __import__('pandas').DataFrame(columns=['season','week','position_model','fantasy_points','fie_projection','baseline_projection'])
)
profiles=obj['profiles']
assert set(profiles)=={'REDRAFT','DYNASTY','REDRAFT_BESTBALL','DYNASTY_BESTBALL','CHOPPED'}
for k,v in profiles.items():
    assert abs(sum(v['draft_weights'].values())-1)<1e-9
    assert abs(sum(v['waiver_weights'].values())-1)<1e-9
assert profiles['REDRAFT']['draft_weights'] != profiles['DYNASTY']['draft_weights']
assert profiles['REDRAFT_BESTBALL']['draft_weights'] != profiles['CHOPPED']['draft_weights']
print('OK M5 policy integrity')

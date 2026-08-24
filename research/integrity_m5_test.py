#!/usr/bin/env python3
"""Small deterministic M5 policy integrity checks."""
from fie_m5 import WAIVER_FEATURES, format_strategy, waiver_temporal_folds
import pandas as pd

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

# Waiver validation must be able to satisfy its four-fold promotion rule on
# the seven-season historical backbone.  It must not be restricted to the
# later M4 OOS rows and should not depend on an M4 FIE projection feature.
wf=waiver_temporal_folds(pd.DataFrame({'season':[2019,2020,2021,2022,2023,2024,2025]}))
assert [t for _,t in wf]==[2021,2022,2023,2024,2025], wf
assert all(max(tr)<te for tr,te in wf)
assert 'fie_projection' not in WAIVER_FEATURES
print('OK M5 policy integrity')

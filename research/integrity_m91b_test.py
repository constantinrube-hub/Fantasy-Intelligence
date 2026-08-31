#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd
import numpy as np
from build_m91b_season_challenger import (
    canonical_team,build_enhanced_market_context,adapt_transition_profile,
    local_baseline_residual_anchor,
)

assert canonical_team("LA")=="LAR"
assert canonical_team("LAR")=="LAR"
assert canonical_team("JAC")=="JAX"
assert canonical_team("WSH")=="WAS"

# Receptions/receiving yards must create explicitly auditable current-team proxies
# when projected targets/air yards are absent.
market=[
 {"canonical_player_id":"wr1","position_model":"WR","team":"NEW","stats":{"rec":90,"rec_yd":1200}},
 {"canonical_player_id":"wr2","position_model":"WR","team":"NEW","stats":{"rec":60,"rec_yd":800}},
 {"canonical_player_id":"rb1","position_model":"RB","team":"NEW","stats":{"rush_att":220,"rec":45,"rec_yd":350}},
 {"canonical_player_id":"rb2","position_model":"RB","team":"NEW","stats":{"rush_att":120,"rec":25,"rec_yd":180}},
 {"canonical_player_id":"qb1","position_model":"QB","team":"NEW","stats":{"pass_att":520,"rush_att":70}},
]
ctx,_=build_enhanced_market_context(market,17)
assert abs(ctx["wr1"]["values"]["target_share_prior4"]-(90/220))<1e-9
assert "proxy:" in ctx["wr1"]["provenance"]["target_share_prior4"]
assert ctx["rb1"]["values"]["carry_share_prior4"]>0.5

profiles=pd.DataFrame([
 {"canonical_player_id":"wr1","position_model":"WR","profile_team":"OLD",
  "prev_fantasy_ppg":15.0,"offense_snap_share_prior4":.80,"target_share_prior4":.25,
  "red_zone_target_share_prior4":.25,"receiving_competition_index_prior4":.75,
  "receiving_competitor_count":3.0},
 {"canonical_player_id":"donor1","position_model":"WR","profile_team":"NEW",
  "offense_snap_share_prior4":.90,"target_share_prior4":.28,"red_zone_target_share_prior4":.30,
  "receiving_competition_index_prior4":.72,"receiving_competitor_count":3.0},
 {"canonical_player_id":"donor2","position_model":"WR","profile_team":"NEW",
  "offense_snap_share_prior4":.65,"target_share_prior4":.18,"red_zone_target_share_prior4":.15,
  "receiving_competition_index_prior4":.82,"receiving_competitor_count":3.0},
])
spec={"targets":[{"features":[
 "prev_fantasy_ppg","offense_snap_share_prior4","target_share_prior4",
 "red_zone_target_share_prior4","receiving_competition_index_prior4",
 "receiving_competitor_count","opportunity_change_score_prior1"
]}]}
adapt,audit=adapt_transition_profile(
 profiles.iloc[0].to_dict(),cid="wr1",pos="WR",current_team="NEW",spec=spec,
 context=ctx,profiles=profiles,availability={"depth_chart_order":1},change_scales={}
)
assert audit["status"]=="NEW_TEAM_CONTEXT_REBUILT_V2"
assert adapt["profile_team"]=="NEW"
assert abs(adapt["target_share_prior4"]-(90/220))<1e-9
assert adapt["offense_snap_share_prior4"]==.90  # depth-matched NEW-team role template
assert adapt["red_zone_target_share_prior4"]==.30
assert "offense_snap_share_prior4" in audit["role_template"]

# Local residual calibration: a backup with a huge raw-FIE level cannot teleport
# into a starter range because only nearby Sleeper baselines determine adjustment scale.
rows=[]
for i,mkt in enumerate([10,11,12,13,14,15,16,17,250,260,270,280]):
    rows.append({
      "position_model":"QB","sleeper_market_projection":mkt,
      "m91b_raw_fie_projection":(200+i*2 if mkt<20 else 240+i),
      "m91b_exact_scoring_replay":True,"m91b_team_changed":False,
      "m91b_uncertainty_spread_multiplier":1.0,
    })
df=pd.DataFrame(rows)
proj,audit=local_baseline_residual_anchor(df,min_reference=8,max_reference=8)
# Lowest-market row remains near the backup neighborhood despite a raw FIE ~200.
assert proj.iloc[0] < 25,proj.iloc[0]
assert audit.iloc[0]["status"]=="LOCAL_BASELINE_RESIDUAL_ANCHOR"

# Transition uncertainty must shrink mean correction, not increase it.
df2=df.copy()
df2.loc[0,"m91b_team_changed"]=True
df2.loc[0,"m91b_uncertainty_spread_multiplier"]=1.5
proj2,_=local_baseline_residual_anchor(df2,min_reference=8,max_reference=8)
base=float(df2.loc[0,"sleeper_market_projection"])
assert abs(float(proj2.iloc[0])-base) <= abs(float(proj.iloc[0])-base)+1e-8

print("PASS M9.1b: team aliases, richer new-team proxies/templates, local residual calibration and transition shrinkage")

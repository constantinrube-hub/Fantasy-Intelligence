#!/usr/bin/env python3
from __future__ import annotations
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from build_m91_season_challenger import (
    adapt_profile_for_new_team, build_current_team_context,
    market_history_status, is_context_feature, empirical_position_anchor,
    rehydrate_latest_profiles,
)

# Synthetic new-team market: enough structure to rebuild QB/RB/WR/TE roles.
market=[
 {"canonical_player_id":"qb","position_model":"QB","team":"NEW","stats":{"pass_att":500,"rush_att":70}},
 {"canonical_player_id":"qb2","position_model":"QB","team":"NEW","stats":{"pass_att":100,"rush_att":10}},
 {"canonical_player_id":"rb","position_model":"RB","team":"NEW","stats":{"rush_att":240,"rec_tgt":65,"rec_air_yd":110}},
 {"canonical_player_id":"rb2","position_model":"RB","team":"NEW","stats":{"rush_att":130,"rec_tgt":35,"rec_air_yd":70}},
 {"canonical_player_id":"wr","position_model":"WR","team":"NEW","stats":{"rush_att":5,"rec_tgt":145,"rec_air_yd":1650}},
 {"canonical_player_id":"wr2","position_model":"WR","team":"NEW","stats":{"rush_att":4,"rec_tgt":90,"rec_air_yd":850}},
 {"canonical_player_id":"te","position_model":"TE","team":"NEW","stats":{"rush_att":0,"rec_tgt":105,"rec_air_yd":850}},
 {"canonical_player_id":"te2","position_model":"TE","team":"NEW","stats":{"rush_att":0,"rec_tgt":55,"rec_air_yd":390}},
]
ctx,_=build_current_team_context(market,17)

cases = {
 "QB": ("qb", ["qb_pass_attempt_share_prior4","team_pass_attempts_prior4_team"]),
 "RB": ("rb", ["carry_share_prior4","target_share_prior4","backfield_competitor_count"]),
 "WR": ("wr", ["target_share_prior4","ngs_percent_share_of_intended_air_yards_prior4","receiving_competitor_count"]),
 "TE": ("te", ["target_share_prior4","ngs_percent_share_of_intended_air_yards_prior4","receiving_competitor_count"]),
}
profiles=[]
for pos,(cid,_) in cases.items():
    profiles.append({
      "canonical_player_id":cid,"profile_team":"OLD","position_model":pos,
      "prev_fantasy_ppg":20.0,
      "pfr_times_pressured_pct_prior4":25.0,
      "inside_5_carry_share_prior4":0.4,
    })
    profiles.append({
      "canonical_player_id":f"donor_{pos}","profile_team":"NEW","position_model":pos,
      "pfr_times_pressured_pct_prior4":18.0,
    })
profiles=pd.DataFrame(profiles)

for pos,(cid,role_fields) in cases.items():
    feature_list=["prev_fantasy_ppg","pfr_times_pressured_pct_prior4","inside_5_carry_share_prior4",*role_fields]
    spec={"targets":[{"features":feature_list}]}
    profile=profiles[profiles.canonical_player_id.eq(cid)].iloc[0].to_dict()
    adapted,audit=adapt_profile_for_new_team(
        profile,cid=cid,pos=pos,current_team="NEW",spec=spec,
        market_context=ctx,profiles=profiles
    )
    assert audit["team_changed"] is True, pos
    assert audit["status"]=="NEW_TEAM_CONTEXT_REBUILT",pos
    assert adapted["profile_team"]=="NEW",pos
    assert adapted["prev_fantasy_ppg"]==20.0,pos  # portable player signal retained
    assert adapted["pfr_times_pressured_pct_prior4"]==18.0,pos  # new-team environment
    assert pd.isna(adapted["inside_5_carry_share_prior4"]),pos  # old role never leaks
    assert "inside_5_carry_share_prior4" in audit["cleared_old_team_context"],pos
    for f in role_fields:
        assert f in adapted and pd.notna(adapted[f]),(pos,f,adapted.get(f))

# Distribution anchor: raw model level can be globally wrong but the current-year
# challenger stays on Sleeper's position distribution instead of trusting raw totals.
n=16
toy=pd.DataFrame({
 "position_model":["QB"]*n,
 "m91_raw_fie_projection":np.linspace(180,320,n),  # deliberately lower level
 "sleeper_market_projection":np.linspace(230,390,n),
 "m91_exact_scoring_replay":[True]*n,
 "team_changed":[False]*n,
})
anchored,audit=empirical_position_anchor(toy,min_reference=12)
assert anchored.notna().all()
assert abs(float(anchored.median())-float(toy.sleeper_market_projection.median())) < 15
assert audit.iloc[0]["status"]=="POSITION_EMPIRICAL_QUANTILE_ANCHOR"

# Self-rehydration must reconstruct a profile from player-week + committed spec
# without fitting or needing M4 OOS artifacts.
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    pw=td/"player_week.csv.gz"
    rows=[]
    for week in range(1,5):
        rows.append({
            "canonical_player_id":"qbprof","season":2025,"week":week,
            "position_model":"QB","fantasy_points":20+week,"full_name":"QB Profile",
            "team":"OLD","passing_yards":250+week,"rushing_yards":30+week,
            "prev_fantasy_ppg":np.nan,
        })
    pd.DataFrame(rows).to_csv(pw,index=False,compression="gzip")
    fake_m9={"preseason_season_projection":{"diagnostic_model_specs":{"QB":{
        "targets":[{"target":"passing_yards","features":["prev_fantasy_ppg"]}]
    }}}}
    outp=td/"profiles.csv.gz"
    prof=rehydrate_latest_profiles(player_week_path=pw,m9=fake_m9,output_path=outp)
    assert outp.is_file()
    assert len(prof)==1
    assert prof.iloc[0]["canonical_player_id"]=="qbprof"
    assert prof.iloc[0]["profile_team"]=="OLD"
    assert int(prof.iloc[0]["prev_games"])==4

with tempfile.TemporaryDirectory() as td:
    r=Path(td); (r/"2026").mkdir()
    (r/"2026"/"season_market_x.jsonl.gz").write_bytes(b"x")
    h=market_history_status(r,2026)
    assert h["status"]=="BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE"

assert is_context_feature("target_share_prior4")
assert not is_context_feature("ngs_completion_percentage_above_expectation_prior4")
print("PASS M9.1: QB/RB/WR/TE team changes rebuild new-team context; old-team role context cannot leak; distribution anchor replaces blunt mean centering")

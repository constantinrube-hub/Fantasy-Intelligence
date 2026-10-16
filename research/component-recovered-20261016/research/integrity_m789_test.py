#!/usr/bin/env python3
"""Self-contained integrity checks for M7-M9 performance research.

These tests focus on the failure modes that would be most damaging in production:
forward-label leakage, same-week premium-data leakage, ambiguous source aggregation,
non-deterministic uncertainty bands, and false FIE-vs-market claims after fail-closed
fallback.
"""
from __future__ import annotations

import gzip
import json
import math
import tempfile
from argparse import Namespace
from pathlib import Path

import pandas as pd
import numpy as np

from fie_m7 import add_future_targets
from fie_m9 import return_season_frame, score_return_stats, simulate_player_season, json_safe
from performance_source_contract import (
    TRENCH_COLUMNS,
    ROUTE_COLUMNS,
    aggregate_player_trenches_to_team,
    lag_player_features,
    lag_team_features,
    validate_player_feature_source,
    validate_team_source,
)
from build_m9_season_board import board
from fie_m8 import sequential_activation_composite


def close(a, b, tol=1e-9):
    return math.isfinite(float(a)) and abs(float(a) - float(b)) <= tol


# M7 forward targets must never cross a player-season boundary.
d = pd.DataFrame([
    {"canonical_player_id": "p1", "season": 2024, "week": 1, "fantasy_points": 10.0},
    {"canonical_player_id": "p1", "season": 2024, "week": 2, "fantasy_points": 20.0},
    {"canonical_player_id": "p1", "season": 2025, "week": 1, "fantasy_points": 99.0},
])
f = add_future_targets(d)
r1 = f[(f.season == 2024) & (f.week == 1)].iloc[0]
r2 = f[(f.season == 2024) & (f.week == 2)].iloc[0]
assert close(r1.future_fp_next1, 20.0)
assert pd.isna(r2.future_fp_next1), "M7 target leaked across season boundary"
assert close(r1.future_fp_next3, 20.0), "future-next3 should use only available same-season future weeks"

# Realised weekly team data must be shifted before rolling: week 3 sees weeks 1-2,
# never its own week-3 value.
t = pd.DataFrame([
    {"season": 2025, "week": 1, "team": "AAA", "ol_pass_block_win_rate": 0.50},
    {"season": 2025, "week": 2, "team": "AAA", "ol_pass_block_win_rate": 0.70},
    {"season": 2025, "week": 3, "team": "AAA", "ol_pass_block_win_rate": 0.99},
])
tl = lag_team_features(t, ["ol_pass_block_win_rate"], prefix="premium_", window=4)
assert pd.isna(tl.loc[tl.week.eq(2), "premium_ol_pass_block_win_rate"]).all()
assert close(tl.loc[tl.week.eq(3), "premium_ol_pass_block_win_rate"].iloc[0], 0.60)

# Same invariant for player-level route/coverage charting.
pf = pd.DataFrame([
    {"season": 2025, "week": 1, "team": "AAA", "canonical_player_id": "p1", "first_read_share": 0.20},
    {"season": 2025, "week": 2, "team": "AAA", "canonical_player_id": "p1", "first_read_share": 0.40},
    {"season": 2025, "week": 3, "team": "AAA", "canonical_player_id": "p1", "first_read_share": 0.95},
])
pl = lag_player_features(pf, ["first_read_share"], prefix="premium_", windows=(2,))
assert close(pl.loc[pl.week.eq(3), "premium_first_read_share_prior2"].iloc[0], 0.30)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # Duplicate team-week source rows must be rejected rather than silently averaged.
    dup = pd.DataFrame([
        {"season": 2025, "week": 1, "team": "AAA", "ol_pass_block_win_rate": 0.5},
        {"season": 2025, "week": 1, "team": "AAA", "ol_pass_block_win_rate": 0.7},
    ])
    path = td / "dup_team.csv"; dup.to_csv(path, index=False)
    q, health = validate_team_source(str(path), TRENCH_COLUMNS, max_season=2025)
    assert q.empty and health.duplicate_keys == 2 and health.status == "invalid_point_in_time"

    dup_p = pd.DataFrame([
        {"season": 2025, "week": 1, "team": "AAA", "canonical_player_id": "p1", "first_read_share": 0.2},
        {"season": 2025, "week": 1, "team": "AAA", "canonical_player_id": "p1", "first_read_share": 0.3},
    ])
    pathp = td / "dup_player.csv"; dup_p.to_csv(pathp, index=False)
    q, health = validate_player_feature_source(str(pathp), ROUTE_COLUMNS, max_season=2025)
    assert q.empty and health.duplicate_keys == 2 and health.status == "invalid_point_in_time"

    # Player trench aggregation must use workload weights, while keeping weak-link
    # information as a distinct challenger rather than hiding it in the average.
    pt = pd.DataFrame([
        {"season": 2025, "week": 1, "team": "AAA", "player_id": "ol1", "pass_block_snaps": 80, "ol_pass_block_win_rate": 0.80},
        {"season": 2025, "week": 1, "team": "AAA", "player_id": "ol2", "pass_block_snaps": 20, "ol_pass_block_win_rate": 0.40},
    ])
    agg = aggregate_player_trenches_to_team(pt).iloc[0]
    assert close(agg.ol_pass_block_win_rate, 0.72)
    assert agg["ol_pass_block_win_rate_weak_link"] < agg.ol_pass_block_win_rate

    # MARKET_FALLBACK must never create an artificial FIE rank edge.
    m1 = td / "m1.json"; m1.write_text(json.dumps({"scoring": {"settings": {}}}))
    m9 = td / "m9.json"; m9.write_text(json.dumps({
        "preseason_season_projection": {"model_specs": {}},
        "projection_distribution": {"position_calibration": {"QB": {"residual_mean": 0, "residual_std": 1}}},
    }))
    market = td / "market.jsonl.gz"
    rows = [
        {"sleeper_id": "1", "canonical_player_id": "p1", "full_name": "QB One", "position_model": "QB", "team": "AAA", "stats": {"pts_ppr": 300}, "adp": {"adp_ppr": 10}},
        {"sleeper_id": "2", "canonical_player_id": "p2", "full_name": "QB Two", "position_model": "QB", "team": "BBB", "stats": {"pts_ppr": 250}, "adp": {"adp_ppr": 20}},
    ]
    with gzip.open(market, "wt", encoding="utf-8") as h:
        for x in rows: h.write(json.dumps(x) + "\n")
    b = board(Namespace(m1_bundle=str(m1), m9_bundle=str(m9), market_snapshot=str(market),
                        profile_table="", adp_key="adp_ppr", games=17, simulations=500,
                        seed=94, active_probability=1.0))
    assert set(b.projection_source) == {"MARKET_FALLBACK"}
    assert b.rank_edge.isna().all(), "fallback rows must not masquerade as FIE market disagreements"

    # A validated offensive preseason spec is still not enough when the league scores
    # returns: the row must remain fail-closed until the relevant return target clears.
    prof = td / "profiles.csv"
    pd.DataFrame([{"canonical_player_id":"p1","profile_team":"AAA","prev_games":10}]).to_csv(prof,index=False)
    spec = {"targets":[{"target":"receptions","features":["prev_games"],"imputer_medians":[10.0],
                         "scaler_mean":[0.0],"scaler_scale":[1.0],"coefficients":[0.0],"intercept":5.0,"prediction_floor":0.0}]}
    m1.write_text(json.dumps({"scoring":{"settings":{"rec":1.0,"kr_yd":0.1}}}))
    m9.write_text(json.dumps({"preseason_season_projection":{"model_specs":{"WR":spec}},
                              "projection_distribution":{"position_calibration":{"WR":{"residual_mean":0,"residual_std":1}}},
                              "returner_intelligence":{"season_projection":{"model_specs":{},"latest_profiles":[]}}}))
    with gzip.open(market,"wt",encoding="utf-8") as h:
        h.write(json.dumps({"sleeper_id":"1","canonical_player_id":"p1","full_name":"WR One","position_model":"WR","team":"AAA",
                            "stats":{"pts_ppr":100},"adp":{"adp_ppr":10}})+"\n")
    rb = board(Namespace(m1_bundle=str(m1),m9_bundle=str(m9),market_snapshot=str(market),profile_table=str(prof),
                         adp_key="adp_ppr",games=17,simulations=500,seed=94,active_probability=1.0))
    assert rb.iloc[0].projection_source == "MARKET_FALLBACK" and "kr_yd" in str(rb.iloc[0].scoring_unsupported)

    # Once KR yards has its own validated season spec and same-team return profile,
    # return scoring is added as a separate raw-football component.
    ret_spec = {"features":["prev_return_att_pg"],"imputer_medians":[1.0],"scaler_mean":[0.0],"scaler_scale":[1.0],
                "coefficients":[0.0],"intercept":20.0,"prediction_floor":0.0}
    m9.write_text(json.dumps({"preseason_season_projection":{"model_specs":{"WR":spec}},
                              "projection_distribution":{"position_calibration":{"WR":{"residual_mean":0,"residual_std":1}}},
                              "returner_intelligence":{"season_projection":{"model_specs":{"kr_yd":ret_spec},
                                  "latest_profiles":[{"canonical_player_id":"p1","profile_team":"AAA","prev_return_att_pg":1.0}]}}}))
    rb2 = board(Namespace(m1_bundle=str(m1),m9_bundle=str(m9),market_snapshot=str(market),profile_table=str(prof),
                          adp_key="adp_ppr",games=17,simulations=500,seed=94,active_probability=1.0))
    assert rb2.iloc[0].projection_source == "FIE_M9_VALIDATED_PRESEASON_RETURN"
    assert close(rb2.iloc[0].fie_ppg, 7.0), rb2.iloc[0].to_dict()

    # Missing Sleeper-to-canonical mapping may use only a unique exact normalized
    # name+position match; ambiguous names remain unmatched rather than guessed.
    pd.DataFrame([{"canonical_player_id":"p1","full_name":"WR One","position_model":"WR","profile_team":"AAA","prev_games":10}]).to_csv(prof,index=False)
    m1.write_text(json.dumps({"scoring":{"settings":{"rec":1.0}}}))
    m9.write_text(json.dumps({"preseason_season_projection":{"model_specs":{"WR":spec}},
                              "projection_distribution":{"position_calibration":{"WR":{"residual_mean":0,"residual_std":1}}},
                              "returner_intelligence":{"season_projection":{"model_specs":{},"latest_profiles":[]}}}))
    with gzip.open(market,"wt",encoding="utf-8") as h:
        h.write(json.dumps({"sleeper_id":"1","canonical_player_id":None,"full_name":"WR One","position_model":"WR","team":"AAA",
                            "stats":{"pts_ppr":100},"adp":{"adp_ppr":10}})+"\n")
    nb = board(Namespace(m1_bundle=str(m1),m9_bundle=str(m9),market_snapshot=str(market),profile_table=str(prof),
                         adp_key="adp_ppr",games=17,simulations=500,seed=94,active_probability=1.0))
    assert nb.iloc[0].identity_join_method == "unique_name_position" and nb.iloc[0].canonical_player_id == "p1"
    assert nb.iloc[0].projection_source == "FIE_M9_VALIDATED_PRESEASON"



# M8 activation is a single sequential replacement spec, not an additive M7+M8 stack.
# A synthetic matchup signal that genuinely predicts the base FIE residual should clear
# the chronological gate and serialize one combined correction.
seq_df=[]; seq_oos=[]
for season in range(2019, 2026):
    for j in range(50):
        pid=f"q{j}"
        x=((j*7 + season) % 23)/22.0
        seq_df.append({"season":season,"week":j+1,"canonical_player_id":pid,"position_model":"QB","opp_public_pass_rush_index":x})
        seq_oos.append({"season":season,"week":j+1,"canonical_player_id":pid,"position_model":"QB",
                        "fantasy_points":10.0+3.0*x,"fie_projection":10.0})
seq=sequential_activation_composite(pd.DataFrame(seq_df),pd.DataFrame(seq_oos),
    {"QB":{"public_pass_rush_matchup":["opp_public_pass_rush_index"]}},
    [{"position":"QB","family":"public_pass_rush_matchup","status":"validated_candidate"}],
    {"driver_research":{"activation_composite":{"model_specs":{}}}})
assert seq.get("status") == "validated_candidate" and "QB" in seq.get("model_specs",{})
ss=seq["model_specs"]["QB"]
assert ss["component_features"]["m7"] == [] and ss["component_features"]["m8"] == ["opp_public_pass_rush_index"]
assert "do not add a separate M7 correction" in ss["semantics"]

# Return season transitions must align season N features only to season N+1 actuals.
rp = pd.DataFrame([
    {"canonical_player_id":"r1","season":2024,"week":1,"team":"AAA","position_model":"WR","return_att":2,"return_share":1.0,"primary_returner":1,"return_td":0,"kr_yd":40,"pr_yd":0,"kr_td":0,"pr_td":0,"offense_snap_share":0.5},
    {"canonical_player_id":"r1","season":2025,"week":1,"team":"AAA","position_model":"WR","return_att":1,"return_share":1.0,"primary_returner":1,"return_td":0,"kr_yd":30,"pr_yd":0,"kr_td":0,"pr_td":0,"offense_snap_share":0.6},
])
rz, rlatest = return_season_frame(rp)
assert len(rz) == 1 and int(rz.iloc[0].target_season) == 2025
assert close(rz.iloc[0].prev_kr_yd_pg, 40.0) and close(rz.iloc[0].target_kr_yd_pg, 30.0)
assert int(rlatest.iloc[0].profile_season) == 2025
assert close(score_return_stats({"kr_yd":20},{"kr_yd":0.1})["points"],2.0)

# Season simulation must be reproducible and quantiles monotone.
cal = {"residual_mean": 0.0, "residual_std": 4.0}
a = simulate_player_season(15.0, 17, cal, n=2000, seed=123)
b = simulate_player_season(15.0, 17, cal, n=2000, seed=123)
assert a == b, "M9 season distributions must be deterministic for a fixed seed"
assert a["p10"] <= a["p25"] <= a["p50"] <= a["p75"] <= a["p90"]

# Strict JSON boundary must preserve missing research diagnostics as null rather than
# emitting invalid NaN/Infinity tokens or fabricating zero-valued information.
_nonfinite = {
    "nested": [float("nan"), np.float64(float("inf")), np.float32(float("-inf"))],
    "finite": np.float64(2.5),
}
_clean = json_safe(_nonfinite)
assert _clean["nested"] == [None, None, None]
assert close(_clean["finite"], 2.5)
json.dumps(_clean, allow_nan=False)

print("PASS M7-M9 integrity: leakage, source contracts, fail-closed ranking, deterministic distributions")

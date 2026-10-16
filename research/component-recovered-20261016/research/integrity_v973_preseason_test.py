#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preseason_projection_v2 import fixture_player_week
from preseason_projection_v3 import validate_preseason_head_to_head

scoring={"pass_yd":.04,"pass_td":4,"pass_int":-2,"rush_yd":.1,"rush_td":6,"rec":1,"rec_yd":.1,"rec_td":6,"fum_lost":-2}
pw=fixture_player_week()
pv={"per_position":{"QB":{"status":"validated_candidate"}}}
report,pred,cal=validate_preseason_head_to_head(pw,scoring,pd.DataFrame(),v972_result=pv,positions=("QB",))
assert report["status"]=="complete_research_only"
g=report["governance"]
assert g["auto_activation"] is False and g["production_activation"] is False
assert g["market_inputs_used"] is False and g["adp_inputs_used"] is False
assert g["canonical_m9_modified"] is False and g["runtime_projection_modified"] is False
assert report["production_activation_allowed"] is False
assert report["replacement_claim_vs_market_fallback"] is False
assert report["comparison"]["market_fallback_head_to_head"]["status"]=="blocked_insufficient_verified_historical_market"
qb=report["per_position"]["QB"]
assert qb["folds"] >= 4, qb
assert len([x for x in report["folds"] if x["position"]=="QB"]) >= 4
assert not pred.empty and {"actual_ppg","v972_pred_ppg","m9_pred_ppg","actual_season_points","predicted_games"}.issubset(pred.columns)
assert not cal.empty and set(cal.model.astype(str)).issubset({"V972","M9"})
# A promotion-review flag may only exist after all strict component/head-to-head gates.
if qb.get("football_model_promotion_review_ready"):
    assert qb["v972_prior_gate_status"]=="validated_candidate"
    assert qb["all_v972_folds_exact_scoring_replay"] is True
    assert qb["ppg_mae_head_to_head_gate"]["robust"] is True
    assert qb["full_schedule_mae_head_to_head_gate"]["robust"] is True
    assert all(bool(qb["noninferiority"][k]) for k in ["rank_mae","spearman","top12_overlap","absolute_calibration_bias"])
print("PASS integrity_v973_preseason_test")

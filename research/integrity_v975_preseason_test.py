#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preseason_projection_v5 import validate_qb_ensemble

rows=[]
rng=np.random.default_rng(975)
for season in [2022,2023,2024,2025]:
    for i in range(54):
        actual=12 + i*0.16 + (season-2022)*0.15 + rng.normal(0,1.0)
        # V972 carries useful ranking signal but mild positive bias.
        v=actual + 0.45 + rng.normal(0,1.8)
        # M9 is better calibrated but somewhat noisier.
        m=actual + 0.20 + rng.normal(0,2.1)
        rows.append({
            "position":"QB","test_season":season,"canonical_player_id":f"{season}-{i}",
            "full_name":f"QB {season} {i}","actual_games":17 if i%8 else 12,
            "predicted_games":15.4,"actual_ppg":actual,"v972_pred_ppg":v,"m9_pred_ppg":m,
            "actual_season_points":actual*(17 if i%8 else 12),
            "v972_pred_season_points":v*15.4,"m9_pred_season_points":m*15.4,
            "metric":"PPG",
        })
pred=pd.DataFrame(rows)
v974={
    "build":"V9.7.4-EXACT-M9-COMPARATOR-AUDIT-1","status":"complete_research_only",
    "per_position":{"QB":{
        "v972_prior_gate_status":"validated_candidate",
        "all_v972_folds_exact_scoring_replay":True,
        "all_m9_folds_exact_scoring_replay":True,
        "availability_vs_full_schedule_gate":{"robust":True},
    }}
}
report,out,params,cal=validate_qb_ensemble(v974,pred)
assert report["governance"]["auto_activation"] is False
assert report["governance"]["production_activation_allowed"] is False
assert report["governance"]["test_season_leakage_allowed"] is False
assert report["source_v974"]["all_m9_folds_exact_scoring_replay"] is True
assert len(report["folds"]) == 4
assert list(params.test_season.astype(int)) == [2022,2023,2024,2025]
first=params.iloc[0]
assert abs(float(first.weight_v972)-0.5) < 1e-9
assert not bool(first.calibration_enabled)
for _,r in params.iloc[1:].iterrows():
    seasons=[int(x) for x in str(r.weight_training_seasons).split(",") if str(x).strip()]
    assert all(x < int(r.test_season) for x in seasons)
assert not out.empty
assert {"ensemble_pred_ppg","weight_v972","calibration_enabled"}.issubset(out.columns)
assert not cal.empty
assert set(cal.model.astype(str)).issubset({"ENSEMBLE","V972","M9"})
print("PASS integrity_v975_preseason_test")

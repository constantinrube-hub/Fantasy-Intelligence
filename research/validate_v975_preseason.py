#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

def main():
    p=argparse.ArgumentParser(); p.add_argument("output_dir"); a=p.parse_args()
    root=Path(a.output_dir)
    files=[
        "preseason_v975_validation.json","preseason_v975_predictions.csv",
        "preseason_v975_params.csv","preseason_v975_calibration.csv"
    ]
    missing=[x for x in files if not (root/x).is_file()]
    if missing: raise AssertionError(f"missing V9.7.5 outputs: {missing}")
    r=json.loads((root/"preseason_v975_validation.json").read_text(encoding="utf-8"))
    assert r.get("build")=="V9.7.5-QB-CHRONOLOGICAL-ENSEMBLE-CALIBRATION-1"
    assert r.get("status") in {"complete_research_only","blocked_insufficient_chronological_folds"}
    g=r.get("governance") or {}
    assert g.get("auto_activation") is False
    assert g.get("production_activation") is False
    assert g.get("production_activation_allowed") is False
    assert g.get("canonical_m9_modified") is False
    assert g.get("canonical_m1_modified") is False
    assert g.get("runtime_projection_modified") is False
    assert g.get("v972_shadow_modified") is False
    assert g.get("market_inputs_used") is False and g.get("adp_inputs_used") is False
    assert g.get("source_predictions_are_v974_exact_oof") is True
    assert g.get("chronological_stacking") is True
    assert g.get("test_season_leakage_allowed") is False
    assert g.get("statistical_gates_lowered") is False
    assert r.get("production_activation_allowed") is False
    assert r.get("replacement_claim_vs_market_fallback") is False
    src=r.get("source_v974") or {}
    assert src.get("all_v972_folds_exact_scoring_replay") is True
    assert src.get("all_m9_folds_exact_scoring_replay") is True
    qb=(r.get("per_position") or {}).get("QB") or {}
    if qb.get("football_model_promotion_review_ready"):
        assert (qb.get("ppg_mae_head_to_head_gate_vs_exact_m9") or {}).get("robust") is True
        assert (qb.get("full_schedule_mae_head_to_head_gate_vs_exact_m9") or {}).get("robust") is True
        ni=qb.get("standalone_noninferiority") or {}
        for k in [
            "ppg_mae_better_or_equal_best_standalone","full_schedule_mae_better_or_equal_best_standalone",
            "rank_mae","spearman","top12_overlap","absolute_calibration_bias"
        ]: assert ni.get(k) is True, (k,ni)
    if qb.get("expected_season_points_ready"):
        assert qb.get("football_model_promotion_review_ready") is True
        assert (qb.get("expected_season_mae_head_to_head_gate_vs_exact_m9") or {}).get("robust") is True
        assert (src.get("availability_gate") or {}).get("robust") is True
        assert (qb.get("standalone_noninferiority") or {}).get("expected_season_mae_better_or_equal_best_standalone") is True
    params=pd.read_csv(root/"preseason_v975_params.csv",low_memory=False)
    if not params.empty:
        assert {"test_season","weight_v972","weight_m9","calibration_enabled","weight_training_seasons"}.issubset(params.columns)
        assert ((pd.to_numeric(params.weight_v972,errors="coerce")>=0)&(pd.to_numeric(params.weight_v972,errors="coerce")<=1)).all()
        for _,row in params.iterrows():
            train=[int(x) for x in str(row.weight_training_seasons).split(",") if x and x!="nan"]
            assert all(x < int(row.test_season) for x in train), (row.test_season,train)
    pred=pd.read_csv(root/"preseason_v975_predictions.csv",low_memory=False)
    if not pred.empty:
        need={"position","test_season","canonical_player_id","actual_ppg","v972_pred_ppg","m9_pred_ppg",
              "ensemble_pred_ppg","actual_season_points","ensemble_pred_season_points","weight_v972"}
        assert need.issubset(pred.columns), sorted(need-set(pred.columns))
        assert set(pred.position.astype(str))=={"QB"}
    cal=pd.read_csv(root/"preseason_v975_calibration.csv",low_memory=False)
    if not cal.empty:
        assert set(cal.model.astype(str)).issubset({"ENSEMBLE","V972","M9"})
    print(
        "PASS V9.7.5 QB ensemble",
        "review=",r.get("football_model_promotion_review_positions",[]),
        "expected=",r.get("expected_season_points_ready_positions",[])
    )
if __name__=="__main__": main()

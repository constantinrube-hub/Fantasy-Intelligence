#!/usr/bin/env python3
"""Validate V9.7.4 exact-M9 comparator audit outputs."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

def main():
    p = argparse.ArgumentParser()
    p.add_argument("output_dir")
    a = p.parse_args()
    root = Path(a.output_dir)
    files = [
        "preseason_v974_validation.json",
        "preseason_v974_predictions.csv",
        "preseason_v974_calibration.csv",
    ]
    missing = [x for x in files if not (root/x).is_file()]
    if missing:
        raise AssertionError(f"missing V9.7.4 outputs: {missing}")

    r = json.loads((root/"preseason_v974_validation.json").read_text(encoding="utf-8"))
    assert r.get("build") == "V9.7.4-EXACT-M9-COMPARATOR-AUDIT-1"
    assert r.get("status") == "complete_research_only"
    g = r.get("governance") or {}
    assert g.get("auto_activation") is False
    assert g.get("production_activation") is False
    assert g.get("canonical_m9_modified") is False
    assert g.get("canonical_m1_modified") is False
    assert g.get("runtime_projection_modified") is False
    assert g.get("market_inputs_used") is False
    assert g.get("adp_inputs_used") is False
    assert g.get("comparator_only_m9_scoring_hardening") is True
    assert g.get("exact_m9_comparator_required_for_promotion_review") is True
    assert g.get("v973_statistical_gates_changed") is False
    assert r.get("production_activation_allowed") is False
    assert r.get("replacement_claim_vs_market_fallback") is False

    for pos, meta in (r.get("per_position") or {}).items():
        assert meta.get("exact_m9_comparator_required") is True
        if meta.get("football_model_promotion_review_ready"):
            assert meta.get("all_m9_folds_exact_scoring_replay") is True
            assert meta.get("exact_m9_comparator_gate") is True
            assert meta.get("v972_prior_gate_status") == "validated_candidate"
            assert (meta.get("ppg_mae_head_to_head_gate") or {}).get("robust") is True
            assert (meta.get("full_schedule_mae_head_to_head_gate") or {}).get("robust") is True
            ni = meta.get("noninferiority") or {}
            assert all(ni.get(k) is True for k in [
                "rank_mae", "spearman", "top12_overlap", "absolute_calibration_bias"
            ])
        if meta.get("expected_season_points_ready"):
            assert meta.get("football_model_promotion_review_ready") is True
            assert (meta.get("expected_season_mae_head_to_head_gate") or {}).get("robust") is True
            assert (meta.get("availability_vs_full_schedule_gate") or {}).get("robust") is True

    preds = pd.read_csv(root/"preseason_v974_predictions.csv", low_memory=False)
    if not preds.empty:
        need = {
            "position","test_season","canonical_player_id","actual_games","predicted_games",
            "actual_ppg","v972_pred_ppg","m9_pred_ppg","actual_season_points",
            "v972_pred_season_points","m9_pred_season_points","metric",
        }
        assert need.issubset(preds.columns), sorted(need-set(preds.columns))
        assert set(preds.metric.astype(str).unique()).issubset({"PPG","SEASON"})

    cal = pd.read_csv(root/"preseason_v974_calibration.csv", low_memory=False)
    if not cal.empty:
        need = {"position","test_season","metric","model","decile","n","mean_prediction","mean_actual","bias"}
        assert need.issubset(cal.columns), sorted(need-set(cal.columns))
        assert set(cal.model.astype(str).unique()).issubset({"V972","M9"})

    exact = {
        p: bool((m or {}).get("all_m9_folds_exact_scoring_replay"))
        for p,m in (r.get("per_position") or {}).items()
    }
    print(
        "PASS V9.7.4 comparator audit "
        f"review={r.get('football_model_promotion_review_positions',[])} "
        f"expected={r.get('expected_season_points_ready_positions',[])} "
        f"m9_exact={exact}"
    )

if __name__ == "__main__":
    main()

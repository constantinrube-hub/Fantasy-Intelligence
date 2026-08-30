#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

REQUIRED=[
    "strategy_stack.json","preseason_v2.json","preseason_v973_validation.json","preseason_v973_predictions.csv","preseason_v973_calibration.csv",
    "season_projection_v972.csv","market_movement.csv","adp_outcome_curves.csv","league_value_board.csv","draft_actions.csv",
    "injury_opportunity.json","market_mistake_research.json","actionable_findings.json"
]

def main():
    p=argparse.ArgumentParser(); p.add_argument("output_dir"); a=p.parse_args(); root=Path(a.output_dir)
    missing=[x for x in REQUIRED if not (root/x).exists()]
    if missing: raise AssertionError(f"missing strategy outputs: {missing}")
    s=json.loads((root/"strategy_stack.json").read_text()); pv=json.loads((root/"preseason_v2.json").read_text()); f=json.loads((root/"actionable_findings.json").read_text())
    v973=json.loads((root/"preseason_v973_validation.json").read_text())
    assert s.get("status")=="complete_research_only"
    g=s.get("governance") or {}; assert g.get("auto_activation") is False; assert g.get("canonical_projections_modified") is False; assert g.get("football_model_uses_adp") is False
    prov=s.get("provenance") or {}; assert prov.get("resolved_adp_key") in {"adp_ppr","adp_half_ppr","adp_std","adp_2qb","adp_dynasty_ppr","adp_dynasty_half_ppr","adp_dynasty_std","adp_dynasty_2qb"}
    assert "phase_readiness" in s
    assert pv.get("governance",{}).get("market_inputs_used") is False; assert pv.get("production_activation_allowed") is False
    assert f.get("governance",{}).get("auto_activation") is False

    # V9.7.3 is evaluation-only and may not use market data or grant runtime rights.
    vg=v973.get("governance") or {}
    assert v973.get("status")=="complete_research_only"
    assert vg.get("auto_activation") is False and vg.get("production_activation") is False
    assert vg.get("market_inputs_used") is False and vg.get("adp_inputs_used") is False
    assert vg.get("canonical_m9_modified") is False and vg.get("runtime_projection_modified") is False
    assert v973.get("production_activation_allowed") is False
    assert v973.get("replacement_claim_vs_market_fallback") is False
    market_h2h=((v973.get("comparison") or {}).get("market_fallback_head_to_head") or {})
    assert market_h2h.get("status") in {"blocked_insufficient_verified_historical_market","verified_complete"}
    for pos,meta in (v973.get("per_position") or {}).items():
        if meta.get("football_model_promotion_review_ready"):
            assert meta.get("v972_prior_gate_status")=="validated_candidate"
            assert meta.get("all_v972_folds_exact_scoring_replay") is True
            assert (meta.get("ppg_mae_head_to_head_gate") or {}).get("robust") is True
            assert (meta.get("full_schedule_mae_head_to_head_gate") or {}).get("robust") is True
            ni=meta.get("noninferiority") or {}
            assert ni.get("rank_mae") is True and ni.get("spearman") is True and ni.get("top12_overlap") is True and ni.get("absolute_calibration_bias") is True
        if meta.get("expected_season_points_ready"):
            assert meta.get("football_model_promotion_review_ready") is True
            assert (meta.get("expected_season_mae_head_to_head_gate") or {}).get("robust") is True
            assert (meta.get("availability_vs_full_schedule_gate") or {}).get("robust") is True

    preds=pd.read_csv(root/"preseason_v973_predictions.csv",low_memory=False)
    if not preds.empty:
        need={"position","test_season","canonical_player_id","actual_games","predicted_games","actual_ppg","v972_pred_ppg","m9_pred_ppg",
              "actual_season_points","v972_pred_season_points","m9_pred_season_points","metric"}
        assert need.issubset(preds.columns), f"missing V9.7.3 prediction columns: {sorted(need-set(preds.columns))}"
        assert set(preds.metric.astype(str).unique()).issubset({"PPG","SEASON"})
    cal=pd.read_csv(root/"preseason_v973_calibration.csv",low_memory=False)
    if not cal.empty:
        need={"position","test_season","metric","model","decile","n","mean_prediction","mean_actual","bias"}
        assert need.issubset(cal.columns), f"missing V9.7.3 calibration columns: {sorted(need-set(cal.columns))}"
        assert set(cal.model.astype(str).unique()).issubset({"V972","M9"})

    shadow=pd.read_csv(root/"season_projection_v972.csv",low_memory=False)
    if not shadow.empty:
        need={"m9_strategy_projection","m9_fie_season_mean","strategy_projection","strategy_projection_source",
              "projection_delta_vs_m9","v972_shadow_applied","v972_shadow_status"}
        assert need.issubset(shadow.columns), f"missing V9.7.2 shadow columns: {sorted(need-set(shadow.columns))}"
        applied=shadow[shadow.v972_shadow_applied.astype(str).str.lower().isin(["true","1"])]
        if not applied.empty:
            eligible=set(str(x) for x in (pv.get("production_eligible_positions") or []))
            assert set(applied.position_model.astype(str)).issubset(eligible), "non-validated position received V9.7.2 shadow"
            assert (applied.strategy_projection_source=="V972_VALIDATED_COMPONENT_SHADOW").all()
            assert pd.to_numeric(applied.strategy_projection,errors="coerce").notna().all()
        assert "fie_season_mean" in shadow.columns and "m9_fie_season_mean" in shadow.columns
    meta=s.get("season_projection_v972_meta") or {}
    assert meta.get("production_activation") is False and meta.get("market_inputs_used") is False
    assert meta.get("canonical_m9_columns_modified") is False
    v973meta=s.get("preseason_v973_meta") or {}
    assert v973meta.get("production_activation_allowed") is False
    assert v973meta.get("market_fallback_replacement_validated") is False

    board=pd.read_csv(root/"league_value_board.csv",low_memory=False)
    if not board.empty:
        assert {"fie_value_projection","fie_vorp","replacement_points","rank_edge","value_label","draft_relevant","actionable_draft_signal","draft_horizon","watchlist_horizon"}.issubset(board.columns)
        targets=board[board.get("actionable_draft_signal",False).astype(bool) & board.value_label.isin(["STRONG_VALUE","VALUE"])]
        if not targets.empty:
            assert (pd.to_numeric(targets.fie_vorp,errors="coerce") >= 0).all(), "actionable TARGET below replacement"
            assert targets.current_player_match.astype(bool).all(), "actionable TARGET without current player match"
            assert targets.within_watchlist_horizon.astype(bool).all(), "actionable TARGET beyond watchlist horizon"
    for row in f.get("findings") or []:
        if row.get("surface")=="DRAFT":
            assert row.get("player_id"), "draft finding lacks stable identity"
            ev=row.get("evidence") or {}
            if row.get("action")=="TARGET": assert float(ev.get("fie_vorp")) >= 0
    print(f"PASS strategy-stack validation rows={len(board)} findings={f.get('finding_count',0)} preseason_positions={pv.get('production_eligible_positions',[])} v972_applied={meta.get('shadow_applied',0)} v973_review={v973.get('football_model_promotion_review_positions',[])}")
if __name__=="__main__": main()

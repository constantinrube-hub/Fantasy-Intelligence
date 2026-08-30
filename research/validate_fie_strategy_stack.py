#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

REQUIRED=["strategy_stack.json","preseason_v2.json","season_projection_v972.csv","market_movement.csv","adp_outcome_curves.csv","league_value_board.csv","draft_actions.csv","injury_opportunity.json","market_mistake_research.json","actionable_findings.json"]

def main():
    p=argparse.ArgumentParser(); p.add_argument("output_dir"); a=p.parse_args(); root=Path(a.output_dir)
    missing=[x for x in REQUIRED if not (root/x).exists()]
    if missing: raise AssertionError(f"missing strategy outputs: {missing}")
    s=json.loads((root/"strategy_stack.json").read_text()); pv=json.loads((root/"preseason_v2.json").read_text()); f=json.loads((root/"actionable_findings.json").read_text())
    assert s.get("status")=="complete_research_only"
    g=s.get("governance") or {}; assert g.get("auto_activation") is False; assert g.get("canonical_projections_modified") is False; assert g.get("football_model_uses_adp") is False
    prov=s.get("provenance") or {}; assert prov.get("resolved_adp_key") in {"adp_ppr","adp_half_ppr","adp_std","adp_2qb","adp_dynasty_ppr","adp_dynasty_half_ppr","adp_dynasty_std","adp_dynasty_2qb"}
    assert "phase_readiness" in s
    assert pv.get("governance",{}).get("market_inputs_used") is False; assert pv.get("production_activation_allowed") is False
    assert f.get("governance",{}).get("auto_activation") is False
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
        # Canonical M9 fields must still be present side-by-side for rollback.
        assert "fie_season_mean" in shadow.columns and "m9_fie_season_mean" in shadow.columns
    meta=s.get("season_projection_v972_meta") or {}
    assert meta.get("production_activation") is False and meta.get("market_inputs_used") is False
    assert meta.get("canonical_m9_columns_modified") is False
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
    print(f"PASS strategy-stack validation rows={len(board)} findings={f.get('finding_count',0)} preseason_positions={pv.get('production_eligible_positions',[])} v972_applied={meta.get('shadow_applied',0)}")
if __name__=="__main__": main()

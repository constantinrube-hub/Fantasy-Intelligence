#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

REQUIRED=["strategy_stack.json","preseason_v2.json","market_movement.csv","adp_outcome_curves.csv","league_value_board.csv","draft_actions.csv","injury_opportunity.json","market_mistake_research.json","actionable_findings.json"]

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
    print(f"PASS strategy-stack validation rows={len(board)} findings={f.get('finding_count',0)} preseason_positions={pv.get('production_eligible_positions',[])}")
if __name__=="__main__": main()

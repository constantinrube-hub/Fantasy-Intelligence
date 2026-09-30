#!/usr/bin/env python3
"""Integrity test for the Sol weekly-lineup design boundary."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/in-season-pr2-weekly-lineup-decision-support-design.json"
DOC = ROOT / "docs/audits/IN_SEASON_PR2_WEEKLY_LINEUP_DECISION_SUPPORT_DESIGN.md"
RUNTIME = ROOT / "config/contracts/runtime-contracts.json"
DECISION = ROOT / "research/decision_validation_contract.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks = 0
    cfg = read(CONFIG)
    runtime = read(RUNTIME)
    decision = read(DECISION)
    doc = DOC.read_text(encoding="utf-8")

    assert cfg["status"] == "SOL_DESIGN_COMPLETE_TERRA_IMPLEMENTATION_AUTHORIZED"
    checks += 1
    assert cfg["canonical_owners"]["slot_and_position_contract"] == "config/contracts/runtime-contracts.json"
    checks += 1
    assert runtime.get("roster_slots") and runtime.get("position_aliases")
    checks += 1
    assert cfg["lineup_solver"]["greedy_assignment_forbidden"] is True
    assert cfg["lineup_solver"]["player_max_assignments"] == 1
    checks += 1
    assert cfg["lineup_solver"]["missing_projection_zero_imputation"] is False
    assert cfg["lineup_solver"]["optimal_claim_requires_complete_material_candidate_coverage"] is True
    checks += 1
    for fmt in ("REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"):
        assert "NOT_APPLICABLE_AUTOMATIC_LINEUP" in cfg["format_policy"][fmt]
    checks += 1
    assert cfg["objectives"]["primary"] == "maximize sum(decision_weekly_projection)"
    assert cfg["objectives"]["opponent_context_changes_primary"] is False
    assert cfg["objectives"]["max_win_actionable"] is False
    checks += 1
    assert cfg["availability_policy"]["projection_haircut"] is False
    assert cfg["availability_policy"]["invented_availability_probability"] is False
    checks += 1
    assert cfg["lock_policy"]["started_player_fixed_to_submitted_state"] is True
    assert cfg["lock_policy"]["unknown_or_stale_schedule"] == "BLOCKED_LOCK_STATE_UNRESOLVED"
    checks += 1
    assert cfg["portfolio"]["dynamic_enabled_registry"] is True
    assert cfg["portfolio"]["hard_coded_league_count"] is False
    assert cfg["portfolio"]["scoring_isolation"] == "A_TO_B_TO_A_BYTE_EQUIVALENT"
    checks += 1
    start_sit = decision["domains"]["start_sit"]
    assert cfg["evaluation"]["minimum_rows"] == start_sit["minimum_rows"] == 300
    assert cfg["evaluation"]["minimum_temporal_periods"] == start_sit["minimum_temporal_periods"] == 8
    checks += 1
    assert cfg["evaluation"]["target_week_realized_stats_excluded"] is True
    assert cfg["governance"]["transaction_or_lineup_execution"] is False
    assert cfg["governance"]["app_integration_authorized"] is False
    checks += 1
    for phrase in (
        "maximum-weight bipartite assignment",
        "NOT_APPLICABLE_AUTOMATIC_LINEUP",
        "INACTIVE_CONTINGENCY",
        "BLOCKED_LOCK_STATE_UNRESOLVED",
        "A -> B -> A",
        "300 eligible rows and eight temporal periods",
        "M9 remains production champion",
    ):
        assert phrase in doc, phrase
    checks += 1

    print(f"PASS In-Season PR2 weekly lineup Sol design integrity ({checks} checks)")


if __name__ == "__main__":
    main()


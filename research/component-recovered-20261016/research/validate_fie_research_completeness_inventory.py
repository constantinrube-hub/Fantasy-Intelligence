#!/usr/bin/env python3
"""Fail-closed validator for the Tranche 6B evidence inventory."""
from __future__ import annotations

import argparse
from pathlib import Path

from build_fie_research_completeness_inventory import BLOCKERS, DIMENSIONS, OFFENSE, SCHEMA, STATES, build_inventory
from fie_research_pipeline_contract import ROOT, canonical_bytes, load_json


def validate(obj: dict) -> None:
    assert obj.get("schema") == SCHEMA
    assert obj.get("governance") == {"research_only": True, "automatic_promotion": False, "production_behavior_changed": False, "cross_league_promotion": False}
    summary = obj.get("summary") or {}
    assert summary.get("authoritative_verdict") == ["PIPELINE_COVERAGE_COMPLETE", "FOOTBALL_EVIDENCE_INCOMPLETE", "PROMOTION_BLOCKED"]
    assert summary.get("league_count") == 22
    assert len(summary.get("formats") or []) == 6
    assert summary.get("completed_pipeline_count") == 22
    assert summary.get("report_complete_count") == 22
    assert summary.get("app_publish_complete_count") == 22
    assert summary.get("m91c_blocked_promotion_count") == 22
    assert summary.get("v974_exact_comparator_pass_count") == 0
    assert summary.get("offense_blocked_count") == 88
    assert not any(state == "PRODUCTION_AUTHORIZED" for state in (summary.get("cell_states") or {}))
    assert len(obj.get("leagues") or []) == 22
    for league in obj["leagues"]:
        assert set(league.get("model_gate") or {}) == set(OFFENSE)
        assert all(str(value).startswith("BLOCKED_") for value in league["model_gate"].values())
        assert league.get("m91c", {}).get("production_eligible") is False
        cells = league.get("cells") or []
        assert len(cells) == len(OFFENSE) * 4 * len(DIMENSIONS)
        keys = set()
        for cell in cells:
            assert cell.get("position") in OFFENSE
            assert cell.get("dimension") in DIMENSIONS
            assert cell.get("state") in STATES
            assert set(cell.get("blockers") or []).issubset(BLOCKERS)
            if cell["state"] != "PRODUCTION_AUTHORIZED":
                assert cell["blockers"], cell
            keys.add(tuple(cell.get(k) for k in ("position", "horizon", "feature_family", "decision_domain", "dimension")))
        assert len(keys) == len(cells)
    sources = obj.get("sources") or {}
    assert sources.get("market", {}).get("years") == ["2026"]
    assert sources.get("availability", {}).get("years") == ["2026"]
    assert sources.get("market", {}).get("historical_completed_seasons") == []
    assert sources.get("availability", {}).get("historical_completed_seasons") == []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="data/research/portfolio/2026/research-completeness-inventory.json")
    parser.add_argument("--verify-deterministic", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    obj = load_json(path, {})
    validate(obj)
    if args.verify_deterministic:
        regenerated = build_inventory()
        assert canonical_bytes(obj) == canonical_bytes(regenerated), "inventory is stale or non-deterministic"
    print(f"PASS Tranche 6B completeness inventory leagues={obj['summary']['league_count']} cells={sum(len(x['cells']) for x in obj['leagues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

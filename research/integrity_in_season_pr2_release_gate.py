#!/usr/bin/env python3
"""One deterministic, no-network release gate for In-Season PR2 lineups."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "research/integrity_weekly_lineup_exact_solver_test.py",
    "research/integrity_in_season_pr2_weekly_lineups_test.py",
    "research/integrity_in_season_pr2_lineup_capture_test.py",
    "research/integrity_in_season_pr2_lineup_workflow_test.py",
    "research/integrity_in_season_pr2_lineup_outcome_adapter_test.py",
    "research/integrity_in_season_pr2_lineup_nflverse_outcome_test.py",
    "research/integrity_in_season_pr2_lineup_outcome_test.py",
    "research/integrity_in_season_pr2_lineup_evaluation_test.py",
    "research/integrity_in_season_pr2_lineup_outcome_workflow_test.py",
    "research/integrity_current_storage_test.py",
)
WORKFLOWS = (
    ".github/workflows/capture-fie-pr2-weekly-lineups.yml",
    ".github/workflows/evaluate-fie-pr2-weekly-lineups.yml",
)


def main() -> None:
    design = json.loads((ROOT / "config/in-season-pr2-weekly-lineup-decision-support-design.json").read_text(encoding="utf-8"))
    assert design.get("governance", {}).get("production_model") == "M9"
    assert design.get("evaluation", {}).get("minimum_rows") == 300
    capture = (ROOT / WORKFLOWS[0]).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in capture and "schedule:" in capture
    assert "purpose: weekly_lineups" in capture and "--schedule-check --github-output" in capture
    assert "  push:" not in capture
    outcome = (ROOT / WORKFLOWS[1]).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in outcome
    assert "schedule:" not in outcome and "  push:" not in outcome
    for relative in TESTS:
        path = ROOT / relative
        assert path.is_file(), relative
        subprocess.run([sys.executable, relative], cwd=ROOT, check=True)
    print("PASS In-Season PR2 release gate: exact lineups, scheduled immutable capture, manual outcomes, and 23-league storage preserved")


if __name__ == "__main__":
    main()

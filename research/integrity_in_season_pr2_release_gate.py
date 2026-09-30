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
    for relative in WORKFLOWS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text, relative
        assert "schedule:" not in text and "  push:" not in text, relative
    for relative in TESTS:
        path = ROOT / relative
        assert path.is_file(), relative
        subprocess.run([sys.executable, relative], cwd=ROOT, check=True)
    print("PASS In-Season PR2 release gate: exact lineups, immutable capture/outcomes, manual-only workflows, and 23-league storage preserved")


if __name__ == "__main__":
    main()

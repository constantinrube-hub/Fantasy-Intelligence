#!/usr/bin/env python3
"""Static guardrails for the manually dispatched PR2 outcome workflow."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/evaluate-fie-pr2-weekly-lineups.yml"


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text and "schedule:" not in text and "  push:" not in text
    assert "github.ref == 'refs/heads/main'" in text
    for token in ("capture_path:", "outcome_revision_id:", "capture_in_season_pr2_lineup_nflverse_outcomes.py", "adapt_in_season_pr2_lineup_outcome_stats.py", "build_in_season_pr2_lineup_outcome.py", "evaluate_in_season_pr2_lineups.py"):
        assert token in text, token
    assert "outcomes/source-inputs" in text and "outcomes/$INPUT_OUTCOME_REVISION_ID" in text
    assert "pip install --disable-pip-version-check -r research/requirements.txt" in text
    assert "git add data/research/evaluation" in text
    assert "api.sleeper" not in text and "schedule:" not in text
    print("PASS PR2 lineup outcome workflow is manual, bounded, and nflverse-source-only")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Static guardrails for automatic and manual PR2 outcome evaluation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/evaluate-fie-pr2-weekly-lineups.yml"


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text and "schedule:" in text and "  push:" not in text
    assert "purpose: weekly_lineup_outcomes" in text and "needs: calendar" in text
    assert "needs.calendar.outputs.allowed == 'true' && github.ref == 'refs/heads/main'" in text
    assert "cancel-in-progress: false" in text
    for token in ("capture_path:", "outcome_revision_id:", "resolve_in_season_pr2_lineup_outcome_target.py", "--github-output", "capture_in_season_pr2_lineup_nflverse_outcomes.py", "adapt_in_season_pr2_lineup_outcome_stats.py", "build_in_season_pr2_lineup_outcome.py", "evaluate_in_season_pr2_lineups.py"):
        assert token in text, token
    assert "steps.outcome_policy.outputs.capture_allowed == 'true'" in text
    assert "outcomes/source-inputs" in text and "outcomes/$INPUT_OUTCOME_REVISION_ID" in text
    assert "pip install --disable-pip-version-check -r research/requirements.txt" in text
    assert "git add data/research/evaluation" in text
    assert "api.sleeper" not in text
    print("PASS PR2 lineup outcome workflow is scheduled, duplicate-safe, manually revisable, and nflverse-source-only")


if __name__ == "__main__":
    main()

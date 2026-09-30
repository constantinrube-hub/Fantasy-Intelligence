#!/usr/bin/env python3
"""Static guard for the controlled manual PR2 lineup capture workflow."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    workflow = (ROOT / ".github/workflows/capture-fie-pr2-weekly-lineups.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "capture_in_season_pr2_lineup_evidence.py" in workflow
    assert "--write-canonical-if-eligible" in workflow
    assert "git add data/research/evaluation" in workflow
    assert "git push origin HEAD:main" in workflow
    assert "app/" not in workflow and "dist/" not in workflow
    print("PASS In-Season PR2 manual lineup capture workflow")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Guard the single-owner boundary between Window 1B and PR2."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    workflow = (ROOT / ".github/workflows/build-fie-window1b-evaluation.yml").read_text(encoding="utf-8")
    assert "name: Build FIE Window 1B Season Preview" in workflow
    assert "workflow_dispatch:" in workflow and "schedule:" not in workflow and "  push:" not in workflow
    assert "weekly-snapshot" not in workflow and "weekly-evaluate" not in workflow
    assert "python research/window1b_evaluation.py season-preview" in workflow
    assert "data/research/evaluation/2026/preseason/season-preview-v1.json" in workflow
    assert "data/research/evaluation/2026/preseason/season-preview-v1.md" in workflow
    assert "git add data/research/evaluation/2026" not in workflow

    help_result = subprocess.run(
        [sys.executable, "research/window1b_evaluation.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "season-preview" in help_result.stdout
    assert "weekly-snapshot" not in help_result.stdout and "weekly-evaluate" not in help_result.stdout

    contract = json.loads((ROOT / "config/window1b-season-preview-weekly-evaluation.json").read_text(encoding="utf-8"))
    weekly = contract["weekly_evaluation"]
    assert weekly["operational_status"] == "SUPERSEDED_BY_PR2_PRESERVED_READ_ONLY"
    assert weekly["new_window1b_weekly_writes_authorized"] is False
    assert weekly["historical_window1b_artifacts_preserved"] is True
    assert "evaluate-fie-pr2-weekly-lineups.yml" in weekly["canonical_owner"]

    consumer = (ROOT / "research/window1c_weekly_actions.py").read_text(encoding="utf-8")
    assert 'lineups/outcomes' in consumer
    assert '"owner": "PR2"' in consumer
    assert '"owner": "WINDOW1B_LEGACY"' in consumer
    print("PASS Window 1B/PR2 single weekly-evaluation ownership with legacy preservation")


if __name__ == "__main__":
    main()

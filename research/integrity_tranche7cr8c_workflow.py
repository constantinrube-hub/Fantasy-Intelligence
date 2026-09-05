#!/usr/bin/env python3
"""Static boundary for the R8C default-branch workflow preflight."""
from __future__ import annotations

import argparse
import json
import re
import subprocess

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7cr8c-workflow-preflight.yml"
OPERATIONAL = "capture-fie-m10-prospective.yml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("target", "closure"), default="target"); args = parser.parse_args(argv)
    target = json.loads((ROOT / "config/tranche7cr8c-workflow-preflight.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    operational = (ROOT / ".github/workflows" / OPERATIONAL).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8C" and target["source_r8b_closure"] == "95a43fb"
    if args.mode == "target":
        assert target["lifecycle"] == "preflight_active" and set(lifecycle["active_controlled_workflows"]) == {WORKFLOW}
        assert re.search(r"(?m)^  push:", workflow)
    else:
        assert target["lifecycle"] == "closed_manual_validation" and WORKFLOW not in lifecycle["active_controlled_workflows"]
        assert not re.search(r"(?m)^  push:", workflow)
    assert re.search(r"(?m)^  workflow_dispatch:", workflow) and not re.search(r"(?m)^  schedule:", workflow)
    assert "permissions: {contents: read}" in workflow
    assert "if: github.ref == 'refs/heads/main'" in operational and "permissions: {contents: write}" in operational
    assert "cancel-in-progress: false" in operational and "git push origin HEAD:main" in operational and "git push --force" not in operational
    assert "git diff --cached --quiet" in operational and operational.count("git rebase origin/main") == 2
    assert "validate_m10_prospective_write_plan.py" in operational and "data/research/prospective/m10" in operational
    for path in ("research/capture_m10_prospective_weekly_raw.py", "research/run_m10_prospective_weekly_capture.py", "research/validate_m10_prospective_write_plan.py"):
        assert (ROOT / path).is_file(), path
    forbidden = subprocess.run(["git", "grep", "-l", "capture-fie-m10-prospective", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    print(f"PASS R8C {args.mode}: main-only workflow is write-bounded, non-deploying, and research-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

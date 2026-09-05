#!/usr/bin/env python3
"""Controlled fixture target boundary for the R8C workflow."""
from __future__ import annotations

import json
import re
import subprocess

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7cr8c-workflow-target.yml"


def main() -> int:
    target = json.loads((ROOT / "config/tranche7cr8c-workflow-target.json").read_text(encoding="utf-8"))
    preflight = json.loads((ROOT / "config/tranche7cr8c-workflow-preflight.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8C" and target["source_preflight_commit"] == "d7bd020"
    assert target["lifecycle"] == "target_active" and target["artifact_policy"] == "controlled_no_network_operational_dry_run"
    assert preflight["lifecycle"] == "closed_manual_validation"
    assert set(lifecycle["active_controlled_workflows"]) == {WORKFLOW}
    assert re.search(r"(?m)^  push:", workflow) and re.search(r"(?m)^  workflow_dispatch:", workflow) and not re.search(r"(?m)^  schedule:", workflow)
    assert "permissions: {contents: read}" in workflow and "--fixture" in workflow and "run_m10_prospective_weekly_capture.py" in workflow
    forbidden = subprocess.run(["git", "grep", "-l", "validate-fie-tranche7cr8c-workflow-target", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    print("PASS R8C target: controlled operational dry run is no-network, read-only, and non-production")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Controlled target boundary for R8B's fixture-only weekly producer."""
from __future__ import annotations

import json
import re
import subprocess

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7cr8b-weekly-producer-target.yml"


def main() -> int:
    target = json.loads((ROOT / "config/tranche7cr8b-weekly-producer-target.json").read_text(encoding="utf-8"))
    preflight = json.loads((ROOT / "config/tranche7cr8b-weekly-producer-preflight.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8B" and target["source_preflight_commit"] == "cfff9e0"
    assert target["artifact_policy"] == "controlled_no_network_fixture_only" and target["lifecycle"] == "target_active"
    assert preflight["lifecycle"] == "closed_manual_validation"
    assert set(lifecycle["active_controlled_workflows"]) == {WORKFLOW}
    assert re.search(r"(?m)^  push:", workflow) and re.search(r"(?m)^  workflow_dispatch:", workflow) and not re.search(r"(?m)^  schedule:", workflow)
    assert "permissions: {contents: read}" in workflow and "--fixture" in workflow
    source = (ROOT / "research/build_m10_prospective_weekly_capture.py").read_text(encoding="utf-8")
    assert "only --fixture" in source and "create_bundle" in source and "create_operational_capture" in source
    forbidden = subprocess.run(["git", "grep", "-l", "build_m10_prospective_weekly_capture", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    print("PASS R8B target: controlled fixture proves frozen weekly capture without network, schedule, or app activation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

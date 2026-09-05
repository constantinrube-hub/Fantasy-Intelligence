#!/usr/bin/env python3
"""Lifecycle boundary for R8's one combined deterministic release gate."""
from __future__ import annotations

import argparse
import json
import re
import subprocess

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7cr8-combined-closure.yml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("target", "closure"), default="target"); args = parser.parse_args(argv)
    target = json.loads((ROOT / "config/tranche7cr8-combined-closure-target.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8" and target["source_r8a_closure"] == "7d0356a" and target["source_r8b_closure"] == "95a43fb" and target["source_r8c_target"] == "9d9e613"
    assert target["artifact_policy"] == "controlled_no_network_r8_closure" and target["release_gate"] == "one_deterministic_personal_release_build"
    assert target["research_only"] and target["production_model"] == "M9"
    assert not any(target[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "live_provider_request"))
    if args.mode == "target":
        assert target["lifecycle"] == "target_active" and set(lifecycle["active_controlled_workflows"]) == {WORKFLOW}
        assert re.search(r"(?m)^  push:", workflow)
    else:
        assert target["lifecycle"] == "closed_manual_validation" and WORKFLOW not in lifecycle["active_controlled_workflows"]
        assert not re.search(r"(?m)^  push:", workflow)
    assert re.search(r"(?m)^  workflow_dispatch:", workflow) and not re.search(r"(?m)^  schedule:", workflow)
    assert "permissions: {contents: read}" in workflow and "tools/release_build.py --mode personal" in workflow
    for path in ("config/tranche7cr8-combined-closure-target.json", "config/repository-lifecycle-contract.json", ".github/workflows/validate-fie-tranche7cr8-combined-closure.yml"):
        assert f"- '{path}'" in workflow, path
    for path in ("research/integrity_tranche7cr8_corrected_lock.py", "research/integrity_tranche7cr8b_weekly_producer.py", "research/integrity_tranche7cr8c_workflow.py", "research/integrity_m10_prospective_r8c_workflow_test.py"):
        assert (ROOT / path).is_file(), path
    forbidden = subprocess.run(["git", "grep", "-l", "tranche7cr8-combined-closure", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    print(f"PASS R8 combined {args.mode}: one no-network release gate preserves M9 and all production boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

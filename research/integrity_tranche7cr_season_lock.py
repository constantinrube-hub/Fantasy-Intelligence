#!/usr/bin/env python3
"""Static governance boundary for the first 7C-R rollout increment."""
from __future__ import annotations

import json
import re
import subprocess
import argparse
from pathlib import Path

from fie_research_pipeline_contract import ROOT

WORKFLOW = "validate-fie-tranche7cr-season-lock.yml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target", "closure"), default="target")
    args = parser.parse_args()
    target = json.loads((ROOT / "config/tranche7cr-season-lock-target.json").read_text(encoding="utf-8"))
    assert target["tranche"] == "7C-R1" and target["source_design_commit"] == "e0171ee9750e41494d44724ee5d1532e1dee2931"
    assert target["research_only"] is True and target["production_model"] == "M9"
    assert not any(target[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "scheduled_collection"))
    assert target["training_target_seasons"] == list(range(2019, 2026)) and target["forbidden_outcome_seasons"] == [2026]
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    assert set(lifecycle["active_controlled_workflows"]) == ({WORKFLOW} if args.mode == "target" else set())
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert bool(re.search(r"(?m)^  push:", workflow)) is (args.mode == "target")
    assert re.search(r"(?m)^  workflow_dispatch:", workflow)
    assert not re.search(r"(?m)^  schedule:", workflow)
    source = (ROOT / "research/m10_prospective_season_lock.py").read_text(encoding="utf-8")
    for marker in ("fie-hgb-tree-v1", "first_write", "forbidden_outcome_seasons", "M10_LINEAR", "M10_HGB"):
        assert marker in source
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_season_lock", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    if args.mode == "closure":
        assert target["lifecycle"] == "closed_manual_validation"
        assert target["validated_target"]["status"] == "DEPLOYABLE_SOURCE"
        assert len(target["release_artifact"]["sha256"]) == 64
        assert len(target["release_artifact"]["season_lock_sha256"]) == 64
    print(f"PASS Tranche 7C-R1 {args.mode}: portable offline season lock only; no scheduled write or production surface")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Controlled-boundary checks for R8A corrected-lock preflight."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from fie_research_pipeline_contract import ROOT

WORKFLOW = "validate-fie-tranche7cr8-corrected-lock-preflight.yml"


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("target", "closure"), default="target"); args = parser.parse_args()
    target = json.loads((ROOT / "config/tranche7cr8-corrected-lock-preflight.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8A" and target["lock_schema"] == "fie-m10-prospective-season-lock-v2"
    assert target["training_target_seasons"] == list(range(2019, 2026)) and target["forbidden_outcome_seasons"] == [2026]
    assert target["research_only"] and target["production_model"] == "M9"
    assert not any(target[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "scheduled_collection"))
    assert set(target["required_fixtures"]) == {"cross_season", "target_week_team_change", "negative_yardage", "null_features", "insufficient_history"}
    assert target["activation_guard"] == {"v1": "reject", "v2": "accept_when_non_fixture_and_valid"}
    active = set(lifecycle["active_controlled_workflows"])
    if args.mode == "target":
        assert active == {"validate-fie-tranche7cr8-real-season-lock.yml"}
        assert not re.search(r"(?m)^  push:", workflow) and re.search(r"(?m)^  workflow_dispatch:", workflow)
    else:
        assert target["lifecycle"] == "closed_manual_validation"
        assert WORKFLOW not in active
        assert not re.search(r"(?m)^  push:", workflow)
        assert target["validated_preflight"]["status"] == "DEPLOYABLE_SOURCE"
    assert not re.search(r"(?m)^  schedule:", workflow)
    for path in ("research/m10_prospective_features.py", "research/m10_prospective_season_lock_v2.py", "research/build_m10_prospective_historical_input_v2.py", "research/m10_prospective_activation_guard.py"):
        assert (ROOT / path).is_file(), path
    source = (ROOT / "research/m10_prospective_season_lock_v2.py").read_text(encoding="utf-8")
    for marker in ("fie-m10-prospective-season-lock-v2", "residual_samples", "row_identity_manifest", "forbidden_outcome_seasons"):
        assert marker in source
    print(f"PASS Tranche 7C-R8A {args.mode}: corrected lock remains research-only and non-operational")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Targeted regression and closure contract for Tranche 6B."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from build_fie_research_completeness_inventory import build_inventory
from fie_research_pipeline_contract import ROOT
from validate_fie_research_completeness_inventory import validate


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target", "release"), default="target")
    args = parser.parse_args(argv)
    inventory = build_inventory()
    validate(inventory)
    assert inventory["governance"]["production_behavior_changed"] is False
    assert inventory["summary"]["cell_states"].get("PRODUCTION_AUTHORIZED", 0) == 0
    assert inventory["summary"]["blockers"].get("GOVERNANCE_BLOCKED", 0) > 0
    assert inventory["summary"]["blockers"].get("INSUFFICIENT_HISTORY", 0) > 0

    target = json.loads((ROOT / "config/tranche6b-research-completeness-target.json").read_text(encoding="utf-8"))
    validated = target.get("validated_target") or {}
    commit = str(validated.get("commit") or "")
    assert target.get("tranche") == "6B" and len(commit) == 40 and str(validated.get("github_actions_run") or "").isdigit(), target
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=True)
    assert validated.get("status") == "DEPLOYABLE_SOURCE", validated
    for path, expected in (target.get("authorized_generated_synchronization") or {}).items():
        assert sha256(path) == expected, path
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    # 6B closed with no active controlled validator.  Later tranches may register
    # one temporary push-triggered target under the lifecycle policy, so preserve
    # the frozen closure state rather than rejecting all future audit work.
    closure_lifecycle = json.loads(subprocess.check_output(
        ["git", "show", "966e961:config/repository-lifecycle-contract.json"], cwd=ROOT, text=True
    ))
    assert not (closure_lifecycle.get("active_controlled_workflows") or []), closure_lifecycle
    for active in lifecycle.get("active_controlled_workflows") or []:
        path = ROOT / ".github/workflows" / str(active)
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert "  push:" in text and "  workflow_dispatch:" in text, active
    workflow = (ROOT / ".github/workflows/validate-fie-tranche6b-research-completeness.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow and "  push:" not in workflow and "  schedule:" not in workflow
    print("PASS Tranche 6B closure: inventory is deterministic, generated sync is exact, and promotion remains blocked")


if __name__ == "__main__":
    main()

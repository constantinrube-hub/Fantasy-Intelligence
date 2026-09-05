#!/usr/bin/env python3
"""Static boundary test for the Tranche 7C audit-branch adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7c-operational-prospective-collection.yml"
PREFLIGHT = ROOT / "config/tranche7c-operational-prospective-collection-preflight.json"
TARGET = ROOT / "config/tranche7c-operational-prospective-collection-target.json"
SOURCE = "f955ff4"
CLOSURE = "90ca7f8ae468f86e7e0918de41a98546fcecee53"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {"push": bool(re.search(r"(?m)^  push:", text)), "schedule": bool(re.search(r"(?m)^  schedule:", text)), "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text))}


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def git_blob_sha256(revision: str, path: str) -> str:
    return hashlib.sha256(subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target", "closure"), default="target")
    args = parser.parse_args(argv)
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert preflight["tranche"] == "7C" and preflight["source_contract_closure"] == SOURCE
    assert preflight["research_only"] is True and preflight["production_model"] == "M9"
    assert not any(preflight[key] for key in ("production_behavior_change", "app_integration", "shadow_integration", "scheduled_collection", "live_provider_request"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    if args.mode == "target":
        assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
        assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    else:
        closure_lifecycle = json.loads(subprocess.check_output(
            ["git", "show", f"{CLOSURE}:config/repository-lifecycle-contract.json"], cwd=ROOT, text=True
        ))
        assert not closure_lifecycle.get("active_controlled_workflows"), closure_lifecycle
        for active in lifecycle.get("active_controlled_workflows") or []:
            active_path = ROOT / ".github/workflows" / str(active)
            assert active_path.is_file(), active_path
            assert flags(active_path) == {"push": True, "schedule": False, "dispatch": True}, active
        assert flags(workflow) == {"push": False, "schedule": False, "dispatch": True}
        target = json.loads(TARGET.read_text(encoding="utf-8"))
        assert target.get("tranche") == "7C" and target.get("decision") == "CLOSE_AUDIT_BRANCH_OPERATIONAL_CAPTURE_ADAPTER", target
        assert target.get("source_contract_closure") == SOURCE and target.get("production_model") == "M9", target
        assert target.get("validated_target") == {
            "commit": "81bd41a72695db391febb0e32edee0b596277020",
            "github_actions_run": "33961901784",
            "status": "DEPLOYABLE_SOURCE",
        }, target
        assert target.get("release_artifact", {}).get("sha256") == "35313391341dabc4c79082aae67cc3c534faeae67b15f69afc618abc58e65a6f", target
        assert not any(target.get(key) for key in ("production_behavior_change", "app_integration", "shadow_integration", "scheduled_collection", "live_provider_request")), target
        for path, expected in (target.get("authorized_generated_synchronization") or {}).items():
            assert git_blob_sha256(CLOSURE, path) == expected, path
    adapter = (ROOT / "research/m10_prospective_operational_capture.py").read_text(encoding="utf-8")
    assert "live_provider_request" in adapter and "historical_reconstruction" in adapter and "canonical_score" in adapter
    assert "enabled-league coverage changed" in adapter and "require_fixture=False" in (ROOT / "research/validate_m10_operational_prospective_capture.py").read_text(encoding="utf-8")
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_operational", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE, "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 7C {args.mode}: audit-branch hash-locked inputs only; no schedule, app, shadow, or production change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

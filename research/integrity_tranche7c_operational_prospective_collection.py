#!/usr/bin/env python3
"""Static boundary test for the Tranche 7C audit-branch adapter."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7c-operational-prospective-collection.yml"
PREFLIGHT = ROOT / "config/tranche7c-operational-prospective-collection-preflight.json"
SOURCE = "f955ff4"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {"push": bool(re.search(r"(?m)^  push:", text)), "schedule": bool(re.search(r"(?m)^  schedule:", text)), "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target",), default="target")
    parser.parse_args(argv)
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert preflight["tranche"] == "7C" and preflight["source_contract_closure"] == SOURCE
    assert preflight["research_only"] is True and preflight["production_model"] == "M9"
    assert not any(preflight[key] for key in ("production_behavior_change", "app_integration", "shadow_integration", "scheduled_collection", "live_provider_request"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
    assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    adapter = (ROOT / "research/m10_prospective_operational_capture.py").read_text(encoding="utf-8")
    assert "live_provider_request" in adapter and "historical_reconstruction" in adapter and "canonical_score" in adapter
    assert "enabled-league coverage changed" in adapter and "require_fixture=False" in (ROOT / "research/validate_m10_operational_prospective_capture.py").read_text(encoding="utf-8")
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_operational", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE, "HEAD"], cwd=ROOT, check=True)
    print("PASS Tranche 7C target: audit-branch hash-locked inputs only; no schedule, app, shadow, or production change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

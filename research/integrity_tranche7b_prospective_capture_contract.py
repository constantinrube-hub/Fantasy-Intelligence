#!/usr/bin/env python3
"""Static target boundary for the Tranche 7B deterministic capture contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7b-prospective-capture-contract.yml"
PREFLIGHT = ROOT / "config/tranche7b-prospective-capture-contract-preflight.json"
TARGET = ROOT / "config/tranche7b-prospective-capture-contract-target.json"
DESIGN = "3314828cc0020c4528f6b9b7d8828c6bebd48bb8"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {"push": bool(re.search(r"(?m)^  push:", text)), "schedule": bool(re.search(r"(?m)^  schedule:", text)), "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text))}


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target", "closure"), default="target")
    args = parser.parse_args(argv)
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert preflight["tranche"] == "7B" and preflight["source_design_commit"] == DESIGN
    assert preflight["research_only"] is True and preflight["production_model"] == "M9"
    assert preflight["production_behavior_change"] is False and preflight["shadow_integration"] is False
    assert preflight["scheduled_collection"] is False and preflight["live_network_collection"] is False
    contract = json.loads((ROOT / "config/m10-prospective-evidence-contract.json").read_text(encoding="utf-8"))
    assert contract["design_tranche"] == "7A" and contract["models"] == ["M9", "M10_LINEAR", "M10_HGB"]
    assert contract["positions"] == ["QB", "RB", "WR", "TE"]
    assert not any(contract[key] for key in ("production_activation", "app_integration", "shadow_integration", "automatic_promotion"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    if args.mode == "target":
        assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
        assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    else:
        assert not lifecycle.get("active_controlled_workflows"), lifecycle
        assert flags(workflow) == {"push": False, "schedule": False, "dispatch": True}
        target = json.loads(TARGET.read_text(encoding="utf-8"))
        assert target.get("tranche") == "7B" and target.get("decision") == "CLOSE_DETERMINISTIC_CAPTURE_CONTRACT", target
        assert target.get("validated_target") == {"commit": "0b120fd652a142372a221240381acfa47c40a238", "github_actions_run": "33960545413", "status": "DEPLOYABLE_SOURCE"}, target
        assert target.get("release_artifact", {}).get("sha256") == "eb2c764ed9f11244ae14b08d67b904fbbd2f20f6258aa3975d0e1be06c211af4", target
        assert target.get("production_model") == "M9"
        assert not any(target.get(key) for key in ("production_behavior_change", "app_integration", "shadow_integration", "scheduled_collection", "live_network_collection")), target
        for path, expected in (target.get("authorized_generated_synchronization") or {}).items():
            assert sha256(path) == expected, path
    builder = (ROOT / "research/build_m10_prospective_capture.py").read_text(encoding="utf-8")
    assert "if not args.fixture:" in builder and "Tranche 7C" in builder
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_capture", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", DESIGN, "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 7B {args.mode}: no-network deterministic capture only; M9 and production surfaces preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

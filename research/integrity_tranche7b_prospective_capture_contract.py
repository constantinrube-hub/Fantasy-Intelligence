#!/usr/bin/env python3
"""Static target boundary for the Tranche 7B deterministic capture contract."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7b-prospective-capture-contract.yml"
PREFLIGHT = ROOT / "config/tranche7b-prospective-capture-contract-preflight.json"
DESIGN = "3314828cc0020c4528f6b9b7d8828c6bebd48bb8"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {"push": bool(re.search(r"(?m)^  push:", text)), "schedule": bool(re.search(r"(?m)^  schedule:", text)), "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target",), default="target")
    parser.parse_args(argv)
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
    assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
    assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    builder = (ROOT / "research/build_m10_prospective_capture.py").read_text(encoding="utf-8")
    assert "if not args.fixture:" in builder and "Tranche 7C" in builder
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_capture", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", DESIGN, "HEAD"], cwd=ROOT, check=True)
    print("PASS Tranche 7B target: no-network deterministic capture only; M9 and production surfaces preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded Tranche 6C integrity contract.

This preflight accepts only prospective evidence hardening.  It deliberately
does not authorize forecast reconstruction, a model change, or a promotion.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from build_fie_point_in_time_evidence_report import build_report
from fie_research_pipeline_contract import ROOT
from validate_fie_point_in_time_evidence_report import validate


WORKFLOW = "validate-fie-tranche6c-point-in-time-evidence.yml"


def workflow_flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "closure"), default="preflight")
    args = parser.parse_args(argv)
    report = build_report()
    validate(report)
    assert report["governance"]["production_behavior_changed"] is False
    assert report["governance"]["historical_forecast_backfill"] is False
    assert report["governance"]["current_endpoint_reconstruction"] is False
    assert report["summary"]["completed_historical_seasons"] == []

    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    assert workflow.is_file(), workflow
    if args.mode == "preflight":
        assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
        assert workflow_flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    else:
        assert not (lifecycle.get("active_controlled_workflows") or []), lifecycle
        assert workflow_flags(workflow) == {"push": False, "schedule": False, "dispatch": True}
    subprocess.run(["git", "merge-base", "--is-ancestor", "d365e22e44af4c4d621083900c4b7d20c43636fc", "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 6C {args.mode}: prospective evidence only; no historical reconstruction or production change")


if __name__ == "__main__":
    main()

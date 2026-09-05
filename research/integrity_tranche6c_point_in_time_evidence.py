#!/usr/bin/env python3
"""Bounded Tranche 6C integrity contract.

This preflight accepts only prospective evidence hardening.  It deliberately
does not authorize forecast reconstruction, a model change, or a promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from build_fie_point_in_time_evidence_report import build_report
from fie_research_pipeline_contract import ROOT
from validate_fie_point_in_time_evidence_report import validate


WORKFLOW = "validate-fie-tranche6c-point-in-time-evidence.yml"
TARGET = ROOT / "config/tranche6c-point-in-time-evidence-target.json"


def workflow_flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


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
        target = json.loads(TARGET.read_text(encoding="utf-8"))
        validated = target.get("validated_target") or {}
        assert target.get("tranche") == "6C", target
        assert validated == {
            "commit": "7b80acc95603f81794c7ef1ffd8d2caaf9f6e3a4",
            "github_actions_run": "33932408549",
            "status": "DEPLOYABLE_SOURCE",
        }, validated
        assert target.get("release_artifact", {}).get("sha256") == "b0914c05338f0201bbc72c754f3b968efb9b163dce9fc611a52aac7d48083a44", target
        for path, expected in (target.get("authorized_generated_synchronization") or {}).items():
            assert sha256(path) == expected, path
    subprocess.run(["git", "merge-base", "--is-ancestor", "d365e22e44af4c4d621083900c4b7d20c43636fc", "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 6C {args.mode}: prospective evidence only; no historical reconstruction or production change")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Static production-isolation and lifecycle contract for Tranche 6E."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = "validate-fie-tranche6e-cross-model-decision-review.yml"
TARGET = ROOT / "config/tranche6e-cross-model-decision-review-target.json"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("target", "closure"), default="target")
    args = parser.parse_args(argv)
    contract = json.loads((ROOT / "config/m10-cross-model-review.json").read_text(encoding="utf-8"))
    assert contract["review_model"] == "GPT-5.6 Sol High"
    assert contract["champion"] == "M9"
    assert contract["automatic_promotion"] is False
    assert contract["production_activation"] is False
    assert contract["shadow_default"] is False
    assert contract["source_commit"] == "24a0d5ac9f1c37bdfb92f11ea7f77205f80df4e2"
    assert contract["source_artifact_sha256"] == "f13d6b8770be7bfd94181ca33edfd0f884d2611aa0a59b453b4ce9cf02bc1d9b"
    assert contract["source_m10_json_sha256"] == "c491de5af28f5d1586ea3393560a0c292c0e2ba4de57b6b1825e6dce66a81b60"

    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    assert workflow.is_file(), workflow
    if args.mode == "target":
        assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}, lifecycle
        assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    else:
        assert not lifecycle.get("active_controlled_workflows"), lifecycle
        assert flags(workflow) == {"push": False, "schedule": False, "dispatch": True}
        target = json.loads(TARGET.read_text(encoding="utf-8"))
        assert target.get("tranche") == "6E" and target.get("decision") == "RETAIN_M9_NO_6F_SHADOW_APPROVAL", target
        assert target.get("validated_target") == {
            "commit": "b248c7387f5ae3c9aa7b7c64ee0076f85cc96924",
            "github_actions_run": "33951332941",
            "status": "DEPLOYABLE_SOURCE",
        }, target
        assert target.get("production_behavior_change") is False and target.get("production_model") == "M9", target
        assert target.get("release_artifact", {}).get("sha256") == "ce9f3c819fc7144768c0b6a2b4930f1ef06d899170e2a2495ab3fa837a819b56", target
        assert target.get("review_artifact", {}).get("sha256") == "d6b15e2cfb378cf5e5c02e567761d249f731cbee675ff7908b64eff78278c848", target
        for path, expected in (target.get("authorized_generated_synchronization") or {}).items():
            assert sha256(path) == expected, path

    forbidden = subprocess.run(
        ["git", "grep", "-l", "m10-cross-model-decision-review", "--", "app", "functions", "dist/app"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", "b248c73", "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 6E {args.mode}: retain M9; no promotion, shadow, app, or production activation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

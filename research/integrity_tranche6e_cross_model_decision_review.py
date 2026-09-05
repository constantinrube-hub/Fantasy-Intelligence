#!/usr/bin/env python3
"""Static production-isolation and lifecycle contract for Tranche 6E."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = "validate-fie-tranche6e-cross-model-decision-review.yml"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


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

    forbidden = subprocess.run(
        ["git", "grep", "-l", "m10-cross-model-decision-review", "--", "app", "functions", "dist/app"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout.strip()
    assert not forbidden, forbidden
    subprocess.run(["git", "merge-base", "--is-ancestor", "6e6e433", "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 6E {args.mode}: retain M9; no promotion, shadow, app, or production activation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

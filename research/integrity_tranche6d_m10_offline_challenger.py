#!/usr/bin/env python3
"""Static boundary contract for Tranche 6D implementation and closure."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche6d-m10-offline-challenger.yml"


def flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {"push": bool(re.search(r"(?m)^  push:", text)), "schedule": bool(re.search(r"(?m)^  schedule:", text)), "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text))}


def main(argv=None) -> None:
    p = argparse.ArgumentParser(); p.add_argument("--mode", choices=("target", "closure"), default="target"); a = p.parse_args(argv)
    contract = json.loads((ROOT / "config/m10-offline-experiment.json").read_text(encoding="utf-8"))
    assert contract["research_only"] is True and contract["production_model"] == "M9"
    assert contract["production_activation"] is False and contract["app_integration"] is False
    assert contract["ensemble_policy"] == "PROHIBITED_IN_TRANCHE_6D"
    assert contract["hgb_loss_policy"] == {
        "count_targets": "poisson_when_outer_training_target_sum_is_positive",
        "zero_sum_count_target_fallback": "squared_error",
        "continuous_targets": "squared_error",
    }
    assert contract["positions"] == ["QB", "RB", "WR", "TE"]
    assert [f["test_season"] for f in contract["outer_folds"]] == [2022, 2023, 2024, 2025]
    assert all(2026 not in f["train_seasons"] and f["test_season"] != 2026 for f in contract["outer_folds"])
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = ROOT / ".github/workflows" / WORKFLOW
    if a.mode == "target":
        assert set(lifecycle.get("active_controlled_workflows") or []) == {WORKFLOW}
        assert flags(workflow) == {"push": True, "schedule": False, "dispatch": True}
    else:
        assert not lifecycle.get("active_controlled_workflows")
        assert flags(workflow) == {"push": False, "schedule": False, "dispatch": True}
    forbidden = subprocess.run(
        ["git", "grep", "-l", "m10-offline-challenger", "--", "app", "functions", "dist/app"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    ).stdout.strip()
    assert not forbidden, forbidden
    builder = (ROOT / "research/build_m10_offline_challenger.py").read_text(encoding="utf-8")
    assert 'float(observed.sum()) > 0 else "squared_error"' in builder
    assert "panel = panel.merge(m9" not in builder
    assert 'test = z[z.season.eq(fold["test_season"])].copy().merge(' in builder
    subprocess.run(["git", "merge-base", "--is-ancestor", "dcc41be", "HEAD"], cwd=ROOT, check=True)
    print(f"PASS Tranche 6D {a.mode}: offline research only; M9 champion and production surfaces unchanged")


if __name__ == "__main__": main()

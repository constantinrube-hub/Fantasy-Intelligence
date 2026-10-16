#!/usr/bin/env python3
"""Fail-closed validator for a Tranche 6D M10 offline artifact."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from fie_research_pipeline_contract import ROOT


POSITIONS = {"QB", "RB", "WR", "TE"}
CANDIDATES = {"M9", "M10_LINEAR", "M10_HGB"}


def finite(value) -> bool:
    try: return math.isfinite(float(value))
    except Exception: return False


def validate(obj: dict, *, require_fixture: bool = False) -> None:
    assert obj.get("schema") == "fie-m10-offline-challenger-v1"
    assert obj.get("fixture") is require_fixture if require_fixture else isinstance(obj.get("fixture"), bool)
    assert obj.get("governance") == {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "ensemble": False}
    assert obj.get("promotion_status") == "NOT_REVIEWED_TRANCHE_6E_REQUIRED"
    assert obj.get("distribution_method") == "training-window empirical position residual envelope; diagnostic only"
    assert (obj.get("source_lineage") or {}).get("seasons") == [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    assert obj.get("status") == "RESEARCH_ONLY_EVALUATED"
    assert obj.get("component_graph") == ["team_opportunity", "player_participation_role", "per_opportunity_efficiency", "event_conversion", "joint_reconciliation", "exact_league_scoring"]
    assert {row.get("name") for row in obj.get("candidate_ladder", [])} == CANDIDATES
    expected = {2022: [2019, 2020, 2021], 2023: [2019, 2020, 2021, 2022], 2024: [2019, 2020, 2021, 2022, 2023], 2025: [2019, 2020, 2021, 2022, 2023, 2024]}
    folds = obj.get("fold_results") or []
    assert {(row["position"], row["test_season"]) for row in folds} == {(p, y) for p in POSITIONS for y in expected}
    for row in folds:
        assert row["position"] in POSITIONS and row["train_seasons"] == expected[row["test_season"]]
        assert row["paired_rows"] >= 10 and row["feature_count"] >= 2 and row["raw_targets"]
        assert set(row["metrics"]) == CANDIDATES
        for metric in row["metrics"].values():
            assert metric["n"] == row["paired_rows"]
            assert all(finite(metric[key]) for key in ("mae", "bias", "p10_p90_coverage", "p10_p90_width"))
            assert set(metric["pinball"]) == {"0.1", "0.25", "0.5", "0.75", "0.9"}
            assert all(finite(value) for value in metric["pinball"].values())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--path", default="artifacts/tranche6d/m10-offline-challenger.json"); p.add_argument("--require-fixture", action="store_true"); a = p.parse_args(argv)
    path = Path(a.path); path = path if path.is_absolute() else ROOT / path
    obj = json.loads(path.read_text(encoding="utf-8")); validate(obj, require_fixture=a.require_fixture)
    print(f"PASS M10 offline challenger folds={len(obj['fold_results'])} production=M9 activation=false")
    return 0


if __name__ == "__main__": raise SystemExit(main())

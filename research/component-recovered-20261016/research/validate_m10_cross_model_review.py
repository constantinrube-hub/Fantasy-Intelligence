#!/usr/bin/env python3
"""Fail-closed validator for the Tranche 6E cross-model decision review."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSITIONS = {"QB", "RB", "WR", "TE"}


def finite(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def validate(review: dict) -> None:
    assert review.get("schema") == "fie-m10-cross-model-decision-review-v1"
    assert review.get("review_model") == "GPT-5.6 Sol High"
    assert review.get("source_evidence") == {
        "commit": "24a0d5ac9f1c37bdfb92f11ea7f77205f80df4e2",
        "fixture": True,
        "folds": 16,
        "github_actions_run": "33935011577",
        "m10_json_sha256": "c491de5af28f5d1586ea3393560a0c292c0e2ba4de57b6b1825e6dce66a81b60",
        "release_artifact_sha256": "f13d6b8770be7bfd94181ca33edfd0f884d2611aa0a59b453b4ce9cf02bc1d9b",
        "tranche": "6D",
    }
    assert review.get("governance") == {
        "app_integration": False,
        "automatic_promotion": False,
        "production_activation": False,
        "production_model": "M9",
        "shadow_integration": False,
    }
    rows = review.get("positions") or []
    assert {row.get("position") for row in rows} == POSITIONS
    for row in rows:
        assert row.get("promotion_decision") == "RESEARCH_ONLY_BLOCKED_PROMOTION"
        assert row.get("shadow_approved") is False
        assert row.get("calibration_review", {}).get("status") == "DIAGNOSTIC_ONLY"
        assert row.get("disagreement_review", {}).get("status") == "NOT_EVALUABLE"
        assert row.get("subgroup_review", {}).get("status") == "INCOMPLETE"
        assert row.get("decision_utility_review", {}).get("status") == "ABSENT"
        assert row.get("exact_scoring_replay", {}).get("status") == "INCOMPLETE_DEFAULT_FIXTURE_ONLY"
        assert len(row.get("champion", {}).get("outer_seasons") or []) == 4
        challengers = row.get("challengers") or []
        assert {candidate.get("candidate") for candidate in challengers} == {"M10_LINEAR", "M10_HGB"}
        for candidate in challengers:
            assert candidate.get("promotion_review_ready") is False and candidate.get("shadow_approved") is False
            assert candidate.get("point_improvement_gate") in {"PASS", "FAIL"}
            assert all(finite(candidate.get(key)) for key in ("mae", "bias", "spearman", "p10_p90_coverage", "p10_p90_width", "mean_relative_mae_lift"))
            assert all(finite(value) for value in (candidate.get("outer_season_bootstrap_ci95") or {}).values())
    qb = next(row for row in rows if row["position"] == "QB")
    assert qb.get("promising_candidates") == ["M10_HGB"]
    qb_hgb = next(row for row in qb["challengers"] if row["candidate"] == "M10_HGB")
    assert qb_hgb["mae_fold_wins_vs_m9"] == 4 and qb_hgb["mean_relative_mae_lift"] > 0.04
    assert qb_hgb["outer_season_bootstrap_ci95"]["low"] > 0
    assert all(not row.get("promising_candidates") for row in rows if row["position"] != "QB")
    conclusion = review.get("cross_model_conclusion") or {}
    assert conclusion.get("decision") == "RETAIN_M9_NO_6F_SHADOW_APPROVAL"
    assert conclusion.get("promotion_status") == "BLOCKED"
    assert conclusion.get("promising_research_lead") == {"position": "QB", "candidate": "M10_HGB"}
    assert set(conclusion.get("blocking_reasons") or []) == {"MISSING_SOURCE", "INSUFFICIENT_HISTORY", "CALIBRATION_FAILURE", "DECISION_UTILITY_FAILURE", "GOVERNANCE_BLOCKED"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="artifacts/tranche6e/m10-cross-model-decision-review.json")
    args = parser.parse_args(argv)
    path = Path(args.path)
    path = path if path.is_absolute() else ROOT / path
    review = json.loads(path.read_text(encoding="utf-8"))
    validate(review)
    print("PASS Tranche 6E review: retain M9; QB M10-HGB is research lead only; no 6F shadow approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

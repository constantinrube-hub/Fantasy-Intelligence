#!/usr/bin/env python3
"""Build the Sol-governed Tranche 6E cross-model and decision review.

The review is deliberately fail-closed.  It can preserve a promising point-model
signal, but it cannot infer row-level disagreement, subgroup calibration, scoring
profile replay, or decision utility from aggregate fold metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/m10-cross-model-review.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weighted(rows: list[dict[str, Any]], candidate: str, key: str) -> float:
    total = sum(int(row["metrics"][candidate]["n"]) for row in rows)
    return sum(float(row["metrics"][candidate][key]) * int(row["metrics"][candidate]["n"]) for row in rows) / total


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    location = (len(ordered) - 1) * q
    lower = int(location)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (location - lower)


def exhaustive_block_ci(values: list[float]) -> tuple[float, float]:
    assert len(values) == 4
    means = [sum(values[index] for index in draw) / 4 for draw in itertools.product(range(4), repeat=4)]
    return quantile(means, 0.025), quantile(means, 0.975)


def candidate_summary(rows: list[dict[str, Any]], candidate: str, contract: dict[str, Any]) -> dict[str, Any]:
    lifts = [
        (float(row["metrics"]["M9"]["mae"]) - float(row["metrics"][candidate]["mae"]))
        / float(row["metrics"]["M9"]["mae"])
        for row in rows
    ]
    ci_low, ci_high = exhaustive_block_ci(lifts)
    mean_lift = sum(lifts) / len(lifts)
    point_gate = mean_lift >= float(contract["minimum_mean_relative_mae_lift"]) and ci_low > 0
    pinball = {
        q: sum(
            float(row["metrics"][candidate]["pinball"][q]) * int(row["metrics"][candidate]["n"])
            for row in rows
        ) / sum(int(row["metrics"][candidate]["n"]) for row in rows)
        for q in ("0.1", "0.25", "0.5", "0.75", "0.9")
    }
    return {
        "candidate": candidate,
        "outer_seasons": [int(row["test_season"]) for row in rows],
        "paired_rows": sum(int(row["metrics"][candidate]["n"]) for row in rows),
        "mae": weighted(rows, candidate, "mae"),
        "bias": weighted(rows, candidate, "bias"),
        "spearman": weighted(rows, candidate, "spearman"),
        "p10_p90_coverage": weighted(rows, candidate, "p10_p90_coverage"),
        "p10_p90_width": weighted(rows, candidate, "p10_p90_width"),
        "pinball": pinball,
        "mae_fold_wins_vs_m9": sum(value > 0 for value in lifts),
        "relative_mae_lift_by_season": [
            {"test_season": int(row["test_season"]), "lift": value}
            for row, value in zip(rows, lifts)
        ],
        "mean_relative_mae_lift": mean_lift,
        "outer_season_bootstrap_ci95": {"low": ci_low, "high": ci_high},
        "point_improvement_gate": "PASS" if point_gate else "FAIL",
        "promotion_review_ready": False,
        "shadow_approved": False,
    }


def build(source: Path) -> dict[str, Any]:
    contract = load(CONTRACT)
    evidence = load(source)
    assert evidence.get("schema") == "fie-m10-offline-challenger-v1"
    assert evidence.get("fixture") is True
    assert evidence.get("governance", {}).get("production_model") == "M9"
    assert evidence.get("promotion_status") == "NOT_REVIEWED_TRANCHE_6E_REQUIRED"
    assert sha256(source) == contract["source_m10_json_sha256"]
    folds = evidence.get("fold_results") or []
    expected = {(position, season) for position in contract["positions"] for season in (2022, 2023, 2024, 2025)}
    assert {(row["position"], int(row["test_season"])) for row in folds} == expected

    positions = []
    for position in contract["positions"]:
        rows = sorted((row for row in folds if row["position"] == position), key=lambda row: int(row["test_season"]))
        champion = candidate_summary(rows, "M9", {**contract, "minimum_mean_relative_mae_lift": 0.0})
        champion["point_improvement_gate"] = "CHAMPION_COMPARATOR"
        reviews = [candidate_summary(rows, candidate, contract) for candidate in contract["candidates"]]
        promising = [row["candidate"] for row in reviews if row["point_improvement_gate"] == "PASS"]
        positions.append({
            "position": position,
            "champion": champion,
            "challengers": reviews,
            "point_signal": "PROMISING_RESEARCH_LEAD" if promising else "NO_STABLE_POINT_LIFT",
            "promising_candidates": promising,
            "calibration_review": {
                "status": "DIAGNOSTIC_ONLY",
                "reason": "empirical residual envelopes report pinball and interval coverage but lack row-level conditional and material-subgroup calibration evidence",
            },
            "disagreement_review": {
                "status": "NOT_EVALUABLE",
                "reason": "row-level paired predictions were not retained in the validated 6D artifact",
            },
            "subgroup_review": {
                "evaluated": ["position", "outer_season"],
                "missing": ["week_range", "team_change", "rookie_young_player", "participation_band", "scoring_format", "league_capability"],
                "status": "INCOMPLETE",
            },
            "decision_utility_review": {
                "status": "ABSENT",
                "reason": "no legal-lineup, start-sit, draft, trade, or waiver decision traces are present",
            },
            "exact_scoring_replay": {
                "status": "INCOMPLETE_DEFAULT_FIXTURE_ONLY",
                "scoring_signature": evidence.get("scoring_signature"),
            },
            "promotion_decision": "RESEARCH_ONLY_BLOCKED_PROMOTION",
            "shadow_approved": False,
        })

    return {
        "schema": "fie-m10-cross-model-decision-review-v1",
        "review_model": contract["review_model"],
        "source_evidence": {
            "tranche": "6D",
            "commit": contract["source_commit"],
            "github_actions_run": contract["source_run"],
            "release_artifact_sha256": contract["source_artifact_sha256"],
            "m10_json_sha256": sha256(source),
            "fixture": True,
            "folds": len(folds),
        },
        "governance": {
            "production_model": "M9",
            "production_activation": False,
            "automatic_promotion": False,
            "app_integration": False,
            "shadow_integration": False,
        },
        "positions": positions,
        "cross_model_conclusion": {
            "decision": "RETAIN_M9_NO_6F_SHADOW_APPROVAL",
            "promotion_status": "BLOCKED",
            "promising_research_lead": {"position": "QB", "candidate": "M10_HGB"},
            "blocking_reasons": [
                "MISSING_SOURCE",
                "INSUFFICIENT_HISTORY",
                "CALIBRATION_FAILURE",
                "DECISION_UTILITY_FAILURE",
                "GOVERNANCE_BLOCKED",
            ],
            "required_next_evidence": [
                "real point-in-time paired row-level predictions",
                "row-level model-disagreement analysis",
                "material subgroup and probability-band calibration",
                "all-applicable scoring-profile replay",
                "downstream decision-utility traces",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/tranche6e/m10-offline-challenger.json")
    parser.add_argument("--output", default="artifacts/tranche6e/m10-cross-model-decision-review.json")
    args = parser.parse_args(argv)
    source = Path(args.input)
    source = source if source.is_absolute() else ROOT / source
    output = Path(args.output)
    output = output if output.is_absolute() else ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(source), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS wrote {output}: retain M9; no 6F shadow approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

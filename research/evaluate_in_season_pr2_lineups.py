#!/usr/bin/env python3
"""Point-in-time outcome replay for immutable In-Season PR2 lineup captures.

This evaluator has no provider access.  A separate outcome producer must first
publish league-scored realized points keyed by the exact captured player
identity.  Consequently a later current snapshot cannot alter hindsight,
coverage, or prospective-method evidence.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from point_in_time_capture import first_write_json
    from weekly_lineup_decision_support import LineupEvidenceError, canonical_player_id, exact_lineup, numeric
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.point_in_time_capture import first_write_json
    from research.weekly_lineup_decision_support import LineupEvidenceError, canonical_player_id, exact_lineup, numeric


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-in-season-pr2-lineup-evaluation-v1"
OUTCOME_SCHEMA = "fie-in-season-pr2-lineup-outcome-v1"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def blocker(report: dict[str, Any], code: str, detail: Any = None) -> dict[str, Any]:
    return {
        "league_id": report.get("league_id"),
        "league_name": report.get("league_name"),
        "format": report.get("format"),
        "status": code,
        "detail": detail,
    }


def evaluate_league(report: dict[str, Any], outcome: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    if report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
        return blocker(report, "NOT_APPLICABLE_AUTOMATIC_LINEUP")
    source = report.get("evaluation_input")
    if not isinstance(source, dict) or source.get("schema") != "fie-in-season-pr2-lineup-evaluation-input-v1":
        return blocker(report, "BLOCKED_CAPTURE_EVALUATION_INPUT_MISSING")
    league_id = str(report.get("league_id"))
    by_league = outcome.get("league_player_realized_points") if isinstance(outcome.get("league_player_realized_points"), dict) else {}
    values = by_league.get(league_id)
    if not isinstance(values, dict):
        return blocker(report, "BLOCKED_LEAGUE_OUTCOME_MISSING")
    candidates = []
    missing = []
    for candidate in source.get("active_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        player_id = str(candidate.get("captured_player_id") or canonical_player_id(candidate) or "")
        value = numeric(values.get(player_id))
        if not player_id or value is None:
            missing.append(player_id or "UNKNOWN")
            continue
        candidates.append({**candidate, "realized_points": value})
    if missing:
        return blocker(report, "BLOCKED_REALIZED_PLAYER_OUTCOME_MISSING", sorted(missing))
    try:
        hindsight = exact_lineup(candidates, source.get("roster_positions") or [], value_key="realized_points", root=root)
    except LineupEvidenceError as exc:
        return blocker(report, str(exc))
    if not hindsight.get("complete_assignment"):
        return blocker(report, "BLOCKED_HINDSIGHT_LEGAL_ASSIGNMENT_INCOMPLETE", hindsight.get("unfilled_slots"))
    realized = {str(key): float(value) for key, value in values.items() if numeric(value) is not None}
    recommended = [str(x) for x in source.get("recommended_player_ids") or []]
    submitted = [str(x) for x in source.get("submitted_player_ids") or []]
    required = sorted(set(recommended) | set(submitted))
    absent = [player_id for player_id in required if player_id not in realized]
    if absent:
        return blocker(report, "BLOCKED_RECOMMENDED_OR_SUBMITTED_OUTCOME_MISSING", absent)
    recommended_total = round(sum(realized[player_id] for player_id in recommended), 6)
    submitted_total = round(sum(realized[player_id] for player_id in submitted), 6)
    hindsight_total = float(hindsight["total"])
    hindsight_ids = set(hindsight.get("selected_player_ids") or [])
    hit_count = len(set(recommended) & hindsight_ids)
    return {
        "league_id": league_id,
        "league_name": report.get("league_name"),
        "format": report.get("format"),
        "status": "READY",
        "capture_evidence": {
            "capture_roster_state_sha256": (report.get("evidence") or {}).get("roster_state_sha256"),
            "scoring_signature": (report.get("evidence") or {}).get("scoring_signature"),
            "runtime_contract_sha256": source.get("runtime_contract_sha256"),
        },
        "recommended_realized_points": recommended_total,
        "submitted_realized_points": submitted_total,
        "hindsight_best_legal_points": hindsight_total,
        "lineup_regret": round(hindsight_total - recommended_total, 6),
        "points_lost_vs_hindsight_best_legal_lineup": round(hindsight_total - submitted_total, 6),
        "submitted_vs_recommended_realized_points": round(submitted_total - recommended_total, 6),
        "best_legal_player_hit_rate": round(hit_count / len(hindsight_ids), 6) if hindsight_ids else None,
        "recommended_player_count": len(recommended),
        "hindsight_player_count": len(hindsight_ids),
        "hindsight_assignment": hindsight.get("assignment"),
    }


def evaluate_capture(capture: dict[str, Any], outcome: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    if not capture.get("capture_id") or not capture.get("capture_content_sha256"):
        raise ValueError("capture must be an immutable content-bound PR2 lineup capture")
    if outcome.get("schema") != OUTCOME_SCHEMA:
        raise ValueError("outcome schema invalid")
    if outcome.get("capture_id") != capture.get("capture_id") or outcome.get("capture_content_sha256") != capture.get("capture_content_sha256"):
        raise ValueError("outcome is not bound to this immutable capture")
    reports = [evaluate_league(report, outcome, root=root) for report in capture.get("leagues") or [] if isinstance(report, dict)]
    ready = [row for row in reports if row.get("status") == "READY"]
    status_counts = Counter(str(row.get("status")) for row in reports)
    return {
        "schema": SCHEMA,
        "capture_id": capture["capture_id"],
        "capture_content_sha256": capture["capture_content_sha256"],
        "outcome_revision_id": outcome.get("outcome_revision_id"),
        "season": outcome.get("season"),
        "week": outcome.get("week"),
        "league_count": len(reports),
        "ready_league_count": len(ready),
        "status_counts": dict(sorted(status_counts.items())),
        "aggregate": {
            "recommended_realized_points": round(sum(float(row["recommended_realized_points"]) for row in ready), 6),
            "submitted_realized_points": round(sum(float(row["submitted_realized_points"]) for row in ready), 6),
            "hindsight_best_legal_points": round(sum(float(row["hindsight_best_legal_points"]) for row in ready), 6),
            "lineup_regret": round(sum(float(row["lineup_regret"]) for row in ready), 6),
            "points_lost_vs_hindsight_best_legal_lineup": round(sum(float(row["points_lost_vs_hindsight_best_legal_lineup"]) for row in ready), 6),
        },
        "leagues": reports,
        "governance": {"research_only": True, "production_model": "M9", "opponent_aware_promotion": False, "minimum_rows_for_review": 300, "minimum_temporal_periods_for_review": 8},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate one immutable PR2 lineup capture against an explicit outcome envelope")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = evaluate_capture(read_json(Path(args.capture)), read_json(Path(args.outcome)))
    path = Path(args.output)
    if not path.is_absolute():
        path = ROOT / path
    first_write_json(path, result)
    print(json.dumps({"output": str(path), "status_counts": result["status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""No-network point-in-time replay tests for In-Season PR2 lineups."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import evaluate_in_season_pr2_lineups as e
import build_in_season_pr2_lineup_outcome as b
import in_season_pr2_weekly_lineups as p
from integrity_in_season_pr2_weekly_lineups_test import fixture, setup, write


def test_exact_hindsight_is_bound_to_the_immutable_capture():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "1")
        current_path = root / "data/research/leagues/1/current/milestone5_current.json"
        current = json.loads(current_path.read_text(encoding="utf-8"))
        for row in current["players"]:
            if row["canonical_player_id"] in {"a", "b", "c"}:
                row["sleeper_weekly_projection"] = {"a": 21, "b": 17, "c": 15}[row["canonical_player_id"]]
                row["model_id"] = "fixture-m4"
                row["model_version"] = "v1"
        current["forecast_artifacts"] = {label: {"status": "BOUND", "artifact": label, "sha256": "a" * 64}
                                         for label in ("M4", "M5", "M6")}
        current["sleeper_baseline_receipt"] = {"status": "ARCHIVED_PROJECTION_STATS_MATCH", "archive_sha256": "b" * 64}
        write(current_path, current)
        write(root / "data/research/leagues/registry.json", {"leagues": {"1": {"enabled": True, "league_name": "Alpha", "format": "REDRAFT", "priority": "HIGH"}}})
        portfolio = p.build_portfolio(root, season=2026, week=4, as_of=datetime(2026, 9, 30, tzinfo=timezone.utc))
        paths = p.write_canonical_pregame_capture(root, portfolio)
        capture = json.loads(paths["capture"].read_text(encoding="utf-8"))
        candidates = capture["leagues"][0]["evaluation_input"]["active_candidates"]
        assert capture["leagues"][0]["evaluation_input"]["fie_forecast_artifacts"] == current["forecast_artifacts"]
        assert capture["leagues"][0]["evaluation_input"]["sleeper_baseline_receipt"] == current["sleeper_baseline_receipt"]
        assert next(row for row in candidates if row["captured_player_id"] == "canonical:a")["projection_evidence"] == {
            "fie_mean": 20.0, "sleeper_mean": 21.0, "decision_mean": 20.0,
            "decision_source_class": "FIE_GOVERNED", "fie_weekly_activation_eligible": True,
            "model_id": "fixture-m4", "model_version": "v1", "projection_source": None,
        }
        outcome = {
            "schema": e.OUTCOME_SCHEMA,
            "capture_id": capture["capture_id"],
            "capture_content_sha256": capture["capture_content_sha256"],
            "outcome_revision_id": "official-final-v1",
            "season": 2026,
            "week": 4,
            "league_player_realized_points": {"1": {"canonical:a": 5, "canonical:b": 20, "canonical:c": 3, "canonical:q": 1}},
        }
        result = e.evaluate_capture(capture, outcome, root=root)
        league = result["leagues"][0]
        assert league["status"] == "READY"
        assert league["recommended_realized_points"] == 25
        assert league["submitted_realized_points"] == 8
        assert league["hindsight_best_legal_points"] == 25
        assert league["points_lost_vs_hindsight_best_legal_lineup"] == 17
        assert league["projection_coverage"] == {"candidate_rows": 4, "fie_mean_rows": 3, "sleeper_mean_rows": 3,
                                                 "paired_mean_rows": 3, "governed_fie_mean_rows": 3}
        assert result["projection_coverage"] == league["projection_coverage"]
        assert result["paired_mean_rows_by_position"] == {"RB": 2, "WR": 1}
        assert {row["captured_player_id"]: (row["fie_mean"], row["sleeper_mean"], row["realized_points"])
                for row in league["paired_projection_rows"]} == {
                    "canonical:a": (20.0, 21.0, 5.0), "canonical:b": (19.0, 17.0, 20.0),
                    "canonical:c": (18.0, 15.0, 3.0),
                }
        changed = json.loads(json.dumps(capture))
        changed["leagues"][0]["evaluation_input"]["active_candidates"][0]["projection_evidence"]["fie_mean"] = 999
        try:
            e.evaluate_capture(changed, outcome, root=root)
            raise AssertionError("altered capture values accepted under the original hash")
        except e.LineupEvidenceError as exc:
            assert "CAPTURE_CONTENT_MISMATCH" in str(exc)
        changed = json.loads(json.dumps(capture))
        changed["leagues"][0]["evaluation_input"]["sleeper_baseline_receipt"]["archive_sha256"] = "c" * 64
        try:
            e.evaluate_capture(changed, outcome, root=root)
            raise AssertionError("altered Sleeper receipt accepted under the original capture hash")
        except e.LineupEvidenceError as exc:
            assert "CAPTURE_CONTENT_MISMATCH" in str(exc)
        try:
            b.build_outcome(changed, {"schema": b.RAW_SCHEMA}, outcome_revision_id="tampered")
            raise AssertionError("outcome builder accepted an altered capture")
        except e.LineupEvidenceError as exc:
            assert "CAPTURE_CONTENT_MISMATCH" in str(exc)
        assert result["governance"]["opponent_aware_promotion"] is False


def test_outcome_capture_hash_mismatch_fails_closed():
    capture = {"capture_id": "a", "capture_content_sha256": "b", "leagues": []}
    outcome = {"schema": e.OUTCOME_SCHEMA, "capture_id": "a", "capture_content_sha256": "wrong", "league_player_realized_points": {}}
    try:
        e.evaluate_capture(capture, outcome)
    except ValueError as exc:
        assert "not bound" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("mismatched outcome was accepted")


def main() -> None:
    tests = [test_exact_hindsight_is_bound_to_the_immutable_capture, test_outcome_capture_hash_mismatch_fails_closed]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 lineup evaluation ({len(tests)} tests)")


if __name__ == "__main__":
    main()

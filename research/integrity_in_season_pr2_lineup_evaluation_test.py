#!/usr/bin/env python3
"""No-network point-in-time replay tests for In-Season PR2 lineups."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import evaluate_in_season_pr2_lineups as e
import in_season_pr2_weekly_lineups as p
from integrity_in_season_pr2_weekly_lineups_test import fixture, setup, write


def test_exact_hindsight_is_bound_to_the_immutable_capture():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "1")
        write(root / "data/research/leagues/registry.json", {"leagues": {"1": {"enabled": True, "league_name": "Alpha", "format": "REDRAFT", "priority": "HIGH"}}})
        portfolio = p.build_portfolio(root, season=2026, week=4, as_of=datetime(2026, 9, 30, tzinfo=timezone.utc))
        paths = p.write_canonical_pregame_capture(root, portfolio)
        capture = json.loads(paths["capture"].read_text(encoding="utf-8"))
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

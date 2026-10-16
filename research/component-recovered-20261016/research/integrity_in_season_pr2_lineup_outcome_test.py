#!/usr/bin/env python3
"""No-network exact league-scoring outcome tests for PR2 lineup captures."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import build_in_season_pr2_lineup_outcome as b
import evaluate_in_season_pr2_lineups as e
import in_season_pr2_weekly_lineups as p
from integrity_in_season_pr2_weekly_lineups_test import fixture, setup, write


def capture_fixture(root: Path) -> dict:
    setup(root); fixture(root, "1")
    write(root / "data/research/leagues/registry.json", {"leagues": {"1": {"enabled": True, "league_name": "Alpha", "format": "REDRAFT", "priority": "HIGH"}}})
    portfolio = p.build_portfolio(root, season=2026, week=4, as_of=datetime(2026, 9, 30, tzinfo=timezone.utc))
    paths = p.write_canonical_pregame_capture(root, portfolio)
    return json.loads(paths["capture"].read_text(encoding="utf-8"))


def test_exact_profile_scoring_and_evaluator_replay():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); capture = capture_fixture(root)
        raw = {
            "schema": b.RAW_SCHEMA,
            "provider": "fixture",
            "endpoint": "fixture",
            "observed_at": "2026-10-02T12:00:00+00:00",
            "sparse_zero_fields_are_explicit": True,
            "stats_by_player_id": {
                "canonical:a": {"rushing_yards": 50},
                "canonical:b": {"rushing_yards": 100},
                "canonical:c": {"receptions": 3},
                "canonical:q": {"receiving_yards": 10},
            },
        }
        outcome = b.build_outcome(capture, raw, outcome_revision_id="official-final-v1")
        assert outcome["league_scoring_replay"]["1"]["status"] == "READY"
        assert outcome["league_player_realized_points"]["1"] == {"canonical:a": 5.0, "canonical:b": 10.0, "canonical:c": 3.0, "canonical:q": 0.0}
        result = e.evaluate_capture(capture, outcome, root=root)
        assert result["leagues"][0]["recommended_realized_points"] == 15
        paths = b.write_outcome(root / "outcome", outcome, raw)
        assert b.write_outcome(root / "outcome", outcome, raw) == paths and paths["outcome"].is_file()


def test_missing_raw_player_stats_stays_typed_not_zero_filled():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); capture = capture_fixture(root)
        raw = {"schema": b.RAW_SCHEMA, "observed_at": "2026-10-02T12:00:00+00:00", "sparse_zero_fields_are_explicit": True, "stats_by_player_id": {}}
        outcome = b.build_outcome(capture, raw, outcome_revision_id="official-final-v1")
        assert outcome["league_scoring_replay"]["1"]["status"] == "BLOCKED_OUTCOME_REPLAY_INCOMPLETE"
        assert "1" not in outcome["league_player_realized_points"]


def test_kicker_and_dst_exact_scoring_stay_position_specific():
    kicker, kdiag = b.score_candidate({"position_model": "K"}, {"fgm": 2, "xpm": 1}, {"fgm": 3, "xpm": 1}, sparse_zero_is_explicit=True)
    defense, ddiag = b.score_candidate({"position_model": "DEF"}, {"points_allowed": 0, "sack": 2}, {"pts_allow_0": 10, "sack": 1}, sparse_zero_is_explicit=True)
    assert kicker == 7 and kdiag["exact"] is True
    assert defense == 12 and ddiag["exact"] is True


def main() -> None:
    tests = [test_exact_profile_scoring_and_evaluator_replay, test_missing_raw_player_stats_stays_typed_not_zero_filled, test_kicker_and_dst_exact_scoring_stay_position_specific]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 lineup outcome scoring ({len(tests)} tests)")


if __name__ == "__main__":
    main()

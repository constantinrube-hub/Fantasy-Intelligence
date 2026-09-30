#!/usr/bin/env python3
"""No-network identity-binding tests for PR2 outcome source adaptation."""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import adapt_in_season_pr2_lineup_outcome_stats as a
import build_in_season_pr2_lineup_outcome as b
from integrity_in_season_pr2_lineup_outcome_test import capture_fixture


def source(capture: dict) -> dict:
    return {
        "schema": a.SOURCE_SCHEMA,
        "provider": "fixture-provider",
        "endpoint": "fixture://player-stats/2026/4",
        "observed_at": "2026-10-02T12:00:00+00:00",
        "season": capture["leagues"][0]["season"],
        "week": capture["leagues"][0]["week"],
        "sparse_zero_fields_are_explicit": True,
        "stats_by_source_player_id": {"a": {"rushing_yards": 50}, "b": {"rushing_yards": 100}, "c": {"receptions": 3}, "q": {"receiving_yards": 10}},
    }


def test_adapter_binds_only_frozen_capture_identities():
    with tempfile.TemporaryDirectory() as td:
        capture = capture_fixture(Path(td))
        raw = a.adapt_source(capture, source(capture))
        assert raw["schema"] == b.RAW_SCHEMA
        assert raw["stats_by_player_id"] == {"canonical:a": {"rushing_yards": 50}, "canonical:b": {"rushing_yards": 100}, "canonical:c": {"receptions": 3}, "canonical:q": {"receiving_yards": 10}}
        assert {row["status"] for row in raw["identity_bindings"]} == {"READY"}
        assert raw["governance"]["missing_provider_rows_zero_imputed"] is False


def test_missing_provider_row_remains_missing_for_typed_outcome_blocker():
    with tempfile.TemporaryDirectory() as td:
        capture = capture_fixture(Path(td)); payload = source(capture)
        del payload["stats_by_source_player_id"]["q"]
        raw = a.adapt_source(capture, payload)
        assert "canonical:q" not in raw["stats_by_player_id"]
        assert any(row["status"] == "MISSING_PROVIDER_STAT_ROW" for row in raw["identity_bindings"])
        outcome = b.build_outcome(capture, raw, outcome_revision_id="fixture")
        assert outcome["league_scoring_replay"]["1"]["status"] == "BLOCKED_OUTCOME_REPLAY_INCOMPLETE"


def test_target_mismatch_and_identity_collision_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        capture = capture_fixture(Path(td)); wrong = source(capture); wrong["week"] = 5
        try:
            a.adapt_source(capture, wrong)
            raise AssertionError("week mismatch accepted")
        except ValueError as exc:
            assert "target" in str(exc)
        conflict = copy.deepcopy(capture)
        candidates = conflict["leagues"][0]["evaluation_input"]["active_candidates"]
        candidates[1]["sleeper_id"] = candidates[0]["sleeper_id"]
        try:
            a.adapt_source(conflict, source(capture))
            raise AssertionError("identity collision accepted")
        except ValueError as exc:
            assert "conflicting" in str(exc)


def test_frozen_team_defense_can_use_explicit_direct_outcome_only():
    with tempfile.TemporaryDirectory() as td:
        capture = capture_fixture(Path(td))
        candidate = capture["leagues"][0]["evaluation_input"]["active_candidates"][0]
        candidate.update({"captured_player_id": "teamdef:AAA", "position_model": "DEF", "team": "AAA"})
        payload = source(capture)
        payload["direct_stats_by_captured_player_id"] = {"teamdef:AAA": {"sack": 2, "points_allowed": 0}}
        raw = a.adapt_source(capture, payload)
        assert raw["stats_by_player_id"]["teamdef:AAA"]["sack"] == 2
        binding = next(row for row in raw["identity_bindings"] if row["captured_player_id"] == "teamdef:AAA")
        assert binding["status"] == "READY_DIRECT_TEAM_DEFENSE" and binding["source_player_id_namespace"] == "teamdef"


def main() -> None:
    tests = [test_adapter_binds_only_frozen_capture_identities, test_missing_provider_row_remains_missing_for_typed_outcome_blocker, test_target_mismatch_and_identity_collision_fail_closed, test_frozen_team_defense_can_use_explicit_direct_outcome_only]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 lineup outcome adapter ({len(tests)} tests)")


if __name__ == "__main__":
    main()

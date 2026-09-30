#!/usr/bin/env python3
"""No-network tests for PR2 nflverse completed-week outcome capture."""
from __future__ import annotations

import tempfile
from pathlib import Path

import adapt_in_season_pr2_lineup_outcome_stats as a
import capture_in_season_pr2_lineup_nflverse_outcomes as n
from integrity_in_season_pr2_lineup_outcome_test import capture_fixture


CSV = """player_id,season,week,season_type,rushing_yards,fg_made,pat_made\n00-0000001,2026,4,REG,50,,\n00-0000002,2026,4,REG,,2,1\n00-0000003,2026,5,REG,99,,\n""".encode()
PBP = """game_id,home_team,away_team,season,week,season_type,defteam,posteam,sack,interception,fumble_forced,fumble_lost,safety,touchdown,td_team,yards_gained,play_type,return_team\ng1,AAA,BBB,2026,4,REG,AAA,BBB,2,1,1,1,0,0,,250,pass,\ng1,AAA,BBB,2026,4,REG,BBB,AAA,0,0,0,0,0,0,,300,pass,\n""".encode()


def with_gsis(capture: dict) -> dict:
    for index, candidate in enumerate(capture["leagues"][0]["evaluation_input"]["active_candidates"], start=1):
        candidate["gsis_id"] = f"00-000000{index}"
    return capture


def with_dst(capture: dict) -> dict:
    capture["leagues"][0]["evaluation_input"]["active_candidates"].append({"captured_player_id": "teamdef:AAA", "position_model": "DEF", "team": "AAA"})
    return capture


def test_nflverse_source_uses_frozen_gsis_ids_and_regular_target_week_only():
    with tempfile.TemporaryDirectory() as td:
        capture = with_gsis(capture_fixture(Path(td)))
        source = n.build_source(capture, CSV, season=2026, week=4, observed_at="2026-10-02T12:00:00+00:00", endpoint="fixture://stats")
        assert source["source_player_id_namespace"] == "gsis"
        assert source["stats_by_source_player_id"] == {"00-0000001": {"player_id": "00-0000001", "season": "2026", "week": "4", "season_type": "REG", "rushing_yards": "50"}, "00-0000002": {"player_id": "00-0000002", "season": "2026", "week": "4", "season_type": "REG", "fg_made": "2", "pat_made": "1"}}
        raw = a.adapt_source(capture, source)
        assert raw["source_player_id_namespace"] == "gsis"
        assert any(row["status"] == "MISSING_PROVIDER_STAT_ROW" for row in raw["identity_bindings"])


def test_capture_target_mismatch_and_duplicate_rows_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        capture = with_gsis(capture_fixture(Path(td)))
        try:
            n.build_source(capture, CSV, season=2026, week=5, observed_at="x", endpoint="fixture")
            raise AssertionError("mismatched target accepted")
        except ValueError as exc:
            assert "capture season/week" in str(exc)
        duplicate = CSV + b"00-0000001,2026,4,REG,1,,\n"
        try:
            n.build_source(capture, duplicate, season=2026, week=4, observed_at="x", endpoint="fixture")
            raise AssertionError("duplicate player row accepted")
        except ValueError as exc:
            assert "duplicate" in str(exc)


def test_dst_is_replayed_only_from_target_week_pbp_not_team_score_guess():
    with tempfile.TemporaryDirectory() as td:
        capture = with_dst(with_gsis(capture_fixture(Path(td))))
        source = n.build_source(capture, CSV, season=2026, week=4, observed_at="x", endpoint="fixture", pbp_bytes=PBP, pbp_endpoint="fixture://pbp")
        dst = source["direct_stats_by_captured_player_id"]["teamdef:AAA"]
        assert dst["sack"] == 2 and dst["int"] == 1 and dst["points_allowed"] == 0.0 and dst["yards_allowed"] == 250.0
        assert source["coverage"]["team_defense_supported"] is True


def main() -> None:
    tests = [test_nflverse_source_uses_frozen_gsis_ids_and_regular_target_week_only, test_capture_target_mismatch_and_duplicate_rows_fail_closed, test_dst_is_replayed_only_from_target_week_pbp_not_team_score_guess]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 nflverse lineup outcome capture ({len(tests)} tests)")


if __name__ == "__main__":
    main()

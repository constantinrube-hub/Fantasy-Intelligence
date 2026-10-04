#!/usr/bin/env python3
"""No-network contract tests for the PR2 weekly lineup evidence capture."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import capture_in_season_pr2_lineup_evidence as c


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path) -> None:
    lid = "1"
    write(root / "config/league-portfolio.json", {"sleeper_username": "C0nstant1n"})
    write(root / "data/research/leagues/registry.json", {"leagues": {lid: {"enabled": True, "league_name": "Alpha", "format": "REDRAFT"}}})
    core = {"league_id": lid, "sleeper": {"users": [{"user_id": "u", "display_name": "C0nstant1n"}], "rosters": [{"roster_id": 4, "owner_id": "u", "players": ["a", "b"]}]}}
    core_path = root / "data/research/leagues/1/app/core.json"
    write(core_path, core)
    write(root / "data/research/leagues/1/app/manifest.json", {"core": {"path": "data/research/leagues/1/app/core.json", "sha256": sha(core_path)}})
    write(root / "data/research/leagues/1/current/milestone5_current.json", {"season": 2026, "week": 4, "players": [{"sleeper_id": "a", "canonical_player_id": "a", "team": "AAA", "position_model": "RB"}, {"sleeper_id": "b", "canonical_player_id": "b", "team": "BBB", "position_model": "WR"}]})


def test_schedule_slice_and_exact_player_bindings():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        schedule = [{"home_team": "AAA", "away_team": "BBB", "kickoff_utc": "2026-10-01T00:15:00+00:00", "game_id": "2026_04_BBB_AAA"}]
        evidence = c.build_evidence(root, season=2026, week=4, observed_at="2026-09-30T12:00:00+00:00", schedule=schedule, matchup_payloads={"1": [{"roster_id": 4, "matchup_id": 9, "points": 0}, {"roster_id": 8, "matchup_id": 9, "points": 0}]})
        locks = evidence["lock_evidence_by_league"]["1"]
        assert locks["player_kickoffs"] == {"canonical:a": "2026-10-01T00:15:00+00:00", "canonical:b": "2026-10-01T00:15:00+00:00"}
        assert evidence["matchup_evidence_by_league"]["1"]["rows"][1]["roster_id"] == 8
        assert evidence["league_bindings"][0]["current_snapshot_sha256"]


def test_first_write_is_idempotent_and_scope_is_registry_bound():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); fixture(root)
        schedule = [{"home_team": "AAA", "away_team": "BBB", "kickoff_utc": "2026-10-01T00:15:00+00:00", "game_id": "g"}]
        evidence = c.build_evidence(root, season=2026, week=4, observed_at="2026-09-30T12:00:00+00:00", schedule=schedule, matchup_payloads={"1": []})
        paths = c.write_capture(root, evidence, {"schedule_games": schedule, "matchup_payloads": {"1": []}})
        again = c.write_capture(root, evidence, {"schedule_games": schedule, "matchup_payloads": {"1": []}})
        assert paths == again and paths["capture"].is_file() and paths["latest"].is_file()
        try:
            c.build_evidence(root, season=2026, week=4, observed_at="2026-09-30T12:00:00+00:00", schedule=schedule, matchup_payloads={"1": []}, league_scope={"retired"})
        except ValueError as exc:
            assert "no enabled leagues" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("retired/non-registry scope was accepted")


def test_nflverse_csv_filters_regular_season_only():
    csv_bytes = b"season,week,game_type,home_team,away_team,gameday,gametime,game_id\n2026,4,REG,AAA,BBB,2026-10-01,20:15,g\n2026,4,PRE,CCC,DDD,2026-10-01,20:15,pre\n"
    rows = c.schedule_games(csv_bytes, season=2026, week=4)
    assert rows == [{"home_team": "AAA", "away_team": "BBB", "kickoff_utc": "2026-10-02T00:15:00+00:00", "game_id": "g"}]


def checkpoint_csv() -> bytes:
    return (
        b"season,week,game_type,home_team,away_team,gameday,gametime,game_id\n"
        b"2026,5,REG,AAA,BBB,2026-10-08,20:15,thu\n"
        b"2026,5,REG,CCC,DDD,2026-10-11,13:00,sun\n"
        b"2026,5,REG,EEE,FFF,2026-10-11,16:25,late\n"
    )


def test_automatic_week_open_and_sunday_checkpoints_are_dynamic_and_bounded():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        week_open = c.automatic_capture_decision(root, checkpoint_csv(), season=2026, as_of="2026-10-08T18:15:00+00:00")
        assert week_open["capture_allowed"] is True
        assert week_open["checkpoint_id"] == "PR2_WEEK_OPEN_T6" and week_open["week"] == 5
        assert week_open["hours_before_anchor"] == 6.0
        sunday = c.automatic_capture_decision(root, checkpoint_csv(), season=2026, as_of="2026-10-11T13:00:00+00:00")
        assert sunday["checkpoint_id"] == "PR2_SUNDAY_MAIN_T4"
        assert sunday["anchor_at"] == "2026-10-11T17:00:00+00:00"
        outside = c.automatic_capture_decision(root, checkpoint_csv(), season=2026, as_of="2026-10-10T11:00:00+00:00")
        assert outside["capture_allowed"] is False and outside["reason"] == "OUTSIDE_CHECKPOINT_WINDOW"


def test_existing_automatic_checkpoint_suppresses_provider_capture_retry():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        capture = root / "data/research/evaluation/2026/weeks/week-5/lineups/evidence/captures/portfolio-existing/operational-evidence.json"
        write(capture, {"season": 2026, "week": 5, "checkpoint_id": "PR2_WEEK_OPEN_T6"})
        result = c.automatic_capture_decision(root, checkpoint_csv(), season=2026, as_of="2026-10-08T18:15:00+00:00")
        assert result["capture_allowed"] is False
        assert result["reason"] == "CHECKPOINT_ALREADY_CAPTURED"


def main() -> None:
    tests = [
        test_schedule_slice_and_exact_player_bindings,
        test_first_write_is_idempotent_and_scope_is_registry_bound,
        test_nflverse_csv_filters_regular_season_only,
        test_automatic_week_open_and_sunday_checkpoints_are_dynamic_and_bounded,
        test_existing_automatic_checkpoint_suppresses_provider_capture_retry,
    ]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 lineup capture ({len(tests)} tests)")


if __name__ == "__main__":
    main()

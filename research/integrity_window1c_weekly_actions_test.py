#!/usr/bin/env python3
"""Focused synthetic integrity tests for Window 1C."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import window1c_weekly_actions as w


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def league_fixture(root: Path, lid: str, *, fmt: str = "REDRAFT", drift: bool = False, realized_guard: bool = True) -> None:
    fp = "fp-live"
    league_root = root / "data/research/leagues" / lid
    write(league_root / "profile.json", {
        "league_id": lid,
        "format": fmt,
        "profile_fingerprint": fp,
        "scoring_signature": "sig1",
    })
    core = {
        "schema": "fie-league-core-v1",
        "schema_version": 1,
        "league_id": lid,
        "league_name": f"League {lid}",
        "format": fmt,
        "profile_fingerprint": fp,
        "scoring_signature": "sig1",
        "shared": {"player_catalog": "data/research/app/player-catalog.json"},
        "sleeper": {
            "league": {
                "league_id": lid,
                "roster_positions": ["QB", "RB", "FLEX", "BN", "BN"],
                "settings": {"waiver_budget": 100},
            },
            "rosters": [
                {
                    "roster_id": 1,
                    "owner_id": "u1",
                    "players": ["A", "B", "C", "D"],
                    "starters": ["A", "B", "C"],
                    "settings": {"waiver_budget_used": 10},
                },
                {
                    "roster_id": 2,
                    "owner_id": "u2",
                    "players": ["X"],
                    "starters": ["X", "0", "0"],
                    "settings": {},
                },
            ],
            "users": [
                {"user_id": "u1", "display_name": "C0nstant1n", "metadata": {"team_name": "My Team"}},
                {"user_id": "u2", "display_name": "Other", "metadata": {}},
            ],
        },
    }
    core_path = league_root / "app/core.json"
    write(core_path, core)
    write(league_root / "app/manifest.json", {
        "schema": "fie-league-manifest-v1",
        "league_id": lid,
        "profile_fingerprint": fp,
        "scoring_signature": "sig1",
        "core": {
            "path": f"data/research/leagues/{lid}/app/core.json",
            "sha256": sha(core_path),
            "bytes": core_path.stat().st_size,
        },
    })
    current_players = [
        {"sleeper_id": "A", "full_name": "Alpha QB", "position_model": "QB", "team": "AAA", "opponent": "BBB", "decision_weekly_projection": 20.0, "fie_weekly_projection": 20.0, "sleeper_weekly_projection": 19.0, "weekly_activation_eligible": True, "projection_source": "M6 FIE raw-stat model", "p10": 15.0, "p90": 25.0, "confidence": 80, "waiver_activation_eligible": False},
        {"sleeper_id": "B", "full_name": "Beta RB", "position_model": "RB", "team": "AAA", "opponent": "BBB", "decision_weekly_projection": 8.0, "fie_weekly_projection": None, "sleeper_weekly_projection": 8.0, "weekly_activation_eligible": False, "projection_source": "Sleeper diagnostic only (M6 gate off)", "p10": None, "p90": None, "confidence": 30, "waiver_activation_eligible": False},
        {"sleeper_id": "C", "full_name": "Charlie WR", "position_model": "WR", "team": "AAA", "opponent": "BBB", "decision_weekly_projection": 7.0, "fie_weekly_projection": None, "sleeper_weekly_projection": 7.0, "weekly_activation_eligible": False, "projection_source": "Sleeper diagnostic only (M6 gate off)", "p10": None, "p90": None, "confidence": 25, "waiver_activation_eligible": False},
        {"sleeper_id": "D", "full_name": "Delta WR", "position_model": "WR", "team": "CCC", "opponent": "DDD", "decision_weekly_projection": 12.0, "fie_weekly_projection": 12.0, "sleeper_weekly_projection": 11.0, "weekly_activation_eligible": True, "projection_source": "M6 blend FIE 0.60 / Sleeper 0.40", "p10": 8.0, "p90": 16.0, "confidence": 75, "waiver_activation_eligible": False},
        {"sleeper_id": "E", "full_name": "Echo RB", "position_model": "RB", "team": "EEE", "opponent": "FFF", "decision_weekly_projection": 13.0, "fie_weekly_projection": 13.0, "sleeper_weekly_projection": 12.0, "weekly_activation_eligible": True, "projection_source": "M6 FIE raw-stat model", "p10": 9.0, "p90": 17.0, "confidence": 78, "waiver_activation_eligible": True, "waiver_next3_projection": 14.0, "waiver_feature_coverage": 0.8},
        {"sleeper_id": "F", "full_name": "Foxtrot WR", "position_model": "WR", "team": "GGG", "opponent": "HHH", "decision_weekly_projection": 11.0, "fie_weekly_projection": None, "sleeper_weekly_projection": 11.0, "weekly_activation_eligible": False, "projection_source": "Sleeper diagnostic only (M6 gate off)", "p10": None, "p90": None, "confidence": 28, "waiver_activation_eligible": False, "waiver_next3_projection": None},
        {"sleeper_id": "X", "full_name": "Owned Elsewhere", "position_model": "RB", "team": "III", "opponent": "JJJ", "decision_weekly_projection": 18.0, "fie_weekly_projection": 18.0, "sleeper_weekly_projection": 17.0, "weekly_activation_eligible": True, "projection_source": "M6 FIE raw-stat model", "waiver_activation_eligible": True, "waiver_next3_projection": 20.0},
    ]
    write(league_root / "current/milestone5_current.json", {
        "schema_version": 3,
        "generated_at": "2026-09-08T06:00:00+00:00",
        "status": "complete",
        "season": 2026,
        "week": 2,
        "season_type": "regular",
        "league_id": lid,
        "league_format": fmt,
        "profile_fingerprint": fp,
        "live_profile_fingerprint": "fp-drift" if drift else fp,
        "profile_current_match": not drift,
        "profile_diff": {"roster_positions": {"old": 5, "new": 6}} if drift else {},
        "scoring_signature": "sig1",
        "snapshot_max_age_hours": 18,
        "target_week_realised_stats_excluded": realized_guard,
        "players": current_players,
        "summary": {"weekly_activation_eligible": 4, "waiver_activation_eligible": 2},
        "source_health": {"reason": None},
        "kickoff": {"first_kickoff_utc": "2026-09-10T00:20:00+00:00"},
    })


def setup_root(root: Path) -> None:
    catalog = {
        "fields": ["player_id", "full_name", "position", "status", "injury_status"],
        "players": {
            "A": {"player_id": "A", "full_name": "Alpha QB", "position": "QB", "fantasy_positions": ["QB"], "status": "Active"},
            "B": {"player_id": "B", "full_name": "Beta RB", "position": "RB", "fantasy_positions": ["RB"], "status": "Active", "injury_status": "Out"},
            "C": {"player_id": "C", "full_name": "Charlie WR", "position": "WR", "fantasy_positions": ["WR"], "status": "Active"},
            "D": {"player_id": "D", "full_name": "Delta WR", "position": "WR", "fantasy_positions": ["WR"], "status": "Active"},
            "E": {"player_id": "E", "full_name": "Echo RB", "position": "RB", "fantasy_positions": ["RB"], "status": "Active"},
            "F": {"player_id": "F", "full_name": "Foxtrot WR", "position": "WR", "fantasy_positions": ["WR"], "status": "Active"},
            "X": {"player_id": "X", "full_name": "Owned Elsewhere", "position": "RB", "fantasy_positions": ["RB"], "status": "Active"},
        },
    }
    write(root / "data/research/app/player-catalog.json", catalog)
    write(root / "config/league-portfolio.json", {"schema_version": 1, "sleeper_username": "C0nstant1n", "leagues": []})


def test_managed_action_report() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "111111", fmt="REDRAFT")
        write(root / "data/research/leagues/registry.json", {"leagues": {"111111": {"enabled": True, "format": "REDRAFT", "league_name": "Test Redraft", "profile_fingerprint": "fp-live"}}})
        write(root / "data/research/evaluation/2026/weeks/week-1/league-111111/evaluation-v1.json", {"schema": "fie-window1b-weekly-evaluation-v1", "status": "READY", "league_id": "111111", "season": 2026, "week": 1, "metrics": {"mae": 3.2}})
        as_of = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
        out = w.build_portfolio(root, season=2026, week=2, as_of=as_of)
        assert out["enabled_league_count"] == 1
        league = out["leagues"][0]
        assert league["status"] == "ACTION_REQUIRED"
        assert league["managed_roster_id"] == 1
        assert league["evidence"]["projection_source_mix_owned_roster"]["FIE_GOVERNED"] == 2
        assert league["evidence"]["projection_source_mix_owned_roster"]["SLEEPER_FALLBACK"] == 2
        assert league["actions"]["injury_alerts"][0]["player_id"] == "B"
        assert league["actions"]["injury_alerts"][0]["severity"] == "URGENT"
        assert len(league["actions"]["lineup"]) == 1
        swap = league["actions"]["lineup"][0]
        assert swap["start"]["player_id"] == "D"
        assert swap["bench"]["player_id"] == "C"
        assert abs(swap["projection_delta"] - 5.0) < 1e-9
        waiver = league["actions"]["waiver_watchlist"]
        assert waiver[0]["player_id"] == "E"
        assert all(x["player_id"] != "X" for x in waiver)
        assert all(x.get("bid_recommendation") is None for x in waiver)
        assert all(x.get("drop_recommendation") is None for x in waiver)
        assert all(x.get("action") not in {"CLAIM", "PASS"} for x in waiver)
        assert league["prior_week_evaluation"]["metrics"]["mae"] == 3.2
        assert league["governance"]["faab_optimization"] is False
        assert league["governance"]["window_1d_reserved_for_waiver_optimization"] is True


def test_best_ball_disables_start_sit() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "222222", fmt="REDRAFT_BESTBALL")
        reg = {"enabled": True, "format": "REDRAFT_BESTBALL", "league_name": "Best Ball", "profile_fingerprint": "fp-live"}
        as_of = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
        out = w.build_league_report(root, "222222", reg, username="C0nstant1n", as_of=as_of, target_season=2026, target_week=2)
        assert out["action_status"]["lineup"] == "NOT_APPLICABLE_BEST_BALL"
        assert out["actions"]["lineup"] == []


def test_profile_drift_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "333333", drift=True)
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "Drift", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "333333", reg, username="C0nstant1n", as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["status"] == "BLOCKED_PROFILE_DRIFT"
        assert out["actions"]["lineup"] == []


def test_stale_snapshot_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "444444")
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "Stale", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "444444", reg, username="C0nstant1n", as_of=datetime(2026, 9, 9, 2, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["status"] == "BLOCKED_STALE_CURRENT_SNAPSHOT"


def test_realized_stats_guard_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "555555", realized_guard=False)
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "Leak", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "555555", reg, username="C0nstant1n", as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["status"] == "BLOCKED_REALIZED_STATS_GUARD"


def test_missing_user_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "666666")
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "No User", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "666666", reg, username="Nobody", as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["status"] == "BLOCKED_MANAGED_ROSTER_UNRESOLVED"


def test_app_core_drift_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "777777")
        core = root / "data/research/leagues/777777/app/core.json"
        core.write_text(core.read_text(encoding="utf-8") + " ", encoding="utf-8")
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "App Drift", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "777777", reg, username="C0nstant1n", as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["status"] == "BLOCKED_APP_CORE_DRIFT"


def test_week_mismatch_blocks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "888888")
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "Wrong Week", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "888888", reg, username="C0nstant1n", as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc), target_season=2026, target_week=3)
        assert out["status"] == "BLOCKED_WEEK_MISMATCH"


def test_missing_projection_never_becomes_zero() -> None:
    row = {"decision_weekly_projection": None, "sleeper_weekly_projection": None, "weekly_activation_eligible": False}
    rec = w.player_action_record("Z", row, {})
    assert rec["weekly_projection"] is None
    assert rec["projection_source_class"] == "UNAVAILABLE"


def test_after_kickoff_downgrades_execution() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "999999")
        # Extend freshness so we can specifically test the kickoff guard.
        cur = root / "data/research/leagues/999999/current/milestone5_current.json"
        x = json.loads(cur.read_text())
        x["snapshot_max_age_hours"] = 72
        write(cur, x)
        reg = {"enabled": True, "format": "REDRAFT", "league_name": "After Kickoff", "profile_fingerprint": "fp-live"}
        out = w.build_league_report(root, "999999", reg, username="C0nstant1n", as_of=datetime(2026, 9, 10, 1, tzinfo=timezone.utc), target_season=2026, target_week=2)
        assert out["action_status"]["lineup"] == "LOCKED_AFTER_FIRST_KICKOFF"
        assert out["actions"]["lineup"][0]["action"] == "REVIEW_ONLY_AFTER_KICKOFF"


def main() -> None:
    tests = [
        test_managed_action_report,
        test_best_ball_disables_start_sit,
        test_profile_drift_blocks,
        test_stale_snapshot_blocks,
        test_realized_stats_guard_blocks,
        test_missing_user_blocks,
        test_app_core_drift_blocks,
        test_week_mismatch_blocks,
        test_missing_projection_never_becomes_zero,
        test_after_kickoff_downgrades_execution,
    ]
    for test in tests:
        test()
    print(f"PASS Window 1C weekly actions integrity ({len(tests)} tests)")


if __name__ == "__main__":
    main()

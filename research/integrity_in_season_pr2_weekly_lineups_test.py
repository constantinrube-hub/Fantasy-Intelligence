#!/usr/bin/env python3
"""Synthetic no-network tests for the first PR2 producer milestone."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import in_season_pr2_weekly_lineups as p


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path, lid: str, *, fmt: str = "REDRAFT", missing: bool = False) -> None:
    league_root = root / "data/research/leagues" / lid
    profile = {"league_id": lid, "format": fmt, "profile_fingerprint": "fp", "scoring_signature": "score-a"}
    write(league_root / "profile.json", profile)
    core = {
        "league_id": lid, "format": fmt, "profile_fingerprint": "fp", "shared": {"player_catalog": "data/research/app/player-catalog.json"},
        "sleeper": {"league": {"roster_positions": ["RB", "FLEX", "BN"]}, "users": [{"user_id": "u", "display_name": "C0nstant1n"}], "rosters": [{"roster_id": 1, "owner_id": "u", "players": ["a", "b", "c", "q"], "starters": ["a", "c"]}]},
    }
    core_path = league_root / "app/core.json"
    write(core_path, core)
    write(league_root / "app/manifest.json", {"core": {"path": f"data/research/leagues/{lid}/app/core.json", "sha256": sha(core_path)}})
    rows = [
        {"sleeper_id": "a", "canonical_player_id": "a", "position_model": "RB", "decision_weekly_projection": 20, "weekly_activation_eligible": True, "fie_weekly_projection": 20, "p10": 14, "p90": 26},
        {"sleeper_id": "b", "canonical_player_id": "b", "position_model": "RB", "decision_weekly_projection": 19, "weekly_activation_eligible": True, "fie_weekly_projection": 19, "p10": 13, "p90": 25},
        {"sleeper_id": "c", "canonical_player_id": "c", "position_model": "WR", "decision_weekly_projection": 18, "weekly_activation_eligible": True, "fie_weekly_projection": 18, "p10": 10, "p90": 28},
        {"sleeper_id": "q", "canonical_player_id": "q", "position_model": "WR", "decision_weekly_projection": None if missing else 4, "weekly_activation_eligible": False, "fie_weekly_projection": None, "p10": None, "p90": None},
    ]
    write(league_root / "current/milestone5_current.json", {"season": 2026, "week": 4, "profile_fingerprint": "fp", "profile_current_match": True, "target_week_realised_stats_excluded": True, "scoring_signature": "score-a", "players": rows})


def setup(root: Path) -> None:
    write(root / "config/contracts/runtime-contracts.json", {"position_aliases": {"DST": "DEF"}, "roster_slots": {"RB": {"positions": ["RB"], "starter": True}, "FLEX": {"positions": ["RB", "WR", "TE"], "starter": True}, "BN": {"positions": [], "starter": False}}})
    write(root / "config/league-portfolio.json", {"sleeper_username": "C0nstant1n"})
    write(root / "data/research/app/player-catalog.json", {"players": {"a": {"position": "RB"}, "b": {"position": "RB"}, "c": {"position": "WR"}, "q": {"position": "WR", "injury_status": "QUESTIONABLE"}}})


def test_exact_primary_and_submitted_delta():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "1")
        report = p.build_league(root, "1", {"league_name": "Alpha", "format": "REDRAFT"}, username="C0nstant1n", target_season=2026, target_week=4)
        assert report["status"] == "ACTION_REQUIRED"
        assert report["primary_lineup"]["total"] == 39
        assert report["submitted_lineup"]["total"] == 38
        assert report["actions"] and report["actions"][0]["start_player_id"] == "canonical:b"
        assert report["contingencies"][0]["scenario"] == "INACTIVE_CONTINGENCY"
        assert report["opponent_context"]["status"] == "NOT_YET_CAPTURED"


def test_best_ball_is_not_a_manual_action():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "2", fmt="REDRAFT_BESTBALL")
        report = p.build_league(root, "2", {"league_name": "Ball", "format": "REDRAFT_BESTBALL"}, username="C0nstant1n")
        assert report["status"] == "NOT_APPLICABLE_AUTOMATIC_LINEUP"
        assert report["primary_lineup"] is None


def test_material_missing_projection_blocks():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "3", missing=True)
        report = p.build_league(root, "3", {"league_name": "Missing", "format": "REDRAFT"}, username="C0nstant1n")
        assert report["status"] == "BLOCKED_MATERIAL_PROJECTION_MISSING"


def main() -> None:
    tests = [test_exact_primary_and_submitted_delta, test_best_ball_is_not_a_manual_action, test_material_missing_projection_blocks]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 weekly lineup producer ({len(tests)} tests)")


if __name__ == "__main__":
    main()


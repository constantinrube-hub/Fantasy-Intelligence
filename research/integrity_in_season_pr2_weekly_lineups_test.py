#!/usr/bin/env python3
"""Synthetic no-network tests for the first PR2 producer milestone."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
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
        "sleeper": {"league": {"roster_positions": ["RB", "FLEX", "BN"]}, "users": [{"user_id": "u", "display_name": "C0nstant1n"}], "rosters": [{"roster_id": 1, "owner_id": "u", "players": ["a", "b", "c", "q"], "starters": ["a", "c"]}, {"roster_id": 8, "owner_id": "opponent", "players": ["b", "c"], "starters": ["b", "c"]}]},
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
    write(league_root / "current/milestone5_current.json", {"season": 2026, "week": 4, "profile_fingerprint": "fp", "profile_current_match": True, "target_week_realised_stats_excluded": True, "scoring_signature": "score-a", "kickoff": {"first_kickoff_utc": "2026-10-01T00:15:00+00:00"}, "players": rows})


def setup(root: Path) -> None:
    write(root / "config/contracts/runtime-contracts.json", {"position_aliases": {"DST": "DEF"}, "roster_slots": {"RB": {"positions": ["RB"], "starter": True}, "FLEX": {"positions": ["RB", "WR", "TE"], "starter": True}, "BN": {"positions": [], "starter": False}}})
    write(root / "config/league-portfolio.json", {"sleeper_username": "C0nstant1n"})
    write(root / "data/research/app/player-catalog.json", {"players": {"a": {"position": "RB"}, "b": {"position": "RB"}, "c": {"position": "WR"}, "q": {"position": "WR", "injury_status": "QUESTIONABLE"}}})


def test_exact_primary_and_submitted_delta():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "1")
        report = p.build_league(root, "1", {"league_name": "Alpha", "format": "REDRAFT"}, username="C0nstant1n", target_season=2026, target_week=4, as_of=datetime(2026, 9, 30, tzinfo=timezone.utc))
        assert report["status"] == "ACTION_REQUIRED"
        assert report["primary_lineup"]["total"] == 39
        assert report["submitted_lineup"]["total"] == 38
        assert report["actions"] and report["actions"][0]["start_player_id"] == "canonical:b"
        assert report["contingencies"][0]["scenario"] == "INACTIVE_CONTINGENCY"
        assert report["opponent_context"]["status"] == "NOT_YET_CAPTURED"
        assert report["lock_state"]["status"] == "PREGAME_BEFORE_FIRST_KICKOFF"


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


def test_verified_locks_and_h2h_context_are_evidence_bound():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "4")
        current_path = root / "data/research/leagues/4/current/milestone5_current.json"
        current = json.loads(current_path.read_text(encoding="utf-8"))
        current["kickoff"]["first_kickoff_utc"] = "2026-09-29T00:15:00+00:00"
        write(current_path, current)
        locks = {"player_kickoffs": {"canonical:a": "2026-09-30T00:00:00+00:00", "canonical:b": "2026-10-02T00:00:00+00:00", "canonical:c": "2026-10-02T00:00:00+00:00", "canonical:q": "2026-10-02T00:00:00+00:00"}}
        matchup = {"captured_at": "2026-09-30T01:00:00+00:00", "rows": [{"roster_id": 1, "matchup_id": 7, "points": 0}, {"roster_id": 8, "matchup_id": 7, "points": 0}]}
        report = p.build_league(root, "4", {"league_name": "Locked", "format": "REDRAFT"}, username="C0nstant1n", as_of=datetime(2026, 9, 30, 1, tzinfo=timezone.utc), lock_evidence=locks, matchup_evidence=matchup)
        assert report["lock_state"]["status"] == "PLAYER_LOCKS_VERIFIED"
        assert report["primary_lineup"]["actionable"] is True
        assert {x["slot_index"]: x["player_id"] for x in report["primary_lineup"]["assignment"]}[0] == "canonical:a"
        assert report["opponent_context"]["status"] == "CAPTURED_H2H_CONTEXT"
        assert report["opponent_context"]["actionable"] is False


def test_after_kickoff_without_player_times_is_review_only():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "5")
        report = p.build_league(root, "5", {"league_name": "No locks", "format": "REDRAFT"}, username="C0nstant1n", as_of=datetime(2026, 10, 1, 2, tzinfo=timezone.utc))
        assert report["lock_state"]["status"] == "BLOCKED_PLAYER_KICKOFF_EVIDENCE_MISSING"
        assert report["primary_lineup"]["actionable"] is False
        assert report["actions"][0]["action"] == "REVIEW_ONLY_LOCK_EVIDENCE_UNRESOLVED"


def test_pregame_opponent_context_and_ceiling_stay_advisory():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "7")
        current_path = root / "data/research/leagues/7/current/milestone5_current.json"
        current = json.loads(current_path.read_text(encoding="utf-8"))
        for row in current["players"]:
            if row["sleeper_id"] == "q":
                row.update({"weekly_activation_eligible": True, "fie_weekly_projection": 4, "p10": 2, "p90": 7})
        write(current_path, current)
        matchup = {"captured_at": "2026-09-30T01:00:00+00:00", "rows": [{"roster_id": 1, "matchup_id": 7, "points": 0}, {"roster_id": 8, "matchup_id": 7, "points": 0}]}
        report = p.build_league(root, "7", {"league_name": "H2H", "format": "REDRAFT"}, username="C0nstant1n", as_of=datetime(2026, 9, 30, tzinfo=timezone.utc), matchup_evidence=matchup)
        context = report["opponent_context"]
        assert context["status"] == "CAPTURED_H2H_CONTEXT"
        assert context["opponent_lineup"]["status"] == "EXACT_MAX_MEAN_ADVISORY"
        assert context["opponent_lineup"]["actionable"] is False
        assert context["projected_mean_margin"] == 2
        assert report["ceiling_advisory"]["status"] == "CEILING_ADVISORY"
        assert report["ceiling_advisory"]["actionable"] is False


def test_immutable_capture_is_pregame_and_idempotent():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); setup(root); fixture(root, "6")
        write(root / "data/research/leagues/registry.json", {"leagues": {"6": {"enabled": True, "league_name": "Capture", "format": "REDRAFT"}}})
        report = p.build_portfolio(root, season=2026, week=4, as_of=datetime(2026, 9, 30, tzinfo=timezone.utc))
        paths = p.write_canonical_pregame_capture(root, report)
        again = p.write_canonical_pregame_capture(root, report)
        assert paths["capture"] == again["capture"] and paths["capture"].is_file() and paths["latest"].is_file()


def test_external_evidence_envelope_is_typed_and_target_bound():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        evidence = root / "evidence.json"
        write(evidence, {"schema": "fie-in-season-pr2-weekly-lineup-evidence-v1", "season": 2026, "week": 4, "lock_evidence_by_league": {"1": {"player_kickoffs": {}}}, "matchup_evidence_by_league": {"1": {"rows": []}}})
        locks, matchups = p.evidence_maps(evidence, season=2026, week=4)
        assert set(locks) == {"1"} and set(matchups) == {"1"}
        try:
            p.evidence_maps(evidence, season=2026, week=5)
        except p.LineupEvidenceError as exc:
            assert str(exc) == "BLOCKED_LINEUP_EVIDENCE_WEEK_MISMATCH"
        else:  # pragma: no cover
            raise AssertionError("mismatched evidence was accepted")


def test_portfolio_exposure_preserves_scoring_context_and_focus_order():
    reports = [
        {"league_id": "a", "league_name": "AEF - FFLeague", "format": "REDRAFT", "priority": "HIGH", "status": "ACTION_REQUIRED", "evidence": {"scoring_signature": "score-a"}, "primary_lineup": {"selected_player_ids": ["canonical:x"], "bench_player_ids": ["canonical:y"], "total": 100}, "submitted_lineup": {"assignment": [], "total": 90}, "actions": [{}], "official_unavailable": []},
        {"league_id": "b", "league_name": "Chopped - Drive", "format": "CHOPPED", "priority": "VERY_HIGH", "status": "READY_NO_LINEUP_CHANGE", "evidence": {"scoring_signature": "score-b"}, "primary_lineup": {"selected_player_ids": ["canonical:y"], "bench_player_ids": ["canonical:x"], "total": 80}, "submitted_lineup": {"assignment": [], "total": 80}, "actions": [], "official_unavailable": []},
    ]
    intelligence = p.portfolio_intelligence(reports)
    assert intelligence["priority_queue"][0]["league_id"] == "a"
    conflict = next(x for x in intelligence["cross_league_role_differences"] if x["player_id"] == "canonical:x")
    assert conflict["actionable"] is False
    assert {x["scoring_signature"] for x in conflict["recommended_starter_contexts"] + conflict["recommended_bench_contexts"]} == {"score-a", "score-b"}


def main() -> None:
    tests = [test_exact_primary_and_submitted_delta, test_best_ball_is_not_a_manual_action, test_material_missing_projection_blocks, test_verified_locks_and_h2h_context_are_evidence_bound, test_after_kickoff_without_player_times_is_review_only, test_pregame_opponent_context_and_ceiling_stay_advisory, test_immutable_capture_is_pregame_and_idempotent, test_external_evidence_envelope_is_typed_and_target_bound, test_portfolio_exposure_preserves_scoring_context_and_focus_order]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 weekly lineup producer ({len(tests)} tests)")


if __name__ == "__main__":
    main()

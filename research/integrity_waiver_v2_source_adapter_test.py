#!/usr/bin/env python3
"""Integrity checks for conservative raw-source normalization into Waiver-v2."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from waiver_v2_source_adapter import adapt, normalize_player_stats, normalize_weekly_roster


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    stats_path, roster_path, games_path, identity_path = [root / name for name in ("stats.csv", "roster.csv", "games.csv", "identity.csv")]
    pd.DataFrame([
        {"season": 2025, "week": 1, "season_type": "REG", "player_id": "p-qb", "recent_team": "AAA", "position": "QB", "passing_yards": 250, "passing_tds": 2, "interceptions": 1, "rushing_yards": 5, "receptions": 0, "kickoff_return_yards": 0, "punt_return_yards": 0},
        {"season": 2025, "week": 1, "season_type": "REG", "player_id": "p-wr", "recent_team": "BBB", "position": "WR", "passing_yards": 0, "passing_tds": 0, "interceptions": 0, "rushing_yards": 0, "receptions": 4},
        # Aggregate/non-player rows can lack player identity and must not block
        # the offensive-player source contract.
        {"season": 2025, "week": 1, "season_type": "REG", "player_id": None, "recent_team": "AAA", "position": "TEAM", "passing_yards": 250},
    ]).to_csv(stats_path, index=False)
    pd.DataFrame([
        {"season": 2025, "week": 1, "game_type": "REG", "team": "AAA", "position": "QB", "gsis_id": "p-qb", "status": "ACT"},
        {"season": 2025, "week": 1, "game_type": "REG", "team": "BBB", "position": "WR", "gsis_id": "p-wr", "status": "ACT"},
        {"season": 2025, "week": 1, "game_type": "REG", "team": "CCC", "position": "RB", "gsis_id": "p-rb", "status": "RES"},
        # Transaction code RSR is overridden by the documented current active
        # weekly-status description, while E01 remains undocumented.
        {"season": 2025, "week": 1, "game_type": "REG", "team": "AAA", "position": "WR", "gsis_id": "p-active", "status": "RSR", "status_description_abbr": "A01"},
        {"season": 2025, "week": 1, "game_type": "REG", "team": "BBB", "position": "TE", "gsis_id": "p-unknown", "status": "E01", "status_description_abbr": "E01"},
        # A roster-only historical player can retain an exact GSIS ID after
        # dropping from the current master catalogue; a missing ID cannot be
        # converted into a player-week zero.
        {"season": 2025, "week": 1, "game_type": "REG", "team": "AAA", "position": "WR", "gsis_id": "00-0039999", "status": "ACT"},
        {"season": 2025, "week": 1, "game_type": "REG", "team": "BBB", "position": "TE", "gsis_id": None, "status": "ACT"},
    ]).to_csv(roster_path, index=False)
    pd.DataFrame([{"season": 2025, "week": 1, "game_type": "REG", "home_team": "AAA", "away_team": "BBB", "home_score": 20, "away_score": 17}]).to_csv(games_path, index=False)
    pd.DataFrame([
        {"gsis_id": "p-qb", "canonical_player_id": "QB1"},
        {"gsis_id": "p-wr", "canonical_player_id": "WR1"},
        {"gsis_id": "p-rb", "canonical_player_id": "RB1"},
        {"gsis_id": "p-active", "canonical_player_id": "WR2"},
        {"gsis_id": "p-unknown", "canonical_player_id": "TE1"},
    ]).to_csv(identity_path, index=False)
    receipt = adapt(raw_player_stats_path=stats_path, raw_weekly_roster_path=roster_path, raw_games_path=games_path, identity_path=identity_path, output_dir=root / "adapted")
    canonical_stats = pd.read_csv(root / "adapted" / "player-stats.csv.gz")
    canonical_schedule = pd.read_csv(root / "adapted" / "team-schedule.csv.gz")
    assert receipt["activation_eligible"] is False
    assert receipt["exact_stat_bindings"]["passing_interceptions"] == "interceptions"
    assert receipt["exact_stat_bindings"]["kickoff_return_yards"] == "kickoff_return_yards"
    assert receipt["exact_stat_bindings"]["punt_return_yards"] == "punt_return_yards"
    assert receipt["weekly_roster_status_audit"]["active_description_override_count"] == 1
    assert receipt["weekly_roster_status_audit"]["excluded_undocumented_status_counts"] == {"E01": 1}
    assert receipt["weekly_roster_status_audit"]["exact_source_gsis_fallback_ids"] == 1
    assert receipt["weekly_roster_status_audit"]["excluded_missing_identity_rows"] == 1
    assert canonical_stats.loc[canonical_stats.canonical_player_id.eq("QB1"), "passing_interceptions"].iloc[0] == 1
    bye = canonical_schedule[canonical_schedule.team.eq("CCC")].iloc[0]
    assert not bool(bye.team_has_game) and bool(bye.game_complete)

    canonical_roster, audit = normalize_weekly_roster(pd.read_csv(roster_path), pd.read_csv(identity_path), return_audit=True)
    assert "WR2" in set(canonical_roster.canonical_player_id)
    assert "00-0039999" in set(canonical_roster.canonical_player_id)
    assert "TE1" not in set(canonical_roster.canonical_player_id)
    assert audit["excluded_undocumented_status_counts"] == {"E01": 1}

    unresolved_offense = pd.read_csv(stats_path)
    unresolved_offense.loc[0, "player_id"] = "missing-qb"
    try:
        normalize_player_stats(unresolved_offense, pd.read_csv(identity_path))
        raise AssertionError("unresolved offensive player must still fail closed")
    except ValueError as error:
        assert "unresolved canonical identities" in str(error)

    unresolved_roster = pd.read_csv(roster_path)
    unresolved_roster.loc[0, "gsis_id"] = "unmapped-gsis"
    try:
        normalize_weekly_roster(unresolved_roster, pd.read_csv(identity_path))
        raise AssertionError("unresolved roster player must still fail closed")
    except ValueError as error:
        assert "unresolved canonical identities" in str(error)

    missing_team = pd.read_csv(roster_path).query("team != 'BBB'")
    missing_team.to_csv(roster_path, index=False)
    try:
        adapt(raw_player_stats_path=stats_path, raw_weekly_roster_path=roster_path, raw_games_path=games_path, identity_path=identity_path, output_dir=root / "missing")
        raise AssertionError("scheduled team absent from roster must fail closed")
    except ValueError as error:
        assert "omits scheduled teams" in str(error)

print("OK waiver-v2 raw-source adapter exactness and completeness contract")

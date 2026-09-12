#!/usr/bin/env python3
"""Counterfactual raw-stat replay for completed 2026 Week 1 games.

This is explicitly not an original pregame capture. It replays frozen M9 using
only 2025 completed game history, then joins 2026 completed box-score stats.
No fantasy scoring, league profile, market or decision output is produced.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from week1_game_projections import (
    CORE_POSITIONS, GAMES_URL, PLAYER_WEEK_URL, PLAYERS_URL, ROOT,
    canonical_team, fetch_bytes, game_rows, history_frame, identity_match,
    sleeper_team_players, utc_now, write_csv,
)

SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
GAME_IDS = {"NE_SEA", "SF_LAR"}


def raw_actuals(stats: pd.DataFrame, identity: pd.DataFrame, season: int, game_teams: set[str]) -> pd.DataFrame:
    """Normalize completed target-week components without using them as inputs."""
    frame = history_frame(stats, identity, season + 1)
    frame = frame[(pd.to_numeric(frame["season"], errors="coerce") == season) & (pd.to_numeric(frame["week"], errors="coerce") == 1)]
    frame["team"] = frame["team"].map(canonical_team)
    return frame[frame["team"].isin(game_teams)].copy()


def build(output_root: Path, *, observed_at: str | None = None) -> Path:
    observed_at = observed_at or utc_now()
    schedule_raw, _ = fetch_bytes(GAMES_URL)
    games = [game for game in game_rows(pd.read_csv(pd.io.common.BytesIO(schedule_raw), low_memory=False), 2026, 1, observed_at) if f"{game['away_team']}_{game['home_team']}" in GAME_IDS]
    if len(games) != 2:
        raise ValueError("expected exactly NE@SEA and SF@LAR Week 1 games")
    team_game = {team: game for game in games for team in (game["home_team"], game["away_team"])}
    sleeper_raw, _ = fetch_bytes(SLEEPER_PLAYERS_URL)
    sleeper_payload = json.loads(sleeper_raw.decode("utf-8"))
    players_raw, _ = fetch_bytes(PLAYERS_URL)
    history_raw, _ = fetch_bytes(PLAYER_WEEK_URL.format(season=2025))
    actual_raw, _ = fetch_bytes(PLAYER_WEEK_URL.format(season=2026))
    from fie_research import build_identity
    from m10_prospective_weekly_producer import _point_rows
    identity, _ = build_identity(pd.read_csv(pd.io.common.BytesIO(players_raw), low_memory=False))
    sleeper = sleeper_team_players(sleeper_payload, set(team_game))
    mapped, _ = identity_match(identity, sleeper)
    target_rows = []
    for player in sleeper:
        sid = str(player["sleeper_id"])
        if player["position_model"] not in CORE_POSITIONS or sid not in mapped:
            continue
        game = team_game[player["team"]]
        opponent = game["away_team"] if player["team"] == game["home_team"] else game["home_team"]
        target_rows.append({"season": 2026, "week": 1, "canonical_player_id": mapped[sid]["canonical_player_id"], "full_name": player.get("full_name"), "position_model": player["position_model"], "team": player["team"], "opponent_team": opponent, "player_kickoff_at": game["kickoff_at"], "sleeper_id": sid, "game_id": game["game_id"]})
    target = pd.DataFrame(target_rows)
    history = history_frame(pd.read_csv(pd.io.common.BytesIO(history_raw), low_memory=False), identity, 2026)
    lock = json.loads((ROOT / "data/research/prospective/m10/season-locks/2026/season-lock.json").read_text())
    capture = {"season": 2026, "week": 1, "observed_at": "2026-09-09T00:00:00+00:00", "first_kickoff_at": games[0]["kickoff_at"], "schedule_snapshot_sha256": "POSTHOC_RECONSTRUCTION"}
    rows = [row for row in _point_rows(lock, history, target.drop(columns=["sleeper_id", "game_id", "full_name"]), capture=capture, source_bundle_sha256="POSTHOC_RECONSTRUCTION") if row["model"] == "M9"]
    actual = raw_actuals(pd.read_csv(pd.io.common.BytesIO(actual_raw), low_memory=False), identity, 2026, set(team_game))
    actual_map = {str(row["canonical_player_id"]): row for row in actual.to_dict("records")}
    output = []
    extra = {row["canonical_player_id"]: row for row in target_rows}
    for row in rows:
        observed = actual_map.get(row["canonical_player_id"], {})
        meta = extra[row["canonical_player_id"]]
        # Each position lock owns a different raw-component set.  Comparing a
        # QB against receiving fields (or a WR against passing fields) creates
        # None predictions and is not a meaningful model error.
        for stat, prediction in sorted(row["predicted_raw_components"].items()):
            value = observed.get(stat)
            actual_value = None
            try:
                candidate = float(value)
                actual_value = candidate if math.isfinite(candidate) else None
            except (TypeError, ValueError):
                pass
            predicted_value = float(prediction)
            output.append({"status": "POSTHOC_RECONSTRUCTION_NOT_ORIGINAL_CAPTURE", "game_id": meta["game_id"], "team": row["team"], "opponent_team": row["opponent_team"], "canonical_player_id": row["canonical_player_id"], "full_name": meta.get("full_name"), "position_model": row["position_model"], "raw_stat": stat, "m9_predicted": predicted_value, "actual": actual_value, "error_actual_minus_prediction": None if actual_value is None else actual_value - predicted_value, "model": "M9_FROZEN_2026_LOCK"})
    out = output_root / "2026" / "week_01" / "posthoc-raw-stat-comparison-v1"
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "player-raw-stat-comparison.csv", output)
    (out / "manifest.json").write_text(json.dumps({"schema": "fie-posthoc-raw-stat-comparison-v1", "status": "POSTHOC_RECONSTRUCTION_NOT_ORIGINAL_CAPTURE", "games": games, "model": "M9 frozen 2026 lock", "history_input": "2025 completed regular season only", "outcome_input": "2026 Week 1 completed player-week box scores", "league_scoring_used": False}, indent=2) + "\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", default="data/research/evaluation"); args = parser.parse_args()
    root = Path(args.output_root); print(build(root if root.is_absolute() else ROOT / root))

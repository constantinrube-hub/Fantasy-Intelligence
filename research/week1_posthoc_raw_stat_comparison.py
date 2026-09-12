#!/usr/bin/env python3
"""Counterfactual raw-stat replay for completed 2026 Week 1 games.

This is explicitly not an original pregame capture. It replays frozen M9 using
only 2025 completed game history, then joins 2026 completed box-score stats.
No fantasy scoring, league profile, market or decision output is produced.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

import pandas as pd

from week1_game_projections import (
    CORE_POSITIONS, GAMES_URL, PLAYER_WEEK_URL, PLAYERS_URL, ROOT,
    UNAVAILABLE, availability_state, canonical_team, fetch_bytes, game_rows,
    history_frame, identity_match, parse_time, utc_now, write_csv,
)

GAME_IDS = {"NE_SEA", "SF_LAR"}
AVAILABILITY_ROOT = ROOT / "data/research/availability/sleeper/2026"


def _snapshot_before(kickoff: str) -> tuple[Path, str]:
    """Select the latest immutable availability capture before kickoff."""
    candidates = []
    for meta_path in AVAILABILITY_ROOT.glob("availability_*.jsonl.gz.meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            captured_at = str(meta["captured_at"])
            if parse_time(captured_at) < parse_time(kickoff):
                data_path = Path(str(meta_path).removesuffix(".meta.json"))
                if data_path.is_file():
                    candidates.append((parse_time(captured_at), data_path, captured_at))
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
    if not candidates:
        raise ValueError(f"no immutable availability snapshot before {kickoff}")
    _, path, captured_at = max(candidates, key=lambda item: item[0])
    return path, captured_at


def _read_snapshot(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def governed_universe(games: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Create the target universe from point-in-time availability evidence.

    Skill players must be active and have an explicit depth-chart order. QB is
    limited to depth-chart order 1; backups remain in the audit as conditional
    non-targets because M9 has no in-game injury probability model.
    """
    selected, audit, bindings = [], [], []
    for game in games:
        path, captured_at = _snapshot_before(game["kickoff_at"])
        bindings.append({"game_id": game["game_id"], "path": str(path.relative_to(ROOT)), "captured_at": captured_at, "kickoff_at": game["kickoff_at"]})
        teams = {game["home_team"], game["away_team"]}
        for raw in _read_snapshot(path):
            team = canonical_team(raw.get("team")); position = str(raw.get("position_model") or "").upper()
            if team not in teams or position not in CORE_POSITIONS:
                continue
            state = availability_state(raw)
            depth = raw.get("depth_chart_order")
            try:
                depth_value = int(depth) if depth is not None and math.isfinite(float(depth)) else None
            except (TypeError, ValueError):
                depth_value = None
            blocker = None
            if state in UNAVAILABLE or str(raw.get("status") or "").strip().lower() not in {"active", "act"}:
                blocker = "BLOCKED_CONFIRMED_OR_ROSTER_UNAVAILABLE"
            elif depth_value is None:
                blocker = "BLOCKED_DEPTH_CHART_ORDER_MISSING"
            elif position == "QB" and depth_value != 1:
                blocker = "BLOCKED_BACKUP_QB_CONDITIONAL_ONLY"
            row = {**raw, "team": team, "position_model": position, "availability_state": state, "depth_chart_order": depth_value, "game_id": game["game_id"], "snapshot_captured_at": captured_at, "universe_status": blocker or "ELIGIBLE_PREGAME_TARGET"}
            audit.append(row)
            if blocker is None:
                selected.append(row)
    # A player belongs to one scheduled game. Duplicates indicate corrupt input.
    if len({row["sleeper_id"] for row in selected}) != len(selected):
        raise ValueError("duplicate player across governed game universes")
    return selected, audit, bindings


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
    players_raw, _ = fetch_bytes(PLAYERS_URL)
    history_raw, _ = fetch_bytes(PLAYER_WEEK_URL.format(season=2025))
    actual_raw, _ = fetch_bytes(PLAYER_WEEK_URL.format(season=2026))
    from fie_research import build_identity
    from m10_prospective_weekly_producer import _point_rows
    identity, _ = build_identity(pd.read_csv(pd.io.common.BytesIO(players_raw), low_memory=False))
    sleeper, universe_audit, availability_bindings = governed_universe(games)
    mapped, ambiguous = identity_match(identity, sleeper)
    target_rows = []
    for player in sleeper:
        sid = str(player["sleeper_id"])
        if player["position_model"] not in CORE_POSITIONS or sid not in mapped:
            continue
        game = team_game[player["team"]]
        opponent = game["away_team"] if player["team"] == game["home_team"] else game["home_team"]
        target_rows.append({"season": 2026, "week": 1, "canonical_player_id": mapped[sid]["canonical_player_id"], "full_name": player.get("full_name"), "position_model": player["position_model"], "team": player["team"], "opponent_team": opponent, "player_kickoff_at": game["kickoff_at"], "sleeper_id": sid, "game_id": game["game_id"], "availability_state": player["availability_state"], "depth_chart_order": player["depth_chart_order"], "availability_captured_at": player["snapshot_captured_at"]})
    target = pd.DataFrame(target_rows)
    history = history_frame(pd.read_csv(pd.io.common.BytesIO(history_raw), low_memory=False), identity, 2026)
    lock = json.loads((ROOT / "data/research/prospective/m10/season-locks/2026/season-lock.json").read_text())
    capture = {"season": 2026, "week": 1, "observed_at": max(binding["captured_at"] for binding in availability_bindings), "first_kickoff_at": games[0]["kickoff_at"], "schedule_snapshot_sha256": "POSTHOC_RECONSTRUCTION"}
    metadata_columns = ["sleeper_id", "game_id", "full_name", "availability_state", "depth_chart_order", "availability_captured_at"]
    rows = [row for row in _point_rows(lock, history, target.drop(columns=metadata_columns), capture=capture, source_bundle_sha256="POSTHOC_RECONSTRUCTION") if row["model"] == "M9"]
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
            output.append({"status": "POSTHOC_RECONSTRUCTION_NOT_ORIGINAL_CAPTURE", "game_id": meta["game_id"], "team": row["team"], "opponent_team": row["opponent_team"], "canonical_player_id": row["canonical_player_id"], "full_name": meta.get("full_name"), "position_model": row["position_model"], "availability_state": meta["availability_state"], "depth_chart_order": meta["depth_chart_order"], "availability_captured_at": meta["availability_captured_at"], "raw_stat": stat, "m9_predicted": predicted_value, "actual": actual_value, "error_actual_minus_prediction": None if actual_value is None else actual_value - predicted_value, "model": "M9_FROZEN_2026_LOCK"})
    out = output_root / "2026" / "week_01" / "posthoc-raw-stat-comparison-v1"
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "player-raw-stat-comparison.csv", output)
    write_csv(out / "universe-audit.csv", universe_audit)
    (out / "manifest.json").write_text(json.dumps({"schema": "fie-posthoc-raw-stat-comparison-v2", "status": "POSTHOC_RECONSTRUCTION_NOT_ORIGINAL_CAPTURE", "games": games, "model": "M9 frozen 2026 lock", "history_input": "2025 completed regular season only", "target_universe_input": "latest immutable Sleeper availability snapshot captured before each kickoff", "availability_bindings": availability_bindings, "universe_policy": {"skill_players": "active with explicit depth-chart order", "quarterbacks": "depth-chart order 1 only", "confirmed_unavailable": "excluded", "missing_depth_chart_order": "excluded", "backup_qb": "conditional-only and excluded from M9 target/reconciliation"}, "eligible_players": len(target_rows), "identity_ambiguous_or_unresolved": len(ambiguous), "outcome_input": "2026 Week 1 completed player-week box scores", "league_scoring_used": False}, indent=2) + "\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", default="data/research/evaluation"); args = parser.parse_args()
    root = Path(args.output_root); print(build(root if root.is_absolute() else ROOT / root))

"""Shared, as-of feature construction for corrected M10 prospective locks.

The module is intentionally usable by both historical training construction and a
future weekly producer.  Team budgets are computed on team games, never within a
player history, so a transferred player's old team cannot leak into a new-team row.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

FEATURES = ("player_prior4_volume", "player_prior4_efficiency", "team_prior4_budget")
RAW_TARGETS = (
    "attempts", "completions", "passing_yards", "passing_tds", "interceptions",
    "carries", "rushing_yards", "rushing_tds", "targets", "receptions",
    "receiving_yards", "receiving_tds",
)
REQUIRED_IDENTITY = ("season", "week", "canonical_player_id", "position_model", "team")


def _number(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce")


def _prior4(values: pd.Series) -> pd.Series:
    return values.shift(1).rolling(4, min_periods=2).mean()


def _prepare(rows: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_IDENTITY) - set(rows.columns)
    if missing:
        raise ValueError(f"M10 feature rows lack identity fields: {sorted(missing)}")
    frame = rows.copy()
    for name in RAW_TARGETS:
        if name not in frame:
            frame[name] = float("nan")
        frame[name] = _number(frame[name])
    frame["_volume"] = frame[["attempts", "carries", "targets"]].sum(axis=1, min_count=1)
    frame["_yards"] = frame[["passing_yards", "rushing_yards", "receiving_yards"]].sum(axis=1, min_count=1)
    frame["_efficiency"] = frame["_yards"] / frame["_volume"].where(frame["_volume"] > 0)
    return frame.sort_values(["season", "week", "canonical_player_id", "team"], kind="mergesort").reset_index(drop=True)


def build_features(completed_rows: pd.DataFrame, target_rows: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return shared pregame features for completed history and optional target rows.

    `completed_rows` must contain only completed regular-season games. `target_rows`
    contains identities known before kickoff and no target-week outcomes. Its rows are
    never eligible to contribute to a rolling history.
    """
    history = _prepare(completed_rows)
    history["_completed"] = True
    if target_rows is None:
        combined = history
    else:
        target = _prepare(target_rows)
        target["_completed"] = False
        for name in RAW_TARGETS:
            if target[name].notna().any():
                raise ValueError("prospective target rows must not contain target-week outcomes")
        combined = pd.concat([history, target], ignore_index=True, sort=False)
        combined = combined.sort_values(["season", "week", "canonical_player_id", "team", "_completed"], kind="mergesort").reset_index(drop=True)

    completed = combined[combined["_completed"]].copy()
    player = completed.sort_values(["canonical_player_id", "season", "week"], kind="mergesort").copy()
    player["player_prior4_volume"] = player.groupby("canonical_player_id", sort=False)["_volume"].transform(_prior4)
    player["player_prior4_efficiency"] = player.groupby("canonical_player_id", sort=False)["_efficiency"].transform(_prior4)
    player_values = player[["season", "week", "canonical_player_id", "team", "player_prior4_volume", "player_prior4_efficiency"]]

    team_games = completed.groupby(["season", "week", "team"], as_index=False, sort=True)["_volume"].sum(min_count=1)
    team_games = team_games.sort_values(["team", "season", "week"], kind="mergesort")
    team_games["team_prior4_budget"] = team_games.groupby("team", sort=False)["_volume"].transform(_prior4)
    team_values = team_games[["season", "week", "team", "team_prior4_budget"]]

    result = combined.merge(player_values, on=["season", "week", "canonical_player_id", "team"], how="left", validate="many_to_one")
    result = result.merge(team_values, on=["season", "week", "team"], how="left", validate="many_to_one")
    # Target rows do not exist in player_values. Compute their player history from
    # completed rows only, while keeping team budget keyed to their own target team.
    targets = result[~result["_completed"]].copy()
    if len(targets):
        history_player = completed.sort_values(["canonical_player_id", "season", "week"], kind="mergesort")
        prior_rows = []
        for index, row in targets.iterrows():
            prior = history_player[(history_player["canonical_player_id"] == row["canonical_player_id"]) & ((history_player["season"] < row["season"]) | ((history_player["season"] == row["season"]) & (history_player["week"] < row["week"])))]
            prior = prior.tail(4)
            result.loc[index, "player_prior4_volume"] = prior["_volume"].mean() if len(prior) >= 2 else float("nan")
            result.loc[index, "player_prior4_efficiency"] = prior["_efficiency"].mean() if len(prior) >= 2 else float("nan")
            team_prior = team_games[(team_games["team"] == row["team"]) & ((team_games["season"] < row["season"]) | ((team_games["season"] == row["season"]) & (team_games["week"] < row["week"])))]
            team_prior = team_prior.tail(4)
            result.loc[index, "team_prior4_budget"] = team_prior["_volume"].mean() if len(team_prior) >= 2 else float("nan")
    return result.sort_values(["season", "week", "canonical_player_id", "team"], kind="mergesort").reset_index(drop=True)


def feature_record(row: pd.Series) -> dict[str, float | None]:
    """Create JSON-safe values while retaining missing values as null."""
    values: dict[str, float | None] = {}
    for name in FEATURES:
        value = row.get(name)
        values[name] = None if pd.isna(value) else float(value)
    return values


def row_key(row: pd.Series) -> str:
    return f"{int(row['season'])}-{int(row['week']):02d}-{row['canonical_player_id']}-{row['position_model']}-{row['team']}"


def validate_feature_names(values: Iterable[str]) -> None:
    if tuple(values) != FEATURES:
        raise ValueError("M10 v2 feature names are not the locked shared order")

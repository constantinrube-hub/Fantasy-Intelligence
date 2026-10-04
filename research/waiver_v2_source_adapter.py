#!/usr/bin/env python3
"""Normalize nflverse-style historical sources for the Waiver-v2 ledger.

This adapter is deliberately conservative.  It only applies documented,
semantic field renames; it refuses unresolved identities, unknown roster
statuses, duplicate player-week rows, or a roster source that omits a scheduled
team.  Its output is an explicit research input contract, not an M5 mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from scoring_relevance import canonical_position


OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE"}
# Source: nflreadr roster-status data dictionary.  These statuses identify a
# player still attached to the weekly team universe.  A reserve/inactive player
# receives a confirmed zero only after the schedule/stat-completeness gates in
# the outcome ledger; this adapter does not infer availability.
ROSTERED_MEMBERSHIP_STATUSES = {"ACT", "DEV", "E14", "EXE", "INA", "PUP", "RES", "RSN", "SUS"}
# nflreadr documents these as waived, released, retired, or free-agent states.
# They are not a weekly team member and therefore cannot become a synthetic
# player-week zero.
DEPARTED_ROSTER_STATUSES = {"CUT", "NWT", "RET", "RFA", "RSR", "TRC", "TRD", "TRT", "UFA"}
# The historical `status` field can retain a transaction code while the weekly
# `status_description_abbr` states the actual active roster designation. A01
# is the documented active designation and wins over the transaction code.
ACTIVE_STATUS_DESCRIPTIONS = {"A01"}
# An nflverse weekly roster can retain a historical player whose row is absent
# from today's master player catalogue.  A syntactically exact GSIS ID is still
# a canonical identity under the repository-wide identity policy, so it can be
# used only as its own canonical fallback.  Names and other source fields never
# become identity fallbacks.
EXACT_GSIS_ID = re.compile(r"^00-\d{7}$")
# Each fallback is already used in the research pipeline and has a known
# identical statistical meaning; arbitrary similar names are not accepted.
EXACT_STAT_RENAMES = {
    "passing_interceptions": ("passing_interceptions", "interceptions"),
    "attempts": ("attempts", "passing_attempts"),
    "carries": ("carries", "rushing_attempts"),
    # E2 uses the published player-week sacks suffered total as the canonical
    # scoring value for Sleeper's QB-only pass_sack rule. nflverse names that
    # field ``sacks_suffered``; a direct ``sacks`` field remains equivalent
    # when a source supplies it. PBP is retained separately to reconcile the
    # passer/week accounting rather than overwrite it.
    "sacks": ("sacks", "sacks_suffered"),
    # E4 reconciles individual return yards directly against the published
    # player-week aggregates; aliases are intentionally not accepted.
    "kickoff_return_yards": ("kickoff_return_yards",),
    "punt_return_yards": ("punt_return_yards",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _first(frame: pd.DataFrame, choices: tuple[str, ...], label: str) -> str:
    for choice in choices:
        if choice in frame.columns:
            return choice
    raise ValueError(f"waiver-v2 source adapter missing {label}; expected one of {', '.join(choices)}")


def _regular(frame: pd.DataFrame) -> pd.DataFrame:
    type_column = next((column for column in ("season_type", "game_type") if column in frame.columns), None)
    if type_column is None:
        return frame.copy()
    return frame[frame[type_column].astype(str).str.upper().isin({"REG", "REGULAR"})].copy()


def _identity_map(identity: pd.DataFrame) -> pd.DataFrame:
    required = {"gsis_id", "canonical_player_id"}
    if not required <= set(identity.columns):
        raise ValueError("waiver-v2 identity source requires gsis_id and canonical_player_id")
    result = identity[["gsis_id", "canonical_player_id"]].dropna().copy()
    result["gsis_id"] = result["gsis_id"].astype(str).str.strip()
    result["canonical_player_id"] = result["canonical_player_id"].astype(str).str.strip()
    result = result[(result.gsis_id != "") & (result.canonical_player_id != "")]
    if result.duplicated("gsis_id").any():
        raise ValueError("waiver-v2 identity source has duplicate gsis_id bindings")
    return result


def _missing_source_identity(values: pd.Series) -> pd.Series:
    normalized = values.astype("string").str.strip()
    return values.isna() | normalized.isin({"", "nan", "None", "<NA>"})


def normalize_player_stats(raw_stats: pd.DataFrame, identity: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Return canonical regular-season player stats and exact rename receipt."""
    source = _regular(raw_stats)
    id_column = _first(source, ("gsis_id", "player_id", "nflverse_id"), "player identity")
    season_column = _first(source, ("season",), "season")
    week_column = _first(source, ("week",), "week")
    team_column = _first(source, ("recent_team", "team"), "player team")
    position_column = _first(source, ("position", "position_model"), "player position")
    result = source.copy()
    # nflverse player-week releases can include non-player aggregate rows. They
    # are outside the offensive-player ledger universe and may not carry a
    # player ID. Filter them before requiring canonical PlayerIdentity.
    result["position_model"] = result[position_column].map(canonical_position)
    result = result[result.position_model.isin(OFFENSIVE_POSITIONS)].copy()
    result["_source_gsis_id"] = result[id_column].astype(str).str.strip()
    result = result.merge(_identity_map(identity), left_on="_source_gsis_id", right_on="gsis_id", how="left", validate="many_to_one")
    unresolved = result["canonical_player_id"].isna() | result["canonical_player_id"].astype(str).str.strip().isin({"", "nan", "None"})
    if unresolved.any():
        sample = sorted({str(value).strip() for value in result.loc[unresolved, "_source_gsis_id"].tolist()})[:8]
        raise ValueError(f"waiver-v2 player stats contain unresolved canonical identities: {sample}")
    result["season"] = pd.to_numeric(result[season_column], errors="raise").astype(int)
    result["week"] = pd.to_numeric(result[week_column], errors="raise").astype(int)
    result["team"] = result[team_column].astype(str).str.strip().str.upper()
    if (result.team == "").any() or result.team.isin({"NAN", "NONE"}).any():
        raise ValueError("waiver-v2 player stats contain an unresolved team")
    bindings: dict[str, str] = {}
    for canonical, candidates in EXACT_STAT_RENAMES.items():
        present = [column for column in candidates if column in result.columns]
        if not present:
            continue
        chosen = present[0]
        if len(present) > 1:
            left = pd.to_numeric(result[present[0]], errors="coerce")
            right = pd.to_numeric(result[present[1]], errors="coerce")
            unequal = left.notna() & right.notna() & ~left.eq(right)
            if unequal.any():
                raise ValueError(f"waiver-v2 stat aliases disagree for {canonical}: {present}")
        result[canonical] = result[chosen]
        bindings[canonical] = chosen
    identity_columns = ["canonical_player_id", "season", "week"]
    if result.duplicated(identity_columns).any():
        raise ValueError("waiver-v2 player stats have duplicate canonical player-season-week rows")
    return result.drop(columns=["_source_gsis_id", "gsis_id"], errors="ignore"), bindings


def normalize_weekly_roster(raw_roster: pd.DataFrame, identity: pd.DataFrame, *, return_audit: bool = False) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    """Return the complete weekly offensive roster universe, without departures.

    Undocumented statuses and rows without an exact source identity are
    excluded from this dense universe and reported in the audit. An exact GSIS
    ID absent from the current master catalogue binds only to itself. This is
    fail-closed at player level: the adapter emits neither a roster row nor an
    inferred zero for unavailable identities, but it does not discard the
    otherwise valid historical source snapshot.
    """
    source = _regular(raw_roster)
    required = {"season", "week", "team", "position", "gsis_id", "status"}
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"waiver-v2 weekly roster missing required fields: {', '.join(missing)}")
    result = source.copy()
    result["position_model"] = result["position"].map(canonical_position)
    result = result[result.position_model.isin(OFFENSIVE_POSITIONS)].copy()
    status = result["status"].astype(str).str.strip().str.upper()
    description = result.get("status_description_abbr", pd.Series("", index=result.index)).fillna("").astype(str).str.strip().str.upper()
    active_override = description.isin(ACTIVE_STATUS_DESCRIPTIONS)
    member = active_override | status.isin(ROSTERED_MEMBERSHIP_STATUSES)
    departed = ~active_override & status.isin(DEPARTED_ROSTER_STATUSES)
    undocumented = ~(member | departed)
    audit = {
        "included_status_counts": status[member].value_counts().sort_index().to_dict(),
        "active_description_override_count": int(active_override.sum()),
        "excluded_departed_status_counts": status[departed].value_counts().sort_index().to_dict(),
        "excluded_undocumented_status_counts": status[undocumented].value_counts().sort_index().to_dict(),
        "excluded_undocumented_rows": int(undocumented.sum()),
    }
    result = result[member].copy()
    result["_source_gsis_id"] = result["gsis_id"].astype(str).str.strip()
    result = result.merge(_identity_map(identity), left_on="_source_gsis_id", right_on="gsis_id", how="left", validate="many_to_one")
    unresolved = result["canonical_player_id"].isna() | result["canonical_player_id"].astype(str).str.strip().isin({"", "nan", "None"})
    exact_gsis_fallback = unresolved & result["_source_gsis_id"].map(lambda value: bool(EXACT_GSIS_ID.fullmatch(str(value))))
    result.loc[exact_gsis_fallback, "canonical_player_id"] = result.loc[exact_gsis_fallback, "_source_gsis_id"]
    missing_identity = unresolved & _missing_source_identity(result["_source_gsis_id"])
    unresolved = unresolved & ~(exact_gsis_fallback | missing_identity)
    audit["exact_source_gsis_fallback_rows"] = int(exact_gsis_fallback.sum())
    audit["exact_source_gsis_fallback_ids"] = int(result.loc[exact_gsis_fallback, "_source_gsis_id"].nunique())
    audit["excluded_missing_identity_rows"] = int(missing_identity.sum())
    if unresolved.any():
        sample = sorted({str(value).strip() for value in result.loc[unresolved, "_source_gsis_id"].tolist()})[:8]
        raise ValueError(f"waiver-v2 weekly roster contains unresolved canonical identities: {sample}")
    result = result[~missing_identity].copy()
    result["season"] = pd.to_numeric(result["season"], errors="raise").astype(int)
    result["week"] = pd.to_numeric(result["week"], errors="raise").astype(int)
    result["team"] = result["team"].astype(str).str.strip().str.upper()
    if (result.team == "").any() or result.team.isin({"NAN", "NONE"}).any():
        raise ValueError("waiver-v2 weekly roster contains an unresolved team")
    output = result[["canonical_player_id", "season", "week", "team", "position_model"]].copy()
    output["roster_complete"] = True
    if output.duplicated(["canonical_player_id", "season", "week"]).any():
        raise ValueError("waiver-v2 weekly roster has duplicate canonical player-season-week rows")
    return (output, audit) if return_audit else output


def normalize_team_schedule(raw_games: pd.DataFrame, weekly_roster: pd.DataFrame) -> pd.DataFrame:
    """Materialize game and confirmed-bye rows for each rostered team-week."""
    games = _regular(raw_games)
    required = {"season", "week"}
    missing = sorted(required - set(games.columns))
    if missing:
        raise ValueError(f"waiver-v2 games source missing required fields: {', '.join(missing)}")
    home = _first(games, ("home_team", "home"), "home team")
    away = _first(games, ("away_team", "away"), "away team")
    home_score = _first(games, ("home_score",), "home score")
    away_score = _first(games, ("away_score",), "away score")
    games = games.copy()
    games["season"] = pd.to_numeric(games["season"], errors="raise").astype(int)
    games["week"] = pd.to_numeric(games["week"], errors="raise").astype(int)
    games["_home"] = games[home].astype(str).str.strip().str.upper()
    games["_away"] = games[away].astype(str).str.strip().str.upper()
    if games.duplicated(["season", "week", "_home"]).any() or games.duplicated(["season", "week", "_away"]).any():
        raise ValueError("waiver-v2 games source has duplicate team-week schedule bindings")
    rows: list[dict[str, Any]] = []
    for (season, week), roster_slice in weekly_roster.groupby(["season", "week"], sort=True):
        game_slice = games[(games.season == int(season)) & (games.week == int(week))]
        if game_slice.empty:
            raise ValueError(f"waiver-v2 games source has no regular-season schedule for {season} week {week}")
        scheduled = set(game_slice._home) | set(game_slice._away)
        roster_teams = set(roster_slice.team.astype(str))
        missing_teams = scheduled - roster_teams
        if missing_teams:
            raise ValueError(f"waiver-v2 weekly roster omits scheduled teams for {season} week {week}: {sorted(missing_teams)}")
        scores_complete = pd.to_numeric(game_slice[home_score], errors="coerce").notna() & pd.to_numeric(game_slice[away_score], errors="coerce").notna()
        schedule_week_complete = bool(scores_complete.all())
        for team in sorted(roster_teams):
            game = game_slice[(game_slice._home == team) | (game_slice._away == team)]
            if game.empty:
                rows.append({"season": int(season), "week": int(week), "team": team, "team_has_game": False, "game_complete": schedule_week_complete})
            else:
                home_value = pd.to_numeric(game.iloc[0][home_score], errors="coerce")
                away_value = pd.to_numeric(game.iloc[0][away_score], errors="coerce")
                complete = bool(pd.notna(home_value) and pd.notna(away_value))
                rows.append({"season": int(season), "week": int(week), "team": team, "team_has_game": True, "game_complete": complete})
    output = pd.DataFrame(rows)
    if output.duplicated(["season", "week", "team"]).any():
        raise ValueError("waiver-v2 normalized schedule has duplicate team-week rows")
    return output


def adapt(
    *, raw_player_stats_path: Path, raw_weekly_roster_path: Path, raw_games_path: Path,
    identity_path: Path, output_dir: Path,
) -> dict[str, Any]:
    """Write three canonical source tables and a deterministic receipt."""
    stats = pd.read_csv(raw_player_stats_path, low_memory=False)
    roster = pd.read_csv(raw_weekly_roster_path, low_memory=False)
    games = pd.read_csv(raw_games_path, low_memory=False)
    identity = pd.read_csv(identity_path, low_memory=False)
    canonical_stats, stat_bindings = normalize_player_stats(stats, identity)
    canonical_roster, roster_audit = normalize_weekly_roster(roster, identity, return_audit=True)
    canonical_schedule = normalize_team_schedule(games, canonical_roster)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "player_stats": output_dir / "player-stats.csv.gz",
        "weekly_roster": output_dir / "weekly-roster.csv.gz",
        "team_schedule": output_dir / "team-schedule.csv.gz",
    }
    for key, frame in (("player_stats", canonical_stats), ("weekly_roster", canonical_roster), ("team_schedule", canonical_schedule)):
        frame.to_csv(paths[key], index=False, compression={"method": "gzip", "mtime": 0})
    receipt = {
        "schema_version": 1,
        "diagnostic_only": True,
        "activation_eligible": False,
        "inputs": {
            "raw_player_stats": {"path": str(raw_player_stats_path), "sha256": _sha256(raw_player_stats_path), "rows": int(len(stats))},
            "raw_weekly_roster": {"path": str(raw_weekly_roster_path), "sha256": _sha256(raw_weekly_roster_path), "rows": int(len(roster))},
            "raw_games": {"path": str(raw_games_path), "sha256": _sha256(raw_games_path), "rows": int(len(games))},
            "identity": {"path": str(identity_path), "sha256": _sha256(identity_path), "rows": int(len(identity))},
        },
        "exact_stat_bindings": stat_bindings,
        "weekly_roster_status_audit": roster_audit,
        "outputs": {key: {"path": str(path), "sha256": _sha256(path), "rows": int(len(frame))} for key, path, frame in (
            ("player_stats", paths["player_stats"], canonical_stats),
            ("weekly_roster", paths["weekly_roster"], canonical_roster),
            ("team_schedule", paths["team_schedule"], canonical_schedule),
        )},
        "limitations": [
            "This adapter only prepares research inputs; it cannot activate M5, recommendations, transactions, or the app.",
            "Undocumented roster statuses are excluded player-by-player with a typed audit; scheduled teams absent from the roster source fail closed.",
            "Only documented exact stat renames are applied; unrecognised source fields remain unavailable to exact scoring.",
        ],
    }
    receipt_path = output_dir / "source-adapter-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize raw sources for the Waiver-v2 exact outcome ledger")
    parser.add_argument("--player-stats", required=True)
    parser.add_argument("--weekly-roster", required=True)
    parser.add_argument("--games", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    receipt = adapt(
        raw_player_stats_path=Path(args.player_stats), raw_weekly_roster_path=Path(args.weekly_roster),
        raw_games_path=Path(args.games), identity_path=Path(args.identity), output_dir=Path(args.output_dir),
    )
    print(json.dumps({"outputs": receipt["outputs"], "activation_eligible": False}, indent=2))


if __name__ == "__main__":
    main()

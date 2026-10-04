#!/usr/bin/env python3
"""Fail-closed offensive outcome ledger for Waiver-v2.

This is deliberately separate from the legacy M1/M5 scorer.  It can produce
an exact, dense player/scoring-week ledger only when a league's active,
position-relevant scoring rules have an explicit weekly-stat implementation
and the supplied roster, schedule, and stat inputs are complete.  Otherwise
it preserves the player-week row with a null outcome and a blocker -- it never
turns missing data into zero or silently uses a partial score.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import pandas as pd

from scoring_relevance import canonical_position, position_relevant, rule_metadata


OFFENSIVE_POSITIONS = ("QB", "RB", "WR", "TE")
OUTCOME_LEDGER_VERSION = "waiver-v2-dense-offensive-outcome-ledger-v1"

# These are intentionally canonical source fields, rather than the permissive
# aliases accepted by the legacy scorer.  A future source reconciliation may
# add another field only after confirming it has identical semantics.
EXACT_WEEKLY_STAT_RULES = {
    "pass_yd": "passing_yards",
    "pass_td": "passing_tds",
    "pass_int": "passing_interceptions",
    "pass_cmp": "completions",
    "pass_att": "attempts",
    "pass_2pt": "passing_2pt_conversions",
    "pass_fd": "passing_first_downs",
    "rush_yd": "rushing_yards",
    "rush_td": "rushing_tds",
    "rush_att": "carries",
    "rush_2pt": "rushing_2pt_conversions",
    "rush_fd": "rushing_first_downs",
    "rec": "receptions",
    "rec_yd": "receiving_yards",
    "rec_td": "receiving_tds",
    "rec_tgt": "targets",
    "rec_2pt": "receiving_2pt_conversions",
    "rec_fd": "receiving_first_downs",
    "fum": "fumbles",
    "fum_lost": "fumbles_lost",
}

POSITION_RECEPTION_RULES = {
    "bonus_rec_te": "TE", "rec_te": "TE",
    "bonus_rec_rb": "RB", "rec_rb": "RB",
    "bonus_rec_wr": "WR", "rec_wr": "WR",
}

THRESHOLD_BONUS_RULES = {
    "bonus_pass_yd_300": ("passing_yards", 300),
    "bonus_pass_yd_400": ("passing_yards", 400),
    "bonus_rush_yd_100": ("rushing_yards", 100),
    "bonus_rush_yd_200": ("rushing_yards", 200),
    "bonus_rec_yd_100": ("receiving_yards", 100),
    "bonus_rec_yd_200": ("receiving_yards", 200),
}


def _finite_nonzero(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) != 0.0
    except (TypeError, ValueError):
        return False


def _true(value: Any) -> bool:
    if value is True:
        return True
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    try:
        if bool(pd.isna(value)):
            return False
    except (TypeError, ValueError):
        pass
    try:
        return bool(value == 1)
    except (TypeError, ValueError):
        return False


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"waiver-v2 {label} missing required columns: {', '.join(missing)}")


def _rule_inventory_row(key: str, weight: float, position: str, available_columns: set[str]) -> dict[str, Any]:
    metadata = rule_metadata(key)
    row: dict[str, Any] = {
        "key": key,
        "weight": weight,
        "position": position,
        "relevance_status": "RELEVANT",
        "rule_family": metadata.get("family"),
        "scoring_contract_sha256": metadata.get("contract_sha256"),
        "required_columns": [],
        "source_kind": "unsupported",
        "support_status": "BLOCKED_UNSUPPORTED_EXACT_SCORING",
        "reason": "no confirmed exact weekly-player-stat implementation",
    }
    if metadata.get("family") == "UNKNOWN":
        row.update({
            "support_status": "UNKNOWN_RULE",
            "reason": "unknown scoring key remains relevant and blocks exact replay",
        })
        return row
    if key in EXACT_WEEKLY_STAT_RULES:
        column = EXACT_WEEKLY_STAT_RULES[key]
        row.update({"required_columns": [column], "source_kind": "weekly_player_stat"})
        if column in available_columns:
            row.update({"support_status": "EXACT_SOURCE_READY", "reason": "canonical weekly player-stat field available"})
        else:
            row["reason"] = f"canonical weekly player-stat field {column} absent"
        return row
    if key in POSITION_RECEPTION_RULES:
        row.update({"required_columns": ["receptions"], "source_kind": "position_reception"})
        if "receptions" in available_columns:
            row.update({"support_status": "EXACT_SOURCE_READY", "reason": "position and receptions are explicit in ledger inputs"})
        else:
            row["reason"] = "canonical weekly receptions field absent"
        return row
    if key in THRESHOLD_BONUS_RULES:
        column, _ = THRESHOLD_BONUS_RULES[key]
        row.update({"required_columns": [column], "source_kind": "threshold_bonus"})
        if column in available_columns:
            row.update({"support_status": "EXACT_SOURCE_READY", "reason": "canonical weekly player-stat threshold field available"})
        else:
            row["reason"] = f"canonical weekly player-stat field {column} absent"
        return row
    return row


def build_offensive_scoring_inventory(
    scoring: Mapping[str, Any],
    *,
    position: str,
    available_columns: set[str] | list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Return a fail-closed, position-specific exact-scoring inventory.

    Rules irrelevant to the supplied offensive position are reported separately
    and cannot block that position.  Every non-zero relevant rule must be
    implemented *and* have its canonical source field available before exact
    replay is allowed.
    """
    pos = canonical_position(position)
    if pos not in OFFENSIVE_POSITIONS:
        raise ValueError(f"waiver-v2 outcome inventory only supports offensive positions: {position}")
    columns = {str(column) for column in available_columns}
    relevant: list[dict[str, Any]] = []
    ignored: list[str] = []
    for raw_key, raw_weight in (scoring or {}).items():
        key = str(raw_key)
        if not _finite_nonzero(raw_weight):
            continue
        if not position_relevant(key, pos):
            ignored.append(key)
            continue
        relevant.append(_rule_inventory_row(key, float(raw_weight), pos, columns))
    ready = [row["key"] for row in relevant if row["support_status"] == "EXACT_SOURCE_READY"]
    blocked = [row for row in relevant if row["support_status"] != "EXACT_SOURCE_READY"]
    unknown = [row["key"] for row in blocked if row["support_status"] == "UNKNOWN_RULE"]
    return {
        "outcome_ledger_version": OUTCOME_LEDGER_VERSION,
        "position": pos,
        "relevant_nonzero_rules": relevant,
        "supported_keys": sorted(ready),
        "blocked_keys": blocked,
        "unknown_keys": sorted(unknown),
        "ignored_irrelevant_keys": sorted(ignored),
        "coverage_rate": len(ready) / len(relevant) if relevant else 1.0,
        "exact_replay_eligible": not blocked,
    }


def _score_exact_row(row: pd.Series, scoring: Mapping[str, Any], position: str) -> float:
    """Score only rules already approved by ``build_offensive_scoring_inventory``."""
    total = 0.0
    for raw_key, raw_weight in (scoring or {}).items():
        key = str(raw_key)
        if not _finite_nonzero(raw_weight) or not position_relevant(key, position):
            continue
        weight = float(raw_weight)
        if key in EXACT_WEEKLY_STAT_RULES:
            total += float(row[EXACT_WEEKLY_STAT_RULES[key]]) * weight
        elif key in POSITION_RECEPTION_RULES:
            if position == POSITION_RECEPTION_RULES[key]:
                total += float(row["receptions"]) * weight
        elif key in THRESHOLD_BONUS_RULES:
            column, threshold = THRESHOLD_BONUS_RULES[key]
            total += weight if float(row[column]) >= threshold else 0.0
        else:  # Defensive guard: callers must check inventory before scoring.
            raise ValueError(f"waiver-v2 attempted exact score with unsupported key {key}")
    return total


def build_dense_offensive_outcome_ledger(
    player_stats: pd.DataFrame,
    weekly_roster: pd.DataFrame,
    team_schedule: pd.DataFrame,
    scoring: Mapping[str, Any],
    *,
    scoring_signature: str,
    player_stats_complete: bool,
) -> pd.DataFrame:
    """Build explicit player/scoring-week outcomes from complete input evidence.

    ``weekly_roster`` establishes the player universe; ``team_schedule``
    distinguishes a confirmed bye from a game; and ``player_stats_complete``
    authorizes a missing stat row to be scored as zero for a completed game.
    If any of those proofs is unavailable, the row remains present but its
    outcome is null and incomplete.
    """
    if not str(scoring_signature or "").strip():
        raise ValueError("waiver-v2 outcome ledger requires a scoring_signature")
    identity = ["canonical_player_id", "season", "week"]
    roster_required = identity + ["team", "position_model", "roster_complete"]
    schedule_required = ["season", "week", "team", "team_has_game", "game_complete"]
    _require_columns(weekly_roster, roster_required, "weekly roster")
    _require_columns(team_schedule, schedule_required, "team schedule")
    _require_columns(player_stats, identity, "player stats")
    if weekly_roster.duplicated(identity).any():
        raise ValueError("waiver-v2 weekly roster must have one row per player, season, and scoring week")
    if team_schedule.duplicated(["season", "week", "team"]).any():
        raise ValueError("waiver-v2 team schedule must have one row per team and scoring week")
    if player_stats.duplicated(identity).any():
        raise ValueError("waiver-v2 player stats must have one row per player, season, and scoring week")

    stats_columns = set(player_stats.columns)
    roster = weekly_roster.copy()
    roster["position_model"] = roster["position_model"].map(canonical_position)
    roster = roster[roster["position_model"].isin(OFFENSIVE_POSITIONS)].copy()
    merged = roster.merge(team_schedule, on=["season", "week", "team"], how="left", validate="one_to_one")
    stat_value_columns = [column for column in player_stats.columns if column not in identity]
    merged = merged.merge(player_stats, on=identity, how="left", validate="one_to_one", suffixes=("", "_stat"))

    inventories = {
        position: build_offensive_scoring_inventory(scoring, position=position, available_columns=stats_columns)
        for position in OFFENSIVE_POSITIONS
    }
    records: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        position = str(row["position_model"])
        inventory = inventories[position]
        record = {
            "canonical_player_id": row["canonical_player_id"],
            "season": int(row["season"]),
            "week": int(row["week"]),
            "team": row["team"],
            "position_model": position,
            "scoring_signature": str(scoring_signature),
            "outcome_ledger_version": OUTCOME_LEDGER_VERSION,
            "exact_scoring": bool(inventory["exact_replay_eligible"]),
            "fantasy_points_exact": None,
            "outcome_complete": False,
            "outcome_status": "BLOCKED_UNSUPPORTED_EXACT_SCORING",
            "outcome_blocker_codes": ";".join(sorted({item["support_status"] for item in inventory["blocked_keys"]})),
        }
        if not inventory["exact_replay_eligible"]:
            records.append(record)
            continue
        if not _true(row["roster_complete"]):
            record.update({"outcome_status": "BLOCKED_ROSTER_INCOMPLETE", "outcome_blocker_codes": "BLOCKED_ROSTER_INCOMPLETE"})
            records.append(record)
            continue
        if pd.isna(row.get("team_has_game")) or pd.isna(row.get("game_complete")):
            record.update({"outcome_status": "BLOCKED_SCHEDULE_INCOMPLETE", "outcome_blocker_codes": "BLOCKED_SCHEDULE_INCOMPLETE"})
            records.append(record)
            continue
        if not _true(row["game_complete"]):
            record.update({"outcome_status": "BLOCKED_GAME_INCOMPLETE", "outcome_blocker_codes": "BLOCKED_GAME_INCOMPLETE"})
            records.append(record)
            continue
        if not _true(row["team_has_game"]):
            record.update({"fantasy_points_exact": 0.0, "outcome_complete": True, "outcome_status": "CONFIRMED_BYE", "outcome_blocker_codes": ""})
            records.append(record)
            continue
        has_stat_row = any(pd.notna(row.get(column)) for column in stat_value_columns)
        if not has_stat_row and not player_stats_complete:
            record.update({"outcome_status": "BLOCKED_PLAYER_STATS_INCOMPLETE", "outcome_blocker_codes": "BLOCKED_PLAYER_STATS_INCOMPLETE"})
            records.append(record)
            continue
        score_row = row.copy()
        for rule in inventory["relevant_nonzero_rules"]:
            for column in rule["required_columns"]:
                value = score_row.get(column)
                if pd.isna(value):
                    if player_stats_complete:
                        score_row[column] = 0.0
                    else:
                        record.update({"outcome_status": "BLOCKED_PLAYER_STATS_INCOMPLETE", "outcome_blocker_codes": "BLOCKED_PLAYER_STATS_INCOMPLETE"})
                        break
            if record["outcome_status"] == "BLOCKED_PLAYER_STATS_INCOMPLETE":
                break
        if record["outcome_status"] == "BLOCKED_PLAYER_STATS_INCOMPLETE":
            records.append(record)
            continue
        record.update({
            "fantasy_points_exact": _score_exact_row(score_row, scoring, position),
            "outcome_complete": True,
            "outcome_status": "COMPLETE_EXACT",
            "outcome_blocker_codes": "",
        })
        records.append(record)
    return pd.DataFrame(records)

#!/usr/bin/env python3
"""Fail-closed Waiver-v2 target and eligibility contract.

This module is intentionally independent from legacy M5.  It builds a labelled
future *scoring-week* horizon only from a dense, already exact-scored outcome
ledger, then exposes the four separate waiver eligibility layers defined by
``config/offensive-waiver-eligibility-design.json``.

It does not score raw NFL events, train a model, alter an M5 artifact, or grant
live current-snapshot eligibility.  Those later steps must supply the exact
scoring and validation evidence consumed here.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

import pandas as pd


WAIVER_V2_LABEL_BUILDER_VERSION = "waiver-v2-same-season-scoring-weeks-v1"
WAIVER_V2_REQUIRED_HORIZON_WEEKS = 3
FORECAST_ONLY_FORMATS = frozenset({
    "DYNASTY",
    "REDRAFT_BESTBALL",
    "DYNASTY_BESTBALL",
    "CHOPPED",
    "CHOPPED_BESTBALL",
})


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
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


def _required_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"waiver-v2 outcome ledger missing required columns: {', '.join(missing)}")


def build_same_season_horizon_targets(
    frame: pd.DataFrame,
    *,
    value_column: str = "fantasy_points_exact",
    outcome_complete_column: str = "outcome_complete",
    player_column: str = "canonical_player_id",
    season_column: str = "season",
    week_column: str = "week",
    horizon_weeks: int = WAIVER_V2_REQUIRED_HORIZON_WEEKS,
) -> pd.DataFrame:
    """Add full, same-season future scoring-week targets to a dense ledger.

    ``frame`` must already contain one row for every player/scoring-week that
    can be labelled.  Byes and confirmed no-stat games are explicit rows with
    an exact score of zero and ``outcome_complete=true``.  A missing row or an
    incomplete future outcome leaves the target null.  The helper deliberately
    never infers that missing means zero and never follows a player into the
    next season.
    """
    if int(horizon_weeks) < 1:
        raise ValueError("horizon_weeks must be at least one")
    horizon_weeks = int(horizon_weeks)
    required = [player_column, season_column, week_column, value_column, outcome_complete_column]
    _required_columns(frame, required)

    d = frame.copy()
    key_columns = [player_column, season_column, week_column]
    if d[key_columns].isna().any().any():
        raise ValueError("waiver-v2 outcome ledger has null player, season, or week identity")
    if d.duplicated(key_columns).any():
        raise ValueError("waiver-v2 outcome ledger must have one row per player, season, and scoring week")

    d[season_column] = pd.to_numeric(d[season_column], errors="raise").astype(int)
    d[week_column] = pd.to_numeric(d[week_column], errors="raise").astype(int)
    if (d[week_column] < 1).any():
        raise ValueError("waiver-v2 scoring weeks must be positive integers")

    result_total = "fp_next%d_weeks_total_exact" % horizon_weeks
    result_mean = "fp_next%d_weeks_exact" % horizon_weeks
    result_full = "fp_next%d_weeks_full_horizon" % horizon_weeks
    result_count = "fp_next%d_weeks_complete_count" % horizon_weeks
    result_version = "fp_next%d_weeks_label_builder_version" % horizon_weeks
    target_week_columns = ["fp_next%d_weeks_target_week_%d" % (horizon_weeks, offset) for offset in range(1, horizon_weeks + 1)]

    d[result_total] = float("nan")
    d[result_mean] = float("nan")
    d[result_full] = False
    d[result_count] = 0
    d[result_version] = WAIVER_V2_LABEL_BUILDER_VERSION
    for column in target_week_columns:
        d[column] = pd.Series([pd.NA] * len(d), dtype="Int64")

    lookup = {
        (str(row[player_column]), int(row[season_column]), int(row[week_column])): row
        for _, row in d.iterrows()
    }
    for index, row in d.iterrows():
        player = str(row[player_column])
        season = int(row[season_column])
        decision_week = int(row[week_column])
        values: list[float] = []
        complete_count = 0
        for offset, target_column in enumerate(target_week_columns, start=1):
            target_week = decision_week + offset
            d.at[index, target_column] = target_week
            target = lookup.get((player, season, target_week))
            if target is None:
                continue
            if not _true(target[outcome_complete_column]) or not _finite(target[value_column]):
                continue
            values.append(float(target[value_column]))
            complete_count += 1
        d.at[index, result_count] = complete_count
        if complete_count != horizon_weeks:
            continue
        d.at[index, result_total] = float(sum(values))
        d.at[index, result_mean] = float(sum(values) / horizon_weeks)
        d.at[index, result_full] = True
    return d


def waiver_v2_eligibility(
    *,
    league_format: str,
    exact_scoring: bool,
    model_validated: bool,
    lineage_match: bool,
    horizon_weeks: int | None,
    full_horizon: bool,
    history_games: int | None,
    min_history_games: int = 2,
    required_features_present: bool,
    feature_coverage: float | None,
    min_feature_coverage: float | None,
    forecast: float | None,
    ranking_validated: bool,
    candidate_set_valid: bool,
    format_decision_validated: bool,
    legal_replacement_available: bool,
    transaction_state_valid: bool,
) -> dict[str, Any]:
    """Return the four fail-closed Waiver-v2 eligibility layers.

    The caller supplies evidence booleans from their authoritative owners.
    Missing, malformed, or unvalidated evidence is deliberately treated as a
    blocker.  A short-horizon forecast is allowed to be visible in every known
    format, while recommendation eligibility is initially Redraft-only.
    """
    fmt = str(league_format or "").upper().strip() or "UNKNOWN"
    blockers: list[str] = []
    if not exact_scoring:
        blockers.append("BLOCKED_UNSUPPORTED_EXACT_SCORING")
    if not model_validated:
        blockers.append("BLOCKED_MODEL_NOT_VALIDATED")
    if not lineage_match:
        blockers.append("BLOCKED_IDENTITY_OR_LINEAGE")
    if horizon_weeks != WAIVER_V2_REQUIRED_HORIZON_WEEKS or not full_horizon:
        blockers.append("BLOCKED_INCOMPLETE_HORIZON")
    if history_games is None or int(history_games) < int(min_history_games):
        blockers.append("BLOCKED_HISTORY")
    if not required_features_present:
        blockers.append("BLOCKED_REQUIRED_FEATURES")
    if min_feature_coverage is None or feature_coverage is None or not _finite(feature_coverage) or float(feature_coverage) < float(min_feature_coverage):
        blockers.append("BLOCKED_FEATURE_COVERAGE")
    if not _finite(forecast):
        blockers.append("BLOCKED_FORECAST_NONFINITE")

    forecast_eligible = not blockers
    ranking_blockers: list[str] = []
    if forecast_eligible and not ranking_validated:
        ranking_blockers.append("BLOCKED_RANKING_NOT_VALIDATED")
    if forecast_eligible and not candidate_set_valid:
        ranking_blockers.append("BLOCKED_CANDIDATE_SET")
    ranking_eligible = forecast_eligible and not ranking_blockers

    recommendation_blockers: list[str] = []
    if ranking_eligible and fmt in FORECAST_ONLY_FORMATS:
        recommendation_blockers.append("BLOCKED_FORMAT_DECISION_EVIDENCE")
    elif ranking_eligible and fmt != "REDRAFT":
        recommendation_blockers.append("BLOCKED_UNKNOWN_FORMAT")
    if ranking_eligible and not format_decision_validated:
        recommendation_blockers.append("BLOCKED_FORMAT_DECISION_EVIDENCE")
    if ranking_eligible and not legal_replacement_available:
        recommendation_blockers.append("BLOCKED_DROP_VALUE_UNAVAILABLE")
    recommendation_eligible = ranking_eligible and not recommendation_blockers

    transaction_blockers: list[str] = []
    if recommendation_eligible and not transaction_state_valid:
        transaction_blockers.append("BLOCKED_TRANSACTION_STATE")
    transaction_eligible = recommendation_eligible and not transaction_blockers

    all_blockers = blockers + ranking_blockers + recommendation_blockers + transaction_blockers
    if not forecast_eligible:
        status = blockers[0]
    elif fmt in FORECAST_ONLY_FORMATS:
        status = "FORECAST_ONLY_FORMAT_UTILITY_BLOCKED"
    elif not ranking_eligible:
        status = "RESEARCH_WATCHLIST"
    elif not recommendation_eligible:
        status = "RESEARCH_WATCHLIST"
    else:
        status = "RECOMMENDATION_READY"

    return {
        "waiver_forecast_status": status,
        "waiver_forecast_eligible": forecast_eligible,
        "waiver_ranking_eligible": ranking_eligible,
        "waiver_recommendation_eligible": recommendation_eligible,
        "waiver_transaction_eligible": transaction_eligible,
        # The legacy planner only understands this field.  Keep it tied to the
        # stricter recommendation layer until that consumer is migrated.
        "waiver_activation_eligible": recommendation_eligible,
        "waiver_next3_projection": float(forecast) if forecast_eligible else None,
        "waiver_horizon_weeks": WAIVER_V2_REQUIRED_HORIZON_WEEKS if forecast_eligible else None,
        "waiver_blocker_codes": all_blockers,
    }

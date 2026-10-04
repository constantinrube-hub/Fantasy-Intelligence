#!/usr/bin/env python3
"""Deterministic integrity checks for the isolated Waiver-v2 contract."""
from __future__ import annotations

import math

import pandas as pd

from waiver_v2_contract import (
    WAIVER_V2_LABEL_BUILDER_VERSION,
    build_same_season_horizon_targets,
    waiver_v2_eligibility,
)


def ledger(rows):
    return pd.DataFrame(rows)


# The target uses future scoring *weeks*, not future player appearance rows.
# A confirmed bye/no-stat week has an explicit exact zero and is retained.
source = ledger([
    {"canonical_player_id": "p1", "season": 2025, "week": 15, "fantasy_points_exact": 5.0, "outcome_complete": True},
    {"canonical_player_id": "p1", "season": 2025, "week": 16, "fantasy_points_exact": 10.0, "outcome_complete": True},
    {"canonical_player_id": "p1", "season": 2025, "week": 17, "fantasy_points_exact": 0.0, "outcome_complete": True},
    {"canonical_player_id": "p1", "season": 2025, "week": 18, "fantasy_points_exact": 20.0, "outcome_complete": True},
    # This row must not complete the 2025 Week-16 horizon.
    {"canonical_player_id": "p1", "season": 2026, "week": 1, "fantasy_points_exact": 100.0, "outcome_complete": True},
])
out = build_same_season_horizon_targets(source)
w15 = out[(out.season == 2025) & (out.week == 15)].iloc[0]
w16 = out[(out.season == 2025) & (out.week == 16)].iloc[0]
assert bool(w15.fp_next3_weeks_full_horizon) is True
assert math.isclose(float(w15.fp_next3_weeks_total_exact), 30.0)
assert math.isclose(float(w15.fp_next3_weeks_exact), 10.0)
assert [int(w15.fp_next3_weeks_target_week_1), int(w15.fp_next3_weeks_target_week_2), int(w15.fp_next3_weeks_target_week_3)] == [16, 17, 18]
assert w15.fp_next3_weeks_label_builder_version == WAIVER_V2_LABEL_BUILDER_VERSION
assert bool(w16.fp_next3_weeks_full_horizon) is False
assert int(w16.fp_next3_weeks_complete_count) == 2
assert pd.isna(w16.fp_next3_weeks_exact), "Week 18 must not shift into next season"

# Missing or incomplete source data remains unknown rather than becoming zero.
incomplete = source[source.season.eq(2025)].copy()
incomplete["outcome_complete"] = incomplete["outcome_complete"].astype(object)
incomplete.loc[incomplete.week.eq(17), "outcome_complete"] = pd.NA
incomplete.loc[incomplete.week.eq(17), "fantasy_points_exact"] = float("nan")
incomplete_out = build_same_season_horizon_targets(incomplete)
assert not bool(incomplete_out.loc[incomplete_out.week.eq(15), "fp_next3_weeks_full_horizon"].iloc[0])
assert pd.isna(incomplete_out.loc[incomplete_out.week.eq(15), "fp_next3_weeks_exact"].iloc[0])

missing_week = source[(source.season.ne(2025)) | (source.week.ne(17))].copy()
missing_out = build_same_season_horizon_targets(missing_week)
assert not bool(missing_out.loc[(missing_out.season.eq(2025)) & (missing_out.week.eq(15)), "fp_next3_weeks_full_horizon"].iloc[0])

try:
    build_same_season_horizon_targets(pd.concat([source, source.iloc[[0]]], ignore_index=True))
    raise AssertionError("duplicate player/season/week ledger rows must fail")
except ValueError as error:
    assert "one row per player" in str(error)


def ready_kwargs(**overrides):
    base = {
        "league_format": "REDRAFT",
        "exact_scoring": True,
        "model_validated": True,
        "lineage_match": True,
        "horizon_weeks": 3,
        "full_horizon": True,
        "history_games": 3,
        "min_history_games": 2,
        "required_features_present": True,
        "feature_coverage": 0.8,
        "min_feature_coverage": 0.6,
        "forecast": 14.25,
        "ranking_validated": True,
        "candidate_set_valid": True,
        "format_decision_validated": True,
        "legal_replacement_available": True,
        "transaction_state_valid": True,
    }
    return {**base, **overrides}


# All layers can be ready only for a governed Redraft decision.  The legacy
# activation flag remains the recommendation layer, never the forecast layer.
redraft = waiver_v2_eligibility(**ready_kwargs())
assert redraft["waiver_forecast_eligible"]
assert redraft["waiver_ranking_eligible"]
assert redraft["waiver_recommendation_eligible"]
assert redraft["waiver_transaction_eligible"]
assert redraft["waiver_activation_eligible"]
assert math.isclose(redraft["waiver_next3_projection"], 14.25)
assert redraft["waiver_blocker_codes"] == []

# A valid short-horizon forecast is visible in every format, but it is not a
# Dynasty/Best-Ball/Chopped acquisition recommendation.
dynasty = waiver_v2_eligibility(**ready_kwargs(league_format="DYNASTY"))
assert dynasty["waiver_forecast_eligible"]
assert dynasty["waiver_ranking_eligible"]
assert not dynasty["waiver_recommendation_eligible"]
assert not dynasty["waiver_activation_eligible"]
assert dynasty["waiver_forecast_status"] == "FORECAST_ONLY_FORMAT_UTILITY_BLOCKED"
assert dynasty["waiver_next3_projection"] == 14.25
assert "BLOCKED_FORMAT_DECISION_EVIDENCE" in dynasty["waiver_blocker_codes"]

# Forecast readiness alone cannot leak into the legacy Window 1D planner.
watchlist = waiver_v2_eligibility(**ready_kwargs(format_decision_validated=False))
assert watchlist["waiver_forecast_eligible"]
assert watchlist["waiver_ranking_eligible"]
assert not watchlist["waiver_recommendation_eligible"]
assert not watchlist["waiver_activation_eligible"]
assert watchlist["waiver_forecast_status"] == "RESEARCH_WATCHLIST"

# Every upstream failure fails closed and removes the forecast value.
scoring_blocked = waiver_v2_eligibility(**ready_kwargs(exact_scoring=False))
assert not scoring_blocked["waiver_forecast_eligible"]
assert scoring_blocked["waiver_next3_projection"] is None
assert scoring_blocked["waiver_forecast_status"] == "BLOCKED_UNSUPPORTED_EXACT_SCORING"

partial_horizon = waiver_v2_eligibility(**ready_kwargs(horizon_weeks=2, full_horizon=False))
assert not partial_horizon["waiver_forecast_eligible"]
assert "BLOCKED_INCOMPLETE_HORIZON" in partial_horizon["waiver_blocker_codes"]

feature_blocked = waiver_v2_eligibility(**ready_kwargs(required_features_present=False, feature_coverage=0.5))
assert not feature_blocked["waiver_forecast_eligible"]
assert "BLOCKED_REQUIRED_FEATURES" in feature_blocked["waiver_blocker_codes"]
assert "BLOCKED_FEATURE_COVERAGE" in feature_blocked["waiver_blocker_codes"]

print("OK waiver-v2 same-season target and layered eligibility contract")

#!/usr/bin/env python3
"""Regression checks for the fail-closed Waiver-v2 offensive outcome ledger."""
from __future__ import annotations

import math

import pandas as pd

from waiver_v2_outcomes import build_dense_offensive_outcome_ledger, build_offensive_scoring_inventory


core_scoring = {"pass_yd": 0.04, "pass_td": 4, "pass_int": -1, "rush_yd": 0.1, "rec": 1}
columns = {"passing_yards", "passing_tds", "passing_interceptions", "rushing_yards", "receptions"}
qb = build_offensive_scoring_inventory(core_scoring, position="QB", available_columns=columns)
assert qb["exact_replay_eligible"]
assert qb["supported_keys"] == ["pass_int", "pass_td", "pass_yd", "rush_yd"]
assert qb["ignored_irrelevant_keys"] == ["rec"]

# A known but not-yet-reconciled event rule cannot be silently approximated.
blocked = build_offensive_scoring_inventory({"pass_yd": 0.04, "pass_int_td": -2}, position="QB", available_columns=columns)
assert not blocked["exact_replay_eligible"]
assert blocked["blocked_keys"][0]["key"] == "pass_int_td"
assert blocked["blocked_keys"][0]["support_status"] == "BLOCKED_SOURCE_INCOMPLETE"

# E2 event values require both the dedicated field and a green event-source
# receipt. The ordinary interception penalty still stacks independently.
event_columns = columns | {"event_fumbles", "event_fumbles_lost", "event_pass_int_td", "event_bonus_rush_td_qb", "sacks"}
event_support = {key: {"support_status": "EXACT_EVENT_READY", "reason": "fixture"} for key in ("fum", "fum_lost", "pass_int_td", "bonus_rush_td_qb")}
e2_qb = build_offensive_scoring_inventory({"pass_int": -2, "pass_int_td": -2, "pass_sack": -1, "bonus_rush_td_qb": -2}, position="QB", available_columns=event_columns, event_rule_support=event_support)
assert e2_qb["exact_replay_eligible"] and set(e2_qb["supported_keys"]) == {"pass_int", "pass_int_td", "pass_sack", "bonus_rush_td_qb"}
e2_rb = build_offensive_scoring_inventory({"bonus_rush_td_qb": -2}, position="RB", available_columns=event_columns, event_rule_support=event_support)
assert e2_rb["exact_replay_eligible"] and e2_rb["ignored_irrelevant_keys"] == ["bonus_rush_td_qb"]

# E4 return-yard rules require their own event columns and green independent
# PBP/player-week reconciliation.  A blocked field-goal-return family cannot
# be made exact merely because kickoff/punt values are available.
e4_columns = event_columns | {"event_kick_return_yards", "event_punt_return_yards", "event_field_goal_return_yards"}
e4_support = {**event_support, "kr_yd": {"support_status": "EXACT_EVENT_READY", "reason": "fixture"},
              "pr_yd": {"support_status": "EXACT_EVENT_READY", "reason": "fixture"},
              "fg_ret_yd": {"support_status": "BLOCKED_SOURCE_INCOMPLETE", "reason": "no direct role"}}
e4_wr = build_offensive_scoring_inventory({"kr_yd": 0.01, "pr_yd": 0.02}, position="WR", available_columns=e4_columns, event_rule_support=e4_support)
assert e4_wr["exact_replay_eligible"] and set(e4_wr["supported_keys"]) == {"kr_yd", "pr_yd"}
e4_fg = build_offensive_scoring_inventory({"fg_ret_yd": 0.01}, position="WR", available_columns=e4_columns, event_rule_support=e4_support)
assert not e4_fg["exact_replay_eligible"] and e4_fg["blocked_keys"][0]["support_status"] == "BLOCKED_SOURCE_INCOMPLETE"

# E5's long-play counters are individual event counts, so 50-yard touchdown
# rules can stack with their matching 40-yard rules and never use weekly yards
# as a proxy for the number of qualifying plays.
e5_columns = e4_columns | {"event_pass_completions_40", "event_pass_tds_40", "event_pass_tds_50"}
e5_support = {**e4_support, **{key: {"support_status": "EXACT_EVENT_READY", "reason": "fixture"} for key in ("pass_cmp_40p", "pass_td_40p", "pass_td_50p")}}
e5_qb = build_offensive_scoring_inventory({"pass_cmp_40p": 1, "pass_td_40p": 2, "pass_td_50p": 3}, position="QB", available_columns=e5_columns, event_rule_support=e5_support)
assert e5_qb["exact_replay_eligible"] and set(e5_qb["supported_keys"]) == {"pass_cmp_40p", "pass_td_40p", "pass_td_50p"}

# Unknown keys are relevant by default and also prevent an exact replay.
unknown = build_offensive_scoring_inventory({"fictional_bonus": 3}, position="RB", available_columns=columns)
assert not unknown["exact_replay_eligible"]
assert unknown["unknown_keys"] == ["fictional_bonus"]

roster = pd.DataFrame([
    {"canonical_player_id": "qb", "season": 2026, "week": 1, "team": "A", "position_model": "QB", "roster_complete": True},
    {"canonical_player_id": "te", "season": 2026, "week": 1, "team": "A", "position_model": "TE", "roster_complete": True},
    {"canonical_player_id": "rb", "season": 2026, "week": 1, "team": "B", "position_model": "RB", "roster_complete": True},
    {"canonical_player_id": "wr", "season": 2026, "week": 1, "team": "C", "position_model": "WR", "roster_complete": True},
])
schedule = pd.DataFrame([
    {"season": 2026, "week": 1, "team": "A", "team_has_game": True, "game_complete": True},
    {"season": 2026, "week": 1, "team": "B", "team_has_game": False, "game_complete": True},
    {"season": 2026, "week": 1, "team": "C", "team_has_game": True, "game_complete": True},
])
stats = pd.DataFrame([
    {"canonical_player_id": "qb", "season": 2026, "week": 1, "passing_yards": 250, "passing_tds": 2, "passing_interceptions": 1, "rushing_yards": 10, "receptions": 0},
    {"canonical_player_id": "wr", "season": 2026, "week": 1, "passing_yards": 0, "passing_tds": 0, "passing_interceptions": 0, "rushing_yards": 0, "receptions": 0},
])
ledger = build_dense_offensive_outcome_ledger(stats, roster, schedule, core_scoring, scoring_signature="ppr-test", player_stats_complete=True)
qb_row = ledger[ledger.canonical_player_id.eq("qb")].iloc[0]
te_row = ledger[ledger.canonical_player_id.eq("te")].iloc[0]
rb_row = ledger[ledger.canonical_player_id.eq("rb")].iloc[0]
wr_row = ledger[ledger.canonical_player_id.eq("wr")].iloc[0]
assert qb_row.outcome_status == "COMPLETE_EXACT" and math.isclose(float(qb_row.fantasy_points_exact), 18.0)
assert te_row.outcome_status == "COMPLETE_EXACT" and float(te_row.fantasy_points_exact) == 0.0
assert rb_row.outcome_status == "CONFIRMED_BYE" and float(rb_row.fantasy_points_exact) == 0.0
assert wr_row.outcome_status == "COMPLETE_EXACT" and float(wr_row.fantasy_points_exact) == 0.0
assert ledger.outcome_complete.all()

# A missing player row can be zero only after the caller asserts a complete
# weekly player-stat source; otherwise the ledger must retain uncertainty.
incomplete = build_dense_offensive_outcome_ledger(stats.iloc[[0]], roster, schedule, core_scoring, scoring_signature="ppr-test", player_stats_complete=False)
incomplete_wr = incomplete[incomplete.canonical_player_id.eq("wr")].iloc[0]
assert incomplete_wr.outcome_status == "BLOCKED_PLAYER_STATS_INCOMPLETE"
assert not bool(incomplete_wr.outcome_complete) and pd.isna(incomplete_wr.fantasy_points_exact)

# Unsupported league scoring preserves all player-week identities but exposes
# no partial total that M5 could accidentally consume.
unsupported_ledger = build_dense_offensive_outcome_ledger(stats, roster, schedule, {"pass_yd": 0.04, "pass_int_td": -2}, scoring_signature="unsupported", player_stats_complete=True)
unsupported_qb = unsupported_ledger[unsupported_ledger.canonical_player_id.eq("qb")].iloc[0]
assert unsupported_qb.outcome_status == "BLOCKED_UNSUPPORTED_EXACT_SCORING"
assert pd.isna(unsupported_qb.fantasy_points_exact)

try:
    build_dense_offensive_outcome_ledger(pd.concat([stats, stats.iloc[[0]]]), roster, schedule, core_scoring, scoring_signature="ppr-test", player_stats_complete=True)
    raise AssertionError("duplicate player-stat rows must fail")
except ValueError as error:
    assert "one row per player" in str(error)

print("OK waiver-v2 offensive scoring inventory and dense outcome ledger")

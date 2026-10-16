#!/usr/bin/env python3
"""End-to-end provenance integrity for the offline Waiver-v2 ledger builder."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from build_waiver_v2_outcome_ledger import build, scoring_signature


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    player_stats = root / "player-stats.csv"
    weekly_roster = root / "weekly-roster.csv"
    team_schedule = root / "team-schedule.csv"
    scoring = root / "scoring.json"
    ledger_path = root / "outcomes.csv.gz"
    report_path = root / "outcomes.json"
    pd.DataFrame([
        {"canonical_player_id": "qb", "season": 2026, "week": 1, "passing_yards": 275, "passing_tds": 2, "passing_interceptions": 1, "rushing_yards": 0, "receptions": 0},
        {"canonical_player_id": "wr", "season": 2026, "week": 1, "passing_yards": 0, "passing_tds": 0, "passing_interceptions": 0, "rushing_yards": 0, "receptions": 5},
    ]).to_csv(player_stats, index=False)
    pd.DataFrame([
        {"canonical_player_id": "qb", "season": 2026, "week": 1, "team": "A", "position_model": "QB", "roster_complete": True},
        {"canonical_player_id": "wr", "season": 2026, "week": 1, "team": "B", "position_model": "WR", "roster_complete": True},
        {"canonical_player_id": "rb", "season": 2026, "week": 1, "team": "C", "position_model": "RB", "roster_complete": True},
    ]).to_csv(weekly_roster, index=False)
    pd.DataFrame([
        {"season": 2026, "week": 1, "team": "A", "team_has_game": True, "game_complete": True},
        {"season": 2026, "week": 1, "team": "B", "team_has_game": True, "game_complete": True},
        {"season": 2026, "week": 1, "team": "C", "team_has_game": True, "game_complete": True},
    ]).to_csv(team_schedule, index=False)
    settings = {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1, "rec": 1}
    scoring.write_text(json.dumps({"scoring_settings": settings}), encoding="utf-8")
    report = build(
        player_stats_path=player_stats,
        weekly_roster_path=weekly_roster,
        team_schedule_path=team_schedule,
        scoring_path=scoring,
        output_path=ledger_path,
        report_path=report_path,
        player_stats_complete=True,
    )
    persisted = pd.read_csv(ledger_path)
    receipt = json.loads(report_path.read_text(encoding="utf-8"))
    assert report == receipt
    assert receipt["diagnostic_only"] is True and receipt["activation_eligible"] is False
    assert receipt["ledger"]["complete_exact_rows"] == 3
    assert receipt["ledger"]["status_counts"] == {"COMPLETE_EXACT": 3}
    assert receipt["scoring_signature"] == scoring_signature(settings)
    assert len(receipt["scoring_signature"]) == 16
    assert receipt["inputs"]["player_stats"]["sha256"]
    assert persisted["scoring_signature"].nunique() == 1
    assert persisted["outcome_complete"].all()

    # The RB has no stat row.  Withdrawing the completeness assertion must
    # preserve that uncertainty in both the ledger and its report.
    report = build(
        player_stats_path=player_stats,
        weekly_roster_path=weekly_roster,
        team_schedule_path=team_schedule,
        scoring_path=scoring,
        output_path=ledger_path,
        report_path=report_path,
        player_stats_complete=False,
    )
    persisted = pd.read_csv(ledger_path)
    assert report["ledger"]["complete_exact_rows"] == 2
    rb = persisted[persisted.canonical_player_id.eq("rb")].iloc[0]
    assert not bool(rb.outcome_complete)
    assert rb.outcome_status == "BLOCKED_PLAYER_STATS_INCOMPLETE"

    # E2 values score only with the companion event receipt. This verifies a
    # pick-six stacks with the ordinary interception and that a QB-only
    # rushing-TD adjustment does not become an RB/WR/TE rule.
    event_weekly = root / "event-weekly.csv"
    pd.DataFrame([
        {"canonical_player_id": "qb", "season": 2026, "week": 1, "event_fumbles": 1, "event_fumbles_lost": 1,
         "event_pass_int_td": 1, "event_bonus_rush_td_qb": 1},
    ]).to_csv(event_weekly, index=False)
    pd.DataFrame([
        {"canonical_player_id": "qb", "season": 2026, "week": 1, "passing_yards": 0, "passing_tds": 0, "passing_interceptions": 1,
         "rushing_yards": 0, "rushing_tds": 1, "receptions": 0, "sacks": 1},
        {"canonical_player_id": "wr", "season": 2026, "week": 1, "passing_yards": 0, "passing_tds": 0, "passing_interceptions": 0,
         "rushing_yards": 0, "rushing_tds": 0, "receptions": 0, "sacks": 0},
    ]).to_csv(player_stats, index=False)
    e2_settings = {"pass_int": -2, "pass_int_td": -2, "pass_sack": -1, "rush_td": 6, "bonus_rush_td_qb": -2, "fum": -1, "fum_lost": -2}
    scoring.write_text(json.dumps({"scoring_settings": e2_settings}), encoding="utf-8")
    support = {key: {"support_status": "EXACT_EVENT_READY", "reason": "fixture"} for key in ("fum", "fum_lost", "pass_int_td", "bonus_rush_td_qb")}
    report = build(
        player_stats_path=player_stats, weekly_roster_path=weekly_roster, team_schedule_path=team_schedule,
        scoring_path=scoring, output_path=ledger_path, report_path=report_path, player_stats_complete=True,
        event_weekly_stats_path=event_weekly, event_rule_support=support,
    )
    persisted = pd.read_csv(ledger_path)
    qb = persisted[persisted.canonical_player_id.eq("qb")].iloc[0]
    assert qb.outcome_status == "COMPLETE_EXACT" and float(qb.fantasy_points_exact) == -4.0
    assert report["inputs"]["event_weekly_stats"]["sha256"]

print("OK waiver-v2 offline outcome-ledger builder provenance")

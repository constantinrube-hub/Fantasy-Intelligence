#!/usr/bin/env python3
"""End-to-end provenance integrity for the offline Waiver-v2 ledger builder."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from build_waiver_v2_outcome_ledger import build


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
    scoring.write_text(json.dumps({"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1, "rec": 1}), encoding="utf-8")
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

print("OK waiver-v2 offline outcome-ledger builder provenance")

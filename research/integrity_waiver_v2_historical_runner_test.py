#!/usr/bin/env python3
"""Fixture checks for the persisted historical Waiver-v2 source snapshot."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from run_waiver_v2_historical_ledger import write_source_snapshot


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    players = pd.DataFrame([{"gsis_id": "p1", "display_name": "Player One"}])
    stats = [pd.DataFrame([{"season": 2025, "week": 1, "player_id": "p1"}])]
    rosters = [pd.DataFrame([{"season": 2025, "week": 1, "gsis_id": "p1"}])]
    games = pd.DataFrame([{"season": 2025, "week": 1, "home_team": "AAA", "away_team": "BBB"}])
    identity = pd.DataFrame([{"gsis_id": "p1", "canonical_player_id": "p1"}])
    snapshot = write_source_snapshot(players=players, player_stats_frames=stats, weekly_roster_frames=rosters, games=games, identity=identity, raw_dir=root / "raw")
    assert set(snapshot) == {"players", "player_stats", "weekly_roster", "games", "identity"}
    for row in snapshot.values():
        assert Path(row["path"]).is_file()
        assert len(row["sha256"]) == 64
    assert snapshot["player_stats"]["rows"] == 1
    assert len(pd.read_csv(snapshot["weekly_roster"]["path"])) == 1

print("OK waiver-v2 historical runner preserves raw source snapshot")

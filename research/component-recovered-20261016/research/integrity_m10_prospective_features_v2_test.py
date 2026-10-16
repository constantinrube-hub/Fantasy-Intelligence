#!/usr/bin/env python3
"""No-network edge-case proof for R8A's shared time-safe feature owner."""
from __future__ import annotations

import math

import pandas as pd

from m10_prospective_features import FEATURES, build_features, feature_record


def row(season: int, week: int, player: str, team: str, volume: float, *, yards: float = 20.0) -> dict:
    return {"season": season, "week": week, "canonical_player_id": player, "position_model": "RB", "team": team,
            "attempts": 0.0, "carries": volume, "targets": 0.0, "rushing_yards": yards, "receiving_yards": 0.0, "passing_yards": 0.0}


def main() -> int:
    history = [
        row(2025, 1, "transfer", "AAA", 10.0), row(2025, 2, "transfer", "AAA", 10.0),
        row(2025, 3, "transfer", "AAA", 10.0, yards=-7.0), row(2025, 4, "transfer", "AAA", 10.0),
        row(2025, 3, "bbb-one", "BBB", 50.0), row(2025, 4, "bbb-two", "BBB", 70.0),
        row(2025, 1, "new", "CCC", 5.0),
    ]
    completed = pd.DataFrame(history)
    target = pd.DataFrame([row(2026, 1, "transfer", "BBB", float("nan")), row(2026, 1, "new", "CCC", float("nan"))])
    for name in ("attempts", "carries", "targets", "rushing_yards", "receiving_yards", "passing_yards"):
        target[name] = float("nan")
    prospective = build_features(completed, target)
    transfer = prospective[(prospective["canonical_player_id"] == "transfer") & ~prospective["_completed"]].iloc[0]
    newcomer = prospective[(prospective["canonical_player_id"] == "new") & ~prospective["_completed"]].iloc[0]
    assert transfer["team_prior4_budget"] == 60.0, transfer["team_prior4_budget"]
    assert transfer["team_prior4_budget"] != 10.0
    assert transfer["player_prior4_volume"] == 10.0
    assert math.isnan(newcomer["player_prior4_volume"]) and feature_record(newcomer)["player_prior4_volume"] is None
    historic = build_features(completed)
    historic_row = historic[(historic["canonical_player_id"] == "transfer") & (historic["week"] == 4)].iloc[0]
    replay_history = completed[completed["week"] < 4]
    replay_target = completed[(completed["canonical_player_id"] == "transfer") & (completed["week"] == 4)].copy()
    for name in ("attempts", "carries", "targets", "rushing_yards", "receiving_yards", "passing_yards"):
        replay_target[name] = float("nan")
    replay = build_features(replay_history, replay_target)
    prospective_row = replay[(replay["canonical_player_id"] == "transfer") & ~replay["_completed"]].iloc[0]
    for name in FEATURES:
        assert historic_row[name] == prospective_row[name], (name, historic_row[name], prospective_row[name])
    assert historic[(historic["canonical_player_id"] == "transfer") & (historic["week"] == 3)].iloc[0]["rushing_yards"] == -7.0
    try:
        build_features(completed, pd.DataFrame([row(2026, 1, "bad", "AAA", 4.0)]))
    except ValueError:
        pass
    else:
        raise AssertionError("target-week outcomes must be rejected")
    print("PASS R8A shared features preserve parity, target-week team budget, nulls, and negative yardage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

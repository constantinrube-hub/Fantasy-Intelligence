#!/usr/bin/env python3
"""Regression coverage for the locked M10 raw-target domains."""
from __future__ import annotations

import numpy as np
import pandas as pd

from build_m10_prospective_historical_input import make_rows
from m10_prospective_season_lock import loss_for, matrix


def row(week: int, rushing_yards: float | None, carries: float) -> dict:
    return {
        "season": 2025, "week": week, "team": "TST", "position_model": "QB",
        "canonical_player_id": "test-qb", "fantasy_points": 10.0,
        "attempts": 25.0, "completions": 17.0, "passing_yards": 200.0,
        "passing_tds": 1.0, "interceptions": 0.0, "carries": carries,
        "rushing_yards": rushing_yards, "rushing_tds": 0.0,
        "targets": 0.0, "receptions": 0.0, "receiving_yards": 0.0,
        "receiving_tds": 0.0,
    }


def main() -> int:
    rows = make_rows(pd.DataFrame([row(1, -3.0, 0.0), row(2, 5.0, 2.0), row(3, None, 3.0)]))
    assert [item["targets"]["rushing_yards"] for item in rows] == [-3.0, 5.0, None]
    x, yardage = matrix(rows, ["player_prior4_volume"], "rushing_yards", minimum=2)
    assert x.shape == (2, 1) and yardage.tolist() == [-3.0, 5.0]
    assert loss_for("rushing_yards", yardage) == "squared_error"
    _, carries = matrix(rows, ["player_prior4_volume"], "carries", minimum=3)
    assert carries.tolist() == [0.0, 2.0, 3.0] and loss_for("carries", carries) == "poisson"
    invalid = [dict(item, targets=dict(item["targets"])) for item in rows]
    invalid[0]["targets"]["carries"] = -1.0
    try:
        matrix(invalid, ["player_prior4_volume"], "carries", minimum=3)
    except AssertionError as error:
        assert "negative count label" in str(error)
    else:
        raise AssertionError("negative count labels must fail")
    print("PASS M10 target domains preserve negative yardage, null labels, and count safeguards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

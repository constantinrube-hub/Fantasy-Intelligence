"""c3_grade.py - registered evaluation for the M3k fringe guard (readiness item c3).
One arm, R-M3k, graded against raw M10_HGB.

Run after the Week 10 outcomes (expected Tue 17 Nov 2026); interim weekly readouts are
descriptive only. Fixed by c3_m3m4_registration_v1.json.

Universe: M10_HGB forecast rows of Weeks 8-10 whose outcome has a stat line (played), positions
QB/RB/WR/TE. Week 8 rows of the CAR-GB game (kickoff 2026-10-30 00:15 UTC) are excluded: that
game was played before registration.

Per arm and position, pooled over Weeks 8-10, against raw M10:
  MSE (primary), MAE, bias, within-week Spearman (players with either projection >= 5 PPR,
  week-position cells with >= 8 players, mean over cells).
PASS for an arm requires all three:
  (1) MSE lower than M10's at >= 3 of 4 positions
  (2) MAE not higher than M10's by more than 0.02 at any position
  (3) mean within-week Spearman not lower than M10's by more than 0.02 at any position
Also reported (not part of the rule): flagged-row bias and MAE, paired bootstrap 90 % interval
of the MSE difference (player-week resampling, 2,000 draws, seed 20261030), the same metrics for
Thursday Sleeper where joinable, and week-level results.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

POS = ["QB", "RB", "WR", "TE"]
EXCLUDE_KICKOFF = "2026-10-30T00:15:00+00:00"


def test_universe(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d.actual.notna() & d.pos.isin(POS) & d.week.between(8, 10)]
    return d[~((d.week == 8) & (d.kickoff == EXCLUDE_KICKOFF))]


def _spearman(d: pd.DataFrame, col: str) -> float:
    vals = []
    for _, g in d.groupby(["week", "pos"]):
        g = g[(g["M10"] >= 5) | (g[col] >= 5)]
        if len(g) >= 8:
            vals.append(spearmanr(g[col], g.actual).statistic)
    return float(np.mean(vals)) if vals else float("nan")


def metrics(d: pd.DataFrame, col: str) -> dict:
    e = d.actual - d[col]
    return {"n": int(len(d)), "mse": float((e ** 2).mean()), "mae": float(e.abs().mean()),
            "bias": float(e.mean()), "spearman": _spearman(d, col)}


def boot_mse_diff(d: pd.DataFrame, col: str, draws=2000, seed=20261030):
    rng = np.random.default_rng(seed)
    diff = ((d.actual - d[col]) ** 2 - (d.actual - d["M10"]) ** 2).to_numpy()
    idx = rng.integers(0, len(diff), (draws, len(diff)))
    m = diff[idx].mean(axis=1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


def grade(d: pd.DataFrame, arms) -> dict:
    out = {}
    for arm in arms:
        per = {}
        for p in POS:
            x = d[d.pos == p]
            per[p] = {"arm": metrics(x, arm), "m10": metrics(x, "M10"), "mse_diff_ci90": boot_mse_diff(x, arm)}
        c1 = sum(per[p]["arm"]["mse"] < per[p]["m10"]["mse"] for p in POS) >= 3
        c2 = all(per[p]["arm"]["mae"] <= per[p]["m10"]["mae"] + 0.02 for p in POS)
        c3 = all(per[p]["arm"]["spearman"] >= per[p]["m10"]["spearman"] - 0.02 for p in POS)
        res = {"positions": per, "rule": {"mse_3_of_4": c1, "mae_guard": c2, "spearman_guard": c3},
               "pass": bool(c1 and c2 and c3)}
        if "flag_type" in d:  # reported, not part of the rule
            res["by_flag"] = {f: {"n": int((d.flag_type == f).sum()),
                                  "arm": metrics(d[d.flag_type == f], arm) if (d.flag_type == f).any() else None,
                                  "m10": metrics(d[d.flag_type == f], "M10") if (d.flag_type == f).any() else None}
                              for f in ["FG1", "FG2", "FG3", "none"]}
        out[arm] = res
    return out

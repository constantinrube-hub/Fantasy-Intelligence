"""c3_model.py - M3k fringe guard for M10_HGB (readiness item c3). REGISTERED ARM.

Registered in c3_m3_registration_v1.json. Changing anything here changes this file's SHA-256 and
voids the registration.

Applies to M10_HGB default-PPR means per player-week, using only information from before the
target week's games (nflverse snap counts of earlier weeks, nflverse rookie season).

Flags (a row takes the first flag that applies, in this order):
  FG1  week >= 4 and at most 1 game this season with an offensive snap
  FG2  rookie and mean offensive snap share this season < 40 % (no games -> 0 %)
  FG3  >= 2 games this season and the last game's snap share is at least 15 percentage points
       below the mean of the up-to-3 games before it
Adjustment: pred' = k[pos, flag] * pred for flagged rows; unflagged rows unchanged.
  k = sum(actual PPR) / sum(M10 PPR) over played history rows (weeks >= 4) with that position and
  flag; if that cell has < 100 rows, all positions with that flag are pooled. Clipped to [0.3, 1.0].
History = M10_HGB out-of-sample rows 2022-25 from the season lock (final fit on all four seasons).

Why multiplicative: for FG1 players the ratio actual/M10 is about 0.5-0.75 at every projection
level (2022-25), so the error is proportional. The registered-in-words alternative ("shrink toward
a low base rate") pulls low projections up and failed the 2025 check; see the results note.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

POS = ["QB", "RB", "WR", "TE"]
TYPES = ["FG1", "FG2", "FG3"]
FG2_SHARE = 0.40
FG3_DROP = 0.15
MIN_CELL = 100
K_CLIP = (0.3, 1.0)
ARM = "R-M3k"


def flags(d: pd.DataFrame) -> pd.DataFrame:
    fg1 = (d.week >= 4) & (d.gp_before <= 1)
    fg2 = d.rookie.astype(bool) & (d.share_mean.fillna(0.0) < FG2_SHARE)
    fg3 = ((d.gp_before >= 2) & ((d.share_last - d.share_prev3) <= -FG3_DROP)).fillna(False)
    ftype = np.select([fg1, fg2, fg3], TYPES, "none")
    return pd.DataFrame({"fg1": fg1, "fg2": fg2, "fg3": fg3, "flag_type": ftype,
                         "flag": ftype != "none"}, index=d.index)


def fit(hist: pd.DataFrame) -> dict:
    h = hist[hist.week >= 4]
    ty = flags(h).flag_type
    k = {}
    for p in POS:
        k[p] = {}
        for f in TYPES:
            m = (h.pos == p) & (ty == f)
            pooled = bool(m.sum() < MIN_CELL)
            if pooled:
                m = ty == f
            ratio = float(h.actual[m].sum() / h.pred[m].sum())
            k[p][f] = {"k": float(np.clip(ratio, *K_CLIP)), "raw_ratio": ratio, "n": int(m.sum()), "pooled": pooled}
    return k


def apply(d: pd.DataFrame, k: dict) -> pd.Series:
    ty = flags(d).flag_type
    mult = [k[p][f]["k"] if f != "none" else 1.0 for p, f in zip(d.pos, ty)]
    return d.pred * np.asarray(mult)

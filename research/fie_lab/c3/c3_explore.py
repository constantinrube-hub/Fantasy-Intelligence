"""c3_explore.py - the forms that were checked on 2025 and NOT registered (readiness item c3).

Kept so every number in the results note can be reproduced. None of these is a challenger.
  M3-shrink  register wording: flagged pred' = pred + lambda_pos (c_pos - pred), c_pos = mean actual
             of flagged history rows, lambda_pos least squares clipped to [0, 1]
  M4-ab      register wording: pred' = max(0, a + b pred), OLS per position on history weeks w+-2
  M4-slope   level-preserving revision: pred' = max(0, m + b (pred - m)), b = OLS slope and m = mean
             prediction on history weeks w+-2
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import c3_model as M

POS = M.POS


def fit_shrink(h: pd.DataFrame) -> dict:
    f = M.flags(h).flag
    out = {}
    for p in POS:
        m = (h.pos == p) & (h.week >= 4) & f
        y, x = h.actual[m].to_numpy(), h.pred[m].to_numpy()
        c = y.mean(); u = c - x
        out[p] = (float(c), float(np.clip((u * (y - x)).sum() / (u * u).sum(), 0, 1)))
    return out


def apply_shrink(d: pd.DataFrame, o: dict) -> pd.Series:
    f = M.flags(d).flag
    c = d.pos.map({p: o[p][0] for p in POS}); lam = d.pos.map({p: o[p][1] for p in POS})
    return pd.Series(np.where(f, d.pred + lam * (c - d.pred), d.pred), index=d.index)


def fit_line(h: pd.DataFrame, weeks) -> dict:
    out = {}
    for w in weeks:
        for p in POS:
            m = (h.pos == p) & h.week.between(w - 2, w + 2)
            b, a = np.polyfit(h.pred[m], h.actual[m], 1)
            out[(w, p)] = (float(a), float(b), float(h.pred[m].mean()))
    return out


def apply_ab(d: pd.DataFrame, o: dict) -> pd.Series:
    return pd.Series([max(0.0, o[(w, p)][0] + o[(w, p)][1] * x) for x, w, p in zip(d.pred, d.week, d.pos)], index=d.index)


def apply_slope(d: pd.DataFrame, o: dict) -> pd.Series:
    return pd.Series([max(0.0, o[(w, p)][2] + o[(w, p)][1] * (x - o[(w, p)][2])) for x, w, p in zip(d.pred, d.week, d.pos)],
                     index=d.index)


def all_forms(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    s = fit_shrink(train); ln = fit_line(train, range(1, 19))
    return pd.DataFrame({"M3-shrink": apply_shrink(test, s), "M4-ab": apply_ab(test, ln),
                         "M4-slope": apply_slope(test, ln)}, index=test.index)

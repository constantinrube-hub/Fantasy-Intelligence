"""c3_build.py - fit, check and freeze the M3k fringe guard; write the Week 8 forecasts.

Usage:  python -I c3_build.py OUT_DIR
Outputs (OUT_DIR):
  c3_m3k_frozen_v1.json            k factors (final fit 2022-25) and Week 8 counts
  c3_m3k_week8_forecasts_v1.csv    M10 and R-M3k for every Week 8 M10_HGB row, flags, test exclusion
  c3_check_tables.json             2025 check (M3k + the rejected forms), 2026 W4-7 description
Reads only the FIE repo (read-only clone) and the nflverse raw files.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c3_explore as X  # noqa: E402
import c3_grade as G  # noqa: E402
import c3_lib as L  # noqa: E402
import c3_model as M  # noqa: E402

FEATS = ["gp_before", "share_mean", "share_last", "share_prev3", "rookie", "pfr_mapped"]
COLS = ["M10", M.ARM, "M3-shrink", "M4-ab", "M4-slope"]


def with_features(d, snaps, players):
    f = L.pregame_features(d[["season", "week", "gsis_id"]].reset_index(drop=True), snaps, players)
    d = d.reset_index(drop=True).copy()
    for c in FEATS:
        d[c] = f[c].values
    return d


def r(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 3)


def table(d, cols):
    out = {}
    for p in M.POS:
        x = d[d.pos == p]
        out[p] = {c: {k: (r(v) if k != "n" else v) for k, v in G.metrics(x, c).items()} for c in cols}
    f = M.flags(d).flag
    out["flagged"] = {"n": int(f.sum()), **{c: {"bias": r((d.actual - d[c])[f].mean()),
                                                 "mae": r((d.actual - d[c])[f].abs().mean()),
                                                 "mse": r(((d.actual - d[c])[f] ** 2).mean())} for c in cols}}
    return out


def score(train, test):
    k = M.fit(train)
    test = test.copy()
    test["M10"] = test.pred
    test[M.ARM] = M.apply(test, k)
    return pd.concat([test, X.all_forms(train, test)], axis=1)


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    snaps = L.load_snaps([2022, 2023, 2024, 2025, 2026])
    players = L.load_players()
    hist = with_features(L.history_table(), snaps, players)
    assert hist.season.between(2022, 2025).all()

    # 1. check (reported): fit 2022-24, evaluate 2025
    te = score(hist[hist.season <= 2024], hist[hist.season == 2025])
    check = {"weeks_4_17": table(te[te.week.between(4, 17)], COLS),
             "weeks_8_10": table(te[te.week.between(8, 10)], COLS)}

    # 2. final k factors on 2022-25
    k = M.fit(hist)

    # 3. 2026 Weeks 4-7, CONTAMINATED (M3 was found on these weeks)
    t = with_features(L.table_2026((4, 5, 6, 7)), snaps, players)
    t = score(hist, t)
    desc26 = table(t[t.actual.notna()], COLS)

    # 4. Week 8 forecasts (pre-game; snap counts through Week 7 only)
    w8 = with_features(L.forecasts_2026(8), snaps, players)
    assert (w8.pred - w8.pred_check).abs().max() < 1e-9
    w8[M.ARM] = M.apply(w8, k)
    w8 = pd.concat([w8.drop(columns=["pred_check"]), M.flags(w8)], axis=1)
    w8["excluded_from_test"] = w8.kickoff == G.EXCLUDE_KICKOFF
    w8 = w8.sort_values(["pos", "gsis_id"]).reset_index(drop=True)
    w8["pred"] = w8.pred.round(6); w8[M.ARM] = w8[M.ARM].round(6)
    for c in ["share_mean", "share_last", "share_prev3"]:
        w8[c] = w8[c].round(4)
    w8.to_csv(os.path.join(out_dir, "c3_m3k_week8_forecasts_v1.csv"), index=False, lineterminator="\n")

    frozen = {
        "schema": "fie-lab-c3-m3k-frozen-v1",
        "model": "M10_HGB",
        "arm": M.ARM,
        "history": {"source": "season-lock residual_samples, M10_HGB, test seasons 2022-25", "rows": int(len(hist))},
        "constants": {"FG2_SHARE": M.FG2_SHARE, "FG3_DROP": M.FG3_DROP, "MIN_CELL": M.MIN_CELL, "K_CLIP": list(M.K_CLIP)},
        "k": k,
        "week8": {"rows": int(len(w8)), "flagged": int(w8.flag.sum()),
                  "flagged_by_type": {f: int((w8.flag_type == f).sum()) for f in M.TYPES},
                  "excluded_from_test_rows": int(w8.excluded_from_test.sum())},
    }
    json.dump(frozen, open(os.path.join(out_dir, "c3_m3k_frozen_v1.json"), "w"), indent=1, sort_keys=True)
    json.dump({"check_2025": check, "desc_2026_w4_7_contaminated": desc26},
              open(os.path.join(out_dir, "c3_check_tables.json"), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])

"""c3_week.py - R-M3k forecasts for one target week from the frozen k factors (readiness item c3).

Usage: python -I c3_week.py WEEK FROZEN_JSON OUT_CSV
Run before the target week's first kickoff, or at grading with the same result: features use only
snap counts of earlier weeks (pregame_features filters week < WEEK, and the loader drops 2026 rows
at or after WEEK). The k factors come from c3_m3k_frozen_v1.json and are never refitted.
"""
from __future__ import annotations

import json
import os
import sys


def main(week: int, frozen_path: str, out_csv: str) -> None:
    os.environ["C3_CUTOFF_2026"] = str(week)  # must be set before c3_lib is imported
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import c3_grade as G
    import c3_lib as L
    import c3_model as M
    k = json.load(open(frozen_path))["k"]
    snaps = L.load_snaps([2026])
    players = L.load_players()
    f = L.forecasts_2026(week)
    feats = L.pregame_features(f[["season", "week", "gsis_id"]].reset_index(drop=True), snaps, players)
    f = f.reset_index(drop=True)
    for c in ["gp_before", "share_mean", "share_last", "share_prev3", "rookie", "pfr_mapped"]:
        f[c] = feats[c].values
    f[M.ARM] = M.apply(f, k)
    f = f.drop(columns=["pred_check"]).join(M.flags(f))
    f["excluded_from_test"] = f.kickoff == G.EXCLUDE_KICKOFF
    f = f.sort_values(["pos", "gsis_id"]).reset_index(drop=True)
    f["pred"] = f.pred.round(6); f[M.ARM] = f[M.ARM].round(6)
    for c in ["share_mean", "share_last", "share_prev3"]:
        f[c] = f[c].round(4)
    f.to_csv(out_csv, index=False, lineterminator="\n")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3])

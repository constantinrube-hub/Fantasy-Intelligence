"""c3_grade_run.py - the registered grading run for R-M3k (readiness item c3).

Usage: python -I c3_grade_run.py FORECAST_DIR OUT_JSON
FORECAST_DIR holds c3_m3k_week{8,9,10}_forecasts.csv: Week 8 is the frozen file from the
registration (c3_m3k_week8_forecasts_v1.csv, checked against its SHA-256); Weeks 9 and 10 come from
c3_week.py. Outcomes are read from the repo's M10 outcome files (revision_1), joined by forecast_id.
Verdict due after the Week 10 outcomes land (expected Tue 17 Nov 2026).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import pandas as pd

WEEK8_SHA256 = "6162d235dad0594d3a599e5a8bdbfcf90bceaf524b58c3061237fd61c216af75"


def main(fdir: str, out_json: str) -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import c3_grade as G
    import c3_lib as L
    import c3_model as M
    parts = []
    for w in (8, 9, 10):
        p = os.path.join(fdir, f"c3_m3k_week{w}_forecasts.csv")
        if w == 8:
            got = hashlib.sha256(open(p, "rb").read()).hexdigest()
            assert got == WEEK8_SHA256, f"Week 8 forecast file differs from the frozen one: {got}"
        f = pd.read_csv(p)
        o = L.outcomes_2026(w, grading=True)
        parts.append(f.merge(o, on="forecast_id", how="left"))
    d = pd.concat(parts, ignore_index=True)
    d["M10"] = d.pred
    u = G.test_universe(d)
    res = G.grade(u, [M.ARM])
    res["universe"] = {"rows": int(len(u)), "by_week": {int(k): int(v) for k, v in u.week.value_counts().sort_index().items()}}
    res["by_week"] = {int(w): G.grade(u[u.week == w], [M.ARM])[M.ARM]["rule"] for w in (8, 9, 10)}
    json.dump(res, open(out_json, "w"), indent=1, default=float)
    print(json.dumps({"pass": res[M.ARM]["pass"], "rule": res[M.ARM]["rule"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

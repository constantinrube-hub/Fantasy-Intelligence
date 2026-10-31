"""c3_test.py - leak and reproducibility tests for the M3k build (readiness item c3).

Usage: python -I c3_test.py BUILD_OUT_DIR
T1 reproducibility: a second build into a fresh folder gives byte-identical outputs.
T2 Week 8 leak:    rewrite every 2026 Week >= 8 row in the stats and snap files (snaps set to 0,
                   fantasy points x9) in a copied raw folder; the build must give identical outputs.
T3 history leak:   multiply all 2026 rows of the copied raw files by 9 (points) / zero snaps for
                   Weeks 1-7; the frozen k factors must not change (they use 2022-25 only).
T4 scorer:         ppr_from_components reproduces predicted_fantasy_points_default for Week 8.
T5 week script:    c3_week.py 8 reproduces the frozen Week 8 file byte for byte.
T6 grading code:   c3_grade.grade runs end to end (dry run on relabelled Weeks 5-7; numbers unused).
"""
from __future__ import annotations

import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw")
FILES = ["c3_m3k_frozen_v1.json", "c3_m3k_week8_forecasts_v1.csv", "c3_check_tables.json"]


def build(out, raw):
    env = dict(os.environ, C3_RAW=raw)
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "c3_build.py"), out], check=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def same(a, b, files=FILES):
    return all(filecmp.cmp(os.path.join(a, f), os.path.join(b, f), shallow=False) for f in files)


def copy_raw(dst, week_rule):
    os.makedirs(dst)
    for f in os.listdir(RAW):
        src = os.path.join(RAW, f)
        if f.endswith("_2026.csv"):
            d = pd.read_csv(src, low_memory=False)
            m = week_rule(d)
            if "offense_snaps" in d:
                d.loc[m, "offense_snaps"] = 0; d.loc[m, "offense_pct"] = 0.0
            if "fantasy_points_ppr" in d:
                d.loc[m, "fantasy_points_ppr"] = d.loc[m, "fantasy_points_ppr"] * 9
            d.to_csv(os.path.join(dst, f), index=False)
        else:
            shutil.copy(src, dst)


def main(ref):
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        o1 = os.path.join(tmp, "o1"); build(o1, RAW)
        res["T1_reproducible"] = same(ref, o1)

        r2 = os.path.join(tmp, "raw_w8"); copy_raw(r2, lambda d: d.week >= 8)
        o2 = os.path.join(tmp, "o2"); build(o2, r2)
        res["T2_week8_rows_ignored"] = same(ref, o2)

        r3 = os.path.join(tmp, "raw_2026"); copy_raw(r3, lambda d: d.week >= 1)
        o3 = os.path.join(tmp, "o3"); build(o3, r3)
        k_ref = json.load(open(os.path.join(ref, FILES[0])))["k"]
        k_3 = json.load(open(os.path.join(o3, FILES[0])))["k"]
        res["T3_k_independent_of_2026"] = k_ref == k_3

        # T5: the per-week script reproduces the frozen Week 8 file byte for byte
        p5 = os.path.join(tmp, "w8.csv")
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "c3_week.py"), "8",
                        os.path.join(ref, FILES[0]), p5], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res["T5_week_script_matches_freeze"] = filecmp.cmp(p5, os.path.join(ref, FILES[1]), shallow=False)

    sys.path.insert(0, HERE)
    import c3_grade as G
    import c3_lib as L
    import c3_model as M
    w8 = L.forecasts_2026(8)
    res["T4_scorer_max_abs_diff"] = float((w8.pred - w8.pred_check).abs().max())

    # T6: dry run of the grading code on 2026 Weeks 4-7 relabelled as 8-10 (code path only;
    # these numbers mean nothing and are not reported)
    t = L.table_2026((5, 6, 7))
    t["week"] = t.week + 3
    t["M10"] = t.pred
    t[M.ARM] = t.pred * 0.95
    t["flag_type"] = "none"
    g = G.grade(G.test_universe(t), [M.ARM])
    res["T6_grading_dry_run_keys"] = sorted(g[M.ARM]["rule"].keys())
    res["sha256"] = {f: hashlib.sha256(open(os.path.join(ref, f), "rb").read()).hexdigest() for f in FILES}
    print(json.dumps(res, indent=1))
    assert res["T1_reproducible"] and res["T2_week8_rows_ignored"] and res["T3_k_independent_of_2026"]
    assert res["T4_scorer_max_abs_diff"] < 1e-9
    assert res["T5_week_script_matches_freeze"]


if __name__ == "__main__":
    main(sys.argv[1])

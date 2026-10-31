#!/usr/bin/env python3
"""
fie_paired_sleeper_eval.py — paired weekly accuracy check: Sleeper vs FIE M10 forecasts.

Author: Claude (for Constantin), 25 Oct 2026. Diagnostic only; reads a local clone of
constantinrube-hub/Fantasy-Intelligence and writes nothing into it.

WHAT IT COMPARES (same players, same week, same Thursday cutoff)
  SLEEPER       Sleeper/RotoWire weekly projection, captured by the repo's
                "Capture Immutable FIE Sleeper Weekly Benchmark" workflow
                (data/research/market/sleeper/2026/week_NN.jsonl.gz, <=18 h before TNF).
                Scored here with the repo's DEFAULT_PPR weights + 2 pts per 2-pt conversion.
  M10_HGB       FIE M10 HistGradientBoosting (prospective season lock v2).
  RIDGE_PROXY   The forecast rows labelled "M9" in the M10 ledger. This is NOT production M9:
                it is a Ridge(alpha=10) on the same three M10 features
                (research/m10_prospective_season_lock_v2.py). Renamed here to avoid confusion.
  (M10_LINEAR is skipped: Ridge(alpha=6) on the same features, near-identical to the proxy.)

  FIE predictions are the ledger field predicted_fantasy_points_default (default PPR; M10 does
  not project fumbles or 2-pt conversions, so FIE carries that omission — that is FIE's fault,
  not the test's).

POPULATION
  M10 outcome rows with status OBSERVED_PROVIDER_ROW (player has an nflverse box-score row),
  joined to a Sleeper projection through a Sleeper-ID -> GSIS crosswalk.
  Players who did not play are excluded: this measures accuracy given the player played,
  not availability. Actual = nflverse fantasy_points_ppr.

CROSSWALK
  1) every MATCHED_EXACT_GSIS row in data/operations/weekly-usage-crosswalk/2026/*/*.json
  2) plus DynastyProcess db_playerids.csv (sleeper_id, gsis_id), from --crosswalk PATH or,
     if omitted, downloaded from raw.githubusercontent.com/dynastyprocess/data.
  The repo alone covers ~300 IDs, too few; the CSV raises coverage to ~6,000.

STATISTICS
  lift% = (sum|err_Sleeper| - sum|err_model|) / sum|err_Sleeper| * 100  (positive = FIE better)
  Per-week lifts, their mean, and a t-interval ACROSS WEEKS (weeks are the independent unit;
  players within a week share games and news). With fewer than 4 weeks the interval is printed
  but should not be read as evidence. A player-level bootstrap is also printed; it ignores
  within-week correlation and is therefore optimistic.

BLEND (v2, option --blend; registration w8_blend_registration_v1.json, S-BLEND75)
  B75 = 0.75 x SLEEPER + 0.25 x M10_HGB per player on the default-PPR basis above (the registered
  variant); B50 = 0.5/0.5 as context only. Both are added to the MAE/bias/lift report, and a rule block
  applies the registered rule: pooled over Weeks 8-10, B75's MAE lower than Sleeper's at >= 3 of 4
  positions AND mean within-week Spearman of B75 (players with Sleeper >= 5 PPR, >= 8 per
  week-position) not lower than Sleeper's by more than 0.01 at any position. It prints VERDICT only
  when Weeks 8, 9 and 10 are all present; otherwise INTERIM (description). Weeks 4-7 are printed
  separately as seen data. Without --blend the output is byte-identical to v1.

DATED CROSSWALK (v2, option --crosswalk-archive DIR; replaces readiness item w2)
  The DynastyProcess file changes over time, so a rerun on a later day can pair different players.
  With --crosswalk-archive DIR, a downloaded file is saved as DIR/db_playerids_<UTC date>.csv (plus
  .sha256) unless a file with identical content is already there, and the file used is printed with
  its SHA-256. Pass that file back with --crosswalk to reproduce a run exactly.

USAGE (Windows PowerShell, from anywhere)
  git -C C:\\Users\\User\\FIE\\FI pull
  py -3 fie_paired_sleeper_eval.py --repo C:\\Users\\User\\FIE\\FI --weeks 4-7
  py -3 fie_paired_sleeper_eval.py --repo C:\\Users\\User\\FIE\\FI --weeks 4-8 --csv paired_rows.csv
  py -3 fie_paired_sleeper_eval.py --repo C:\\Users\\User\\FIE\\FI --weeks 4-10 --blend --crosswalk-archive C:\\Users\\User\\FIE\\FIE-Lab\\crosswalk

Requires only the Python 3.9+ standard library.

CHANGE LOG
  v1 (25 Oct 2026): first version; replaces the ad-hoc session script used for the W4-6 numbers
                    in FIE_MODEL_INVENTORY_AND_TEST_PLAN_2026-10-25.md.
  v2 (30 Oct 2026): --blend (S-BLEND75 registered rule + B50 context) and --crosswalk-archive (dated
                    crosswalk copies). Without the new options, stdout and --csv are byte-identical to v1
                    (tested on a fixture repo against the registered v1, SHA-256 a3c04c6b...).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import glob
import gzip
import io
import json
import math
import os
import random
import statistics as st
import sys
import urllib.request
from collections import defaultdict

DP_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
SLEEPER_PPR = {  # repo DEFAULT_PPR offensive weights + 2-pt conversions
    "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "rush_td": 6.0,
    "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0, "fum_lost": -2.0,
    "pass_2pt": 2.0, "rush_2pt": 2.0, "rec_2pt": 2.0,
}
MODELS = ("M10_HGB", "RIDGE_PROXY")
BLENDS = {"B75": 0.75, "B50": 0.5}   # weight on SLEEPER; the rest on M10_HGB (B75 registered, B50 context)
BLEND_RULE_WEEKS = (8, 9, 10)
POSITIONS = ("QB", "RB", "WR", "TE")
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
       9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120}


def parse_weeks(text: str) -> list[int]:
    out: list[int] = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def jsonl_gz(path: str):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def archive_crosswalk(text: str, folder: str) -> str:
    """Save a dated copy unless identical content is already archived; return the path used."""
    os.makedirs(folder, exist_ok=True)
    data = text.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    for f in sorted(glob.glob(os.path.join(folder, "db_playerids_*.csv"))):
        with open(f, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() == digest:
                return f
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    path = os.path.join(folder, f"db_playerids_{stamp}.csv")
    with open(path, "wb") as fh:
        fh.write(data)
    with open(path + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(f"{digest}  {os.path.basename(path)}\n")
    return path


def build_crosswalk(repo: str, csv_path: str | None, archive: str | None = None) -> dict[str, str]:
    s2g: dict[str, str] = {}
    for f in glob.glob(os.path.join(repo, "data/operations/weekly-usage-crosswalk/2026/*/*.json")):
        with open(f, encoding="utf-8") as fh:
            for r in json.load(fh).get("rows", []):
                if r.get("status") == "MATCHED_EXACT_GSIS" and r.get("sleeper_player_id"):
                    s2g[str(r["sleeper_player_id"])] = str(r["source_gsis_player_id"]).replace("gsis:", "")
    repo_n = len(s2g)
    if csv_path:
        with open(csv_path, encoding="utf-8") as fh:
            text = fh.read()
    else:
        with urllib.request.urlopen(DP_URL, timeout=60) as resp:
            text = resp.read().decode("utf-8")
    if archive is not None:
        used = csv_path or archive_crosswalk(text, archive)
        print(f"crosswalk file: {used}  sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    for r in csv.DictReader(io.StringIO(text)):
        sid, gid = r.get("sleeper_id"), r.get("gsis_id")
        if sid and gid and "NA" not in (sid, gid):
            s2g.setdefault(sid, gid)
    print(f"crosswalk: {repo_n} IDs from repo, {len(s2g)} after DynastyProcess")
    return s2g


def load_week(repo: str, week: int, s2g: dict[str, str], blend: bool = False):
    base = os.path.join(repo, "data/research")
    sl_path = os.path.join(base, f"market/sleeper/2026/week_{week:02d}.jsonl.gz")
    fc_path = os.path.join(base, f"prospective/m10/forecasts/2026/week_{week:02d}/forecast.jsonl.gz")
    oc_path = os.path.join(base, f"prospective/m10/outcomes/2026/week_{week:02d}/revision_1/outcomes.jsonl.gz")
    missing = [p for p in (sl_path, fc_path, oc_path) if not os.path.exists(p)]
    if missing:
        print(f"week {week}: SKIPPED, missing {', '.join(os.path.relpath(p, repo) for p in missing)}")
        return [], {}
    sleeper, sleeper_at = {}, None
    for r in jsonl_gz(sl_path):
        sleeper_at = r.get("captured_at")
        gid = s2g.get(str(r["sleeper_id"]))
        if gid:
            sleeper[gid] = sum(float(r["stats"].get(k, 0) or 0) * w for k, w in SLEEPER_PPR.items())
    fc: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in jsonl_gz(fc_path):
        fc[r["forecast_id"]][r["model"]] = r
    rows, counts = [], defaultdict(int)
    fie_at = None
    for o in jsonl_gz(oc_path):
        counts[o["status"]] += 1
        if o["status"] != "OBSERVED_PROVIDER_ROW":
            continue
        f = fc.get(o["forecast_id"], {})
        if "M10_HGB" not in f or "M9" not in f:
            counts["NO_FORECAST"] += 1
            continue
        gid = o["canonical_player_id"]
        if gid not in sleeper:
            counts["NO_SLEEPER_MATCH"] += 1
            continue
        fie_at = f["M10_HGB"]["captured_at"]
        rows.append({
            "week": week, "player": gid, "position": f["M10_HGB"]["position_model"],
            "actual": float(o["raw_outcomes"]["fantasy_points_ppr"]),
            "SLEEPER": sleeper[gid],
            "M10_HGB": float(f["M10_HGB"]["predicted_fantasy_points_default"]),
            "RIDGE_PROXY": float(f["M9"]["predicted_fantasy_points_default"]),
        })
        if blend:
            r = rows[-1]
            for name, w in BLENDS.items():
                r[name] = w * r["SLEEPER"] + (1 - w) * r["M10_HGB"]
    print(f"week {week}: {len(rows)} paired rows | Sleeper captured {str(sleeper_at)[:16]}Z, "
          f"FIE captured {str(fie_at)[:16]}Z | outcome statuses {dict(counts)}")
    return rows, {"sleeper_at": sleeper_at, "fie_at": fie_at}


def lift(rows, model):
    base = sum(abs(r["actual"] - r["SLEEPER"]) for r in rows)
    return float("nan") if base == 0 else (base - sum(abs(r["actual"] - r[model]) for r in rows)) / base * 100


def report(rows, models=MODELS):
    rng = random.Random(7)
    print("\nlift% = FIE vs Sleeper on absolute error; positive means FIE is better.\n")
    for pos in POSITIONS:
        R = [r for r in rows if r["position"] == pos]
        if not R:
            continue
        weeks = sorted({r["week"] for r in R})
        mae = {m: st.mean(abs(r["actual"] - r[m]) for r in R) for m in ("SLEEPER",) + models}
        bias = {m: st.mean(r[m] - r["actual"] for r in R) for m in ("SLEEPER",) + models}
        print(f"{pos}  n={len(R)}  weeks={weeks}")
        print("   MAE   " + "  ".join(f"{m} {mae[m]:.2f}" for m in mae))
        print("   bias  " + "  ".join(f"{m} {bias[m]:+.2f}" for m in bias))
        for m in models:
            per = [lift([r for r in R if r["week"] == w], m) for w in weeks]
            mean = st.mean(per)
            if len(per) >= 2:
                se = st.stdev(per) / math.sqrt(len(per))
                t = T95.get(len(per) - 1, 1.96)
                ci = f"[{mean - t * se:+.1f}, {mean + t * se:+.1f}]" + ("  (<4 weeks: not evidence)" if len(per) < 4 else "")
            else:
                ci = "n/a"
            boot = sorted(lift([rng.choice(R) for _ in R], m) for _ in range(2000))
            print(f"   {m:<11} pooled {lift(R, m):+.1f}%  per week {[round(x, 1) for x in per]}  "
                  f"week-t95 {ci}  player-boot95 [{boot[50]:+.1f}, {boot[1949]:+.1f}]")
        print()


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = ranks(x), ranks(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return float("nan") if den == 0 else num / den


def within_week_spearman(R, model: str) -> float:
    vals = []
    for w in sorted({r["week"] for r in R}):
        cell = [r for r in R if r["week"] == w and r["SLEEPER"] >= 5]
        if len(cell) >= 8:
            v = spearman([r[model] for r in cell], [r["actual"] for r in cell])
            if not math.isnan(v):
                vals.append(v)
    return st.mean(vals) if vals else float("nan")


def blend_rule(rows) -> None:
    """S-BLEND75 registered rule (w8_blend_registration_v1.json)."""
    for label, weeks in (("Weeks 8-10 (registered evaluation)", set(BLEND_RULE_WEEKS)),
                         ("Weeks 4-7 (seen data, not part of the verdict)", {4, 5, 6, 7})):
        S = [r for r in rows if r["week"] in weeks]
        present = sorted({r["week"] for r in S})
        if not S:
            continue
        complete = label.startswith("Weeks 8-10") and set(present) == set(BLEND_RULE_WEEKS)
        tag = "VERDICT (registered rule)" if complete else ("INTERIM: description only" if label.startswith("Weeks 8-10")
                                                            else "RETROSPECTIVE: description only")
        print(f"S-BLEND75 rule, {label}, weeks present {present}: {tag}")
        lower, guard_ok = 0, True
        for pos in POSITIONS:
            R = [r for r in S if r["position"] == pos]
            if not R:
                continue
            m_s = st.mean(abs(r["actual"] - r["SLEEPER"]) for r in R)
            m_b = st.mean(abs(r["actual"] - r["B75"]) for r in R)
            m_c = st.mean(abs(r["actual"] - r["B50"]) for r in R)
            r_s, r_b = within_week_spearman(R, "SLEEPER"), within_week_spearman(R, "B75")
            ok_rank = not (r_b < r_s - 0.01) if not (math.isnan(r_s) or math.isnan(r_b)) else False
            lower += m_b < m_s
            guard_ok &= ok_rank
            print(f"   {pos}  n={len(R)}  MAE SLEEPER {m_s:.3f}  B75 {m_b:.3f}  (B50 {m_c:.3f})  "
                  f"Spearman SLEEPER {r_s:.3f}  B75 {r_b:.3f}  {'ok' if ok_rank else 'GUARD MISSED'}")
        passed = lower >= 3 and guard_ok
        print(f"   MAE lower at {lower} of 4; Spearman guard {'held' if guard_ok else 'missed'} -> "
              f"{'PASS' if passed else 'FAIL'}{'' if complete else ' (not a verdict)'}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--repo", required=True, help="local clone of Fantasy-Intelligence")
    ap.add_argument("--weeks", default="4-7", help="e.g. 4-7 or 4,5,6")
    ap.add_argument("--crosswalk", help="local db_playerids.csv; downloaded if omitted")
    ap.add_argument("--csv", help="optional path to write the paired rows")
    ap.add_argument("--blend", action="store_true", help="add B75 (registered S-BLEND75) and B50 (context) and the rule block")
    ap.add_argument("--crosswalk-archive", help="folder for dated copies of the downloaded crosswalk")
    a = ap.parse_args()
    s2g = build_crosswalk(a.repo, a.crosswalk, a.crosswalk_archive)
    rows = []
    for w in parse_weeks(a.weeks):
        rows.extend(load_week(a.repo, w, s2g, a.blend)[0])
    if not rows:
        print("No paired rows. Check --repo and that outcomes exist for the requested weeks.")
        return 1
    report(rows, MODELS + tuple(BLENDS) if a.blend else MODELS)
    if a.blend:
        blend_rule(rows)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
        print(f"wrote {len(rows)} rows to {a.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

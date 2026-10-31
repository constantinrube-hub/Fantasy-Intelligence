"""c3_lib.py - shared data layer for the M3 fringe guard and M4 recalibration (readiness item c3).

FIE Lab sidecar code. Reads the FIE repository read-only; never writes to it.

Leakage rule (registered): any 2026 row with week >= 8 is dropped at load time, before any
other processing, so no Week 8 outcome (the CAR-GB Thursday game was already played when this
was written) can enter a fit, a flag or a threshold.

Data:
  * M10_HGB out-of-sample history 2022-25: season-lock residual_samples (actual - predicted, raw
    components); predicted = nflverse actual - residual.
  * M10_HGB 2026 forecasts (Weeks 4-8) and outcomes (Weeks 4-7) from the repo.
  * nflverse stats_player_week, snap_counts, players (downloaded 30 Oct 2026 12:43 UTC; hashes
    in raw_sha256.txt).
"""
from __future__ import annotations

import gzip
import json
import os

import numpy as np
import pandas as pd

REPO = os.environ.get("FIE_REPO", "/home/claude/constantinrube-hub/fantasy-intelligence")
RAW = os.environ.get("C3_RAW", os.path.join(os.path.dirname(__file__), "..", "raw"))
M10 = os.path.join(REPO, "data/research/prospective/m10")
POS = ["QB", "RB", "WR", "TE"]
# 2026 rows with week >= the cutoff are never loaded (leakage rule). 8 for the registration build;
# the Week 9/10 forecast runs set it to the target week via C3_CUTOFF_2026 (c3_week.py does this).
CUTOFF_2026_WEEK = int(os.environ.get("C3_CUTOFF_2026", "8"))


def ppr_from_components(c: dict) -> float:
    """M10 default-PPR scorer (verified to 1e-14 against predicted_fantasy_points_default):
    0.04 pass yd, 4 pass TD, -2 INT, 0.1 rush yd, 6 rush TD, 1 rec, 0.1 rec yd, 6 rec TD."""
    g = lambda k: float(c.get(k, 0.0) or 0.0)
    return (0.04 * g("passing_yards") + 4 * g("passing_tds") - 2 * g("interceptions")
            + 0.1 * g("rushing_yards") + 6 * g("rushing_tds")
            + g("receptions") + 0.1 * g("receiving_yards") + 6 * g("receiving_tds"))


# ---------------------------------------------------------------- nflverse
def load_stats(seasons) -> pd.DataFrame:
    out = []
    for y in seasons:
        d = pd.read_csv(os.path.join(RAW, f"stats_player_week_{y}.csv"), low_memory=False)
        d = d[d.season_type == "REG"]
        if y == 2026:
            d = d[d.week < CUTOFF_2026_WEEK]
        out.append(d)
    return pd.concat(out, ignore_index=True)


def load_snaps(seasons) -> pd.DataFrame:
    out = []
    for y in seasons:
        d = pd.read_csv(os.path.join(RAW, f"snap_counts_{y}.csv"))
        d = d[d.game_type == "REG"]
        if y == 2026:
            d = d[d.week < CUTOFF_2026_WEEK]
        out.append(d[["season", "week", "pfr_player_id", "team", "offense_snaps", "offense_pct"]])
    return pd.concat(out, ignore_index=True)


def load_players() -> pd.DataFrame:
    p = pd.read_csv(os.path.join(RAW, "players.csv"), low_memory=False)
    return p[["gsis_id", "pfr_id", "display_name", "rookie_season", "draft_year"]]


def pregame_features(keys: pd.DataFrame, snaps: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """For each (season, week, gsis_id) row in `keys`, features known BEFORE that week's games:
    gp_before   games this season with >= 1 offensive snap, weeks < week
    share_mean  mean offense_pct over those games (NaN if none)
    share_last  offense_pct in the most recent of those games
    share_prev3 mean offense_pct over the up-to-3 games before the most recent one
    rookie      rookie_season == season (fallback draft_year == season)
    """
    pl = players.dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    k = keys.merge(pl[["gsis_id", "pfr_id", "rookie_season", "draft_year"]], on="gsis_id", how="left")
    rook = np.where(k.rookie_season.notna(), k.rookie_season == k.season, k.draft_year == k.season)
    k["rookie"] = rook.astype(bool)
    s = snaps[snaps.offense_snaps >= 1].sort_values(["pfr_player_id", "season", "week"])
    games = {key: g[["week", "offense_pct"]].to_numpy() for key, g in s.groupby(["pfr_player_id", "season"])}
    gp, smean, slast, sprev = [], [], [], []
    for pfr, season, week in zip(k.pfr_id, k.season, k.week):
        arr = games.get((pfr, season))
        if arr is None or pd.isna(pfr):
            gp.append(0); smean.append(np.nan); slast.append(np.nan); sprev.append(np.nan); continue
        a = arr[arr[:, 0] < week]
        gp.append(len(a))
        if len(a) == 0:
            smean.append(np.nan); slast.append(np.nan); sprev.append(np.nan); continue
        smean.append(a[:, 1].mean()); slast.append(a[-1, 1])
        sprev.append(a[-4:-1, 1].mean() if len(a) >= 2 else np.nan)
    k["gp_before"] = gp; k["share_mean"] = smean; k["share_last"] = slast; k["share_prev3"] = sprev
    k["pfr_mapped"] = k.pfr_id.notna()
    return k


# ---------------------------------------------------------------- M10 tables
def history_table() -> pd.DataFrame:
    """M10_HGB out-of-sample rows 2022-25 with predicted and actual default PPR (played rows)."""
    lock = json.load(open(os.path.join(M10, "season-locks/2026/season-lock.json")))
    rows = []
    for m, s in zip(lock["residual_manifest"], lock["residual_samples"]):
        if m["model"] != "M10_HGB":
            continue
        assert m["row_key"] == s["row_key"] and m["position_model"] == s["position_model"]
        season, week, rest = m["row_key"].split("-", 2)
        pos, team = rest.rsplit("-", 2)[1:]
        gsis = rest.rsplit("-", 2)[0]
        rows.append({"season": int(season), "week": int(week), "gsis_id": gsis, "pos": pos,
                     "team": team, "res": s["residuals"]})
    h = pd.DataFrame(rows)
    st = load_stats(sorted(h.season.unique()))
    st = st.rename(columns={"player_id": "gsis_id", "passing_interceptions": "interceptions"})
    cols = ["attempts", "completions", "passing_yards", "passing_tds", "interceptions", "carries",
            "rushing_yards", "rushing_tds", "targets", "receptions", "receiving_yards", "receiving_tds"]
    st = st[["season", "week", "gsis_id", "fantasy_points_ppr"] + cols].drop_duplicates(["season", "week", "gsis_id"])
    h = h.merge(st, on=["season", "week", "gsis_id"], how="left")
    miss = h.fantasy_points_ppr.isna().mean()
    h = h[h.fantasy_points_ppr.notna()].copy()
    pred = []
    for r in h.itertuples():
        comp = {k: getattr(r, k) - v for k, v in r.res.items()}  # residual = actual - predicted
        pred.append(ppr_from_components(comp))
    h["pred"] = pred
    h["actual"] = h.fantasy_points_ppr.astype(float)
    h.attrs["unmatched_share"] = float(miss)
    return h.drop(columns=["res"])


def forecasts_2026(week: int) -> pd.DataFrame:
    f = [json.loads(l) for l in gzip.open(os.path.join(M10, f"forecasts/2026/week_{week:02d}/forecast.jsonl.gz"))]
    f = [r for r in f if r["model"] == "M10_HGB"]
    return pd.DataFrame({
        "season": 2026, "week": week,
        "gsis_id": [r["canonical_player_id"] for r in f],
        "pos": [r["position_model"] for r in f],
        "team": [r["team"] for r in f],
        "forecast_id": [r["forecast_id"] for r in f],
        "kickoff": [r["player_kickoff_at"] for r in f],
        "pred": [float(r["predicted_fantasy_points_default"]) for r in f],
        "pred_check": [ppr_from_components(r["predicted_raw_components"]) for r in f],
    })


def outcomes_2026(week: int, grading: bool = False) -> pd.DataFrame:
    """Outcomes are read for Weeks >= 8 only by the registered grading run (grading=True)."""
    assert grading or week < CUTOFF_2026_WEEK, "leakage rule: no 2026 outcome at or after the cutoff"
    p = os.path.join(M10, f"outcomes/2026/week_{week:02d}/revision_1/outcomes.jsonl.gz")
    o = [json.loads(l) for l in gzip.open(p)]
    return pd.DataFrame({"forecast_id": [r["forecast_id"] for r in o],
                         # raw_outcomes is null when the player has no stat line (did not play)
                         "actual": [(r["raw_outcomes"] or {}).get("fantasy_points_ppr") for r in o]})


def table_2026(weeks=(4, 5, 6, 7)) -> pd.DataFrame:
    out = []
    for w in weeks:
        f = forecasts_2026(w).merge(outcomes_2026(w), on="forecast_id", how="left")
        out.append(f)
    t = pd.concat(out, ignore_index=True)
    return t

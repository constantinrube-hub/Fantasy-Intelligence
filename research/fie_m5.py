#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.7-M5 decision-policy research.

Implements roadmap Steps 24-27 on top of Milestones 1-4:
24 Draft integration evidence and safe production contract,
25 waiver policy trained on future three-game production,
26 weekly Start/Sit calibration with empirical risk bands,
27 format-specific Redraft/Dynasty/Best Ball/Chopped strategy layer.

M5 is the first integration milestone, but it is fail-closed: live use requires a
compatible current decision snapshot plus validated upstream evidence. When
those are unavailable, the browser falls back to the frozen V8.2.2 path.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_m2 import FOLDS
from statistical_guardrails import promotion_gate

CONTROL_BUILD = "V8.2.2"
RESEARCH_BUILD = "V8.7-M5"
MILESTONE = "M5"
POSITIONS = ["QB", "RB", "WR", "TE", "EDGE", "IDL", "LB", "S", "CB"]
KEYS = ["season", "week", "canonical_player_id", "position_model"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()




def json_safe(v):
    if isinstance(v, dict):
        return {k: json_safe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [json_safe(x) for x in v]
    if isinstance(v, tuple):
        return [json_safe(x) for x in v]
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, (np.integer,)):
        return int(v)
    return v

def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def safe_corr(x, y) -> Optional[float]:
    z = pd.DataFrame({"x": pd.to_numeric(pd.Series(x), errors="coerce"), "y": pd.to_numeric(pd.Series(y), errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None
    r = spearmanr(z.x, z.y).statistic
    return None if not np.isfinite(r) else float(r)


def rmse(y, p) -> float:
    return float(math.sqrt(mean_squared_error(y, p)))


def ridge_pipeline(alpha: float = 12.0) -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def export_ridge_spec(model: Pipeline, features: Sequence[str], n_train: int) -> dict:
    imp, sc, reg = model.named_steps["impute"], model.named_steps["scale"], model.named_steps["ridge"]
    return {
        "algorithm": "median_impute+standardize+ridge",
        "features": list(features),
        "imputer_medians": [float(x) for x in imp.statistics_],
        "scaler_mean": [float(x) for x in sc.mean_],
        "scaler_scale": [float(x) if float(x) else 1.0 for x in sc.scale_],
        "coefficients": [float(x) for x in reg.coef_],
        "intercept": float(reg.intercept_),
        "n_train": int(n_train),
        "prediction_floor": 0.0,
    }


def upstream_status(m4: dict, pos: str) -> str:
    for r in m4.get("final_position_models", {}).get("aggregate", []):
        if r.get("position") == pos:
            return r.get("status", "diagnostic_only")
    return "diagnostic_only"


def blend_status(m4: dict, pos: str) -> Tuple[str, Optional[float]]:
    for r in m4.get("blend", {}).get("aggregate", []):
        if r.get("position") == pos:
            return r.get("status", "diagnostic_only"), r.get("recommended_fie_weight_next")
    return "unavailable", None


def load_frames(args):
    d = Path(args.derived_dir)
    oos = read_csv(d / "milestone4_oos_predictions.csv.gz")
    m2 = read_csv(d / "milestone2_player_week.csv.gz")
    pw = read_csv(d / "player_week.csv.gz")
    ps = read_csv(d / "player_season.csv.gz")
    young = read_csv(d / "milestone3_young_player_season.csv.gz")
    m1 = load_json(args.m1_bundle)
    m2b = load_json(args.m2_bundle)
    m3 = load_json(args.m3_bundle)
    m4 = load_json(args.m4_bundle)
    if oos.empty:
        raise RuntimeError("Milestone 4 OOS predictions are required. Run M1→M4 with the same derived directory first.")
    oos["season"] = pd.to_numeric(oos.season, errors="coerce").astype("Int64")
    oos["week"] = pd.to_numeric(oos.week, errors="coerce").astype("Int64")
    if not m2.empty:
        keep = [c for c in KEYS + [
            "fp_prior_4", "fp_next3", "opportunity_xfp_realized", "opportunity_xfp_pregame", "xfp_residual",
            "opportunity_change_score", "role_breakout_signal", "receiving_competition_index",
            "backfield_competition_index", "tackle_competition_index", "pass_rush_support_index",
        ] if c in m2.columns]
        oos = oos.merge(m2[keep], on=[c for c in KEYS if c in m2.columns], how="left", suffixes=("", "_m2"))
    return oos, pw, ps, young, m1, m2b, m3, m4


# --------------------------- Step 24 Draft ---------------------------

def top_quartile_precision(g: pd.DataFrame, pred_col: str, actual_col: str) -> Optional[float]:
    z = g[[pred_col, actual_col]].dropna()
    if len(z) < 8:
        return None
    k = max(1, int(math.ceil(len(z) * .25)))
    p = set(z.nlargest(k, pred_col).index)
    a = set(z.nlargest(k, actual_col).index)
    return float(len(p & a) / k)


def draft_season_validation(oos: pd.DataFrame, m4: dict) -> Tuple[List[dict], List[dict], pd.DataFrame]:
    season = oos.groupby(["season", "canonical_player_id", "full_name", "team", "position_model"], as_index=False).agg(
        games=("fantasy_points", "count"),
        actual_total=("fantasy_points", "sum"),
        fie_total=("fie_projection", "sum"),
        baseline_total=("baseline_projection", "sum"),
    )
    rows = []
    for (yr, pos), g in season.groupby(["season", "position_model"]):
        z = g.dropna(subset=["actual_total", "fie_total", "baseline_total"]).copy()
        if len(z) < 4:
            continue
        fma = float(mean_absolute_error(z.actual_total, z.fie_total))
        bma = float(mean_absolute_error(z.actual_total, z.baseline_total))
        rows.append({
            "position": pos, "test_season": int(yr), "n_players": int(len(z)),
            "fie_season_mae": fma, "baseline_season_mae": bma,
            "mae_improvement_vs_baseline": float((bma - fma) / bma) if bma > 0 else None,
            "fie_season_spearman": safe_corr(z.fie_total, z.actual_total),
            "baseline_season_spearman": safe_corr(z.baseline_total, z.actual_total),
            "fie_top_quartile_precision": top_quartile_precision(z, "fie_total", "actual_total"),
            "baseline_top_quartile_precision": top_quartile_precision(z, "baseline_total", "actual_total"),
        })
    agg = []
    f = pd.DataFrame(rows)
    if not f.empty:
        for pos, g in f.groupby("position"):
            imp = pd.to_numeric(g.mae_improvement_vs_baseline, errors="coerce").dropna()
            wins = int((imp > 0).sum())
            m4ok = upstream_status(m4, pos) == "validated_candidate"
            mean_imp = float(imp.mean()) if len(imp) else None
            sp = pd.to_numeric(g.fie_season_spearman, errors="coerce").dropna()
            bp = pd.to_numeric(g.baseline_season_spearman, errors="coerce").dropna()
            gate = promotion_gate(imp.tolist(), weights=g.loc[imp.index, "n_players"].tolist(), min_mean=.01, min_folds=4, require_positive_ci=True)
            status = "validated_candidate" if m4ok and gate["robust"] else "diagnostic_only"
            agg.append({
                "position": pos, "folds": int(len(g)), "n_players": int(g.n_players.sum()),
                "mean_mae_improvement_vs_baseline": mean_imp, "positive_folds": wins,
                "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"],
                "mean_fie_season_spearman": float(sp.mean()) if len(sp) else None,
                "mean_baseline_season_spearman": float(bp.mean()) if len(bp) else None,
                "status": status,
            })
    return rows, agg, season


# --------------------------- Step 25 Waiver --------------------------

WAIVER_FEATURES = [
    "fie_projection", "fp_prior_4", "opportunity_xfp_pregame", "xfp_residual", "opportunity_change_score",
    "role_breakout_signal", "receiving_competition_index", "backfield_competition_index",
    "tackle_competition_index", "pass_rush_support_index",
]


def waiver_features(g: pd.DataFrame) -> List[str]:
    out = []
    for c in WAIVER_FEATURES:
        if c in g and pd.to_numeric(g[c], errors="coerce").notna().sum() >= 20:
            out.append(c)
    return out


def waiver_validation(oos: pd.DataFrame, m4: dict) -> Tuple[List[dict], List[dict], dict]:
    rows, specs = [], {}
    for train_seasons, test_season in FOLDS:
        for pos in POSITIONS:
            z = oos[oos.position_model.eq(pos)].copy()
            fs = waiver_features(z)
            if len(fs) < 2 or "fp_next3" not in z:
                continue
            tr = z[z.season.isin(train_seasons)].dropna(subset=["fp_next3"]).copy()
            te = z[z.season.eq(test_season)].dropna(subset=["fp_next3"]).copy()
            if len(tr) < 60 or len(te) < 12:
                continue
            model = ridge_pipeline()
            model.fit(tr[fs], pd.to_numeric(tr.fp_next3, errors="coerce"))
            pred = np.maximum(0.0, model.predict(te[fs]))
            y = pd.to_numeric(te.fp_next3, errors="coerce")
            base = pd.to_numeric(te.fp_prior_4, errors="coerce") if "fp_prior_4" in te else pd.Series(np.nan, index=te.index)
            mask = y.notna()
            bmask = mask & base.notna()
            ma = float(mean_absolute_error(y[mask], pred[mask.to_numpy()]))
            bm = float(mean_absolute_error(y[bmask], base[bmask])) if bmask.sum() >= 8 else None
            rows.append({
                "position": pos, "train_start": min(train_seasons), "train_end": max(train_seasons), "test_season": test_season,
                "n_test": int(mask.sum()), "feature_count": len(fs), "mae": ma, "rmse": rmse(y[mask], pred[mask.to_numpy()]),
                "spearman": safe_corr(pred[mask.to_numpy()], y[mask]), "baseline_mae": bm,
                "mae_improvement_vs_recent_fp": float((bm - ma) / bm) if bm and bm > 0 else None,
                "features": fs,
            })
    f = pd.DataFrame(rows)
    agg = []
    if not f.empty:
        for pos, g in f.groupby("position"):
            imp = pd.to_numeric(g.mae_improvement_vs_recent_fp, errors="coerce").dropna()
            mean_imp = float(imp.mean()) if len(imp) else None
            wins = int((imp > 0).sum())
            gate = promotion_gate(imp.tolist(), weights=g.loc[imp.index, "n_test"].tolist(), min_mean=.01, min_folds=4, require_positive_ci=True)
            agg.append({
                "position": pos, "folds": int(len(g)), "n_test": int(g.n_test.sum()),
                "mean_mae": float(np.average(g.mae, weights=g.n_test)),
                "mean_baseline_mae": float(np.average(g.loc[g.baseline_mae.notna(), "baseline_mae"], weights=g.loc[g.baseline_mae.notna(), "n_test"])) if g.baseline_mae.notna().any() else None,
                "mean_mae_improvement_vs_recent_fp": mean_imp, "positive_folds": wins,
                "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"],
                "mean_spearman": float(pd.to_numeric(g.spearman, errors="coerce").mean()),
                "status": "validated_candidate" if upstream_status(m4, pos) == "validated_candidate" and gate["robust"] else "diagnostic_only",
            })
    # Deployable policy specs trained on all completed primary seasons. These predict future three-game PPG.
    for pos in POSITIONS:
        z = oos[oos.position_model.eq(pos)].dropna(subset=["fp_next3"]).copy()
        fs = waiver_features(z)
        if len(z) < 100 or len(fs) < 2:
            continue
        model = ridge_pipeline(); model.fit(z[fs], pd.to_numeric(z.fp_next3, errors="coerce"))
        specs[pos] = export_ridge_spec(model, fs, len(z))
    return rows, agg, {"positions": specs, "target": "mean fantasy points over next 3 games", "live_status": "CONDITIONAL"}


# --------------------------- Step 26 Weekly --------------------------

def weekly_ranking_metrics(oos: pd.DataFrame, m4: dict) -> Tuple[List[dict], List[dict]]:
    rows = []
    for (yr, wk, pos), g in oos.groupby(["season", "week", "position_model"]):
        z = g.dropna(subset=["fantasy_points", "fie_projection"]).copy()
        if len(z) < 6:
            continue
        k = max(1, int(math.ceil(len(z) * .25)))
        actual_top = set(z.nlargest(k, "fantasy_points").index)
        fie_top = set(z.nlargest(k, "fie_projection").index)
        base_top = set(z.nlargest(k, "baseline_projection").index) if z.baseline_projection.notna().sum() >= 6 else set()
        best_actual = float(z.fantasy_points.max())
        fie_pick = z.loc[z.fie_projection.idxmax()]
        base_pick = z.loc[z.baseline_projection.idxmax()] if base_top else None
        rows.append({
            "season": int(yr), "week": int(wk), "position": pos, "n": int(len(z)),
            "fie_spearman": safe_corr(z.fie_projection, z.fantasy_points),
            "baseline_spearman": safe_corr(z.baseline_projection, z.fantasy_points),
            "fie_top_quartile_precision": float(len(actual_top & fie_top) / k),
            "baseline_top_quartile_precision": float(len(actual_top & base_top) / k) if base_top else None,
            "fie_top1_regret": float(best_actual - fie_pick.fantasy_points),
            "baseline_top1_regret": float(best_actual - base_pick.fantasy_points) if base_pick is not None else None,
        })
    a = []
    d = pd.DataFrame(rows)
    if not d.empty:
        for pos, g in d.groupby("position"):
            fs=float(pd.to_numeric(g.fie_spearman, errors="coerce").mean()); bs=float(pd.to_numeric(g.baseline_spearman, errors="coerce").mean())
            fp=float(pd.to_numeric(g.fie_top_quartile_precision, errors="coerce").mean()); bp=float(pd.to_numeric(g.baseline_top_quartile_precision, errors="coerce").mean())
            fr=float(pd.to_numeric(g.fie_top1_regret, errors="coerce").mean()); br=float(pd.to_numeric(g.baseline_top1_regret, errors="coerce").mean())
            season_rank=[]
            for _,sg in g.groupby("season"):
                sf=pd.to_numeric(sg.fie_spearman,errors="coerce").mean(); sb=pd.to_numeric(sg.baseline_spearman,errors="coerce").mean()
                if np.isfinite(sf) and np.isfinite(sb): season_rank.append(float(sf-sb))
            rank_gate=promotion_gate(season_rank,min_mean=.01,min_folds=3,require_positive_ci=True)
            precision_ok = np.isfinite(fp) and np.isfinite(bp) and fp >= bp - .01
            regret_ok = np.isfinite(fr) and np.isfinite(br) and fr <= br * 1.02
            a.append({
                "position": pos, "weeks": int(len(g)), "n": int(g.n.sum()),
                "mean_fie_spearman": fs, "mean_baseline_spearman": bs,
                "mean_fie_top_quartile_precision": fp, "mean_baseline_top_quartile_precision": bp,
                "mean_fie_top1_regret": fr, "mean_baseline_top1_regret": br,
                "rank_improvement_ci95_low":rank_gate["ci95_low"],"rank_improvement_ci95_high":rank_gate["ci95_high"],
                "status": "validated_candidate" if upstream_status(m4, pos) == "validated_candidate" and rank_gate["robust"] and precision_ok and regret_ok else "diagnostic_only",
            })
    return rows, a


def weekly_risk_calibration(oos: pd.DataFrame, m4: dict) -> Tuple[List[dict], List[dict], List[dict]]:
    z = oos.dropna(subset=["fantasy_points", "fie_projection"]).copy()
    z["residual"] = pd.to_numeric(z.fantasy_points, errors="coerce") - pd.to_numeric(z.fie_projection, errors="coerce")
    bands = []
    for pos, g in z.groupby("position_model"):
        r = g.residual.dropna()
        if len(r) < 30:
            continue
        bands.append({
            "position": pos, "n": int(len(r)), "q10": float(r.quantile(.10)), "q25": float(r.quantile(.25)),
            "q50": float(r.quantile(.50)), "q75": float(r.quantile(.75)), "q90": float(r.quantile(.90)),
            "residual_mae": float(r.abs().mean()), "residual_sd": float(r.std(ddof=0)),
            "upstream_status": upstream_status(m4, pos),
        })
    folds = []
    seasons = sorted(int(x) for x in z.season.dropna().unique())
    for test in seasons:
        prior = [s for s in seasons if s < test]
        if not prior:
            continue
        for pos in POSITIONS:
            train = z[z.season.isin(prior) & z.position_model.eq(pos)].residual.dropna()
            te = z[z.season.eq(test) & z.position_model.eq(pos)].copy()
            if len(train) < 25 or len(te) < 12:
                continue
            q10, q50, q90 = [float(train.quantile(q)) for q in (.10, .50, .90)]
            p10 = te.fie_projection + q10; p50 = te.fie_projection + q50; p90 = te.fie_projection + q90
            y = te.fantasy_points
            folds.append({
                "position": pos, "test_season": int(test), "prior_holdout_seasons": prior, "n": int(len(te)),
                "below_p10_rate": float((y < p10).mean()), "above_p90_rate": float((y > p90).mean()),
                "interval80_coverage": float(((y >= p10) & (y <= p90)).mean()),
                "median_bias": float((y - p50).mean()),
            })
    agg = []
    f = pd.DataFrame(folds)
    if not f.empty:
        for pos, g in f.groupby("position"):
            cov = float(np.average(g.interval80_coverage, weights=g.n))
            lo = float(np.average(g.below_p10_rate, weights=g.n)); hi = float(np.average(g.above_p90_rate, weights=g.n))
            upstream = upstream_status(m4, pos)
            fold_ok=((g.interval80_coverage>=.65)&(g.interval80_coverage<=.95)&(g.below_p10_rate<=.20)&(g.above_p90_rate<=.20))
            consistent=int(fold_ok.sum())>=max(2,int(math.ceil(len(g)*.67)))
            calibrated = len(g)>=3 and .68 <= cov <= .92 and lo <= .18 and hi <= .18 and consistent
            agg.append({
                "position": pos, "folds": int(len(g)), "n": int(g.n.sum()), "interval80_coverage": cov,
                "below_p10_rate": lo, "above_p90_rate": hi, "mean_median_bias": float(np.average(g.median_bias, weights=g.n)),"calibrated_folds":int(fold_ok.sum()),
                "status": "validated_candidate" if upstream == "validated_candidate" and calibrated else "diagnostic_only",
            })
    return folds, agg, bands


# --------------------------- Step 27 Formats -------------------------

def bestball_proxy(oos: pd.DataFrame) -> List[dict]:
    d = oos.dropna(subset=["fantasy_points", "fie_projection"]).copy()
    rows = []
    for (yr, pos), season in d.groupby(["season", "position_model"]):
        fie_hits = base_hits = actual_n = 0
        fie_tp = base_tp = 0
        for _, g in season.groupby("week"):
            if len(g) < 6:
                continue
            k = max(1, int(math.ceil(len(g) * .25)))
            actual = set(g.nlargest(k, "fantasy_points").index); actual_n += len(actual)
            fp = set(g.nlargest(k, "fie_projection").index); fie_hits += len(fp); fie_tp += len(fp & actual)
            if g.baseline_projection.notna().sum() >= 6:
                bp = set(g.nlargest(k, "baseline_projection").index); base_hits += len(bp); base_tp += len(bp & actual)
        if actual_n:
            rows.append({
                "season": int(yr), "position": pos,
                "fie_spike_precision": float(fie_tp / fie_hits) if fie_hits else None,
                "baseline_spike_precision": float(base_tp / base_hits) if base_hits else None,
                "spike_events": int(actual_n),
            })
    return rows


def chopped_proxy(oos: pd.DataFrame) -> List[dict]:
    d = oos.dropna(subset=["fantasy_points", "fie_projection"]).copy()
    rows = []
    for (yr, pos), season in d.groupby(["season", "position_model"]):
        parts = []
        for _, g in season.groupby("week"):
            if len(g) < 6:
                continue
            cut = float(g.fantasy_points.quantile(.25)); q = g.copy(); q["bust"] = (q.fantasy_points <= cut).astype(int); parts.append(q)
        if not parts:
            continue
        z = pd.concat(parts)
        if z.bust.nunique() < 2:
            continue
        try: fie_auc = float(roc_auc_score(z.bust, -pd.to_numeric(z.fie_projection, errors="coerce")))
        except Exception: fie_auc = None
        b = z.dropna(subset=["baseline_projection"])
        try: base_auc = float(roc_auc_score(b.bust, -pd.to_numeric(b.baseline_projection, errors="coerce"))) if b.bust.nunique() >= 2 else None
        except Exception: base_auc = None
        rows.append({"season": int(yr), "position": pos, "n": int(len(z)), "fie_bust_auc": fie_auc, "baseline_bust_auc": base_auc})
    return rows


def format_strategy(draft_agg: List[dict], weekly_agg: List[dict], m3: dict, oos: pd.DataFrame) -> dict:
    dmap = {r["position"]: r for r in draft_agg}
    wmap = {r["position"]: r for r in weekly_agg}
    bb = bestball_proxy(oos); ch = chopped_proxy(oos)
    bbdf, chdf = pd.DataFrame(bb), pd.DataFrame(ch)
    bbagg, chagg = [], []
    if not bbdf.empty:
        for pos, g in bbdf.groupby("position"):
            f = pd.to_numeric(g.fie_spike_precision, errors="coerce").mean(); b = pd.to_numeric(g.baseline_spike_precision, errors="coerce").mean()
            dif = pd.to_numeric(g.fie_spike_precision, errors="coerce") - pd.to_numeric(g.baseline_spike_precision, errors="coerce")
            valid = dif.dropna(); wins = int((valid > 0).sum())
            imp = float(f-b) if np.isfinite(f) and np.isfinite(b) else None
            gate=promotion_gate(valid.tolist(),min_mean=.01,min_folds=3,require_positive_ci=True)
            bbagg.append({"position": pos, "folds": int(len(g)), "fie_spike_precision": float(f), "baseline_spike_precision": float(b), "improvement": imp, "positive_folds": wins, "bootstrap_ci95_low":gate["ci95_low"],"bootstrap_ci95_high":gate["ci95_high"], "status": "validated_candidate" if gate["robust"] else "diagnostic_only"})
    if not chdf.empty:
        for pos, g in chdf.groupby("position"):
            f = pd.to_numeric(g.fie_bust_auc, errors="coerce").mean(); b = pd.to_numeric(g.baseline_bust_auc, errors="coerce").mean()
            dif = pd.to_numeric(g.fie_bust_auc, errors="coerce") - pd.to_numeric(g.baseline_bust_auc, errors="coerce")
            valid = dif.dropna(); wins = int((valid > 0).sum())
            imp = float(f-b) if np.isfinite(f) and np.isfinite(b) else None
            gate=promotion_gate(valid.tolist(),min_mean=.01,min_folds=3,require_positive_ci=True)
            chagg.append({"position": pos, "folds": int(len(g)), "fie_bust_auc": float(f), "baseline_bust_auc": float(b), "improvement": imp, "positive_folds": wins, "bootstrap_ci95_low":gate["ci95_low"],"bootstrap_ci95_high":gate["ci95_high"], "status": "validated_candidate" if gate["robust"] else "diagnostic_only"})
    young = {r.get("variant"): r for r in m3.get("young_player_model", {}).get("aggregate", [])}
    redraft_ok = sum(1 for r in draft_agg if r.get("status") == "validated_candidate")
    weekly_ok = sum(1 for r in weekly_agg if r.get("status") == "validated_candidate")
    bb_ok = sum(1 for r in bbagg if r.get("status") == "validated_candidate")
    ch_ok = sum(1 for r in chagg if r.get("status") == "validated_candidate")
    profiles = {
        "REDRAFT": {
            "label": "Redraft", "evidence_status": "validated_proxy" if redraft_ok >= 4 and weekly_ok >= 4 else "diagnostic_only",
            "production_core": "season projection + league VOR",
            "draft_weights": {"season_projection": .55, "vor": .20, "current_role": .10, "weekly_shape": .05, "market_edge": .10},
            "waiver_weights": {"next3": .45, "role_change": .20, "weekly": .20, "roster_gain": .15},
        },
        "DYNASTY": {
            "label": "Dynasty", "evidence_status": "partial_validated" if young.get("preseason", {}).get("status") == "validated_candidate" else "diagnostic_only",
            "production_core": "redraft production + future role probability + age/contract/market",
            "draft_weights": {"season_projection": .32, "vor": .13, "future_role": .25, "age_curve": .12, "talent": .08, "market_edge": .10},
            "waiver_weights": {"next3": .22, "role_change": .18, "future_role": .30, "roster_gain": .15, "market": .15},
            "limitation": "full multi-year dynasty asset-value backtest is not yet available",
        },
        "REDRAFT_BESTBALL": {
            "label": "Redraft + Best Ball", "evidence_status": "validated_player_level_proxy" if bb_ok >= 4 and redraft_ok >= 4 else "diagnostic_only",
            "production_core": "season projection + spike-week probability + depth contribution",
            "draft_weights": {"season_projection": .40, "vor": .15, "spike": .25, "depth_fit": .10, "market_edge": .10},
            "waiver_weights": {"next3": .30, "spike": .30, "role_change": .15, "depth_fit": .15, "market": .10},
            "limitation": "player-level spike validation is not a full historical best-ball roster simulation",
        },
        "DYNASTY_BESTBALL": {
            "label": "Dynasty + Best Ball", "evidence_status": "partial_validated" if young.get("preseason", {}).get("status") == "validated_candidate" and bb_ok >= 4 else "diagnostic_only",
            "production_core": "dynasty future role + spike-week contribution",
            "draft_weights": {"season_projection": .25, "vor": .10, "future_role": .22, "age_curve": .10, "spike": .18, "market_edge": .15},
            "waiver_weights": {"next3": .18, "future_role": .25, "spike": .25, "role_change": .12, "market": .20},
            "limitation": "combined dynasty/best-ball utility is a transparent policy transform, not a directly optimized historical league simulation",
        },
        "CHOPPED": {
            "label": "Chopped", "evidence_status": "validated_player_level_proxy" if ch_ok >= 4 and weekly_ok >= 4 else "diagnostic_only",
            "production_core": "weekly median + calibrated downside + short-horizon role security",
            "draft_weights": {"season_projection": .30, "vor": .10, "floor": .30, "early_week": .20, "health": .10},
            "waiver_weights": {"next3": .25, "floor": .30, "role_change": .15, "weekly": .20, "market": .10},
            "limitation": "bust-risk validation is player-level; true guillotine survival requires historical roster-level elimination data",
        },
    }
    return {"profiles": profiles, "best_ball_proxy": bb, "best_ball_aggregate": bbagg, "chopped_proxy": ch, "chopped_aggregate": chagg}


def write_derived(season: pd.DataFrame, derived_dir: Optional[str]) -> dict:
    if not derived_dir:
        return {"written": False, "files": {}}
    p = Path(derived_dir); p.mkdir(parents=True, exist_ok=True)
    f = p / "milestone5_draft_season_validation.csv.gz"; season.to_csv(f, index=False, compression="gzip")
    return {"written": True, "files": {"milestone5_draft_season_validation": {"path": str(f), "rows": int(len(season)), "columns": int(len(season.columns))}}}


def run(args) -> dict:
    oos, pw, ps, young, m1, m2b, m3, m4 = load_frames(args)
    drows, dagg, season = draft_season_validation(oos, m4)
    wrows, wagg, wspec = waiver_validation(oos, m4)
    rank_rows, rank_agg = weekly_ranking_metrics(oos, m4)
    risk_rows, risk_agg, risk_bands = weekly_risk_calibration(oos, m4)
    formats = format_strategy(dagg, risk_agg, m3, oos)
    manifest = write_derived(season, args.derived_dir)

    validated_models = {r.get("position") for r in m4.get("final_position_models", {}).get("aggregate", []) if r.get("status") == "validated_candidate"}
    validated_blends = {r.get("position") for r in m4.get("blend", {}).get("aggregate", []) if r.get("status") == "validated_candidate"}
    runtime_positions = sorted(validated_models)
    weekly_positions = sorted(set(r.get("position") for r in rank_agg if r.get("status") == "validated_candidate") & set(runtime_positions))
    draft_positions = sorted(set(r.get("position") for r in dagg if r.get("status") == "validated_candidate") & set(runtime_positions))
    waiver_positions = sorted(set(r.get("position") for r in wagg if r.get("status") == "validated_candidate") & set(runtime_positions))
    risk_positions = sorted(set(r.get("position") for r in risk_agg if r.get("status") == "validated_candidate") & set(weekly_positions))
    validated_format_profiles = sorted(k for k, v in formats.get("profiles", {}).items() if str(v.get("evidence_status", "")).startswith("validated_"))
    bb_positions = sorted(r.get("position") for r in formats.get("best_ball_aggregate", []) if r.get("status") == "validated_candidate")
    chopped_positions = sorted(r.get("position") for r in formats.get("chopped_aggregate", []) if r.get("status") == "validated_candidate")
    format_position_gates = {
        "REDRAFT": sorted(set(runtime_positions)),
        "DYNASTY": [],
        "REDRAFT_BESTBALL": sorted(set(runtime_positions) & set(bb_positions)),
        "DYNASTY_BESTBALL": [],
        "CHOPPED": sorted(set(runtime_positions) & set(risk_positions) & set(chopped_positions)),
    }
    bundle = {
        "schema_version": 5, "milestone": MILESTONE, "control_build": CONTROL_BUILD, "research_build": RESEARCH_BUILD,
        "generated_at": utc_now(), "status": "complete", "steps_completed": [24, 25, 26, 27],
        "integration_mode": "fail_closed_conditional",
        "scoring_signature": m4.get("scoring_signature") or m1.get("scoring", {}).get("signature"),
        "scoring_settings": m1.get("scoring", {}).get("settings", {}),
        "methodology": {
            "step24": "Draft uses league-scored season projection/VOR as the anchor; M5 validates availability-conditioned season aggregation and does not pretend this is a preseason injury forecast.",
            "step25": "Waiver policy predicts mean fantasy points over the next three games from projection, opportunity, regression and role-change evidence using expanding windows.",
            "step26": "Weekly decisions use M4 mean projection plus residual-quantile risk bands learned only from prior holdout seasons for calibration tests.",
            "step27": "One football projection core feeds separate transparent Redraft, Dynasty, Best Ball and Chopped utility transforms; format-specific evidence limits are surfaced.",
        },
        "activation": {
            "policy": "fail_closed", "upstream_validated_positions": runtime_positions,
            "blend_validated_positions": sorted(validated_blends),
            "decision_gates": {
                "weekly_mean_positions": weekly_positions,
                "weekly_risk_positions": risk_positions,
                "draft_policy_positions": draft_positions,
                "waiver_policy_positions": waiver_positions,
                "validated_format_profiles": validated_format_profiles,
                "format_position_gates": format_position_gates,
            },
            "requires_current_snapshot": True,
            "current_snapshot_path": "data/research/current/milestone5_current.json",
            "fallback": "V8.2.2 live decision logic",
            "rule": "A player receives M5 decision values only when the current snapshot marks that player activation_eligible=true; all other players retain the V8.2.2 path.",
        },
        "draft_integration": {
            "folds": drows, "aggregate": dagg,
            "live_contract": {
                "production_anchor": "Sleeper/engine season projection remains the preseason anchor until a separately validated preseason FIE season model exists.",
                "m5_additions": ["validated weekly production signal when available", "calibrated floor/ceiling", "M3 young-player role evidence", "format-specific utility transform", "league VOR and market edge"],
                "status": "conditional_activation",
            },
        },
        "waiver_integration": {"folds": wrows, "aggregate": wagg, "model_specs": wspec, "status": "conditional_activation"},
        "weekly_integration": {
            "ranking_folds": rank_rows, "ranking_aggregate": rank_agg,
            "risk_calibration_folds": risk_rows, "risk_calibration_aggregate": risk_agg,
            "risk_bands": risk_bands, "status": "conditional_activation",
        },
        "format_strategy": formats,
        "runtime_contract": {
            "player_keys": ["sleeper_id", "canonical_player_id", "full_name"],
            "required_player_fields": ["decision_weekly_projection", "p10", "p90", "activation_eligible", "projection_source"],
            "optional_player_fields": ["fie_weekly_projection", "sleeper_weekly_projection", "waiver_next3_projection", "young_role_probability", "spike_probability", "bust_probability", "confidence"],
            "version_match": "current snapshot m5_build must equal V8.7-M5 and scoring_signature must match the loaded research profile when present",
        },
        "derived_tables": manifest,
        "limitations": [
            "Step 24 season aggregation is conditioned on observed player-week rows and is not presented as a complete preseason games-played/injury model.",
            "Direct Sleeper blend activation remains blocked by M4 unless immutable pregame Sleeper history validates the position-specific blend.",
            "Best Ball validation is player-level spike-week evidence, not a complete historical optimal-lineup roster simulation.",
            "Chopped validation is player-level downside evidence, not a historical guillotine elimination simulation.",
            "Dynasty policy uses validated young-role evidence plus transparent age/future-role transforms; a full multi-year asset-market model remains future work.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE V8.7-M5 decision-policy bundle")
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--m1-bundle", default="data/research/milestone1.json")
    p.add_argument("--m2-bundle", default="data/research/milestone2.json")
    p.add_argument("--m3-bundle", default="data/research/milestone3.json")
    p.add_argument("--m4-bundle", default="data/research/milestone4.json")
    p.add_argument("--output", default="data/research/milestone5.json")
    p.add_argument("--fixture", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv); b = run(args); out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    b = json_safe(b); out.write_text(json.dumps(b, indent=2, allow_nan=False)); print(f"Wrote {out} status={b['status']} steps={b['steps_completed']}")


if __name__ == "__main__":
    main()

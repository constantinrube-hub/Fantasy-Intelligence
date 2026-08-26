#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.6-M4 research pipeline.

Implements roadmap Steps 19-23 on top of Milestones 1-3:
19 Position Production Lab / governance registry,
20 explicit no-activation lock,
21 final position-specific raw-stat forward models,
22 immutable Sleeper benchmark framework,
23 time-safe optimal FIE/Sleeper blending.

M4 remains diagnostic-only. It creates model specifications and evidence, but does
not change the frozen V8.2.2 live Draft/Waiver/Weekly/Trade/Team scoring logic.
"""
from __future__ import annotations

import argparse
import gzip
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
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import (
    CONTROL_BUILD, DEFAULT_PPR, METRIC_CLASS, POSITIONS, SCORING_MAP, BONUS_RULES, LATEST_COMPLETED_SEASON,
    score_rows, first_col,
)
from fie_m2 import FOLDS, add_change_signals, add_competition_features, add_position_shares, add_team_context
from statistical_guardrails import promotion_gate
from fie_m3 import (
    ADV_PREFIX, CORE_SPECIAL, add_fixture_advanced, add_lagged_advanced,
    add_public_enrichment, ensure_core_priors, load_core,
)

RESEARCH_BUILD = "V8.6-M4"
MILESTONE = "M4"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rmse(y, p) -> float:
    return float(math.sqrt(mean_squared_error(y, p)))


def safe_corr(x, y) -> Optional[float]:
    z = pd.DataFrame({"x": pd.to_numeric(pd.Series(x).reset_index(drop=True), errors="coerce"), "y": pd.to_numeric(pd.Series(y).reset_index(drop=True), errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None
    r = spearmanr(z.x, z.y).statistic
    return None if not np.isfinite(r) else float(r)


def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def canonical_scoring(m1: dict) -> dict:
    s = m1.get("scoring", {}).get("settings") or DEFAULT_PPR
    return {str(k): float(v) for k, v in s.items() if isinstance(v, (int, float)) and np.isfinite(float(v))}


def feature_frame(args):
    """Rebuild the time-safe M3 feature frame from the same historical backbone."""
    player, team, identity, m1, m2 = load_core(args)
    player, team = add_team_context(player, team)
    player = add_competition_features(player)
    player = add_position_shares(player)
    if "opportunity_change_score" not in player:
        player = add_change_signals(player)
    if args.fixture:
        enriched, enrichment = add_fixture_advanced(player)
    else:
        enriched, enrichment = add_public_enrichment(player, identity, args.cache_dir, args.seasons)
    enriched = ensure_core_priors(enriched)
    enriched = add_lagged_advanced(enriched, enrichment.get("feature_columns", []))
    # Additional safe lagged families from M2. xFP residual itself is realized, so only lagged history is eligible.
    d = enriched.sort_values(["canonical_player_id", "season", "week"]).copy()
    g = d.groupby(["canonical_player_id", "season"], group_keys=False)
    for c in ["xfp_residual", "opportunity_xfp_realized"]:
        if c in d:
            d[f"{c}_prior4"] = g[c].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(4, min_periods=2).mean())
    if "opportunity_change_score" in d:
        # M2 role-change score includes the just-completed row by design because it predicts future games.
        # For a same-week M4 forecast it must be shifted one full game.
        d["opportunity_change_score_prior1"] = g["opportunity_change_score"].shift(1)
    return d, team, identity, m1, m2, enrichment


# ------------------------- Step 19 governance lab -------------------------

def governance_registry(m1: dict, m2: dict, m3: dict) -> List[dict]:
    stab = {(r.get("position"), r.get("metric")): r for r in m1.get("stability", [])}
    pred = {(r.get("position"), r.get("metric")): r for r in m1.get("predictiveness", [])}
    rows: List[dict] = []
    keys = sorted(set(stab) | set(pred))
    for pos, metric in keys:
        s, p = stab.get((pos, metric), {}), pred.get((pos, metric), {})
        cls = s.get("classification") or p.get("classification") or METRIC_CLASS.get(metric, "unknown")
        stability = s.get("stability_score")
        next3 = p.get("next3_spearman")
        ros = p.get("ros_spearman")
        n = max(int(s.get("week_to_week_n") or 0), int(p.get("next3_n") or 0))
        if cls == "outcome":
            grad = "regression_or_label_only"
        elif cls in {"participation_true_route"} and n == 0:
            grad = "blocked_missing_coverage"
        elif stability is not None and next3 is not None and stability >= .25 and abs(next3) >= .08 and n >= 150:
            grad = "validated_candidate"
        elif n < 75:
            grad = "insufficient_sample"
        else:
            grad = "diagnostic_only"
        rows.append({
            "position": pos, "feature": metric, "family": "M1 opportunity/stability",
            "classification": cls, "stability_score": stability, "stability_label": s.get("stability_label"),
            "next_week_spearman": p.get("next_week_spearman"), "next3_spearman": next3,
            "ros_spearman": ros, "next_season_spearman": p.get("next_season_spearman"),
            "sample": n, "graduation_status": grad, "live_status": "OFF",
        })
    # M2 model families.
    for r in m2.get("regression_validation", []):
        rows.append({"position": r.get("position"), "feature": "xfp_residual_lagged", "family": "M2 regression",
                     "classification": "regression_indicator", "stability_score": None, "next3_spearman": r.get("residual_to_future_change_spearman"),
                     "sample": r.get("n", 0), "graduation_status": r.get("classification", "diagnostic_only"), "live_status": "OFF"})
    for r in m2.get("opportunity_change_validation", []):
        ok = (r.get("signals") or 0) >= 20 and (r.get("signal_increment") or 0) > 0.25
        rows.append({"position": r.get("position"), "feature": "opportunity_change_score", "family": "M2 role change",
                     "classification": "opportunity_change", "stability_score": None, "next3_spearman": r.get("change_to_future_uplift_spearman"),
                     "sample": r.get("n", 0), "graduation_status": "validated_candidate" if ok else "diagnostic_only", "live_status": "OFF"})
    for r in m2.get("competition_validation", {}).get("aggregate", []):
        imp = r.get("incremental_mae_improvement")
        rows.append({"position": r.get("position"), "feature": r.get("component") + "_competition" if r.get("component") else "competition",
                     "family": "M2 teammate competition", "classification": "context_modifier", "stability_score": None,
                     "incremental_mae_improvement": imp, "sample": None,
                     "graduation_status": "validated_candidate" if imp is not None and imp >= .01 else "diagnostic_only", "live_status": "OFF"})
    # M3 advanced families, family-level evidence only; individual raw metrics remain separately visible in coverage.
    for r in m3.get("position_specific", {}).get("aggregate", []):
        rows.append({"position": r.get("position"), "feature": "advanced_position_context", "family": "M3 advanced positional",
                     "classification": "efficiency_context", "stability_score": None,
                     "incremental_mae_improvement": r.get("mean_improvement_vs_m2_xfp"), "sample": r.get("n_test", 0),
                     "graduation_status": r.get("status", "diagnostic_only"), "live_status": "OFF"})
    return rows


def governance_summary(rows: List[dict]) -> dict:
    d = pd.DataFrame(rows)
    if d.empty:
        return {"rows": 0, "validated_candidates": 0, "blocked": 0, "live_on": 0}
    gs = d.graduation_status.astype(str)
    return {
        "rows": int(len(d)), "positions": int(d.position.nunique()),
        "validated_candidates": int(gs.str.contains("validated").sum()),
        "diagnostic_only": int(gs.eq("diagnostic_only").sum()),
        "blocked_or_insufficient": int(gs.str.contains("blocked|insufficient").sum()),
        "live_on": int((d.live_status == "ON").sum()),
    }


# -------------------- Step 21 raw-stat forward models --------------------

RAW_TARGETS: Dict[str, Dict[str, Sequence[str]]] = {
    "QB": {
        "attempts": ["attempts", "passing_attempts"], "completions": ["completions"],
        "passing_yards": ["passing_yards"], "passing_tds": ["passing_tds"], "interceptions": ["interceptions"],
        "carries": ["carries", "rushing_attempts"], "rushing_yards": ["rushing_yards"], "rushing_tds": ["rushing_tds"],
        "fumbles_lost": ["fumbles_lost"],
    },
    "RB": {
        "carries": ["carries", "rushing_attempts"], "rushing_yards": ["rushing_yards"], "rushing_tds": ["rushing_tds"],
        "targets": ["targets"], "receptions": ["receptions"], "receiving_yards": ["receiving_yards"], "receiving_tds": ["receiving_tds"],
        "fumbles_lost": ["fumbles_lost"],
    },
    "WR": {"targets":["targets"],"receptions":["receptions"],"receiving_yards":["receiving_yards"],"receiving_tds":["receiving_tds"],"fumbles_lost":["fumbles_lost"]},
    "TE": {"targets":["targets"],"receptions":["receptions"],"receiving_yards":["receiving_yards"],"receiving_tds":["receiving_tds"],"fumbles_lost":["fumbles_lost"]},
    "EDGE": {"tackles_solo":["tackles_solo","def_tackles_solo"],"tackles_with_assist":["tackles_with_assist","tackles_assists","def_tackles_assist"],"tackles_for_loss":["tackles_for_loss","def_tackles_for_loss"],"def_sacks":["def_sacks","sacks"],"def_qb_hits":["def_qb_hits","qb_hits"],"def_fumbles_forced":["def_fumbles_forced","fumbles_forced"],"def_fumbles":["def_fumbles","fumble_recoveries"],"def_tds":["def_tds","defensive_tds"]},
    "IDL": {"tackles_solo":["tackles_solo","def_tackles_solo"],"tackles_with_assist":["tackles_with_assist","tackles_assists","def_tackles_assist"],"tackles_for_loss":["tackles_for_loss","def_tackles_for_loss"],"def_sacks":["def_sacks","sacks"],"def_qb_hits":["def_qb_hits","qb_hits"],"def_fumbles_forced":["def_fumbles_forced","fumbles_forced"],"def_fumbles":["def_fumbles","fumble_recoveries"],"def_tds":["def_tds","defensive_tds"]},
    "LB": {"tackles_solo":["tackles_solo","def_tackles_solo"],"tackles_with_assist":["tackles_with_assist","tackles_assists","def_tackles_assist"],"tackles_for_loss":["tackles_for_loss","def_tackles_for_loss"],"def_sacks":["def_sacks","sacks"],"def_qb_hits":["def_qb_hits","qb_hits"],"def_interceptions":["def_interceptions","interceptions_defense"],"def_pass_defended":["def_pass_defended","passes_defended"],"def_fumbles_forced":["def_fumbles_forced","fumbles_forced"],"def_fumbles":["def_fumbles","fumble_recoveries"],"def_tds":["def_tds","defensive_tds"]},
    "S": {"tackles_solo":["tackles_solo","def_tackles_solo"],"tackles_with_assist":["tackles_with_assist","tackles_assists","def_tackles_assist"],"tackles_for_loss":["tackles_for_loss","def_tackles_for_loss"],"def_sacks":["def_sacks","sacks"],"def_interceptions":["def_interceptions","interceptions_defense"],"def_pass_defended":["def_pass_defended","passes_defended"],"def_fumbles_forced":["def_fumbles_forced","fumbles_forced"],"def_fumbles":["def_fumbles","fumble_recoveries"],"def_tds":["def_tds","defensive_tds"]},
    "CB": {"tackles_solo":["tackles_solo","def_tackles_solo"],"tackles_with_assist":["tackles_with_assist","tackles_assists","def_tackles_assist"],"tackles_for_loss":["tackles_for_loss","def_tackles_for_loss"],"def_sacks":["def_sacks","sacks"],"def_interceptions":["def_interceptions","interceptions_defense"],"def_pass_defended":["def_pass_defended","passes_defended"],"def_fumbles_forced":["def_fumbles_forced","fumbles_forced"],"def_fumbles":["def_fumbles","fumble_recoveries"],"def_tds":["def_tds","defensive_tds"]},
}


def feature_pool(df: pd.DataFrame, pos: str) -> List[str]:
    candidates = list(CORE_SPECIAL.get(pos, []))
    for raw in ADV_PREFIX.get(pos, []):
        candidates += [raw + "_prior4", raw + "_prior8"]
    candidates += [
        "opportunity_change_score_prior1", "xfp_residual_prior4", "opportunity_xfp_realized_prior4",
        "receiving_competition_index_prior4", "backfield_competition_index_prior4",
        "tackle_competition_index_prior4", "pass_rush_support_index_prior4",
        "opportunity_xfp_pregame",
    ]
    # Add team/opponent pregame context if present.
    candidates += [c for c in df.columns if c.endswith("_prior4_team") or c.startswith("opponent_team_")]
    out = []
    for c in candidates:
        if c in df and c not in out and pd.to_numeric(df[c], errors="coerce").notna().sum() >= 20:
            out.append(c)
    return out


def ridge_pipeline(alpha: float = 10.0) -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)), ("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def resolve_targets(df: pd.DataFrame, pos: str) -> Dict[str, str]:
    out = {}
    for canonical, aliases in RAW_TARGETS.get(pos, {}).items():
        c = first_col(df, aliases)
        if c is not None and pd.to_numeric(df[c], errors="coerce").notna().sum() >= 20:
            out[canonical] = c
    return out


def export_linear_spec(model: Pipeline, features: Sequence[str], canonical_target: str, source_target: str, n_train: int) -> dict:
    imp = model.named_steps["impute"]
    sc = model.named_steps["scale"]
    reg = model.named_steps["ridge"]
    return {
        "target": canonical_target, "source_target": source_target, "algorithm": "median_impute+standardize+ridge",
        "features": list(features), "imputer_medians": [float(x) for x in imp.statistics_],
        "scaler_mean": [float(x) for x in sc.mean_], "scaler_scale": [float(x) if float(x) else 1.0 for x in sc.scale_],
        "coefficients": [float(x) for x in reg.coef_], "intercept": float(reg.intercept_), "n_train": int(n_train),
        "prediction_floor": 0.0,
    }


def predict_raw_models(train: pd.DataFrame, test: pd.DataFrame, pos: str, features: List[str], export_specs=False):
    targets = resolve_targets(train, pos)
    pred = pd.DataFrame(index=test.index)
    specs = []
    target_rows = []
    for canonical, source in targets.items():
        tr = train.dropna(subset=[source]).copy()
        te = test.copy()
        if len(tr) < 40:
            continue
        ytr = pd.to_numeric(tr[source], errors="coerce").to_numpy(float)
        model = ridge_pipeline()
        model.fit(tr[features], ytr)
        p = np.maximum(0.0, model.predict(te[features]))
        pred[canonical] = p
        yte = pd.to_numeric(te[source], errors="coerce")
        mask = yte.notna()
        if mask.sum() >= 8:
            target_rows.append({"target": canonical, "n": int(mask.sum()), "mae": float(mean_absolute_error(yte[mask], p[mask.to_numpy()])), "spearman": safe_corr(p[mask.to_numpy()], yte[mask])})
        if export_specs:
            specs.append(export_linear_spec(model, features, canonical, source, len(tr)))
    return pred, specs, target_rows


def fantasy_from_pred(pred: pd.DataFrame, pos: str, scoring: dict) -> pd.Series:
    if pred.empty:
        return pd.Series(dtype=float)
    z = pred.copy()
    z["position_model"] = pos
    return score_rows(z, scoring)


def final_model_validation(df: pd.DataFrame, scoring: dict) -> Tuple[List[dict], List[dict], pd.DataFrame, dict]:
    fold_rows: List[dict] = []
    target_metrics: List[dict] = []
    coefficient_rows: List[dict] = []
    oos_parts = []
    for train_seasons, test_season in FOLDS:
        for pos in POSITIONS:
            z = df[df.position_model.eq(pos)].copy()
            fs = feature_pool(z, pos)
            if len(fs) < 2:
                continue
            tr = z[z.season.isin(train_seasons)].dropna(subset=["fantasy_points"]).copy()
            te = z[z.season.eq(test_season)].dropna(subset=["fantasy_points"]).copy()
            if len(tr) < 60 or len(te) < 12:
                continue
            pred_stats, fold_specs, tm = predict_raw_models(tr, te, pos, fs, export_specs=True)
            for spec in fold_specs:
                coeffs = list(spec.get("coefficients") or [])
                feats = list(spec.get("features") or [])
                denom = sum(abs(float(x)) for x in coeffs if np.isfinite(float(x))) or 1.0
                for feat, coef in zip(feats, coeffs):
                    c = float(coef)
                    coefficient_rows.append({
                        "position": pos, "target": spec.get("target"), "feature": feat,
                        "test_season": int(test_season), "coefficient": c,
                        "normalized_abs_weight": abs(c) / denom,
                    })
            if pred_stats.empty:
                continue
            fie = fantasy_from_pred(pred_stats, pos, scoring).reindex(te.index)
            y = pd.to_numeric(te.fantasy_points, errors="coerce")
            mask = y.notna() & fie.notna()
            if mask.sum() < 10:
                continue
            base_col = "opportunity_xfp_pregame" if "opportunity_xfp_pregame" in te and pd.to_numeric(te.opportunity_xfp_pregame, errors="coerce").notna().sum() >= 8 else "fp_prior_4"
            base = pd.to_numeric(te[base_col], errors="coerce")
            bmask = mask & base.notna()
            fie_mae = float(mean_absolute_error(y[mask], fie[mask]))
            base_mae = float(mean_absolute_error(y[bmask], base[bmask])) if bmask.sum() >= 8 else None
            fold_rows.append({
                "position": pos, "train_start": min(train_seasons), "train_end": max(train_seasons), "test_season": test_season,
                "n_test": int(mask.sum()), "feature_count": len(fs), "raw_target_count": int(pred_stats.shape[1]),
                "fie_event_mae": fie_mae, "fie_event_rmse": rmse(y[mask], fie[mask]), "fie_event_spearman": safe_corr(fie[mask], y[mask]),
                "baseline": base_col, "baseline_mae": base_mae,
                "mae_improvement_vs_baseline": ((base_mae - fie_mae) / base_mae) if base_mae and base_mae > 0 else None,
                "features": fs, "raw_targets": list(pred_stats.columns),
            })
            for r in tm:
                target_metrics.append({"position": pos, "test_season": test_season, **r})
            q = te.loc[mask, ["season", "week", "canonical_player_id", "full_name", "team", "position_model", "fantasy_points"]].copy()
            q["fie_projection"] = fie[mask].astype(float)
            q["baseline_projection"] = base[mask].astype(float) if base_col in te else np.nan
            oos_parts.append(q)
    agg = []
    f = pd.DataFrame(fold_rows)
    if not f.empty:
        for pos, g in f.groupby("position"):
            inc = pd.to_numeric(g.mae_improvement_vs_baseline, errors="coerce").dropna()
            positive = int((inc > 0).sum())
            mean_inc = float(inc.mean()) if len(inc) else None
            gate = promotion_gate(inc.tolist(), weights=g.loc[inc.index, "n_test"].tolist(), min_mean=.01, min_folds=4, require_positive_ci=True)
            agg.append({
                "position": pos, "folds": int(len(g)), "n_test": int(g.n_test.sum()),
                "mean_fie_event_mae": float(np.average(g.fie_event_mae, weights=g.n_test)),
                "mean_baseline_mae": float(np.average(g.baseline_mae.dropna(), weights=g.loc[g.baseline_mae.notna(), "n_test"])) if g.baseline_mae.notna().any() else None,
                "mean_improvement_vs_baseline": mean_inc, "positive_folds": positive,
                "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"],
                "status": "validated_candidate" if gate["robust"] else "diagnostic_only",
            })
    oos = pd.concat(oos_parts, ignore_index=True) if oos_parts else pd.DataFrame()

    # Coefficient stability is diagnostic only.  Ridge intentionally keeps correlated
    # predictors, so a sign flip is not treated as automatic evidence of uselessness;
    # the table instead shows whether a feature's standardized direction and relative
    # weight are stable across chronological holdouts.  This is a guard against
    # over-interpreting a single good period or one correlated feature family.
    feature_stability = []
    cf = pd.DataFrame(coefficient_rows)
    if not cf.empty:
        for (pos, target, feat), g in cf.groupby(["position", "target", "feature"]):
            co = pd.to_numeric(g.coefficient, errors="coerce").dropna()
            wt = pd.to_numeric(g.normalized_abs_weight, errors="coerce").dropna()
            if co.empty:
                continue
            pos_share = float((co > 0).mean()); neg_share = float((co < 0).mean())
            sign_consistency = max(pos_share, neg_share)
            mean_weight = float(wt.mean()) if len(wt) else 0.0
            if len(co) >= 3 and sign_consistency >= .75 and mean_weight >= .015:
                label = "stable_direction"
            elif mean_weight < .015:
                label = "low_weight"
            else:
                label = "direction_unstable"
            feature_stability.append({
                "position": pos, "target": target, "feature": feat,
                "folds": int(len(co)), "sign_consistency": sign_consistency,
                "positive_share": pos_share, "negative_share": neg_share,
                "mean_normalized_abs_weight": mean_weight,
                "median_coefficient": float(np.median(co)), "classification": label,
                "activation_effect": "diagnostic_only",
            })

    # Train deployable candidate specs on full primary window. They remain OFF until later integration.
    specs = {}
    for pos in POSITIONS:
        z = df[df.position_model.eq(pos)].dropna(subset=["fantasy_points"]).copy()
        fs = feature_pool(z, pos)
        if len(z) < 100 or len(fs) < 2:
            continue
        _, pspecs, _ = predict_raw_models(z, z.iloc[:1].copy(), pos, fs, export_specs=True)
        pos_stability = [r for r in feature_stability if r.get("position") == pos]
        specs[pos] = {"features": fs, "targets": pspecs, "trained_rows": int(len(z)), "feature_stability": pos_stability, "live_status": "OFF"}
    return fold_rows, agg, target_metrics, oos, {"positions": specs, "feature_stability": feature_stability, "coefficient_stability_policy": {"status": "diagnostic_only", "stable_direction_min_folds": 3, "sign_consistency_min": .75, "mean_normalized_abs_weight_min": .015, "reason": "Ridge coefficient direction is monitored across chronological folds but does not independently promote or remove correlated predictors"}, "algorithm": "position-specific ridge raw-stat stack", "live_status": "OFF"}


# ------------------- Steps 22-23 market benchmark/blend ------------------

def score_sleeper_stats(stats: dict, scoring: dict, position: str = "") -> float:
    pts = 0.0
    for key, w in scoring.items():
        try: weight = float(w)
        except Exception: continue
        if not np.isfinite(weight) or weight == 0: continue
        if key in {"bonus_rec_te", "rec_te"}:
            if str(position).upper() == "TE": pts += float(stats.get("rec", 0) or 0) * weight
            continue
        if key in BONUS_RULES:
            field, threshold = BONUS_RULES[key]
            # Sleeper uses abbreviated keys; map the canonical historical field back to its scoring key.
            sk = {"passing_yards":"pass_yd","rushing_yards":"rush_yd","receiving_yards":"rec_yd"}.get(field)
            if sk and float(stats.get(sk, 0) or 0) >= threshold: pts += weight
            continue
        try: pts += float(stats.get(key, 0) or 0) * weight
        except Exception: pass
    return float(pts)


def load_sleeper_market(path: str, scoring: dict, identity: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, dict]:
    root = Path(path)
    sid_map = {}
    if identity is not None and not identity.empty and {"sleeper_id", "canonical_player_id"}.issubset(identity.columns):
        for rr in identity.dropna(subset=["sleeper_id", "canonical_player_id"]).itertuples(index=False):
            sid_map[str(getattr(rr, "sleeper_id"))] = str(getattr(rr, "canonical_player_id"))
    posthoc_mapped = 0
    files = sorted(root.rglob("*.jsonl.gz")) if root.exists() else []
    rows=[]; rejected=0
    timing_rejected_files=0
    for f in files:
        try:
            meta_path=f.with_suffix(f.suffix+".meta.json")
            meta=json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            try: policy_ver=int(meta.get("capture_policy_version") or 0)
            except Exception: policy_ver=0
            try:
                hours=float(meta.get("hours_before_kickoff")); window=float(meta.get("capture_window_hours"))
                timing_ok=0 < hours <= window
            except Exception:
                timing_ok=False
            file_verified=bool(
                meta.get("pregame_eligible") and policy_ver>=2
                and str(meta.get("season_type") or "").lower()=="regular"
                and meta.get("first_kickoff_utc") and timing_ok
            )
            if not file_verified:
                timing_rejected_files += 1
                continue
            with gzip.open(f, "rt", encoding="utf-8") as h:
                for line in h:
                    r=json.loads(line)
                    if not r.get("pregame_eligible", False):
                        rejected += 1; continue
                    stats=r.get("stats") or {}
                    cid = str(r.get("canonical_player_id") or "")
                    if not cid and r.get("sleeper_id") is not None:
                        cid = sid_map.get(str(r.get("sleeper_id")), "")
                        if cid: posthoc_mapped += 1
                    rows.append({
                        "season":int(r["season"]),"week":int(r["week"]),"canonical_player_id":cid,
                        "market_projection":score_sleeper_stats(stats,scoring,str(r.get("position_model") or "")),
                        "provider":"Sleeper","captured_at":r.get("captured_at"),"snapshot_file":str(f),
                    })
        except Exception:
            continue
    d=pd.DataFrame(rows)
    if not d.empty:
        d=d[d.canonical_player_id.ne("")].drop_duplicates(["season","week","canonical_player_id"],keep="first")
    return d,{"files":len(files),"eligible_rows":int(len(d)),"rejected_nonpregame_rows":int(rejected),"timing_rejected_files":int(timing_rejected_files),"capture_policy":"requires sidecar capture_policy_version>=2, regular season, verified first kickoff and 0<hours_before_kickoff<=capture_window_hours","posthoc_identity_mapped_rows":int(posthoc_mapped),"identity_policy":"raw Sleeper IDs may be mapped to canonical IDs at evaluation time without mutating the immutable snapshot"}


def fixture_market(oos: pd.DataFrame) -> pd.DataFrame:
    if oos.empty:return pd.DataFrame()
    rng=np.random.default_rng(223)
    d=oos[["season","week","canonical_player_id","position_model","fantasy_points"]].copy()
    # A plausible but imperfect pregame market baseline, deterministic for CI only.
    shrink=d.groupby("position_model").fantasy_points.transform("mean")
    d["market_projection"]=0.68*pd.to_numeric(d.fantasy_points,errors="coerce")+0.32*shrink+rng.normal(0,2.8,len(d))
    d["provider"]="fixture_sleeper_pregame"; d["captured_at"]="fixture";d["pregame_eligible"]=True
    return d[["season","week","canonical_player_id","market_projection","provider","captured_at"]]


def market_benchmark(oos: pd.DataFrame, market: pd.DataFrame) -> Tuple[List[dict], List[dict], pd.DataFrame]:
    if oos.empty or market.empty:return [],[],pd.DataFrame()
    d=oos.merge(market,on=["season","week","canonical_player_id"],how="inner")
    rows=[]
    for (pos,season),g in d.groupby(["position_model","season"]):
        if len(g)<10:continue
        y=pd.to_numeric(g.fantasy_points,errors="coerce");f=pd.to_numeric(g.fie_projection,errors="coerce");m=pd.to_numeric(g.market_projection,errors="coerce")
        ok=y.notna()&f.notna()&m.notna(); y,f,m=y[ok],f[ok],m[ok]
        if len(y)<10:continue
        fma=float(mean_absolute_error(y,f));mma=float(mean_absolute_error(y,m))
        rows.append({"position":pos,"test_season":int(season),"n":int(len(y)),"fie_mae":fma,"market_mae":mma,
                     "fie_improvement_vs_market":float((mma-fma)/mma) if mma>0 else None,"fie_spearman":safe_corr(f,y),"market_spearman":safe_corr(m,y)})
    agg=[]; q=pd.DataFrame(rows)
    if not q.empty:
        for pos,g in q.groupby("position"):
            imp=pd.to_numeric(g.fie_improvement_vs_market,errors="coerce").dropna()
            agg.append({"position":pos,"folds":int(len(g)),"n":int(g.n.sum()),"mean_fie_mae":float(np.average(g.fie_mae,weights=g.n)),"mean_market_mae":float(np.average(g.market_mae,weights=g.n)),
                        "mean_fie_improvement_vs_market":float(imp.mean()) if len(imp) else None,"fie_wins":int((g.fie_mae<g.market_mae).sum())})
    return rows,agg,d


def best_weight(g: pd.DataFrame) -> Tuple[float, float]:
    y=pd.to_numeric(g.fantasy_points,errors="coerce").to_numpy(float);f=pd.to_numeric(g.fie_projection,errors="coerce").to_numpy(float);m=pd.to_numeric(g.market_projection,errors="coerce").to_numpy(float)
    best=(0.0,float("inf"))
    for w in np.linspace(0,1,21):
        p=w*f+(1-w)*m;ma=float(mean_absolute_error(y,p))
        if ma<best[1]-1e-12:best=(float(round(w,2)),ma)
    return best


def blend_validation(joined: pd.DataFrame) -> Tuple[List[dict], List[dict]]:
    if joined.empty:return [],[]
    rows=[]
    # Weight for year Y is learned ONLY from completed prior holdout years.
    for pos,gp in joined.groupby("position_model"):
        years=sorted(int(x) for x in gp.season.dropna().unique())
        for year in years:
            prior=gp[gp.season<year].dropna(subset=["fantasy_points","fie_projection","market_projection"])
            te=gp[gp.season==year].dropna(subset=["fantasy_points","fie_projection","market_projection"])
            if len(prior)<20 or len(te)<10:continue
            w,train_mae=best_weight(prior)
            y=pd.to_numeric(te.fantasy_points,errors="coerce").to_numpy(float);f=pd.to_numeric(te.fie_projection,errors="coerce").to_numpy(float);m=pd.to_numeric(te.market_projection,errors="coerce").to_numpy(float)
            b=w*f+(1-w)*m; bma=float(mean_absolute_error(y,b));fma=float(mean_absolute_error(y,f));mma=float(mean_absolute_error(y,m))
            rows.append({"position":pos,"test_season":year,"n":int(len(te)),"fie_weight":w,"market_weight":round(1-w,2),"prior_holdout_rows":int(len(prior)),"prior_holdout_mae_at_weight":train_mae,
                         "blend_mae":bma,"fie_mae":fma,"market_mae":mma,"blend_improvement_vs_fie":float((fma-bma)/fma) if fma>0 else None,"blend_improvement_vs_market":float((mma-bma)/mma) if mma>0 else None,"blend_spearman":safe_corr(b,y)})
    agg=[];d=pd.DataFrame(rows)
    if not d.empty:
        for pos,g in d.groupby("position"):
            both=(g.blend_mae<g.fie_mae)&(g.blend_mae<g.market_mae)
            # recommended weight for the next season comes only from all completed joined holdouts.
            allg=joined[joined.position_model.eq(pos)].dropna(subset=["fantasy_points","fie_projection","market_projection"])
            rw,_=best_weight(allg) if len(allg)>=20 else (None,None)
            impf=pd.to_numeric(g.blend_improvement_vs_fie,errors="coerce").dropna(); impm=pd.to_numeric(g.blend_improvement_vs_market,errors="coerce").dropna()
            gate_f=promotion_gate(impf.tolist(),weights=g.loc[impf.index,"n"].tolist(),min_mean=.01,min_folds=3,require_positive_ci=True)
            gate_m=promotion_gate(impm.tolist(),weights=g.loc[impm.index,"n"].tolist(),min_mean=.01,min_folds=3,require_positive_ci=True)
            candidate=int(both.sum())>=max(2,int(math.ceil(len(g)*.67))) and gate_f["robust"] and gate_m["robust"]
            agg.append({"position":pos,"folds":int(len(g)),"n":int(g.n.sum()),"recommended_fie_weight_next":rw,"recommended_market_weight_next":None if rw is None else round(1-rw,2),
                        "mean_blend_improvement_vs_fie":float(impf.mean()) if len(impf) else None,"mean_blend_improvement_vs_market":float(impm.mean()) if len(impm) else None,"blend_wins_both":int(both.sum()),
                        "fie_ci95_low":gate_f["ci95_low"],"fie_ci95_high":gate_f["ci95_high"],"market_ci95_low":gate_m["ci95_low"],"market_ci95_high":gate_m["ci95_high"],
                        "status":"validated_candidate" if candidate else "diagnostic_only","live_status":"OFF"})
    return rows,agg


def write_derived(oos: pd.DataFrame, registry: List[dict], derived_dir: Optional[str]) -> dict:
    if not derived_dir:return {"written":False,"files":{}}
    p=Path(derived_dir);p.mkdir(parents=True,exist_ok=True);files={}
    op=p/"milestone4_oos_predictions.csv.gz";oos.to_csv(op,index=False,compression="gzip");files["milestone4_oos_predictions"]={"path":str(op),"rows":int(len(oos)),"columns":int(len(oos.columns))}
    rg=p/"milestone4_feature_registry.csv.gz";pd.DataFrame(registry).to_csv(rg,index=False,compression="gzip");files["milestone4_feature_registry"]={"path":str(rg),"rows":int(len(registry))}
    return {"written":True,"files":files}


def run(args) -> dict:
    df, team, identity, m1_from_core, m2_from_core, enrichment = feature_frame(args)
    m1=load_json(args.m1_bundle) or m1_from_core
    m2=load_json(args.m2_bundle) or m2_from_core
    m3=load_json(args.m3_bundle)
    scoring=canonical_scoring(m1)

    registry=governance_registry(m1,m2,m3)
    reg_summary=governance_summary(registry)
    folds,agg,target_metrics,oos,model_specs=final_model_validation(df,scoring)

    if args.fixture:
        market=fixture_market(oos); market_meta={"files":1,"eligible_rows":int(len(market)),"rejected_nonpregame_rows":0,"fixture":True}
    else:
        market,market_meta=load_sleeper_market(args.sleeper_archive,scoring,identity)
    mb_rows,mb_agg,joined=market_benchmark(oos,market)
    blend_rows,blend_agg=blend_validation(joined)

    sleeper_ready = len(mb_rows)>0
    benchmark_status = "complete" if sleeper_ready else "blocked_insufficient_immutable_sleeper_history"
    blend_status = "complete" if blend_rows else "blocked_until_prior_sleeper_holdout_history_exists"
    manifest=write_derived(oos,registry,args.derived_dir)

    bundle={
        "schema_version":4,"milestone":MILESTONE,"control_build":CONTROL_BUILD,"research_build":RESEARCH_BUILD,"generated_at":utc_now(),
        "status":"complete","diagnostic_only":True,"steps_completed":[19,20,21,22,23],
        "scoring_signature":m1.get("scoring",{}).get("signature") or m2.get("scoring_signature") or m3.get("scoring_signature"),
        "methodology":{
            "step19":"one governance registry joins stability, forward predictiveness and incremental model evidence; feature graduation and live activation are separate states",
            "step20":"all M1-M4 research features and trained model specifications are hard OFF for live scoring in this milestone",
            "step21":"position-specific models predict raw football stat components from pregame-only features; league scoring is applied after the raw-stat projections; standardized coefficient direction/weight stability is reported across chronological folds before any interpretation",
            "step22":"direct Sleeper comparison accepts only immutable snapshots explicitly marked pregame_eligible; historical Sleeper endpoints are not retrospectively trusted as pregame archives",
            "step23":"blend weight is learned by position on PRIOR completed holdout seasons only, then evaluated on the next holdout season; no same-year weight tuning",
            "time_safe_folds":["2019-2021 -> 2022","2019-2022 -> 2023","2019-2023 -> 2024","2019-2024 -> 2025"],
        },
        "position_production_lab":{"feature_registry":registry,"summary":reg_summary,"advanced_source_coverage":enrichment.get("coverage",{}),"live_activation_count":0},
        "activation_lock":{"enabled":True,"control_build":"V8.2.2","live_model_overrides":[],"trained_model_specs_live_status":"OFF","reason":"Step 20: no M4 signal can influence production rankings before later integration review"},
        "final_position_models":{"folds":folds,"aggregate":agg,"raw_target_metrics":target_metrics,"model_specs":model_specs},
        "sleeper_benchmark":{"status":benchmark_status,"archive":market_meta,"folds":mb_rows,"aggregate":mb_agg,
            "historical_endpoint_policy":"retrospective API responses are not accepted as proof of the pregame projection that existed before kickoff",
            "required_archive":"immutable first-write weekly raw Sleeper projection snapshots with canonical player IDs and pregame_eligible=true"},
        "blend":{"status":blend_status,"folds":blend_rows,"aggregate":blend_agg,"live_status":"OFF"},
        "derived_tables":manifest,
        "limitations":[
            "A direct historical FIE-vs-Sleeper claim is blocked until enough immutable pregame Sleeper snapshots exist. M4 will not backfill them by querying old projection endpoints and pretending those responses are historical snapshots.",
            "The final event stack is deliberately transparent Ridge modelling rather than an opaque high-capacity learner; later model selection can compare richer algorithms under the same folds.",
            "Raw-stat predictions are continuous expectations and can therefore be fractional for count events; league scoring is applied to those expectations after prediction.",
            "Public participation route and pass-rush guardrails from M3 remain in force.",
            "No M4 output changes live Draft, Waiver, Weekly, Trade, Team, Target or Model scores.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Build FIE V8.6-M4 research bundle")
    p.add_argument("--derived-dir",default="data/research/derived")
    p.add_argument("--m1-bundle",default="data/research/milestone1.json")
    p.add_argument("--m2-bundle",default="data/research/milestone2.json")
    p.add_argument("--m3-bundle",default="data/research/milestone3.json")
    p.add_argument("--cache-dir",default=".cache/fie-research")
    p.add_argument("--sleeper-archive",default="data/research/market/sleeper")
    p.add_argument("--output",default="data/research/milestone4.json")
    p.add_argument("--seasons",default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--fixture",action="store_true")
    a=p.parse_args(argv)
    if isinstance(a.seasons,str):
        lo,hi=map(int,a.seasons.split("-"));a.seasons=list(range(lo,hi+1))
    return a


def main(argv=None):
    args=parse_args(argv);b=run(args);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(b,indent=2,allow_nan=False));print(f"Wrote {out} status={b['status']} steps={b['steps_completed']} sleeper={b['sleeper_benchmark']['status']}")


if __name__=="__main__":main()

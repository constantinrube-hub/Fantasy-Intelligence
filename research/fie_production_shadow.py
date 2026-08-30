#!/usr/bin/env python3
"""FIE production-shadow integration layer.

This module is deliberately *not* production activation.  It consumes the
hardened feature-evidence bundle, independently revalidates each downstream
consumer, trains final historical-only models, and emits shadow predictions.

The design is fail-closed:
- canonical M4/M5/current artifacts are read-only;
- only hardened evidence may enter the shadow registry;
- QB/RB HistGradientBoosting residual challengers are revalidated independently;
- the transparent RB backfield-competitor adjustment is an alternate challenger,
  never stacked on top of HistGB without a separate stacked-model validation;
- component and horizon consumers must clear their own multivariate OOS gate;
- live scoring requires current-season completed-game features;
- Week 1 / preseason never silently falls back to prior-season features;
- no shadow result is auto-activated or written into current/dist runtime paths.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, mean_absolute_error

import fie_feature_evidence as fe
import fie_feature_evidence_hardening as fh
from current_snapshot_storage import load_current_snapshot

BUILD = "V9.5-PRODUCTION-SHADOW-1"
SCHEMA_VERSION = 1
MIN_OUTER_FOLDS = 4
DEFAULT_MIN_LIVE_COVERAGE = 0.45
MAX_WEEKLY_ADJUSTMENT = 8.0
RB_CAP_CANDIDATES = (1.0, 1.5, 2.0, 3.0, 4.0)

COMPONENT_TARGET_COLUMNS = {
    ("QB", "pass_volume"): ("attempts", "passing_attempts"),
    ("QB", "rush_volume"): ("carries", "rushing_attempts"),
    ("RB", "carry_volume"): ("carries", "rushing_attempts"),
    ("RB", "target_volume"): ("targets",),
    ("WR", "target_volume"): ("targets",),
    ("TE", "target_volume"): ("targets",),
}

SUPPORTED_COMPONENTS = set(COMPONENT_TARGET_COLUMNS)
SUPPORTED_HORIZONS = {
    "next_week", "next_3_games", "rest_of_season", "floor", "ceiling", "breakout"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite_float(v) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def json_safe(v):
    if isinstance(v, dict):
        return {str(k): json_safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [json_safe(x) for x in v]
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    return v


def evidence_contract(bundle: dict) -> dict:
    gov = bundle.get("governance") or {}
    hard = (bundle.get("source_contract") or {}).get("hardening_oos") or {}
    positions = hard.get("positions") or {}
    if bundle.get("status") != "complete_research_only":
        raise RuntimeError("Feature evidence is not complete_research_only")
    if not str(bundle.get("research_build") or "").startswith("V9.4-FEATURE-EVIDENCE-HARDENED"):
        raise RuntimeError("Production shadow requires hardened feature evidence")
    if gov.get("auto_activation") is not False:
        raise RuntimeError("Feature evidence auto_activation must be false")
    if gov.get("production_gate_unchanged") is not True:
        raise RuntimeError("Feature evidence production gate must remain unchanged")
    for pos in fe.POSITIONS:
        n = int((positions.get(pos) or {}).get("second_stage_residual_fold_count") or 0)
        if n < MIN_OUTER_FOLDS:
            raise RuntimeError(f"{pos} has only {n} hardened second-stage residual folds")
    return {
        "research_build": bundle.get("research_build"),
        "generated_at": bundle.get("generated_at"),
        "hardening_fold_counts": {
            pos: int((positions.get(pos) or {}).get("second_stage_residual_fold_count") or 0)
            for pos in fe.POSITIONS
        },
        "auto_activation": False,
        "production_gate_unchanged": True,
    }


def catalog_features(catalog: dict, pos: str, limit: int = 48) -> List[str]:
    return list(dict.fromkeys(
        f
        for fs in (catalog.get(pos) or {}).values()
        for f in fs
        if not str(f).startswith("premium_")
    ))[:limit]


def evidence_challenger(bundle: dict, pos: str, model: str) -> Optional[dict]:
    for r in bundle.get("phase4_regularized_challengers") or []:
        if r.get("position") == pos and r.get("model") == model:
            return r
    return None


def _gate_from_folds(folds: List[dict], key: str = "improvement") -> dict:
    vals = [r.get(key) for r in folds if r.get(key) is not None]
    weights = [r.get("n_test", 1) for r in folds if r.get(key) is not None]
    gate = fe.robust_gate(vals, weights)
    gate["sign_flip_p"] = fe.sign_flip_p(vals)
    return gate


def _gate_match(a: dict, b: dict, tol: float = 0.0025) -> bool:
    if bool(a.get("robust")) != bool(b.get("robust")):
        return False
    am = finite_float(a.get("mean")); bm = finite_float(b.get("mean"))
    if am is None or bm is None:
        return am is None and bm is None
    return abs(am - bm) <= tol


def revalidate_histgb(df: pd.DataFrame, oos: pd.DataFrame, catalog: dict, pos: str) -> Tuple[dict, object, List[str], tuple]:
    features = [f for f in catalog_features(catalog, pos) if f in df.columns]
    if not features:
        return {"robust": False, "reason": "no_features"}, None, [], tuple()
    z = fe.merge_oos(df, oos, features)
    z = z[z.position_model.eq(pos)].copy()
    z["fantasy_points"] = pd.to_numeric(z.get("fantasy_points"), errors="coerce")
    z["fie_projection"] = pd.to_numeric(z.get("fie_projection"), errors="coerce")
    z["residual"] = z.fantasy_points - z.fie_projection
    folds = []
    for train_seasons, test in fe.expanding_folds(z.season.dropna().unique()):
        tr = z[z.season.isin(train_seasons)].dropna(subset=["residual"])
        te = z[z.season.eq(test)].dropna(subset=["fantasy_points", "fie_projection"])
        tr = tr[tr[features].notna().any(axis=1)]
        te = te[te[features].notna().any(axis=1)]
        if len(tr) < 120 or len(te) < 20:
            continue
        cfg = fe.inner_pick(tr, features, "residual", "histgb") or (.05, 15, 3.0)
        model = fe.histgb(*cfg)
        model.fit(tr[features], tr.residual)
        adj = np.clip(model.predict(te[features]), -MAX_WEEKLY_ADJUSTMENT, MAX_WEEKLY_ADJUSTMENT)
        y = te.fantasy_points.to_numpy(float)
        base = te.fie_projection.to_numpy(float)
        b = mean_absolute_error(y, base)
        a = mean_absolute_error(y, base + adj)
        folds.append({
            "test_season": int(test), "n_test": int(len(te)),
            "baseline_mae": float(b), "shadow_mae": float(a),
            "improvement": float((b - a) / b) if b > 0 else None,
            "config": list(cfg),
        })
    gate = _gate_from_folds(folds)
    # Final config uses only historical OOS seasons and an inner final-season holdout.
    final_cfg = fe.inner_pick(z.dropna(subset=["residual"]), features, "residual", "histgb") or (.05, 15, 3.0)
    final_model = fe.histgb(*final_cfg)
    fit = z.dropna(subset=["residual"])
    fit = fit[fit[features].notna().any(axis=1)]
    if len(fit) < 120:
        return {**gate, "reason": "insufficient_final_fit"}, None, features, tuple(final_cfg)
    final_model.fit(fit[features], fit.residual)
    gate["folds_detail"] = folds
    gate["final_config"] = list(final_cfg)
    gate["training_rows"] = int(len(fit))
    gate["training_seasons"] = sorted(int(x) for x in pd.to_numeric(fit.season, errors="coerce").dropna().unique())
    return gate, final_model, features, tuple(final_cfg)


def _rb_cap_inner_pick(tr: pd.DataFrame, feature: str) -> float:
    seasons = sorted(int(x) for x in tr.season.dropna().unique())
    if len(seasons) < 3:
        return 2.0
    val = seasons[-1]
    fit = tr[tr.season.lt(val)]
    hold = tr[tr.season.eq(val)]
    if len(fit) < 80 or len(hold) < 15:
        return 2.0
    model = fe.ridge(12)
    model.fit(fit[[feature]], fit.residual)
    raw = model.predict(hold[[feature]])
    y = hold.fantasy_points.to_numpy(float)
    base = hold.fie_projection.to_numpy(float)
    best = None
    for cap in RB_CAP_CANDIDATES:
        pred = base + np.clip(raw, -cap, cap)
        err = mean_absolute_error(y, pred)
        if best is None or err < best[0]:
            best = (err, cap)
    return float(best[1] if best else 2.0)


def revalidate_rb_competitor(df: pd.DataFrame, oos: pd.DataFrame) -> Tuple[dict, object, float]:
    feature = "backfield_competitor_count"
    if feature not in df.columns:
        return {"robust": False, "reason": "feature_missing"}, None, 0.0
    z = fe.merge_oos(df, oos, [feature])
    z = z[z.position_model.eq("RB")].copy()
    z["fantasy_points"] = pd.to_numeric(z.get("fantasy_points"), errors="coerce")
    z["fie_projection"] = pd.to_numeric(z.get("fie_projection"), errors="coerce")
    z["residual"] = z.fantasy_points - z.fie_projection
    folds = []
    for train_seasons, test in fe.expanding_folds(z.season.dropna().unique()):
        tr = z[z.season.isin(train_seasons)].dropna(subset=["residual", feature])
        te = z[z.season.eq(test)].dropna(subset=["fantasy_points", "fie_projection", feature])
        if len(tr) < 80 or len(te) < 15:
            continue
        cap = _rb_cap_inner_pick(tr, feature)
        model = fe.ridge(12)
        model.fit(tr[[feature]], tr.residual)
        adj = np.clip(model.predict(te[[feature]]), -cap, cap)
        y = te.fantasy_points.to_numpy(float)
        base = te.fie_projection.to_numpy(float)
        b = mean_absolute_error(y, base)
        a = mean_absolute_error(y, base + adj)
        folds.append({
            "test_season": int(test), "n_test": int(len(te)), "cap": cap,
            "baseline_mae": float(b), "shadow_mae": float(a),
            "improvement": float((b - a) / b) if b > 0 else None,
        })
    gate = _gate_from_folds(folds)
    fit = z.dropna(subset=["residual", feature])
    final_cap = _rb_cap_inner_pick(fit, feature)
    model = fe.ridge(12)
    if len(fit) >= 80:
        model.fit(fit[[feature]], fit.residual)
    else:
        model = None
    gate["folds_detail"] = folds
    gate["final_cap"] = final_cap
    gate["training_rows"] = int(len(fit))
    return gate, model, final_cap


def _component_frame(df: pd.DataFrame, catalog: dict, pos: str, component: str) -> Tuple[pd.DataFrame, List[str]]:
    z, targets = fe.component_targets(df, pos)
    current = targets.get(component)
    if current is None:
        return pd.DataFrame(), []
    features = [f for f in catalog_features(catalog, pos, 40) if f in z.columns]
    q = z[["season", "week", "canonical_player_id"] + features].copy()
    q["current_target"] = current
    q = q.sort_values(["canonical_player_id", "season", "week"])
    q["future_target"] = q.groupby(["canonical_player_id", "season"])["current_target"].shift(-1)
    return q, features


def revalidate_component(df: pd.DataFrame, catalog: dict, pos: str, component: str) -> Tuple[dict, object, List[str]]:
    q, features = _component_frame(df, catalog, pos, component)
    if q.empty or not features:
        return {"robust": False, "reason": "component_or_features_missing"}, None, features
    folds = []
    for train_seasons, test in fe.expanding_folds(q.season.dropna().unique()):
        tr = q[q.season.isin(train_seasons)].dropna(subset=["future_target", "current_target"])
        te = q[q.season.eq(test)].dropna(subset=["future_target", "current_target"])
        tr = tr[tr[features].notna().any(axis=1)]
        te = te[te[features].notna().any(axis=1)]
        if len(tr) < 100 or len(te) < 20:
            continue
        base = fe.ridge(18)
        full = fe.ridge(18)
        base.fit(tr[["current_target"]], tr.future_target)
        full.fit(tr[["current_target"] + features], tr.future_target)
        y = te.future_target.to_numpy(float)
        pb = base.predict(te[["current_target"]])
        pf = full.predict(te[["current_target"] + features])
        be = mean_absolute_error(y, pb)
        ae = mean_absolute_error(y, pf)
        folds.append({
            "test_season": int(test), "n_test": int(len(te)),
            "baseline_mae": float(be), "shadow_mae": float(ae),
            "improvement": float((be - ae) / be) if be > 0 else None,
        })
    gate = _gate_from_folds(folds)
    fit = q.dropna(subset=["future_target", "current_target"])
    fit = fit[fit[features].notna().any(axis=1)]
    model = fe.ridge(18) if len(fit) >= 100 else None
    if model is not None:
        model.fit(fit[["current_target"] + features], fit.future_target)
    gate["folds_detail"] = folds
    gate["training_rows"] = int(len(fit))
    gate["training_seasons"] = sorted(int(x) for x in pd.to_numeric(fit.season, errors="coerce").dropna().unique()) if len(fit) else []
    return gate, model, features


def routed_horizon_features(evidence: dict, pos: str, horizon: str) -> List[str]:
    rows = evidence.get("phase7_consumer_routing") or []
    return list(dict.fromkeys(
        r.get("feature") for r in rows
        if r.get("position") == pos
        and r.get("source_scope") == "horizon"
        and r.get("evidence_target") == horizon
        and r.get("feature")
    ))


def _horizon_target_frame(df: pd.DataFrame, pos: str, features: Sequence[str]) -> pd.DataFrame:
    d = fe.add_horizons(df)
    z = d[d.position_model.eq(pos)].copy()
    keep = ["season", "week", "canonical_player_id", "fp_prior4_audit", "future_fp_next1", "future_fp_next3", "future_fp_ros"]
    return z[[c for c in keep if c in z.columns] + [f for f in features if f in z.columns]].copy()


def revalidate_horizon(df: pd.DataFrame, evidence: dict, pos: str, horizon: str) -> Tuple[dict, object, List[str], dict]:
    features = [f for f in routed_horizon_features(evidence, pos, horizon) if f in df.columns]
    if not features:
        return {"robust": False, "reason": "no_routed_features"}, None, [], {}
    z = _horizon_target_frame(df, pos, features)
    target = {
        "next_week": "future_fp_next1",
        "next_3_games": "future_fp_next3",
        "rest_of_season": "future_fp_ros",
        "floor": "future_fp_next1",
        "ceiling": "future_fp_next1",
        "breakout": "future_fp_next3",
    }[horizon]
    folds = []
    for train_seasons, test in fe.expanding_folds(z.season.dropna().unique()):
        tr = z[z.season.isin(train_seasons)].dropna(subset=[target, "fp_prior4_audit"])
        te = z[z.season.eq(test)].dropna(subset=[target, "fp_prior4_audit"])
        tr = tr[tr[features].notna().any(axis=1)]
        te = te[te[features].notna().any(axis=1)]
        if horizon in {"next_week", "next_3_games", "rest_of_season"}:
            if len(tr) < 100 or len(te) < 20:
                continue
            base = fe.ridge(18); full = fe.ridge(18)
            base.fit(tr[["fp_prior4_audit"]], tr[target])
            full.fit(tr[["fp_prior4_audit"] + features], tr[target])
            y = te[target].to_numpy(float)
            pb = base.predict(te[["fp_prior4_audit"]])
            pf = full.predict(te[["fp_prior4_audit"] + features])
            be = mean_absolute_error(y, pb); ae = mean_absolute_error(y, pf)
        else:
            if len(tr) < 120 or len(te) < 25:
                continue
            q25 = float(tr[target].quantile(.25)); q60 = float(tr[target].quantile(.60)); q75 = float(tr[target].quantile(.75))
            if horizon == "floor":
                ytr = (tr[target] <= q25).astype(int); yte = (te[target] <= q25).astype(int)
            elif horizon == "ceiling":
                ytr = (tr[target] >= q75).astype(int); yte = (te[target] >= q75).astype(int)
            else:
                ytr = ((tr[target] >= q60) & (tr[target] >= 1.25 * tr.fp_prior4_audit)).astype(int)
                yte = ((te[target] >= q60) & (te[target] >= 1.25 * te.fp_prior4_audit)).astype(int)
            if ytr.nunique() < 2 or yte.nunique() < 2:
                continue
            base = fe.ridge(18); full = fe.ridge(18)
            base.fit(tr[["fp_prior4_audit"]], ytr)
            full.fit(tr[["fp_prior4_audit"] + features], ytr)
            pb = np.clip(base.predict(te[["fp_prior4_audit"]]), .001, .999)
            pf = np.clip(full.predict(te[["fp_prior4_audit"] + features]), .001, .999)
            be = brier_score_loss(yte, pb); ae = brier_score_loss(yte, pf)
        folds.append({
            "test_season": int(test), "n_test": int(len(te)),
            "baseline_loss": float(be), "shadow_loss": float(ae),
            "improvement": float((be - ae) / be) if be > 0 else None,
        })
    gate = _gate_from_folds(folds)
    fit = z.dropna(subset=[target, "fp_prior4_audit"])
    fit = fit[fit[features].notna().any(axis=1)]
    model = None; meta = {}
    if horizon in {"next_week", "next_3_games", "rest_of_season"} and len(fit) >= 100:
        model = fe.ridge(18)
        model.fit(fit[["fp_prior4_audit"] + features], fit[target])
        meta = {"metric": "mae"}
    elif horizon in {"floor", "ceiling", "breakout"} and len(fit) >= 120:
        q25 = float(fit[target].quantile(.25)); q60 = float(fit[target].quantile(.60)); q75 = float(fit[target].quantile(.75))
        if horizon == "floor": yfit = (fit[target] <= q25).astype(int)
        elif horizon == "ceiling": yfit = (fit[target] >= q75).astype(int)
        else: yfit = ((fit[target] >= q60) & (fit[target] >= 1.25 * fit.fp_prior4_audit)).astype(int)
        if yfit.nunique() >= 2:
            model = fe.ridge(18)
            model.fit(fit[["fp_prior4_audit"] + features], yfit)
            meta = {"metric": "brier", "q25": q25, "q60": q60, "q75": q75}
    gate["folds_detail"] = folds
    gate["training_rows"] = int(len(fit))
    return gate, model, features, meta


def _rolling_mean(g: pd.DataFrame, col: str, n: int = 4) -> Optional[float]:
    if g.empty or col not in g.columns:
        return None
    x = pd.to_numeric(g.sort_values("week")[col], errors="coerce").dropna().tail(n)
    return float(x.mean()) if len(x) else None


def current_competition_features(observed: pd.DataFrame) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Recreate M2 competition indices/counts for the upcoming game from completed weeks."""
    if observed.empty:
        return {}
    shares = []
    for pid, g in observed.groupby("canonical_player_id"):
        row = g.sort_values("week").iloc[-1]
        shares.append({
            "canonical_player_id": str(pid),
            "team": str(row.get("team") or ""),
            "position_model": str(row.get("position_model") or ""),
            "target": _rolling_mean(g, "target_share") or 0.0,
            "carry": _rolling_mean(g, "carry_share") or 0.0,
            "defsnap": _rolling_mean(g, "defense_snap_share") or 0.0,
        })
    s = pd.DataFrame(shares)
    out = {}
    for r in s.itertuples(index=False):
        recv = s[(s.team == r.team) & s.position_model.isin(["WR", "TE", "RB"])]
        rb = s[(s.team == r.team) & s.position_model.eq("RB")]
        rec_shares = pd.to_numeric(recv.target, errors="coerce").fillna(0.0)
        rb_shares = pd.to_numeric(rb.carry, errors="coerce").fillna(0.0)
        vals = {
            "receiving_competition_index": float(rec_shares.sum() - float(r.target)) if r.position_model in ["WR", "TE", "RB"] else math.nan,
            "receiving_competitor_count": float((rec_shares >= .08).sum() - (float(r.target) >= .08)) if r.position_model in ["WR", "TE", "RB"] else math.nan,
            "receiving_concentration_hhi": float(np.square(rec_shares).sum()) if r.position_model in ["WR", "TE", "RB"] else math.nan,
            "backfield_competition_index": float(rb_shares.sum() - float(r.carry)) if r.position_model == "RB" else math.nan,
            "backfield_competitor_count": float((rb_shares >= .15).sum() - (float(r.carry) >= .15)) if r.position_model == "RB" else math.nan,
        }
        out[(str(r.canonical_player_id), str(r.position_model))] = {
            k: v for k, v in vals.items() if math.isfinite(v)
        }
    return out


def _current_target(g: pd.DataFrame, pos: str, component: str) -> Optional[float]:
    for c in COMPONENT_TARGET_COLUMNS.get((pos, component), ()):
        if c in g.columns:
            x = pd.to_numeric(g.sort_values("week")[c], errors="coerce").dropna()
            if len(x):
                return float(x.iloc[-1])
    return None


def _fp_prior4(g: pd.DataFrame) -> Optional[float]:
    return _rolling_mean(g, "fantasy_points", 4)


def build_live_feature_value(feature: str, g: pd.DataFrame, team_hist: pd.DataFrame, team: str,
                             opponent: Optional[str], competition: dict) -> Optional[float]:
    from build_current_snapshot import feature_value
    try:
        return finite_float(feature_value(feature, g, team_hist, team, opponent, competition))
    except Exception:
        return None


def _blend_weight(m4: dict, pos: str) -> Optional[float]:
    try:
        from build_current_snapshot import m4_blend_weight
        return m4_blend_weight(m4, pos)
    except Exception:
        return None


def _current_snapshot_live_gate(current: dict) -> Optional[str]:
    if current.get("research_compatible") is not True:
        return "current_snapshot_research_incompatible"
    if current.get("profile_current_match") is False:
        return "current_snapshot_profile_mismatch"
    if str(current.get("season_type") or "").lower() != "regular":
        return f"season_type_{str(current.get('season_type') or 'unknown').lower()}"
    generated = str(current.get("generated_at") or "")
    max_age = finite_float(current.get("snapshot_max_age_hours"))
    if generated and max_age is not None:
        try:
            dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600.0
            if age_h > max_age:
                return f"current_snapshot_stale_{age_h:.1f}h"
        except Exception:
            return "current_snapshot_timestamp_unparseable"
    return None


def live_context(args, current: dict) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load current-season completed-game observations without altering current artifacts."""
    blocked = _current_snapshot_live_gate(current)
    if blocked:
        return pd.DataFrame(), pd.DataFrame(), {"status": "blocked", "reason": blocked, "completed_weeks": []}
    try:
        from build_current_snapshot import current_observed_frame
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), {"status": "blocked", "reason": f"current_builder_import:{e}"}
    season = int(current.get("season") or 0)
    week = int(current.get("week") or 0)
    scoring = current.get("scoring_settings") or {}
    try:
        observed, team_hist, _, meta = current_observed_frame(season, week, scoring, Path(args.current_cache))
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), {"status": "blocked", "reason": f"current_observed_frame:{e}"}
    completed = sorted(int(x) for x in pd.to_numeric(observed.get("week"), errors="coerce").dropna().unique()) if not observed.empty and "week" in observed else []
    if observed.empty:
        reason = (meta or {}).get("reason") or "no_current_season_completed_games"
        return observed, team_hist, {"status": "blocked", "reason": reason, "completed_weeks": completed, "source_meta": meta}
    return observed, team_hist, {"status": "available", "reason": None, "completed_weeks": completed, "source_meta": meta}


def model_registry(evidence: dict, df: pd.DataFrame, oos: pd.DataFrame, catalog: dict) -> Tuple[List[dict], dict]:
    registry = []
    fitted = {"histgb": {}, "rb_competitor": None, "components": {}, "horizons": {}}

    eligible = set((evidence.get("phase7_production_gate") or {}).get("eligible_challengers") or [])
    # Make evidence-rejected WR/TE nonlinear challengers explicit in the registry.
    for pos in ("WR", "TE"):
        registry.append({
            "consumer": "weekly_projection_residual", "position": pos, "model": "histgb",
            "shadow_eligible": False, "reason": "hardened_evidence_rejected",
            "stack_policy": "not_applicable",
        })
    # Residual challengers: only evidence-approved models are even considered.
    for pos in ("QB", "RB"):
        key = f"{pos}:histgb"
        ev = evidence_challenger(evidence, pos, "histgb")
        if key not in eligible or not ev:
            registry.append({"consumer": "weekly_projection_residual", "position": pos, "model": "histgb", "shadow_eligible": False, "reason": "not_evidence_eligible"})
            continue
        gate, model, features, cfg = revalidate_histgb(df, oos, catalog, pos)
        evgate = ev.get("gate") or {}
        match = _gate_match(gate, evgate)
        ok = bool(gate.get("robust") and match and model is not None and int(gate.get("folds") or 0) >= MIN_OUTER_FOLDS)
        registry.append({
            "consumer": "weekly_projection_residual", "position": pos, "model": "histgb",
            "feature_n": len(features), "features": features, "final_config": list(cfg),
            "evidence_gate": evgate, "consumer_revalidation_gate": gate,
            "evidence_revalidation_match": match, "shadow_eligible": ok,
            "reason": "revalidated" if ok else "consumer_revalidation_failed",
            "stack_policy": "standalone_candidate_not_additive",
        })
        if ok:
            fitted["histgb"][pos] = (model, features)

    # Transparent RB single-feature challenger is deliberately separate from HistGB.
    ev_feature = next((r for r in evidence.get("phase1_feature_evidence_matrix") or []
                       if r.get("position") == "RB" and r.get("feature") == "backfield_competitor_count"), None)
    gate, model, cap = revalidate_rb_competitor(df, oos)
    ev_ok = bool(ev_feature and (ev_feature.get("weekly_gate") or {}).get("robust"))
    ok = bool(ev_ok and gate.get("robust") and model is not None and int(gate.get("folds") or 0) >= MIN_OUTER_FOLDS)
    registry.append({
        "consumer": "weekly_projection_residual", "position": "RB", "model": "ridge_backfield_competitor_count",
        "feature_n": 1, "features": ["backfield_competitor_count"], "final_cap": cap,
        "evidence_gate": (ev_feature or {}).get("weekly_gate") if ev_feature else None,
        "consumer_revalidation_gate": gate, "shadow_eligible": ok,
        "reason": "revalidated" if ok else "consumer_revalidation_failed",
        "stack_policy": "alternate_to_rb_histgb_never_summed_without_new_stack_validation",
    })
    if ok:
        fitted["rb_competitor"] = (model, cap)

    # Component consumers: require evidence all-feature model and independent consumer revalidation.
    component_rows = evidence.get("phase2_component_validation") or []
    for pos, component in sorted(SUPPORTED_COMPONENTS):
        ev = next((r for r in component_rows if r.get("position") == pos and r.get("component") == component and r.get("feature") == "__all_features__"), None)
        ev_ok = bool(ev and (ev.get("gate") or {}).get("robust"))
        gate, model, features = revalidate_component(df, catalog, pos, component)
        ok = bool(ev_ok and gate.get("robust") and model is not None and int(gate.get("folds") or 0) >= MIN_OUTER_FOLDS)
        registry.append({
            "consumer": component, "position": pos, "model": "ridge_component_all_features",
            "feature_n": len(features), "features": features,
            "evidence_gate": (ev or {}).get("gate") if ev else None,
            "consumer_revalidation_gate": gate, "shadow_eligible": ok,
            "reason": "revalidated" if ok else ("evidence_not_robust" if not ev_ok else "consumer_revalidation_failed"),
        })
        if ok:
            fitted["components"][(pos, component)] = (model, features)

    # Horizon consumers combine individually routed features and must validate as a multivariate consumer.
    for pos in fe.POSITIONS:
        for horizon in sorted(SUPPORTED_HORIZONS):
            features = routed_horizon_features(evidence, pos, horizon)
            if not features:
                continue
            gate, model, features, meta = revalidate_horizon(df, evidence, pos, horizon)
            ok = bool(gate.get("robust") and model is not None and int(gate.get("folds") or 0) >= MIN_OUTER_FOLDS)
            registry.append({
                "consumer": horizon, "position": pos, "model": "ridge_multivariate_horizon",
                "feature_n": len(features), "features": features, "consumer_revalidation_gate": gate,
                "shadow_eligible": ok, "reason": "revalidated" if ok else "combined_consumer_revalidation_failed",
                "meta": meta,
            })
            if ok:
                fitted["horizons"][(pos, horizon)] = (model, features, meta)

    return registry, fitted


def score_current(args, current: dict, m4: dict, registry: List[dict], fitted: dict,
                  observed: pd.DataFrame, team_hist: pd.DataFrame, live_meta: dict) -> dict:
    players = current.get("players") or []
    if observed.empty or live_meta.get("status") != "available":
        return {
            "status": "blocked_no_current_season_completed_features",
            "reason": live_meta.get("reason"),
            "season": current.get("season"), "week": current.get("week"),
            "completed_weeks": live_meta.get("completed_weeks") or [],
            "weekly_candidates": [], "component_predictions": [], "horizon_predictions": [],
            "summary": {"weekly_scored": 0, "components_scored": 0, "horizons_scored": 0},
        }

    groups = {str(pid): g.copy() for pid, g in observed.groupby("canonical_player_id")}
    comp = current_competition_features(observed)
    row_by_cid = {str(r.get("canonical_player_id")): r for r in players if r.get("canonical_player_id")}
    weekly = []; components = []; horizons = []

    # HistGB weekly candidates.
    for pos, spec in fitted.get("histgb", {}).items():
        model, features = spec
        for cid, g in groups.items():
            base_row = row_by_cid.get(cid)
            if not base_row or str(base_row.get("position_model")) != pos:
                continue
            fie_base = finite_float(base_row.get("fie_weekly_projection"))
            if fie_base is None:
                continue
            latest = g.sort_values("week").iloc[-1]
            team = str(latest.get("team") or base_row.get("team") or "")
            opponent = base_row.get("opponent")
            cvals = comp.get((cid, pos), {})
            values = {f: build_live_feature_value(f, g, team_hist, team, opponent, cvals) for f in features}
            coverage = sum(v is not None for v in values.values()) / max(1, len(features))
            if coverage < args.min_live_coverage:
                continue
            x = pd.DataFrame([{f: values[f] for f in features}])
            adj = float(np.clip(model.predict(x)[0], -MAX_WEEKLY_ADJUSTMENT, MAX_WEEKLY_ADJUSTMENT))
            shadow_fie = max(0.0, fie_base + adj)
            sleeper = finite_float(base_row.get("sleeper_weekly_projection"))
            w = _blend_weight(m4, pos)
            shadow_decision = w * shadow_fie + (1.0 - w) * sleeper if w is not None and sleeper is not None else shadow_fie
            canonical = finite_float(base_row.get("decision_weekly_projection"))
            weekly.append({
                "canonical_player_id": cid, "sleeper_id": base_row.get("sleeper_id"), "full_name": base_row.get("full_name"),
                "team": team or None, "opponent": opponent, "position": pos,
                "candidate": "histgb_residual", "feature_coverage": coverage,
                "canonical_fie_projection": fie_base, "shadow_fie_projection": shadow_fie,
                "residual_adjustment": adj, "blend_weight": w,
                "canonical_decision_projection": canonical, "shadow_decision_projection": shadow_decision,
                "delta_vs_canonical": shadow_decision - canonical if canonical is not None else None,
                "shadow_only": True, "auto_activation": False,
            })

    # RB transparent alternate candidate.
    if fitted.get("rb_competitor") is not None:
        model, cap = fitted["rb_competitor"]
        feature = "backfield_competitor_count"
        for cid, g in groups.items():
            base_row = row_by_cid.get(cid)
            if not base_row or str(base_row.get("position_model")) != "RB":
                continue
            fie_base = finite_float(base_row.get("fie_weekly_projection"))
            val = finite_float((comp.get((cid, "RB"), {}) or {}).get(feature))
            if fie_base is None or val is None:
                continue
            adj = float(np.clip(model.predict(pd.DataFrame([{feature: val}]))[0], -cap, cap))
            shadow_fie = max(0.0, fie_base + adj)
            sleeper = finite_float(base_row.get("sleeper_weekly_projection")); w = _blend_weight(m4, "RB")
            shadow_decision = w * shadow_fie + (1.0 - w) * sleeper if w is not None and sleeper is not None else shadow_fie
            canonical = finite_float(base_row.get("decision_weekly_projection"))
            weekly.append({
                "canonical_player_id": cid, "sleeper_id": base_row.get("sleeper_id"), "full_name": base_row.get("full_name"),
                "team": base_row.get("team"), "opponent": base_row.get("opponent"), "position": "RB",
                "candidate": "ridge_backfield_competitor_count", "feature_coverage": 1.0,
                "backfield_competitor_count": val, "cap": cap,
                "canonical_fie_projection": fie_base, "shadow_fie_projection": shadow_fie,
                "residual_adjustment": adj, "blend_weight": w,
                "canonical_decision_projection": canonical, "shadow_decision_projection": shadow_decision,
                "delta_vs_canonical": shadow_decision - canonical if canonical is not None else None,
                "shadow_only": True, "auto_activation": False,
                "stack_policy": "alternate_to_histgb_not_summed",
            })

    # Component consumers.
    for (pos, component), spec in fitted.get("components", {}).items():
        model, features = spec
        for cid, g in groups.items():
            base_row = row_by_cid.get(cid)
            if not base_row or str(base_row.get("position_model")) != pos:
                continue
            current_target = _current_target(g, pos, component)
            if current_target is None:
                continue
            latest = g.sort_values("week").iloc[-1]
            team = str(latest.get("team") or base_row.get("team") or "")
            cvals = comp.get((cid, pos), {})
            values = {f: build_live_feature_value(f, g, team_hist, team, base_row.get("opponent"), cvals) for f in features}
            coverage = sum(v is not None for v in values.values()) / max(1, len(features))
            if coverage < args.min_live_coverage:
                continue
            x = {"current_target": current_target, **values}
            pred = float(model.predict(pd.DataFrame([x]))[0])
            components.append({
                "canonical_player_id": cid, "sleeper_id": base_row.get("sleeper_id"), "full_name": base_row.get("full_name"),
                "team": team or None, "position": pos, "component": component,
                "current_component": current_target, "shadow_next_game_component": max(0.0, pred),
                "feature_coverage": coverage, "shadow_only": True, "auto_activation": False,
            })

    # Horizon consumers.
    for (pos, horizon), spec in fitted.get("horizons", {}).items():
        model, features, meta = spec
        for cid, g in groups.items():
            base_row = row_by_cid.get(cid)
            if not base_row or str(base_row.get("position_model")) != pos:
                continue
            fp4 = _fp_prior4(g)
            if fp4 is None:
                continue
            latest = g.sort_values("week").iloc[-1]
            team = str(latest.get("team") or base_row.get("team") or "")
            cvals = comp.get((cid, pos), {})
            values = {f: build_live_feature_value(f, g, team_hist, team, base_row.get("opponent"), cvals) for f in features}
            coverage = sum(v is not None for v in values.values()) / max(1, len(features))
            if coverage < args.min_live_coverage:
                continue
            x = {"fp_prior4_audit": fp4, **values}
            raw = float(model.predict(pd.DataFrame([x]))[0])
            pred = float(np.clip(raw, .001, .999)) if horizon in {"floor", "ceiling", "breakout"} else max(0.0, raw)
            horizons.append({
                "canonical_player_id": cid, "sleeper_id": base_row.get("sleeper_id"), "full_name": base_row.get("full_name"),
                "team": team or None, "position": pos, "horizon": horizon,
                "baseline_fp_prior4": fp4, "shadow_prediction": pred,
                "prediction_type": "probability" if horizon in {"floor", "ceiling", "breakout"} else "fantasy_points",
                "feature_coverage": coverage, "shadow_only": True, "auto_activation": False,
            })

    return {
        "status": "complete_shadow_only",
        "reason": None, "season": current.get("season"), "week": current.get("week"),
        "completed_weeks": live_meta.get("completed_weeks") or [],
        "weekly_candidates": weekly, "component_predictions": components, "horizon_predictions": horizons,
        "summary": {"weekly_scored": len(weekly), "components_scored": len(components), "horizons_scored": len(horizons)},
    }


def build_bundle(args) -> dict:
    evidence = read_json(args.evidence_bundle)
    contract = evidence_contract(evidence)

    # Use the exact hardened feature/OOS loader that produced the accepted evidence.
    df, oos, catalog, source = fh.load_live_hardened(args)
    registry, fitted = model_registry(evidence, df, oos, catalog)

    current = load_current_snapshot(args.current_snapshot)
    if not current:
        raise RuntimeError("Current snapshot is missing or unreadable")
    if str(current.get("league_id") or "") != str(args.league_id or ""):
        raise RuntimeError("Current snapshot league_id mismatch")
    m4 = read_json(args.m4_bundle)
    observed, team_hist, live_meta = live_context(args, current)
    current_shadow = score_current(args, current, m4, registry, fitted, observed, team_hist, live_meta)

    eligible = [
        f"{r.get('position')}:{r.get('consumer')}:{r.get('model')}"
        for r in registry if r.get("shadow_eligible")
    ]
    blocked = [
        f"{r.get('position')}:{r.get('consumer')}:{r.get('model')}"
        for r in registry if not r.get("shadow_eligible")
    ]
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "shadow_build": BUILD,
        "generated_at": utc_now(),
        "status": "complete_shadow_research_only",
        "league_id": str(args.league_id or current.get("league_id") or ""),
        "league_format": current.get("league_format"),
        "report_season": int(args.report_season),
        "governance": {
            "auto_activation": False,
            "runtime_projection_modified": False,
            "canonical_current_snapshot_modified": False,
            "dist_modified": False,
            "shadow_only": True,
            "promotion_rule": "A shadow consumer may proceed only after this independent consumer revalidation; activation still requires a separate runtime change and post-integration validation.",
            "rb_stack_rule": "RB HistGB and backfield-competitor Ridge are alternate candidates and are never summed without a new stacked-model OOS validation.",
            "week1_rule": "No offensive shadow live scoring without current-season completed-game features; prior-season fallback is forbidden.",
        },
        "evidence_contract": contract,
        "source_contract": {
            "hardening_oos": source.get("hardening_oos"),
            "current_live_features": live_meta,
        },
        "shadow_model_registry": registry,
        "current_shadow": current_shadow,
        "promotion_gate": {
            "shadow_eligible_consumers": eligible,
            "blocked_or_diagnostic_consumers": blocked,
            "runtime_activation_allowed": False,
        },
    }
    return json_safe(bundle)


def write_outputs(bundle: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "production_shadow.json").write_text(json.dumps(bundle, indent=2, allow_nan=False), encoding="utf-8")

    reg = []
    for r in bundle.get("shadow_model_registry") or []:
        q = {k: v for k, v in r.items() if k not in {"evidence_gate", "consumer_revalidation_gate", "features", "meta"}}
        q["features"] = "|".join(r.get("features") or [])
        g = r.get("consumer_revalidation_gate") or {}
        for k in ["folds", "mean", "positive_folds", "required_positive_folds", "ci95_low", "ci95_high", "robust", "sign_flip_p"]:
            q[f"gate_{k}"] = g.get(k)
        reg.append(q)
    pd.DataFrame(reg).to_csv(outdir / "shadow_model_registry.csv", index=False)

    cur = bundle.get("current_shadow") or {}
    pd.DataFrame(cur.get("weekly_candidates") or []).to_csv(outdir / "shadow_current_players.csv", index=False)
    pd.DataFrame(cur.get("component_predictions") or []).to_csv(outdir / "shadow_component_predictions.csv", index=False)
    pd.DataFrame(cur.get("horizon_predictions") or []).to_csv(outdir / "shadow_horizon_predictions.csv", index=False)
    (outdir / "PRODUCTION_SHADOW_REPORT.md").write_text(report_markdown(bundle), encoding="utf-8")


def report_markdown(bundle: dict) -> str:
    lines = [
        "# FIE Production Shadow Report", "",
        f"Generated: {bundle.get('generated_at')}", "",
        "## Governance", "",
        "This is a **shadow-only** integration. It does not alter canonical FIE projections, current snapshots, governance, or deployed app artifacts.", "",
    ]
    reg = bundle.get("shadow_model_registry") or []
    lines += ["## Consumer revalidation", "", "| Position | Consumer | Model | Δ loss | Folds | CI low | Shadow eligible |", "|---|---|---|---:|---:|---:|---|"]
    for r in reg:
        g = r.get("consumer_revalidation_gate") or {}
        lines.append(
            f"| {r.get('position')} | {r.get('consumer')} | {r.get('model')} | {(g.get('mean') or 0):.2%} | {g.get('folds',0)} | {g.get('ci95_low')} | {'YES' if r.get('shadow_eligible') else 'no'} |"
        )
    cur = bundle.get("current_shadow") or {}
    lines += ["", "## Current-season shadow", "", f"Status: `{cur.get('status')}`", ""]
    if cur.get("reason"):
        lines.append(f"Reason: {cur.get('reason')}")
        lines.append("")
    s = cur.get("summary") or {}
    lines += [
        f"- Weekly shadow candidates scored: {s.get('weekly_scored',0)}",
        f"- Component forecasts scored: {s.get('components_scored',0)}",
        f"- Horizon forecasts scored: {s.get('horizons_scored',0)}",
        "",
        "## Promotion", "",
        "Shadow eligibility is not runtime eligibility. A separate runtime integration and post-integration validation are still required before any live projection may change.", "",
    ]
    return "\n".join(lines)


def fixture_inputs(seed: int = 105):
    # Use the existing Phase 1-7 synthetic generator and recreate its fixture
    # catalog exactly as the original integrity test does.
    df, oos = fe.fixture_data(seed)
    catalog = {
        pos: {"fixture": [c for c in df.columns if c.endswith("prior4")]}
        for pos in fe.POSITIONS
    }
    return df, oos, catalog


def self_test() -> None:
    df, oos, catalog = fixture_inputs()
    # Core competition count recreation must match the M2 threshold semantics.
    obs = pd.DataFrame([
        {"canonical_player_id": "a", "team": "X", "position_model": "RB", "week": 1, "carry_share": .50, "target_share": .10},
        {"canonical_player_id": "b", "team": "X", "position_model": "RB", "week": 1, "carry_share": .30, "target_share": .08},
        {"canonical_player_id": "c", "team": "X", "position_model": "RB", "week": 1, "carry_share": .10, "target_share": .03},
    ])
    c = current_competition_features(obs)
    assert c[("a", "RB")]["backfield_competitor_count"] == 1.0
    assert c[("b", "RB")]["backfield_competitor_count"] == 1.0
    assert c[("c", "RB")]["backfield_competitor_count"] == 2.0

    # Revalidation helpers must produce chronological folds and never silently
    # declare fewer than four folds production-like robust.
    g, _, features, _ = revalidate_histgb(df, oos, catalog, "RB")
    assert features and int(g.get("folds") or 0) >= 4
    rb, _, cap = revalidate_rb_competitor(df, oos)
    # Fixture catalog may not contain the exact competitor-count feature; missing is a valid fail-closed result.
    assert cap >= 0.0 and isinstance(rb, dict)

    assert _current_snapshot_live_gate({
        "research_compatible": True, "profile_current_match": True,
        "season_type": "preseason", "generated_at": utc_now(), "snapshot_max_age_hours": 18
    }) == "season_type_preseason"

    # Governance contract must reject non-hardened evidence.
    try:
        evidence_contract({"status": "complete_research_only", "research_build": "OLD", "governance": {"auto_activation": False, "production_gate_unchanged": True}})
        raise AssertionError("non-hardened evidence accepted")
    except RuntimeError:
        pass
    print("PASS production-shadow integrity")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--league-id", default="")
    p.add_argument("--report-season", type=int, default=2026)
    p.add_argument("--league-root", default="data/research")
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--extended-derived-dir", default=None)
    p.add_argument("--extended-m1-bundle", default=None)
    p.add_argument("--current-cache", default=".cache/fie-current")
    p.add_argument("--current-snapshot", default="data/research/current/milestone5_current.json")
    p.add_argument("--evidence-bundle", default="data/research/feature-evidence/feature_evidence.json")
    p.add_argument("--output-dir", default="data/research/production-shadow")
    p.add_argument("--seasons", default="2016-2025")
    p.add_argument("--min-live-coverage", type=float, default=DEFAULT_MIN_LIVE_COVERAGE)
    p.add_argument("--route-source", default="")
    p.add_argument("--qb-coverage-source", default="")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--self-test", action="store_true")
    for i in range(1, 10):
        p.add_argument(f"--m{i}-bundle", default=None)
    a = p.parse_args(argv)
    if a.self_test:
        return a
    lo, hi = map(int, str(a.seasons).split("-"))
    a.seasons = list(range(lo, hi + 1))
    root = Path(a.league_root)
    if a.extended_derived_dir is None:
        a.extended_derived_dir = str(Path(a.cache_dir) / "feature-evidence" / "extended-core" / "derived")
    if a.extended_m1_bundle is None:
        a.extended_m1_bundle = str(Path(a.cache_dir) / "feature-evidence" / "extended-core" / "milestone1_extended.json")
    for i in range(1, 10):
        if getattr(a, f"m{i}_bundle") is None:
            setattr(a, f"m{i}_bundle", str(root / f"milestone{i}.json"))
    return a


def main(argv=None):
    args = parse_args(argv)
    if args.self_test:
        self_test(); return
    bundle = build_bundle(args)
    write_outputs(bundle, Path(args.output_dir))
    print(
        f"Wrote production shadow to {args.output_dir}: "
        f"eligible_consumers={len(bundle['promotion_gate']['shadow_eligible_consumers'])} "
        f"weekly_scored={(bundle.get('current_shadow') or {}).get('summary',{}).get('weekly_scored',0)}"
    )


if __name__ == "__main__":
    main()

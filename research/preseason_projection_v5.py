#!/usr/bin/env python3
"""FIE V9.7.5 chronological QB ensemble + calibration audit.

Research-only.

Consumes the exact-scoring V9.7.4 out-of-fold comparator predictions and tests
whether a chronologically trained blend of:
    V9.7.2 component-first QB model
    exact-scoring historical M9 QB comparator
is more stable than either standalone model.

There is no test-season leakage:
- 2022 uses a predeclared 50/50 blend and no calibration.
- Each later season chooses its blend weight using only earlier OOF seasons.
- Linear intercept/slope calibration can activate only when expanding prior-season
  validation improves MAE without worsening absolute bias.
- The chosen calibration is then refit on all prior OOF rows and applied to the
  next untouched outer season.

No ADP, current market projection, canonical M9, M1, V9.6 runtime, V9.7.2 shadow,
or production artifact is modified.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from statistical_guardrails import promotion_gate
import preseason_projection_v3 as v3

BUILD = "V9.7.5-QB-CHRONOLOGICAL-ENSEMBLE-CALIBRATION-1"
POSITION = "QB"
MIN_FOLDS = 4
MIN_MEAN_IMPROVEMENT = 0.01
WEIGHT_GRID = np.round(np.linspace(0.0, 1.0, 21), 4)
RANK_TOLERANCE = 0.01
SPEARMAN_TOLERANCE = 0.01
TOP12_TOLERANCE = 0.02
BIAS_TOLERANCE = 0.10


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def _finite(x) -> Optional[float]:
    try:
        y = float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def _schedule_games(season: int) -> int:
    return 17 if int(season) >= 2021 else 16


def _mae(y, p) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(y) & np.isfinite(p)
    return float(np.mean(np.abs(y[ok] - p[ok]))) if ok.any() else float("nan")


def _bias(y, p) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(y) & np.isfinite(p)
    return float(np.mean(p[ok] - y[ok])) if ok.any() else float("nan")


def _raw_blend(df: pd.DataFrame, weight_v972: float) -> np.ndarray:
    v = _num(df["v972_pred_ppg"]).to_numpy(float)
    m = _num(df["m9_pred_ppg"]).to_numpy(float)
    return weight_v972 * v + (1.0 - weight_v972) * m


def _choose_weight(prior: pd.DataFrame) -> tuple[float, dict]:
    """Choose blend weight from prior OOF seasons only, minimizing pooled MAE."""
    if prior.empty:
        return 0.5, {
            "status": "predeclared_equal_weight_no_prior_oof_history",
            "n_train": 0,
            "training_seasons": [],
            "training_mae": None,
        }
    y = _num(prior["actual_ppg"]).to_numpy(float)
    candidates = []
    for w in WEIGHT_GRID:
        p = _raw_blend(prior, float(w))
        candidates.append((float(_mae(y, p)), abs(float(w) - 0.5), float(w)))
    candidates = [x for x in candidates if math.isfinite(x[0])]
    if not candidates:
        return 0.5, {
            "status": "predeclared_equal_weight_invalid_prior_oof_history",
            "n_train": int(len(prior)),
            "training_seasons": sorted(int(x) for x in _num(prior.test_season).dropna().unique()),
            "training_mae": None,
        }
    best = sorted(candidates, key=lambda x: (x[0], x[1], x[2]))[0]
    return best[2], {
        "status": "chronological_prior_oof_grid_search",
        "n_train": int(len(prior)),
        "training_seasons": sorted(int(x) for x in _num(prior.test_season).dropna().unique()),
        "training_mae": best[0],
    }


def _fit_linear_calibration(raw: np.ndarray, actual: np.ndarray) -> tuple[float, float]:
    raw = np.asarray(raw, dtype=float)
    actual = np.asarray(actual, dtype=float)
    ok = np.isfinite(raw) & np.isfinite(actual)
    raw, actual = raw[ok], actual[ok]
    if len(raw) < 12 or float(np.nanstd(raw)) < 1e-9:
        return 0.0, 1.0
    X = np.column_stack([np.ones(len(raw)), raw])
    coef, *_ = np.linalg.lstsq(X, actual, rcond=None)
    intercept = float(np.clip(coef[0], -5.0, 5.0))
    slope = float(np.clip(coef[1], 0.50, 1.50))
    return intercept, slope


def _calibration_validation(prior: pd.DataFrame, weight: float) -> dict:
    """Expanding prior-season validation for calibration activation.

    Weight is already a training-stage hyperparameter selected solely from data
    prior to the untouched outer test season. Calibration itself is validated on
    expanding season splits within that prior history.
    """
    seasons = sorted(int(x) for x in _num(prior.test_season).dropna().unique())
    rows = []
    if len(seasons) < 2:
        return {
            "enabled": False,
            "status": "insufficient_prior_seasons_for_expanding_validation",
            "validation_folds": 0,
            "positive_folds": 0,
            "mean_mae_improvement": None,
            "abs_bias_reduction": None,
            "folds": [],
        }
    for val_season in seasons[1:]:
        tr = prior[_num(prior.test_season) < val_season].copy()
        va = prior[_num(prior.test_season) == val_season].copy()
        if len(tr) < 12 or len(va) < 12:
            continue
        tr_raw = _raw_blend(tr, weight)
        va_raw = _raw_blend(va, weight)
        intercept, slope = _fit_linear_calibration(
            tr_raw, _num(tr["actual_ppg"]).to_numpy(float)
        )
        va_cal = np.maximum(0.0, intercept + slope * va_raw)
        y = _num(va["actual_ppg"]).to_numpy(float)
        raw_mae = _mae(y, va_raw)
        cal_mae = _mae(y, va_cal)
        raw_bias = abs(_bias(y, va_raw))
        cal_bias = abs(_bias(y, va_cal))
        imp = (raw_mae - cal_mae) / raw_mae if raw_mae > 0 else None
        rows.append({
            "validation_season": int(val_season),
            "n": int(len(va)),
            "intercept": intercept,
            "slope": slope,
            "raw_mae": raw_mae,
            "calibrated_mae": cal_mae,
            "mae_improvement": imp,
            "raw_abs_bias": raw_bias,
            "calibrated_abs_bias": cal_bias,
        })
    vals = [float(r["mae_improvement"]) for r in rows if r["mae_improvement"] is not None]
    if not vals:
        return {
            "enabled": False,
            "status": "no_valid_expanding_calibration_fold",
            "validation_folds": 0,
            "positive_folds": 0,
            "mean_mae_improvement": None,
            "abs_bias_reduction": None,
            "folds": rows,
        }
    total_n = sum(int(r["n"]) for r in rows)
    weighted_imp = sum(float(r["mae_improvement"]) * int(r["n"]) for r in rows) / total_n
    raw_bias = sum(float(r["raw_abs_bias"]) * int(r["n"]) for r in rows) / total_n
    cal_bias = sum(float(r["calibrated_abs_bias"]) * int(r["n"]) for r in rows) / total_n
    positive = sum(v > 0 for v in vals)
    required_positive = max(1, math.ceil(len(vals) / 2))
    enabled = bool(weighted_imp > 0 and positive >= required_positive and cal_bias <= raw_bias)
    return {
        "enabled": enabled,
        "status": "enabled_after_expanding_validation" if enabled else "rejected_by_expanding_validation",
        "validation_folds": len(vals),
        "positive_folds": positive,
        "required_positive_folds": required_positive,
        "mean_mae_improvement": float(weighted_imp),
        "abs_bias_reduction": float(raw_bias - cal_bias),
        "folds": rows,
    }


def _weighted(folds: list[dict], model: str, metric: str, key: str) -> Optional[float]:
    vals, ws = [], []
    for r in folds:
        v = _finite(((r.get(model) or {}).get(metric) or {}).get(key))
        w = _finite(r.get("n_test"))
        if v is not None:
            vals.append(v)
            ws.append(w if w is not None and w > 0 else 1.0)
    return float(np.average(vals, weights=ws)) if vals else None


def _relative_improvement(challenger: float, baseline: float) -> Optional[float]:
    if challenger is None or baseline is None or baseline <= 0:
        return None
    return float((baseline - challenger) / baseline)


def _gate(folds: list[dict], key: str) -> dict:
    vals = [r.get(key) for r in folds if r.get(key) is not None]
    ws = [r["n_test"] for r in folds if r.get(key) is not None]
    if not vals:
        return {"robust": False, "folds": 0}
    return promotion_gate(
        vals, weights=ws, min_mean=MIN_MEAN_IMPROVEMENT,
        min_folds=MIN_FOLDS, require_positive_ci=True
    )


def _calibration_bins(pred: pd.DataFrame) -> pd.DataFrame:
    out = []
    if pred.empty:
        return pd.DataFrame(columns=[
            "test_season","model","decile","n","mean_prediction","mean_actual","bias"
        ])
    for season, g in pred.groupby("test_season"):
        for model, col in [
            ("ENSEMBLE", "ensemble_pred_ppg"),
            ("V972", "v972_pred_ppg"),
            ("M9", "m9_pred_ppg"),
        ]:
            z = g[["actual_ppg", col]].copy().dropna()
            if z.empty:
                continue
            q = min(10, len(z))
            try:
                z["decile"] = pd.qcut(
                    _num(z[col]).rank(method="first"),
                    q=q, labels=False, duplicates="drop"
                ) + 1
            except Exception:
                z["decile"] = 1
            for d, h in z.groupby("decile"):
                mp = float(_num(h[col]).mean())
                ma = float(_num(h.actual_ppg).mean())
                out.append({
                    "test_season": int(season),
                    "model": model,
                    "decile": int(d),
                    "n": int(len(h)),
                    "mean_prediction": mp,
                    "mean_actual": ma,
                    "bias": mp - ma,
                })
    return pd.DataFrame(out)


def validate_qb_ensemble(v974_report: dict, v974_predictions: pd.DataFrame):
    source = v974_predictions.copy()
    if "metric" in source.columns:
        source = source[source.metric.astype(str).eq("PPG")].copy()
    source = source[source.position.astype(str).eq(POSITION)].copy()
    source["test_season"] = _num(source.test_season)
    source = source[source.test_season.notna()].copy()
    source["test_season"] = source.test_season.astype(int)
    source = source.sort_values(["test_season", "canonical_player_id"]).drop_duplicates(
        ["test_season", "canonical_player_id"], keep="last"
    )
    required = {
        "actual_ppg","v972_pred_ppg","m9_pred_ppg","actual_games","predicted_games",
        "canonical_player_id","test_season"
    }
    if not required.issubset(source.columns):
        raise RuntimeError(f"V9.7.4 predictions missing: {sorted(required-set(source.columns))}")

    v974_qb = ((v974_report.get("per_position") or {}).get("QB") or {})
    exact_v972 = bool(v974_qb.get("all_v972_folds_exact_scoring_replay"))
    exact_m9 = bool(v974_qb.get("all_m9_folds_exact_scoring_replay"))
    prior_status = str(v974_qb.get("v972_prior_gate_status") or "")

    folds = []
    param_rows = []
    prediction_rows = []
    seasons = sorted(int(x) for x in source.test_season.unique())[-MIN_FOLDS:]

    for season in seasons:
        te = source[source.test_season.eq(season)].copy()
        prior = source[source.test_season.lt(season)].copy()
        if len(te) < 12:
            continue
        weight, weight_meta = _choose_weight(prior)
        cal_meta = _calibration_validation(prior, weight)

        if cal_meta["enabled"]:
            raw_prior = _raw_blend(prior, weight)
            intercept, slope = _fit_linear_calibration(
                raw_prior, _num(prior.actual_ppg).to_numpy(float)
            )
        else:
            intercept, slope = 0.0, 1.0

        raw = _raw_blend(te, weight)
        ens = np.maximum(0.0, intercept + slope * raw)
        actual = _num(te.actual_ppg).to_numpy(float)
        vpred = _num(te.v972_pred_ppg).to_numpy(float)
        mpred = _num(te.m9_pred_ppg).to_numpy(float)
        actual_games = _num(te.actual_games).to_numpy(float)
        predicted_games = _num(te.predicted_games).to_numpy(float)
        ok = (
            np.isfinite(actual) & np.isfinite(vpred) & np.isfinite(mpred) &
            np.isfinite(ens) & np.isfinite(actual_games) & (actual_games > 0) &
            np.isfinite(predicted_games) & (predicted_games > 0)
        )
        if int(ok.sum()) < 12:
            continue
        actual, vpred, mpred, ens = actual[ok], vpred[ok], mpred[ok], ens[ok]
        actual_games, predicted_games = actual_games[ok], predicted_games[ok]
        cap = float(_schedule_games(season))
        actual_season = actual * actual_games
        e_season = ens * predicted_games
        v_season = vpred * predicted_games
        m_season = mpred * predicted_games
        actual_full = actual * cap
        e_full = ens * cap
        v_full = vpred * cap
        m_full = mpred * cap

        em = v3._rank_metrics(actual, ens)
        vm = v3._rank_metrics(actual, vpred)
        mm = v3._rank_metrics(actual, mpred)
        esm = v3._rank_metrics(actual_season, e_season)
        vsm = v3._rank_metrics(actual_season, v_season)
        msm = v3._rank_metrics(actual_season, m_season)
        efm = v3._rank_metrics(actual_full, e_full)
        vfm = v3._rank_metrics(actual_full, v_full)
        mfm = v3._rank_metrics(actual_full, m_full)

        rec = {
            "position": POSITION,
            "test_season": int(season),
            "n_test": int(ok.sum()),
            "weight_v972": float(weight),
            "weight_m9": float(1.0-weight),
            "calibration_enabled": bool(cal_meta["enabled"]),
            "calibration_intercept": float(intercept),
            "calibration_slope": float(slope),
            "weight_training": weight_meta,
            "calibration_training_validation": cal_meta,
            "ensemble": {
                "ppg": em, "expected_season": esm, "full_schedule": efm,
            },
            "v972": {
                "ppg": vm, "expected_season": vsm, "full_schedule": vfm,
            },
            "m9": {
                "ppg": mm, "expected_season": msm, "full_schedule": mfm,
            },
            "ppg_mae_improvement_vs_m9": _relative_improvement(em["mae"], mm["mae"]),
            "expected_season_mae_improvement_vs_m9": _relative_improvement(esm["mae"], msm["mae"]),
            "full_schedule_mae_improvement_vs_m9": _relative_improvement(efm["mae"], mfm["mae"]),
            "ppg_mae_improvement_vs_v972": _relative_improvement(em["mae"], vm["mae"]),
            "expected_season_mae_improvement_vs_v972": _relative_improvement(esm["mae"], vsm["mae"]),
            "full_schedule_mae_improvement_vs_v972": _relative_improvement(efm["mae"], vfm["mae"]),
        }
        folds.append(rec)
        param_rows.append({
            "test_season": int(season),
            "n_test": int(ok.sum()),
            "weight_v972": float(weight),
            "weight_m9": float(1-weight),
            "weight_status": weight_meta["status"],
            "weight_training_seasons": ",".join(map(str, weight_meta.get("training_seasons") or [])),
            "calibration_enabled": bool(cal_meta["enabled"]),
            "calibration_status": cal_meta["status"],
            "calibration_validation_folds": int(cal_meta.get("validation_folds") or 0),
            "calibration_validation_mean_mae_improvement": cal_meta.get("mean_mae_improvement"),
            "intercept": float(intercept),
            "slope": float(slope),
        })

        selected = te.loc[te.index[ok]].copy()
        for j, (_, row) in enumerate(selected.iterrows()):
            prediction_rows.append({
                "position": POSITION,
                "test_season": int(season),
                "canonical_player_id": str(row["canonical_player_id"]),
                "full_name": row.get("full_name"),
                "actual_games": float(actual_games[j]),
                "predicted_games": float(predicted_games[j]),
                "actual_ppg": float(actual[j]),
                "v972_pred_ppg": float(vpred[j]),
                "m9_pred_ppg": float(mpred[j]),
                "ensemble_raw_ppg": float(raw[ok][j]),
                "ensemble_pred_ppg": float(ens[j]),
                "actual_season_points": float(actual_season[j]),
                "v972_pred_season_points": float(v_season[j]),
                "m9_pred_season_points": float(m_season[j]),
                "ensemble_pred_season_points": float(e_season[j]),
                "weight_v972": float(weight),
                "calibration_enabled": bool(cal_meta["enabled"]),
                "calibration_intercept": float(intercept),
                "calibration_slope": float(slope),
            })

    if len(folds) < MIN_FOLDS:
        status = "blocked_insufficient_chronological_folds"
    else:
        status = "complete_research_only"

    ppg_gate = _gate(folds, "ppg_mae_improvement_vs_m9")
    season_gate = _gate(folds, "expected_season_mae_improvement_vs_m9")
    full_gate = _gate(folds, "full_schedule_mae_improvement_vs_m9")

    e_ppg = _weighted(folds, "ensemble", "ppg", "mae")
    v_ppg = _weighted(folds, "v972", "ppg", "mae")
    m_ppg = _weighted(folds, "m9", "ppg", "mae")
    e_season = _weighted(folds, "ensemble", "expected_season", "mae")
    v_season = _weighted(folds, "v972", "expected_season", "mae")
    m_season = _weighted(folds, "m9", "expected_season", "mae")
    e_full = _weighted(folds, "ensemble", "full_schedule", "mae")
    v_full = _weighted(folds, "v972", "full_schedule", "mae")
    m_full = _weighted(folds, "m9", "full_schedule", "mae")

    e_rank = _weighted(folds, "ensemble", "ppg", "rank_mae")
    v_rank = _weighted(folds, "v972", "ppg", "rank_mae")
    m_rank = _weighted(folds, "m9", "ppg", "rank_mae")
    e_spear = _weighted(folds, "ensemble", "ppg", "spearman")
    v_spear = _weighted(folds, "v972", "ppg", "spearman")
    m_spear = _weighted(folds, "m9", "ppg", "spearman")
    e_top = _weighted(folds, "ensemble", "ppg", "top12_overlap")
    v_top = _weighted(folds, "v972", "ppg", "top12_overlap")
    m_top = _weighted(folds, "m9", "ppg", "top12_overlap")
    e_bias = _weighted(folds, "ensemble", "ppg", "bias")
    v_bias = _weighted(folds, "v972", "ppg", "bias")
    m_bias = _weighted(folds, "m9", "ppg", "bias")

    best_ppg = min(x for x in [v_ppg, m_ppg] if x is not None)
    best_season = min(x for x in [v_season, m_season] if x is not None)
    best_full = min(x for x in [v_full, m_full] if x is not None)
    best_rank = min(x for x in [v_rank, m_rank] if x is not None)
    best_spear = max(x for x in [v_spear, m_spear] if x is not None)
    best_top = max(x for x in [v_top, m_top] if x is not None)
    best_abs_bias = min(abs(x) for x in [v_bias, m_bias] if x is not None)

    standalone_noninferiority = {
        "ppg_mae_better_or_equal_best_standalone": bool(e_ppg is not None and e_ppg <= best_ppg),
        "expected_season_mae_better_or_equal_best_standalone": bool(e_season is not None and e_season <= best_season),
        "full_schedule_mae_better_or_equal_best_standalone": bool(e_full is not None and e_full <= best_full),
        "rank_mae": bool(e_rank is not None and e_rank <= best_rank * (1+RANK_TOLERANCE)),
        "spearman": bool(e_spear is not None and e_spear >= best_spear - SPEARMAN_TOLERANCE),
        "top12_overlap": bool(e_top is not None and e_top >= best_top - TOP12_TOLERANCE),
        "absolute_calibration_bias": bool(
            e_bias is not None and abs(e_bias) <= best_abs_bias + BIAS_TOLERANCE
        ),
    }

    availability_gate = v974_qb.get("availability_vs_full_schedule_gate") or {"robust": False}
    football_ready = bool(
        status == "complete_research_only"
        and prior_status == "validated_candidate"
        and exact_v972 and exact_m9
        and ppg_gate.get("robust") and full_gate.get("robust")
        and standalone_noninferiority["ppg_mae_better_or_equal_best_standalone"]
        and standalone_noninferiority["full_schedule_mae_better_or_equal_best_standalone"]
        and standalone_noninferiority["rank_mae"]
        and standalone_noninferiority["spearman"]
        and standalone_noninferiority["top12_overlap"]
        and standalone_noninferiority["absolute_calibration_bias"]
    )
    expected_ready = bool(
        football_ready
        and season_gate.get("robust")
        and bool(availability_gate.get("robust"))
        and standalone_noninferiority["expected_season_mae_better_or_equal_best_standalone"]
    )

    report = {
        "build": BUILD,
        "status": status,
        "governance": {
            "auto_activation": False,
            "production_activation": False,
            "production_activation_allowed": False,
            "runtime_projection_modified": False,
            "canonical_m9_modified": False,
            "canonical_m1_modified": False,
            "v972_shadow_modified": False,
            "market_inputs_used": False,
            "adp_inputs_used": False,
            "source_predictions_are_v974_exact_oof": True,
            "chronological_stacking": True,
            "test_season_leakage_allowed": False,
            "statistical_gates_lowered": False,
        },
        "methodology": {
            "position": POSITION,
            "outer_test_seasons": seasons,
            "first_fold_policy": "predeclared_equal_weight_0.5_no_calibration",
            "later_weight_policy": "grid_search_weight_v972_0_to_1_step_0.05_using_only_prior_exact_OOF_seasons",
            "calibration_policy": (
                "intercept+slope clipped to intercept[-5,5], slope[0.5,1.5]; "
                "enabled only when expanding prior-season validation improves MAE "
                "and does not worsen absolute bias"
            ),
            "promotion_baseline": "exact-scoring M9",
            "standalone_safety_boundary": "ensemble aggregate metrics must also be no worse than best standalone where specified",
        },
        "source_v974": {
            "build": v974_report.get("build"),
            "status": v974_report.get("status"),
            "v972_prior_gate_status": prior_status,
            "all_v972_folds_exact_scoring_replay": exact_v972,
            "all_m9_folds_exact_scoring_replay": exact_m9,
            "availability_gate": availability_gate,
        },
        "folds": folds,
        "per_position": {
            "QB": {
                "status": "promotion_review_ready" if football_ready else "diagnostic_only",
                "folds": len(folds),
                "n_test": int(sum(r["n_test"] for r in folds)),
                "ppg_mae_head_to_head_gate_vs_exact_m9": ppg_gate,
                "expected_season_mae_head_to_head_gate_vs_exact_m9": season_gate,
                "full_schedule_mae_head_to_head_gate_vs_exact_m9": full_gate,
                "standalone_noninferiority": standalone_noninferiority,
                "weighted_metrics": {
                    "ensemble_ppg_mae": e_ppg,
                    "v972_ppg_mae": v_ppg,
                    "m9_ppg_mae": m_ppg,
                    "ensemble_expected_season_mae": e_season,
                    "v972_expected_season_mae": v_season,
                    "m9_expected_season_mae": m_season,
                    "ensemble_full_schedule_mae": e_full,
                    "v972_full_schedule_mae": v_full,
                    "m9_full_schedule_mae": m_full,
                    "ensemble_rank_mae": e_rank,
                    "v972_rank_mae": v_rank,
                    "m9_rank_mae": m_rank,
                    "ensemble_spearman": e_spear,
                    "v972_spearman": v_spear,
                    "m9_spearman": m_spear,
                    "ensemble_top12_overlap": e_top,
                    "v972_top12_overlap": v_top,
                    "m9_top12_overlap": m_top,
                    "ensemble_ppg_bias": e_bias,
                    "v972_ppg_bias": v_bias,
                    "m9_ppg_bias": m_bias,
                },
                "football_model_promotion_review_ready": football_ready,
                "expected_season_points_ready": expected_ready,
                "production_activation_allowed": False,
                "market_fallback_replacement_validated": False,
                "reason": None if football_ready else "one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared",
            }
        },
        "football_model_promotion_review_positions": ["QB"] if football_ready else [],
        "expected_season_points_ready_positions": ["QB"] if expected_ready else [],
        "production_activation_allowed": False,
        "replacement_claim_vs_market_fallback": False,
    }
    pred = pd.DataFrame(prediction_rows)
    params = pd.DataFrame(param_rows)
    calibration = _calibration_bins(pred)
    return report, pred, params, calibration


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--v974-json", required=True)
    p.add_argument("--v974-predictions", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument("--predictions-csv", required=True)
    p.add_argument("--params-csv", required=True)
    p.add_argument("--calibration-csv", required=True)
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    v974 = json.loads(Path(a.v974_json).read_text(encoding="utf-8"))
    pred974 = pd.read_csv(a.v974_predictions, low_memory=False)
    report, pred, params, calibration = validate_qb_ensemble(v974, pred974)

    out = Path(a.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pred.to_csv(a.predictions_csv, index=False)
    params.to_csv(a.params_csv, index=False)
    calibration.to_csv(a.calibration_csv, index=False)
    print(json.dumps({
        "build": BUILD,
        "status": report["status"],
        "promotion_review": report["football_model_promotion_review_positions"],
        "expected_points_ready": report["expected_season_points_ready_positions"],
        "weights": params[["test_season","weight_v972","calibration_enabled"]].to_dict("records") if not params.empty else [],
        "production_activation_allowed": False,
    }, indent=2))


if __name__ == "__main__":
    main()

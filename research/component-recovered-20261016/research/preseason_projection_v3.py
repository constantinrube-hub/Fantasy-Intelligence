#!/usr/bin/env python3
"""FIE V9.7.3 preseason head-to-head and calibration validation.

Research-only.  This module compares the V9.7.2 component-first challenger with the
existing M9 preseason football model on the same historical player-season holdouts.
It does NOT use ADP, current Sleeper season projections, or hindsight market data.

The historical M9 consumer can fall back to Sleeper market projections when M9 cannot
replay exact league scoring.  Because verified historical preseason market snapshots
are not generally available, V9.7.3 explicitly does not fabricate that comparison.
Instead it answers the football-model question directly and records the market-fallback
head-to-head as blocked until verified immutable history exists.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import preseason_projection as m9
import preseason_projection_v2 as v2
from statistical_guardrails import promotion_gate

BUILD = "V9.7.3-PRESEASON-HEAD-TO-HEAD-CALIBRATION-1"
POSITIONS = ("QB", "RB", "WR", "TE")
MIN_FOLDS = 4
MIN_MEAN_IMPROVEMENT = 0.01


def _num(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


def _finite(v) -> Optional[float]:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _schedule_games(season: int) -> int:
    # NFL regular-season schedule length is known before the season and is therefore
    # safe to use in a preseason availability model.
    return 17 if int(season) >= 2021 else 16


def _availability_pipeline() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=12.0)),
    ])


def _rank_metrics(actual: np.ndarray, pred: np.ndarray, top_k: int = 12) -> dict:
    a = np.asarray(actual, dtype=float)
    p = np.asarray(pred, dtype=float)
    ok = np.isfinite(a) & np.isfinite(p)
    a, p = a[ok], p[ok]
    if len(a) == 0:
        return {k: None for k in ["mae", "rmse", "bias", "abs_bias", "rank_mae", "spearman", "top12_overlap"]}
    err = p - a
    ar = pd.Series(a).rank(ascending=False, method="average")
    pr = pd.Series(p).rank(ascending=False, method="average")
    spearman = ar.corr(pr)
    k = min(int(top_k), len(a))
    actual_top = set(np.argsort(-a)[:k].tolist())
    pred_top = set(np.argsort(-p)[:k].tolist())
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(np.square(err)))),
        "bias": float(np.mean(err)),
        "abs_bias": float(abs(np.mean(err))),
        "rank_mae": float(np.mean(np.abs(ar.to_numpy(float) - pr.to_numpy(float)))),
        "spearman": float(spearman) if spearman is not None and math.isfinite(float(spearman)) else None,
        "top12_overlap": float(len(actual_top & pred_top) / k) if k else None,
    }


def _relative_improvement(challenger: Optional[float], baseline: Optional[float]) -> Optional[float]:
    if challenger is None or baseline is None or not math.isfinite(baseline) or baseline <= 0:
        return None
    return float((baseline - challenger) / baseline)


def _weighted(records: Sequence[dict], key: str, weight_key: str = "n_test") -> Optional[float]:
    vals, weights = [], []
    for r in records:
        v = _finite(r.get(key)); w = _finite(r.get(weight_key))
        if v is None:
            continue
        vals.append(v); weights.append(w if w is not None and w > 0 else 1.0)
    return float(np.average(vals, weights=weights)) if vals else None


def _add_target_games(trans: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    if trans.empty or profiles.empty:
        out = trans.copy(); out["target_games"] = np.nan; return out
    nxt = profiles[["canonical_player_id", "position_model", "season", "prev_games"]].copy()
    nxt = nxt.rename(columns={"season": "target_season", "prev_games": "target_games"})
    nxt["canonical_player_id"] = nxt.canonical_player_id.astype(str)
    out = trans.copy(); out["canonical_player_id"] = out.canonical_player_id.astype(str)
    return out.merge(nxt, on=["canonical_player_id", "position_model", "target_season"], how="left")


def _predict_games(train: pd.DataFrame, test: pd.DataFrame, test_season: int) -> Tuple[np.ndarray, dict]:
    cap = float(_schedule_games(test_season))
    train = train.copy(); test = test.copy()
    train["target_schedule_games"] = train.target_season.map(_schedule_games).astype(float)
    test["target_schedule_games"] = float(cap)
    features = []
    for f in ["prev_games", "age", "years_exp", "target_schedule_games"]:
        if f in train.columns and _num(train[f]).notna().sum() >= 20:
            features.append(f)
    y = _num(train.get("target_games", pd.Series(np.nan, index=train.index)))
    ok = y.notna()
    if len(features) < 2 or int(ok.sum()) < 60:
        fallback = np.clip(_num(test.get("prev_games", pd.Series(cap, index=test.index))).fillna(cap).to_numpy(float), 1.0, cap)
        return fallback, {"status": "fallback_prior_games", "features": ["prev_games"], "n_train": int(ok.sum())}
    model = _availability_pipeline(); model.fit(train.loc[ok, features], y.loc[ok])
    pred = np.clip(model.predict(test[features]), 1.0, cap)
    return pred, {"status": "ridge", "features": features, "n_train": int(ok.sum())}


def _v972_fold(z: pd.DataFrame, pos: str, test_season: int, scoring: dict, common_ids: Sequence[str]) -> dict:
    tr = z[z.target_season < test_season].copy()
    te = z[z.target_season == test_season].copy()
    te["canonical_player_id"] = te.canonical_player_id.astype(str)
    te = te.drop_duplicates("canonical_player_id", keep="last").set_index("canonical_player_id").reindex(common_ids).reset_index()
    targets = [t for t in v2.RAW_TARGETS[pos] if f"target__{t}" in z and _num(z[f"target__{t}"]).notna().sum() >= 40]
    pred_stats, usable = {}, []
    for target in targets:
        ycol = f"target__{target}"; pcol = f"prev__{target}"
        fs = v2._features(tr, pos, target)
        train_ok = _num(tr[ycol]).notna()
        if len(fs) < 2 or int(train_ok.sum()) < 45:
            continue
        model = v2._pipeline(); model.fit(tr.loc[train_ok, fs], _num(tr.loc[train_ok, ycol]))
        pred_stats[target] = np.maximum(0.0, model.predict(te[fs])); usable.append(target)
    if not usable:
        return {"status": "blocked_no_usable_targets"}
    audit = v2._position_scoring_audit(usable, pos, scoring)
    pred = v2._score(pred_stats, pos, scoring, len(te))
    actual_stats = {t: _num(te[f"target__{t}"]).to_numpy(float) for t in usable}
    actual = v2._score(actual_stats, pos, scoring, len(te))
    return {"status": "ok", "pred": pred, "actual": actual, "te": te, "targets": usable, "audit": audit, "train": tr}


def _m9_fold(player_week: pd.DataFrame, pos: str, test_season: int, scoring: dict, common_ids: Sequence[str]) -> dict:
    trans, features, targets = m9.build_transition_table(player_week, pos)
    if trans.empty:
        return {"status": "blocked_empty_transition"}
    trans["canonical_player_id"] = trans.canonical_player_id.astype(str)
    trans = trans[(_num(trans.prev_games) >= 3) & _num(trans.target_fantasy_ppg).notna()].copy()
    tr = trans[trans.target_season < test_season].copy()
    te = trans[trans.target_season == test_season].copy()
    te = te.drop_duplicates("canonical_player_id", keep="last").set_index("canonical_player_id").reindex(common_ids).reset_index()
    pred_stats, usable = {}, []
    for canonical in targets:
        ycol = f"target__{canonical}"; pcol = f"prev__{canonical}"
        if ycol not in tr.columns or pcol not in tr.columns or _num(tr[ycol]).notna().sum() < 40:
            continue
        fs = list(dict.fromkeys(["prev_fantasy_ppg", pcol] + [f for f in features if f in tr.columns]))
        train_ok = _num(tr[ycol]).notna()
        if len(fs) < 2 or int(train_ok.sum()) < 45:
            continue
        model = m9._model(); model.fit(tr.loc[train_ok, fs], _num(tr.loc[train_ok, ycol]))
        pred_stats[canonical] = np.maximum(0.0, model.predict(te[fs])); usable.append(canonical)
    if not usable:
        return {"status": "blocked_no_usable_targets"}
    pred = m9._score_stat_frame(pred_stats, pos, scoring, len(te))
    audit = v2._position_scoring_audit(usable, pos, scoring)
    return {"status": "ok", "pred": pred, "te": te, "targets": usable, "audit": audit, "train": tr}


def _calibration_bins(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    if rows.empty:
        return pd.DataFrame(columns=["position", "test_season", "metric", "model", "decile", "n", "mean_prediction", "mean_actual", "bias"])
    for (pos, season, metric), g in rows.groupby(["position", "test_season", "metric"], dropna=False):
        actual_col = "actual_ppg" if metric == "PPG" else "actual_season_points"
        for model, pred_col in [("V972", "v972_pred_ppg" if metric == "PPG" else "v972_pred_season_points"),
                                ("M9", "m9_pred_ppg" if metric == "PPG" else "m9_pred_season_points")]:
            z = g[[actual_col, pred_col]].copy()
            z[actual_col] = _num(z[actual_col]); z[pred_col] = _num(z[pred_col]); z = z.dropna()
            if z.empty:
                continue
            q = min(10, len(z))
            try:
                z["decile"] = pd.qcut(z[pred_col].rank(method="first"), q=q, labels=False, duplicates="drop") + 1
            except Exception:
                z["decile"] = 1
            for decile, h in z.groupby("decile"):
                mp = float(h[pred_col].mean()); ma = float(h[actual_col].mean())
                out.append({"position": str(pos), "test_season": int(season), "metric": metric, "model": model,
                            "decile": int(decile), "n": int(len(h)), "mean_prediction": mp, "mean_actual": ma,
                            "bias": float(mp - ma)})
    return pd.DataFrame(out)


def validate_preseason_head_to_head(
    player_week: pd.DataFrame,
    scoring: dict,
    identity: Optional[pd.DataFrame] = None,
    v972_result: Optional[dict] = None,
    positions: Iterable[str] = POSITIONS,
) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Chronological V9.7.2 vs M9 football-model comparison on identical players."""
    positions = tuple(str(p).upper() for p in positions)
    profiles = v2.build_season_profiles(player_week, identity)
    trans_v2 = _add_target_games(v2.transition_panel(profiles), profiles)
    if v972_result is None:
        v972_result = v2.validate_component_preseason(player_week, scoring, identity)

    report = {
        "build": BUILD,
        "status": "complete_research_only",
        "governance": {
            "auto_activation": False,
            "production_activation": False,
            "runtime_projection_modified": False,
            "canonical_m9_modified": False,
            "market_inputs_used": False,
            "adp_inputs_used": False,
            "head_to_head_same_player_holdouts": True,
            "requires_four_chronological_folds": True,
        },
        "comparison": {
            "challenger": "V9.7.2 component-first preseason football model",
            "baseline": "M9 preseason football model",
            "market_fallback_head_to_head": {
                "status": "blocked_insufficient_verified_historical_market",
                "reason": "Historical M9 MARKET_FALLBACK cannot be reconstructed without immutable verified preseason market snapshots; no hindsight market proxy is permitted.",
            },
            "availability_model": "same fold-trained games model applied to both football models",
            "season_total_semantics": "predicted fantasy PPG multiplied by identical pre-season expected-games prediction",
        },
        "per_position": {},
        "folds": [],
        "football_model_promotion_review_positions": [],
        "expected_season_points_ready_positions": [],
        "production_activation_allowed": False,
        "replacement_claim_vs_market_fallback": False,
    }
    prediction_rows = []

    for pos in positions:
        z = trans_v2[(trans_v2.position_model.astype(str) == pos) & (_num(trans_v2.prev_games) >= 3)].copy()
        if z.empty:
            report["per_position"][pos] = {"status": "blocked_no_transition_data", "football_model_promotion_review_ready": False}
            continue
        v2_seasons = sorted(int(x) for x in _num(z.target_season).dropna().unique())
        m9_trans, _, _ = m9.build_transition_table(player_week, pos)
        if m9_trans.empty:
            report["per_position"][pos] = {"status": "blocked_no_m9_transition_data", "football_model_promotion_review_ready": False}
            continue
        m9_seasons = set(int(x) for x in _num(m9_trans.target_season).dropna().unique())
        test_seasons = [s for s in v2_seasons if s in m9_seasons][-MIN_FOLDS:]
        folds = []

        for test_season in test_seasons:
            v2_test = z[z.target_season == test_season].copy(); v2_test["canonical_player_id"] = v2_test.canonical_player_id.astype(str)
            m9_test = m9_trans[(m9_trans.target_season == test_season) & (_num(m9_trans.prev_games) >= 3) & _num(m9_trans.target_fantasy_ppg).notna()].copy()
            m9_test["canonical_player_id"] = m9_test.canonical_player_id.astype(str)
            # Compare only players who genuinely satisfy both model families' holdout
            # eligibility. Reindexing must never manufacture an all-missing M9 row.
            common_ids = sorted(set(v2_test.canonical_player_id) & set(m9_test.canonical_player_id))
            if len(common_ids) < 12:
                continue
            a = _v972_fold(z, pos, test_season, scoring, common_ids)
            b = _m9_fold(player_week, pos, test_season, scoring, common_ids)
            if a.get("status") != "ok" or b.get("status") != "ok":
                continue
            te = a["te"].copy(); te["canonical_player_id"] = te.canonical_player_id.astype(str)
            # Both model arrays already follow common_ids because each test frame was reindexed.
            actual = np.asarray(a["actual"], dtype=float)
            vpred = np.asarray(a["pred"], dtype=float)
            mpred = np.asarray(b["pred"], dtype=float)
            target_games = _num(te.get("target_games", pd.Series(np.nan, index=te.index))).to_numpy(float)
            games_pred, games_meta = _predict_games(a["train"], te, test_season)
            cap = float(_schedule_games(test_season))
            ok = np.isfinite(actual) & np.isfinite(vpred) & np.isfinite(mpred) & np.isfinite(target_games) & (target_games > 0)
            if int(ok.sum()) < 12:
                continue
            ids = np.asarray(common_ids, dtype=object)[ok]
            actual, vpred, mpred = actual[ok], vpred[ok], mpred[ok]
            target_games, games_pred = target_games[ok], games_pred[ok]
            actual_season = actual * target_games
            v_season = vpred * games_pred
            m_season = mpred * games_pred
            actual_full = actual * cap
            v_full = vpred * cap; m_full = mpred * cap

            v_ppg_m = _rank_metrics(actual, vpred); m_ppg_m = _rank_metrics(actual, mpred)
            v_season_m = _rank_metrics(actual_season, v_season); m_season_m = _rank_metrics(actual_season, m_season)
            # Full-schedule-normalized totals isolate football point calibration from
            # availability. Expected-season totals below separately test missed games.
            v_full_m = _rank_metrics(actual_full, v_full); m_full_m = _rank_metrics(actual_full, m_full)
            availability_mae = float(np.mean(np.abs(games_pred - target_games)))
            full_games_mae = float(np.mean(np.abs(cap - target_games)))
            fold = {
                "position": pos, "test_season": int(test_season), "n_test": int(len(actual)),
                "v972_exact_scoring_replay": bool(a["audit"].get("exact_replay_eligible")),
                "m9_exact_scoring_replay": bool(b["audit"].get("exact_replay_eligible")),
                "v972_targets": list(a["targets"]), "m9_targets": list(b["targets"]),
                "v972_ppg": v_ppg_m, "m9_ppg": m_ppg_m,
                "v972_expected_season": v_season_m, "m9_expected_season": m_season_m,
                "v972_full_schedule_season": v_full_m, "m9_full_schedule_season": m_full_m,
                "ppg_mae_improvement_vs_m9": _relative_improvement(v_ppg_m["mae"], m_ppg_m["mae"]),
                "expected_season_mae_improvement_vs_m9": _relative_improvement(v_season_m["mae"], m_season_m["mae"]),
                "full_schedule_mae_improvement_vs_m9": _relative_improvement(v_full_m["mae"], m_full_m["mae"]),
                "rank_mae_improvement_vs_m9": _relative_improvement(v_ppg_m["rank_mae"], m_ppg_m["rank_mae"]),
                "spearman_delta_vs_m9": (v_ppg_m["spearman"] - m_ppg_m["spearman"]) if v_ppg_m["spearman"] is not None and m_ppg_m["spearman"] is not None else None,
                "top12_overlap_delta_vs_m9": (v_ppg_m["top12_overlap"] - m_ppg_m["top12_overlap"]) if v_ppg_m["top12_overlap"] is not None and m_ppg_m["top12_overlap"] is not None else None,
                "abs_bias_reduction_ppg": (m_ppg_m["abs_bias"] - v_ppg_m["abs_bias"]) if v_ppg_m["abs_bias"] is not None and m_ppg_m["abs_bias"] is not None else None,
                "availability_model": games_meta,
                "availability_games_mae": availability_mae,
                "full_schedule_games_mae": full_games_mae,
                "availability_mae_improvement_vs_full_schedule": _relative_improvement(availability_mae, full_games_mae),
            }
            folds.append(fold); report["folds"].append(fold)

            names = te.get("full_name", pd.Series([None] * len(te))).to_numpy(object)[ok] if "full_name" in te else np.asarray([None] * len(actual), dtype=object)
            for i, pid in enumerate(ids):
                base = {
                    "position": pos, "test_season": int(test_season), "canonical_player_id": str(pid),
                    "full_name": names[i] if i < len(names) else None,
                    "actual_games": float(target_games[i]), "predicted_games": float(games_pred[i]),
                    "actual_ppg": float(actual[i]), "v972_pred_ppg": float(vpred[i]), "m9_pred_ppg": float(mpred[i]),
                    "actual_season_points": float(actual_season[i]), "v972_pred_season_points": float(v_season[i]), "m9_pred_season_points": float(m_season[i]),
                    "actual_full_schedule_points": float(actual_full[i]),
                    "v972_full_schedule_points": float(v_full[i]), "m9_full_schedule_points": float(m_full[i]),
                }
                prediction_rows.append({**base, "metric": "PPG"})
                prediction_rows.append({**base, "metric": "SEASON"})

        if not folds:
            report["per_position"][pos] = {"status": "blocked_no_valid_common_folds", "football_model_promotion_review_ready": False}
            continue

        weights = [r["n_test"] for r in folds]
        ppg_vals = [r["ppg_mae_improvement_vs_m9"] for r in folds if r.get("ppg_mae_improvement_vs_m9") is not None]
        ppg_w = [r["n_test"] for r in folds if r.get("ppg_mae_improvement_vs_m9") is not None]
        season_vals = [r["expected_season_mae_improvement_vs_m9"] for r in folds if r.get("expected_season_mae_improvement_vs_m9") is not None]
        season_w = [r["n_test"] for r in folds if r.get("expected_season_mae_improvement_vs_m9") is not None]
        full_vals = [r["full_schedule_mae_improvement_vs_m9"] for r in folds if r.get("full_schedule_mae_improvement_vs_m9") is not None]
        full_w = [r["n_test"] for r in folds if r.get("full_schedule_mae_improvement_vs_m9") is not None]
        avail_vals = [r["availability_mae_improvement_vs_full_schedule"] for r in folds if r.get("availability_mae_improvement_vs_full_schedule") is not None]
        avail_w = [r["n_test"] for r in folds if r.get("availability_mae_improvement_vs_full_schedule") is not None]
        ppg_gate = promotion_gate(ppg_vals, weights=ppg_w, min_mean=MIN_MEAN_IMPROVEMENT, min_folds=MIN_FOLDS, require_positive_ci=True) if ppg_vals else {"robust": False}
        season_gate = promotion_gate(season_vals, weights=season_w, min_mean=MIN_MEAN_IMPROVEMENT, min_folds=MIN_FOLDS, require_positive_ci=True) if season_vals else {"robust": False}
        full_gate = promotion_gate(full_vals, weights=full_w, min_mean=MIN_MEAN_IMPROVEMENT, min_folds=MIN_FOLDS, require_positive_ci=True) if full_vals else {"robust": False}
        availability_gate = promotion_gate(avail_vals, weights=avail_w, min_mean=0.0, min_folds=MIN_FOLDS, require_positive_ci=False) if avail_vals else {"robust": False}

        v2_status = str(((v972_result.get("per_position") or {}).get(pos) or {}).get("status") or "")
        all_v2_exact = len(folds) >= MIN_FOLDS and all(bool(r.get("v972_exact_scoring_replay")) for r in folds)
        v_rank = _weighted(folds, "v972_ppg.rank_mae") if False else None
        # Nested metric aggregates are explicit to avoid ambiguous dataframe flattening.
        def nested(model: str, metric: str, key: str) -> Optional[float]:
            vals, ws = [], []
            for r in folds:
                v = _finite((r.get(f"{model}_{metric}") or {}).get(key)); w = _finite(r.get("n_test"))
                if v is not None:
                    vals.append(v); ws.append(w if w is not None and w > 0 else 1.0)
            return float(np.average(vals, weights=ws)) if vals else None

        v_rank = nested("v972", "ppg", "rank_mae"); m_rank = nested("m9", "ppg", "rank_mae")
        v_spear = nested("v972", "ppg", "spearman"); m_spear = nested("m9", "ppg", "spearman")
        v_top = nested("v972", "ppg", "top12_overlap"); m_top = nested("m9", "ppg", "top12_overlap")
        v_bias = nested("v972", "ppg", "bias"); m_bias = nested("m9", "ppg", "bias")
        rank_noninferior = v_rank is not None and m_rank is not None and v_rank <= m_rank * 1.01
        spearman_noninferior = v_spear is not None and m_spear is not None and v_spear >= m_spear - 0.01
        top12_noninferior = v_top is not None and m_top is not None and v_top >= m_top - 0.02
        calibration_noninferior = v_bias is not None and m_bias is not None and abs(v_bias) <= abs(m_bias) + 0.10

        football_ready = bool(
            v2_status == "validated_candidate" and len(folds) >= MIN_FOLDS and all_v2_exact
            and ppg_gate.get("robust") and full_gate.get("robust")
            and rank_noninferior and spearman_noninferior and top12_noninferior and calibration_noninferior
        )
        expected_points_ready = bool(football_ready and season_gate.get("robust") and availability_gate.get("robust"))
        status = "promotion_review_ready" if football_ready else "diagnostic_only"
        agg = {
            "status": status,
            "folds": int(len(folds)), "n_test": int(sum(weights)),
            "v972_prior_gate_status": v2_status,
            "all_v972_folds_exact_scoring_replay": bool(all_v2_exact),
            "all_m9_folds_exact_scoring_replay": bool(len(folds) >= MIN_FOLDS and all(bool(r.get("m9_exact_scoring_replay")) for r in folds)),
            "ppg_mae_head_to_head_gate": ppg_gate,
            "expected_season_mae_head_to_head_gate": season_gate,
            "full_schedule_mae_head_to_head_gate": full_gate,
            "availability_vs_full_schedule_gate": availability_gate,
            "weighted_metrics": {
                "v972_ppg_mae": nested("v972", "ppg", "mae"), "m9_ppg_mae": nested("m9", "ppg", "mae"),
                "v972_ppg_rmse": nested("v972", "ppg", "rmse"), "m9_ppg_rmse": nested("m9", "ppg", "rmse"),
                "v972_ppg_bias": v_bias, "m9_ppg_bias": m_bias,
                "v972_rank_mae": v_rank, "m9_rank_mae": m_rank,
                "v972_spearman": v_spear, "m9_spearman": m_spear,
                "v972_top12_overlap": v_top, "m9_top12_overlap": m_top,
                "v972_expected_season_mae": nested("v972", "expected_season", "mae"), "m9_expected_season_mae": nested("m9", "expected_season", "mae"),
                "v972_full_schedule_mae": nested("v972", "full_schedule_season", "mae"), "m9_full_schedule_mae": nested("m9", "full_schedule_season", "mae"),
            },
            "noninferiority": {
                "rank_mae": bool(rank_noninferior), "spearman": bool(spearman_noninferior),
                "top12_overlap": bool(top12_noninferior), "absolute_calibration_bias": bool(calibration_noninferior),
                "tolerances": {"rank_mae_relative": 0.01, "spearman_absolute": 0.01, "top12_overlap_absolute": 0.02, "ppg_bias_absolute": 0.10},
            },
            "football_model_promotion_review_ready": football_ready,
            "expected_season_points_ready": expected_points_ready,
            "market_fallback_replacement_validated": False,
            "reason": None if football_ready else "one_or_more_head_to_head_or_noninferiority_gates_not_cleared",
        }
        report["per_position"][pos] = agg
        if football_ready:
            report["football_model_promotion_review_positions"].append(pos)
        if expected_points_ready:
            report["expected_season_points_ready_positions"].append(pos)

    predictions = pd.DataFrame(prediction_rows)
    calibration = _calibration_bins(predictions)
    report["football_model_promotion_review_positions"] = sorted(report["football_model_promotion_review_positions"])
    report["expected_season_points_ready_positions"] = sorted(report["expected_season_points_ready_positions"])
    return report, predictions, calibration


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--player-week", default="")
    p.add_argument("--identity", default="")
    p.add_argument("--scoring-json", default="")
    p.add_argument("--output-json", required=True)
    p.add_argument("--predictions-csv", required=True)
    p.add_argument("--calibration-csv", required=True)
    p.add_argument("--fixture", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if a.fixture:
        pw = v2.fixture_player_week()
        scoring = {"pass_yd": .04, "pass_td": 4, "pass_int": -2, "rush_yd": .1, "rush_td": 6,
                   "rec": 1, "rec_yd": .1, "rec_td": 6, "fum_lost": -2}
        identity = pd.DataFrame()
    else:
        if not a.player_week or not Path(a.player_week).is_file():
            raise RuntimeError("--player-week is required outside fixture mode")
        pw = pd.read_csv(a.player_week, low_memory=False)
        identity = pd.read_csv(a.identity, low_memory=False) if a.identity and Path(a.identity).is_file() else pd.DataFrame()
        if not a.scoring_json or not Path(a.scoring_json).is_file():
            raise RuntimeError("--scoring-json must contain exact league scoring")
        obj = json.loads(Path(a.scoring_json).read_text())
        scoring = obj.get("settings", obj.get("scoring_settings", obj))
    v972 = v2.validate_component_preseason(pw, scoring, identity)
    report, predictions, calibration = validate_preseason_head_to_head(pw, scoring, identity, v972_result=v972)
    for path in [a.output_json, a.predictions_csv, a.calibration_csv]:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output_json).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    predictions.to_csv(a.predictions_csv, index=False)
    calibration.to_csv(a.calibration_csv, index=False)
    print(json.dumps({"status": report["status"], "promotion_review": report["football_model_promotion_review_positions"],
                      "expected_season_points_ready": report["expected_season_points_ready_positions"],
                      "rows": int(len(predictions))}, indent=2))


if __name__ == "__main__":
    main()

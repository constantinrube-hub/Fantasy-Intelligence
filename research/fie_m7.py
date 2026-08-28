#!/usr/bin/env python3
"""FIE M7: What Drives Fantasy Success.

M7 is an additive, fail-closed research layer on top of M1-M6.  It does not
replace the production model.  It answers three separate questions for QB/RB/WR/TE:

1. Opportunity: which pregame role/volume signals predict future fantasy output?
2. Conversion: which efficiency/ability signals add information after opportunity?
3. Persistence: which signals are stable enough to be useful rather than descriptive?

Every feature family is tested as an incremental residual correction on top of the
existing M4 out-of-sample FIE projection.  A family can only become a validated
candidate when it improves chronological expanding-window holdouts.  Individual
feature rankings remain explanatory/diagnostic and are never activation switches.
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
from scipy.stats import spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import CONTROL_BUILD, LATEST_COMPLETED_SEASON
from fie_m2 import FOLDS
from fie_m4 import feature_frame
from statistical_guardrails import promotion_gate
from performance_source_contract import (
    ROUTE_COLUMNS, QB_COVERAGE_COLUMNS, validate_player_feature_source, lag_player_features,
)

RESEARCH_BUILD = "V9.4-M7"
MILESTONE = "M7"
OFFENSE_POSITIONS = ("QB", "RB", "WR", "TE")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def safe_corr(x, y, min_n: int = 12) -> Tuple[Optional[float], int]:
    z = pd.DataFrame({
        "x": pd.to_numeric(pd.Series(x).reset_index(drop=True), errors="coerce"),
        "y": pd.to_numeric(pd.Series(y).reset_index(drop=True), errors="coerce"),
    }).dropna()
    if len(z) < min_n or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None, int(len(z))
    r = spearmanr(z.x, z.y).statistic
    return (None if not np.isfinite(r) else float(r)), int(len(z))


def model(alpha: float = 12.0) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=alpha)),
    ])


def first_existing(df: pd.DataFrame, names: Sequence[str]) -> Optional[str]:
    for name in names:
        if name in df.columns and pd.to_numeric(df[name], errors="coerce").notna().any():
            return name
    return None


def add_derived_driver_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-safe interactions that express football mechanisms, not bonuses.

    Inputs are already lagged pregame features.  Products are only candidates for
    residual validation; they do not directly change any projection.
    """
    d = df.copy()
    pairs = {
        "m7_qb_pressure_processing": ("pfr_times_pressured_pct_prior4", "ngs_avg_time_to_throw_prior4"),
        "m7_qb_pressure_accuracy": ("pfr_times_pressured_pct_prior4", "ngs_completion_percentage_above_expectation_prior4"),
        "m7_qb_rush_goal_role": ("qb_rush_share_prior4", "inside_5_carry_share_prior4"),
        "m7_rb_role_efficiency": ("carry_share_prior4", "ngs_rush_yards_over_expected_per_att_prior4"),
        "m7_rb_box_efficiency": ("ngs_percent_attempts_gte_eight_defenders_prior4", "ngs_rush_yards_over_expected_per_att_prior4"),
        "m7_wr_target_air_role": ("target_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4"),
        "m7_wr_target_separation": ("target_share_prior4", "ngs_avg_separation_prior4"),
        "m7_te_target_air_role": ("target_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4"),
        "m7_te_target_separation": ("target_share_prior4", "ngs_avg_separation_prior4"),
    }
    for name, (a, b) in pairs.items():
        if a in d.columns and b in d.columns:
            d[name] = pd.to_numeric(d[a], errors="coerce") * pd.to_numeric(d[b], errors="coerce")
    return d


# Each candidate is listed by semantic role.  Missing columns are not filled or
# approximated under another name.  Optional premium adapters may add the names in
# the *_premium families later; public runs simply report them unavailable.
DRIVER_CATALOG: Dict[str, Dict[str, Sequence[str]]] = {
    "QB": {
        "opportunity": [
            "qb_pass_attempt_share_prior4", "qb_rush_share_prior4", "inside_5_carry_share_prior4",
            "snap_share_prior4", "team_pass_attempts_prior4_team", "team_plays_prior4_team",
            "opportunity_change_score_prior1",
        ],
        "passing_accuracy": [
            "ngs_completion_percentage_above_expectation_prior4", "pfr_passing_bad_throw_pct_prior4",
        ],
        "depth_and_aggression": [
            "ngs_avg_intended_air_yards_prior4", "ngs_avg_air_yards_to_sticks_prior4", "ngs_aggressiveness_prior4",
        ],
        "pressure_response": [
            "pfr_times_pressured_pct_prior4", "pfr_times_sacked_prior4", "ngs_avg_time_to_throw_prior4",
            "m7_qb_pressure_processing", "m7_qb_pressure_accuracy",
        ],
        "rushing_leverage": ["qb_rush_share_prior4", "inside_5_carry_share_prior4", "m7_qb_rush_goal_role"],
        "regression": ["xfp_residual_prior4", "opportunity_xfp_realized_prior4"],
        "premium_coverage": [
            "premium_qb_epa_vs_man_prior4", "premium_qb_epa_vs_zone_prior4", "premium_qb_epa_vs_blitz_prior4",
            "premium_qb_epa_vs_two_high_prior4", "premium_qb_pressure_to_sack_prior4",
        ],
    },
    "RB": {
        "opportunity": [
            "offense_snap_share_prior4", "carry_share_prior4", "target_share_prior4",
            "red_zone_carry_share_prior4", "inside_5_carry_share_prior4", "opportunity_change_score_prior1",
        ],
        "rushing_efficiency": [
            "ngs_rush_yards_over_expected_per_att_prior4", "ngs_rush_pct_over_expected_prior4",
            "ngs_efficiency_prior4", "ngs_avg_time_to_los_prior4", "m7_rb_role_efficiency",
        ],
        "box_and_environment": ["ngs_percent_attempts_gte_eight_defenders_prior4", "m7_rb_box_efficiency"],
        "receiving_role": ["target_share_prior4", "off_part_pass_plays_prior4"],
        "competition": ["backfield_competition_index_prior4", "backfield_competitor_count"],
        "regression": ["xfp_residual_prior4", "opportunity_xfp_realized_prior4"],
        "premium_blocking": [
            "premium_yards_before_contact_over_expected_prior4", "premium_run_block_win_rate_prior4",
            "premium_short_yardage_block_win_rate_prior4",
        ],
    },
    "WR": {
        "opportunity": [
            "offense_snap_share_prior4", "target_share_prior4", "red_zone_target_share_prior4",
            "ngs_percent_share_of_intended_air_yards_prior4", "opportunity_change_score_prior1",
        ],
        "target_earning": ["ngs_avg_separation_prior4", "ngs_avg_cushion_prior4", "m7_wr_target_separation"],
        "target_quality": [
            "ngs_percent_share_of_intended_air_yards_prior4", "ngs_avg_air_distance_prior4", "m7_wr_target_air_role",
        ],
        "conversion": ["ngs_avg_yac_above_expectation_prior4", "pfr_receiving_drop_pct_prior4"],
        "competition": ["receiving_competition_index_prior4", "receiving_competitor_count"],
        "regression": ["xfp_residual_prior4", "opportunity_xfp_realized_prior4"],
        "premium_routes": [
            "premium_route_participation_prior4", "premium_targets_per_route_prior4", "premium_first_read_share_prior4",
            "premium_yards_per_route_run_prior4", "premium_separation_win_rate_prior4",
        ],
    },
    "TE": {
        "opportunity": [
            "offense_snap_share_prior4", "target_share_prior4", "red_zone_target_share_prior4",
            "ngs_percent_share_of_intended_air_yards_prior4", "opportunity_change_score_prior1",
        ],
        "target_earning": ["ngs_avg_separation_prior4", "ngs_avg_cushion_prior4", "m7_te_target_separation"],
        "target_quality": ["ngs_percent_share_of_intended_air_yards_prior4", "m7_te_target_air_role"],
        "conversion": ["ngs_avg_yac_above_expectation_prior4", "pfr_receiving_drop_pct_prior4"],
        "competition": ["receiving_competition_index_prior4", "receiving_competitor_count"],
        "regression": ["xfp_residual_prior4", "opportunity_xfp_realized_prior4"],
        "premium_routes_blocking": [
            "premium_route_participation_prior4", "premium_targets_per_route_prior4", "premium_first_read_share_prior4",
            "premium_pass_block_rate_prior4", "premium_inline_rate_prior4", "premium_slot_rate_prior4",
        ],
    },
}


def available_catalog(df: pd.DataFrame) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for pos, families in DRIVER_CATALOG.items():
        out[pos] = {}
        for family, features in families.items():
            out[pos][family] = [f for f in features if f in df.columns and pd.to_numeric(df[f], errors="coerce").notna().any()]
    return out


def load_oos(derived_dir: str, fixture: bool, df: pd.DataFrame) -> pd.DataFrame:
    """Load M4 OOS rows; deterministic pregame prior fallback exists only in fixture."""
    p = Path(derived_dir) / "milestone4_oos_predictions.csv.gz"
    if p.exists():
        return pd.read_csv(p, low_memory=False)
    if not fixture:
        raise RuntimeError("M7 requires milestone4_oos_predictions.csv.gz from M4; run M1→M4 first.")
    q = df[df.season.isin([2022, 2023, 2024, 2025])][[
        "season", "week", "canonical_player_id", "full_name", "team", "position_model", "fantasy_points"
    ]].copy()
    base = pd.to_numeric(df.loc[q.index, "fp_prior_4"], errors="coerce") if "fp_prior_4" in df else pd.Series(np.nan, index=q.index)
    means = pd.to_numeric(q.fantasy_points, errors="coerce").groupby(q.position_model).transform("mean")
    q["fie_projection"] = base.fillna(means)
    q["baseline_projection"] = q["fie_projection"]
    return q.reset_index(drop=True)


def add_future_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create forward fantasy targets without crossing a player-season boundary."""
    d = df.sort_values(["canonical_player_id", "season", "week"]).copy()
    fp = pd.to_numeric(d["fantasy_points"], errors="coerce")
    d["_fp_numeric"] = fp
    # Explicit shifts keep the current week's outcome out of forward labels.
    g = d.groupby(["canonical_player_id", "season"], group_keys=False)["_fp_numeric"]
    s1, s2, s3 = g.shift(-1), g.shift(-2), g.shift(-3)
    d["future_fp_next1"] = s1
    d["future_fp_next3"] = pd.concat([s1, s2, s3], axis=1).mean(axis=1, skipna=True)
    return d.drop(columns=["_fp_numeric"])


def feature_level_evidence(df: pd.DataFrame, catalog: Dict[str, Dict[str, List[str]]]) -> List[dict]:
    d = add_future_targets(df)
    rows: List[dict] = []
    for pos in OFFENSE_POSITIONS:
        z = d[d.position_model.eq(pos)].copy()
        for family, features in catalog.get(pos, {}).items():
            for f in features:
                now, n_now = safe_corr(z[f], z["fantasy_points"])
                n1, n_n1 = safe_corr(z[f], z["future_fp_next1"])
                n3, n_n3 = safe_corr(z[f], z["future_fp_next3"])
                # Persistence is feature-to-next-game same-feature only when an unlagged
                # counterpart exists.  It is intentionally reported separately from FP.
                raw = f[:-7] if f.endswith("_prior4") else None
                persistence, n_persist = (None, 0)
                if raw and raw in z.columns:
                    future_raw = z.groupby(["canonical_player_id", "season"])[raw].shift(-1)
                    persistence, n_persist = safe_corr(z[f], future_raw)
                rows.append({
                    "position": pos, "family": family, "feature": f,
                    "same_week_spearman": now, "same_week_n": n_now,
                    "next_week_spearman": n1, "next_week_n": n_n1,
                    "next3_spearman": n3, "next3_n": n_n3,
                    "persistence_spearman": persistence, "persistence_n": n_persist,
                    "status": "diagnostic_feature_evidence",
                })
    return rows


def residual_family_validation(
    df: pd.DataFrame, oos: pd.DataFrame, catalog: Dict[str, Dict[str, List[str]]]
) -> Tuple[List[dict], List[dict]]:
    keys = ["season", "week", "canonical_player_id", "position_model"]
    all_features = list(dict.fromkeys(f for pos in catalog.values() for fs in pos.values() for f in fs))
    keep = keys + [c for c in all_features if c in df.columns]
    z = oos.merge(df[keep].drop_duplicates(keys), on=keys, how="left")
    folds: List[dict] = []
    for train_seasons, test_season in FOLDS:
        for pos in OFFENSE_POSITIONS:
            p = z[z.position_model.eq(pos)].copy()
            p["fantasy_points"] = pd.to_numeric(p.fantasy_points, errors="coerce")
            p["fie_projection"] = pd.to_numeric(p.fie_projection, errors="coerce")
            p["residual"] = p.fantasy_points - p.fie_projection
            for family, fs0 in catalog.get(pos, {}).items():
                fs = [f for f in fs0 if f in p.columns and pd.to_numeric(p[f], errors="coerce").notna().any()]
                if not fs:
                    continue
                tr = p[p.season.isin(train_seasons)].dropna(subset=["residual"]).copy()
                te = p[p.season.eq(test_season)].dropna(subset=["fantasy_points", "fie_projection"]).copy()
                # Require source coverage in both partitions, not just imputer-fill.
                tr_cov = tr[fs].notna().any(axis=1)
                te_cov = te[fs].notna().any(axis=1)
                tr, te = tr[tr_cov].copy(), te[te_cov].copy()
                if len(tr) < 80 or len(te) < 15:
                    continue
                m = model(); m.fit(tr[fs], tr.residual)
                adj = np.clip(m.predict(te[fs]), -8.0, 8.0)
                base = te.fie_projection.to_numpy(float)
                y = te.fantasy_points.to_numpy(float)
                pred = base + adj
                bmae = float(mean_absolute_error(y, base)); amae = float(mean_absolute_error(y, pred))
                rb, _ = safe_corr(base, y); ra, _ = safe_corr(pred, y)
                folds.append({
                    "position": pos, "family": family, "test_season": int(test_season),
                    "n_train": int(len(tr)), "n_test": int(len(te)), "features": fs,
                    "base_fie_mae": bmae, "adjusted_mae": amae,
                    "incremental_mae_improvement": float((bmae - amae) / bmae) if bmae > 0 else None,
                    "base_spearman": rb, "adjusted_spearman": ra,
                })
    agg: List[dict] = []
    f = pd.DataFrame(folds)
    if not f.empty:
        for (pos, family), g in f.groupby(["position", "family"]):
            imp = pd.to_numeric(g.incremental_mae_improvement, errors="coerce").dropna()
            weights = g.loc[imp.index, "n_test"].tolist() if len(imp) else None
            gate = promotion_gate(imp.tolist(), weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True)
            agg.append({
                "position": pos, "family": family, "folds": int(len(g)), "n_test": int(g.n_test.sum()),
                "mean_incremental_mae_improvement": float(imp.mean()) if len(imp) else None,
                "positive_folds": int((imp > 0).sum()) if len(imp) else 0,
                "bootstrap_ci95_low": gate.get("ci95_low"), "bootstrap_ci95_high": gate.get("ci95_high"),
                "status": "validated_candidate" if gate.get("robust") else "diagnostic_only",
            })
    return folds, agg



def _serialize_fitted_residual_spec(frame: pd.DataFrame, features: List[str]) -> Optional[dict]:
    """Fit and serialize the exact M7 residual pipeline without pickling runtime code."""
    if frame.empty or not features:
        return None
    z = frame.dropna(subset=["residual"]).copy()
    z = z[z[features].notna().any(axis=1)]
    if len(z) < 120:
        return None
    pipe = model(); pipe.fit(z[features], z.residual)
    imp = pipe.named_steps["impute"]
    scale = pipe.named_steps["scale"]
    ridge = pipe.named_steps["ridge"]
    return {
        "features": list(features), "n_train": int(len(z)), "target": "base_fie_residual",
        "imputer": {"strategy": "median", "statistics": [float(x) for x in imp.statistics_]},
        "scaler": {"mean": [float(x) for x in scale.mean_], "scale": [float(x) for x in scale.scale_]},
        "ridge": {"alpha": float(ridge.alpha), "intercept": float(ridge.intercept_), "coef": [float(x) for x in ridge.coef_]},
        "prediction_clip": [-8.0, 8.0],
        "semantics": "incremental residual correction to the canonical M4/FIE weekly projection",
    }


def activation_composite(df: pd.DataFrame, oos: pd.DataFrame, catalog: Dict[str, Dict[str, List[str]]], family_agg: List[dict]) -> dict:
    """Require a second gate before independently good families may be combined.

    This prevents double counting correlated mechanisms such as target share, air share,
    separation and team environment.  Only the jointly validated composite is serialised
    for downstream current-season use.
    """
    passed = {(r["position"], r["family"]) for r in family_agg if r.get("status") == "validated_candidate"}
    joint_catalog: Dict[str, Dict[str, List[str]]] = {}
    for pos in OFFENSE_POSITIONS:
        fs = []
        for fam, members in catalog.get(pos, {}).items():
            if (pos, fam) in passed:
                fs.extend(members)
        if fs:
            joint_catalog[pos] = {"validated_composite": list(dict.fromkeys(fs))}
    if not joint_catalog:
        return {"status": "diagnostic_only", "reason": "no_individual_family_passed", "folds": [], "aggregate": [], "model_specs": {}}
    folds, agg = residual_family_validation(df, oos, joint_catalog)
    agg_by_pos = {r["position"]: r for r in agg if r.get("family") == "validated_composite"}
    specs = {}
    keys = ["season", "week", "canonical_player_id", "position_model"]
    for pos, fams in joint_catalog.items():
        gate = agg_by_pos.get(pos, {})
        if gate.get("status") != "validated_candidate":
            continue
        features = fams["validated_composite"]
        keep = keys + [f for f in features if f in df.columns]
        z = oos.merge(df[keep].drop_duplicates(keys), on=keys, how="left")
        z = z[z.position_model.eq(pos)].copy()
        z["residual"] = pd.to_numeric(z.fantasy_points, errors="coerce") - pd.to_numeric(z.fie_projection, errors="coerce")
        spec = _serialize_fitted_residual_spec(z, features)
        if spec:
            spec["gate"] = gate
            specs[pos] = spec
    return {
        "status": "validated_candidate" if specs else "diagnostic_only",
        "rule": "Individual families may not stack. Only the jointly revalidated composite may create a current-season residual adjustment.",
        "folds": folds, "aggregate": agg, "model_specs": specs,
    }


def rank_drivers(feature_rows: List[dict], family_agg: List[dict]) -> List[dict]:
    """Create a transparent evidence ranking; this is not model feature importance."""
    fam = {(r["position"], r["family"]): r for r in family_agg}
    out: List[dict] = []
    for r in feature_rows:
        vals = [abs(float(r[k])) for k in ("next_week_spearman", "next3_spearman", "persistence_spearman") if r.get(k) is not None]
        signal = float(np.mean(vals)) if vals else 0.0
        a = fam.get((r["position"], r["family"]), {})
        inc = max(-.05, min(.10, float(a.get("mean_incremental_mae_improvement") or 0.0)))
        sample = max(int(r.get("next3_n") or 0), int(r.get("same_week_n") or 0))
        sample_factor = min(1.0, math.log1p(sample) / math.log(1001)) if sample > 0 else 0.0
        evidence = (0.70 * signal + 0.30 * max(0.0, inc)) * sample_factor
        out.append({
            **r,
            "family_incremental_mae_improvement": a.get("mean_incremental_mae_improvement"),
            "family_status": a.get("status", "insufficient_sample"),
            "evidence_score": float(evidence),
            "interpretation": "predictive_not_causal",
        })
    out.sort(key=lambda x: (x["position"], -x["evidence_score"], x["feature"]))
    rank = {p: 0 for p in OFFENSE_POSITIONS}
    for r in out:
        rank[r["position"]] += 1
        r["position_evidence_rank"] = rank[r["position"]]
    return out


def coverage_ledger(catalog: Dict[str, Dict[str, List[str]]]) -> List[dict]:
    rows = []
    for pos, families in DRIVER_CATALOG.items():
        for family, requested in families.items():
            got = catalog.get(pos, {}).get(family, [])
            rows.append({
                "position": pos, "family": family, "requested_features": list(requested),
                "available_features": got, "coverage": len(got) / len(requested) if requested else 1.0,
                "source_class": "optional_premium" if family.startswith("premium_") else "public_core_or_enrichment",
                "status": "available" if got else "blocked_missing_source",
            })
    return rows



def merge_optional_player_charting(df: pd.DataFrame, args) -> Tuple[pd.DataFrame, dict]:
    """Attach leakage-safe optional route/QB-coverage priors without making them dependencies."""
    if df.empty:
        return df, {}
    max_season = int(pd.to_numeric(df.season, errors="coerce").max())
    route, route_health = validate_player_feature_source(args.route_source, ROUTE_COLUMNS, max_season=max_season)
    qb, qb_health = validate_player_feature_source(args.qb_coverage_source, QB_COVERAGE_COLUMNS, max_season=max_season)
    d = df.copy(); keys = ["season","week","team","canonical_player_id"]
    if not route.empty:
        pri = lag_player_features(route, [c for c in ROUTE_COLUMNS if c in route])
        d = d.merge(pri, on=keys, how="left")
    if not qb.empty:
        pri = lag_player_features(qb, [c for c in QB_COVERAGE_COLUMNS if c in qb])
        d = d.merge(pri, on=keys, how="left")
    return d, {"route_source": route_health.__dict__, "qb_coverage_source": qb_health.__dict__,
               "timing_rule": "realised week-N charting is shifted before rolling; same-game values can never enter week-N prediction"}


def run(args) -> dict:
    df, team, identity, m1_core, m2_core, enrichment = feature_frame(args)
    df, optional_charting = merge_optional_player_charting(df, args)
    df = add_derived_driver_features(df)
    catalog = available_catalog(df)
    oos = load_oos(args.derived_dir, args.fixture, df)
    feature_rows = feature_level_evidence(df, catalog)
    folds, family_agg = residual_family_validation(df, oos, catalog)
    ranking = rank_drivers(feature_rows, family_agg)
    composite = activation_composite(df, oos, catalog, family_agg)
    coverage = coverage_ledger(catalog)
    validated = sorted({f"{r['position']}:{r['family']}" for r in family_agg if r.get("status") == "validated_candidate"})
    m1 = load_json(args.m1_bundle) or m1_core
    m6 = load_json(args.m6_bundle)
    return {
        "schema_version": 7,
        "milestone": MILESTONE,
        "control_build": CONTROL_BUILD,
        "research_build": RESEARCH_BUILD,
        "generated_at": utc_now(),
        "status": "complete",
        "steps_completed": [31, 32, 33],
        "scoring_signature": m6.get("scoring_signature") or m1.get("scoring", {}).get("signature"),
        "methodology": {
            "step31": "Separate opportunity, conversion/ability and persistence feature families by position. Same-week outcomes are descriptive; forward correlations use future games only.",
            "step32": "Test each feature family as a residual correction after the existing M4 OOS FIE projection. Promotion uses the existing chronological expanding-window robust gate.",
            "step33": "Publish a driver evidence ranking that combines forward association, persistence and family-level incremental evidence. The ranking is predictive, not causal, and never activates a model by itself.",
            "anti_double_counting": "Mechanism interactions are residual candidates. They are not independent point bonuses and cannot stack directly onto projections.",
        },
        "driver_research": {
            "feature_evidence": feature_rows,
            "family_validation": {"folds": folds, "aggregate": family_agg},
            "driver_ranking": ranking,
            "validated_candidate_families": validated,
            "activation_composite": composite,
            "activation_status": "COMPOSITE_SPEC_AVAILABLE" if composite.get("model_specs") else "DIAGNOSTIC_ONLY_UNTIL_CONSUMER_GATE",
        },
        "source_coverage": coverage,
        "source_enrichment": enrichment,
        "optional_charting_sources": optional_charting,
        "upstream": {"m1_status": m1.get("status"), "m6_status": m6.get("status")},
        "limitations": [
            "Public participation is not silently relabelled as true all-route participation.",
            "Premium route, first-read, coverage and OL features remain absent unless supplied as point-in-time historical data.",
            "Feature evidence ranks prediction utility, not causal football effects.",
            "A family that does not improve the existing FIE OOS residual remains diagnostic even if its raw correlation is large.",
        ],
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE M7 What Drives Fantasy Success research")
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--m1-bundle", default="data/research/milestone1.json")
    p.add_argument("--m2-bundle", default="data/research/milestone2.json")
    p.add_argument("--m3-bundle", default="data/research/milestone3.json")
    p.add_argument("--m4-bundle", default="data/research/milestone4.json")
    p.add_argument("--m5-bundle", default="data/research/milestone5.json")
    p.add_argument("--m6-bundle", default="data/research/milestone6.json")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--route-source", default="", help="Optional player-week all-route/first-read charting; values are lagged before use")
    p.add_argument("--qb-coverage-source", default="", help="Optional player-week QB coverage/pressure splits; values are lagged before use")
    p.add_argument("--seasons", default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--output", default="data/research/milestone7.json")
    p.add_argument("--fixture", action="store_true")
    a = p.parse_args(argv)
    if isinstance(a.seasons, str):
        lo, hi = map(int, a.seasons.split("-")); a.seasons = list(range(lo, hi + 1))
    return a


def main(argv=None):
    args = parse_args(argv)
    bundle = run(args)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2, allow_nan=False))
    print(f"Wrote {out} status={bundle['status']} validated={len(bundle['driver_research']['validated_candidate_families'])}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.8-M6 final research/governance milestone.

Implements roadmap Steps 28-30:
28 advanced second-wave research (opponent-role context, validated interactions,
   descriptive player archetypes, explicit blocked-source ledger),
29 current-season automation contract (implemented by build_current_snapshot.py),
30 permanent governance/versioning/rollback contract.

Step 28 remains diagnostic unless its incremental evidence clears the same expanding-
window rules used throughout the project. Steps 29-30 are production infrastructure,
not permission to bypass M5's decision-specific gates.
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
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import CONTROL_BUILD, POSITIONS, LATEST_COMPLETED_SEASON
from fie_m2 import FOLDS
from fie_m4 import feature_frame
from statistical_guardrails import promotion_gate

RESEARCH_BUILD = "V8.8-M6"
MILESTONE = "M6"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def safe_corr(x, y) -> Optional[float]:
    z = pd.DataFrame({"x": pd.to_numeric(pd.Series(x).reset_index(drop=True), errors="coerce"), "y": pd.to_numeric(pd.Series(y).reset_index(drop=True), errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None
    r = spearmanr(z.x, z.y).statistic
    return None if not np.isfinite(r) else float(r)


def model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=10.0)),
    ])


def load_oos(derived_dir: str, fixture: bool, df: pd.DataFrame) -> pd.DataFrame:
    p = Path(derived_dir) / "milestone4_oos_predictions.csv.gz"
    if p.exists():
        return pd.read_csv(p, low_memory=False)
    if fixture:
        # Deterministic pseudo-OOS projection used only to exercise Step 28.
        q = df[df.season.isin([2022, 2023, 2024, 2025])][[
            "season", "week", "canonical_player_id", "full_name", "team", "position_model", "fantasy_points"
        ]].copy()
        base = df.loc[q.index, "fp_prior_4"] if "fp_prior_4" in df else pd.Series(np.nan, index=q.index)
        q["fie_projection"] = pd.to_numeric(base, errors="coerce").fillna(pd.to_numeric(q.fantasy_points, errors="coerce").groupby(q.position_model).transform("mean"))
        q["baseline_projection"] = q["fie_projection"]
        return q.reset_index(drop=True)
    raise RuntimeError("Milestone 4 OOS predictions are required. Run M1→M4 first.")


# ------------------------ Step 28A: opponent-role context ------------------------

def add_opponent_role_prior(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values(["season", "week", "opponent_team", "position_model"]).copy()
    d["fantasy_points"] = pd.to_numeric(d.fantasy_points, errors="coerce")
    # Aggregate the position room faced by the defense in each game, then shift before rolling.
    gp = d.groupby(["season", "week", "opponent_team", "position_model"], as_index=False).fantasy_points.sum().rename(columns={"fantasy_points": "opp_pos_fp_allowed"})
    gp = gp.sort_values(["opponent_team", "position_model", "season", "week"])
    g = gp.groupby(["opponent_team", "position_model"], group_keys=False)
    gp["opp_pos_fp_allowed_prior4"] = g.opp_pos_fp_allowed.transform(lambda s: s.shift(1).rolling(4, min_periods=2).mean())
    gp["opp_pos_fp_allowed_prior8"] = g.opp_pos_fp_allowed.transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    return df.merge(gp[["season", "week", "opponent_team", "position_model", "opp_pos_fp_allowed_prior4", "opp_pos_fp_allowed_prior8"]],
                    on=["season", "week", "opponent_team", "position_model"], how="left")


def incremental_residual_validation(df: pd.DataFrame, oos: pd.DataFrame, features_by_pos: Dict[str, Sequence[str]], family: str) -> Tuple[List[dict], List[dict]]:
    keys = ["season", "week", "canonical_player_id", "position_model"]
    extra = [c for xs in features_by_pos.values() for c in xs]
    extra = list(dict.fromkeys([c for c in extra if c in df.columns]))
    base_cols = keys + extra
    if "opponent_team" in df.columns:
        base_cols.append("opponent_team")
    z = oos.merge(df[base_cols].drop_duplicates(keys), on=keys, how="left")
    rows: List[dict] = []
    for train_seasons, test_season in FOLDS:
        for pos in POSITIONS:
            fs = [f for f in features_by_pos.get(pos, []) if f in z.columns]
            if not fs:
                continue
            p = z[z.position_model.eq(pos)].copy()
            p["residual"] = pd.to_numeric(p.fantasy_points, errors="coerce") - pd.to_numeric(p.fie_projection, errors="coerce")
            tr = p[p.season.isin(train_seasons)].dropna(subset=["residual"]).copy()
            te = p[p.season.eq(test_season)].dropna(subset=["residual", "fie_projection", "fantasy_points"]).copy()
            if len(tr) < 80 or len(te) < 15:
                continue
            m = model(); m.fit(tr[fs], tr.residual)
            adj = np.clip(m.predict(te[fs]), -8.0, 8.0)
            pred = pd.to_numeric(te.fie_projection, errors="coerce").to_numpy(float) + adj
            y = pd.to_numeric(te.fantasy_points, errors="coerce").to_numpy(float)
            base = pd.to_numeric(te.fie_projection, errors="coerce").to_numpy(float)
            ma = float(mean_absolute_error(y, pred)); bm = float(mean_absolute_error(y, base))
            rows.append({
                "family": family, "position": pos, "test_season": int(test_season), "n_test": int(len(te)),
                "feature_count": int(len(fs)), "features": fs, "adjusted_mae": ma, "base_fie_mae": bm,
                "incremental_mae_improvement": float((bm - ma) / bm) if bm > 0 else None,
                "adjusted_spearman": safe_corr(pred, y), "base_spearman": safe_corr(base, y),
            })
    agg: List[dict] = []
    f = pd.DataFrame(rows)
    if not f.empty:
        for pos, g in f.groupby("position"):
            imp = pd.to_numeric(g.incremental_mae_improvement, errors="coerce").dropna()
            mean_imp = float(imp.mean()) if len(imp) else None
            wins = int((imp > 0).sum())
            gate = promotion_gate(imp.tolist(), weights=g.loc[imp.index, "n_test"].tolist(), min_mean=.01, min_folds=4, require_positive_ci=True)
            agg.append({
                "family": family, "position": pos, "folds": int(len(g)), "n_test": int(g.n_test.sum()),
                "mean_incremental_mae_improvement": mean_imp, "positive_folds": wins,
                "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"],
                "status": "validated_candidate" if gate["robust"] else "diagnostic_only",
            })
    return rows, agg


# ------------------------ Step 28B: interaction hypotheses ------------------------

def add_interactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    d = df.copy()
    definitions: Dict[str, List[Tuple[str, str, str]]] = {
        "QB": [
            ("m6_pressure_time_interaction", "ngs_avg_time_to_throw_prior4", "pfr_times_pressured_pct_prior4"),
            ("m6_pressure_cpoe_interaction", "ngs_completion_percentage_above_expectation_prior4", "pfr_times_pressured_pct_prior4"),
        ],
        "RB": [
            ("m6_box_ryoe_interaction", "ngs_percent_attempts_gte_eight_defenders_prior4", "ngs_rush_yards_over_expected_per_att_prior4"),
            ("m6_role_ryoe_interaction", "carry_share_prior4", "ngs_rush_yards_over_expected_per_att_prior4"),
        ],
        "WR": [
            ("m6_target_airshare_interaction", "target_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4"),
            ("m6_target_separation_interaction", "target_share_prior4", "ngs_avg_separation_prior4"),
        ],
        "TE": [
            ("m6_target_airshare_interaction", "target_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4"),
            ("m6_target_separation_interaction", "target_share_prior4", "ngs_avg_separation_prior4"),
        ],
        "EDGE": [("m6_pressure_role_interaction", "defense_snap_share_prior4", "def_part_pressure_context_rate_prior4")],
        "IDL": [("m6_pressure_role_interaction", "defense_snap_share_prior4", "def_part_pressure_context_rate_prior4")],
        "LB": [("m6_man_role_interaction", "defense_snap_share_prior4", "def_part_man_context_rate_prior4")],
        "S": [("m6_man_role_interaction", "defense_snap_share_prior4", "def_part_man_context_rate_prior4")],
        "CB": [("m6_man_role_interaction", "defense_snap_share_prior4", "def_part_man_context_rate_prior4")],
    }
    by_pos: Dict[str, List[str]] = {p: [] for p in POSITIONS}
    for pos, defs in definitions.items():
        for name, a, b in defs:
            if a in d.columns and b in d.columns:
                d[name] = pd.to_numeric(d[a], errors="coerce") * pd.to_numeric(d[b], errors="coerce")
                if d.loc[d.position_model.eq(pos), name].notna().sum() >= 40:
                    by_pos[pos].append(name)
    return d, by_pos


# ------------------------ Step 28C: descriptive archetypes ------------------------

ARCHETYPE_FEATURES = {
    "QB": ["qb_rush_share_prior4", "ngs_avg_intended_air_yards_prior4", "ngs_avg_time_to_throw_prior4"],
    "RB": ["carry_share_prior4", "target_share_prior4", "inside_5_carry_share_prior4"],
    "WR": ["target_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4", "ngs_avg_separation_prior4"],
    "TE": ["target_share_prior4", "offense_snap_share_prior4", "ngs_percent_share_of_intended_air_yards_prior4"],
    "EDGE": ["defense_snap_share_prior4", "def_part_pressure_context_rate_prior4", "pfr_def_times_hurried_prior4"],
    "IDL": ["defense_snap_share_prior4", "def_part_pressure_context_rate_prior4", "pfr_def_times_hurried_prior4"],
    "LB": ["defense_snap_share_prior4", "def_part_man_context_rate_prior4", "def_part_zone_context_rate_prior4"],
    "S": ["defense_snap_share_prior4", "def_part_man_context_rate_prior4", "def_part_avg_defenders_in_box_prior4"],
    "CB": ["defense_snap_share_prior4", "def_part_man_context_rate_prior4", "def_part_zone_context_rate_prior4"],
}


def archetype_analysis(df: pd.DataFrame) -> List[dict]:
    rows: List[dict] = []
    for pos in POSITIONS:
        fs = [c for c in ARCHETYPE_FEATURES.get(pos, []) if c in df.columns]
        if len(fs) < 2:
            continue
        z = df[df.position_model.eq(pos)].copy()
        # One player-season row using late-season pregame profile; descriptive only.
        z = z.sort_values(["canonical_player_id", "season", "week"]).groupby(["canonical_player_id", "season"], as_index=False).tail(1)
        use = z[["canonical_player_id", "season", "fantasy_points"] + fs].copy()
        if len(use) < 30:
            continue
        X = SimpleImputer(strategy="median").fit_transform(use[fs])
        X = StandardScaler().fit_transform(X)
        k = min(3, max(2, len(use) // 40))
        km = KMeans(n_clusters=k, random_state=88, n_init=20).fit(X)
        use["cluster"] = km.labels_
        for c in sorted(use.cluster.unique()):
            q = use[use.cluster.eq(c)]
            cent = {f: float(pd.to_numeric(q[f], errors="coerce").mean()) for f in fs}
            rows.append({
                "position": pos, "cluster": int(c), "n_player_seasons": int(len(q)),
                "features": fs, "centroid_raw": cent,
                "mean_weekly_fp_at_profile": float(pd.to_numeric(q.fantasy_points, errors="coerce").mean()),
                "status": "descriptive_only",
            })
    return rows


def blocked_advanced_ledger() -> List[dict]:
    return [
        {"analysis": "coordinator_tendency_portability", "status": "blocked_missing_versioned_coordinator_source", "reason": "No trustworthy public historical coordinator/scheme assignment table is bundled across the full modelling window."},
        {"analysis": "offensive_line_unit_quality", "status": "blocked_missing_consistent_player_unit_grades", "reason": "Public team/player inputs do not provide a consistent historical OL-unit quality measure comparable across the rollover-safe historical window."},
        {"analysis": "stadium_stat_crew_tackle_bias", "status": "blocked_missing_official_stat_crew_identifier", "reason": "Venue can be reconstructed, but attributing persistent tackle-credit effects to a stat crew requires an auditable official/scorer identifier rather than stadium name alone."},
        {"analysis": "all_route_alignment_and_separation", "status": "blocked_missing_all_route_tracking", "reason": "Public participation does not provide every eligible receiver's route/alignment/separation on every route; targeted-play separation cannot be used as if it were all-route target-earning evidence."},
        {"analysis": "individual_double_team_rate", "status": "blocked_missing_consistent_public_history", "reason": "No consistent free historical individual double-team series is bundled for all pass rushers/receivers across the primary window."},
    ]


def run(args) -> dict:
    df, team, identity, m1_core, m2_core, enrichment = feature_frame(args)
    m1 = load_json(args.m1_bundle) or m1_core
    m2 = load_json(args.m2_bundle) or m2_core
    m3 = load_json(args.m3_bundle)
    m4 = load_json(args.m4_bundle)
    m5 = load_json(args.m5_bundle)
    oos = load_oos(args.derived_dir, args.fixture, df)

    df_opp = add_opponent_role_prior(df)
    opp_features = {p: ["opp_pos_fp_allowed_prior4", "opp_pos_fp_allowed_prior8"] for p in POSITIONS}
    opp_rows, opp_agg = incremental_residual_validation(df_opp, oos, opp_features, "opponent_role_allowance")

    df_int, int_features = add_interactions(df)
    int_rows, int_agg = incremental_residual_validation(df_int, oos, int_features, "position_interactions")
    archetypes = archetype_analysis(df_int)
    blocked = blocked_advanced_ledger()

    validated_second_wave = sorted({r["position"] for r in opp_agg + int_agg if r.get("status") == "validated_candidate"})
    scoring_sig = m5.get("scoring_signature") or m4.get("scoring_signature") or m1.get("scoring", {}).get("signature")
    bundle = {
        "schema_version": 6,
        "milestone": MILESTONE,
        "control_build": CONTROL_BUILD,
        "research_build": RESEARCH_BUILD,
        "generated_at": utc_now(),
        "status": "complete",
        "steps_completed": [28, 29, 30],
        "scoring_signature": scoring_sig,
        "methodology": {
            "step28": "Second-wave signals are tested only as incremental residual corrections on top of M4 OOS FIE projections. Opponent-role context and interaction hypotheses must improve expanding-window holdouts; archetypes remain descriptive.",
            "step29": "Current-season automation is implemented by build_current_snapshot.py and a scheduled GitHub Action. Target-week rows exclude all results from that target week, and stale/incompatible snapshots fail closed.",
            "step30": "Runtime promotion is governed by a separate versioned manifest with AUTO/CONTROL operator override. The immutable fallback remains V8.2.2 and rollback does not require changing scoring functions.",
        },
        "advanced_second_wave": {
            "opponent_role": {"folds": opp_rows, "aggregate": opp_agg},
            "position_interactions": {"folds": int_rows, "aggregate": int_agg},
            "player_archetypes": archetypes,
            "validated_candidate_positions": validated_second_wave,
            "blocked_analyses": blocked,
            "activation_status": "DIAGNOSTIC_ONLY",
        },
        "current_season_automation": {
            "status": "implemented",
            "builder": "research/build_current_snapshot.py",
            "workflow": ".github/workflows/build-fie-current.yml",
            "output": "data/research/current/milestone5_current.json",
            "producer_build": RESEARCH_BUILD,
            "target_week_rule": "all target-week realised stats are excluded from feature construction",
            "freshness_rule_hours": 18,
            "first_write_sleeper_archive": "data/research/market/sleeper/{season}/week_{week}.jsonl.gz",
        },
        "governance": {
            "status": "implemented",
            "builder": "research/fie_governance.py",
            "active_manifest": "data/research/governance/active_release.json",
            "operator_override": "data/research/governance/operator_override.json",
            "default_mode": "AUTO",
            "control_fallback": CONTROL_BUILD,
            "promotion_rule": "M6 bundle complete + M5 empirical bundle complete + compatible fresh current snapshot + at least one eligible player + operator mode AUTO",
            "rollback_rule": "set operator_override.mode=CONTROL and rebuild/commit; browser then refuses all M5/M6 overrides and uses V8.2.2",
        },
        "upstream": {
            "m1_status": m1.get("status"), "m2_status": m2.get("status"), "m3_status": m3.get("status"),
            "m4_status": m4.get("status"), "m5_status": m5.get("status"),
        },
        "limitations": [
            "Step 28 does not silently fill missing premium data. Blocked research families remain explicit in the bundle.",
            "Player archetypes are descriptive and cannot activate live decisions by themselves.",
            "The current-season builder requires at least two completed prior games for FIE weekly activation; before that it can archive/display Sleeper projections while keeping the FIE gate off.",
            "The current repository architecture is optimized around one empirical scoring profile at a time; materially different league scoring systems should regenerate M1-M6 with that league ID before live activation.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE V8.8-M6 final research/governance bundle")
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--m1-bundle", default="data/research/milestone1.json")
    p.add_argument("--m2-bundle", default="data/research/milestone2.json")
    p.add_argument("--m3-bundle", default="data/research/milestone3.json")
    p.add_argument("--m4-bundle", default="data/research/milestone4.json")
    p.add_argument("--m5-bundle", default="data/research/milestone5.json")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--seasons", default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--output", default="data/research/milestone6.json")
    p.add_argument("--fixture", action="store_true")
    a = p.parse_args(argv)
    if isinstance(a.seasons, str):
        lo, hi = map(int, a.seasons.split("-")); a.seasons = list(range(lo, hi + 1))
    return a


def main(argv=None):
    a = parse_args(argv)
    b = run(a)
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(b, indent=2, allow_nan=False))
    print(f"Wrote {out} status={b['status']} steps={b['steps_completed']}")


if __name__ == "__main__":
    main()

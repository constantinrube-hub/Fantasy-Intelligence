#!/usr/bin/env python3
"""FIE Feature Evidence Hardening layer.

This module wraps the existing Phases 1-7 feature-evidence research without
changing production runtime behavior.  It fixes four research limitations:

1. creates evidence-only extended M4 OOS predictions so residual/challenger
   validation can have genuine multi-season outer folds;
2. compares next-season features against a calibrated Ridge baseline rather
   than raw prior-season fantasy PPG;
3. de-duplicates repeated feature hypotheses across semantic families before
   validation and BH-FDR accounting;
4. emits explicit consumer-routing candidates for robust evidence while keeping
   every route research-only and manual-integration-required.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

import fie_feature_evidence as fe

BUILD = "V9.4-FEATURE-EVIDENCE-HARDENED-1"
HARDENING_SCHEMA = 1
MIN_RESIDUAL_FOLDS = 4

# Keep stable handles to the already-tested Phase 1-7 implementations before
# installing hardened wrappers below.
_BASE_FEATURE_MATRIX = fe.feature_matrix
_BASE_HORIZON_VALIDATION = fe.horizon_validation
_BASE_LOAD_LIVE = fe.load_live


def deduplicated_catalog(catalog: dict) -> Tuple[dict, dict]:
    """Return one hypothesis per position/feature plus semantic-family metadata."""
    dedup: Dict[str, Dict[str, List[str]]] = {}
    meta = {}
    for pos in fe.POSITIONS:
        seen = {}
        for family, features in (catalog.get(pos) or {}).items():
            for feature in features:
                rec = seen.setdefault(feature, {"primary_family": family, "families": []})
                if family not in rec["families"]:
                    rec["families"].append(family)
        ordered = list(seen)
        dedup[pos] = {"deduplicated_hypotheses": ordered}
        for feature, rec in seen.items():
            meta[(pos, feature)] = rec
    return dedup, meta


def _apply_family_metadata(rows: List[dict], meta: dict) -> None:
    for row in rows:
        rec = meta.get((row.get("position"), row.get("feature"))) or {}
        row["family"] = rec.get("primary_family", row.get("family"))
        row["families"] = list(rec.get("families") or [row.get("family")])
        row["hypothesis_id"] = f"{row.get('position')}:{row.get('feature')}"


def season_feature_gate_fair(df, pos, feature):
    """Fair next-season test: calibrated baseline vs calibrated baseline+feature."""
    try:
        from preseason_projection import build_transition_table
    except Exception:
        return [], {"robust": False, "reason": "preseason_projection_unavailable", "baseline_model": "ridge_prev_fantasy_ppg"}

    trans, _, _ = build_transition_table(df, pos)
    if trans.empty or feature not in trans.columns:
        return [], {"robust": False, "reason": "feature_not_in_transition_table", "baseline_model": "ridge_prev_fantasy_ppg"}

    rows = []
    for train_seasons, test in fe.expanding_folds(
        trans.target_season.dropna().unique(), min_train_seasons=3, max_folds=6
    ):
        tr = trans[trans.target_season.isin(train_seasons)].dropna(
            subset=["target_fantasy_ppg", "prev_fantasy_ppg"]
        )
        te = trans[trans.target_season.eq(test)].dropna(
            subset=["target_fantasy_ppg", "prev_fantasy_ppg"]
        )
        # Baseline and augmented model must be scored on identical feature-covered rows.
        tr = tr[tr[[feature]].notna().any(axis=1)]
        te = te[te[[feature]].notna().any(axis=1)]
        if len(tr) < 60 or len(te) < 12:
            continue

        baseline = fe.ridge(18)
        augmented = fe.ridge(18)
        baseline.fit(tr[["prev_fantasy_ppg"]], tr.target_fantasy_ppg)
        augmented.fit(tr[["prev_fantasy_ppg", feature]], tr.target_fantasy_ppg)

        y = pd.to_numeric(te.target_fantasy_ppg, errors="coerce").to_numpy(float)
        pb = baseline.predict(te[["prev_fantasy_ppg"]])
        pa = augmented.predict(te[["prev_fantasy_ppg", feature]])
        ok = np.isfinite(y) & np.isfinite(pb) & np.isfinite(pa)
        if ok.sum() < 12:
            continue
        b = mean_absolute_error(y[ok], pb[ok])
        a = mean_absolute_error(y[ok], pa[ok])
        rows.append({
            "test_season": int(test),
            "n_test": int(ok.sum()),
            "baseline_mae": float(b),
            "augmented_mae": float(a),
            "improvement": float((b - a) / b) if b > 0 else None,
        })

    vals = [r["improvement"] for r in rows if r.get("improvement") is not None]
    weights = [r["n_test"] for r in rows if r.get("improvement") is not None]
    gate = fe.robust_gate(vals, weights)
    gate["sign_flip_p"] = fe.sign_flip_p(vals)
    gate["baseline_model"] = "ridge_prev_fantasy_ppg"
    gate["augmented_model"] = "ridge_prev_fantasy_ppg_plus_feature"
    gate["comparison_rows_identical"] = True
    return rows, gate


def feature_matrix_hardened(df, oos, catalog):
    dedup, meta = deduplicated_catalog(catalog)
    rows, folds = _BASE_FEATURE_MATRIX(df, oos, dedup)
    _apply_family_metadata(rows, meta)
    _apply_family_metadata(folds, meta)
    return rows, folds


def horizon_validation_hardened(df, catalog):
    dedup, meta = deduplicated_catalog(catalog)
    rows = _BASE_HORIZON_VALIDATION(df, dedup)
    _apply_family_metadata(rows, meta)
    return rows


def _oos_key_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in ["season", "week", "canonical_player_id", "position_model"] if c in df.columns]


def build_missing_extended_m4_oos(df: pd.DataFrame, existing_oos: pd.DataFrame, m1: dict, cache_path: Path):
    """Backfill missing pre-2022 M4 holdouts using only earlier seasons.

    Existing canonical M4 OOS rows always win.  Missing seasons are generated with
    the current M4 raw-stat Ridge stack, but feature availability is determined from
    the training partition only.  The backfill is stored under .cache and never
    overwrites the canonical milestone4 OOS artifact.
    """
    from fie_m4 import canonical_scoring, feature_pool, predict_raw_models, fantasy_from_pred

    positions = tuple(fe.POSITIONS)
    existing = existing_oos.copy()
    if not existing.empty:
        existing["season"] = pd.to_numeric(existing["season"], errors="coerce")
    available_seasons = sorted(int(x) for x in pd.to_numeric(df.season, errors="coerce").dropna().unique())
    desired_tests = [s for i, s in enumerate(available_seasons) if i >= 3 and s <= max(available_seasons)]
    existing_tests = set(int(x) for x in existing.season.dropna().unique()) if not existing.empty else set()

    cached = pd.DataFrame()
    if cache_path.exists():
        try:
            cached = pd.read_csv(cache_path, low_memory=False)
        except Exception:
            cached = pd.DataFrame()
    cached_tests = set()
    if not cached.empty and "season" in cached.columns:
        cached_tests = set(int(x) for x in pd.to_numeric(cached["season"], errors="coerce").dropna().unique())

    missing = [s for s in desired_tests if s not in existing_tests and s not in cached_tests]
    scoring = canonical_scoring(m1)
    generated = []

    for test_season in missing:
        # Match canonical M4's 2019 anchor once it is available; only the
        # pre-2022 backfill uses the earlier 2016-2018 extension.
        if test_season >= 2022:
            train_seasons = [s for s in available_seasons if 2019 <= s < test_season]
        else:
            train_seasons = [s for s in available_seasons if s < test_season]
        if len(train_seasons) < 3:
            continue
        for pos in positions:
            z = df[df.position_model.eq(pos)].copy()
            tr = z[z.season.isin(train_seasons)].dropna(subset=["fantasy_points"]).copy()
            te = z[z.season.eq(test_season)].dropna(subset=["fantasy_points"]).copy()
            if len(tr) < 60 or len(te) < 12:
                continue
            # Feature selection is training-only.  This avoids learning from future
            # source availability while preserving the M4 model family.
            fs = feature_pool(tr, pos)
            if len(fs) < 2:
                continue
            pred_stats, _, _ = predict_raw_models(tr, te, pos, fs, export_specs=False)
            if pred_stats.empty:
                continue
            pred = fantasy_from_pred(pred_stats, pos, scoring).reindex(te.index)
            y = pd.to_numeric(te.fantasy_points, errors="coerce")
            ok = y.notna() & pred.notna()
            if ok.sum() < 10:
                continue
            q = te.loc[ok, [c for c in [
                "season", "week", "canonical_player_id", "full_name", "team", "position_model", "fantasy_points"
            ] if c in te.columns]].copy()
            q["fie_projection"] = pred[ok].astype(float)
            if "opportunity_xfp_pregame" in te:
                q["baseline_projection"] = pd.to_numeric(te.loc[ok, "opportunity_xfp_pregame"], errors="coerce")
            elif "fp_prior_4" in te:
                q["baseline_projection"] = pd.to_numeric(te.loc[ok, "fp_prior_4"], errors="coerce")
            else:
                q["baseline_projection"] = np.nan
            q["m4_oos_source"] = "feature_evidence_extended_backfill"
            q["m4_train_start"] = int(min(train_seasons))
            q["m4_train_end"] = int(max(train_seasons))
            generated.append(q)

    new = pd.concat(generated, ignore_index=True) if generated else pd.DataFrame()
    backfill = pd.concat([cached, new], ignore_index=True) if not cached.empty or not new.empty else pd.DataFrame()
    if not backfill.empty:
        keys = _oos_key_cols(backfill)
        backfill = backfill.drop_duplicates(keys, keep="last").sort_values(keys).reset_index(drop=True)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        backfill.to_csv(cache_path, index=False, compression="gzip")

    parts = []
    if not backfill.empty:
        parts.append(backfill)
    if not existing.empty:
        x = existing.copy()
        x["m4_oos_source"] = x.get("m4_oos_source", "canonical_m4")
        parts.append(x)
    combined = pd.concat(parts, ignore_index=True, sort=False) if parts else pd.DataFrame()
    if not combined.empty:
        keys = _oos_key_cols(combined)
        # Existing canonical rows were appended last and therefore win duplicates.
        combined = combined.drop_duplicates(keys, keep="last").sort_values(keys).reset_index(drop=True)

    audit = oos_audit(existing, backfill, combined, available_seasons)
    return combined, audit


def oos_audit(existing: pd.DataFrame, backfill: pd.DataFrame, combined: pd.DataFrame, available_seasons: Sequence[int]) -> dict:
    by_pos = {}
    for pos in fe.POSITIONS:
        z = combined[combined.position_model.eq(pos)] if not combined.empty and "position_model" in combined else pd.DataFrame()
        seasons = []
        if not z.empty and "season" in z.columns:
            seasons = sorted(int(x) for x in pd.to_numeric(z["season"], errors="coerce").dropna().unique())
        second_stage = fe.expanding_folds(seasons, min_train_seasons=3, max_folds=6) if seasons else []
        by_pos[pos] = {
            "oos_seasons": seasons,
            "oos_season_count": len(seasons),
            "second_stage_residual_test_seasons": [int(test) for _, test in second_stage],
            "second_stage_residual_fold_count": len(second_stage),
        }
    return {
        "policy": "canonical M4 OOS rows retained; missing earlier holdouts use current M4 model family with training-only feature availability",
        "production_artifact_overwritten": False,
        "available_feature_frame_seasons": list(map(int, available_seasons)),
        "canonical_oos_rows": int(len(existing)),
        "backfill_oos_rows": int(len(backfill)),
        "combined_oos_rows": int(len(combined)),
        "positions": by_pos,
        "requested_min_second_stage_residual_folds": MIN_RESIDUAL_FOLDS,
    }


def load_extended_core_frame(args):
    """Build an M4-compatible frame from evidence-only 2016+ core derived tables.

    This intentionally skips M3 public enrichment and M2 persisted derived files.
    Its sole purpose is to train leakage-safe early M4 baselines.  Canonical 2019+
    feature evidence continues to use the normal current feature_frame.
    """
    from copy import copy
    from fie_m3 import load_core, ensure_core_priors
    from fie_m2 import add_team_context, add_competition_features, add_position_shares, add_change_signals

    ext = copy(args)
    ext.derived_dir = str(args.extended_derived_dir)
    ext.m1_bundle = str(args.extended_m1_bundle)
    player, team, identity, m1, m2 = load_core(ext)
    player, team = add_team_context(player, team)
    player = add_competition_features(player)
    player = add_position_shares(player)
    if "opportunity_change_score" not in player:
        player = add_change_signals(player)
    player = ensure_core_priors(player)
    d = player.sort_values(["canonical_player_id", "season", "week"]).copy()
    g = d.groupby(["canonical_player_id", "season"], group_keys=False)
    for c in ["xfp_residual", "opportunity_xfp_realized"]:
        if c in d:
            d[f"{c}_prior4"] = g[c].transform(
                lambda x: pd.to_numeric(x, errors="coerce").shift(1).rolling(4, min_periods=2).mean()
            )
    if "opportunity_change_score" in d:
        d["opportunity_change_score_prior1"] = g["opportunity_change_score"].shift(1)
    return d, m1


def load_live_hardened(args):
    # Rebuild the same current feature frame and optional M7 enrichments, then
    # extend only the evidence OOS baseline.
    from fie_m4 import feature_frame
    from fie_m7 import merge_optional_player_charting, add_derived_driver_features, available_catalog, load_oos

    df, team, identity, m1, m2, enrichment = feature_frame(args)
    df, optional = merge_optional_player_charting(df, args)
    df = add_derived_driver_features(df)
    catalog = available_catalog(df)
    canonical_oos = load_oos(args.derived_dir, args.fixture, df)
    if args.fixture:
        extended_df, extended_m1 = df, m1
    else:
        extended_df, extended_m1 = load_extended_core_frame(args)
    cache_path = Path(args.cache_dir) / "feature-evidence" / "m4_extended_oos.csv.gz"
    oos, audit = build_missing_extended_m4_oos(extended_df, canonical_oos, extended_m1, cache_path)
    audit["canonical_feature_frame_seasons"] = sorted(int(x) for x in pd.to_numeric(df.season, errors="coerce").dropna().unique())
    audit["extended_core_frame_seasons"] = sorted(int(x) for x in pd.to_numeric(extended_df.season, errors="coerce").dropna().unique())
    source = {
        "enrichment": enrichment,
        "optional_charting": optional,
        "hardening_oos": audit,
        "hardening_oos_cache": str(cache_path),
    }
    return df, oos, catalog, source


def _tier(q):
    try:
        q = float(q)
        return "tier2_multiplicity_supported" if math.isfinite(q) and q <= .10 else "tier1_temporal_gate_only"
    except Exception:
        return "tier1_temporal_gate_only"


HORIZON_CONSUMERS = {
    "next_week": "weekly_forward_projection",
    "next_3_games": "next3_projection",
    "rest_of_season": "ros_projection",
    "floor": "floor_risk_distribution",
    "ceiling": "ceiling_upside_distribution",
    "breakout": "breakout_probability",
    "next_season": "preseason_projection",
}

COMPONENT_CONSUMERS = {
    "pass_volume": "qb_pass_volume",
    "rush_volume": "qb_rush_volume",
    "completion_rate": "qb_completion_efficiency",
    "yards_per_attempt": "qb_passing_efficiency",
    "carry_volume": "rb_carry_volume",
    "target_volume": "receiving_target_volume",
    "rushing_efficiency": "rb_rushing_efficiency",
    "catch_conversion": "receiving_catch_conversion",
    "yards_per_target": "receiving_efficiency",
}


def build_consumer_routes(bundle: dict) -> List[dict]:
    """Route robust evidence to the correct future consumer without activation."""
    routes = []
    features = bundle.get("phase1_feature_evidence_matrix", [])
    horizons = bundle.get("phase3_multi_horizon_validation", [])
    components = bundle.get("phase2_component_validation", [])

    for r in features:
        gate = r.get("weekly_gate") or {}
        if gate.get("robust"):
            routes.append({
                "position": r["position"], "feature": r["feature"], "source_scope": "weekly_residual",
                "evidence_target": "same_week", "consumer": "weekly_projection_residual",
                "mean_improvement": gate.get("mean"), "fdr_q": r.get("weekly_fdr_q"),
                "evidence_tier": _tier(r.get("weekly_fdr_q")),
            })
        sg = r.get("season_gate") or {}
        if sg.get("robust"):
            routes.append({
                "position": r["position"], "feature": r["feature"], "source_scope": "next_season",
                "evidence_target": "next_season", "consumer": "preseason_projection",
                "mean_improvement": sg.get("mean"), "fdr_q": r.get("season_fdr_q"),
                "evidence_tier": _tier(r.get("season_fdr_q")),
            })

    for r in horizons:
        gate = r.get("gate") or {}
        if not gate.get("robust"):
            continue
        routes.append({
            "position": r["position"], "feature": r["feature"], "source_scope": "horizon",
            "evidence_target": r["horizon"], "consumer": HORIZON_CONSUMERS[r["horizon"]],
            "mean_improvement": gate.get("mean"), "fdr_q": r.get("fdr_q"),
            "evidence_tier": _tier(r.get("fdr_q")),
        })

    for r in components:
        if r.get("feature") == "__all_features__":
            continue
        gate = r.get("gate") or {}
        if not gate.get("robust"):
            continue
        routes.append({
            "position": r["position"], "feature": r["feature"], "source_scope": "component",
            "evidence_target": r["component"], "consumer": COMPONENT_CONSUMERS.get(r["component"], f"component_{r['component']}"),
            "mean_improvement": gate.get("mean"), "fdr_q": r.get("fdr_q"),
            "evidence_tier": _tier(r.get("fdr_q")),
        })

    # One canonical route per hypothesis/consumer/target.
    unique = {}
    for r in routes:
        key = (r["position"], r["feature"], r["source_scope"], r["evidence_target"], r["consumer"])
        r["activation_status"] = "research_only_manual_integration_required"
        r["auto_activation"] = False
        unique[key] = r
    return sorted(unique.values(), key=lambda r: (r["position"], r["consumer"], r["feature"], r["evidence_target"]))


def harden_bundle(bundle: dict) -> dict:
    bundle["research_build"] = BUILD
    bundle["hardening_schema_version"] = HARDENING_SCHEMA
    bundle.setdefault("governance", {}).update({
        "auto_activation": False,
        "production_gate_unchanged": True,
        "extended_oos_is_research_only": True,
        "next_season_baseline": "Ridge(prev_fantasy_ppg) vs Ridge(prev_fantasy_ppg + feature)",
        "hypothesis_deduplication": "one BH-FDR hypothesis per position/feature regardless of semantic family membership",
    })
    routes = build_consumer_routes(bundle)
    bundle["phase7_consumer_routing"] = routes
    bundle["phase7_production_gate"]["consumer_routing_rule"] = (
        "Robust evidence may be routed only to the mechanism/horizon it validated; every route remains research-only until a separate consumer integration is revalidated."
    )
    return bundle


def write_outputs(bundle: dict, outdir: Path):
    fe.write_outputs(bundle, outdir)
    pd.DataFrame(bundle.get("phase7_consumer_routing", [])).to_csv(outdir / "consumer_routing.csv", index=False)
    audit = (bundle.get("source_contract") or {}).get("hardening_oos") or {}
    (outdir / "hardening_audit.json").write_text(json.dumps(fe.json_safe(audit), indent=2, allow_nan=False))
    report = outdir / "FEATURE_EVIDENCE_REPORT.md"
    with report.open("a", encoding="utf-8") as h:
        h.write("\n## Evidence Hardening\n\n")
        h.write("- Extended M4 OOS backfill is research-only and never overwrites the canonical M4 artifact.\n")
        h.write("- Next-season comparisons now use calibrated Ridge baseline vs calibrated Ridge+feature on identical rows.\n")
        h.write("- Feature hypotheses are de-duplicated across semantic families before validation/FDR.\n")
        h.write(f"- Consumer routes emitted: {len(bundle.get('phase7_consumer_routing', []))}; all require manual integration and revalidation.\n")
        for pos, info in ((audit.get("positions") or {}).items()):
            h.write(f"- {pos}: OOS seasons={info.get('oos_seasons')}; second-stage residual folds={info.get('second_stage_residual_fold_count')}.\n")


def install_hardening_wrappers():
    # Base Phase 1 uses its module-global season_feature_gate, so replacing it here
    # also fixes next-season baseline comparisons inside the existing matrix logic.
    fe.season_feature_gate = season_feature_gate_fair
    fe.feature_matrix = feature_matrix_hardened
    fe.horizon_validation = horizon_validation_hardened
    fe.load_live = load_live_hardened


def run(args):
    install_hardening_wrappers()
    bundle = fe.run(args)
    return harden_bundle(bundle)


def self_test():
    # Deduplication is deterministic and preserves all semantic memberships.
    catalog = {
        "QB": {"opportunity": ["a", "b"], "rushing": ["b", "c"]},
        "RB": {}, "WR": {}, "TE": {},
    }
    dedup, meta = deduplicated_catalog(catalog)
    assert dedup["QB"]["deduplicated_hypotheses"] == ["a", "b", "c"]
    assert meta[("QB", "b")]["families"] == ["opportunity", "rushing"]

    # Seven OOS seasons are sufficient for four genuine second-stage residual folds.
    q = pd.DataFrame({
        "season": np.repeat(np.arange(2019, 2026), 4),
        "week": list(range(1, 5)) * 7,
        "canonical_player_id": [f"p{i%4}" for i in range(28)],
        "position_model": ["QB"] * 28,
    })
    audit = oos_audit(pd.DataFrame(), q, q, list(range(2016, 2026)))
    assert audit["positions"]["QB"]["second_stage_residual_test_seasons"] == [2022, 2023, 2024, 2025]

    # Routing is impossible from non-robust evidence and never auto-activates.
    b = {
        "phase1_feature_evidence_matrix": [{
            "position": "QB", "feature": "a", "weekly_gate": {"robust": False},
            "season_gate": {"robust": False}, "weekly_fdr_q": None, "season_fdr_q": None,
        }],
        "phase3_multi_horizon_validation": [{
            "position": "QB", "feature": "a", "horizon": "next_week",
            "gate": {"robust": True, "mean": .02}, "fdr_q": .2,
        }],
        "phase2_component_validation": [],
    }
    routes = build_consumer_routes(b)
    assert len(routes) == 1 and routes[0]["consumer"] == "weekly_forward_projection"
    assert routes[0]["auto_activation"] is False
    print("PASS feature-evidence hardening integrity")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--league-root", required=False, default="data/research")
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--seasons", default="2016-2025")
    p.add_argument("--output-dir", required=False, default="data/research/feature-evidence")
    p.add_argument("--extended-derived-dir", default=None)
    p.add_argument("--extended-m1-bundle", default=None)
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
        self_test()
        return
    bundle = run(args)
    write_outputs(bundle, Path(args.output_dir))
    print(
        f"Wrote hardened feature evidence to {args.output_dir}: "
        f"{len(bundle['phase1_feature_evidence_matrix'])} unique features, "
        f"{len(bundle.get('phase7_consumer_routing', []))} research-only consumer routes"
    )


if __name__ == "__main__":
    main()

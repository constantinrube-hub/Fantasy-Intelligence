#!/usr/bin/env python3
"""Build the V9.6 controlled-runtime model package from accepted production-shadow evidence.

This is the promotion boundary between shadow research and runtime availability.  It
rebuilds the accepted consumers from the same hardened historical frame, requires the
eligible registry to match the committed shadow bundle, and serializes only approved
models.  The runtime package does not itself mutate current snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

import fie_feature_evidence_hardening as fh
import fie_production_shadow as ps
from current_snapshot_storage import load_current_snapshot

BUILD = "V9.6-CONTROLLED-RUNTIME-1"
SCHEMA_VERSION = 1
MODEL_FILENAME = "v96_runtime_models.joblib"
MANIFEST_FILENAME = "v96_runtime.json"

PRIMARY_WEEKLY = {
    "QB": "histgb",
    "RB": "histgb",
}
DIAGNOSTIC_WEEKLY = {
    "RB": "ridge_backfield_competitor_count",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def eligible_ids(registry: list[dict]) -> list[str]:
    return sorted(
        f"{r.get('position')}:{r.get('consumer')}:{r.get('model')}"
        for r in registry
        if r.get("shadow_eligible")
    )


def validate_shadow_for_promotion(shadow: dict, league_id: str) -> list[str]:
    if shadow.get("status") != "complete_shadow_research_only":
        raise RuntimeError("Shadow bundle is not complete_shadow_research_only")
    if not str(shadow.get("shadow_build") or "").startswith("V9.5-PRODUCTION-SHADOW"):
        raise RuntimeError("V9.6 requires a V9.5 production-shadow bundle")
    if str(shadow.get("league_id") or "") != str(league_id):
        raise RuntimeError("Shadow league_id mismatch")
    gov = shadow.get("governance") or {}
    if gov.get("auto_activation") is not False or gov.get("shadow_only") is not True:
        raise RuntimeError("Shadow governance contract is not fail-closed")
    if (shadow.get("promotion_gate") or {}).get("runtime_activation_allowed") is not False:
        raise RuntimeError("Shadow bundle unexpectedly allowed runtime activation")
    eligible = sorted((shadow.get("promotion_gate") or {}).get("shadow_eligible_consumers") or [])
    required = {
        "QB:weekly_projection_residual:histgb",
        "RB:weekly_projection_residual:histgb",
    }
    if not required.issubset(set(eligible)):
        raise RuntimeError("Required QB/RB weekly residual consumers are not shadow eligible")
    forbidden = {
        "WR:weekly_projection_residual:histgb",
        "TE:weekly_projection_residual:histgb",
    }
    if forbidden & set(eligible):
        raise RuntimeError("WR/TE HistGB must remain rejected")
    return eligible


def build(args) -> dict:
    shadow_path = Path(args.shadow_bundle)
    evidence_path = Path(args.evidence_bundle)
    shadow = read_json(shadow_path)
    expected_eligible = validate_shadow_for_promotion(shadow, args.league_id)
    evidence = read_json(evidence_path)
    ps.evidence_contract(evidence)

    # Recreate the exact historical feature/OOS contract used by the accepted shadow run.
    df, oos, catalog, source = fh.load_live_hardened(args)
    registry, fitted = ps.model_registry(evidence, df, oos, catalog)
    rebuilt_eligible = eligible_ids(registry)
    if rebuilt_eligible != expected_eligible:
        missing = sorted(set(expected_eligible) - set(rebuilt_eligible))
        extra = sorted(set(rebuilt_eligible) - set(expected_eligible))
        raise RuntimeError(
            f"Runtime rebuild does not reproduce shadow eligibility; missing={missing} extra={extra}"
        )

    current = load_current_snapshot(args.current_snapshot)
    if not current:
        raise RuntimeError("Current snapshot unavailable")
    if str(current.get("league_id") or "") != str(args.league_id):
        raise RuntimeError("Current snapshot league mismatch")

    profile = read_json(args.league_profile)
    profile_fp = str(current.get("profile_fingerprint") or profile.get("profile_fingerprint") or "")
    scoring_sig = str(current.get("scoring_signature") or profile.get("scoring_signature") or "")
    if not profile_fp or not scoring_sig:
        raise RuntimeError("Cannot build runtime package without profile/scoring identity")

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    model_path = outdir / MODEL_FILENAME

    package = {
        "schema_version": SCHEMA_VERSION,
        "runtime_build": BUILD,
        "league_id": str(args.league_id),
        "report_season": int(args.report_season),
        "profile_fingerprint": profile_fp,
        "scoring_signature": scoring_sig,
        "primary_weekly": dict(PRIMARY_WEEKLY),
        "diagnostic_weekly": dict(DIAGNOSTIC_WEEKLY),
        "eligible_consumers": rebuilt_eligible,
        "registry": registry,
        "fitted": fitted,
    }
    joblib.dump(package, model_path, compress=3)

    # Compact validation summaries are retained in JSON; model internals stay in joblib.
    approved = [r for r in registry if r.get("shadow_eligible")]
    summaries = []
    for r in approved:
        g = r.get("consumer_revalidation_gate") or {}
        summaries.append({
            "position": r.get("position"),
            "consumer": r.get("consumer"),
            "model": r.get("model"),
            "folds": int(g.get("folds") or 0),
            "mean_improvement": g.get("mean"),
            "positive_folds": int(g.get("positive_folds") or 0),
            "ci95_low": g.get("ci95_low"),
            "ci95_high": g.get("ci95_high"),
            "robust": bool(g.get("robust")),
        })

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "runtime_build": BUILD,
        "generated_at": utc_now(),
        "status": "approved_controlled_runtime",
        "league_id": str(args.league_id),
        "league_format": current.get("league_format"),
        "report_season": int(args.report_season),
        "profile_fingerprint": profile_fp,
        "scoring_signature": scoring_sig,
        "model_file": MODEL_FILENAME,
        "model_sha256": sha256_file(model_path),
        "source_shadow": {
            "path": str(shadow_path).replace("\\", "/"),
            "sha256": sha256_file(shadow_path),
            "shadow_build": shadow.get("shadow_build"),
            "generated_at": shadow.get("generated_at"),
        },
        "source_evidence": {
            "path": str(evidence_path).replace("\\", "/"),
            "sha256": sha256_file(evidence_path),
            "research_build": evidence.get("research_build"),
            "generated_at": evidence.get("generated_at"),
        },
        "approved_consumers": rebuilt_eligible,
        "consumer_count": len(rebuilt_eligible),
        "consumer_validation": summaries,
        "governance": {
            "runtime_activation_allowed": True,
            "controlled_runtime_only": True,
            "require_profile_fingerprint_match": True,
            "require_scoring_signature_match": True,
            "require_current_research_compatible": True,
            "require_current_profile_match": True,
            "require_regular_season": True,
            "require_current_season_completed_features": True,
            "require_existing_weekly_activation_for_main_projection": True,
            "minimum_live_feature_coverage": float(args.min_live_coverage),
            "primary_weekly_models": dict(PRIMARY_WEEKLY),
            "rb_alternate_is_diagnostic_only": True,
            "wr_te_histgb_enabled": False,
            "component_consumers_replace_canonical_projection": False,
            "horizon_consumers_replace_canonical_weekly_projection": False,
            "next_season_enabled": False,
            "prior_season_live_fallback": False,
        },
        "source_contract": {
            "hardening_oos": source.get("hardening_oos"),
        },
    }
    manifest_path = outdir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--league-id", required=True)
    p.add_argument("--report-season", type=int, default=2026)
    p.add_argument("--league-root", required=True)
    p.add_argument("--league-profile", required=True)
    p.add_argument("--derived-dir", required=True)
    p.add_argument("--cache-dir", required=True)
    p.add_argument("--extended-derived-dir", required=True)
    p.add_argument("--extended-m1-bundle", required=True)
    p.add_argument("--current-snapshot", required=True)
    p.add_argument("--evidence-bundle", required=True)
    p.add_argument("--shadow-bundle", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--seasons", default="2016-2025")
    p.add_argument("--min-live-coverage", type=float, default=ps.DEFAULT_MIN_LIVE_COVERAGE)
    p.add_argument("--route-source", default="")
    p.add_argument("--qb-coverage-source", default="")
    p.add_argument("--fixture", action="store_true")
    for i in range(1, 10):
        p.add_argument(f"--m{i}-bundle", default=None)
    a = p.parse_args(argv)
    lo, hi = map(int, str(a.seasons).split("-"))
    a.seasons = list(range(lo, hi + 1))
    root = Path(a.league_root)
    for i in range(1, 10):
        if getattr(a, f"m{i}_bundle") is None:
            setattr(a, f"m{i}_bundle", str(root / f"milestone{i}.json"))
    return a


def main(argv=None):
    args = parse_args(argv)
    manifest = build(args)
    print(
        f"Built {manifest['runtime_build']} for league {manifest['league_id']}: "
        f"approved_consumers={manifest['consumer_count']} model_sha256={manifest['model_sha256'][:16]}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tranche 3D / C10-009 evidence-semantics characterization and target contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "semantics": ROOT / "app/core/evidence-semantics.js",
    "projection": ROOT / "app/core/projection-service.js",
    "features": ROOT / "app/current-player-features.js",
    "snapshot": ROOT / "app/current-snapshot-store.js",
    "decision_ui": ROOT / "app/decision-ui.js",
    "dst": ROOT / "app/dst-intelligence.js",
    "kicker": ROOT / "app/kicker-intelligence.js",
}

def text(key: str, *, required: bool = True) -> str:
    p = FILES[key]
    if not p.exists():
        if required:
            raise AssertionError(f"required Tranche 3D surface missing: {p.relative_to(ROOT)}")
        return ""
    return p.read_text(encoding="utf-8", errors="replace")

def has_any(s: str, *needles: str) -> bool:
    low = s.lower()
    return any(n.lower() in low for n in needles)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["baseline", "target"], default="baseline")
    args = ap.parse_args()

    projection = text("projection")
    features = text("features")
    snapshot = text("snapshot")
    decision_ui = text("decision_ui")
    dst = text("dst")
    kicker = text("kicker")
    semantics = text("semantics", required=args.mode == "target")

    # Existing good semantics that C10-009 must preserve.
    projection_source = "source:" in projection
    projection_confidence = "confidence:" in projection
    explicit_available = "availability:'available'" in projection
    explicit_unavailable = "availability:'unavailable'" in projection
    explicit_bye = "reason:'BYE'" in projection and "isBye:true" in projection
    true_zero_bye = "value:0" in projection and explicit_bye
    missing_null = "value:null" in projection and explicit_unavailable
    season_div_17 = "seasonV/17" in projection
    season_baseline = "source:'Season baseline'" in projection
    calibrated_range = "calibrated:true" in projection
    heuristic_range = "calibrated:false" in projection and "Heuristic fallback" in projection
    feature_freshness = "asOfCompletedWeek" in features
    snapshot_freshness = has_any(snapshot, "generated_at", "generatedAt", "as_of", "asOf")
    dst_local = (
        "function currentRange" in dst
        and "source:'FIE empirical'" in dst
        and "'Baseline Estimate'" in dst
        and "estimate" in dst
        and "published*.78" in dst
        and "published*1.22" in dst
    )
    kicker_local = (
        "function currentRange" in kicker
        and "source:'FIE empirical'" in kicker
        and "'Baseline Estimate'" in kicker
        and "estimate" in kicker
        and "published*.78" in kicker
        and "published*1.22" in kicker
    )
    signal_lineage = "signalLineage" in features
    ui_evidence_language = has_any(decision_ui, "confidence", "source", "evidence", "projection")

    typed_contract = all(token in semantics for token in [
        "EvidenceStatus",
        "UncertaintyKind",
        "modeled_available",
        "modeled_unavailable",
        "observed",
        "calibrated_range",
        "heuristic_range",
        "not_applicable",
        "leagueLocalProvenance",
    ])
    adapters = {
        "projection": "installProjection" in semantics and "FIEProjectionResolver" in semantics,
        "current_features": "installFeatures" in semantics and "FIECurrentFeatures" in semantics,
        "current_snapshot": "installSnapshot" in semantics and "FIECurrentSnapshotStore" in semantics,
        "dst": "FIEDST" in semantics and "decorateSpecialistRow" in semantics,
        "kicker": "FIEKicker" in semantics and "decorateSpecialistRow" in semantics,
    }
    bootstrap = (
        "app/core/evidence-semantics.js" in snapshot
        and "data-fie-evidence-semantics" in snapshot
        and "bootEvidenceSemantics" in snapshot
    )
    legacy_math_preserved = all([
        "seasonV/17" in projection,
        "published*.78" in dst,
        "published*1.22" in dst,
        "published*.78" in kicker,
        "published*1.22" in kicker,
    ])

    result = {
        "mode": args.mode,
        "preserved": {
            "projection_source": projection_source,
            "projection_confidence": projection_confidence,
            "availability_available": explicit_available,
            "availability_unavailable": explicit_unavailable,
            "verified_bye_explicit": explicit_bye,
            "verified_bye_true_zero": true_zero_bye,
            "missing_data_null": missing_null,
            "season_div_17_heuristic": season_div_17,
            "season_baseline_label": season_baseline,
            "calibrated_range": calibrated_range,
            "heuristic_range": heuristic_range,
            "feature_completed_week_freshness": feature_freshness,
            "snapshot_provenance_language": snapshot_freshness,
            "dst_local_semantics": dst_local,
            "kicker_local_semantics": kicker_local,
            "current_feature_signal_lineage": signal_lineage,
            "decision_ui_evidence_language": ui_evidence_language,
            "legacy_projection_math": legacy_math_preserved,
        },
        "target": {
            "typed_contract": typed_contract,
            "runtime_bootstrap": bootstrap,
            "adapters": adapters,
        },
    }

    required_good = [
        projection_source, projection_confidence, explicit_available, explicit_unavailable,
        explicit_bye, true_zero_bye, missing_null, season_div_17, season_baseline,
        calibrated_range, heuristic_range, dst_local, kicker_local, signal_lineage,
        legacy_math_preserved,
    ]
    if not all(required_good):
        print(json.dumps(result, sort_keys=True))
        raise AssertionError("Tranche 3D lost a pre-existing evidence or projection semantic")

    if args.mode == "baseline":
        if typed_contract:
            print(json.dumps(result, sort_keys=True))
            raise AssertionError("Expected C10-009 baseline gap is no longer present; use --mode target")
        print("KNOWN_GAP_REPRODUCED evidence semantics are fragmented across projection and specialist surfaces")
        print(json.dumps(result, sort_keys=True))
        return 0

    if not typed_contract:
        print(json.dumps(result, sort_keys=True))
        raise AssertionError("C10-009 target missing canonical typed evidence contract")
    if not bootstrap:
        print(json.dumps(result, sort_keys=True))
        raise AssertionError("C10-009 target missing browser bootstrap for canonical evidence owner")
    missing = [k for k, v in adapters.items() if not v]
    if missing:
        print(json.dumps(result, sort_keys=True))
        raise AssertionError(f"C10-009 target missing canonical runtime adapters: {missing}")

    print("PASS Tranche 3D shared typed evidence semantics across projection, current and specialist API surfaces")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

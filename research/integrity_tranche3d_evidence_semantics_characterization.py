#!/usr/bin/env python3
"""Tranche 3D / C10-009 baseline characterization.

This test intentionally proves that useful evidence semantics already exist, but
remain fragmented across projection and specialist surfaces. It MUST fail if the
known baseline gap disappears unexpectedly; the target implementation will
replace this baseline-mode assertion with a typed-contract target test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "projection": ROOT / "app/core/projection-service.js",
    "features": ROOT / "app/current-player-features.js",
    "snapshot": ROOT / "app/current-snapshot-store.js",
    "decision_ui": ROOT / "app/decision-ui.js",
    "dst": ROOT / "app/dst-intelligence.js",
    "kicker": ROOT / "app/kicker-intelligence.js",
}

def text(key: str) -> str:
    p = FILES[key]
    if not p.exists():
        raise AssertionError(f"required Tranche 3D surface missing: {p.relative_to(ROOT)}")
    return p.read_text(encoding="utf-8", errors="replace")

def has_any(s: str, *needles: str) -> bool:
    low = s.lower()
    return any(n.lower() in low for n in needles)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["baseline"], default="baseline")
    args = ap.parse_args()

    projection = text("projection")
    features = text("features")
    snapshot = text("snapshot")
    decision_ui = text("decision_ui")
    dst = text("dst")
    kicker = text("kicker")

    # Existing good semantics that must not be lost by C10-009.
    projection_source = "source:" in projection
    projection_confidence = "confidence:" in projection
    explicit_available = "availability:'available'" in projection
    explicit_unavailable = "availability:'unavailable'" in projection
    explicit_bye = "reason:'BYE'" in projection and "isBye:true" in projection
    true_zero_bye = "value:0" in projection and explicit_bye
    missing_null = "value:null" in projection and explicit_unavailable

    # Audited heuristic/fallback seam.
    season_div_17 = "seasonV/17" in projection
    season_baseline = "source:'Season baseline'" in projection
    calibrated_range = "calibrated:true" in projection
    heuristic_range = "calibrated:false" in projection and "Heuristic fallback" in projection

    # Freshness/provenance exists, but is represented differently by surface.
    feature_freshness = "asOfCompletedWeek" in features
    snapshot_freshness = has_any(snapshot, "generated_at", "generatedAt", "as_of", "asOf")
    projection_asof = has_any(projection, "asOf", "as_of")
    dst_asof = has_any(dst, "asOf", "as_of")
    kicker_asof = has_any(kicker, "asOf", "as_of")

    # Specialist layers use their own source/estimate/range vocabulary.
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

    # Multiple lineage/explainability concepts exist independently.
    signal_lineage = "signalLineage" in features
    ui_evidence_language = has_any(decision_ui, "confidence", "source", "evidence", "projection")
    snapshot_provenance_language = has_any(snapshot, "source", "lineage", "generated_at", "as_of")

    all_surface_text = "\n".join([projection, features, snapshot, decision_ui, dst, kicker]).lower()
    typed_uncertainty_kind = any(k in all_surface_text for k in (
        "uncertaintykind", "uncertainty_kind", "uncertaintyclass", "uncertainty_class"
    ))
    typed_evidence_status = any(k in all_surface_text for k in (
        "evidencestatus", "evidence_status"
    ))

    # We intentionally do not count generic `status` or `confidence` fields as a
    # shared typed evidence contract. C10-009 requires a canonical semantic owner.
    shared_typed_contract = typed_uncertainty_kind and typed_evidence_status

    result = {
        "mode": args.mode,
        "projection": {
            "source_present": projection_source,
            "confidence_present": projection_confidence,
            "availability_available_present": explicit_available,
            "availability_unavailable_present": explicit_unavailable,
            "verified_bye_explicit": explicit_bye,
            "verified_bye_true_zero": true_zero_bye,
            "missing_data_null": missing_null,
            "season_div_17_heuristic_present": season_div_17,
            "season_baseline_label_present": season_baseline,
            "calibrated_range_present": calibrated_range,
            "heuristic_range_present": heuristic_range,
            "shared_as_of_field_present": projection_asof,
        },
        "freshness": {
            "current_feature_as_of_completed_week": feature_freshness,
            "snapshot_has_freshness_or_provenance_language": snapshot_freshness,
            "projection_as_of": projection_asof,
            "dst_as_of": dst_asof,
            "kicker_as_of": kicker_asof,
        },
        "specialists": {
            "dst_local_evidence_semantics": dst_local,
            "kicker_local_evidence_semantics": kicker_local,
        },
        "other_surfaces": {
            "current_feature_signal_lineage": signal_lineage,
            "decision_ui_evidence_language": ui_evidence_language,
            "snapshot_provenance_language": snapshot_provenance_language,
        },
        "shared": {
            "typed_uncertainty_kind_present": typed_uncertainty_kind,
            "typed_evidence_status_present": typed_evidence_status,
            "typed_contract_present": shared_typed_contract,
        },
    }

    required_good = [
        projection_source,
        projection_confidence,
        explicit_available,
        explicit_unavailable,
        explicit_bye,
        true_zero_bye,
        missing_null,
        season_div_17,
        season_baseline,
        calibrated_range,
        heuristic_range,
        dst_local,
        kicker_local,
        signal_lineage,
    ]
    if not all(required_good):
        print(json.dumps(result, sort_keys=True))
        raise AssertionError("Tranche 3D preflight could not reproduce the audited evidence-semantics baseline")

    if shared_typed_contract:
        print(json.dumps(result, sort_keys=True))
        raise AssertionError(
            "Expected C10-009 baseline gap is no longer present; re-audit before applying the planned target"
        )

    print("KNOWN_GAP_REPRODUCED evidence semantics are fragmented across projection and specialist surfaces")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

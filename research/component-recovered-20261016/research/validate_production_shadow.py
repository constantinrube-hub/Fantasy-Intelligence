#!/usr/bin/env python3
"""Fail-closed validator for FIE production-shadow bundles."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_STATUS = "complete_shadow_research_only"
MIN_FOLDS = 4


def validate(bundle: dict) -> list[str]:
    errors = []
    if bundle.get("status") != ALLOWED_STATUS:
        errors.append(f"status must be {ALLOWED_STATUS}")
    if not str(bundle.get("shadow_build") or "").startswith("V9.5-PRODUCTION-SHADOW"):
        errors.append("unexpected shadow_build")
    gov = bundle.get("governance") or {}
    for k in ["auto_activation", "runtime_projection_modified", "canonical_current_snapshot_modified", "dist_modified"]:
        if gov.get(k) is not False:
            errors.append(f"governance.{k} must be false")
    if gov.get("shadow_only") is not True:
        errors.append("governance.shadow_only must be true")
    ec = bundle.get("evidence_contract") or {}
    if not str(ec.get("research_build") or "").startswith("V9.4-FEATURE-EVIDENCE-HARDENED"):
        errors.append("hardened evidence contract missing")
    if ec.get("auto_activation") is not False or ec.get("production_gate_unchanged") is not True:
        errors.append("evidence governance mismatch")
    for pos in ("QB", "RB", "WR", "TE"):
        if int((ec.get("hardening_fold_counts") or {}).get(pos) or 0) < MIN_FOLDS:
            errors.append(f"{pos} hardened fold count < {MIN_FOLDS}")

    reg = bundle.get("shadow_model_registry") or []
    # Only QB/RB may have HistGB shadow eligibility from the accepted evidence run.
    for r in reg:
        if r.get("model") == "histgb" and r.get("shadow_eligible") and r.get("position") not in {"QB", "RB"}:
            errors.append(f"forbidden HistGB shadow eligibility for {r.get('position')}")
        if r.get("shadow_eligible"):
            g = r.get("consumer_revalidation_gate") or {}
            if not g.get("robust") or int(g.get("folds") or 0) < MIN_FOLDS:
                errors.append(f"eligible consumer lacks robust {MIN_FOLDS}-fold revalidation: {r.get('position')} {r.get('consumer')} {r.get('model')}")
        if r.get("position") == "RB" and r.get("model") in {"histgb", "ridge_backfield_competitor_count"}:
            if "standalone" not in str(r.get("stack_policy") or "") and "alternate" not in str(r.get("stack_policy") or ""):
                errors.append("RB weekly shadow candidate lacks no-stack policy")

    pg = bundle.get("promotion_gate") or {}
    if pg.get("runtime_activation_allowed") is not False:
        errors.append("runtime activation must remain false")
    cur = bundle.get("current_shadow") or {}
    for group in ("weekly_candidates", "component_predictions", "horizon_predictions"):
        for row in cur.get(group) or []:
            if row.get("shadow_only") is not True or row.get("auto_activation") is not False:
                errors.append(f"{group} contains non-shadow row")
    return errors


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("bundle")
    a = p.parse_args(argv)
    b = json.loads(Path(a.bundle).read_text(encoding="utf-8"))
    errors = validate(b)
    if errors:
        for e in errors:
            print("ERROR:", e)
        raise SystemExit(1)
    print(
        "PASS production-shadow validation "
        f"eligible={len((b.get('promotion_gate') or {}).get('shadow_eligible_consumers') or [])} "
        f"current_status={(b.get('current_shadow') or {}).get('status')}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

MIN_RESIDUAL_FOLDS = 4


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle")
    a = p.parse_args()
    b = json.loads(Path(a.bundle).read_text())

    assert b.get("hardening_schema_version") == 1
    assert b.get("research_build") == "V9.4-FEATURE-EVIDENCE-HARDENED-1"
    gov = b.get("governance") or {}
    assert gov.get("auto_activation") is False
    assert gov.get("production_gate_unchanged") is True
    assert gov.get("extended_oos_is_research_only") is True

    features = b.get("phase1_feature_evidence_matrix") or []
    ids = [(r.get("position"), r.get("feature")) for r in features]
    dup = [k for k, n in Counter(ids).items() if n > 1]
    assert not dup, f"duplicate feature hypotheses remain: {dup[:5]}"
    assert all(r.get("hypothesis_id") == f"{r.get('position')}:{r.get('feature')}" for r in features)

    horizons = b.get("phase3_multi_horizon_validation") or []
    hzids = [(r.get("position"), r.get("feature"), r.get("horizon")) for r in horizons]
    hzdup = [k for k, n in Counter(hzids).items() if n > 1]
    assert not hzdup, f"duplicate horizon hypotheses remain: {hzdup[:5]}"

    for r in features:
        sg = r.get("season_gate") or {}
        if sg.get("folds", 0):
            assert sg.get("baseline_model") == "ridge_prev_fantasy_ppg"
            assert sg.get("augmented_model") == "ridge_prev_fantasy_ppg_plus_feature"
            assert sg.get("comparison_rows_identical") is True

    audit = (b.get("source_contract") or {}).get("hardening_oos") or {}
    assert audit.get("production_artifact_overwritten") is False
    pos_audit = audit.get("positions") or {}
    for pos in ("QB", "RB", "WR", "TE"):
        info = pos_audit.get(pos) or {}
        folds = int(info.get("second_stage_residual_fold_count") or 0)
        assert folds >= MIN_RESIDUAL_FOLDS, f"{pos} has only {folds} second-stage residual folds"

    robust_horizon = {
        (r["position"], r["feature"], r["horizon"])
        for r in horizons if (r.get("gate") or {}).get("robust")
    }
    robust_component = {
        (r["position"], r["feature"], r["component"])
        for r in (b.get("phase2_component_validation") or [])
        if r.get("feature") != "__all_features__" and (r.get("gate") or {}).get("robust")
    }
    robust_weekly = {
        (r["position"], r["feature"])
        for r in features if (r.get("weekly_gate") or {}).get("robust")
    }
    robust_season = {
        (r["position"], r["feature"])
        for r in features if (r.get("season_gate") or {}).get("robust")
    }

    routes = b.get("phase7_consumer_routing") or []
    for r in routes:
        assert r.get("auto_activation") is False
        assert r.get("activation_status") == "research_only_manual_integration_required"
        scope = r.get("source_scope")
        if scope == "horizon":
            assert (r["position"], r["feature"], r["evidence_target"]) in robust_horizon
        elif scope == "component":
            assert (r["position"], r["feature"], r["evidence_target"]) in robust_component
        elif scope == "weekly_residual":
            assert (r["position"], r["feature"]) in robust_weekly
        elif scope == "next_season":
            assert (r["position"], r["feature"]) in robust_season
        else:
            raise AssertionError(f"unknown consumer route scope: {scope}")

    print(
        f"PASS hardened feature evidence: {len(features)} unique features, "
        f"{len(routes)} research-only routes, >=4 residual folds per offense position"
    )


if __name__ == "__main__":
    main()

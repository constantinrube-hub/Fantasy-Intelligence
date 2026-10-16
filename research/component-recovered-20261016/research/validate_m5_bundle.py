#!/usr/bin/env python3
"""Validate an FIE M5 decision-policy bundle.

The validator accepts legacy revisions 1-3 and the decision-quality waiver
contract (revision 4). Revision 2 separated waiver promotion from the same-week
M4 gate; revision 3 requires enough chronological holdout seasons; revision 4
additionally requires waiver activation to pass both point-forecast and ranking-
decision validation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LEGACY_FORMATS = {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED"}
CURRENT_FORMATS = LEGACY_FORMATS | {"CHOPPED_BESTBALL"}


def validate_bundle(b: dict) -> None:
    assert b.get("schema_version") == 5
    assert b.get("milestone") == "M5"
    assert b.get("research_build") == "V8.7-M5"
    assert b.get("control_build") == "V8.2.2"
    assert b.get("steps_completed") == [24, 25, 26, 27]
    assert b.get("integration_mode") == "fail_closed_conditional"

    revision = int(b.get("contract_revision") or 1)
    expected_formats = CURRENT_FORMATS if revision >= 5 else LEGACY_FORMATS

    activation = b.get("activation", {})
    assert activation.get("policy") == "fail_closed"
    assert activation.get("requires_current_snapshot") is True
    assert activation.get("fallback") == "V8.2.2 live decision logic"
    assert str(activation.get("current_snapshot_path", "")).endswith("milestone5_current.json")
    assert isinstance(b.get("scoring_settings", {}), dict)

    gates = activation.get("decision_gates", {})
    for key in [
        "weekly_mean_positions",
        "weekly_risk_positions",
        "draft_policy_positions",
        "waiver_policy_positions",
        "validated_format_profiles",
    ]:
        assert isinstance(gates.get(key, []), list), key

    upstream = set(activation.get("upstream_validated_positions", []) or [])
    weekly = set(gates.get("weekly_mean_positions", []) or [])
    weekly_risk = set(gates.get("weekly_risk_positions", []) or [])
    draft = set(gates.get("draft_policy_positions", []) or [])
    waiver = set(gates.get("waiver_policy_positions", []) or [])

    # Same-week and draft policies still depend on the upstream M4 production
    # model. Risk bands additionally require the weekly mean gate.
    assert weekly.issubset(upstream)
    assert draft.issubset(upstream)
    assert weekly_risk.issubset(weekly)

    # Waiver next-3 prediction is independently time-validated in M5.  Do NOT
    # force it to be a subset of the same-week M4 gate.  It must, however,
    # exactly reflect the positions whose M5 waiver aggregate passed promotion.
    waiver_validated = {
        r.get("position")
        for r in b.get("waiver_integration", {}).get("aggregate", [])
        if r.get("position") and r.get("status") == "validated_candidate"
    }
    assert waiver == waiver_validated, (sorted(waiver), sorted(waiver_validated))

    format_gates = gates.get("format_position_gates", {})
    assert set(format_gates) == expected_formats
    for key, vals in format_gates.items():
        assert isinstance(vals, list), key

    for section in ["draft_integration", "waiver_integration", "weekly_integration", "format_strategy", "runtime_contract"]:
        assert section in b, section

    profiles = b["format_strategy"].get("profiles", {})
    assert set(profiles) == expected_formats
    for key, value in profiles.items():
        for weight_key in ["draft_weights", "waiver_weights"]:
            weights = value.get(weight_key, {})
            assert weights and abs(sum(float(x) for x in weights.values()) - 1.0) < 1e-9, (key, weight_key, weights)

    for row in b["weekly_integration"].get("risk_bands", []):
        vals = [row.get("q10"), row.get("q25"), row.get("q50"), row.get("q75"), row.get("q90")]
        if all(x is not None for x in vals):
            assert vals == sorted(vals), (row.get("position"), vals)

    runtime = b.get("runtime_contract", {})
    required = set(runtime.get("required_player_fields", []) or [])
    assert {"decision_weekly_projection", "p10", "p90", "activation_eligible", "projection_source"}.issubset(required)

    # Revision 2 exposes independent weekly/waiver eligibility and
    # decision-specific format gates.  Revision 1 remains valid for already
    # migrated historical Redraft bundles, so deployment does not require a
    # destructive rebuild merely to satisfy the newer validator.
    if revision >= 2:
        specific_fields = set(runtime.get("decision_specific_player_fields", []) or [])
        assert {"weekly_activation_eligible", "waiver_activation_eligible", "waiver_feature_coverage"}.issubset(specific_fields)

        decision_format = gates.get("decision_format_position_gates", {})
        assert set(decision_format) == {"weekly", "draft", "waiver"}
        base = {"weekly": weekly, "draft": draft, "waiver": waiver}
        for decision, by_format in decision_format.items():
            assert set(by_format) == expected_formats, decision
            for fmt, vals in by_format.items():
                assert isinstance(vals, list), (decision, fmt)
                assert set(vals).issubset(base[decision]), (decision, fmt, vals, sorted(base[decision]))

    if revision >= 3:
        waiver_meta = b.get("waiver_integration", {}).get("model_specs", {}) or {}
        required_folds = int(waiver_meta.get("required_promotion_folds") or 4)
        max_folds = int(waiver_meta.get("max_valid_folds") or 0)
        seasons = waiver_meta.get("available_test_seasons") or []
        assert required_folds >= 4
        assert max_folds >= required_folds, (max_folds, required_folds, seasons)
        assert len(set(seasons)) >= required_folds, seasons

    if revision >= 4:
        for row in b.get("waiver_integration", {}).get("aggregate", []) or []:
            assert row.get("forecast_status") in {"validated_candidate", "diagnostic_only"}, row
            assert row.get("decision_ranking_status") in {"validated_candidate", "diagnostic_only"}, row
            for key in [
                "mean_spearman", "mean_baseline_spearman", "mean_spearman_improvement_vs_recent_fp",
                "mean_top_quartile_precision", "mean_baseline_top_quartile_precision",
                "mean_top1_regret", "mean_baseline_top1_regret",
            ]:
                assert key in row, (row.get("position"), key)
            if row.get("status") == "validated_candidate":
                assert row.get("forecast_status") == "validated_candidate", row.get("position")
                assert row.get("decision_ranking_status") == "validated_candidate", row.get("position")

    text = json.dumps(b)
    if revision >= 5:
        fmt = gates.get("format_position_gates", {})
        decision_fmt = gates.get("decision_format_position_gates", {})
        assert "CHOPPED_BESTBALL" in fmt
        for decision in ("weekly", "draft", "waiver"):
            assert "CHOPPED_BESTBALL" in decision_fmt.get(decision, {}), decision
        # The hybrid can never activate a position absent from either constituent
        # format. This is the fail-closed composition rule.
        hybrid = set(fmt["CHOPPED_BESTBALL"])
        assert hybrid.issubset(set(fmt.get("CHOPPED", [])))
        assert hybrid.issubset(set(fmt.get("REDRAFT_BESTBALL", [])))
        for decision in ("weekly", "draft", "waiver"):
            by = decision_fmt[decision]
            h = set(by["CHOPPED_BESTBALL"])
            assert h.issubset(set(by.get("CHOPPED", []))), decision
            assert h.issubset(set(by.get("REDRAFT_BESTBALL", []))), decision

    assert "unconditional_activation" not in text


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0] if argv else "data/research/milestone5.json")
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    bundle = json.loads(path.read_text())
    validate_bundle(bundle)
    revision = int(bundle.get("contract_revision") or 1)
    print(f"OK {path}: M5 schema/guardrails validated contract_revision={revision}")


if __name__ == "__main__":
    main()

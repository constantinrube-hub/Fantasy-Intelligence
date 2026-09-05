#!/usr/bin/env python3
"""Static integrity checks for the Sol-authored Tranche 7C-R8 boundary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    design = json.loads((ROOT / "config/m10-prospective-operational-runner-design.json").read_text(encoding="utf-8"))
    doc = (ROOT / "docs/audits/TRANCHE7CR8_OPERATIONAL_RUNNER_DESIGN.md").read_text(encoding="utf-8")
    state = (ROOT / "docs/audits/AUDIT_CURRENT_STATE.md").read_text(encoding="utf-8")
    rollout = (ROOT / "docs/audits/TRANCHE7C_DEFAULT_BRANCH_ROLLOUT_DESIGN.md").read_text(encoding="utf-8")

    assert design["schema"] == "fie-m10-prospective-operational-runner-design-v1"
    assert design["review_model"] == "GPT-5.6 Sol High"
    assert design["research_only"] and design["production_model"] == "M9"
    assert not any(design[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration"))
    assert design["r7_disposition"]["activation_eligible"] is False
    assert design["r7_disposition"]["copy_to_canonical_lock_path"] is False

    corrected = design["r8a_corrected_lock"]
    assert corrected["schema"] == "fie-m10-prospective-season-lock-v2"
    assert corrected["shared_feature_owner"] and corrected["historical_prospective_parity_required"]
    assert corrected["team_change_policy"]["team_budget_follows_old_team"] is False
    required = {
        "training_matrix_sha256", "row_identity_manifest_sha256", "feature_contract_sha256",
        "target_contract_sha256", "dependency_lock_sha256", "scorer_sha256",
        "training_code_manifest_sha256", "candidate_config_sha256", "rollout_design_sha256",
        "residual_samples_sha256", "residual_manifest_sha256", "model_parameter_sha256",
    }
    assert set(corrected["required_hashes"]) == required
    assert corrected["activation_guard_rejects"] == ["fie-m10-prospective-season-lock-v1"]

    residual = design["residual_distribution"]
    assert residual["quantiles"] == [0.1, 0.25, 0.5, 0.75, 0.9]
    assert residual["shared_declared_outer_folds"] and residual["same_eligible_rows"]
    assert "not_joint_simulation" in residual["interpretation"]
    assert design["weekly_producer"]["trains_or_selects"] is False
    assert design["workflow"]["scheduled_write_ref"] == "refs/heads/main"
    assert design["workflow"]["force_push"] is False
    assert design["workflow"]["audit_target_real_evidence_write"] is False
    assert design["current_terra_authority"] == "R8A_corrected_lock_preflight_only"

    for text in (doc, state, rollout):
        assert "R8A" in text and "M9" in text
    assert "not eligible for activation" in doc
    assert "one full personal release gate" in doc
    print("PASS Tranche 7C-R8 Sol operational-runner design is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

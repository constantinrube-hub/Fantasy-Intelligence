#!/usr/bin/env python3
"""Static boundary for the Sol-designed Tranche 7C-R operational rollout."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "config/m10-prospective-rollout-design.json"
DOC = ROOT / "docs/audits/TRANCHE7C_DEFAULT_BRANCH_ROLLOUT_DESIGN.md"


def main() -> int:
    value = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert value["schema"] == "fie-m10-prospective-rollout-design-v1"
    assert value["phase"] == "7C-R" and value["review_model"] == "GPT-5.6 Sol High"
    assert value["source_closure"] == "cd3d5f76c5c2032d23c68b9119cca042ff59aa1b"
    assert value["activation_branch"] == "main" and value["implementation_model"] == "GPT-5.6 Terra High"
    assert value["production_model"] == "M9" and value["research_only"] is True
    assert not any(value[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "automatic_promotion"))
    lock = value["season_lock"]
    assert lock["season"] == 2026 and max(lock["training_target_seasons"]) == 2025
    assert lock["forbidden_outcome_seasons"] == [2026] and lock["scheduled_refit"] is False
    assert lock["portable_model_format"] == "canonical_json_only"
    domains = value["target_domain_policy"]
    assert "rushing_yards" in domains["continuous_targets"] and "carries" in domains["count_targets"]
    assert domains["continuous_observations"] == "finite_negative_values_preserved"
    assert domains["missing_observations"] == "remain_null_and_excluded_per_target"
    assert domains["prediction_floor_scope"] == "post_inference_only_never_training_labels"
    weekly = value["weekly_capture"]
    assert weekly["window_hours"] == 18 and weekly["same_eligible_rows"] is True
    assert weekly["all_enabled_profiles_required"] is True and weekly["expected_enabled_leagues_at_design"] == 22
    assert weekly["historical_reconstruction"] is False
    assert set(weekly["models"]) == {"M9", "M10_LINEAR", "M10_HGB"}
    assert set(weekly["positions"]) == {"QB", "RB", "WR", "TE"}
    assert value["workflow"]["scheduled_write_branch"] == "main"
    forbidden = set(value["forbidden_inputs"])
    assert {"ADP", "market_price", "Sleeper_fantasy_projection", "replacement_economics", "production_recommendation"} <= forbidden
    text = DOC.read_text(encoding="utf-8")
    for phrase in ("first-write immutable", "maximum absolute error", "No market projection", "merge of the validated rollout to `main`", "four-completed-outer-season", "continuous yardage labels"):
        assert phrase in text, phrase
    print("PASS Tranche 7C-R Sol design: default-branch evidence rollout is bounded, immutable, and non-production")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

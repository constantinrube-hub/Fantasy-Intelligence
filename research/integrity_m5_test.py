#!/usr/bin/env python3
"""Small deterministic M5 policy and validator integrity checks."""
from fie_m5 import WAIVER_FEATURES, format_strategy, waiver_temporal_folds
from validate_m5_bundle import validate_bundle
import pandas as pd

# Format policy weights must remain normalized and strategy-specific.
obj = format_strategy(
    [{"position": "WR", "status": "validated_candidate"}] * 4,
    [{"position": "WR", "status": "validated_candidate"}] * 4,
    {"young_player_model": {"aggregate": [{"variant": "preseason", "status": "validated_candidate"}]}},
    pd.DataFrame(columns=["season", "week", "position_model", "fantasy_points", "fie_projection", "baseline_projection"]),
)
profiles = obj["profiles"]
assert set(profiles) == {"REDRAFT", "DYNASTY", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED"}
for key, value in profiles.items():
    assert abs(sum(value["draft_weights"].values()) - 1) < 1e-9
    assert abs(sum(value["waiver_weights"].values()) - 1) < 1e-9
assert profiles["REDRAFT"]["draft_weights"] != profiles["DYNASTY"]["draft_weights"]
assert profiles["REDRAFT_BESTBALL"]["draft_weights"] != profiles["CHOPPED"]["draft_weights"]

# Waiver validation must be able to satisfy its four-fold promotion rule on
# the seven-season historical backbone. It must not be restricted to later M4
# OOS rows and should not depend on an M4 FIE projection feature.
wf = waiver_temporal_folds(pd.DataFrame({"season": [2019, 2020, 2021, 2022, 2023, 2024, 2025]}))
assert [test for _, test in wf] == [2021, 2022, 2023, 2024, 2025], wf
assert all(max(train) < test for train, test in wf)
assert "fie_projection" not in WAIVER_FEATURES

# Regression guard for the August 2026 failure: revision-2 waiver promotion is
# independent from upstream weekly M4 promotion, and the validator must accept
# that contract rather than requiring the literal text "activation_eligible=true".
formats = {"REDRAFT": [], "DYNASTY": [], "REDRAFT_BESTBALL": [], "DYNASTY_BESTBALL": [], "CHOPPED": []}
bundle = {
    "schema_version": 5,
    "milestone": "M5",
    "research_build": "V8.7-M5",
    "control_build": "V8.2.2",
    "contract_revision": 2,
    "steps_completed": [24, 25, 26, 27],
    "integration_mode": "fail_closed_conditional",
    "scoring_settings": {},
    "activation": {
        "policy": "fail_closed",
        "requires_current_snapshot": True,
        "current_snapshot_path": "data/research/leagues/123/current/milestone5_current.json",
        "fallback": "V8.2.2 live decision logic",
        "upstream_validated_positions": ["QB"],
        "decision_gates": {
            "weekly_mean_positions": ["QB"],
            "weekly_risk_positions": [],
            "draft_policy_positions": ["QB"],
            "waiver_policy_positions": ["WR"],
            "validated_format_profiles": [],
            "format_position_gates": formats,
            "decision_format_position_gates": {
                "weekly": {**formats, "REDRAFT": ["QB"]},
                "draft": {**formats, "REDRAFT": ["QB"]},
                "waiver": {**formats, "REDRAFT": ["WR"]},
            },
        },
    },
    "draft_integration": {},
    "waiver_integration": {"aggregate": [{"position": "WR", "status": "validated_candidate"}]},
    "weekly_integration": {"risk_bands": []},
    "format_strategy": {
        "profiles": {
            key: {"draft_weights": {"x": 1.0}, "waiver_weights": {"x": 1.0}}
            for key in formats
        }
    },
    "runtime_contract": {
        "required_player_fields": ["decision_weekly_projection", "p10", "p90", "activation_eligible", "projection_source"],
        "decision_specific_player_fields": ["weekly_activation_eligible", "waiver_activation_eligible", "waiver_feature_coverage"],
    },
}
validate_bundle(bundle)

print("OK M5 policy + independent waiver-gate validator integrity")

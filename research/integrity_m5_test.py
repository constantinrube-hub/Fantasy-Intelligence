#!/usr/bin/env python3
"""Small deterministic M5 policy and validator integrity checks."""
from fie_m5 import WAIVER_FEATURES, format_strategy, waiver_temporal_folds, safe_corr, waiver_validation
from validate_m5_bundle import validate_bundle
import pandas as pd
import numpy as np
from build_current_snapshot import m5_format_gate

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
assert "fp_next3" not in WAIVER_FEATURES
assert "opportunity_change_score" not in WAIVER_FEATURES
assert "role_breakout_signal" not in WAIVER_FEATURES

# Correlation helpers must compare observation order, never pandas index labels.
# This reproduces the bug where ndarray predictions were paired with a Series
# retaining original row labels and correlations became null/incorrect.
x = [1, 2, 3, 4, 5, 6, 7, 8]
y = pd.Series([1, 2, 3, 4, 5, 6, 7, 8], index=[101, 103, 105, 107, 109, 111, 113, 115])
assert abs(float(safe_corr(x, y)) - 1.0) < 1e-12

# Revision-4 waiver validation must promote only when both forecast accuracy and
# actual ranking decisions improve on chronological holdouts.
rng = np.random.default_rng(7)
synthetic = []
for season in range(2019, 2026):
    for i in range(60):
        signal = i / 10 + (season - 2019) * .02
        actual = max(0.0, 2 + 2.0 * signal + rng.normal(0, .15))
        synthetic.append({
            "season": season, "week": i // 10 + 1, "position_model": "WR", "fp_next3": actual,
            "fp_prior_4": max(0.0, 14 - signal + rng.normal(0, .3)),
            "fp_prior_1": signal, "fp_prior_2": signal * .9,
            "snap_share_prior4": signal / 10, "target_share_prior4": signal / 20,
        })
_, synthetic_agg, _ = waiver_validation(pd.DataFrame(synthetic), {})
wr = next(r for r in synthetic_agg if r["position"] == "WR")
assert wr["forecast_status"] == "validated_candidate"
assert wr["decision_ranking_status"] == "validated_candidate"
assert wr["status"] == "validated_candidate"
assert wr["mean_spearman"] > wr["mean_baseline_spearman"]
assert wr["mean_top_quartile_precision"] >= wr["mean_baseline_top_quartile_precision"]
assert wr["mean_top1_regret"] <= wr["mean_baseline_top1_regret"]

# Server-side current snapshots must honor the same decision+format gate as the
# browser. A generic waiver position is not sufficient for CHOPPED if its
# CHOPPED-specific evidence gate excludes it.
format_gate_fixture = {
    "activation": {"decision_gates": {
        "weekly_mean_positions": ["QB", "LB"],
        "waiver_policy_positions": ["WR", "LB"],
        "decision_format_position_gates": {
            "weekly": {"REDRAFT": ["QB", "LB"], "CHOPPED": ["LB"]},
            "waiver": {"REDRAFT": ["WR", "LB"], "CHOPPED": ["LB"]},
        },
    }}
}
assert m5_format_gate(format_gate_fixture, "waiver", "REDRAFT", "WR")
assert not m5_format_gate(format_gate_fixture, "waiver", "CHOPPED", "WR")
assert m5_format_gate(format_gate_fixture, "waiver", "CHOPPED", "LB")
assert not m5_format_gate(format_gate_fixture, "weekly", "CHOPPED", "QB")
assert m5_format_gate(format_gate_fixture, "weekly", None, "QB")  # legacy fallback

# Regression guard for the August 2026 failure: revision-4 waiver promotion is
# independent from upstream weekly M4 promotion, has enough temporal folds, and
# requires decision-ranking evidence in addition to point-forecast MAE.
formats = {"REDRAFT": [], "DYNASTY": [], "REDRAFT_BESTBALL": [], "DYNASTY_BESTBALL": [], "CHOPPED": []}
bundle = {
    "schema_version": 5,
    "milestone": "M5",
    "research_build": "V8.7-M5",
    "control_build": "V8.2.2",
    "contract_revision": 4,
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
    "waiver_integration": {
        "aggregate": [{
            "position": "WR", "status": "validated_candidate", "folds": 5,
            "forecast_status": "validated_candidate", "decision_ranking_status": "validated_candidate",
            "mean_spearman": .52, "mean_baseline_spearman": .40,
            "mean_spearman_improvement_vs_recent_fp": .12,
            "mean_top_quartile_precision": .61, "mean_baseline_top_quartile_precision": .54,
            "mean_top1_regret": 2.0, "mean_baseline_top1_regret": 3.0,
        }],
        "model_specs": {"available_test_seasons": [2021, 2022, 2023, 2024, 2025], "max_valid_folds": 5, "required_promotion_folds": 4},
    },
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

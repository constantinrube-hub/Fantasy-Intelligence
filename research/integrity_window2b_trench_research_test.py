#!/usr/bin/env python3
"""Synthetic fail-closed integrity checks for Window 2B."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("window2b", HERE / "window2b_trench_research.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def synthetic(position="QB", useful=True, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    for season in range(2019, 2026):
        for i in range(90):
            x = rng.normal()
            b1 = rng.normal(12, 4)
            b4 = rng.normal(12, 3)
            bmean = rng.normal(12, 2)
            noise = rng.normal(0, 1.0)
            target = 0.35*b1 + 0.25*b4 + 0.40*bmean + (5.0*x if useful else 0.0) + noise
            rows.append({
                "season": season,
                "position_model": position,
                "fantasy_target": target,
                "fp_prior1": b1,
                "fp_prior4_mean": b4,
                "fp_season_to_date_mean": bmean,
                "prior_games": 4.0,
                "own_sack_rate_allowed": x,
                "opp_sack_rate_generated": 0.25*x + rng.normal(0, 0.4),
            })
    return pd.DataFrame(rows)


def gates():
    g = dict(M.GATES)
    g.update({"bootstrap_draws": 300, "min_total_eval_rows": 200, "min_test_folds": 3, "min_train_rows_per_fold": 100, "min_test_rows_per_fold": 25})
    return g


def main():
    checks = []

    strong = M.validate_family(
        synthetic(useful=True), position="QB", family="PASS_PROTECTION_FRONT_CORE",
        feature_names=("own_sack_rate_allowed", "opp_sack_rate_generated"), gates=gates(), seed=1,
    )
    checks.append(("strong_incremental_signal_validates", strong["status"] == "RESEARCH_VALIDATED_CANDIDATE"))
    checks.append(("chronological_folds_present", strong.get("test_seasons") == [2021, 2022, 2023, 2024, 2025]))
    checks.append(("positive_ci_required_and_met", strong.get("bootstrap_ci95_low", -1) > 0))
    checks.append(("same_row_contract", strong.get("same_row_comparison") is True))

    null = M.validate_family(
        synthetic(useful=False, seed=19), position="QB", family="PASS_PROTECTION_FRONT_CORE",
        feature_names=("own_sack_rate_allowed", "opp_sack_rate_generated"), gates=gates(), seed=2,
    )
    checks.append(("nonincremental_signal_blocked", null["status"] == "BLOCKED_NOT_VALIDATED"))

    incomplete = synthetic(useful=True).copy()
    incomplete.loc[incomplete.index[:20], "own_sack_rate_allowed"] = np.nan
    res = M.validate_family(
        incomplete, position="QB", family="PASS_PROTECTION_FRONT_CORE",
        feature_names=("own_sack_rate_allowed", "opp_sack_rate_generated"), gates=gates(), seed=3,
    )
    checks.append(("missing_trench_not_zero_imputed", res.get("complete_case_rows") == len(incomplete)-20))

    thin = M.build_thin_integration([strong, null, {"position":"D/ST","family":"X","status":"BLOCKED_TARGET_CONTRACT_NOT_BOUND","features":[]}], {"test":True})
    by_status = {x["status"]: x for x in thin["candidate_context"]}
    checks.append(("validated_candidate_research_only", by_status["RESEARCH_VALIDATED_CANDIDATE"]["allowed_surface"] == "research_context_only"))
    checks.append(("blocked_candidate_disabled", by_status["BLOCKED_NOT_VALIDATED"]["enabled"] is False))
    checks.append(("production_surfaces_prohibited", "production_projection" in by_status["RESEARCH_VALIDATED_CANDIDATE"]["prohibited_surfaces"]))
    checks.append(("m9_preserved", thin["production_model"] == "M9" and thin["automatic_promotion"] is False))
    checks.append(("adp_not_feature", thin["adp_used_as_football_feature"] is False))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = root / "data/research/trench/historical/season_2024-v1.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({
            "target_week_realised_stats_excluded": True,
            "snapshots": [{
                "status":"READY_RESEARCH_ONLY", "target_week":3, "max_input_week":2,
                "teams":{"BUF":{"offense":{"sack_rate_allowed":0.05,"rush_epa_per_attempt":0.1,"rush_success_rate":0.5,"stuff_rate_allowed":0.2},"defense":{"sack_rate_generated":0.08,"rush_epa_allowed_per_attempt":-0.1,"rush_success_rate_allowed":0.4,"stuff_rate_forced":0.25}}}
            }]
        }), encoding="utf-8")
        flat, prov = M.flatten_trench_history(root, [2024])
        checks.append(("window2a_history_flattens", len(flat)==1 and prov[0]["status"]=="AVAILABLE"))

        p.write_text(json.dumps({
            "target_week_realised_stats_excluded": True,
            "snapshots": [{"status":"READY_RESEARCH_ONLY","target_week":3,"max_input_week":3,"teams":{}}]
        }), encoding="utf-8")
        try:
            M.flatten_trench_history(root, [2024])
            leaked = False
        except M.ResearchError as exc:
            leaked = "TRENCH_TARGET_WEEK_LEAKAGE" in str(exc)
        checks.append(("target_week_trench_leakage_rejected", leaked))

    players = pd.DataFrame([{
        "season":2024,"week":3,"team":"BUF","opponent_team":"NYJ","position_model":"QB",
        "fantasy_target":20.0,"fp_prior1":18.0,"fp_prior4_mean":17.0,"fp_season_to_date_mean":17.5,"prior_games":2.0,
    }])
    trench = pd.DataFrame([
        {"season":2024,"week":3,"team":"BUF","own_sack_rate_allowed":0.04,"own_qb_hit_rate_allowed":0.1,"own_rush_epa_per_attempt":0.05,"own_rush_success_rate":0.5,"own_stuff_rate_allowed":0.2,"own_offense_proxy":0.4,"own_sack_rate_generated":0.07,"own_qb_hit_rate_generated":0.15,"own_rush_epa_allowed_per_attempt":-0.05,"own_rush_success_rate_allowed":0.44,"own_stuff_rate_forced":0.24,"own_defense_proxy":0.2},
        {"season":2024,"week":3,"team":"NYJ","own_sack_rate_allowed":0.09,"own_qb_hit_rate_allowed":0.2,"own_rush_epa_per_attempt":-0.03,"own_rush_success_rate":0.4,"own_stuff_rate_allowed":0.3,"own_offense_proxy":-0.3,"own_sack_rate_generated":0.12,"own_qb_hit_rate_generated":0.25,"own_rush_epa_allowed_per_attempt":-0.1,"own_rush_success_rate_allowed":0.38,"own_stuff_rate_forced":0.31,"own_defense_proxy":0.8},
    ])
    joined = M.join_trench(players, trench)
    checks.append(("opponent_context_joined_by_explicit_team", abs(float(joined.iloc[0]["opp_sack_rate_generated"])-0.12)<1e-12))

    # Standard-PPR fallback smoke test.
    target = M.ppr_target(pd.Series({"passing_yards":250,"passing_tds":2,"interceptions":1,"rushing_yards":20}))
    checks.append(("screening_target_deterministic", abs(target-18.0)<1e-12))

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise AssertionError("Window 2B integrity regression(s): " + ", ".join(failed))
    print(f"PASS Window 2B trench research integrity ({len(checks)}/{len(checks)})")


if __name__ == "__main__":
    main()

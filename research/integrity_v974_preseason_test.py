#!/usr/bin/env python3
"""Deterministic V9.7.4 exact-M9 comparator integrity test."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import preseason_projection as m9
from preseason_projection_v2 import fixture_player_week
from preseason_projection_v4 import validate_exact_m9_comparator

scoring = {
    "pass_yd": .04, "pass_td": 4, "pass_int": -2,
    "rush_yd": .1, "rush_td": 6,
    "rec": 1, "rec_yd": .1, "rec_td": 6,
    "fum": -1, "fum_lost": -2,
}

# Force the exact issue V9.7.4 exists to audit: split nflverse fumble columns
# only, no aggregate total/lost columns.
pw = fixture_player_week().copy()
for c in [
    "rushing_fumbles", "receiving_fumbles", "sack_fumbles",
    "rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost",
]:
    pw[c] = 0.0
for c in ["fumbles", "fumbles_lost"]:
    if c in pw.columns:
        pw = pw.drop(columns=[c])
pw.loc[pw.index[::113], "rushing_fumbles"] = 1.0
pw.loc[pw.index[::113], "rushing_fumbles_lost"] = 1.0

# Snapshot canonical M9 globals and prove the comparator boundary restores them.
extra_before = m9.SEASON_EXTRA_TARGETS
add_before = m9.add_scoring_completion_columns
score_before = m9._score_stat_frame

pv2 = {"per_position": {"QB": {"status": "validated_candidate"}}}
report, pred, cal = validate_exact_m9_comparator(
    pw, scoring, pd.DataFrame(), v972_result=pv2, positions=("QB",)
)

assert m9.SEASON_EXTRA_TARGETS is extra_before
assert m9.add_scoring_completion_columns is add_before
assert m9._score_stat_frame is score_before

assert report["build"] == "V9.7.4-EXACT-M9-COMPARATOR-AUDIT-1"
assert report["status"] == "complete_research_only"
g = report["governance"]
assert g["canonical_m9_modified"] is False
assert g["canonical_m1_modified"] is False
assert g["runtime_projection_modified"] is False
assert g["market_inputs_used"] is False
assert g["adp_inputs_used"] is False
assert g["comparator_only_m9_scoring_hardening"] is True
assert g["v973_statistical_gates_changed"] is False
assert report["production_activation_allowed"] is False
assert report["replacement_claim_vs_market_fallback"] is False

qb = report["per_position"]["QB"]
assert qb["folds"] >= 4, qb
assert qb["all_v972_folds_exact_scoring_replay"] is True, qb
assert qb["all_m9_folds_exact_scoring_replay"] is True, qb
assert qb["exact_m9_comparator_gate"] is True, qb

for fold in [x for x in report["folds"] if x["position"] == "QB"]:
    assert fold["m9_exact_scoring_replay"] is True, fold
    assert "fumbles" in fold["m9_targets"], fold
    assert "fumbles_lost" in fold["m9_targets"], fold

assert not pred.empty
assert not cal.empty
print("PASS integrity_v974_preseason_test exact-M9 comparator")

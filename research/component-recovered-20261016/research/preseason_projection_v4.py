#!/usr/bin/env python3
"""FIE V9.7.4 exact-M9 comparator audit.

Research-only final comparator pass for the preseason V9.7 challenger.

V9.7.3 compared V9.7.2 against the historical M9 preseason football model on
identical chronological player-season holdouts.  The challenger replayed this
league's offensive scoring exactly, while the historical M9 comparator could
not replay the separate Sleeper ``fum`` scoring key because canonical M1/M9 did
not expose total fumbles as a season target.

V9.7.4 changes ONLY the historical comparator used inside this audit:
- reconstruct total fumbles from aggregate or split nflverse weekly fields;
- reconstruct fumbles lost from aggregate or split fields;
- add total fumbles to the M9 comparator target catalog;
- score the comparator with the same isolated exact-fumble scoring boundary
  already validated by V9.7.1;
- rerun the unchanged V9.7.3 chronological head-to-head gates.

Canonical M9, M1, V9.6 runtime, V9.7.2 shadow projections and market consumers
are not modified.  No production activation is possible from this module.
"""
from __future__ import annotations

import argparse
import copy
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional, Tuple

import pandas as pd

import preseason_projection as m9
import preseason_projection_v2 as v2
import preseason_projection_v3 as v3

BUILD = "V9.7.4-EXACT-M9-COMPARATOR-AUDIT-1"
POSITIONS = ("QB", "RB", "WR", "TE")


def _load_scoring(path: str | Path) -> dict:
    p = Path(path)
    x = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(x.get("scoring"), dict) and isinstance(x["scoring"].get("settings"), dict):
        return x["scoring"]["settings"]
    if isinstance(x.get("scoring_settings"), dict):
        return x["scoring_settings"]
    if isinstance(x.get("settings"), dict):
        return x["settings"]
    return x


def _exact_completion_columns(df: pd.DataFrame, original_add) -> pd.DataFrame:
    """Comparator-only canonical fumble columns from existing historical data."""
    d = original_add(df)
    d["fumbles"] = v2._fumbles_series(d)
    d["fumbles_lost"] = v2._fumbles_lost_series(d)
    return d


@contextmanager
def exact_m9_comparator_boundary():
    """Temporarily harden M9 only inside the historical comparator audit.

    The canonical module globals are restored in ``finally`` even if validation
    raises.  No repository artifact or production model is changed by this
    context manager.
    """
    original_extra = m9.SEASON_EXTRA_TARGETS
    original_add = m9.add_scoring_completion_columns
    original_score = m9._score_stat_frame

    extra = copy.deepcopy(original_extra)
    for pos in POSITIONS:
        extra.setdefault(pos, {})
        extra[pos]["fumbles"] = ["fumbles"]
        # Keep the explicit loss target even when an older M9 catalog omits it.
        extra[pos]["fumbles_lost"] = ["fumbles_lost"]

    def add_exact(df: pd.DataFrame) -> pd.DataFrame:
        return _exact_completion_columns(df, original_add)

    def score_exact(values, pos: str, scoring: dict, n: int):
        # V9.7.1's isolated scorer delegates established scoring to score_rows()
        # and handles Sleeper ``fum`` locally.  Reusing it here makes the
        # comparator scoring boundary identical without changing canonical M9.
        return v2._score(values, pos, scoring, n)

    m9.SEASON_EXTRA_TARGETS = extra
    m9.add_scoring_completion_columns = add_exact
    m9._score_stat_frame = score_exact
    try:
        yield
    finally:
        m9.SEASON_EXTRA_TARGETS = original_extra
        m9.add_scoring_completion_columns = original_add
        m9._score_stat_frame = original_score


def validate_exact_m9_comparator(
    player_week: pd.DataFrame,
    scoring: dict,
    identity: Optional[pd.DataFrame] = None,
    v972_result: Optional[dict] = None,
    positions: Iterable[str] = POSITIONS,
) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Run V9.7.3 unchanged with an exact-scoring M9 comparator."""
    with exact_m9_comparator_boundary():
        report, predictions, calibration = v3.validate_preseason_head_to_head(
            player_week,
            scoring,
            identity,
            v972_result=v972_result,
            positions=positions,
        )

    report["build"] = BUILD
    report["status"] = "complete_research_only"
    g = report.setdefault("governance", {})
    g.update({
        "auto_activation": False,
        "production_activation": False,
        "runtime_projection_modified": False,
        "canonical_m9_modified": False,
        "canonical_m1_modified": False,
        "market_inputs_used": False,
        "adp_inputs_used": False,
        "comparator_only_m9_scoring_hardening": True,
        "exact_m9_comparator_required_for_promotion_review": True,
        "v973_statistical_gates_changed": False,
    })
    comparison = report.setdefault("comparison", {})
    comparison["baseline"] = (
        "M9 preseason football model with comparator-only exact total-fumble "
        "and fumble-loss league-scoring replay"
    )
    comparison["m9_comparator_adjustment"] = {
        "scope": "historical_audit_only",
        "total_fumbles": "aggregate fumbles else sum(rushing_fumbles, receiving_fumbles, sack_fumbles)",
        "fumbles_lost": "aggregate fumbles_lost else sum(rushing_fumbles_lost, receiving_fumbles_lost, sack_fumbles_lost)",
        "scorer": "V9.7.1 isolated exact-fumble scoring boundary",
        "canonical_m9_modified": False,
        "canonical_m1_modified": False,
        "production_artifact_modified": False,
    }

    # V9.7.4 adds exactly one new fail-closed requirement: the historical M9
    # comparator itself must replay league scoring exactly in every comparison
    # fold.  All statistical thresholds remain those from V9.7.3.
    football_ready = []
    expected_ready = []
    for pos, meta in (report.get("per_position") or {}).items():
        exact = bool(meta.get("all_m9_folds_exact_scoring_replay"))
        meta["exact_m9_comparator_required"] = True
        meta["exact_m9_comparator_gate"] = exact
        prior_football = bool(meta.get("football_model_promotion_review_ready"))
        prior_expected = bool(meta.get("expected_season_points_ready"))
        if not exact:
            meta["football_model_promotion_review_ready"] = False
            meta["expected_season_points_ready"] = False
            meta["status"] = "diagnostic_only"
            meta["reason"] = "m9_exact_scoring_comparator_gate_not_cleared"
        else:
            meta["football_model_promotion_review_ready"] = prior_football
            meta["expected_season_points_ready"] = prior_expected
        if meta.get("football_model_promotion_review_ready"):
            football_ready.append(str(pos))
        if meta.get("expected_season_points_ready"):
            expected_ready.append(str(pos))

    report["football_model_promotion_review_positions"] = sorted(football_ready)
    report["expected_season_points_ready_positions"] = sorted(expected_ready)
    report["production_activation_allowed"] = False
    report["replacement_claim_vs_market_fallback"] = False
    report["decision_semantics"] = {
        "promotion_review_only": True,
        "automatic_promotion": False,
        "unchanged_gates": {
            "minimum_chronological_folds": v3.MIN_FOLDS,
            "minimum_mean_mae_improvement": v3.MIN_MEAN_IMPROVEMENT,
            "positive_ci_required": True,
            "ppg_and_full_schedule_gates_required": True,
            "ranking_noninferiority_required": True,
            "expected_season_requires_availability_gate": True,
        },
    }
    return report, predictions, calibration


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--player-week", required=True)
    p.add_argument("--identity", default="")
    p.add_argument("--scoring-json", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument("--predictions-csv", required=True)
    p.add_argument("--calibration-csv", required=True)
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    pw = pd.read_csv(a.player_week, low_memory=False)
    identity = pd.read_csv(a.identity, low_memory=False) if a.identity and Path(a.identity).is_file() else pd.DataFrame()
    scoring = _load_scoring(a.scoring_json)

    # Recompute the V9.7.1 prior gate on the same historical backbone rather than
    # trusting a stale artifact.
    pv2 = v2.validate_component_preseason(pw, scoring, identity)
    report, predictions, calibration = validate_exact_m9_comparator(
        pw, scoring, identity, v972_result=pv2
    )

    out_json = Path(a.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    predictions.to_csv(a.predictions_csv, index=False)
    calibration.to_csv(a.calibration_csv, index=False)

    print(json.dumps({
        "build": BUILD,
        "status": report.get("status"),
        "promotion_review": report.get("football_model_promotion_review_positions", []),
        "expected_points_ready": report.get("expected_season_points_ready_positions", []),
        "m9_exact_by_position": {
            p: bool((report.get("per_position", {}).get(p, {}) or {}).get("all_m9_folds_exact_scoring_replay"))
            for p in POSITIONS
        },
        "production_activation_allowed": False,
    }, indent=2))


if __name__ == "__main__":
    main()

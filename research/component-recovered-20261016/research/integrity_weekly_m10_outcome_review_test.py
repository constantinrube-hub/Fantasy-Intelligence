#!/usr/bin/env python3
"""Real Week 4 lineage and synthetic complete-case paired scoring regressions."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from m10_prospective_capture_contract import MODELS
from weekly_m10_outcome_review import paired_profile, review, score_if_complete
from weekly_report_bundle import bundle, markdown

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    week4 = review(ROOT, 2026, 4, datetime(2026, 10, 8, 12, tzinfo=timezone.utc))
    assert week4["status"] == "BLOCKED_FROZEN_PROFILE_SNAPSHOT_UNAVAILABLE"
    assert week4["captured_player_count"] == 782 and week4["observed_player_count"] == 358
    assert week4["coverage_counts"]["BLOCKED_NO_SOURCE_PLAYER_ROW"] == 419
    assert week4["coverage_counts"]["BLOCKED_POSITION_MISMATCH"] == 5
    assert week4["profile_reviews"] == [] and week4["promotion_allowed"] is False
    report = bundle(ROOT, 2026, 4, datetime(2026, 10, 8, 12, tzinfo=timezone.utc))
    product = report["products"]["POST_WEEK_REVIEW"]
    assert product["status"] == "PARTIAL_OWNER_OUTPUT" and product["complete"] is False
    assert product["content"]["m10_research"]["observed_player_count"] == 358
    assert report["complete_product_count"] == 0
    assert "M10 prospective outcome evidence" in markdown(report)
    try:
        review(ROOT, 2026, 4, datetime(2026, 10, 2, tzinfo=timezone.utc))
    except ValueError as exc:
        assert "FUTURE_SOURCE" in str(exc)
    else:
        raise AssertionError("future outcome was available before source observation")

    assert score_if_complete({"passing_yards": 100, "passing_tds": 1}, {"pass_yd": 0.04, "pass_td": 4}, "QB") == (8.0, [])
    assert score_if_complete({"passing_yards": None}, {"pass_yd": .04}, "QB")[1] == ["pass_yd:SOURCE_FIELD_NULL"]
    assert score_if_complete({"fumbles_lost_total": 1}, {"fum_lost": -2}, "QB")[1] == ["fum_lost:SOURCE_FIELD_ABSENT"]
    assert score_if_complete({"passing_yards": 5}, {"unknown_key": 1}, "QB")[1] == ["unknown_key:UNSUPPORTED_KEY"]
    profile = {"league_id": "league", "profile_scoring_signature": "signature", "profile_fingerprint": "fingerprint",
               "scoring_settings": {"pass_yd": 0.04}}
    outcome = {"forecast_id": "id1", "canonical_player_id": "gsis-1", "status": "OBSERVED_PROVIDER_ROW",
               "raw_outcomes": {"passing_yards": 100}}
    forecasts = [{"forecast_id": "id1", "canonical_player_id": "gsis-1", "position_model": "QB", "model": model,
                  "predicted_raw_components": {"passing_yards": yards}}
                 for model, yards in zip(MODELS, (125, 150, 75))]
    scoring = [{"forecast_id": "id1", "model": model, "league_id": "league",
                "profile_scoring_signature": "signature", "profile_fingerprint": "fingerprint",
                "scored_fantasy_points": yards * 0.04}
               for model, yards in zip(MODELS, (125, 150, 75))]
    paired = paired_profile(profile, [outcome], forecasts, scoring)
    assert paired["status"] == "DESCRIPTIVE_PAIRED_ONE_WEEK_ONLY" and paired["paired_player_count"] == 1
    assert paired["metrics"]["M9"] == {"mae": 1.0, "rmse": 1.0, "bias": 1.0}
    assert paired["metrics"]["M10_LINEAR"]["bias"] == 2.0
    assert paired["metrics"]["M10_HGB"]["bias"] == -1.0
    assert paired["superiority_claim_allowed"] is False
    broken = deepcopy(forecasts); broken[1]["predicted_raw_components"]["passing_yards"] = None
    assert paired_profile(profile, [outcome], broken, scoring)["status"] == "BLOCKED_NO_EXACT_PAIRED_ROWS"
    broken = deepcopy(scoring); broken[0]["profile_fingerprint"] = "drift"
    assert paired_profile(profile, [outcome], forecasts, broken)["status"] == "BLOCKED_FROZEN_PROFILE_IDENTITY_MISMATCH"
    broken = deepcopy(scoring); broken[0]["scored_fantasy_points"] = 999
    assert paired_profile(profile, [outcome], forecasts, broken)["excluded_reasons"]["BLOCKED_FROZEN_PREDICTION_REPLAY_MISMATCH"] == 1
    print("PASS M10 postweek review: real frozen lineage, future exclusion, exact-field preflight and paired one-week metrics")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read-only, paired M10 postweek evidence from frozen capture and outcome ledgers.

Exact scores require the frozen full profile, the original scorer version, and
every nonzero scoring field in both the forecast and observed source rows.
"""
from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from pathlib import Path

from m10_prospective_capture_contract import (
    MODELS, canonical_bytes, capture_paths, read_json, read_jsonl_gzip,
    sha256_bytes, sha256_file, validate_capture,
)
from weekly_evidence_audit import stamp

BONUS_RECEIVING = {"bonus_rec_te", "rec_te", "bonus_rec_rb", "rec_rb", "bonus_rec_wr", "rec_wr"}


def score_if_complete(raw: dict, settings: dict, position: str) -> tuple[float | None, list[str]]:
    """Call the canonical scorer only after all weighted source fields are proven."""
    from fie_research import BONUS_RULES, SCORING_MAP, score_rows
    import pandas as pd

    missing = []
    scoring_row = {**raw, "position_model": position}
    for key, weight in sorted(settings.items()):
        try:
            number = float(weight)
        except (TypeError, ValueError):
            missing.append(f"{key}:INVALID_WEIGHT"); continue
        if not math.isfinite(number):
            missing.append(f"{key}:INVALID_WEIGHT"); continue
        if number == 0:
            continue
        if key in BONUS_RECEIVING:
            names = ["receptions"]
        elif key in BONUS_RULES:
            names = [BONUS_RULES[key][0]]
        elif key == "fum_lost":
            # The archive's fumbles_lost_total is not the canonical scorer's
            # fumbles_lost alias. Never silently sum possibly incomplete splits.
            names = ["fumbles_lost"]
        else:
            names = SCORING_MAP.get(key)
        if not names:
            missing.append(f"{key}:UNSUPPORTED_KEY"); continue
        selected = next((name for name in names if name in raw), None)
        if selected is None:
            missing.append(f"{key}:SOURCE_FIELD_ABSENT"); continue
        value = raw[selected]
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            missing.append(f"{key}:SOURCE_FIELD_NULL"); continue
        if not math.isfinite(parsed):
            missing.append(f"{key}:SOURCE_FIELD_NULL")
    if missing:
        return None, sorted(set(missing))
    value = float(score_rows(pd.DataFrame([scoring_row]), settings).iloc[0])
    if not math.isfinite(value):
        raise ValueError("M10_OUTCOME_SCORER_NONFINITE")
    return value, []


def paired_profile(profile: dict, outcomes: list[dict], forecasts: list[dict], scoring: list[dict]) -> dict:
    league_id = str(profile["league_id"])
    signature, fingerprint = profile["profile_scoring_signature"], profile["profile_fingerprint"]
    base = {"league_id": league_id, "profile_scoring_signature": signature,
            "profile_fingerprint": fingerprint,
            "scoring_settings_sha256": sha256_bytes(canonical_bytes(profile["scoring_settings"])),
            "captured_player_count": len(outcomes)}
    if not profile["scoring_settings"]:
        return {**base, "status": "BLOCKED_EMPTY_FROZEN_SCORING_PROFILE", "paired_player_count": 0}
    forecasts_by_key = {(str(row["forecast_id"]), str(row["model"])): row for row in forecasts}
    scoring_by_key = {(str(row["forecast_id"]), str(row["model"])): row for row in scoring if str(row["league_id"]) == league_id}
    if len(forecasts_by_key) != len(forecasts) or len(scoring_by_key) != len(outcomes) * len(MODELS):
        return {**base, "status": "BLOCKED_PAIRED_FORECAST_OR_SCORING_ROWS", "paired_player_count": 0}
    if any(row.get("profile_scoring_signature") != signature or row.get("profile_fingerprint") != fingerprint
           for row in scoring_by_key.values()):
        return {**base, "status": "BLOCKED_FROZEN_PROFILE_IDENTITY_MISMATCH", "paired_player_count": 0}
    per_model = {model: [] for model in MODELS}
    reasons: Counter[str] = Counter()
    observed = 0
    for outcome in outcomes:
        if outcome.get("status") != "OBSERVED_PROVIDER_ROW" or not isinstance(outcome.get("raw_outcomes"), dict):
            reasons[str(outcome.get("status") or "BLOCKED_OUTCOME_ROW")] += 1
            continue
        observed += 1
        fid = str(outcome["forecast_id"])
        trio = [forecasts_by_key.get((fid, model)) for model in MODELS]
        score_trio = [scoring_by_key.get((fid, model)) for model in MODELS]
        if any(row is None for row in trio + score_trio):
            reasons["BLOCKED_UNPAIRED_MODEL_ROWS"] += 1; continue
        position = trio[0]["position_model"]
        if any(row["position_model"] != position or row["canonical_player_id"] != outcome["canonical_player_id"] for row in trio):
            reasons["BLOCKED_MODEL_IDENTITY_MISMATCH"] += 1; continue
        actual, gaps = score_if_complete(outcome["raw_outcomes"], profile["scoring_settings"], position)
        if gaps:
            for gap in gaps: reasons["OUTCOME_" + gap] += 1
            continue
        predicted = []
        for forecast in trio:
            point, gaps = score_if_complete(forecast["predicted_raw_components"], profile["scoring_settings"], position)
            if gaps:
                for gap in gaps: reasons["FORECAST_" + gap] += 1
                break
            predicted.append(point)
        if len(predicted) != len(MODELS):
            continue
        for model, point, replay in zip(MODELS, predicted, score_trio):
            frozen = float(replay["scored_fantasy_points"])
            if not math.isfinite(frozen) or abs(point - frozen) > 1e-6:
                reasons["BLOCKED_FROZEN_PREDICTION_REPLAY_MISMATCH"] += 1
                predicted = []
                break
        if len(predicted) != len(MODELS):
            continue
        for model, point in zip(MODELS, predicted):
            per_model[model].append(point - actual)
    n = len(per_model[MODELS[0]])
    if not all(len(per_model[model]) == n for model in MODELS):
        raise ValueError("M10_OUTCOME_PAIRED_COHORT_ASYMMETRIC")
    metrics = {model: {"mae": sum(abs(e) for e in errors) / n,
                       "rmse": math.sqrt(sum(e*e for e in errors) / n),
                       "bias": sum(errors) / n} for model, errors in per_model.items()} if n else None
    return {**base, "status": "DESCRIPTIVE_PAIRED_ONE_WEEK_ONLY" if n else "BLOCKED_NO_EXACT_PAIRED_ROWS",
            "observed_player_count": observed, "paired_player_count": n,
            "excluded_reasons": dict(sorted(reasons.items())), "metrics": metrics,
            "superiority_claim_allowed": False}


def review(root: Path, season: int, week: int, as_of: datetime) -> dict:
    if as_of.tzinfo is None:
        raise ValueError("M10_OUTCOME_REVIEW_TIMEZONE_REQUIRED")
    prospective = root / "data/research/prospective/m10"
    paths = capture_paths(prospective, season, week)
    result = {"schema": "fie-m10-postweek-evidence-review-v1", "season": season, "week": week,
              "as_of_utc": as_of.isoformat(), "research_only": True,
              "production_model": "M9", "promotion_allowed": False,
              "comparison_scope": "M9/M10_LINEAR/M10_HGB same frozen week-open cutoff; not the separate Sunday Sleeper baseline"}
    if not paths["manifest"].is_file():
        return {**result, "status": "BLOCKED_PROSPECTIVE_CAPTURE_MISSING", "profile_reviews": []}
    if not (paths["outcome_dir"] / "outcome-manifest.json").is_file():
        return {**result, "status": "BLOCKED_REAL_OUTCOME_REVISION_MISSING", "profile_reviews": []}
    validate_capture(prospective, season, week, require_outcome=True, require_fixture=False)
    capture = read_json(paths["manifest"])
    outcome_meta = read_json(paths["outcome_dir"] / "outcome-manifest.json")
    if capture["fixture"] or outcome_meta["fixture"]:
        raise ValueError("M10_OUTCOME_REVIEW_REAL_CAPTURE_REQUIRED")
    outcomes = read_jsonl_gzip(paths["outcome_dir"] / "outcomes.jsonl.gz")
    if stamp(capture["captured_at"]) > as_of or any(stamp(row["observed_at"]) > as_of for row in outcomes):
        raise ValueError("M10_OUTCOME_REVIEW_FUTURE_SOURCE")
    counts = dict(sorted(Counter(str(row.get("status") or "UNKNOWN") for row in outcomes).items()))
    result.update(forecast_manifest_sha256=sha256_file(paths["manifest"]),
                  outcome_manifest_sha256=sha256_file(paths["outcome_dir"] / "outcome-manifest.json"),
                  source_payload_sha256=outcome_meta["source_payload_sha256"],
                  captured_player_count=len(outcomes), observed_player_count=counts.get("OBSERVED_PROVIDER_ROW", 0),
                  coverage_counts=counts)
    profile_path = paths["scoring"].parent / "profile-snapshot.json"
    if not profile_path.is_file():
        return {**result, "status": "BLOCKED_FROZEN_PROFILE_SNAPSHOT_UNAVAILABLE", "profile_reviews": [],
                "note": "Do not reconstruct cutoff scoring settings from a current profile. Source player totals are diagnostics, not exact league scores."}
    lineage = [row for row in capture.get("input_lineage", []) if row.get("role") == "profile_snapshot"]
    if len(lineage) != 1 or sha256_file(profile_path) != lineage[0]["sha256"]:
        raise ValueError("M10_OUTCOME_REVIEW_PROFILE_LINEAGE_MISMATCH")
    forecasts = read_jsonl_gzip(paths["forecasts"])
    scoring = read_jsonl_gzip(paths["scoring"])
    scorer_sha = sha256_file(root / "research/fie_research.py")
    if any(row.get("scoring_registry_version_sha256") != scorer_sha for row in scoring):
        return {**result, "status": "BLOCKED_FROZEN_SCORER_VERSION_DRIFT", "profile_reviews": []}
    profiles = read_json(profile_path)["profiles"]
    if len({str(row["league_id"]) for row in profiles}) != len(profiles):
        raise ValueError("M10_OUTCOME_REVIEW_DUPLICATE_FROZEN_PROFILE")
    reviews = [paired_profile(profile, outcomes, forecasts, scoring) for profile in profiles]
    return {**result, "status": "DESCRIPTIVE_PAIRED_REVIEW" if any(row["paired_player_count"] > 0 for row in reviews)
            else "BLOCKED_NO_EXACT_PAIRED_ROWS", "profile_snapshot_sha256": sha256_file(profile_path),
            "profile_reviews": reviews, "profile_status_counts": dict(Counter(row["status"] for row in reviews)),
            "note": "One week cannot establish challenger superiority; no shadow or production promotion."}

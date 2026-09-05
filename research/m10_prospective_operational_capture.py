#!/usr/bin/env python3
"""Fail-closed audit-branch adapter for Tranche 7C prospective inputs.

It performs no provider requests and never derives an earlier forecast.  A caller
must supply a hash-locked bundle that was already captured before the declared
weekly cutoff.  Recurring collection is deliberately outside this module.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from m10_prospective_capture_contract import (
    MODELS, POSITIONS, ROOT, SCHEMA, canonical_bytes, capture_hours, capture_paths,
    contract_sha256, read_json, read_jsonl_gzip, sha256_bytes, sha256_file,
    validate_capture, write_json, write_jsonl_gzip,
)


INPUT_SCHEMA = "fie-m10-prospective-operational-input-v1"
R8_INPUT_SCHEMA = "fie-m10-prospective-operational-input-v2"
OUTCOME_INPUT_SCHEMA = "fie-m10-prospective-operational-outcome-input-v1"
REQUIRED_SOURCES = {"forecast_rows", "profile_snapshot", "decision_inputs"}


def bundle_path(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"input bundle path must be a safe relative path: {raw}")
    return root / path


def parse_bundle(path: Path) -> tuple[dict[str, Any], Path]:
    value = read_json(path)
    if value.get("schema") not in {INPUT_SCHEMA, R8_INPUT_SCHEMA}:
        raise ValueError("invalid operational input schema")
    return value, path.parent


def _timestamps_ok(record: dict[str, Any], capture_at: str) -> None:
    from m10_prospective_capture_contract import parse_time
    assert record.get("point_in_time_eligible") is True
    assert record.get("historical_reconstruction") is False
    assert parse_time(str(record["captured_at"])) <= parse_time(capture_at)
    assert parse_time(str(record["as_of"])) <= parse_time(capture_at)


def validate_input_bundle(path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    value, root = parse_bundle(path)
    assert value.get("research_only") is True and value.get("production_model") == "M9"
    assert not any(value.get(key) for key in ("production_activation", "app_integration", "shadow_integration", "automatic_promotion", "live_provider_request"))
    capture = value.get("capture") or {}
    season, week = int(capture["season"]), int(capture["week"])
    captured_at, first_kickoff_at = str(capture["captured_at"]), str(capture["first_kickoff_at"])
    hours = capture_hours(captured_at, first_kickoff_at)
    assert 0.0 <= hours <= 18.0 and float(capture["hours_before_first_kickoff"]) == hours
    records = value.get("source_records") or []
    assert {str(row.get("role")) for row in records} == REQUIRED_SOURCES
    paths: dict[str, Path] = {}
    for record in records:
        role = str(record["role"])
        item = bundle_path(root, str(record["path"]))
        assert item.is_file(), item
        assert sha256_file(item) == str(record["sha256"]), item
        _timestamps_ok(record, captured_at)
        paths[role] = item
    if value.get("schema") == R8_INPUT_SCHEMA:
        from m10_prospective_activation_guard import validate_activation_lock
        lock = validate_activation_lock(ROOT)
        assert str(value.get("season_lock_sha256")) == str(lock["season_lock_sha256"])
        assert len(str(value.get("source_bundle_sha256") or "")) == 64
    return value, paths


def canonical_score(raw: dict[str, Any], scoring: dict[str, Any]) -> float:
    """Use the repository's existing exact scorer only at real operational use."""
    import pandas as pd
    from fie_research import score_rows
    row = dict(raw)
    result = score_rows(pd.DataFrame([row]), scoring)
    value = float(result.iloc[0])
    if not value == value or value in (float("inf"), float("-inf")):
        raise ValueError("canonical scoring produced a non-finite result")
    return value


def validate_profiles(profiles: list[dict[str, Any]], *, fixture: bool) -> None:
    required = {"league_id", "league_format", "profile_scoring_signature", "profile_fingerprint", "scoring_settings", "captured_at"}
    assert profiles and all(required <= set(row) for row in profiles)
    pairs = {(str(row["league_id"]), str(row["profile_fingerprint"])) for row in profiles}
    assert len(pairs) == len(profiles)
    if not fixture:
        from fie_research_pipeline_contract import enabled_league_rows
        enabled = enabled_league_rows()
        assert set(str(row["league_id"]) for row in profiles) == set(enabled), "profile replay must cover every enabled league"
        assert len(enabled) == 22, "enabled-league coverage changed; require a new governed design"
        for row in profiles:
            registry = enabled[str(row["league_id"])]
            assert str(row["profile_scoring_signature"]) == str(registry.get("scoring_signature") or "")
            assert str(row["profile_fingerprint"]) == str(registry.get("profile_fingerprint") or "")


def validate_forecasts(rows: list[dict[str, Any]], capture: dict[str, Any]) -> None:
    assert rows and {str(row.get("model")) for row in rows} == set(MODELS)
    paired: dict[str, set[str]] = {}
    for row in rows:
        assert int(row["season"]) == int(capture["season"]) and int(row["week"]) == int(capture["week"])
        assert str(row["captured_at"]) == str(capture["captured_at"])
        assert str(row["position_model"]) in POSITIONS
        assert row.get("predicted_raw_components") and row.get("prediction_quantiles")
        assert row.get("source_bundle_sha256") and row.get("model_parameter_sha256")
        assert not any(str(key).startswith("actual") for key in row)
        paired.setdefault(str(row["forecast_id"]), set()).add(str(row["model"]))
    assert len(paired) >= 4 and all(value == set(MODELS) for value in paired.values())
    assert {next(row["position_model"] for row in rows if row["forecast_id"] == key) for key in paired} == set(POSITIONS)


def validate_decisions(rows: list[dict[str, Any]], forecast_ids: set[str]) -> None:
    assert rows
    grouped: dict[tuple[str, str], dict[str, tuple[str, ...]]] = {}
    for row in rows:
        assert row.get("research_only") is True and row.get("production_recommendation_changed") is False
        model = str(row["model"])
        assert model in MODELS
        ids = tuple(sorted(str(item) for item in row.get("legal_forecast_ids") or []))
        if row.get("status") == "BLOCKED_INCOMPLETE_LEGAL_ROSTER":
            assert row.get("blocker") == "INCOMPLETE_LEGAL_ROSTER_AT_CUTOFF" and not ids and not row.get("selected_forecast_ids")
        else:
            assert ids and set(ids) <= forecast_ids and set(row.get("selected_forecast_ids") or []) <= set(ids)
        grouped.setdefault((str(row["domain"]), str(row["league_id"])), {})[model] = ids
    assert all(set(models) == set(MODELS) and len(set(models.values())) == 1 for models in grouped.values())


def replay_scoring(forecasts: list[dict[str, Any]], profiles: list[dict[str, Any]], score: Callable[[dict[str, Any], dict[str, Any]], float]) -> list[dict[str, Any]]:
    scorer_hash = sha256_file(ROOT / "research/fie_research.py")
    rows: list[dict[str, Any]] = []
    for forecast in forecasts:
        for profile in profiles:
            point = score({**dict(forecast["predicted_raw_components"]), "position_model": forecast["position_model"]}, dict(profile["scoring_settings"]))
            rows.append({
                "forecast_id": forecast["forecast_id"], "canonical_player_id": forecast["canonical_player_id"], "model": forecast["model"],
                "league_id": profile["league_id"], "league_format": profile["league_format"],
                "profile_scoring_signature": profile["profile_scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"],
                "scored_fantasy_points": point, "scoring_registry_version_sha256": scorer_hash, "research_only": True,
            })
    return rows


def create_operational_capture(input_manifest: Path, output_root: Path, *, score: Callable[[dict[str, Any], dict[str, Any]], float] = canonical_score) -> dict[str, Any]:
    manifest_input, inputs = validate_input_bundle(input_manifest)
    fixture = bool(manifest_input.get("fixture") is True)
    capture = manifest_input["capture"]
    season, week = int(capture["season"]), int(capture["week"])
    paths = capture_paths(output_root, season, week)
    if paths["manifest"].exists() or paths["missed"].exists():
        return {"status": "EXISTS", "manifest": paths["manifest"] if paths["manifest"].exists() else paths["missed"]}
    forecasts = read_jsonl_gzip(inputs["forecast_rows"])
    profiles = read_json(inputs["profile_snapshot"])["profiles"]
    validate_forecasts(forecasts, capture)
    validate_profiles(profiles, fixture=fixture)
    if manifest_input.get("schema") == R8_INPUT_SCHEMA:
        from m10_prospective_activation_guard import validate_activation_lock
        from m10_prospective_weekly_producer import build_decision_traces, exact_profile_scoring
        lock = validate_activation_lock(ROOT)
        roster_states = read_json(inputs["decision_inputs"]).get("league_roster_states") or []
        scoring = exact_profile_scoring(forecasts, profiles, lock)
        decisions = build_decision_traces(profiles, roster_states, scoring, capture=capture)
    else:
        decisions = read_json(inputs["decision_inputs"])["decision_traces"]
        scoring = replay_scoring(forecasts, profiles, score)
    validate_decisions(decisions, {str(row["forecast_id"]) for row in forecasts})
    write_jsonl_gzip(paths["forecasts"], forecasts)
    write_jsonl_gzip(paths["scoring"], scoring)
    write_jsonl_gzip(paths["decisions"], decisions)
    source_rows = manifest_input["source_records"]
    output = {
        "schema": SCHEMA, "fixture": fixture, "status": "CAPTURED", "season": season, "week": week,
        "captured_at": capture["captured_at"], "first_kickoff_at": capture["first_kickoff_at"], "hours_before_first_kickoff": capture["hours_before_first_kickoff"],
        "capture_contract_sha256": contract_sha256(), "schedule_snapshot_sha256": capture["schedule_snapshot_sha256"], "input_manifest_sha256": sha256_file(input_manifest),
        "input_lineage": [{key: row[key] for key in ("role", "path", "sha256", "captured_at", "as_of", "point_in_time_eligible", "historical_reconstruction")} for row in source_rows],
        "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "shadow_integration": False, "automatic_promotion": False},
        "ledgers": {
            "forecast": {"path": paths["forecasts"].relative_to(output_root).as_posix(), "sha256": sha256_file(paths["forecasts"]), "rows": len(forecasts)},
            "scoring_replay": {"path": paths["scoring"].relative_to(output_root).as_posix(), "sha256": sha256_file(paths["scoring"]), "rows": len(scoring)},
            "decision_trace": {"path": paths["decisions"].relative_to(output_root).as_posix(), "sha256": sha256_file(paths["decisions"]), "rows": len(decisions)},
        }, "expected_models": list(MODELS), "expected_positions": list(POSITIONS), "first_write_immutable": True,
    }
    write_json(paths["manifest"], output)
    return {"status": "CREATED", "manifest": paths["manifest"]}


def append_outcomes(outcome_manifest: Path, output_root: Path) -> dict[str, Any]:
    value = read_json(outcome_manifest)
    root = outcome_manifest.parent
    assert value.get("schema") == OUTCOME_INPUT_SCHEMA and value.get("historical_reconstruction") is False
    assert value.get("point_in_time_outcome_source") is True and value.get("revision") == 1
    season, week = int(value["season"]), int(value["week"])
    paths = capture_paths(output_root, season, week)
    assert paths["manifest"].is_file(), "outcomes require an immutable forecast"
    output = paths["outcome_dir"] / "outcomes.jsonl.gz"
    meta = paths["outcome_dir"] / "outcome-manifest.json"
    if meta.exists():
        return {"status": "EXISTS", "manifest": meta}
    rows_path = bundle_path(root, str(value["rows_path"]))
    assert rows_path.is_file() and sha256_file(rows_path) == str(value["rows_sha256"])
    rows = read_jsonl_gzip(rows_path)
    forecasts = {row["forecast_id"] for row in read_jsonl_gzip(paths["forecasts"])}
    assert {row["forecast_id"] for row in rows} == forecasts
    assert all("model" not in row and int(row["revision"]) == 1 for row in rows)
    write_jsonl_gzip(output, rows)
    write_json(meta, {"schema": "fie-m10-prospective-outcome-v1", "fixture": bool(value.get("fixture") is True), "season": season, "week": week, "revision": 1, "forecast_manifest_sha256": sha256_file(paths["manifest"]), "outcome_path": output.relative_to(output_root).as_posix(), "outcome_sha256": sha256_file(output), "rows": len(rows), "append_only": True, "source_release_or_commit": value["source_release_or_commit"], "source_payload_sha256": value["source_payload_sha256"]})
    return {"status": "CREATED", "manifest": meta}


def create_operational_missed_capture(output_root: Path, *, season: int, week: int, observed_at: str, first_kickoff_at: str, reason: str) -> dict[str, Any]:
    """Write a permanent miss only after the verified kickoff has passed."""
    from m10_prospective_capture_contract import create_missed_capture, parse_time
    if reason == "WINDOW_NOT_REACHED":
        raise ValueError("WINDOW_NOT_REACHED is a successful no-write state, never a permanent miss")
    if parse_time(observed_at) < parse_time(first_kickoff_at):
        raise ValueError("operational missed capture may be recorded only after kickoff")
    return create_missed_capture(output_root, season, week, observed_at, first_kickoff_at, reason)


def append_outcome_revision(outcome_manifest: Path, output_root: Path) -> dict[str, Any]:
    """Append, never overwrite, a corrected model-independent outcome revision."""
    value, root = read_json(outcome_manifest), outcome_manifest.parent
    assert value.get("schema") == OUTCOME_INPUT_SCHEMA and value.get("historical_reconstruction") is False
    revision = int(value["revision"]); assert revision >= 2 and value.get("parent_revision_sha256") and value.get("source_diff_manifest_sha256")
    season, week = int(value["season"]), int(value["week"]); paths = capture_paths(output_root, season, week)
    assert paths["manifest"].is_file(), "outcome revisions require an immutable forecast"
    parent_dir = paths["outcome_dir"].parent / f"revision_{revision - 1}"
    parent_meta = parent_dir / "outcome-manifest.json"; assert parent_meta.is_file() and sha256_file(parent_meta) == value["parent_revision_sha256"]
    target_dir = paths["outcome_dir"].parent / f"revision_{revision}"; target = target_dir / "outcomes.jsonl.gz"; meta = target_dir / "outcome-manifest.json"
    if meta.exists(): return {"status": "EXISTS", "manifest": meta}
    rows_path = bundle_path(root, str(value["rows_path"])); assert rows_path.is_file() and sha256_file(rows_path) == value["rows_sha256"]
    rows = read_jsonl_gzip(rows_path); forecasts = {r["forecast_id"] for r in read_jsonl_gzip(paths["forecasts"])}
    assert {r["forecast_id"] for r in rows} == forecasts and all("model" not in r and int(r["revision"]) == revision for r in rows)
    write_jsonl_gzip(target, rows)
    write_json(meta, {"schema":"fie-m10-prospective-outcome-v1","fixture":bool(value.get("fixture")),"season":season,"week":week,"revision":revision,"parent_revision_sha256":value["parent_revision_sha256"],"source_diff_manifest_sha256":value["source_diff_manifest_sha256"],"outcome_path":target.relative_to(output_root).as_posix(),"outcome_sha256":sha256_file(target),"rows":len(rows),"append_only":True,"source_payload_sha256":value["source_payload_sha256"]})
    return {"status":"CREATED","manifest":meta}

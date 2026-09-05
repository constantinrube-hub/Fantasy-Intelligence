#!/usr/bin/env python3
"""Fail-closed, no-network producer for the 7C-R weekly raw source bundle."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from m10_prospective_capture_contract import ROOT, canonical_bytes, capture_hours, parse_time, read_json, sha256_bytes, sha256_file, write_json

INPUT_SCHEMA = "fie-m10-prospective-source-envelope-input-v1"
R8_RAW_SCHEMA = "fie-m10-prospective-weekly-raw-envelope-v1"
ENVELOPE_SCHEMA = "fie-m10-prospective-source-envelope-v1"
BUNDLE_SCHEMA = "fie-m10-prospective-weekly-source-bundle-v1"
ROLES = {"schedule", "completed_games", "identity_snapshot", "roster_profile_snapshot"}


def safe_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts: raise ValueError("source record path must be a safe relative path")
    return root / path


def validate_input(path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    value, root = read_json(path), path.parent
    assert value.get("schema") in {INPUT_SCHEMA, R8_RAW_SCHEMA} and value.get("research_only") is True
    assert value.get("production_model") == "M9" and not any(value.get(k) for k in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "live_provider_request", "historical_reconstruction"))
    capture = value["capture"]; hours = capture_hours(capture["observed_at"], capture["first_kickoff_at"])
    assert int(capture["season"]) == 2026 and int(capture["week"]) > 0 and float(capture["hours_before_first_kickoff"]) == hours
    assert parse_time(capture["observed_at"]) < parse_time(capture["first_kickoff_at"])
    paths: dict[str, Path] = {}
    assert {r.get("role") for r in value["source_records"]} == ROLES
    for record in value["source_records"]:
        role, item = str(record["role"]), safe_path(root, str(record["path"]))
        assert item.is_file() and sha256_file(item) == record["sha256"]
        assert record.get("point_in_time_eligible") is True and record.get("historical_reconstruction") is False
        assert parse_time(record["captured_at"]) <= parse_time(capture["observed_at"])
        assert parse_time(record["as_of"]) <= parse_time(capture["observed_at"])
        paths[role] = item
    schedule = read_json(paths["schedule"])
    assert schedule["season"] == capture["season"] and schedule["week"] == capture["week"]
    assert schedule["season_type"] == "REG" and schedule["first_kickoff_at"] == capture["first_kickoff_at"]
    identity, profiles = read_json(paths["identity_snapshot"]), read_json(paths["roster_profile_snapshot"])
    assert identity.get("governed_crosswalk") is True and identity.get("ambiguous_count") is not None
    assert profiles.get("enabled_league_count") == 22 and len(profiles.get("profiles") or []) == 22
    return value, paths


def bundle_path(root: Path, season: int, week: int) -> Path:
    return root / "source-bundles" / str(season) / f"week_{week:02d}" / "bundle.json"


def create_bundle(input_manifest: Path, output_root: Path) -> dict[str, Any]:
    value, paths = validate_input(input_manifest); capture = value["capture"]
    hours = float(capture["hours_before_first_kickoff"])
    if hours > 18.0: return {"status": "WINDOW_NOT_REACHED", "manifest": None}
    assert hours >= 0.0, "post-kickoff processing belongs to the later typed-miss component"
    destination = bundle_path(output_root, int(capture["season"]), int(capture["week"]))
    records = [{key: row[key] for key in ("role", "path", "sha256", "captured_at", "as_of", "point_in_time_eligible", "historical_reconstruction", "source_identity", "response_files") if key in row} for row in value["source_records"]]
    for output, source in zip(records, value["source_records"]):
        if source.get("release_or_etag") is not None:
            output["release_or_etag"] = source["release_or_etag"]
    result = {"schema": BUNDLE_SCHEMA, "fixture": bool(value.get("fixture")), "season": capture["season"], "week": capture["week"], "observed_at": capture["observed_at"], "first_kickoff_at": capture["first_kickoff_at"], "hours_before_first_kickoff": hours, "schedule_snapshot_sha256": sha256_file(paths["schedule"]), "source_envelope_sha256": sha256_file(input_manifest), "source_records": records, "research_only": True, "production_model": "M9", "first_write_immutable": True}
    result["bundle_sha256"] = sha256_bytes(canonical_bytes(result))
    if destination.exists():
        if destination.read_bytes() != canonical_bytes(result) + b"\n": raise ValueError("first-write source bundle differs")
        return {"status": "EXISTS", "manifest": destination}
    write_json(destination, result); return {"status": "CREATED", "manifest": destination}


def fixture_input(root: Path, observed: str = "2026-09-09T06:00:00+00:00") -> Path:
    kickoff = "2026-09-10T00:00:00+00:00"; bundle = root / "input"; bundle.mkdir(parents=True, exist_ok=True)
    payloads = {
        "schedule": {"season": 2026, "week": 1, "season_type": "REG", "first_kickoff_at": kickoff},
        "completed_games": {"games": [], "public_core": True},
        "identity_snapshot": {"governed_crosswalk": True, "ambiguous_count": 0},
        "roster_profile_snapshot": {"enabled_league_count": 22, "profiles": [{"league_id": f"fixture-{i}"} for i in range(22)]},
    }
    records=[]
    for role, payload in payloads.items():
        path=bundle/f"{role}.json"; write_json(path,payload); records.append({"role":role,"path":path.name,"sha256":sha256_file(path),"captured_at":observed,"as_of":observed,"point_in_time_eligible":True,"historical_reconstruction":False})
    manifest=bundle/"source-envelope.json"; write_json(manifest,{"schema":INPUT_SCHEMA,"fixture":True,"research_only":True,"production_model":"M9","production_activation":False,"app_integration":False,"runtime_integration":False,"shadow_integration":False,"live_provider_request":False,"historical_reconstruction":False,"capture":{"season":2026,"week":1,"observed_at":observed,"first_kickoff_at":kickoff,"hours_before_first_kickoff":capture_hours(observed,kickoff)},"source_records":records}); return manifest

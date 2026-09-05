#!/usr/bin/env python3
"""No-network integration test for the Tranche 7C locked-input adapter."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
import argparse

from m10_prospective_capture_contract import (
    fixture_decision_rows, fixture_forecasts, fixture_outcome_rows, sha256_file,
    validate_capture, write_json, write_jsonl_gzip,
)
from m10_prospective_operational_capture import append_outcomes, canonical_score, create_operational_capture, validate_input_bundle


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", action="store_true", help="requires research dependencies; used by controlled CI")
    args = parser.parse_args(argv)
    root = Path(tempfile.mkdtemp(prefix="fie-tranche7c-"))
    try:
        bundle = root / "bundle"
        captured, kickoff = "2026-09-09T06:00:00+00:00", "2026-09-10T00:00:00+00:00"
        forecasts = fixture_forecasts(2026, 1, captured, kickoff)
        forecast_path = bundle / "forecasts.jsonl.gz"
        write_jsonl_gzip(forecast_path, forecasts)
        profiles_path = bundle / "profiles.json"
        profiles = {"profiles": [
            {"league_id": "fixture-redraft", "league_format": "REDRAFT", "profile_scoring_signature": "fixture-ppr-v1", "profile_fingerprint": "a" * 64, "scoring_settings": {"pass_yd": 0.04, "rec": 1.0}, "captured_at": captured},
            {"league_id": "fixture-bestball", "league_format": "REDRAFT_BESTBALL", "profile_scoring_signature": "fixture-bestball-v1", "profile_fingerprint": "b" * 64, "scoring_settings": {"pass_yd": 0.05, "rec": 0.5}, "captured_at": captured},
        ]}
        write_json(profiles_path, profiles)
        decisions_path = bundle / "decisions.json"
        write_json(decisions_path, {"decision_traces": fixture_decision_rows(forecasts, 2026, 1, captured)})
        records = []
        for role, path in (("forecast_rows", forecast_path), ("profile_snapshot", profiles_path), ("decision_inputs", decisions_path)):
            records.append({"role": role, "path": path.relative_to(bundle).as_posix(), "sha256": sha256_file(path), "captured_at": captured, "as_of": captured, "point_in_time_eligible": True, "historical_reconstruction": False})
        manifest = bundle / "input-manifest.json"
        write_json(manifest, {"schema": "fie-m10-prospective-operational-input-v1", "fixture": True, "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "shadow_integration": False, "automatic_promotion": False, "live_provider_request": False, "capture": {"season": 2026, "week": 1, "captured_at": captured, "first_kickoff_at": kickoff, "hours_before_first_kickoff": 18.0, "schedule_snapshot_sha256": forecasts[0]["schedule_snapshot_sha256"]}, "source_records": records})
        score = lambda raw, scoring: float(raw["yards"]) * float(scoring.get("pass_yd", 0.0)) + float(raw["opportunities"]) * float(scoring.get("rec", 0.0))
        if args.canonical:
            assert canonical_score({"passing_yards": 100.0, "receptions": 2.0}, {"pass_yd": 0.04, "rec": 1.0}) == 6.0
            score = canonical_score
        output = root / "capture"
        assert create_operational_capture(manifest, output, score=score)["status"] == "CREATED"
        assert validate_capture(output, 2026, 1)["status"] == "CAPTURED"
        assert create_operational_capture(manifest, output, score=score)["status"] == "EXISTS"
        outcome_path = bundle / "outcomes.jsonl.gz"
        write_jsonl_gzip(outcome_path, fixture_outcome_rows(forecasts, 2026, 1))
        outcome_manifest = bundle / "outcomes.json"
        write_json(outcome_manifest, {"schema": "fie-m10-prospective-operational-outcome-input-v1", "fixture": True, "season": 2026, "week": 1, "revision": 1, "historical_reconstruction": False, "point_in_time_outcome_source": True, "source_release_or_commit": "fixture-r1", "source_payload_sha256": "c" * 64, "rows_path": outcome_path.relative_to(bundle).as_posix(), "rows_sha256": sha256_file(outcome_path)})
        assert append_outcomes(outcome_manifest, output)["status"] == "CREATED"
        assert validate_capture(output, 2026, 1, require_outcome=True)["outcome_present"] is True
        bad = root / "bad-input.json"
        bad_value = __import__("json").loads(manifest.read_text(encoding="utf-8"))
        bad_value["capture"]["hours_before_first_kickoff"] = 19.0
        write_json(bad, bad_value)
        try:
            validate_input_bundle(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("late operational input was accepted")
    finally:
        shutil.rmtree(root)
    print("PASS Tranche 7C locked inputs, exact replay adapter, decision traces, and append-only outcomes")


if __name__ == "__main__":
    main()

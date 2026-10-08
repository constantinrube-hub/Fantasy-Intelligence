#!/usr/bin/env python3
"""Cutoff profile is preserved byte-for-byte and rejects a conflicting retry."""
from __future__ import annotations

import tempfile
from pathlib import Path

from m10_prospective_capture_contract import capture_hours, sha256_file, write_json, write_jsonl_gzip
from preserve_m10_profile_snapshot import preserve


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-m10-profiles-") as name:
        root = Path(name)
        source, out = root / "prepared", root / "prospective"
        source.mkdir()
        observed, kickoff = "2026-09-09T12:00:00+00:00", "2026-09-10T00:00:00+00:00"
        profiles = source / "profiles.json"
        write_json(profiles, {"profiles": [{
            "league_id": "fixture", "league_format": "REDRAFT", "profile_scoring_signature": "fixture-sig",
            "profile_fingerprint": "fixture-fingerprint", "scoring_settings": {"rec": 1.0}, "captured_at": observed,
        }]})
        forecast = source / "forecasts.jsonl.gz"
        write_jsonl_gzip(forecast, [])
        decisions = source / "decisions.json"
        write_json(decisions, {})
        records = [{"role": role, "path": path.name, "sha256": sha256_file(path),
                    "captured_at": observed, "as_of": observed,
                    "point_in_time_eligible": True, "historical_reconstruction": False}
                   for role, path in (("forecast_rows", forecast), ("profile_snapshot", profiles), ("decision_inputs", decisions))]
        manifest = source / "input-manifest.json"
        write_json(manifest, {
            "schema": "fie-m10-prospective-operational-input-v1", "fixture": True,
            "research_only": True, "production_model": "M9", "capture": {
                "season": 2026, "week": 1, "captured_at": observed, "first_kickoff_at": kickoff,
                "hours_before_first_kickoff": capture_hours(observed, kickoff),
            }, "source_records": records,
        })
        target = preserve(manifest, out)
        assert target.read_bytes() == profiles.read_bytes()
        assert preserve(manifest, out) == target
        target.write_bytes(b"different")
        try:
            preserve(manifest, out)
        except ValueError as exc:
            assert "M10_PROFILE_SNAPSHOT_FIRST_WRITE_COLLISION" in str(exc)
        else:
            raise AssertionError("conflicting profile retry admitted")
        target.unlink()
        profiles.write_bytes(b"tampered")
        try:
            preserve(manifest, out)
        except AssertionError:
            pass
        else:
            raise AssertionError("altered input profile hash admitted")
    print("M10 cutoff profile snapshot: exact bytes, safe retry, collision and input tamper passed")


if __name__ == "__main__":
    main()

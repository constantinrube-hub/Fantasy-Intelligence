#!/usr/bin/env python3
"""No-network R8B proof for frozen v2 weekly inference and capture."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from m10_prospective_capture_contract import read_json, sha256_file, write_json
from m10_prospective_operational_capture import create_operational_capture, create_operational_missed_capture, validate_input_bundle
from m10_prospective_source_bundle import create_bundle
from m10_prospective_weekly_producer import build_weekly_input, fixture_raw_envelope


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="fie-r8b-"))
    try:
        raw = fixture_raw_envelope(root)
        evidence = root / "evidence"
        bundle = create_bundle(raw, evidence)
        assert bundle["status"] == "CREATED"
        prepared = build_weekly_input(raw, root / "prepared", source_bundle=Path(bundle["manifest"]))
        assert prepared["status"] == "CREATED"
        value, paths = validate_input_bundle(Path(prepared["manifest"]))
        assert value["schema"] == "fie-m10-prospective-operational-input-v2" and set(paths) == {"forecast_rows", "profile_snapshot", "decision_inputs"}
        capture = root / "capture"
        assert create_operational_capture(Path(prepared["manifest"]), capture)["status"] == "CREATED"
        manifest = read_json(capture / "forecasts" / "2026" / "week_05" / "capture-manifest.json")
        assert manifest["ledgers"]["forecast"]["rows"] == 12
        assert manifest["ledgers"]["scoring_replay"]["rows"] == 12 * 22
        assert create_operational_capture(Path(prepared["manifest"]), capture)["status"] == "EXISTS"
        # The source envelope is immutable and its response metadata is committed
        # into the source bundle before any model transform runs.
        source = read_json(Path(bundle["manifest"]))
        assert all(row.get("source_identity") and row.get("release_or_etag") for row in source["source_records"])
        # An incomplete roster does not reduce the forecast universe; it blocks
        # only that league's decision traces symmetrically for all candidates.
        decision = read_json(paths["decision_inputs"])
        decision["league_roster_states"][0]["complete"] = False
        write_json(paths["decision_inputs"], decision)
        manifest_value = read_json(Path(prepared["manifest"]))
        for record in manifest_value["source_records"]:
            if record["role"] == "decision_inputs": record["sha256"] = sha256_file(paths["decision_inputs"])
        write_json(Path(prepared["manifest"]), manifest_value)
        blocked = root / "blocked"
        assert create_operational_capture(Path(prepared["manifest"]), blocked)["status"] == "CREATED"
        rows = __import__("gzip").open(blocked / "decision-traces" / "2026" / "week_05" / "decision-traces.jsonl.gz", "rt", encoding="utf-8").read().splitlines()
        assert sum("BLOCKED_INCOMPLETE_LEGAL_ROSTER" in row for row in rows) == 3
        early = fixture_raw_envelope(root / "early", "2026-09-08T00:00:00+00:00")
        assert create_bundle(early, root / "early-evidence")["status"] == "WINDOW_NOT_REACHED"
        late = fixture_raw_envelope(root / "late", "2026-09-10T02:00:00+00:00")
        assert build_weekly_input(late, root / "late-prepared", source_bundle=Path(bundle["manifest"]))["status"] == "POST_KICKOFF"
        assert create_operational_missed_capture(root / "missed", season=2026, week=5, observed_at="2026-09-10T02:00:00+00:00", first_kickoff_at="2026-09-10T00:00:00+00:00", reason="INPUTS_UNAVAILABLE")["status"] == "CREATED"
    finally:
        shutil.rmtree(root)
    print("PASS R8B frozen v2 inference, exact profile residual replay, and typed legal-roster blockers")


if __name__ == "__main__":
    main()

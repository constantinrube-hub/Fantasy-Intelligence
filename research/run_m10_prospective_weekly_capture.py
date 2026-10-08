#!/usr/bin/env python3
"""Run R8C's governed weekly capture from a pre-written raw source envelope."""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from m10_prospective_capture_contract import ROOT, capture_paths, read_json
from m10_prospective_operational_capture import create_operational_capture, create_operational_missed_capture
from m10_prospective_source_bundle import create_bundle
from m10_prospective_weekly_producer import build_weekly_input, validate_raw_envelope
from preserve_m10_profile_snapshot import preserve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--raw-envelope", required=True); parser.add_argument("--output-root", default="data/research/prospective/m10"); args = parser.parse_args(argv)
    raw = Path(args.raw_envelope); raw = raw if raw.is_absolute() else ROOT / raw
    root = Path(args.output_root); root = root if root.is_absolute() else ROOT / root
    value, _ = validate_raw_envelope(raw)
    capture = value["capture"]; hours = float(capture["hours_before_first_kickoff"])
    print(f"M10_STAGE capture season={capture['season']} week={capture['week']} hours_before_first_kickoff={hours:.3f}", flush=True)
    existing = capture_paths(root, int(capture["season"]), int(capture["week"]))
    completed = existing["manifest"] if existing["manifest"].exists() else existing["missed"]
    if completed.exists():
        print(f"PASS R8C weekly capture EXISTS: {completed}")
        return 0
    if hours > 18.0:
        print("NO_WRITE_WINDOW_NOT_REACHED"); return 0
    if hours < 0.0:
        result = create_operational_missed_capture(root, season=int(capture["season"]), week=int(capture["week"]), observed_at=str(capture["observed_at"]), first_kickoff_at=str(capture["first_kickoff_at"]), reason="INPUTS_UNAVAILABLE", fixture=bool(value.get("fixture") is True))
        print(f"PASS R8C typed miss {result['status']}"); return 0
    print("M10_STAGE preserve_source_bundle", flush=True)
    source = create_bundle(raw, root)
    assert source["status"] in {"CREATED", "EXISTS"}
    scratch = Path(tempfile.mkdtemp(prefix="fie-r8c-prepared-"))
    try:
        prepared = build_weekly_input(raw, scratch, source_bundle=Path(source["manifest"]))
        assert prepared["status"] in {"CREATED", "WINDOW_NOT_REACHED"}
        if prepared["status"] == "WINDOW_NOT_REACHED":
            print("NO_WRITE_WINDOW_NOT_REACHED"); return 0
        profile_path = preserve(Path(prepared["manifest"]), root)
        print(f"M10_STAGE frozen_profile_snapshot {profile_path}", flush=True)
        print("M10_STAGE immutable_capture_and_profile_replay", flush=True)
        result = create_operational_capture(Path(prepared["manifest"]), root)
    finally:
        shutil.rmtree(scratch)
    print(f"PASS R8C weekly capture {result['status']}: {result['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

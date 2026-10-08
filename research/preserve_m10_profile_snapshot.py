#!/usr/bin/env python3
"""First-write the exact cutoff profile settings used for M10 scoring replay."""
from __future__ import annotations

from pathlib import Path

from m10_prospective_capture_contract import read_json, sha256_file, week_dir
from m10_prospective_operational_capture import validate_input_bundle, validate_profiles


def preserve(input_manifest: Path, output_root: Path) -> Path:
    value, paths = validate_input_bundle(input_manifest)
    profiles_path = paths["profile_snapshot"]
    profiles = read_json(profiles_path)["profiles"]
    validate_profiles(profiles, fixture=value.get("fixture") is True)
    capture = value["capture"]
    target = week_dir(output_root, "scoring-replay", int(capture["season"]), int(capture["week"])) / "profile-snapshot.json"
    data = profiles_path.read_bytes()
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError("M10_PROFILE_SNAPSHOT_FIRST_WRITE_COLLISION")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    assert sha256_file(target) == sha256_file(profiles_path)
    return target

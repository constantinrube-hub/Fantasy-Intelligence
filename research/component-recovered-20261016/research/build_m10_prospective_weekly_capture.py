#!/usr/bin/env python3
"""Build the deterministic R8B fixture capture used by the controlled target."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_capture_contract import ROOT, validate_capture
from m10_prospective_operational_capture import create_operational_capture
from m10_prospective_source_bundle import create_bundle
from m10_prospective_weekly_producer import build_weekly_input, fixture_raw_envelope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true", help="the controlled target accepts no live provider calls")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("R8B controlled target permits only --fixture; live collection requires closed R8C on main")
    root = Path(args.output_root)
    root = root if root.is_absolute() else ROOT / root
    raw = fixture_raw_envelope(root / "inputs")
    bundle = create_bundle(raw, root)
    assert bundle["status"] == "CREATED"
    prepared = build_weekly_input(raw, root / "prepared", source_bundle=Path(bundle["manifest"]))
    assert prepared["status"] == "CREATED"
    capture = create_operational_capture(Path(prepared["manifest"]), root)
    assert capture["status"] == "CREATED"
    result = validate_capture(root, 2026, 5, require_fixture=True)
    print(f"PASS R8B fixture capture={capture['status']} forecast_rows={result['forecast_rows']} scoring_rows={result['scoring_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

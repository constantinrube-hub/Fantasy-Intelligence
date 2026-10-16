#!/usr/bin/env python3
"""Build the corrected R8A portable 2026 season lock from an explicit input."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_season_lock_v2 import ROOT, build_lock, first_write, load_json, make_fixture_input, validate_lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="explicit corrected historical training matrix JSON")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if bool(args.input) == bool(args.fixture):
        parser.error("provide exactly one of --input or --fixture")
    lock = build_lock(make_fixture_input() if args.fixture else load_json(Path(args.input)))
    validate_lock(lock)
    output = Path(args.output); output = output if output.is_absolute() else ROOT / output
    print(f"PASS {first_write(output, lock)} {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

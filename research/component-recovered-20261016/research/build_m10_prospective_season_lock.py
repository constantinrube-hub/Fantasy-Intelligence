#!/usr/bin/env python3
"""Build the immutable 2026 research-only M9/M10 season lock."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_season_lock import ROOT, build_lock, first_write, load_json, make_fixture_input, validate_lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="explicit historical training matrix JSON")
    parser.add_argument("--fixture", action="store_true", help="use the deterministic no-network test matrix")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if bool(args.input) == bool(args.fixture):
        parser.error("provide exactly one of --input or --fixture")
    source = make_fixture_input() if args.fixture else load_json(Path(args.input))
    lock = build_lock(source); validate_lock(lock)
    path = Path(args.output); path = path if path.is_absolute() else ROOT / path
    print(f"PASS {first_write(path, lock)} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

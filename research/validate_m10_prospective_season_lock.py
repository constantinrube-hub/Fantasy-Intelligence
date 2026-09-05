#!/usr/bin/env python3
"""Validate an exported Tranche 7C-R1 season lock without refitting."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_season_lock import load_json, validate_lock


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("lock"); args = parser.parse_args()
    validate_lock(load_json(Path(args.lock)))
    print(f"PASS valid immutable season lock {args.lock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a corrected R8A lock without refitting."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_season_lock_v2 import load_json, validate_lock


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("lock"); args = parser.parse_args()
    validate_lock(load_json(Path(args.lock)))
    print(f"PASS valid corrected immutable season lock {args.lock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a controlled operational-prospective capture.

The default remains fail-closed for a non-fixture collection.  The explicit
fixture switch exists solely for the R8C no-network workflow target.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_capture_contract import ROOT, validate_capture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/research/prospective/m10")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--require-outcome", action="store_true")
    parser.add_argument("--fixture", action="store_true", help="require a controlled no-network fixture capture")
    args = parser.parse_args(argv)
    root = Path(args.root)
    root = root if root.is_absolute() else ROOT / root
    # Default invariant remains require_fixture=False; fixture mode is explicit.
    require_fixture = True if args.fixture else False
    result = validate_capture(root, args.season, args.week, require_outcome=args.require_outcome, require_fixture=require_fixture)
    print(f"PASS Tranche 7C operational capture status={result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

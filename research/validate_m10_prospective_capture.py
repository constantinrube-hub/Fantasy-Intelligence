#!/usr/bin/env python3
"""Validate a deterministic Tranche 7B synthetic prospective capture."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_capture_contract import ROOT, validate_capture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/research/prospective/m10")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--require-outcome", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    root = root if root.is_absolute() else ROOT / root
    result = validate_capture(root, args.season, args.week, require_outcome=args.require_outcome)
    print(f"PASS Tranche 7B capture status={result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

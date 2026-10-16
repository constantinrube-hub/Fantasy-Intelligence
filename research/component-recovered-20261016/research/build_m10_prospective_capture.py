#!/usr/bin/env python3
"""Create Tranche 7B synthetic prospective-capture evidence only."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_capture_contract import ROOT, create_fixture_capture, create_fixture_outcomes, create_missed_capture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true", help="required in 7B; live collection begins only in 7C")
    parser.add_argument("--fixture-outcomes", action="store_true")
    parser.add_argument("--missed-capture", action="store_true")
    parser.add_argument("--missed-reason", default="WINDOW_MISSED")
    parser.add_argument("--output-root", default="data/research/prospective/m10")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--captured-at", default="2026-09-09T06:00:00+00:00")
    parser.add_argument("--first-kickoff-at", default="2026-09-10T00:00:00+00:00")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Tranche 7B permits only --fixture; live prospective collection requires Tranche 7C")
    if args.fixture_outcomes and args.missed_capture:
        raise SystemExit("--fixture-outcomes cannot accompany --missed-capture")
    root = Path(args.output_root)
    root = root if root.is_absolute() else ROOT / root
    if args.missed_capture:
        result = create_missed_capture(root, args.season, args.week, args.captured_at, args.first_kickoff_at, args.missed_reason)
    else:
        result = create_fixture_capture(root, args.season, args.week, args.captured_at, args.first_kickoff_at)
        if args.fixture_outcomes:
            create_fixture_outcomes(root, args.season, args.week)
    print(f"PASS Tranche 7B fixture {result['status']}: {result['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

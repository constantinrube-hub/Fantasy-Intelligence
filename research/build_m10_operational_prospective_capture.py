#!/usr/bin/env python3
"""Run the 7C audit-branch adapter from an explicit, locked input bundle."""
from __future__ import annotations

import argparse
from pathlib import Path

from m10_prospective_operational_capture import ROOT, append_outcomes, create_operational_capture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--output-root", default="data/research/prospective/m10")
    parser.add_argument("--outcomes-manifest")
    args = parser.parse_args(argv)
    input_manifest = Path(args.input_manifest)
    input_manifest = input_manifest if input_manifest.is_absolute() else ROOT / input_manifest
    output_root = Path(args.output_root)
    output_root = output_root if output_root.is_absolute() else ROOT / output_root
    result = create_operational_capture(input_manifest, output_root)
    if args.outcomes_manifest:
        outcome = Path(args.outcomes_manifest)
        outcome = outcome if outcome.is_absolute() else ROOT / outcome
        append_outcomes(outcome, output_root)
    print(f"PASS Tranche 7C operational adapter {result['status']}: {result['manifest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

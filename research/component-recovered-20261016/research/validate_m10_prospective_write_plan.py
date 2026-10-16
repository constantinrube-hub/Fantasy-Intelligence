#!/usr/bin/env python3
"""Validate the exact staged or diffed path set of an R8C operational write."""
from __future__ import annotations

import argparse
import subprocess

from fie_research_pipeline_contract import ROOT
from m10_prospective_activation_guard import validate_write_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--github-ref", required=True); parser.add_argument("--base"); args = parser.parse_args(argv)
    command = ["git", "diff", "--name-only", args.base] if args.base else ["git", "diff", "--name-only"]
    paths = [value.strip() for value in subprocess.check_output(command, cwd=ROOT, text=True).splitlines() if value.strip()]
    validate_write_plan(args.github_ref, paths)
    print(f"PASS R8C write allowlist paths={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

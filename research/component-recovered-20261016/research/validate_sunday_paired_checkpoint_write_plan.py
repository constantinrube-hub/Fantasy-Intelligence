#!/usr/bin/env python3
"""Allow only additive Sunday checkpoint evidence and its derived inventory."""
from __future__ import annotations
import argparse
import subprocess
from fie_research_pipeline_contract import ROOT

PREFIXES = (
    "data/research/prospective/m10/checkpoints/",
    "data/research/prospective/paired-checkpoints/",
    "data/research/market/sleeper/checkpoints/",
)
INVENTORY = "data/research/portfolio/2026/point-in-time-evidence-report.json"


def validate(ref: str, paths: list[str]) -> None:
    if ref != "refs/heads/main": raise ValueError("Sunday checkpoint writes require main")
    forbidden = [path for path in paths if path != INVENTORY and not any(path.startswith(prefix) for prefix in PREFIXES)]
    if forbidden: raise ValueError("Sunday checkpoint write plan escaped additive namespaces: " + ", ".join(forbidden))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--github-ref", required=True); parser.add_argument("--base"); args = parser.parse_args(argv)
    command = ["git", "diff", "--name-only", args.base] if args.base else ["git", "diff", "HEAD", "--name-only"]
    paths = [row.strip() for row in subprocess.check_output(command, cwd=ROOT, text=True).splitlines() if row.strip()]
    validate(args.github_ref, paths); print(f"PASS Sunday checkpoint write allowlist paths={len(paths)}"); return 0


if __name__ == "__main__": raise SystemExit(main())

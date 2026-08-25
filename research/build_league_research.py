#!/usr/bin/env python3
"""Canonical non-committing League-ID M1-M6 builder used by bulk onboarding.

This script deliberately performs no git operations. Parallel jobs can therefore
build isolated League-ID artifacts safely, upload them, and let one merge job
commit once.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*parts: str) -> None:
    cmd = [str(x) for x in parts]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def season_windows() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    last_complete = now.year - 2 if now.month == 1 else now.year - 1
    return f"2019-{last_complete}", f"2016-{last_complete}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--format", required=True)
    ap.add_argument("--portfolio-config", default="config/league-portfolio.json")
    ap.add_argument("--league-root")
    ap.add_argument("--derived-dir")
    ap.add_argument("--cache-dir")
    ap.add_argument("--registry", default="/tmp/fie-bulk-registry.json")
    ap.add_argument("--full-raw-cache", action="store_true")
    args = ap.parse_args()

    lid = str(args.league_id)
    if not lid.isdigit() or not (6 <= len(lid) <= 32):
        raise SystemExit("invalid Sleeper League ID")
    league_root = Path(args.league_root or f"data/research/leagues/{lid}")
    derived = Path(args.derived_dir or f".cache/fie-research/leagues/{lid}/derived")
    cache = Path(args.cache_dir or f".cache/fie-research/leagues/{lid}")
    league_root.mkdir(parents=True, exist_ok=True)
    derived.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    primary, extended = season_windows()

    # Never retain stale historical outputs in a requested rebuild. Current-season
    # and operator override files are left alone when an existing namespace is used.
    for i in range(1, 7):
        p = league_root / f"milestone{i}.json"
        if p.exists():
            p.unlink()
    prof = league_root / "profile.json"
    if prof.exists():
        prof.unlink()

    run("python", "research/league_profile.py", "build", "--league-id", lid, "--format", args.format,
        "--output", str(league_root / "profile.json"), "--registry", args.registry,
        "--portfolio-config", args.portfolio_config)

    m1 = ["python", "research/fie_research.py", "--seasons", primary, "--extended-seasons", extended,
          "--output", str(league_root / "milestone1.json"), "--derived-dir", str(derived), "--league-id", lid]
    if args.full_raw_cache:
        m1.append("--full-raw-cache")
    run(*m1)
    run("python", "research/validate_bundle.py", str(league_root / "milestone1.json"))

    run("python", "research/fie_m2.py", "--m1-derived-dir", str(derived), "--m1-bundle", str(league_root / "milestone1.json"),
        "--derived-dir", str(derived), "--output", str(league_root / "milestone2.json"))
    run("python", "research/validate_m2_bundle.py", str(league_root / "milestone2.json"))

    run("python", "research/fie_m3.py", "--derived-dir", str(derived), "--m1-bundle", str(league_root / "milestone1.json"),
        "--m2-bundle", str(league_root / "milestone2.json"), "--cache-dir", str(cache), "--seasons", primary,
        "--output", str(league_root / "milestone3.json"))
    run("python", "research/validate_m3_bundle.py", str(league_root / "milestone3.json"))

    run("python", "research/fie_m4.py", "--derived-dir", str(derived), "--m1-bundle", str(league_root / "milestone1.json"),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--cache-dir", str(cache), "--sleeper-archive", "data/research/market/sleeper", "--seasons", primary,
        "--output", str(league_root / "milestone4.json"))
    run("python", "research/validate_m4_bundle.py", str(league_root / "milestone4.json"))

    run("python", "research/fie_m5.py", "--derived-dir", str(derived), "--m1-bundle", str(league_root / "milestone1.json"),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--m4-bundle", str(league_root / "milestone4.json"), "--output", str(league_root / "milestone5.json"))
    run("python", "research/validate_m5_bundle.py", str(league_root / "milestone5.json"))

    run("python", "research/fie_m6.py", "--derived-dir", str(derived), "--m1-bundle", str(league_root / "milestone1.json"),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--m4-bundle", str(league_root / "milestone4.json"), "--m5-bundle", str(league_root / "milestone5.json"),
        "--cache-dir", str(cache), "--seasons", primary, "--output", str(league_root / "milestone6.json"))
    run("python", "research/validate_m6_bundle.py", str(league_root / "milestone6.json"))

    run("python", "research/stamp_league_artifacts.py", "--profile", str(league_root / "profile.json"),
        *[str(league_root / f"milestone{i}.json") for i in range(1, 7)])
    for i, validator in [(1, "validate_bundle.py"), (2, "validate_m2_bundle.py"), (3, "validate_m3_bundle.py"),
                         (4, "validate_m4_bundle.py"), (5, "validate_m5_bundle.py"), (6, "validate_m6_bundle.py")]:
        run("python", f"research/{validator}", str(league_root / f"milestone{i}.json"))

    run("python", "research/fie_governance.py", "--league-id", lid, "--league-profile", str(league_root / "profile.json"),
        "--m4-bundle", str(league_root / "milestone4.json"), "--m5-bundle", str(league_root / "milestone5.json"),
        "--m6-bundle", str(league_root / "milestone6.json"), "--current-snapshot", str(league_root / "current/milestone5_current.json"),
        "--operator-override", str(league_root / "governance/operator_override.json"),
        "--global-operator-override", "data/research/governance/operator_override.json",
        "--output", str(league_root / "governance/active_release.json"))

    print(f"Bulk build complete for {lid}: {league_root}")


if __name__ == "__main__":
    main()

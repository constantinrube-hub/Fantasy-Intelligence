#!/usr/bin/env python3
"""Capture a timing-verified immutable Sleeper projection benchmark.

Automated mode writes only during a configurable window before the FIRST regular-
season kickoff of the Sleeper week.  This avoids freezing a Tuesday/preseason
projection merely because it happened to be the first response observed.  Once a
snapshot exists it is never rewritten; SHA-256 registration/tamper checks are
shared with build_current_snapshot.py.

Canonical IDs are optional at capture time.  The raw Sleeper player ID is immutable
and M4 may map it to a canonical ID later from the historical identity table.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from build_current_snapshot import archive_sleeper_projection, first_kickoff_utc, load_schedule

UA = "Fantasy-Intelligence-Engine/market-capture-v3"


def get_json(url: str):
    r = requests.get(url, timeout=30, headers={"User-Agent": UA, "Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int)
    p.add_argument("--week", type=int)
    p.add_argument("--derived-dir", default="data/research/derived")
    p.add_argument("--output-root", default="data/research/market/sleeper")
    p.add_argument("--cache-dir", default=".cache/fie-market")
    p.add_argument(
        "--auto-pregame",
        action="store_true",
        help="Verify regular-season status and first kickoff from nflverse before marking eligible.",
    )
    p.add_argument(
        "--capture-window-hours",
        type=float,
        default=18.0,
        help="In auto mode, first-write only when first kickoff is this many hours away or less.",
    )
    p.add_argument(
        "--pregame-eligible",
        action="store_true",
        help="Manual assertion for operator captures. Prefer --auto-pregame in automation.",
    )
    p.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args()


def main():
    a = parse_args()
    if a.force:
        raise SystemExit("--force is disabled: Sleeper benchmark snapshots are immutable by design")
    if a.auto_pregame and a.pregame_eligible:
        raise SystemExit("Choose --auto-pregame or --pregame-eligible, not both")

    state = {}
    if not a.season or not a.week or a.auto_pregame:
        state = get_json("https://api.sleeper.app/v1/state/nfl")
    season = a.season or int(state.get("season"))
    week = a.week or int(state.get("week"))
    out_root = Path(a.output_root)
    out = out_root / str(season) / f"week_{week:02d}.jsonl.gz"

    # Existing first-write snapshots can always be re-registered/hash-verified
    # without another provider request or a new timing assertion.
    if out.exists():
        meta = archive_sleeper_projection([], season, week, pd.DataFrame(), out_root, False)
        print(f"Preserved immutable {meta.get('path')} sha256={meta.get('sha256')} pregame_eligible={meta.get('pregame_eligible')}")
        return

    pregame = bool(a.pregame_eligible)
    if a.auto_pregame:
        season_type = str(state.get("season_type") or "").lower()
        if season_type != "regular":
            print(f"SKIP: Sleeper season_type={season_type or 'unknown'}; benchmark capture waits for regular season")
            return
        schedule = load_schedule(Path(a.cache_dir))
        kickoff = first_kickoff_utc(schedule, season, week)
        if kickoff is None:
            raise SystemExit("Cannot verify first kickoff; refusing to mark a benchmark pregame-eligible")
        now = datetime.now(timezone.utc)
        hours = (kickoff - now).total_seconds() / 3600
        if hours <= 0:
            raise SystemExit(f"MISSED: Week {week} first kickoff already occurred at {kickoff.isoformat()}; no eligible snapshot written")
        if hours > float(a.capture_window_hours):
            print(f"SKIP: first kickoff is {hours:.1f}h away; capture window starts at <= {a.capture_window_hours:.1f}h")
            return
        pregame = True
        print(f"Timing verified: first kickoff {kickoff.isoformat()} ({hours:.1f}h away)")

    ident_path = Path(a.derived_dir) / "player_identity.csv.gz"
    ident = pd.read_csv(ident_path, low_memory=False) if ident_path.exists() else pd.DataFrame()
    rows = get_json(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular")
    meta = archive_sleeper_projection(rows or [], season, week, ident, out_root, pregame)
    print(
        f"Wrote {meta.get('path')} rows={meta.get('rows')} pregame_eligible={meta.get('pregame_eligible')} "
        f"sha256={meta.get('sha256')} canonical_identity_available={not ident.empty}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Capture completed-week nflverse player stats for one PR2 lineup outcome.

The source is the established public nflverse player-week release.  It is a
strict athlete/GSIS bridge only: team D/ST rows remain absent and therefore
block exact outcome replay until separately evidenced from a team-capable
source.  No display-name joins or later current-snapshot lookups are allowed.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    from adapt_in_season_pr2_lineup_outcome_stats import SOURCE_SCHEMA, source_identity
    from point_in_time_capture import first_write_json, sha256_bytes
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.adapt_in_season_pr2_lineup_outcome_stats import SOURCE_SCHEMA, source_identity
    from research.point_in_time_capture import first_write_json, sha256_bytes


STATS_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
UA = "Fantasy-Intelligence-InSeason-Lineup-Outcomes/1.0"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": UA, "Accept": "text/csv"})
    with urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read()


def capture_gsis_ids(capture: dict[str, Any]) -> set[str]:
    if not capture.get("capture_id") or not capture.get("capture_content_sha256"):
        raise ValueError("immutable capture required")
    values: set[str] = set()
    for report in capture.get("leagues") or []:
        if not isinstance(report, dict) or report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
            continue
        source = report.get("evaluation_input") or {}
        if source.get("schema") != "fie-in-season-pr2-lineup-evaluation-input-v1":
            continue
        for candidate in source.get("active_candidates") or []:
            if isinstance(candidate, dict):
                identity = source_identity(candidate, "gsis")
                if identity:
                    values.add(identity)
    return values


def rows_for_target(csv_bytes: bytes, *, season: int, week: int, gsis_ids: set[str]) -> dict[str, dict[str, Any]]:
    rows = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        try:
            if int(row.get("season") or 0) != int(season) or int(row.get("week") or 0) != int(week):
                continue
        except ValueError:
            continue
        if str(row.get("season_type") or "").upper() not in {"REG", "REGULAR"}:
            continue
        player_id = str(row.get("player_id") or "").strip()
        if player_id not in gsis_ids:
            continue
        if player_id in selected:
            raise ValueError(f"duplicate nflverse player-week row: {player_id}")
        selected[player_id] = {key: value for key, value in row.items() if value not in (None, "")}
    return dict(sorted(selected.items()))


def build_source(capture: dict[str, Any], csv_bytes: bytes, *, season: int, week: int, observed_at: str, endpoint: str) -> dict[str, Any]:
    expected_season = capture.get("leagues", [{}])[0].get("season") if capture.get("leagues") else None
    expected_week = capture.get("leagues", [{}])[0].get("week") if capture.get("leagues") else None
    if int(expected_season or 0) != int(season) or int(expected_week or 0) != int(week):
        raise ValueError("capture season/week does not match requested nflverse outcome target")
    gsis_ids = capture_gsis_ids(capture)
    if not gsis_ids:
        raise ValueError("capture has no frozen GSIS athlete identities")
    stats = rows_for_target(csv_bytes, season=season, week=week, gsis_ids=gsis_ids)
    return {
        "schema": SOURCE_SCHEMA,
        "provider": "nflverse",
        "endpoint": endpoint,
        "observed_at": observed_at,
        "season": int(season),
        "week": int(week),
        "source_player_id_namespace": "gsis",
        "sparse_zero_fields_are_explicit": True,
        "stats_by_source_player_id": stats,
        "source_payload_sha256": sha256_bytes(csv_bytes),
        "coverage": {"frozen_gsis_candidate_count": len(gsis_ids), "matched_nflverse_player_rows": len(stats), "team_defense_supported": False},
        "governance": {"research_only": True, "display_name_join": False, "missing_player_rows_zero_imputed": False, "dst_requires_separate_team_outcome_source": True},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture nflverse player-week source stats for an immutable PR2 lineup capture")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--week", required=True, type=int)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats-csv", help="Supplied nflverse player-week CSV; omitted fetches the documented release URL")
    parser.add_argument("--observed-at", default=datetime.now(timezone.utc).isoformat())
    args = parser.parse_args(argv)
    endpoint = STATS_URL.format(season=args.season)
    csv_bytes = Path(args.stats_csv).read_bytes() if args.stats_csv else fetch_bytes(endpoint)
    source = build_source(read_json(Path(args.capture)), csv_bytes, season=args.season, week=args.week, observed_at=args.observed_at, endpoint=endpoint)
    output = Path(args.output)
    first_write_json(output, source)
    print(json.dumps({"output": str(output), "matched_nflverse_player_rows": source["coverage"]["matched_nflverse_player_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

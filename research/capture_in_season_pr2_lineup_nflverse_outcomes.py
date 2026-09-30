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

import pandas as pd

try:
    from adapt_in_season_pr2_lineup_outcome_stats import SOURCE_SCHEMA, source_identity
    from point_in_time_capture import first_write_json, sha256_bytes
    from fie_dst import _team_game_rows
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.adapt_in_season_pr2_lineup_outcome_stats import SOURCE_SCHEMA, source_identity
    from research.point_in_time_capture import first_write_json, sha256_bytes
    from research.fie_dst import _team_game_rows


STATS_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv"
UA = "Fantasy-Intelligence-InSeason-Lineup-Outcomes/1.0"
TEAM_ALIASES = {"LA": "LAR", "STL": "LAR", "JAC": "JAX", "WSH": "WAS", "OAK": "LV", "SD": "LAC"}


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


def canonical_team(value: Any) -> str:
    team = str(value or "").upper().strip()
    return TEAM_ALIASES.get(team, team)


def capture_dst_ids(capture: dict[str, Any]) -> dict[str, str]:
    """Return frozen teamdef capture IDs keyed by canonical NFL team code."""
    values: dict[str, str] = {}
    for report in capture.get("leagues") or []:
        if not isinstance(report, dict) or report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
            continue
        for candidate in (report.get("evaluation_input") or {}).get("active_candidates") or []:
            if not isinstance(candidate, dict) or str(candidate.get("position_model") or "").upper() not in {"DEF", "DST", "D/ST"}:
                continue
            captured = str(candidate.get("captured_player_id") or "")
            team = canonical_team(candidate.get("team"))
            if not captured.startswith("teamdef:") or not team:
                continue
            prior = values.setdefault(team, captured)
            if prior != captured:
                raise ValueError(f"frozen D/ST team identity collision: {team}")
    return values


def dst_rows_for_target(pbp_bytes: bytes, *, season: int, week: int, captured_team_ids: dict[str, str]) -> dict[str, dict[str, Any]]:
    if not captured_team_ids:
        return {}
    frame = pd.read_csv(io.BytesIO(pbp_bytes), low_memory=False)
    required = {"season", "week", "season_type"}
    if not required.issubset(frame.columns):
        raise ValueError("nflverse PBP columns required for D/ST outcome unavailable")
    target = frame[(pd.to_numeric(frame["season"], errors="coerce") == int(season)) & (pd.to_numeric(frame["week"], errors="coerce") == int(week))]
    target = target[target["season_type"].astype(str).str.upper().isin(["REG", "REGULAR"])]
    if target.empty:
        return {}
    values: dict[str, dict[str, Any]] = {}
    for row in _team_game_rows(target):
        captured = captured_team_ids.get(canonical_team(row.get("team")))
        if not captured:
            continue
        if captured in values:
            raise ValueError(f"duplicate nflverse D/ST target-week row: {captured}")
        values[captured] = {str(key): value for key, value in row.items() if key not in {"team", "opponent", "season", "week", "game_id", "home"}}
    return dict(sorted(values.items()))


def build_source(capture: dict[str, Any], csv_bytes: bytes, *, season: int, week: int, observed_at: str, endpoint: str, pbp_bytes: bytes | None = None, pbp_endpoint: str | None = None) -> dict[str, Any]:
    expected_season = capture.get("leagues", [{}])[0].get("season") if capture.get("leagues") else None
    expected_week = capture.get("leagues", [{}])[0].get("week") if capture.get("leagues") else None
    if int(expected_season or 0) != int(season) or int(expected_week or 0) != int(week):
        raise ValueError("capture season/week does not match requested nflverse outcome target")
    gsis_ids = capture_gsis_ids(capture)
    if not gsis_ids:
        raise ValueError("capture has no frozen GSIS athlete identities")
    stats = rows_for_target(csv_bytes, season=season, week=week, gsis_ids=gsis_ids)
    dst_ids = capture_dst_ids(capture)
    dst = dst_rows_for_target(pbp_bytes, season=season, week=week, captured_team_ids=dst_ids) if pbp_bytes is not None else {}
    payload_hash = sha256_bytes(csv_bytes + (b"\0" + pbp_bytes if pbp_bytes is not None else b""))
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
        "direct_stats_by_captured_player_id": dst,
        "source_payload_sha256": payload_hash,
        "additional_endpoints": [pbp_endpoint] if pbp_endpoint else [],
        "coverage": {"frozen_gsis_candidate_count": len(gsis_ids), "matched_nflverse_player_rows": len(stats), "frozen_team_defense_candidate_count": len(dst_ids), "matched_nflverse_team_defense_rows": len(dst), "team_defense_supported": pbp_bytes is not None},
        "governance": {"research_only": True, "display_name_join": False, "missing_player_rows_zero_imputed": False, "team_defense_from_nflverse_pbp": pbp_bytes is not None},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture nflverse player-week source stats for an immutable PR2 lineup capture")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--week", required=True, type=int)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats-csv", help="Supplied nflverse player-week CSV; omitted fetches the documented release URL")
    parser.add_argument("--pbp-csv", help="Supplied nflverse PBP CSV for D/ST outcomes; omitted fetches it when the capture has D/ST candidates")
    parser.add_argument("--observed-at", default=datetime.now(timezone.utc).isoformat())
    args = parser.parse_args(argv)
    endpoint = STATS_URL.format(season=args.season)
    csv_bytes = Path(args.stats_csv).read_bytes() if args.stats_csv else fetch_bytes(endpoint)
    capture = read_json(Path(args.capture))
    dst_needed = bool(capture_dst_ids(capture))
    pbp_endpoint = PBP_URL.format(season=args.season)
    pbp_bytes = Path(args.pbp_csv).read_bytes() if args.pbp_csv else (fetch_bytes(pbp_endpoint) if dst_needed else None)
    source = build_source(capture, csv_bytes, season=args.season, week=args.week, observed_at=args.observed_at, endpoint=endpoint, pbp_bytes=pbp_bytes, pbp_endpoint=pbp_endpoint if pbp_bytes is not None else None)
    output = Path(args.output)
    first_write_json(output, source)
    print(json.dumps({"output": str(output), "matched_nflverse_player_rows": source["coverage"]["matched_nflverse_player_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

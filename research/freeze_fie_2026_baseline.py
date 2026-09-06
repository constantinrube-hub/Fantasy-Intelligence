#!/usr/bin/env python3
"""Freeze a truthful versioned 22-league baseline from governed current outputs."""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from fie_research_pipeline_contract import ROOT
from point_in_time_capture import first_write_json, parse_time, sha256_bytes, sha256_file, utc_now


SCHEMA = "fie-2026-season-baseline-v1"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
FORMATS = {"REDRAFT", "DYNASTY", "CHOPPED", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"}


def fetch_games() -> bytes:
    request = Request(GAMES_URL, headers={"User-Agent": "Fantasy-Intelligence-Baseline/1.0"})
    with urlopen(request, timeout=35) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {GAMES_URL}")
        return response.read()


def first_regular_kickoff(raw_csv: bytes, season: int) -> str | None:
    kickoffs = []
    for row in csv.DictReader(io.StringIO(raw_csv.decode("utf-8"))):
        if row.get("season") != str(season) or row.get("game_type") != "REG":
            continue
        local = datetime.fromisoformat(f"{row['gameday']}T{row['gametime']}").replace(tzinfo=ZoneInfo("America/New_York"))
        kickoffs.append(local.astimezone(timezone.utc))
    return min(kickoffs).isoformat() if kickoffs else None


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def source(path: Path, root: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def build_baseline(*, root: Path, season: int, games_csv: bytes, created_at: str) -> dict[str, Any]:
    registry_path = root / "data/research/leagues/registry.json"
    registry = load(registry_path)
    enabled = {str(k): v for k, v in (registry.get("leagues") or {}).items() if v.get("enabled") is True}
    if len(enabled) != 22:
        raise ValueError(f"baseline requires 22 enabled leagues, found {len(enabled)}")
    if {entry.get("format") for entry in enabled.values()} != FORMATS:
        raise ValueError("baseline requires all six registered formats")
    kickoff = first_regular_kickoff(games_csv, season)
    league_rows, timestamps = [], []
    for league_id, entry in sorted(enabled.items()):
        profile_path = root / str(entry["profile_path"])
        release_path = root / f"data/research/leagues/{league_id}/governance/active_release.json"
        app_manifest_path = root / f"data/research/leagues/{league_id}/app/manifest.json"
        rankings_path = root / f"data/research/leagues/{league_id}/performance/{season}/research_pipeline/rankings.json"
        profile, release, app_manifest = load(profile_path), load(release_path), load(app_manifest_path)
        current_rel = str((release.get("current_snapshot") or {}).get("path") or "")
        current_path = root / current_rel
        if not current_rel or not current_path.is_file():
            raise ValueError(f"governed current snapshot missing for {league_id}")
        if profile.get("profile_fingerprint") != entry.get("profile_fingerprint"):
            raise ValueError(f"registry/profile fingerprint mismatch for {league_id}")
        if profile.get("scoring_signature") != entry.get("scoring_signature"):
            raise ValueError(f"registry/profile scoring mismatch for {league_id}")
        generated_values = [
            (release.get("current_snapshot") or {}).get("generated_at"),
            release.get("generated_at"), app_manifest.get("generated_at"),
        ]
        for value in generated_values:
            if value:
                timestamps.append(parse_time(str(value)))
        sources = {
            "profile": source(profile_path, root),
            "active_release": source(release_path, root),
            "app_manifest": source(app_manifest_path, root),
            "current_snapshot": source(current_path, root),
            "rankings": source(rankings_path, root),
        }
        league_rows.append({
            "league_id": league_id,
            "league_name": entry.get("league_name"),
            "format": entry.get("format"),
            "profile_fingerprint": profile["profile_fingerprint"],
            "scoring_signature": profile["scoring_signature"],
            "roster_positions": profile.get("roster_positions") or [],
            "current_snapshot": {
                "season": (release.get("current_snapshot") or {}).get("season"),
                "week": (release.get("current_snapshot") or {}).get("week"),
                "generated_at": (release.get("current_snapshot") or {}).get("generated_at"),
                "eligible_players": (release.get("current_snapshot") or {}).get("eligible_players"),
                "runtime_enabled": release.get("runtime_enabled"),
                "current_complete": (release.get("checks") or {}).get("current_complete"),
                "reason": release.get("reason"),
            },
            "sources": sources,
        })
    source_cutoff = max(timestamps).isoformat() if timestamps else None
    if kickoff is None:
        eligibility = "FIRST_KICKOFF_UNVERIFIABLE"
    elif source_cutoff and parse_time(source_cutoff) < parse_time(kickoff):
        eligibility = "PRESEASON_ELIGIBLE"
    else:
        eligibility = "IN_SEASON_BASELINE_NOT_PRESEASON"
    return {
        "schema_version": SCHEMA,
        "baseline_version": 1,
        "season": season,
        "created_at": parse_time(created_at).isoformat(),
        "source_cutoff": source_cutoff,
        "first_regular_season_kickoff": kickoff,
        "eligibility": eligibility,
        "eligibility_semantics": "PRESEASON_ELIGIBLE only when every recorded governed source timestamp precedes the first regular-season kickoff; no historical reconstruction.",
        "enabled_league_count": len(league_rows),
        "formats": sorted(FORMATS),
        "registry": source(registry_path, root),
        "schedule_source": {"endpoint": GAMES_URL, "payload_sha256": sha256_bytes(games_csv)},
        "leagues": league_rows,
        "governance": {
            "immutable_first_write": True,
            "research_only": True,
            "production_model": "M9",
            "production_or_runtime_changed": False,
            "market_or_adp_used_as_football_feature": False,
        },
    }


def validate_baseline(value: dict[str, Any], root: Path) -> None:
    assert value.get("schema_version") == SCHEMA
    assert value.get("season") == 2026 and value.get("baseline_version") == 1
    assert value.get("enabled_league_count") == 22 and len(value.get("leagues") or []) == 22
    assert set(value.get("formats") or []) == FORMATS
    assert value.get("eligibility") in {"PRESEASON_ELIGIBLE", "IN_SEASON_BASELINE_NOT_PRESEASON", "FIRST_KICKOFF_UNVERIFIABLE"}
    assert value.get("governance") == {
        "immutable_first_write": True,
        "research_only": True,
        "production_model": "M9",
        "production_or_runtime_changed": False,
        "market_or_adp_used_as_football_feature": False,
    }
    for league in value["leagues"]:
        for item in league["sources"].values():
            path = root / item["path"]
            assert path.is_file() and sha256_file(path) == item["sha256"], path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/research/baselines/2026/baseline-v1.json")
    parser.add_argument("--games-csv")
    parser.add_argument("--created-at")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    if output.exists():
        validate_baseline(load(output), ROOT)
        print(f"PASS immutable baseline already exists: {output}")
        return 0
    games_csv = Path(args.games_csv).read_bytes() if args.games_csv else fetch_games()
    baseline = build_baseline(root=ROOT, season=2026, games_csv=games_csv, created_at=args.created_at or utc_now())
    first_write_json(output, baseline)
    validate_baseline(baseline, ROOT)
    print(f"PASS froze {len(baseline['leagues'])}-league baseline eligibility={baseline['eligibility']} at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

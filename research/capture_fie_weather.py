#!/usr/bin/env python3
"""Capture immutable pregame forecasts with explicit observed-time provenance."""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from fie_research_pipeline_contract import ROOT
from point_in_time_capture import (
    build_envelope,
    compact_timestamp,
    first_write_json,
    latest_eligible,
    parse_time,
    sha256_bytes,
    utc_now,
)


GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
STATE_URL = "https://api.sleeper.app/v1/state/nfl"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
UA = "Fantasy-Intelligence-Weather-Evidence/1.0"
CONTEXT_SCHEMA = "fie-context-evidence-v1"


def fetch_bytes(url: str) -> tuple[bytes, dict[str, str | None]]:
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/csv,*/*"})
    with urlopen(request, timeout=35) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read(), {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def kickoff_utc(row: dict[str, str]) -> str:
    local = datetime.fromisoformat(f"{row['gameday']}T{row['gametime']}").replace(tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(timezone.utc).isoformat()


def schedule_rows(raw_csv: bytes, season: int, week: int) -> list[dict[str, Any]]:
    rows = []
    for raw in csv.DictReader(io.StringIO(raw_csv.decode("utf-8"))):
        if raw.get("season") != str(season) or raw.get("week") != str(week) or raw.get("game_type") != "REG":
            continue
        rows.append({
            "game_id": raw["game_id"],
            "home_team": raw["home_team"],
            "away_team": raw["away_team"],
            "kickoff": kickoff_utc(raw),
            "roof": raw.get("roof") or None,
            "surface": raw.get("surface") or None,
            "stadium_id": raw.get("stadium_id") or None,
            "stadium": raw.get("stadium") or None,
        })
    return sorted(rows, key=lambda row: (row["kickoff"], row["game_id"]))


def forecast_url(latitude: float, longitude: float) -> str:
    return FORECAST_URL + "?" + urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,wind_gusts_10m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "UTC",
        "forecast_days": 16,
    })


def hourly_at_kickoff(payload: dict[str, Any], kickoff: str) -> dict[str, Any]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        raise ValueError("weather provider returned no hourly forecast")
    target = parse_time(kickoff)
    parsed = [parse_time(str(value) + ("+00:00" if "Z" not in str(value) and "+" not in str(value)[10:] else "")) for value in times]
    index = min(range(len(parsed)), key=lambda i: abs((parsed[i] - target).total_seconds()))
    if abs((parsed[index] - target).total_seconds()) > 3600:
        raise ValueError("no hourly forecast within one hour of kickoff")

    def value(name: str) -> float | None:
        values = hourly.get(name) or []
        raw = values[index] if index < len(values) else None
        return float(raw) if isinstance(raw, (int, float)) else None

    precipitation = value("precipitation_probability")
    return {
        "forecast_effective_at": parsed[index].isoformat(),
        "temperature_f": value("temperature_2m"),
        "precipitation_probability": precipitation / 100.0 if precipitation is not None else None,
        "wind_mph": value("wind_speed_10m"),
        "gust_mph": value("wind_gusts_10m"),
    }


def build_context(
    *, season: int, week: int, observed_at: str, games: list[dict[str, Any]], sources: list[dict[str, Any]]
) -> dict[str, Any]:
    future = [game for game in games if parse_time(game["kickoff"]) > parse_time(observed_at)]
    cutoff = min((game["kickoff"] for game in future), default=observed_at)
    return {
        "schema_version": CONTEXT_SCHEMA,
        "season": season,
        "week": week,
        "cutoff": cutoff,
        "games": games,
        "provenance": {
            "generated_at": observed_at,
            "prediction_cutoff": cutoff,
            "model_id": None,
            "model_version": None,
            "model_config_sha256": None,
            "research_manifest_sha256": None,
            "profile_fingerprint": None,
            "scoring_signature": None,
            "sources": sources,
        },
    }


def fixture_context() -> dict[str, Any]:
    cutoff = "2026-10-08T16:00:00+00:00"
    runs = [
        {"observed_at": "2026-10-08T12:10:00+00:00", "run_at": "2026-10-08T12:00:00+00:00", "wind_mph": 25.0},
        {"observed_at": "2026-10-08T18:10:00+00:00", "run_at": "2026-10-08T18:00:00+00:00", "wind_mph": 10.0},
    ]
    selected = latest_eligible(runs, cutoff=cutoff)
    assert selected and selected["wind_mph"] == 25.0
    return build_context(
        season=2026, week=5, observed_at="2026-10-08T15:00:00+00:00",
        games=[{
            "game_id": "2026_05_AAA_BBB", "home_team": "BBB", "away_team": "AAA",
            "kickoff": "2026-10-08T20:15:00+00:00",
            "environment": {
                "forecast_observed_at": selected["observed_at"], "forecast_run_at": selected["run_at"],
                "forecast_run_metadata_status": "EXPOSED", "wind_mph": selected["wind_mph"],
                "gust_mph": 34.0, "temperature_f": 48.0, "precipitation_probability": 0.35,
                "roof": "outdoors", "surface": "grass",
            },
            "coaching": {}, "team_context": {},
        }],
        sources=[],
    )


def capture(*, output_root: Path, season: int, week: int, fixture: bool = False) -> Path:
    observed_at = "2026-10-08T15:00:00+00:00" if fixture else utc_now()
    stamp = compact_timestamp(observed_at)
    capture_dir = output_root / str(season) / f"week_{week:02d}" / stamp
    if fixture:
        context = fixture_context()
        first_write_json(capture_dir / "context-evidence.json", context)
        return capture_dir / "context-evidence.json"

    schedule_bytes, schedule_headers = fetch_bytes(GAMES_URL)
    schedule = schedule_rows(schedule_bytes, season, week)
    if not schedule:
        raise ValueError(f"no regular-season schedule for {season} week {week}")
    venues = json.loads((ROOT / "config/nfl-venue-coordinates-v1.json").read_text(encoding="utf-8"))["teams"]
    schedule_payload = {"season": season, "week": week, "games": schedule, "response_sha256": sha256_bytes(schedule_bytes)}
    schedule_envelope = build_envelope(
        capture_id=f"nflverse-schedule-{season}-{week:02d}-{stamp}", capture_intent="OTHER_GOVERNED",
        provider="nflverse", endpoint=GAMES_URL, observed_at=observed_at,
        as_of_semantics="Schedule response observed at capture time and used only to identify future game kickoffs/venues.",
        payload=schedule_payload, release_identifier=schedule_headers.get("etag") or schedule_headers.get("last_modified"),
        revision_metadata_status="EXPOSED" if any(schedule_headers.values()) else "NOT_EXPOSED_BY_PROVIDER",
    )
    first_write_json(capture_dir / "schedule-source-envelope.json", schedule_envelope)
    context_games, source_refs = [], []
    for game in schedule:
        if parse_time(game["kickoff"]) <= parse_time(observed_at):
            continue
        venue = venues.get(game["home_team"])
        if not venue:
            context_games.append({**game, "environment": {
                "forecast_observed_at": None, "forecast_run_at": None,
                "forecast_run_metadata_status": "UNAVAILABLE_VENUE_COORDINATES",
                "temperature_f": None, "precipitation_probability": None, "wind_mph": None, "gust_mph": None,
                "roof": game.get("roof"), "surface": game.get("surface"),
            }, "coaching": {}, "team_context": {}})
            continue
        url = forecast_url(float(venue["latitude"]), float(venue["longitude"]))
        raw, headers = fetch_bytes(url)
        payload = json.loads(raw.decode("utf-8"))
        selected = hourly_at_kickoff(payload, game["kickoff"])
        envelope = build_envelope(
            capture_id=f"open-meteo-{game['game_id']}-{stamp}", capture_intent="WEATHER_FORECAST",
            provider="Open-Meteo", endpoint=url, observed_at=observed_at, effective_at=game["kickoff"],
            as_of_semantics="Forecast response observed before kickoff; provider run initialization is not exposed by this endpoint.",
            payload=payload, release_identifier=headers.get("etag") or headers.get("last_modified"),
            revision_identifier=None, revision_metadata_status="NOT_EXPOSED_BY_PROVIDER",
        )
        envelope_path = capture_dir / f"{game['game_id']}.source-envelope.json"
        first_write_json(envelope_path, envelope)
        source_refs.append({
            "source_id": f"open-meteo:{game['game_id']}:{stamp}", "source_type": "PROVIDER_RESPONSE",
            "endpoint": url, "observed_at": observed_at, "effective_at": game["kickoff"],
            "release_identifier": envelope.get("release_identifier"), "revision_identifier": None,
            "payload_sha256": envelope["payload_sha256"], "as_of_semantics": envelope["as_of_semantics"],
        })
        context_games.append({**game, "environment": {
            "forecast_observed_at": observed_at, "forecast_run_at": None,
            "forecast_run_metadata_status": "NOT_EXPOSED_BY_PROVIDER", **selected,
            "roof": game.get("roof"), "surface": game.get("surface"),
        }, "coaching": {}, "team_context": {}})
    context = build_context(season=season, week=week, observed_at=observed_at, games=context_games, sources=source_refs)
    first_write_json(capture_dir / "context-evidence.json", context)
    return capture_dir / "context-evidence.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="data/research/context/weather")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args(argv)
    if args.week is None:
        if args.fixture:
            args.week = 5
        else:
            state = json.loads(fetch_bytes(STATE_URL)[0].decode("utf-8"))
            args.season = int(state.get("season") or args.season)
            args.week = max(1, int(state.get("week") or 1))
    root = Path(args.output_root)
    if not root.is_absolute():
        root = ROOT / root
    path = capture(output_root=root, season=args.season, week=args.week, fixture=args.fixture)
    print(f"PASS weather evidence {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

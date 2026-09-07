#!/usr/bin/env python3
"""Window 2D: point-in-time context foundation.

Assembles game, venue, weather, rest, availability and validated trench-registry
context into one immutable research bundle. Window 2D is intentionally a
foundation, not a predictive model: it defines provenance-safe context surfaces
for later Window 2E research and does not add multipliers, projection deltas,
rank changes or automatic promotion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-window2d-context-foundation-v1"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
UA = "Fantasy-Intelligence-Window2D/1.0"
TEAM_ALIASES = {"JAC": "JAX", "JAX": "JAX", "LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV"}


class ContextError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def compact_timestamp(value: str) -> str:
    return parse_time(value).strftime("%Y%m%dT%H%M%S%fZ")


def normalize_team(value: Any) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def first_write_json(path: Path, payload: Any) -> str:
    encoded = canonical_bytes(payload) + b"\n"
    if path.exists():
        if path.read_bytes() != encoded:
            raise ContextError(f"IMMUTABLE_FIRST_WRITE_COLLISION:{path}")
        return "EXISTS_IDENTICAL"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return "CREATED"


def kickoff_utc(gameday: str, gametime: str) -> str:
    local = datetime.fromisoformat(f"{gameday}T{gametime}").replace(tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(timezone.utc).isoformat()


def parse_schedule_csv(raw: bytes, season: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
        if row.get("season") != str(season) or row.get("game_type") != "REG":
            continue
        try:
            week = int(row.get("week") or 0)
        except ValueError:
            continue
        gameday = row.get("gameday")
        gametime = row.get("gametime")
        if not gameday or not gametime:
            continue
        home = normalize_team(row.get("home_team"))
        away = normalize_team(row.get("away_team"))
        if not home or not away:
            continue
        rows.append({
            "season": int(season),
            "week": week,
            "game_id": str(row.get("game_id") or f"{season}_{week}_{away}_{home}"),
            "home_team": home,
            "away_team": away,
            "kickoff": kickoff_utc(gameday, gametime),
            "roof": row.get("roof") or None,
            "surface": row.get("surface") or None,
            "stadium_id": row.get("stadium_id") or None,
            "stadium": row.get("stadium") or None,
        })
    return sorted(rows, key=lambda x: (x["kickoff"], x["game_id"]))


def fetch_schedule(season: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    req = Request(GAMES_URL, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    try:
        with urlopen(req, timeout=45) as response:
            if response.status != 200:
                raise ContextError(f"SCHEDULE_HTTP_{response.status}")
            raw = response.read()
        rows = parse_schedule_csv(raw, season)
        if not rows:
            raise ContextError("SCHEDULE_EMPTY")
        return rows, {
            "status": "AVAILABLE_LIVE",
            "endpoint": GAMES_URL,
            "sha256": sha256_bytes(raw),
            "row_count": len(rows),
        }
    except Exception as exc:
        return [], {
            "status": "UNAVAILABLE",
            "endpoint": GAMES_URL,
            "sha256": None,
            "row_count": 0,
            "error": f"{type(exc).__name__}:{exc}",
        }


def discover_latest(root: Path, pattern: str, as_of: str, generated_getter) -> Path | None:
    limit = parse_time(as_of)
    candidates: list[tuple[datetime, Path]] = []
    for path in root.glob(pattern):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            generated = generated_getter(payload)
            if not generated:
                continue
            when = parse_time(str(generated))
            if when <= limit:
                candidates.append((when, path))
        except Exception:
            continue
    return max(candidates, key=lambda x: x[0])[1] if candidates else None


def discover_weather(root: Path, season: int, week: int, as_of: str) -> Path | None:
    base = root / "data/research/context/weather" / str(season) / f"week_{week:02d}"
    if not base.exists():
        return None
    return discover_latest(
        base,
        "*/context-evidence.json",
        as_of,
        lambda p: (p.get("provenance") or {}).get("generated_at"),
    )


def discover_availability(root: Path, season: int, week: int, as_of: str) -> Path | None:
    base = root / "data/research/availability/v2" / str(season) / f"week_{week:02d}"
    if not base.exists():
        return None
    return discover_latest(base, "*/availability-v2.json", as_of, lambda p: p.get("generated_at"))


def load_weather(path: Path | None, *, as_of: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if path is None or not path.exists():
        return {}, {"status": "MISSING", "path": None, "sha256": None}
    payload = json.loads(path.read_text(encoding="utf-8"))
    generated = (payload.get("provenance") or {}).get("generated_at")
    if generated and parse_time(str(generated)) > parse_time(as_of):
        raise ContextError("WEATHER_CONTEXT_OBSERVED_AFTER_AS_OF")
    games: dict[str, dict[str, Any]] = {}
    for raw in payload.get("games") or []:
        gid = str(raw.get("game_id") or "")
        kickoff = raw.get("kickoff")
        home = normalize_team(raw.get("home_team"))
        away = normalize_team(raw.get("away_team"))
        if not gid or not kickoff or not home or not away:
            continue
        games[gid] = {**raw, "game_id": gid, "home_team": home, "away_team": away, "kickoff": parse_time(str(kickoff)).isoformat()}
    return games, {
        "status": "BOUND",
        "path": str(path),
        "sha256": sha256_file(path),
        "generated_at": generated,
        "prediction_cutoff": (payload.get("provenance") or {}).get("prediction_cutoff") or payload.get("cutoff"),
    }


def load_availability(path: Path | None, *, as_of: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if path is None or not path.exists():
        return {}, {"status": "MISSING", "path": None, "sha256": None}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "fie-window2c-availability-v2":
        raise ContextError(f"AVAILABILITY_SCHEMA_MISMATCH:{payload.get('schema')}")
    generated = payload.get("generated_at")
    if generated and parse_time(str(generated)) > parse_time(as_of):
        raise ContextError("AVAILABILITY_OBSERVED_AFTER_AS_OF")
    return payload, {
        "status": "BOUND",
        "path": str(path),
        "sha256": sha256_file(path),
        "generated_at": generated,
        "source_status": payload.get("status"),
    }


def load_trench_registry(path: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if path is None or not path.exists():
        return [], {"status": "MISSING", "path": None, "sha256": None}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "fie-window2b-trench-thin-integration-v1":
        raise ContextError(f"TRENCH_REGISTRY_SCHEMA_MISMATCH:{payload.get('schema')}")
    validated: list[dict[str, Any]] = []
    for row in payload.get("candidate_context") or []:
        enabled = bool(row.get("enabled"))
        if not enabled:
            continue
        if row.get("status") != "RESEARCH_VALIDATED_CANDIDATE" or row.get("allowed_surface") != "research_context_only":
            raise ContextError(f"INVALID_ENABLED_TRENCH_CANDIDATE:{row.get('position')}:{row.get('family')}")
        validated.append({
            "position": row.get("position"),
            "family": row.get("family"),
            "feature_names": list(row.get("feature_names") or []),
            "allowed_surface": "research_context_only",
            "status": "RESEARCH_VALIDATED_CANDIDATE",
        })
    return validated, {
        "status": "BOUND",
        "path": str(path),
        "sha256": sha256_file(path),
        "validated_candidate_count": len(validated),
    }


def rest_context(team: str, current: dict[str, Any], schedule: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    kickoff = parse_time(current["kickoff"])
    # A prior game must have actually reached its scheduled kickoff by as_of; future schedule never counts as rest evidence.
    limit = min(kickoff, parse_time(as_of))
    prior: list[dict[str, Any]] = []
    for game in schedule:
        when = parse_time(game["kickoff"])
        if when >= limit:
            continue
        if team in {game.get("home_team"), game.get("away_team")}:
            prior.append(game)
    if not prior:
        return {
            "status": "NO_PRIOR_REGULAR_SEASON_GAME",
            "previous_game_id": None,
            "previous_kickoff": None,
            "days_rest": None,
            "rest_class": None,
        }
    previous = max(prior, key=lambda row: parse_time(row["kickoff"]))
    days = (kickoff - parse_time(previous["kickoff"])).total_seconds() / 86400.0
    if days < 6.5:
        klass = "SHORT_REST"
    elif days > 8.5:
        klass = "EXTENDED_REST"
    else:
        klass = "NORMAL_REST"
    return {
        "status": "AVAILABLE_DESCRIPTIVE_ONLY",
        "previous_game_id": previous["game_id"],
        "previous_kickoff": previous["kickoff"],
        "days_rest": days,
        "rest_class": klass,
    }


def safe_environment(raw: dict[str, Any] | None, *, kickoff: str, as_of: str) -> dict[str, Any]:
    if not raw:
        return {
            "status": "MISSING",
            "forecast_observed_at": None,
            "forecast_effective_at": None,
            "temperature_f": None,
            "precipitation_probability": None,
            "wind_mph": None,
            "gust_mph": None,
            "roof": None,
            "surface": None,
            "stadium_id": None,
            "stadium": None,
        }
    env = raw.get("environment") or {}
    observed = env.get("forecast_observed_at")
    effective = env.get("forecast_effective_at")
    valid = True
    if observed:
        valid = parse_time(str(observed)) <= min(parse_time(kickoff), parse_time(as_of))
    if not valid:
        return {
            "status": "REJECTED_POST_CUTOFF_WEATHER",
            "forecast_observed_at": observed,
            "forecast_effective_at": effective,
            "temperature_f": None,
            "precipitation_probability": None,
            "wind_mph": None,
            "gust_mph": None,
            "roof": env.get("roof") or raw.get("roof"),
            "surface": env.get("surface") or raw.get("surface"),
            "stadium_id": raw.get("stadium_id"),
            "stadium": raw.get("stadium"),
        }
    values_present = any(env.get(key) is not None for key in ("temperature_f", "precipitation_probability", "wind_mph", "gust_mph"))
    return {
        "status": "AVAILABLE_DESCRIPTIVE_ONLY" if values_present else "MISSING_FORECAST_VALUES",
        "forecast_observed_at": observed,
        "forecast_effective_at": effective,
        "forecast_run_at": env.get("forecast_run_at"),
        "forecast_run_metadata_status": env.get("forecast_run_metadata_status"),
        "temperature_f": env.get("temperature_f"),
        "precipitation_probability": env.get("precipitation_probability"),
        "wind_mph": env.get("wind_mph"),
        "gust_mph": env.get("gust_mph"),
        "roof": env.get("roof") or raw.get("roof"),
        "surface": env.get("surface") or raw.get("surface"),
        "stadium_id": raw.get("stadium_id"),
        "stadium": raw.get("stadium"),
    }


def recursive_contains_key(value: Any, tokens: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            lower = str(key).lower()
            if any(token in lower for token in tokens):
                return True
            if recursive_contains_key(child, tokens):
                return True
    elif isinstance(value, list):
        return any(recursive_contains_key(child, tokens) for child in value)
    return False


def build_context_foundation(
    *,
    season: int,
    week: int,
    as_of: str,
    target_games: list[dict[str, Any]],
    schedule_history: list[dict[str, Any]],
    schedule_binding: dict[str, Any],
    weather_games: dict[str, dict[str, Any]],
    weather_binding: dict[str, Any],
    availability: dict[str, Any],
    availability_binding: dict[str, Any],
    trench_candidates: list[dict[str, Any]],
    trench_binding: dict[str, Any],
) -> dict[str, Any]:
    as_of = parse_time(as_of).isoformat()
    team_availability = availability.get("team_summary") or {}
    player_availability = availability.get("players") or []

    games_out: list[dict[str, Any]] = []
    teams_out: list[dict[str, Any]] = []
    team_keys: set[str] = set()

    for game in sorted(target_games, key=lambda row: (row["kickoff"], row["game_id"])):
        kickoff = parse_time(str(game["kickoff"])).isoformat()
        home = normalize_team(game["home_team"])
        away = normalize_team(game["away_team"])
        if not home or not away or home == away:
            raise ContextError(f"INVALID_GAME_TEAMS:{game.get('game_id')}")
        weather_raw = weather_games.get(str(game["game_id"]))
        environment = safe_environment(weather_raw, kickoff=kickoff, as_of=as_of)
        venue = {
            "roof": environment.get("roof") if environment.get("roof") is not None else game.get("roof"),
            "surface": environment.get("surface") if environment.get("surface") is not None else game.get("surface"),
            "stadium_id": environment.get("stadium_id") if environment.get("stadium_id") is not None else game.get("stadium_id"),
            "stadium": environment.get("stadium") if environment.get("stadium") is not None else game.get("stadium"),
        }
        games_out.append({
            "game_id": game["game_id"],
            "season": int(season),
            "week": int(week),
            "kickoff": kickoff,
            "home_team": home,
            "away_team": away,
            "venue": venue,
            "weather": environment,
            "neutral_site": None,
            "predictive_multiplier": None,
        })
        for team, opponent, site in ((home, away, "HOME"), (away, home, "AWAY")):
            if team in team_keys:
                raise ContextError(f"TEAM_MULTIPLE_GAMES_IN_WEEK:{team}")
            team_keys.add(team)
            teams_out.append({
                "team": team,
                "game_id": game["game_id"],
                "kickoff": kickoff,
                "opponent": opponent,
                "site": site,
                "rest": rest_context(team, game, schedule_history, as_of),
                "availability": team_availability.get(team) or {"status": "MISSING"},
                "travel": {
                    "status": "NOT_BOUND_V1",
                    "distance_miles": None,
                    "timezone_shift_hours": None,
                    "reason": "Window 2D does not fabricate travel coordinates or neutral-site routing",
                },
                "coaching": {
                    "status": "NOT_BOUND_V1",
                    "head_coach": None,
                    "offensive_coordinator": None,
                    "defensive_coordinator": None,
                    "reason": "point-in-time coaching source not yet governed; predictive testing belongs to Window 2E",
                },
                "context_multiplier": None,
            })

    players_out: list[dict[str, Any]] = []
    for row in player_availability:
        if row.get("team") not in team_keys:
            continue
        players_out.append({
            "sleeper_id": row.get("sleeper_id"),
            "full_name": row.get("full_name"),
            "team": row.get("team"),
            "position_model": row.get("position_model"),
            "game_id": row.get("game_id"),
            "kickoff": row.get("kickoff"),
            "availability_state": row.get("availability_state"),
            "availability_evidence_class": row.get("evidence_class"),
            "confirmed_unavailable": row.get("confirmed_unavailable"),
            "uncertain_availability": row.get("uncertain_availability"),
        })

    missing_dependencies: list[str] = []
    if availability_binding.get("status") != "BOUND":
        missing_dependencies.append("availability_v2")
    if weather_binding.get("status") != "BOUND":
        missing_dependencies.append("weather")
    if trench_binding.get("status") != "BOUND":
        missing_dependencies.append("window2b_thin_integration")
    if schedule_binding.get("status") not in {"AVAILABLE_LIVE", "FIXTURE", "FIXTURE_OR_CALLER_BOUND", "BOUND"}:
        missing_dependencies.append("schedule_history")
    if not games_out:
        overall_status = "BLOCKED_TARGET_WEEK_SCHEDULE_UNAVAILABLE"
    elif missing_dependencies:
        overall_status = "PARTIAL_RESEARCH_ONLY"
    else:
        overall_status = "READY_RESEARCH_ONLY"

    payload = {
        "schema": SCHEMA,
        "schema_version": 1,
        "generated_at": as_of,
        "research_only": True,
        "production_model": "M9",
        "season": int(season),
        "week": int(week),
        "status": overall_status,
        "missing_dependencies": missing_dependencies,
        "point_in_time": True,
        "target_week_realised_stats_used": False,
        "predictive_weighting_authorized": False,
        "automatic_model_promotion": False,
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "waiver_values_changed": False,
        "adp_used_as_football_feature": False,
        "source_bindings": {
            "schedule_history": schedule_binding,
            "weather": weather_binding,
            "availability_v2": availability_binding,
            "trench_thin_integration": trench_binding,
        },
        "feature_families": {
            "game_identity": {"status": "BOUND" if games_out else "MISSING", "predictive_weight": None},
            "venue": {"status": "BOUND_DESCRIPTIVE_ONLY" if games_out else "MISSING", "predictive_weight": None},
            "weather": {"status": weather_binding.get("status"), "predictive_weight": None},
            "rest": {"status": schedule_binding.get("status"), "predictive_weight": None},
            "availability_v2": {"status": availability_binding.get("status"), "predictive_weight": None},
            "trench": {
                "status": trench_binding.get("status"),
                "validated_only": True,
                "predictive_weight": None,
                "validated_candidate_count": len(trench_candidates),
                "validated_candidates": trench_candidates,
            },
            "travel": {"status": "NOT_BOUND_V1", "predictive_weight": None},
            "coaching": {"status": "NOT_BOUND_V1", "predictive_weight": None},
        },
        "context": {
            "games": games_out,
            "teams": sorted(teams_out, key=lambda row: row["team"]),
            "players": sorted(players_out, key=lambda row: (row["team"], row.get("position_model") or "", row.get("sleeper_id") or "")),
        },
        "governance": {
            "allowed_surface": "research_context_only",
            "context_effects_require_window2e_validation": True,
            "market_adp_excluded": True,
            "no_zero_imputation": True,
            "missing_context_remains_missing": True,
            "no_context_projection_multiplier": True,
        },
    }

    # Hard fail if any forbidden decision/effect surface sneaks into the assembled context.
    if recursive_contains_key(payload.get("context"), ("fantasy_points", "projection_delta", "rank_delta", "waiver_value", "adp", "market_value")):
        raise ContextError("FORBIDDEN_PROJECTION_RANK_WAIVER_OR_MARKET_FIELD_IN_CONTEXT")
    return payload


def target_week_games(
    *,
    season: int,
    week: int,
    schedule: list[dict[str, Any]],
    weather_games: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [row for row in schedule if int(row.get("season") or season) == season and int(row.get("week") or 0) == week]
    if rows:
        return rows
    # Fail-soft fallback: weather evidence carries the governed current-week schedule identity.
    out: list[dict[str, Any]] = []
    for raw in weather_games.values():
        out.append({
            "season": season,
            "week": week,
            "game_id": raw["game_id"],
            "home_team": raw["home_team"],
            "away_team": raw["away_team"],
            "kickoff": raw["kickoff"],
            "roof": raw.get("roof") or (raw.get("environment") or {}).get("roof"),
            "surface": raw.get("surface") or (raw.get("environment") or {}).get("surface"),
            "stadium_id": raw.get("stadium_id"),
            "stadium": raw.get("stadium"),
        })
    return sorted(out, key=lambda row: (row["kickoff"], row["game_id"]))


def run(
    *,
    root: Path,
    season: int,
    week: int,
    as_of: str,
    availability_path: Path | None = None,
    weather_path: Path | None = None,
    trench_path: Path | None = None,
    schedule_rows: list[dict[str, Any]] | None = None,
    schedule_binding: dict[str, Any] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    as_of = parse_time(as_of).isoformat()
    weather_path = weather_path or discover_weather(root, season, week, as_of)
    availability_path = availability_path or discover_availability(root, season, week, as_of)
    trench_path = trench_path or (root / "data/research/evaluation/2026/trench/thin-integration-v1.json")

    weather_games, weather_binding = load_weather(weather_path, as_of=as_of)
    availability, availability_binding = load_availability(availability_path, as_of=as_of)
    trench_candidates, trench_binding = load_trench_registry(trench_path if trench_path.exists() else None)

    if schedule_rows is None:
        schedule_rows, fetched_binding = fetch_schedule(season)
        schedule_binding = fetched_binding
    else:
        schedule_binding = schedule_binding or {"status": "FIXTURE_OR_CALLER_BOUND", "row_count": len(schedule_rows)}

    games = target_week_games(season=season, week=week, schedule=schedule_rows, weather_games=weather_games)
    payload = build_context_foundation(
        season=season,
        week=week,
        as_of=as_of,
        target_games=games,
        schedule_history=schedule_rows,
        schedule_binding=schedule_binding,
        weather_games=weather_games,
        weather_binding=weather_binding,
        availability=availability,
        availability_binding=availability_binding,
        trench_candidates=trench_candidates,
        trench_binding=trench_binding,
    )

    output_root = output_root or (root / "data/research/context/foundation")
    stamp = compact_timestamp(as_of)
    out_dir = output_root / str(season) / f"week_{week:02d}" / stamp
    path = out_dir / "context-foundation-v1.json"
    write_status = first_write_json(path, payload)
    return {
        "status": payload.get("status"),
        "context_foundation": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
        "write": write_status,
        "games": len(payload["context"]["games"]),
        "teams": len(payload["context"]["teams"]),
        "players": len(payload["context"]["players"]),
        "validated_trench_candidates": len(trench_candidates),
        "weather_status": weather_binding.get("status"),
        "availability_status": availability_binding.get("status"),
        "schedule_status": schedule_binding.get("status"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIE Window 2D Context Foundation")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--availability-path", default=None)
    parser.add_argument("--weather-path", default=None)
    parser.add_argument("--trench-path", default=None)
    parser.add_argument("--output-root", default="data/research/context/foundation")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    def resolve(value: str | None) -> Path | None:
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else root / path

    out = Path(args.output_root)
    if not out.is_absolute():
        out = root / out
    result = run(
        root=root,
        season=args.season,
        week=args.week,
        as_of=args.as_of or utc_now(),
        availability_path=resolve(args.availability_path),
        weather_path=resolve(args.weather_path),
        trench_path=resolve(args.trench_path),
        output_root=out,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

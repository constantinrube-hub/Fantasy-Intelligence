#!/usr/bin/env python3
"""Window 2A: Trench Evidence + Feature Owner.

This module establishes one research-only owner for public offensive-line and
front-seven team context. It intentionally does not change M9, canonical player
rankings, runtime projections, waiver decisions, or app output.

The owner uses nflverse/nflfastR play-by-play as raw evidence and derives only
team-level, reproducible proxies. These are not isolated player grades: QB play,
RB decision-making, scheme, game state, and opponent quality can all contribute.
Window 2B is responsible for chronological predictive validation and any later
thin integration.

Leakage contract:
* a target-week feature snapshot may consume only regular-season plays with
  week < target_week;
* target-week realised plays are never admitted even if the downloaded season
  file already contains them;
* missing measurements remain missing; no trench value is zero-imputed;
* prospective READY snapshots are immutable first-write evidence;
* blocked status files are mutable so unavailable public data can recover later.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-window2a-trench-evidence-v1"
OWNER_SCHEMA = "fie-trench-feature-owner-v1"
PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv"
UA = "Fantasy-Intelligence-Window2A/1.0"
DEFAULT_MIN_TEAMS = 28

OFFENSE_CORE = (
    ("sack_rate_allowed", -1.0),
    ("rush_epa_per_attempt", +1.0),
    ("rush_success_rate", +1.0),
    ("stuff_rate_allowed", -1.0),
)
OFFENSE_OPTIONAL = (("qb_hit_rate_allowed", -1.0),)
DEFENSE_CORE = (
    ("sack_rate_generated", +1.0),
    ("rush_epa_allowed_per_attempt", -1.0),
    ("rush_success_rate_allowed", -1.0),
    ("stuff_rate_forced", +1.0),
)
DEFENSE_OPTIONAL = (("qb_hit_rate_generated", +1.0),)


class EvidenceError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _collision_view(value: Any) -> Any:
    """Remove only capture-time volatility for idempotent first-write checks."""
    x = copy.deepcopy(value)
    if isinstance(x, dict):
        x.pop("generated_at", None)
        source = x.get("source")
        if isinstance(source, dict):
            source.pop("captured_at", None)
    return x


def first_write_json(path: Path, value: Any) -> str:
    """Write immutable evidence once; identical reruns are harmless."""
    if path.exists():
        existing = read_json(path)
        if canonical_json(_collision_view(existing)) == canonical_json(_collision_view(value)):
            return "identical"
        raise EvidenceError(f"FIRST_WRITE_COLLISION:{path}")
    atomic_json(path, value)
    return "written"


def finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def as_int(value: Any) -> int | None:
    x = finite(value)
    return int(x) if x is not None else None


def flag(value: Any) -> bool:
    x = finite(value)
    if x is not None:
        return x == 1.0
    return str(value or "").strip().lower() in {"true", "t", "yes", "y"}


def safe_rate(numerator: float | int | None, denominator: float | int | None) -> float | None:
    n = finite(numerator)
    d = finite(denominator)
    if n is None or d is None or d <= 0:
        return None
    return float(n / d)


def normalize_team(value: Any) -> str:
    team = str(value or "").strip().upper()
    aliases = {"JAX": "JAX", "JAC": "JAX", "LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV"}
    return aliases.get(team, team)


def regular_season(value: Any) -> bool:
    v = str(value or "REG").strip().upper().replace("_", "")
    return v in {"REG", "REGULAR", "REGULARSEASON"}


def empty_side() -> dict[str, Any]:
    return {
        "weeks": set(),
        "pass_dropbacks": 0,
        "sacks": 0,
        "qb_hits": 0,
        "qb_hit_observed_passes": 0,
        "designed_rushes": 0,
        "rush_epa_sum": 0.0,
        "rush_epa_observed": 0,
        "rush_successes": 0,
        "rush_success_observed": 0,
        "stuffed_rushes": 0,
        "rush_yards_observed": 0,
    }


def _accumulate_pass(side: dict[str, Any], week: int, row: dict[str, Any], has_qb_hit: bool) -> None:
    side["weeks"].add(week)
    side["pass_dropbacks"] += 1
    if flag(row.get("sack")):
        side["sacks"] += 1
    if has_qb_hit:
        q = finite(row.get("qb_hit"))
        if q is not None:
            side["qb_hit_observed_passes"] += 1
            if q == 1.0:
                side["qb_hits"] += 1


def _accumulate_rush(side: dict[str, Any], week: int, row: dict[str, Any]) -> None:
    side["weeks"].add(week)
    side["designed_rushes"] += 1
    epa = finite(row.get("epa"))
    if epa is not None:
        side["rush_epa_sum"] += epa
        side["rush_epa_observed"] += 1
    success = finite(row.get("success"))
    if success is not None:
        side["rush_success_observed"] += 1
        if success == 1.0:
            side["rush_successes"] += 1
    yards = finite(row.get("yards_gained"))
    if yards is not None:
        side["rush_yards_observed"] += 1
        if yards <= 0:
            side["stuffed_rushes"] += 1


def extract_team_week_evidence(path: Path, season: int) -> dict[int, dict[str, dict[str, Any]]]:
    """Stream one nflfastR CSV into team/week offense+defense raw evidence."""
    weeks: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {"week", "posteam", "defteam", "pass_attempt", "rush_attempt"}
        missing = sorted(required - fields)
        if missing:
            raise EvidenceError("PBP_REQUIRED_COLUMNS_MISSING:" + ",".join(missing))
        has_qb_hit = "qb_hit" in fields
        for row in reader:
            if "season_type" in fields and not regular_season(row.get("season_type")):
                continue
            if "season" in fields:
                s = as_int(row.get("season"))
                if s is not None and s != int(season):
                    continue
            week = as_int(row.get("week"))
            if week is None or week < 1:
                continue
            if flag(row.get("no_play")):
                continue
            off = normalize_team(row.get("posteam"))
            deff = normalize_team(row.get("defteam"))
            if not off or not deff or off == deff:
                continue
            bucket = weeks[week]
            if off not in bucket:
                bucket[off] = {"offense": empty_side(), "defense": empty_side()}
            if deff not in bucket:
                bucket[deff] = {"offense": empty_side(), "defense": empty_side()}

            is_pass = flag(row.get("pass_attempt")) and not flag(row.get("qb_spike"))
            is_designed_rush = (
                flag(row.get("rush_attempt"))
                and not flag(row.get("qb_scramble"))
                and not flag(row.get("qb_kneel"))
            )
            if is_pass:
                _accumulate_pass(bucket[off]["offense"], week, row, has_qb_hit)
                _accumulate_pass(bucket[deff]["defense"], week, row, has_qb_hit)
            if is_designed_rush:
                _accumulate_rush(bucket[off]["offense"], week, row)
                _accumulate_rush(bucket[deff]["defense"], week, row)
    return dict(weeks)


def merge_side(target: dict[str, Any], source: dict[str, Any]) -> None:
    target["weeks"].update(source.get("weeks") or set())
    for key in (
        "pass_dropbacks", "sacks", "qb_hits", "qb_hit_observed_passes", "designed_rushes",
        "rush_epa_sum", "rush_epa_observed", "rush_successes", "rush_success_observed",
        "stuffed_rushes", "rush_yards_observed",
    ):
        target[key] += source.get(key, 0)


def cumulative_before(team_week: dict[int, dict[str, dict[str, Any]]], target_week: int) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for week in sorted(team_week):
        if int(week) >= int(target_week):
            continue
        for team, sides in team_week[week].items():
            if team not in out:
                out[team] = {"offense": empty_side(), "defense": empty_side()}
            merge_side(out[team]["offense"], sides["offense"])
            merge_side(out[team]["defense"], sides["defense"])
    return out


def side_rates(side: dict[str, Any], kind: str) -> dict[str, Any]:
    weeks = sorted(int(x) for x in side.get("weeks") or [])
    common = {
        "sample_week_count": len(weeks),
        "sample_weeks": weeks,
        "pass_dropbacks": int(side.get("pass_dropbacks") or 0),
        "designed_rushes": int(side.get("designed_rushes") or 0),
    }
    if kind == "offense":
        return {
            **common,
            "sacks_allowed": int(side.get("sacks") or 0),
            "sack_rate_allowed": safe_rate(side.get("sacks"), side.get("pass_dropbacks")),
            "qb_hits_allowed": int(side.get("qb_hits") or 0) if side.get("qb_hit_observed_passes") else None,
            "qb_hit_rate_allowed": safe_rate(side.get("qb_hits"), side.get("qb_hit_observed_passes")),
            "qb_hit_observed_passes": int(side.get("qb_hit_observed_passes") or 0),
            "rush_epa_per_attempt": safe_rate(side.get("rush_epa_sum"), side.get("rush_epa_observed")),
            "rush_epa_observed": int(side.get("rush_epa_observed") or 0),
            "rush_success_rate": safe_rate(side.get("rush_successes"), side.get("rush_success_observed")),
            "rush_success_observed": int(side.get("rush_success_observed") or 0),
            "stuff_rate_allowed": safe_rate(side.get("stuffed_rushes"), side.get("rush_yards_observed")),
            "rush_yards_observed": int(side.get("rush_yards_observed") or 0),
        }
    return {
        **common,
        "sacks_generated": int(side.get("sacks") or 0),
        "sack_rate_generated": safe_rate(side.get("sacks"), side.get("pass_dropbacks")),
        "qb_hits_generated": int(side.get("qb_hits") or 0) if side.get("qb_hit_observed_passes") else None,
        "qb_hit_rate_generated": safe_rate(side.get("qb_hits"), side.get("qb_hit_observed_passes")),
        "qb_hit_observed_passes": int(side.get("qb_hit_observed_passes") or 0),
        "rush_epa_allowed_per_attempt": safe_rate(side.get("rush_epa_sum"), side.get("rush_epa_observed")),
        "rush_epa_observed": int(side.get("rush_epa_observed") or 0),
        "rush_success_rate_allowed": safe_rate(side.get("rush_successes"), side.get("rush_success_observed")),
        "rush_success_observed": int(side.get("rush_success_observed") or 0),
        "stuff_rate_forced": safe_rate(side.get("stuffed_rushes"), side.get("rush_yards_observed")),
        "rush_yards_observed": int(side.get("rush_yards_observed") or 0),
    }


def zscores(values: dict[str, float | None], min_teams: int) -> dict[str, float | None]:
    good = {k: float(v) for k, v in values.items() if finite(v) is not None}
    if len(good) < int(min_teams):
        return {k: None for k in values}
    vals = list(good.values())
    mu = statistics.fmean(vals)
    sd = statistics.pstdev(vals)
    if not math.isfinite(sd) or sd <= 1e-12:
        return {k: None for k in values}
    return {k: ((float(values[k]) - mu) / sd if k in good else None) for k in values}


def apply_owner_features(team_rows: dict[str, dict[str, Any]], min_teams: int = DEFAULT_MIN_TEAMS) -> dict[str, dict[str, Any]]:
    """Apply one owner contract to team rates. Higher proxy values are better."""
    out = copy.deepcopy(team_rows)
    for side_name, core, optional in (
        ("offense", OFFENSE_CORE, OFFENSE_OPTIONAL),
        ("defense", DEFENSE_CORE, DEFENSE_OPTIONAL),
    ):
        all_components = core + optional
        component_z: dict[str, dict[str, float | None]] = {}
        for metric, _direction in all_components:
            vals = {team: finite((row.get(side_name) or {}).get(metric)) for team, row in out.items()}
            component_z[metric] = zscores(vals, min_teams=min_teams)

        for team, row in out.items():
            side = row.get(side_name) or {}
            zmap = {metric: component_z[metric].get(team) for metric, _ in all_components}
            side["component_z"] = zmap
            missing_core = [metric for metric, _ in core if zmap.get(metric) is None]
            signed: list[float] = []
            used: list[str] = []
            if not missing_core:
                for metric, direction in all_components:
                    z = finite(zmap.get(metric))
                    if z is not None:
                        signed.append(direction * z)
                        used.append(metric)
            proxy = statistics.fmean(signed) if signed else None
            side["research_proxy_v1"] = float(proxy) if proxy is not None and math.isfinite(proxy) else None
            side["proxy_components_used"] = used
            side["proxy_missing_core_components"] = missing_core
            side["proxy_status"] = "READY_RESEARCH_ONLY" if side["research_proxy_v1"] is not None else "INSUFFICIENT_COMPONENT_EVIDENCE"
            row[side_name] = side
    return out


def build_snapshot(
    team_week: dict[int, dict[str, dict[str, Any]]],
    *, season: int,
    target_week: int,
    source: dict[str, Any],
    min_teams: int = DEFAULT_MIN_TEAMS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base = {
        "schema": SCHEMA,
        "schema_version": 1,
        "generated_at": generated_at or utc_now(),
        "season": int(season),
        "target_week": int(target_week),
        "through_week": int(target_week) - 1,
        "target_week_realised_stats_excluded": True,
        "research_only": True,
        "production_model": "M9",
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "adp_used_as_football_feature": False,
        "source": source,
        "feature_owner": {
            "schema": OWNER_SCHEMA,
            "owner_module": "research/window2a_trench_evidence.py",
            "input_grain": "nflfastR play-by-play",
            "output_grain": "NFL team x target week",
            "proxy_direction": "higher_is_better",
            "production_validated": False,
            "validation_owner": "Window 2B",
            "offense_core_components": [m for m, _ in OFFENSE_CORE],
            "offense_optional_components": [m for m, _ in OFFENSE_OPTIONAL],
            "defense_core_components": [m for m, _ in DEFENSE_CORE],
            "defense_optional_components": [m for m, _ in DEFENSE_OPTIONAL],
            "standardization": "cross-team population z-score on cumulative prior-week rates",
            "proxy_combination": "equal mean of direction-adjusted available z-scores after all core components exist",
            "confounding_warning": "team trench proxy; not an isolated offensive-line or defender grade",
        },
    }
    if int(target_week) <= 1:
        return {**base, "status": "BLOCKED_INSUFFICIENT_PRIOR_WEEK_EVIDENCE", "team_count": 0, "teams": {}}

    cumulative = cumulative_before(team_week, int(target_week))
    team_rows: dict[str, dict[str, Any]] = {}
    for team, sides in sorted(cumulative.items()):
        team_rows[team] = {
            "team": team,
            "offense": side_rates(sides["offense"], "offense"),
            "defense": side_rates(sides["defense"], "defense"),
        }
    team_count = len(team_rows)
    if team_count < int(min_teams):
        return {
            **base,
            "status": "BLOCKED_INSUFFICIENT_TEAM_COVERAGE",
            "minimum_team_count": int(min_teams),
            "team_count": team_count,
            "teams": team_rows,
        }
    owned = apply_owner_features(team_rows, min_teams=int(min_teams))
    max_input_week = max((w for w in team_week if int(w) < int(target_week)), default=None)
    return {
        **base,
        "status": "READY_RESEARCH_ONLY",
        "minimum_team_count": int(min_teams),
        "team_count": team_count,
        "max_input_week": int(max_input_week) if max_input_week is not None else None,
        "teams": owned,
    }


def download_pbp(season: int, cache_dir: Path, url_template: str = PBP_URL) -> tuple[Path | None, dict[str, Any]]:
    url = url_template.format(season=int(season))
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"play_by_play_{int(season)}.csv"
    if path.exists() and path.stat().st_size > 1000:
        return path, {
            "name": "nflverse_pbp",
            "url": url,
            "season": int(season),
            "status": "AVAILABLE_CACHE",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "captured_at": utc_now(),
        }
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            with tempfile.NamedTemporaryFile(delete=False, dir=str(cache_dir), suffix=".tmp") as tmp:
                shutil.copyfileobj(response, tmp)
                tmp_path = Path(tmp.name)
        if tmp_path.stat().st_size <= 1000:
            tmp_path.unlink(missing_ok=True)
            raise EvidenceError("PBP_DOWNLOAD_TOO_SMALL")
        tmp_path.replace(path)
        return path, {
            "name": "nflverse_pbp",
            "url": url,
            "season": int(season),
            "status": "AVAILABLE_LIVE",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "captured_at": utc_now(),
        }
    except Exception as exc:
        return None, {
            "name": "nflverse_pbp",
            "url": url,
            "season": int(season),
            "status": "UNAVAILABLE",
            "sha256": None,
            "bytes": None,
            "captured_at": utc_now(),
            "error": f"{type(exc).__name__}:{exc}",
        }


def sleeper_target_week() -> tuple[int, int]:
    req = urllib.request.Request("https://api.sleeper.app/v1/state/nfl", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        state = json.loads(response.read().decode("utf-8"))
    season = int(state.get("season") or datetime.now(timezone.utc).year)
    week = int(state.get("week") or 1)
    season_type = str(state.get("season_type") or "").lower()
    if season_type in {"pre", "preseason"}:
        week = 1
    return season, week


def source_blocker(*, season: int, target_week: int, source: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "schema_version": 1,
        "generated_at": utc_now(),
        "season": int(season),
        "target_week": int(target_week),
        "through_week": int(target_week) - 1,
        "target_week_realised_stats_excluded": True,
        "research_only": True,
        "production_model": "M9",
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "adp_used_as_football_feature": False,
        "status": status,
        "source": source,
        "feature_owner": {"schema": OWNER_SCHEMA, "owner_module": "research/window2a_trench_evidence.py", "production_validated": False, "validation_owner": "Window 2B"},
        "team_count": 0,
        "teams": {},
    }


def build_live_prospective(
    *, root: Path, season: int | None, target_week: int | None, cache_dir: Path, min_teams: int, url_template: str = PBP_URL
) -> tuple[dict[str, Any], Path | None, str | None]:
    if season is None or target_week is None:
        live_season, live_week = sleeper_target_week()
        season = live_season if season is None else season
        target_week = live_week if target_week is None else target_week
    season = int(season); target_week = int(target_week)
    base_dir = root / "data" / "research" / "trench" / str(season) / "prospective" / f"week_{target_week:02d}"
    status_path = base_dir / "status.json"
    canonical_path = base_dir / "trench-evidence-v1.json"

    if target_week <= 1:
        source = {"name": "nflverse_pbp", "season": season, "status": "NOT_NEEDED_NO_PRIOR_WEEK", "captured_at": utc_now()}
        payload = source_blocker(season=season, target_week=target_week, source=source, status="BLOCKED_INSUFFICIENT_PRIOR_WEEK_EVIDENCE")
        atomic_json(status_path, payload)
        return payload, None, "blocked"

    pbp_path, source = download_pbp(season, cache_dir=cache_dir, url_template=url_template)
    if pbp_path is None:
        payload = source_blocker(season=season, target_week=target_week, source=source, status="BLOCKED_SOURCE_UNAVAILABLE")
        atomic_json(status_path, payload)
        return payload, None, "blocked"

    try:
        team_week = extract_team_week_evidence(pbp_path, season)
        payload = build_snapshot(team_week, season=season, target_week=target_week, source=source, min_teams=min_teams)
    except Exception as exc:
        payload = source_blocker(season=season, target_week=target_week, source=source, status=f"BLOCKED_SOURCE_PARSE:{type(exc).__name__}:{exc}")
        atomic_json(status_path, payload)
        return payload, None, "blocked"

    atomic_json(status_path, {k: v for k, v in payload.items() if k != "teams"} | {"canonical_path": str(canonical_path.relative_to(root)) if payload.get("status") == "READY_RESEARCH_ONLY" else None})
    if payload.get("status") != "READY_RESEARCH_ONLY":
        return payload, None, "blocked"
    disposition = first_write_json(canonical_path, payload)
    return payload, canonical_path, disposition


def historical_season_payload(*, season: int, team_week: dict[int, dict[str, dict[str, Any]]], source: dict[str, Any], min_teams: int) -> dict[str, Any]:
    regular_weeks = sorted(int(w) for w in team_week if int(w) >= 1)
    max_week = max(regular_weeks, default=0)
    snapshots = []
    for target_week in range(2, max_week + 1):
        snap = build_snapshot(team_week, season=season, target_week=target_week, source=source, min_teams=min_teams, generated_at="HISTORICAL_DETERMINISTIC")
        snapshots.append({
            "target_week": target_week,
            "status": snap.get("status"),
            "through_week": snap.get("through_week"),
            "max_input_week": snap.get("max_input_week"),
            "team_count": snap.get("team_count"),
            "teams": snap.get("teams"),
        })
    return {
        "schema": "fie-window2a-trench-history-v1",
        "schema_version": 1,
        "season": int(season),
        "research_only": True,
        "production_model": "M9",
        "target_week_realised_stats_excluded": True,
        "source": {k: v for k, v in source.items() if k != "captured_at"},
        "feature_owner_schema": OWNER_SCHEMA,
        "regular_weeks_available": regular_weeks,
        "snapshots": snapshots,
    }


def build_history(*, root: Path, seasons: Iterable[int], cache_dir: Path, min_teams: int, url_template: str = PBP_URL) -> dict[str, Any]:
    summary = {"schema": "fie-window2a-trench-history-manifest-v1", "generated_at": utc_now(), "research_only": True, "seasons": []}
    out_dir = root / "data" / "research" / "trench" / "historical"
    out_dir.mkdir(parents=True, exist_ok=True)
    for season in sorted({int(x) for x in seasons}):
        pbp_path, source = download_pbp(season, cache_dir=cache_dir, url_template=url_template)
        row = {"season": season, "source_status": source.get("status"), "output": None, "status": None}
        if pbp_path is None:
            row["status"] = "BLOCKED_SOURCE_UNAVAILABLE"
            summary["seasons"].append(row)
            continue
        try:
            team_week = extract_team_week_evidence(pbp_path, season)
            payload = historical_season_payload(season=season, team_week=team_week, source=source, min_teams=min_teams)
            out = out_dir / f"season_{season}-v1.json"
            atomic_json(out, payload)
            row.update({"status": "READY_RESEARCH_ONLY", "output": str(out.relative_to(root)), "snapshot_count": len(payload["snapshots"]), "sha256": sha256_file(out)})
        except Exception as exc:
            row["status"] = f"BLOCKED_SOURCE_PARSE:{type(exc).__name__}:{exc}"
        summary["seasons"].append(row)
    atomic_json(out_dir / "manifest.json", summary)
    return summary


def parse_seasons(value: str) -> list[int]:
    out = []
    for token in str(value or "").replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(token))
    return sorted(set(out))


def main() -> None:
    ap = argparse.ArgumentParser(description="Window 2A trench evidence + feature owner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prospective")
    p.add_argument("--season", type=int)
    p.add_argument("--target-week", type=int)
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--cache-dir", default=".cache/window2a-trench")
    p.add_argument("--min-teams", type=int, default=DEFAULT_MIN_TEAMS)

    h = sub.add_parser("history")
    h.add_argument("--seasons", default="2019-2025")
    h.add_argument("--root", default=str(ROOT))
    h.add_argument("--cache-dir", default=".cache/window2a-trench")
    h.add_argument("--min-teams", type=int, default=DEFAULT_MIN_TEAMS)

    args = ap.parse_args()
    root = Path(args.root).resolve()
    cache = Path(args.cache_dir)
    if not cache.is_absolute():
        cache = root / cache

    if args.cmd == "prospective":
        payload, out, disposition = build_live_prospective(
            root=root, season=args.season, target_week=args.target_week, cache_dir=cache, min_teams=args.min_teams
        )
        print(json.dumps({"status": payload.get("status"), "season": payload.get("season"), "target_week": payload.get("target_week"), "output": str(out.relative_to(root)) if out else None, "disposition": disposition}, indent=2, sort_keys=True))
        return

    seasons = parse_seasons(args.seasons)
    result = build_history(root=root, seasons=seasons, cache_dir=cache, min_teams=args.min_teams)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

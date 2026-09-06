#!/usr/bin/env python3
"""Window 1B: deterministic preseason preview and weekly evaluation evidence.

This module is intentionally research-only. It does not change rankings, runtime
contracts, model weights, promotion state, or ADP/market inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_PREVIEW = "fie-window1b-season-preview-v1"
SCHEMA_WEEKLY_SNAPSHOT = "fie-window1b-weekly-prediction-snapshot-v1"
SCHEMA_WEEKLY_EVALUATION = "fie-window1b-weekly-evaluation-v1"
BESTBALL_FORMATS = {"REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"}
REQUIRED_BASELINE_SOURCES = ("profile", "current_snapshot", "app_manifest", "rankings")


class EvidenceError(RuntimeError):
    """Raised when Window 1B must fail closed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _repo_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidenceError(f"PATH_OUTSIDE_REPO:{relative}") from exc
    return candidate


def verify_source(root: Path, source: dict[str, Any], label: str) -> Path:
    relative = str(source.get("path") or "")
    expected = str(source.get("sha256") or "")
    if not relative or not expected:
        raise EvidenceError(f"MISSING_SOURCE_BINDING:{label}")
    path = _repo_path(root, relative)
    if not path.is_file():
        raise EvidenceError(f"MISSING_SOURCE_FILE:{label}:{relative}")
    actual = sha256_file(path)
    if actual != expected:
        raise EvidenceError(f"BASELINE_SOURCE_DRIFT:{label}:{relative}:{expected}:{actual}")
    return path


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _player_ids(row: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    identity = row.get("player_identity") if isinstance(row.get("player_identity"), dict) else {}
    for value in (
        row.get("sleeper_id"),
        row.get("player_id"),
        row.get("canonical_fie_player_id"),
        identity.get("sleeper_player_id"),
        identity.get("sleeper_id"),
        identity.get("canonical_fie_player_id"),
        identity.get("canonical_player_id"),
    ):
        if value is None:
            continue
        text = str(value).strip()
        if text and text != "0" and text not in ids:
            ids.append(text)
    return ids


def _valid_roster_ids(values: Iterable[Any] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        if value is None:
            continue
        text = str(value).strip()
        if text and text != "0" and text not in result:
            result.append(text)
    return result


def _ranking_index(rankings: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rows = rankings.get("players") if isinstance(rankings.get("players"), list) else rankings.get("rows")
    if not isinstance(rows, list):
        raise EvidenceError("RANKINGS_PLAYERS_MISSING")
    index: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    valid_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        valid_rows.append(row)
        for player_id in _player_ids(row):
            if player_id in index and index[player_id] is not row:
                duplicates.add(player_id)
            else:
                index[player_id] = row
    for player_id in duplicates:
        index.pop(player_id, None)
    return index, valid_rows


def _season_projection(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    value = _numeric(row.get("projection_points"))
    if value is None:
        return None
    scope = str(row.get("projection_scope") or "").upper()
    if "WEEK" in scope:
        return None
    if scope and "SEASON" not in scope:
        return None
    return value


def _sum_season_projection(player_ids: list[str], index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values: list[float] = []
    missing_ids: list[str] = []
    for player_id in player_ids:
        value = _season_projection(index.get(player_id))
        if value is None:
            missing_ids.append(player_id)
        else:
            values.append(value)
    denominator = len(player_ids)
    return {
        "value": float(sum(values)) if values else None,
        "mapped_count": len(values),
        "expected_count": denominator,
        "coverage_rate": (len(values) / denominator) if denominator else None,
        "missing_player_ids": missing_ids,
    }


def _sum_metric(player_ids: list[str], index: dict[str, dict[str, Any]], field: str) -> dict[str, Any]:
    values: list[float] = []
    missing_ids: list[str] = []
    for player_id in player_ids:
        row = index.get(player_id)
        value = _numeric(row.get(field)) if row else None
        if value is None:
            missing_ids.append(player_id)
        else:
            values.append(value)
    total = float(sum(values)) if values else None
    denominator = len(player_ids)
    return {
        "value": total,
        "mapped_count": len(values),
        "expected_count": denominator,
        "coverage_rate": (len(values) / denominator) if denominator else None,
        "missing_player_ids": missing_ids,
    }


def _team_label(roster: dict[str, Any], user_by_id: dict[str, dict[str, Any]]) -> str:
    owner_id = str(roster.get("owner_id") or "")
    user = user_by_id.get(owner_id, {})
    metadata = user.get("metadata") if isinstance(user.get("metadata"), dict) else {}
    for candidate in (metadata.get("team_name"), user.get("display_name"), user.get("username")):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return f"Roster {roster.get('roster_id', '?')}"


def _asset_summary(row: dict[str, Any], catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    player_id = (_player_ids(row) or [None])[0]
    catalog_row = (catalog or {}).get(str(player_id), {}) if player_id is not None else {}
    name = row.get("name") or row.get("player_name") or catalog_row.get("player_name") or catalog_row.get("full_name")
    return {
        "player_id": player_id,
        "player_name": name,
        "position": row.get("position") or row.get("pos") or catalog_row.get("position"),
        "team": row.get("team") or catalog_row.get("team"),
        "season_projection_points": _season_projection(row),
        "raw_projection_points": _numeric(row.get("projection_points")),
        "projection_scope": row.get("projection_scope"),
        "projection_source": row.get("projection_source"),
        "vorp": _numeric(row.get("vorp")),
        "overall_rank": _numeric(row.get("overall_rank")),
        "position_rank": _numeric(row.get("position_rank")),
        "confidence": _numeric(row.get("confidence")),
        "model_selected": row.get("model_selected"),
    }


def _asset_sort_key(row: dict[str, Any]) -> tuple[float, float, float, str]:
    overall = _numeric(row.get("overall_rank"))
    pos_rank = _numeric(row.get("position_rank"))
    vorp = _numeric(row.get("vorp"))
    return (
        -(overall if overall is not None else 10**9),
        -(pos_rank if pos_rank is not None else 10**9),
        vorp if vorp is not None else float("-inf"),
        str(row.get("name") or row.get("player_name") or ""),
    )


def _position_summary(player_ids: list[str], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"projection_points": 0.0, "vorp": 0.0, "mapped": 0})
    for player_id in player_ids:
        row = index.get(player_id)
        if not row:
            continue
        position = str(row.get("position") or row.get("pos") or "UNK")
        projection = _season_projection(row)
        vorp = _numeric(row.get("vorp"))
        if projection is None and vorp is None:
            continue
        grouped[position]["mapped"] += 1
        if projection is not None:
            grouped[position]["projection_points"] += projection
        if vorp is not None:
            grouped[position]["vorp"] += vorp
    return [
        {
            "position": position,
            "mapped_players": values["mapped"],
            "projection_points": values["projection_points"],
            "vorp": values["vorp"],
        }
        for position, values in sorted(grouped.items())
    ]


def _manifest_core(root: Path, manifest: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    entry = manifest.get("core") if isinstance(manifest.get("core"), dict) else None
    if entry is None:
        files = manifest.get("files")
        if not isinstance(files, list):
            raise EvidenceError("APP_MANIFEST_CORE_MISSING")
        core_entries = [item for item in files if isinstance(item, dict) and item.get("name") == "core"]
        if len(core_entries) != 1:
            raise EvidenceError(f"APP_MANIFEST_CORE_COUNT:{len(core_entries)}")
        entry = core_entries[0]
    relative = str(entry.get("path") or "")
    expected = str(entry.get("sha256") or "")
    if not relative or not expected:
        raise EvidenceError("APP_MANIFEST_CORE_BINDING_MISSING")
    path = _repo_path(root, relative)
    if not path.is_file():
        raise EvidenceError(f"APP_CORE_MISSING:{relative}")
    actual = sha256_file(path)
    if actual != expected:
        raise EvidenceError(f"APP_CORE_DRIFT:{relative}:{expected}:{actual}")
    return path, entry


def _league_preview(root: Path, league: dict[str, Any]) -> dict[str, Any]:
    sources = league.get("sources")
    if not isinstance(sources, dict):
        raise EvidenceError(f"LEAGUE_SOURCES_MISSING:{league.get('league_id')}")
    verified_paths: dict[str, Path] = {}
    for name in REQUIRED_BASELINE_SOURCES:
        source = sources.get(name)
        if not isinstance(source, dict):
            raise EvidenceError(f"REQUIRED_SOURCE_MISSING:{league.get('league_id')}:{name}")
        verified_paths[name] = verify_source(root, source, f"{league.get('league_id')}:{name}")

    manifest = read_json(verified_paths["app_manifest"])
    core_path, core_entry = _manifest_core(root, manifest)
    core = read_json(core_path)
    rankings = read_json(verified_paths["rankings"])
    index, ranking_rows = _ranking_index(rankings)

    if str(core.get("league_id")) != str(league.get("league_id")):
        raise EvidenceError(f"APP_CORE_LEAGUE_MISMATCH:{league.get('league_id')}")
    if str(rankings.get("league_id") or league.get("league_id")) != str(league.get("league_id")):
        raise EvidenceError(f"RANKINGS_LEAGUE_MISMATCH:{league.get('league_id')}")

    sleeper = core.get("sleeper") if isinstance(core.get("sleeper"), dict) else {}
    users = sleeper.get("users") if isinstance(sleeper.get("users"), list) else (core.get("users") if isinstance(core.get("users"), list) else [])
    user_by_id = {
        str(user.get("user_id")): user
        for user in users
        if isinstance(user, dict) and user.get("user_id") is not None
    }
    rosters = sleeper.get("rosters") if isinstance(sleeper.get("rosters"), list) else (core.get("rosters") if isinstance(core.get("rosters"), list) else [])
    catalog = core.get("player_catalog") if isinstance(core.get("player_catalog"), dict) else {}
    league_format = str(league.get("format") or core.get("format") or "UNKNOWN")
    best_ball = league_format in BESTBALL_FORMATS

    team_rows: list[dict[str, Any]] = []
    for roster in rosters:
        if not isinstance(roster, dict):
            continue
        roster_ids = _valid_roster_ids(roster.get("players"))
        starter_ids = _valid_roster_ids(roster.get("starters"))
        primary_ids = roster_ids if best_ball else starter_ids

        starter_projection = _sum_season_projection(starter_ids, index)
        roster_projection = _sum_season_projection(roster_ids, index)
        starter_vorp = _sum_metric(starter_ids, index, "vorp")
        roster_vorp = _sum_metric(roster_ids, index, "vorp")
        primary_projection = roster_projection if best_ball else starter_projection

        if primary_projection["expected_count"] == 0 or primary_projection["mapped_count"] == 0:
            status = "INSUFFICIENT_EVIDENCE"
        elif primary_projection["mapped_count"] == primary_projection["expected_count"]:
            status = "READY"
        else:
            status = "PARTIAL"

        mapped_roster_rows = [index[player_id] for player_id in roster_ids if player_id in index]
        top_assets = [
            _asset_summary(row, catalog)
            for row in sorted(mapped_roster_rows, key=_asset_sort_key, reverse=True)[:5]
        ]

        team_rows.append({
            "roster_id": roster.get("roster_id"),
            "owner_id": roster.get("owner_id"),
            "team_name": _team_label(roster, user_by_id),
            "status": status,
            "primary_metric": "roster_projection_sum" if best_ball else "starter_projection_sum",
            "starter_projection": starter_projection,
            "roster_projection": roster_projection,
            "starter_vorp": starter_vorp,
            "roster_vorp": roster_vorp,
            "position_summary": _position_summary(roster_ids, index),
            "top_assets": top_assets,
            "baseline_record": roster.get("settings") if isinstance(roster.get("settings"), dict) else {},
        })

    def rank_key(team: dict[str, Any]) -> tuple[float, float, float, str]:
        primary = team["roster_projection"] if best_ball else team["starter_projection"]
        secondary = team["starter_projection"] if best_ball else team["roster_projection"]
        vorp = team["roster_vorp"] if best_ball else team["starter_vorp"]
        return (
            primary["value"] if primary["value"] is not None else float("-inf"),
            secondary["value"] if secondary["value"] is not None else float("-inf"),
            vorp["value"] if vorp["value"] is not None else float("-inf"),
            str(team.get("roster_id") or ""),
        )

    ranked = sorted(team_rows, key=rank_key, reverse=True)
    next_rank = 1
    for team in ranked:
        primary = team["roster_projection"] if best_ball else team["starter_projection"]
        team["preview_rank"] = next_rank if primary["value"] is not None else None
        if primary["value"] is not None:
            next_rank += 1

    board = sorted(
        [row for row in ranking_rows if _numeric(row.get("overall_rank")) is not None],
        key=lambda row: (
            _numeric(row.get("overall_rank")),
            str(row.get("name") or row.get("player_name") or ""),
        ),
    )

    statuses = [team["status"] for team in ranked]
    if statuses and all(status == "READY" for status in statuses):
        league_status = "READY"
    elif any(status in {"READY", "PARTIAL"} for status in statuses):
        league_status = "READY_WITH_PARTIAL_COVERAGE"
    else:
        league_status = "INSUFFICIENT_EVIDENCE"

    return {
        "league_id": str(league.get("league_id")),
        "league_name": league.get("league_name") or core.get("league_name") or (sleeper.get("league") or {}).get("name"),
        "format": league_format,
        "profile_fingerprint": league.get("profile_fingerprint"),
        "scoring_signature": league.get("scoring_signature"),
        "status": league_status,
        "ranking_semantics": {
            "primary": "season-scope roster projection sum" if best_ball else "season-scope starter projection sum",
            "tie_break_1": "season-scope starter projection sum" if best_ball else "season-scope roster projection sum",
            "tie_break_2": "roster VORP sum" if best_ball else "starter VORP sum",
            "calibrated_win_probability": False,
            "new_model_weighting": False,
        },
        "source_bindings": {
            name: {
                "path": sources[name]["path"],
                "sha256": sources[name]["sha256"],
            }
            for name in REQUIRED_BASELINE_SOURCES
        } | {
            "app_core": {"path": core_entry["path"], "sha256": core_entry["sha256"]}
        },
        "teams": ranked,
        "player_board_top_24": [_asset_summary(row, catalog) for row in board[:24]],
    }


def build_season_preview(root: Path, baseline_path: Path) -> dict[str, Any]:
    baseline = read_json(baseline_path)
    if baseline.get("eligibility") != "PRESEASON_ELIGIBLE":
        raise EvidenceError(f"BASELINE_NOT_PRESEASON_ELIGIBLE:{baseline.get('eligibility')}")
    leagues = baseline.get("leagues")
    if not isinstance(leagues, list) or not leagues:
        raise EvidenceError("BASELINE_LEAGUES_MISSING")

    preview_leagues = [_league_preview(root, league) for league in leagues if isinstance(league, dict)]
    format_counts: dict[str, int] = defaultdict(int)
    status_counts: dict[str, int] = defaultdict(int)
    for league in preview_leagues:
        format_counts[league["format"]] += 1
        status_counts[league["status"]] += 1

    if len(preview_leagues) != int(baseline.get("enabled_league_count") or len(preview_leagues)):
        raise EvidenceError("BASELINE_LEAGUE_COUNT_MISMATCH")

    baseline_relative = str(baseline_path.resolve().relative_to(root.resolve())) if baseline_path.resolve().is_relative_to(root.resolve()) else str(baseline_path)
    return {
        "schema_version": SCHEMA_PREVIEW,
        "namespace": f"fie/{baseline.get('baseline_version', 1)}/2026/window1b/season-preview/v1",
        "season": 2026,
        "generated_at": baseline.get("created_at"),
        "preseason_cutoff": baseline.get("first_regular_season_kickoff"),
        "baseline": {
            "path": baseline_relative,
            "sha256": sha256_file(baseline_path),
            "baseline_version": baseline.get("baseline_version"),
            "eligibility": baseline.get("eligibility"),
        },
        "policy": {
            "research_only": True,
            "production_model": "M9",
            "changes_rankings_or_runtime": False,
            "new_model_weighting": False,
            "market_or_adp_used_as_football_feature": False,
            "missing_evidence_zero_imputed": False,
            "team_rank_is_transparent_projection_aggregation_not_win_probability": True,
        },
        "portfolio": {
            "league_count": len(preview_leagues),
            "format_counts": dict(sorted(format_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "leagues": preview_leagues,
    }


def _fmt(value: Any) -> str:
    number = _numeric(value)
    return "—" if number is None else f"{number:.1f}"


def preview_markdown(preview: dict[str, Any]) -> str:
    lines = [
        "# FIE 2026 Season Preview — Frozen Preseason Baseline",
        "",
        f"Baseline created: `{preview.get('generated_at')}`  ",
        f"Preseason cutoff: `{preview.get('preseason_cutoff')}`  ",
        f"Leagues: **{preview.get('portfolio', {}).get('league_count', 0)}**",
        "",
        "> This is a transparent aggregation of the frozen league-specific canonical M9 ranking outputs. It does not re-weight the football model, use ADP as a football feature, or imply calibrated championship/win probabilities.",
        "",
    ]
    for league in preview.get("leagues", []):
        lines.extend([
            f"## {league.get('league_name') or league.get('league_id')}",
            "",
            f"**Format:** {league.get('format')}  ",
            f"**Status:** {league.get('status')}  ",
            f"**Ranking basis:** {league.get('ranking_semantics', {}).get('primary')}",
            "",
            "| Rank | Team | Primary projection | Starter projection | Roster projection | Starter VORP | Coverage |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ])
        for team in league.get("teams", []):
            primary = team.get("roster_projection") if league.get("format") in BESTBALL_FORMATS else team.get("starter_projection")
            coverage = primary.get("coverage_rate") if isinstance(primary, dict) else None
            coverage_text = "—" if coverage is None else f"{coverage * 100:.0f}%"
            lines.append(
                f"| {team.get('preview_rank') or '—'} | {team.get('team_name')} | {_fmt(primary.get('value') if isinstance(primary, dict) else None)} | "
                f"{_fmt(team.get('starter_projection', {}).get('value'))} | {_fmt(team.get('roster_projection', {}).get('value'))} | "
                f"{_fmt(team.get('starter_vorp', {}).get('value'))} | {coverage_text} |"
            )
        lines.extend(["", "### Canonical player board — top 24", "", "| # | Player | Pos | Team | Season projection | VORP | Overall rank |", "|---:|---|---|---|---:|---:|---:|"])
        for i, player in enumerate(league.get("player_board_top_24", []), 1):
            lines.append(
                f"| {i} | {player.get('player_name') or player.get('player_id') or '—'} | {player.get('position') or '—'} | {player.get('team') or '—'} | "
                f"{_fmt(player.get('season_projection_points'))} | {_fmt(player.get('vorp'))} | {_fmt(player.get('overall_rank'))} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _first_write_json(path: Path, payload: dict[str, Any]) -> str:
    data = canonical_bytes(payload) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
        return "written"
    except FileExistsError:
        existing = path.read_bytes()
        if existing == data:
            return "identical"
        raise EvidenceError(f"FIRST_WRITE_COLLISION:{path}")


def _prediction_rows_from_source(source: Any) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return [row for row in source if isinstance(row, dict)]
    if isinstance(source, dict):
        for key in ("rows", "players", "predictions"):
            if isinstance(source.get(key), list):
                return [row for row in source[key] if isinstance(row, dict)]
    return []


def build_weekly_snapshot(
    current_path: Path,
    prediction_source_path: Path | None,
    cutoff_utc: str,
) -> dict[str, Any]:
    current = read_json(current_path)
    season = int(current.get("season") or 0)
    week = int(current.get("week") or 0)
    league_id = str(current.get("league_id") or "")
    if not season or not week or not league_id:
        raise EvidenceError("CURRENT_SNAPSHOT_IDENTITY_MISSING")
    if current.get("target_week_realised_stats_excluded") is not True:
        raise EvidenceError("TARGET_WEEK_REALIZED_STATS_NOT_EXCLUDED")

    observed_at = current.get("generated_at")
    observed_dt = _parse_dt(observed_at)
    cutoff_dt = _parse_dt(cutoff_utc)
    if observed_dt is None or cutoff_dt is None:
        raise EvidenceError("WEEKLY_TIMING_MISSING")
    if observed_dt >= cutoff_dt:
        raise EvidenceError(f"POST_KICKOFF_PREDICTION_SOURCE:{observed_at}:{cutoff_utc}")

    summary = current.get("summary") if isinstance(current.get("summary"), dict) else {}
    eligible = int(summary.get("weekly_activation_eligible") or 0)
    base = {
        "schema_version": SCHEMA_WEEKLY_SNAPSHOT,
        "namespace": f"fie/{season}/week/{week}/league/{league_id}/prediction-snapshot/v1",
        "season": season,
        "week": week,
        "league_id": league_id,
        "observed_at": observed_at,
        "cutoff_utc": cutoff_utc,
        "source": {"path": str(current_path), "sha256": sha256_file(current_path)},
        "policy": {
            "research_only": True,
            "target_week_realised_stats_excluded": True,
            "changes_rankings_or_runtime": False,
            "missing_evidence_zero_imputed": False,
        },
    }

    if eligible <= 0:
        health = current.get("source_health") if isinstance(current.get("source_health"), dict) else {}
        return base | {
            "status": "BLOCKED_NO_ELIGIBLE_WEEKLY_PREDICTIONS",
            "blocker": {
                "weekly_activation_eligible": eligible,
                "reason": health.get("reason") or summary.get("production_reason") or "no eligible weekly predictions",
            },
            "rows": [],
        }

    if prediction_source_path is None:
        return base | {
            "status": "BLOCKED_PREDICTION_ROWS_NOT_BOUND",
            "blocker": {"weekly_activation_eligible": eligible, "reason": "explicit prediction source required"},
            "rows": [],
        }

    raw = read_json(prediction_source_path)
    rows: list[dict[str, Any]] = []
    for row in _prediction_rows_from_source(raw):
        player_id = None
        for candidate in (row.get("sleeper_id"), row.get("player_id"), row.get("canonical_fie_player_id")):
            if candidate is not None and str(candidate).strip() not in {"", "0"}:
                player_id = str(candidate).strip()
                break
        projection = None
        for key in ("fie_expected_fantasy_points", "fie_projection", "weekly_projection", "projection_points"):
            projection = _numeric(row.get(key))
            if projection is not None:
                break
        if player_id is None or projection is None:
            continue
        if "weekly_activation_eligible" in row and not bool(row.get("weekly_activation_eligible")):
            continue
        rows.append({"player_id": player_id, "projected_points": projection})

    rows.sort(key=lambda row: row["player_id"])
    if not rows:
        return base | {
            "status": "BLOCKED_PREDICTION_ROWS_NOT_RESOLVED",
            "blocker": {"weekly_activation_eligible": eligible, "reason": "bound source had no eligible player/projection rows"},
            "prediction_source": {"path": str(prediction_source_path), "sha256": sha256_file(prediction_source_path)},
            "rows": [],
        }
    return base | {
        "status": "READY",
        "prediction_source": {"path": str(prediction_source_path), "sha256": sha256_file(prediction_source_path)},
        "row_count": len(rows),
        "rows": rows,
    }


def _load_outcome_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    return _prediction_rows_from_source(read_json(path))


def evaluate_weekly(snapshot_path: Path, outcomes_path: Path | None) -> dict[str, Any]:
    snapshot = read_json(snapshot_path)
    base = {
        "schema_version": SCHEMA_WEEKLY_EVALUATION,
        "namespace": str(snapshot.get("namespace") or "") + "/evaluation/v1",
        "season": snapshot.get("season"),
        "week": snapshot.get("week"),
        "league_id": snapshot.get("league_id"),
        "prediction_snapshot": {"path": str(snapshot_path), "sha256": sha256_file(snapshot_path)},
        "policy": {
            "research_only": True,
            "changes_rankings_or_runtime": False,
            "tunes_or_retrains_model": False,
            "missing_outcomes_zero_imputed": False,
        },
    }
    if snapshot.get("status") != "READY":
        return base | {
            "status": "BLOCKED_PREDICTION_SNAPSHOT_NOT_READY",
            "prediction_status": snapshot.get("status"),
        }
    if outcomes_path is None or not outcomes_path.is_file():
        return base | {"status": "PENDING_OUTCOME", "matched_rows": 0}

    outcomes: dict[str, float] = {}
    for row in _load_outcome_rows(outcomes_path):
        player_id = row.get("player_id") or row.get("sleeper_id")
        actual = _numeric(row.get("actual_points"))
        if player_id is not None and actual is not None:
            outcomes[str(player_id)] = actual

    errors: list[float] = []
    abs_errors: list[float] = []
    sq_errors: list[float] = []
    matched: list[dict[str, Any]] = []
    predictions = snapshot.get("rows") if isinstance(snapshot.get("rows"), list) else []
    for row in predictions:
        if not isinstance(row, dict):
            continue
        player_id = str(row.get("player_id") or "")
        predicted = _numeric(row.get("projected_points"))
        actual = outcomes.get(player_id)
        if not player_id or predicted is None or actual is None:
            continue
        error = predicted - actual
        errors.append(error)
        abs_errors.append(abs(error))
        sq_errors.append(error * error)
        matched.append({"player_id": player_id, "projected_points": predicted, "actual_points": actual, "error": error})

    if not matched:
        return base | {
            "status": "PENDING_OUTCOME",
            "outcomes": {"path": str(outcomes_path), "sha256": sha256_file(outcomes_path)},
            "prediction_rows": len(predictions),
            "matched_rows": 0,
        }

    n = len(matched)
    return base | {
        "status": "EVALUATED",
        "outcomes": {"path": str(outcomes_path), "sha256": sha256_file(outcomes_path)},
        "prediction_rows": len(predictions),
        "matched_rows": n,
        "coverage_rate": n / len(predictions) if predictions else None,
        "metrics": {
            "mae": sum(abs_errors) / n,
            "rmse": math.sqrt(sum(sq_errors) / n),
            "mean_bias_projected_minus_actual": sum(errors) / n,
        },
        "rows": matched,
    }


def write_json(path: Path, payload: dict[str, Any], immutable: bool = False) -> str:
    if immutable:
        return _first_write_json(path, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(payload) + b"\n")
    return "written"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    sub = parser.add_subparsers(dest="command", required=True)

    preview = sub.add_parser("season-preview")
    preview.add_argument("--baseline", default="data/research/baselines/2026/baseline-v1.json")
    preview.add_argument("--output-json", default="data/research/evaluation/2026/preseason/season-preview-v1.json")
    preview.add_argument("--output-md", default="data/research/evaluation/2026/preseason/season-preview-v1.md")

    snapshot = sub.add_parser("weekly-snapshot")
    snapshot.add_argument("--current-snapshot", required=True)
    snapshot.add_argument("--prediction-source")
    snapshot.add_argument("--cutoff-utc", required=True)
    snapshot.add_argument("--output", required=True)

    evaluation = sub.add_parser("weekly-evaluate")
    evaluation.add_argument("--snapshot", required=True)
    evaluation.add_argument("--outcomes")
    evaluation.add_argument("--output", required=True)

    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    try:
        if args.command == "season-preview":
            baseline_path = _repo_path(root, args.baseline)
            payload = build_season_preview(root, baseline_path)
            write_json(_repo_path(root, args.output_json), payload)
            md_path = _repo_path(root, args.output_md)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(preview_markdown(payload), encoding="utf-8")
            print(f"Window 1B season preview: READY leagues={len(payload['leagues'])} output={args.output_json}")
        elif args.command == "weekly-snapshot":
            current_path = _repo_path(root, args.current_snapshot)
            prediction_path = _repo_path(root, args.prediction_source) if args.prediction_source else None
            payload = build_weekly_snapshot(current_path, prediction_path, args.cutoff_utc)
            result = write_json(_repo_path(root, args.output), payload, immutable=True)
            print(f"Window 1B weekly snapshot: {payload['status']} first_write={result}")
        elif args.command == "weekly-evaluate":
            snapshot_path = _repo_path(root, args.snapshot)
            outcomes_path = _repo_path(root, args.outcomes) if args.outcomes else None
            payload = evaluate_weekly(snapshot_path, outcomes_path)
            write_json(_repo_path(root, args.output), payload)
            print(f"Window 1B weekly evaluation: {payload['status']}")
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Window 1B fail-closed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

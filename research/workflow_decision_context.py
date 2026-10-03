#!/usr/bin/env python3
"""Operational target identity and coverage, separate from model governance.

Snapshot age/week can block a decision; it must never choose that decision's
target. Automatic targets use the regular-season schedule. Explicit historical
weeks remain available without a provider request.
"""
from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from nfl_schedule_time import NFL_SCHEDULE_ZONE

SCHEDULE_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
UTC = timezone.utc


def default_season(as_of: datetime) -> int:
    """January's regular-season closeout belongs to the preceding NFL season."""
    local = as_of.astimezone(NFL_SCHEDULE_ZONE)
    return local.year - 1 if local.month <= 3 else local.year


def fetch_schedule() -> bytes:
    request = Request(SCHEDULE_URL, headers={"User-Agent": "FIE-Decision-Context/1.0"})
    with urlopen(request, timeout=35) as response:
        return response.read()


def resolve_target(
    *, season: int, week: int | None, as_of: datetime,
    schedule_path: Path | None = None, fetcher: Callable[[], bytes] = fetch_schedule,
) -> dict[str, Any]:
    if as_of.tzinfo is None:
        raise ValueError("TARGET_AS_OF_TIMEZONE_MISSING")
    target = {"season": int(season), "as_of_utc": as_of.astimezone(UTC).isoformat()}
    if week is not None:
        if isinstance(week, bool) or not 1 <= int(week) <= 18:
            raise ValueError("TARGET_REGULAR_WEEK_OUT_OF_RANGE")
        return {**target, "week": int(week), "basis": "EXPLICIT_OPERATOR_WEEK"}
    try:
        raw = schedule_path.read_bytes() if schedule_path else fetcher()
        rows = [row for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
                if row.get("season") == str(season)
                and str(row.get("game_type") or row.get("season_type") or "").upper()
                in {"REG", "REGULAR", "REGULAR_SEASON"}]
        by_week: dict[int, list[dict[str, str]]] = {}
        for row in rows:
            by_week.setdefault(int(row["week"]), []).append(row)
        # Reject historical-only/truncated schedules instead of inventing Week 1
        # or treating a missing future week as the end of the season.
        if set(by_week) != set(range(1, 19)):
            raise ValueError("TARGET_REGULAR_SCHEDULE_INCOMPLETE")
        for candidate in sorted(by_week):
            games = by_week[candidate]
            final_day = max(date.fromisoformat(row["gameday"]) for row in games)
            boundary = datetime.combine(final_day + timedelta(days=1), time(), NFL_SCHEDULE_ZONE)
            if as_of < boundary:
                return {
                    **target, "week": candidate, "basis": "REGULAR_SCHEDULE_CALENDAR",
                    "week_calendar_end_utc": boundary.astimezone(UTC).isoformat(),
                    "schedule_sha256": hashlib.sha256(raw).hexdigest(),
                    "schedule_source": str(schedule_path) if schedule_path else SCHEDULE_URL,
                    "schedule_observed_at": datetime.now(UTC).isoformat(),
                }
            # A late game or stale provider response must not silently advance
            # the week at midnight. Final scores/results are used only to verify
            # the operational boundary, never as forecast features.
            if any(not str(row.get("result") or "").strip()
                   and not (str(row.get("home_score") or "").strip()
                            and str(row.get("away_score") or "").strip())
                   for row in games):
                raise ValueError(f"TARGET_PREVIOUS_WEEK_NOT_FINAL:{candidate}")
        raise ValueError("TARGET_REGULAR_SEASON_COMPLETE_USE_EXPLICIT_WEEK")
    except (KeyError, TypeError, UnicodeError, OSError) as exc:
        raise ValueError(f"TARGET_SCHEDULE_UNAVAILABLE:{type(exc).__name__}") from exc


def input_readiness(
    root: Path, league_id: str, registry_row: dict[str, Any],
    *, season: int, week: int, as_of: datetime,
) -> dict[str, Any]:
    """Read small metadata only; the producer still owns hydration validation."""
    import json

    base = root / "data/research/leagues" / str(league_id)

    def read(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    current_path, profile_path = base / "current/milestone5_current.json", base / "profile.json"
    current, profile, manifest = read(current_path), read(profile_path), read(base / "app/manifest.json")
    generated = current.get("generated_at")
    try:
        stamp = datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
        age = round((as_of - stamp).total_seconds() / 3600, 3) if stamp.tzinfo else None
    except (TypeError, ValueError):
        age = None
    health = current.get("source_health") or {}
    summary = current.get("summary") or {}
    return {
        "target_season": season, "target_week": week,
        "current_season": current.get("season"), "current_week": current.get("week"),
        "current_generated_at": generated, "current_age_hours": age,
        "current_snapshot_sha256": hashlib.sha256(current_path.read_bytes()).hexdigest() if current_path.is_file() else None,
        "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest() if profile_path.is_file() else None,
        "registry_profile_fingerprint": registry_row.get("profile_fingerprint"),
        "profile_fingerprint": profile.get("profile_fingerprint"),
        "current_profile_fingerprint": current.get("profile_fingerprint"),
        "profile_current_match": current.get("profile_current_match"),
        "profile_scoring_signature": profile.get("scoring_signature"),
        "current_scoring_signature": current.get("scoring_signature"),
        "app_profile_fingerprint": manifest.get("profile_fingerprint"),
        "app_scoring_signature": manifest.get("scoring_signature"),
        "weekly_activation_eligible_total": summary.get("weekly_activation_eligible"),
        "waiver_activation_eligible_total": summary.get("waiver_activation_eligible"),
        "source_health_reason": health.get("reason"),
        "source_errors": [{"source": row.get("source"), "error": row.get("error")}
                          for row in health.get("sources") or [] if row.get("ok") is False],
        "metadata_only": True,
    }


def projection_coverage(current: dict[str, Any]) -> dict[str, Any]:
    """Report raw model-position row coverage, not deduplicated player counts."""
    positions: dict[str, dict[str, int]] = {}
    for row in current.get("players") or []:
        if not isinstance(row, dict):
            continue
        position = str(row.get("position_model") or "UNKNOWN")
        counts = positions.setdefault(position, {"rows": 0, "weekly_eligible_rows": 0, "waiver_eligible_rows": 0})
        counts["rows"] += 1
        counts["weekly_eligible_rows"] += bool(row.get("weekly_activation_eligible"))
        counts["waiver_eligible_rows"] += bool(row.get("waiver_activation_eligible"))
    return {"unit": "source_rows_before_identity_deduplication", "by_model_position": dict(sorted(positions.items()))}


def summarize_readiness(reports: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    lineups: Counter[str] = Counter()
    execution: Counter[str] = Counter()
    waivers: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    for report in reports:
        status = str(report.get("status") or "UNKNOWN")
        actions = report.get("action_status") or {}
        if status.startswith("NOT_APPLICABLE"):
            category = "not_applicable"
        elif status.startswith("BLOCKED"):
            category = "blocked"
        elif (status.startswith("PARTIAL")
              or actions.get("waiver_watchlist") in {"WATCH_ONLY_NO_WAIVER_MODEL", "NO_AVAILABLE_EVIDENCE"}
              or any(str(value).startswith("PARTIAL") for value in
                     (actions.get("lineup"), actions.get("waiver_watchlist")))):
            category = "partial"
        elif status in {"READY", "READY_NO_URGENT_ACTION", "ACTION_REQUIRED", "READY_NO_FAAB_REMAINING"}:
            category = "ready"
        else:
            category = "unknown"
        counts[category] += 1
        if category in {"blocked", "partial", "unknown"}:
            reason = status
            if category == "partial" and not status.startswith("PARTIAL"):
                reason = next((str(value) for value in (actions.get("waiver_watchlist"), actions.get("lineup"))
                               if str(value).startswith("PARTIAL") or value in
                               {"WATCH_ONLY_NO_WAIVER_MODEL", "NO_AVAILABLE_EVIDENCE"}), status)
            reasons[reason] += 1
        if actions:
            lineups[str(actions.get("lineup") or "UNKNOWN")] += 1
            waivers[str(actions.get("waiver_watchlist") or "UNKNOWN")] += 1
            execution[str((report.get("timing") or {}).get("lineup_execution_status") or "UNKNOWN_LOCK_STATE")] += 1
    applicable = sum(counts[key] for key in ("ready", "partial", "blocked", "unknown"))
    if not applicable:
        status = "NOT_APPLICABLE" if reports else "NO_LEAGUES"
    elif counts["blocked"] == applicable:
        status = "BLOCKED"
    elif counts["partial"] or counts["blocked"] or counts["unknown"]:
        status = "PARTIAL"
    else:
        status = "READY"
    return {
        "status": status,
        "counts": {key: counts[key] for key in ("ready", "partial", "blocked", "not_applicable", "unknown")},
        "reason_counts": dict(sorted(reasons.items())),
        "lineup_status_counts": dict(sorted(lineups.items())),
        "lineup_execution_status_counts": dict(sorted(execution.items())),
        "waiver_watchlist_status_counts": dict(sorted(waivers.items())),
        "coverage_note": "Portfolio readiness is not proof of model activation, complete position coverage, or executable lineup changes; inspect the separate capability statuses.",
    }


def readiness_markdown(summary: dict[str, Any]) -> list[str]:
    counts = summary["counts"]
    return [
        f"Evidence status: **{summary['status']}** — " + "; ".join(f"{key}: {value}" for key, value in counts.items()),
        "",
        f"Lineup capabilities: `{summary['lineup_status_counts']}`",
        f"Lineup execution context: `{summary['lineup_execution_status_counts']}`",
        f"Waiver watchlist capabilities: `{summary['waiver_watchlist_status_counts']}`",
        "",
        summary["coverage_note"],
        "",
    ]


def write_output_index(path: Path, *, season: int, report_json: Path, report_markdown: Path) -> None:
    """Point workflow summary/commit steps at this invocation's exact outputs."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "season": int(season), "report_json": str(report_json),
        "report_markdown": str(report_markdown),
        "report_sha256": hashlib.sha256(report_json.read_bytes()).hexdigest(),
    }, indent=2) + "\n", encoding="utf-8")

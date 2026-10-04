#!/usr/bin/env python3
"""Resolve one due automatic PR2 postgame evaluation target.

The resolver never reconstructs a lineup.  It selects the newest immutable
pregame portfolio capture for the oldest completed, unevaluated week and binds
the automatic revision identity to that capture.  A completed week is eligible
only after its latest scheduled kickoff plus a conservative stabilization
buffer; provider capture and the exact outcome replay remain separate steps.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    from capture_in_season_pr2_lineup_evidence import GAMES_URL, schedule_games
    from in_season_pr2_weekly_lineups import SCHEMA_PORTFOLIO, capture_payload
    from weekly_lineup_operational_evidence import parse_dt, sha256_value
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.capture_in_season_pr2_lineup_evidence import GAMES_URL, schedule_games
    from research.in_season_pr2_weekly_lineups import SCHEMA_PORTFOLIO, capture_payload
    from research.weekly_lineup_operational_evidence import parse_dt, sha256_value


ROOT = Path(__file__).resolve().parents[1]
STABILIZATION_HOURS = 12.0
UA = "Fantasy-Intelligence-InSeason-Lineup-Outcome-Resolver/1.0"


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


def capture_target(value: dict[str, Any]) -> tuple[int, int]:
    if value.get("schema") != SCHEMA_PORTFOLIO:
        raise ValueError("PR2 portfolio capture schema invalid")
    capture_id = str(value.get("capture_id") or "")
    digest = str(value.get("capture_content_sha256") or "")
    if not capture_id or digest != sha256_value(capture_payload(value)):
        raise ValueError("PR2 portfolio capture content binding invalid")
    rows = [row for row in value.get("leagues") or [] if isinstance(row, dict)]
    managed = [row for row in rows if row.get("status") != "NOT_APPLICABLE_AUTOMATIC_LINEUP"]
    seasons = {int(row["season"]) for row in managed if row.get("season") is not None}
    weeks = {int(row["week"]) for row in managed if row.get("week") is not None}
    if len(seasons) != 1 or len(weeks) != 1:
        raise ValueError("PR2 portfolio capture target unresolved")
    return next(iter(seasons)), next(iter(weeks))


def capture_rows(root: Path, season: int) -> list[dict[str, Any]]:
    base = root / "data/research/evaluation" / str(season) / "weeks"
    rows: list[dict[str, Any]] = []
    for path in sorted(base.glob("week-*/lineups/captures/portfolio-*.json")):
        value = read_json(path)
        target_season, week = capture_target(value)
        if target_season != int(season):
            raise ValueError(f"capture season/path mismatch: {path}")
        generated = parse_dt(value.get("generated_at"))
        if generated is None:
            raise ValueError(f"capture generated_at invalid: {path}")
        rows.append({
            "season": target_season,
            "week": week,
            "capture_id": str(value["capture_id"]),
            "capture_path": path.relative_to(root).as_posix(),
            "generated_at": generated,
        })
    return rows


def evaluated_capture_ids(root: Path, season: int) -> set[str]:
    base = root / "data/research/evaluation" / str(season) / "weeks"
    values: set[str] = set()
    for path in sorted(base.glob("week-*/lineups/outcomes/*/outcome.json")):
        outcome = read_json(path)
        capture_id = str(outcome.get("capture_id") or "")
        if not capture_id or str(outcome.get("outcome_revision_id") or "") != path.parent.name:
            raise ValueError(f"outcome lineage/revision binding invalid: {path}")
        values.add(capture_id)
    return values


def automatic_outcome_decision(
    root: Path,
    schedule_csv: bytes,
    *,
    season: int,
    as_of: str,
    stabilization_hours: float = STABILIZATION_HOURS,
) -> dict[str, Any]:
    now = parse_dt(as_of)
    if now is None:
        raise ValueError("as_of must be an ISO timestamp")
    captures = capture_rows(root, season)
    base = {
        "capture_allowed": False,
        "reason": "NO_IMMUTABLE_CAPTURE",
        "season": int(season),
        "week": "",
        "capture_path": "",
        "capture_id": "",
        "outcome_revision_id": "",
        "latest_kickoff_at": "",
    }
    if not captures:
        return base
    evaluated = evaluated_capture_ids(root, season)
    latest_by_week: dict[int, dict[str, Any]] = {}
    for row in captures:
        current = latest_by_week.get(int(row["week"]))
        if current is None or (row["generated_at"], row["capture_id"]) > (current["generated_at"], current["capture_id"]):
            latest_by_week[int(row["week"])] = row
    waiting = False
    for week, row in sorted(latest_by_week.items()):
        if row["capture_id"] in evaluated:
            continue
        games = schedule_games(schedule_csv, season=season, week=week)
        if not games:
            raise ValueError(f"regular-season schedule missing for captured week {week}")
        kickoffs = [parse_dt(game.get("kickoff_utc")) for game in games]
        if any(value is None for value in kickoffs):
            raise ValueError(f"kickoff unresolved for captured week {week}")
        latest = max(value for value in kickoffs if value is not None)
        if now < latest + timedelta(hours=float(stabilization_hours)):
            waiting = True
            continue
        revision = f"nflverse-initial-v1-{row['capture_id']}"
        return {
            **base,
            "capture_allowed": True,
            "reason": "COMPLETED_WEEK_CAPTURE_DUE",
            "week": week,
            "capture_path": row["capture_path"],
            "capture_id": row["capture_id"],
            "outcome_revision_id": revision,
            "latest_kickoff_at": latest.isoformat(),
        }
    return {**base, "reason": "WAITING_FOR_OUTCOME_STABILIZATION" if waiting else "CAPTURES_ALREADY_EVALUATED"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve an automatic PR2 completed-week outcome target")
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--schedule-csv", help="Supplied nflverse games.csv; omitted fetches it")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--stabilization-hours", default=STABILIZATION_HOURS, type=float)
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args(argv)
    schedule_csv = Path(args.schedule_csv).read_bytes() if args.schedule_csv else fetch_bytes(GAMES_URL)
    decision = automatic_outcome_decision(
        ROOT,
        schedule_csv,
        season=args.season,
        as_of=args.as_of,
        stabilization_hours=args.stabilization_hours,
    )
    if args.github_output:
        for key in ("capture_allowed", "reason", "season", "week", "capture_path", "capture_id", "outcome_revision_id", "latest_kickoff_at"):
            value: Any = decision.get(key, "")
            if isinstance(value, bool):
                value = str(value).lower()
            print(f"{key}={value}")
    else:
        print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

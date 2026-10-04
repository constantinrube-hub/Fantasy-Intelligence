#!/usr/bin/env python3
"""Capture immutable provider evidence for In-Season PR2 weekly lineups.

The capture boundary deliberately owns all provider/network access.  The
lineup solver consumes only the resulting explicit envelope, which prevents a
later refresh from reconstructing who was locked or who the direct H2H
opponent was at a given time.
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
from zoneinfo import ZoneInfo

try:
    from current_snapshot_storage import load_current_snapshot
    from in_season_pr2_weekly_lineups import (
        current_index,
        managed_roster,
        read_json,
        verified_core,
    )
    from nfl_schedule_time import first_present, kickoff_iso
    from point_in_time_capture import build_envelope, compact_timestamp, first_write_json, sha256_bytes, canonical_bytes
    from weekly_lineup_decision_support import canonical_player_id
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.current_snapshot_storage import load_current_snapshot
    from research.in_season_pr2_weekly_lineups import current_index, managed_roster, read_json, verified_core
    from research.nfl_schedule_time import first_present, kickoff_iso
    from research.point_in_time_capture import build_envelope, compact_timestamp, first_write_json, sha256_bytes, canonical_bytes
    from research.weekly_lineup_decision_support import canonical_player_id


ROOT = Path(__file__).resolve().parents[1]
SLEEPER_BASE = "https://api.sleeper.app/v1"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
SCHEMA = "fie-in-season-pr2-weekly-lineup-evidence-v1"
UA = "Fantasy-Intelligence-InSeason-Lineup-Evidence/1.0"
NEW_YORK = ZoneInfo("America/New_York")
AUTOMATIC_CHECKPOINTS = {
    "PR2_WEEK_OPEN_T6": {"opens_hours_before": 7.5, "closes_hours_before": 4.0},
    "PR2_SUNDAY_MAIN_T4": {"opens_hours_before": 4.0, "closes_hours_before": 2.5},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/csv"})
    with urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read()


def fetch_json(url: str) -> Any:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def schedule_games(csv_bytes: bytes, *, season: int, week: int) -> list[dict[str, Any]]:
    rows = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    out = []
    for row in rows:
        try:
            if int(float(str(row.get("season") or "0"))) != int(season) or int(float(str(row.get("week") or "0"))) != int(week):
                continue
        except ValueError:
            continue
        kind = str(first_present(row, "game_type", "season_type", "type") or "").upper().replace("_", "")
        if kind not in {"REG", "REGULAR", "REGULARSEASON"}:
            continue
        home, away = str(row.get("home_team") or "").upper(), str(row.get("away_team") or "").upper()
        try:
            kickoff = kickoff_iso(first_present(row, "gameday", "game_date"), first_present(row, "gametime", "game_time", "kickoff"))
        except ValueError:
            continue
        if home and away:
            out.append({"home_team": home, "away_team": away, "kickoff_utc": kickoff, "game_id": row.get("game_id")})
    if not out:
        raise ValueError(f"no valid regular-season schedule games for {season} week {week}")
    return sorted(out, key=lambda row: (str(row["kickoff_utc"]), str(row["away_team"]), str(row["home_team"])))


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("capture time must include a timezone")
    return parsed.astimezone(timezone.utc)


def season_schedule(csv_bytes: bytes, *, season: int) -> dict[int, list[dict[str, Any]]]:
    weeks: dict[int, list[dict[str, Any]]] = {}
    for week in range(1, 19):
        try:
            weeks[week] = schedule_games(csv_bytes, season=season, week=week)
        except ValueError:
            continue
    if not weeks:
        raise ValueError(f"no valid regular-season schedule games for {season}")
    return weeks


def checkpoint_already_captured(root: Path, *, season: int, week: int, checkpoint_id: str) -> bool:
    base = root / "data/research/evaluation" / str(season) / "weeks" / f"week-{week}" / "lineups" / "evidence" / "captures"
    for path in sorted(base.glob("portfolio-*/operational-evidence.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if value.get("checkpoint_id") == checkpoint_id:
            return True
    return False


def automatic_capture_decision(root: Path, csv_bytes: bytes, *, season: int, as_of: str) -> dict[str, Any]:
    """Resolve one due checkpoint without fetching Sleeper or guessing a week.

    The three-hour general poll is bounded to T-7.5 through T-4 for the first
    weekly kickoff. Dedicated Sunday half-hour polls use T-4 through T-2.5,
    after the scheduled current refresh. Existing checkpoint evidence wins.
    """
    now = parse_time(as_of)
    due: list[dict[str, Any]] = []
    already = []
    for week, games in sorted(season_schedule(csv_bytes, season=season).items()):
        anchors: list[tuple[str, datetime]] = [("PR2_WEEK_OPEN_T6", min(parse_time(row["kickoff_utc"]) for row in games))]
        sunday = [
            parse_time(row["kickoff_utc"])
            for row in games
            if parse_time(row["kickoff_utc"]).astimezone(NEW_YORK).weekday() == 6
            and 13 <= parse_time(row["kickoff_utc"]).astimezone(NEW_YORK).hour < 16
        ]
        if sunday:
            anchors.append(("PR2_SUNDAY_MAIN_T4", min(sunday)))
        for checkpoint_id, anchor in anchors:
            policy = AUTOMATIC_CHECKPOINTS[checkpoint_id]
            hours = (anchor - now).total_seconds() / 3600.0
            if not policy["closes_hours_before"] <= hours <= policy["opens_hours_before"]:
                continue
            if checkpoint_already_captured(root, season=season, week=week, checkpoint_id=checkpoint_id):
                already.append(f"{week}:{checkpoint_id}")
                continue
            due.append({
                "capture_allowed": True,
                "reason": "CHECKPOINT_DUE",
                "season": int(season),
                "week": int(week),
                "checkpoint_id": checkpoint_id,
                "anchor_at": anchor.isoformat(),
                "hours_before_anchor": round(hours, 6),
            })
    if due:
        # When week-open and Sunday share an anchor, preserve both identities
        # over successive serialized polls by taking week-open first.
        due.sort(key=lambda row: (row["week"], 0 if row["checkpoint_id"] == "PR2_WEEK_OPEN_T6" else 1))
        return due[0]
    return {
        "capture_allowed": False,
        "reason": "CHECKPOINT_ALREADY_CAPTURED" if already else "OUTSIDE_CHECKPOINT_WINDOW",
        "season": int(season),
        "week": "",
        "checkpoint_id": "",
        "anchor_at": "",
        "hours_before_anchor": "",
        "existing_checkpoints": already,
    }


def team_kickoffs(games: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for game in games:
        for team in (game.get("home_team"), game.get("away_team")):
            text = str(team or "").upper().strip()
            if not text or text in out:
                raise ValueError(f"ambiguous or missing team schedule mapping: {text or 'EMPTY'}")
            out[text] = str(game["kickoff_utc"])
    return out


def enabled_registry(root: Path) -> dict[str, dict[str, Any]]:
    rows = (read_json(root / "data/research/leagues/registry.json", {}) or {}).get("leagues") or {}
    result = {str(lid): row for lid, row in rows.items() if isinstance(row, dict) and row.get("enabled") is True}
    if not result:
        raise ValueError("no enabled leagues in registry")
    return result


def build_evidence(
    root: Path,
    *,
    season: int,
    week: int,
    observed_at: str,
    schedule: list[dict[str, Any]],
    matchup_payloads: dict[str, list[dict[str, Any]]],
    league_scope: set[str] | None = None,
    checkpoint_id: str = "MANUAL",
) -> dict[str, Any]:
    """Build the consumer envelope from already-captured source responses."""
    root = root.resolve()
    registry = enabled_registry(root)
    if league_scope is not None:
        registry = {lid: row for lid, row in registry.items() if lid in league_scope}
    if not registry:
        raise ValueError("selected league scope contains no enabled leagues")
    by_team = team_kickoffs(schedule)
    username = str((read_json(root / "config/league-portfolio.json", {}) or {}).get("sleeper_username") or "")
    lock_by_league, matchup_by_league, bindings = {}, {}, []
    for league_id, registry_row in sorted(registry.items()):
        league_root = root / "data/research/leagues" / league_id
        current_path, manifest = league_root / "current/milestone5_current.json", league_root / "app/manifest.json"
        if not current_path.is_file() or not manifest.is_file():
            raise ValueError(f"required current/app evidence missing: {league_id}")
        current = load_current_snapshot(current_path, root=root)
        if int(current.get("season") or 0) != int(season) or int(current.get("week") or 0) != int(week):
            raise ValueError(f"current snapshot target mismatch: {league_id}")
        _, core = verified_core(root, manifest)
        roster, _ = managed_roster(core, username)
        if roster is None:
            raise ValueError(f"managed roster unresolved: {league_id}")
        index = current_index(current)
        player_kickoffs, missing = {}, []
        for raw_id in roster.get("players") or []:
            player = index.get(str(raw_id)) or index.get(str(raw_id).upper())
            player_id = canonical_player_id(player) if isinstance(player, dict) else None
            team = str((player or {}).get("team") or "").upper().strip()
            if player_id and team in by_team:
                player_kickoffs[player_id] = by_team[team]
            else:
                missing.append(str(raw_id))
        rows = matchup_payloads.get(league_id)
        if not isinstance(rows, list):
            raise ValueError(f"matchup payload unavailable or invalid: {league_id}")
        snapshot_sha = sha256_bytes(current_path.read_bytes())
        lock_by_league[league_id] = {
            "captured_at": observed_at,
            "season": int(season),
            "week": int(week),
            "player_kickoffs": dict(sorted(player_kickoffs.items())),
            "unmapped_roster_player_ids": sorted(missing),
            "schedule_games_sha256": sha256_bytes(canonical_bytes(schedule)),
        }
        matchup_by_league[league_id] = {"captured_at": observed_at, "season": int(season), "week": int(week), "rows": rows}
        bindings.append({
            "league_id": league_id,
            "league_name": registry_row.get("league_name"),
            "format": registry_row.get("format"),
            "current_snapshot": str(current_path.relative_to(root)),
            "current_snapshot_sha256": snapshot_sha,
            "managed_roster_id": roster.get("roster_id"),
            "roster_player_count": len(roster.get("players") or []),
            "mapped_player_kickoff_count": len(player_kickoffs),
            "unmapped_roster_player_ids": sorted(missing),
            "matchup_payload_sha256": sha256_bytes(canonical_bytes(rows)),
        })
    return {
        "schema": SCHEMA,
        "research_decision_support_only": True,
        "production_model": "M9",
        "app_runtime_changed": False,
        "transaction_or_lineup_execution": False,
        "season": int(season),
        "week": int(week),
        "checkpoint_id": str(checkpoint_id),
        "captured_at": observed_at,
        "schedule_games": schedule,
        "schedule_games_sha256": sha256_bytes(canonical_bytes(schedule)),
        "lock_evidence_by_league": lock_by_league,
        "matchup_evidence_by_league": matchup_by_league,
        "league_bindings": bindings,
    }


def write_capture(root: Path, evidence: dict[str, Any], source_payload: dict[str, Any]) -> dict[str, Path]:
    season, week, captured_at = int(evidence["season"]), int(evidence["week"]), str(evidence["captured_at"])
    capture_id = f"portfolio-{compact_timestamp(captured_at)}"
    base = root / "data/research/evaluation" / str(season) / "weeks" / f"week-{week}" / "lineups" / "evidence"
    source = build_envelope(
        capture_id=f"fie-in-season-pr2-lineups-{season}-{week:02d}-{compact_timestamp(captured_at)}",
        capture_intent="OTHER_GOVERNED",
        provider="Sleeper + nflverse",
        endpoint="Sleeper /league/{league_id}/matchups/{week}; nflverse games.csv regular-season target slice",
        observed_at=captured_at,
        as_of_semantics="Exact provider responses and target-week schedule slice observed at observed_at; no post-capture roster or matchup reconstruction.",
        payload=source_payload,
        revision_metadata_status="UNKNOWN",
    )
    capture_dir = base / "captures" / capture_id
    first_write_json(capture_dir / "source-envelope.json", source)
    first_write_json(capture_dir / "operational-evidence.json", evidence)
    latest = base / "latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"capture": capture_dir / "operational-evidence.json", "latest": latest}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture immutable In-Season PR2 lineup evidence")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int)
    parser.add_argument("--schedule-csv", help="Use a supplied nflverse games.csv; omitted fetches it")
    parser.add_argument("--matchups-json", help="JSON object keyed by league ID; omitted fetches Sleeper")
    parser.add_argument("--league-scope", default="", help="Optional comma-separated enabled league IDs")
    parser.add_argument("--observed-at", help="UTC ISO timestamp; defaults to capture time")
    parser.add_argument("--checkpoint-id", default="MANUAL", choices=["MANUAL", *AUTOMATIC_CHECKPOINTS])
    parser.add_argument("--schedule-check", action="store_true", help="Resolve whether an automatic checkpoint is due")
    parser.add_argument("--github-output", action="store_true", help="Emit schedule-check fields as GitHub outputs")
    args = parser.parse_args(argv)
    observed_at = args.observed_at or utc_now()
    csv_bytes = Path(args.schedule_csv).read_bytes() if args.schedule_csv else fetch_bytes(GAMES_URL)
    if args.schedule_check:
        decision = automatic_capture_decision(ROOT, csv_bytes, season=args.season, as_of=observed_at)
        if args.github_output:
            for key in ("capture_allowed", "reason", "season", "week", "checkpoint_id", "anchor_at", "hours_before_anchor"):
                value = decision.get(key, "")
                if isinstance(value, bool):
                    value = str(value).lower()
                print(f"{key}={value}")
        else:
            print(json.dumps(decision, sort_keys=True))
        return 0
    if args.week is None:
        parser.error("--week is required unless --schedule-check is used")
    schedule = schedule_games(csv_bytes, season=args.season, week=args.week)
    registry = enabled_registry(ROOT)
    scope = {x.strip() for x in args.league_scope.split(",") if x.strip()} or None
    selected = {lid for lid in registry if scope is None or lid in scope}
    if args.matchups_json:
        payloads = read_json(Path(args.matchups_json), {}) or {}
    else:
        payloads = {lid: fetch_json(f"{SLEEPER_BASE}/league/{lid}/matchups/{args.week}") for lid in sorted(selected)}
    evidence = build_evidence(ROOT, season=args.season, week=args.week, observed_at=observed_at, schedule=schedule, matchup_payloads=payloads, league_scope=scope, checkpoint_id=args.checkpoint_id)
    paths = write_capture(ROOT, evidence, {"schedule_source_sha256": sha256_bytes(csv_bytes), "schedule_games": schedule, "matchup_payloads": {lid: payloads[lid] for lid in sorted(selected)}})
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

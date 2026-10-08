#!/usr/bin/env python3
"""Read-only checkpoint audit. Observations never create prospective evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from point_in_time_capture import canonical_bytes
from m10_prospective_capture_contract import capture_paths, validate_capture
from capture_fie_sunday_paired_checkpoint import (
    checkpoint_decision, paths as sunday_paths, validate_checkpoint,
)


def stamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("AUDIT_TIMESTAMP_TIMEZONE_REQUIRED")
    return result.astimezone(timezone.utc)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def window_status(as_of: datetime, opens: datetime, closes: datetime) -> str:
    return "NOT_DUE" if as_of < opens else "DUE_MISSING" if as_of <= closes else "MISSED_UNRECORDED"


def schedule(root: Path, season: int, week: int, as_of: datetime) -> tuple[list[dict], dict]:
    """Reuse an observed schedule; no provider request or target-week stats."""
    candidates = []
    base = root / f"data/research/context/weather/{season}/week_{week:02d}"
    for path in base.glob("*/schedule-source-envelope.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        observed = stamp(value["observed_at"])
        if observed <= as_of:
            candidates.append((observed, path, value))
    if not candidates:
        raise ValueError("AUDIT_STORED_SCHEDULE_UNAVAILABLE")
    observed, path, value = max(candidates, key=lambda row: (row[0], str(row[1])))
    payload = value["payload"]
    if (payload.get("season"), payload.get("week")) != (season, week):
        raise ValueError("AUDIT_SCHEDULE_TARGET_MISMATCH")
    if hashlib.sha256(canonical_bytes(payload)).hexdigest() != value["payload_sha256"]:
        raise ValueError("AUDIT_SCHEDULE_PAYLOAD_HASH_MISMATCH")
    games = [{**game, "kickoff_at": game["kickoff"]} for game in payload["games"]]
    if not games or len({game["game_id"] for game in games}) != len(games):
        raise ValueError("AUDIT_SCHEDULE_EMPTY_OR_DUPLICATE")
    for game in games:
        stamp(game["kickoff_at"])
    return games, {"path": path.relative_to(root).as_posix(), "sha256": digest(path),
                   "observed_at": observed.isoformat(), "game_count": len(games)}


def terminal(root: Path, manifest: Path, missed: Path, validator, timing: dict, as_of: datetime) -> dict:
    row = dict(timing)
    if manifest.exists() and missed.exists():
        return {**row, "status": "BLOCKED_CONFLICTING_TERMINAL_EVIDENCE"}
    path = manifest if manifest.exists() else missed if missed.exists() else None
    if path is None:
        return row
    row.update(path=path.relative_to(root).as_posix(), sha256=digest(path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        observed = value.get("captured_at") or value.get("observed_at") or value.get("m10_observed_at")
        if not observed or stamp(observed) > as_of:
            raise ValueError("AUDIT_EVIDENCE_AFTER_AS_OF_OR_UNTIMED")
        if value.get("sleeper_observed_at") and stamp(value["sleeper_observed_at"]) > as_of:
            raise ValueError("AUDIT_SLEEPER_EVIDENCE_AFTER_AS_OF")
        if (value.get("season"), value.get("week")) != (timing["season"], timing["week"]):
            raise ValueError("AUDIT_EVIDENCE_TARGET_MISMATCH")
        result = validator(path == missed)
        return {**row, "status": "MISSED_RECORDED" if path == missed else "CAPTURED_VALIDATED",
                "validation": result}
    except Exception as exc:
        return {**row, "status": "BLOCKED_INVALID_EVIDENCE", "reason": f"{type(exc).__name__}:{exc}"}


def audit(root: Path, season: int, week: int, as_of: datetime) -> dict:
    if as_of.tzinfo is None or not 1 <= week <= 18:
        raise ValueError("AUDIT_TARGET_OR_TIME_INVALID")
    result = {"schema": "fie-weekly-evidence-audit-v1", "season": season, "week": week,
              "as_of_utc": as_of.isoformat(), "read_only": True, "network_access": False,
              "historical_reconstruction": False, "production_model_changed": False,
              "checkpoints": [], "note": "Missing evidence is observed here; only the original capture owner may write a terminal missed-capture record."}
    try:
        games, source = schedule(root, season, week, as_of)
    except Exception as exc:
        return {**result, "status": "BLOCKED", "reason": f"{type(exc).__name__}:{exc}"}
    result["schedule_source"] = source
    kickoff = min(stamp(game["kickoff_at"]) for game in games)
    m10 = capture_paths(root / "data/research/prospective/m10", season, week)
    timing = {"checkpoint": "M10_WEEK_OPEN", "season": season, "week": week, "opens_at": (kickoff - timedelta(hours=18)).isoformat(),
              "closes_at": kickoff.isoformat(),
              "status": window_status(as_of, kickoff - timedelta(hours=18), kickoff)}
    result["checkpoints"].append(terminal(root, m10["manifest"], m10["missed"],
        lambda missed: validate_capture(root / "data/research/prospective/m10", season, week, require_fixture=False), timing, as_of))
    decision = checkpoint_decision(games, as_of.isoformat())
    sunday = sunday_paths(root, season, week)
    timing = {"checkpoint": "SUNDAY_M10_SLEEPER_PAIRED", "season": season, "week": week, "status": {
        "WINDOW_NOT_REACHED": "NOT_DUE", "DUE": "DUE_MISSING", "WINDOW_MISSED": "MISSED_UNRECORDED",
        "NO_MAIN_SLATE": "NOT_APPLICABLE"}[decision["status"]],
        "opens_at": decision.get("target_at"), "closes_at": decision.get("window_close_at")}

    def validate_sunday(missed: bool):
        if not missed:
            return validate_checkpoint(root, season, week)
        value = json.loads(sunday["missed"].read_text(encoding="utf-8"))
        from capture_fie_sunday_paired_checkpoint import MISSED_SCHEMA, CHECKPOINT_ID
        assert value["schema"] == MISSED_SCHEMA and value["checkpoint_id"] == CHECKPOINT_ID
        assert value["season"] == season and value["week"] == week and value["status"] == "MISSED"
        assert value["historical_reconstruction"] is False and value["first_write_immutable"] is True
        assert checkpoint_decision(games, value["observed_at"])["status"] == "WINDOW_MISSED"
        return {"status": "MISSED"}

    result["checkpoints"].append(terminal(root, sunday["manifest"], sunday["missed"], validate_sunday, timing, as_of))
    bad = [row for row in result["checkpoints"] if row["status"].startswith("BLOCKED")]
    gaps = [row for row in result["checkpoints"] if row["status"] in {"DUE_MISSING", "MISSED_UNRECORDED", "MISSED_RECORDED"}]
    result["status"] = "BLOCKED" if bad else "ATTENTION" if gaps else "ON_TRACK"
    return result


def markdown(report: dict) -> str:
    lines = [f"## Prospective checkpoint audit — {report['season']} Week {report['week']}",
             f"Status: **{report['status']}**; as of `{report['as_of_utc']}`.", "",
             "| Checkpoint | State | Opens (UTC) | Closes (UTC) |",
             "|---|---|---|---|"]
    for row in report["checkpoints"]:
        lines.append(f"| {row['checkpoint']} | {row['status']} | {row.get('opens_at', '—')} | {row.get('closes_at', '—')} |")
    if report.get("reason"):
        lines += ["", report["reason"]]
    lines += ["", report["note"], "", "This audit covers M10 week-open and the paired Sunday M10/Sleeper checkpoint. It does not certify all weekly report products, lineup captures, or contextual datasets.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--as-of-utc", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(Path(args.root).resolve(), args.season, args.week,
                   stamp(args.as_of_utc) if args.as_of_utc else datetime.now(timezone.utc))
    path = Path(args.output)
    root = Path(args.root).resolve()
    if path.resolve().is_relative_to(root / "data/research"):
        raise ValueError("AUDIT_OUTPUT_MUST_NOT_WRITE_RESEARCH_EVIDENCE")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Observation outputs are immutable per invocation, outside forecast paths.
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(markdown(result))


if __name__ == "__main__":
    main()

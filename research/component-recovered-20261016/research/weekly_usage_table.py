#!/usr/bin/env python3
"""Source-keyed retrospective opportunity rows from the player-performance owner."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from point_in_time_capture import first_write_json
from weekly_evidence_audit import digest, stamp
from weekly_lineup_decision_support import numeric
from weekly_player_performance import build as replay_performance, replay_matches


DICTIONARY_PATH = Path("config/weekly-usage-dictionary.json")
SCHEMA = "fie-weekly-usage-table-v1"


def build(root: Path, performance_path: Path) -> dict:
    root, performance_path = root.resolve(), performance_path.resolve()
    if not performance_path.is_relative_to(root / "data/operations/weekly-performance"):
        raise ValueError("USAGE_PERFORMANCE_REPORT_OUTSIDE_OWNER")
    report = json.loads(performance_path.read_text(encoding="utf-8"))
    season, week = report.get("season"), report.get("week")
    expected = root / f"data/operations/weekly-performance/{season}/week_{int(week):02d}/reports"
    if not performance_path.is_relative_to(expected) or report.get("schema") != "fie-weekly-player-performance-v1":
        raise ValueError("USAGE_PERFORMANCE_REPORT_TARGET_INVALID")
    if report.get("status") not in {"AVAILABLE_PROVIDER_ROWS", "PARTIAL_UNRESOLVED_SOURCE_PLAYERS", "PARTIAL_MISSING_TEAM_ROWS"}:
        raise ValueError("USAGE_REQUIRES_RETROSPECTIVE_PROVIDER_ROWS")
    source = report.get("source") or {}
    source_path = (root / str(source.get("path") or "")).resolve()
    if not source_path.is_relative_to(root) or not source_path.is_file() or digest(source_path) != source.get("sha256"):
        raise ValueError("USAGE_PERFORMANCE_SOURCE_MISMATCH")
    replayed = replay_performance(root, source_path, season, week, stamp(report["as_of_utc"]))
    if not replay_matches(report, replayed):
        raise ValueError("USAGE_PERFORMANCE_REPLAY_MISMATCH")
    dictionary_path = root / DICTIONARY_PATH
    dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
    if (dictionary.get("schema") != "fie-weekly-usage-dictionary-v1"
            or dictionary.get("source_owner") != "research/weekly_player_performance.py"
            or dictionary.get("grain") != ["season", "week", "game_id", "source_gsis_player_id", "team"]):
        raise ValueError("USAGE_DICTIONARY_CONTRACT_INVALID")
    fields = dictionary.get("fields") or {}
    if not fields or any(spec.get("provider_column") != key for key, spec in fields.items()):
        raise ValueError("USAGE_DICTIONARY_FIELDS_INVALID")
    unsupported = sorted((dictionary.get("unsupported_fields") or {}).keys())
    rows, seen, unresolved = [], set(), 0
    for game in report.get("games") or []:
        for team in game.get("teams") or []:
            for player in team.get("players") or []:
                player_id, source_index = player.get("player_id"), player.get("source_row_index")
                if player_id is not None and (not isinstance(player_id, str) or not player_id.startswith("gsis:")):
                    raise ValueError("USAGE_SOURCE_PLAYER_ID_INVALID")
                if player_id is None:
                    unresolved += 1
                    if player.get("identity_status") != "UNRESOLVED_SOURCE_PLAYER" or not isinstance(source_index, int):
                        raise ValueError("USAGE_UNRESOLVED_SOURCE_ROW_INVALID")
                elif player.get("identity_status") != "SOURCE_GSIS_ID":
                    raise ValueError("USAGE_SOURCE_PLAYER_ID_STATUS_MISMATCH")
                key = (game["game_id"], team["team"], player_id if player_id is not None else f"UNRESOLVED:{source_index}")
                if key in seen:
                    raise ValueError("USAGE_DUPLICATE_SOURCE_PLAYER_GAME")
                seen.add(key)
                source_metrics = player.get("metrics") or {}
                metrics = {}
                for field in fields:
                    value = source_metrics.get(field)
                    parsed = numeric(value)
                    if value is not None and parsed is None:
                        raise ValueError("USAGE_SOURCE_METRIC_INVALID")
                    metrics[field] = parsed
                rows.append({"season": season, "week": week, "game_id": game["game_id"], "team": team["team"],
                             "source_gsis_player_id": player_id, "source_row_index": source_index,
                             "canonical_player_id": None, "position": player.get("position"), "metrics": metrics})
    if len(rows) != report.get("player_game_count") or unresolved != len(report.get("unresolved_source_row_indices") or []):
        raise ValueError("USAGE_PERFORMANCE_ROW_COVERAGE_MISMATCH")
    rows.sort(key=lambda item: (str(item["game_id"]), str(item["team"]), str(item["source_gsis_player_id"] or ""), item["source_row_index"]))
    return {"schema": SCHEMA, "season": season, "week": week,
            "status": "DESCRIPTIVE_PARTIAL" if report["status"] != "AVAILABLE_PROVIDER_ROWS" else "DESCRIPTIVE_SOURCE_ROWS",
            "player_game_rows": len(rows), "unresolved_source_rows": unresolved,
            "performance_report": {"path": performance_path.relative_to(root).as_posix(), "sha256": digest(performance_path),
                                   "status": report["status"]},
            "dictionary": {"path": DICTIONARY_PATH.as_posix(), "sha256": digest(dictionary_path)},
            "source": source, "unsupported_fields": unsupported, "rows": rows,
            "governance": {"retrospective_only": True, "target_week_pregame_feature_eligible": False,
                           "canonical_identity_resolved": False, "sleeper_crosswalk_inferred": False,
                           "model_or_ranking_changed": False,
                           "note": "GSIS source keys stay source keys. Missing metrics remain null; snaps, routes, route participation and alignment are unsupported."}}


def ensure_completed(root: Path, season: int, current_week: int, as_of: datetime) -> dict:
    root = root.resolve()
    if as_of.tzinfo is None or not 1 <= current_week <= 18:
        raise ValueError("USAGE_TARGET_OR_TIME_INVALID")
    candidates = []
    for week in range(1, current_week + 1):
        base = root / f"data/operations/weekly-performance/{season}/week_{week:02d}/reports"
        for path in base.glob("*.json"):
            report = json.loads(path.read_text(encoding="utf-8"))
            observed = stamp(report["as_of_utc"])
            if observed <= as_of:
                candidates.append((week, observed, path))
    if not candidates:
        return {"status": "NO_OP_NO_STORED_PERFORMANCE_REPORT", "season": season}
    week, _, path = max(candidates, key=lambda item: (item[0], item[1], str(item[2])))
    table = build(root, path)
    report_hash, dictionary_hash = table["performance_report"]["sha256"], table["dictionary"]["sha256"]
    output = root / f"data/operations/weekly-usage/{season}/week_{week:02d}/usage-{report_hash[:12]}-{dictionary_hash[:12]}.json"
    result = first_write_json(output, table)
    return {"status": "USAGE_TABLE_CREATED" if result == "CREATED" else "NO_OP_EXISTING_USAGE_TABLE",
            "season": season, "week": week, "report": output.relative_to(root).as_posix(), "player_game_rows": table["player_game_rows"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True, help="Current NFL week; newest completed report is selected")
    args = parser.parse_args()
    print(json.dumps(ensure_completed(args.root, args.season, args.week, datetime.now(timezone.utc)), sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Retrospective GSIS-to-Sleeper coverage from exact stored catalog IDs.

The current catalog is a later observed provider view, not a frozen pregame
identity source. This report does not grant canonical or decision authority.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from point_in_time_capture import first_write_json
from weekly_evidence_audit import digest, stamp
from weekly_usage_table import build as build_usage


SCHEMA = "fie-weekly-usage-identity-crosswalk-v1"
CATALOG = Path("data/research/app/player-catalog.json")


def build(root: Path, performance_path: Path, catalog_path: Path) -> dict:
    root, catalog_path = root.resolve(), catalog_path.resolve()
    if catalog_path != root / CATALOG or not catalog_path.is_file():
        raise ValueError("USAGE_CROSSWALK_REQUIRES_STORED_CATALOG")
    usage = build_usage(root, performance_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    players = catalog.get("players")
    if (catalog.get("schema") != "fie-player-catalog-v1" or catalog.get("schema_version") != 1
            or catalog.get("source") != "Sleeper /v1/players/nfl"
            or not isinstance(players, dict) or catalog.get("player_count") != len(players)):
        raise ValueError("USAGE_CROSSWALK_CATALOG_CONTRACT_INVALID")
    observed = stamp(catalog["generated_at"])
    if observed > datetime.now(timezone.utc):
        raise ValueError("USAGE_CROSSWALK_CATALOG_FUTURE_OBSERVATION")

    # A reused GSIS ID cannot silently select a Sleeper identity. Catalog
    # names/teams are never used to fill an absent or ambiguous exact ID.
    by_gsis: dict[str, set[str]] = {}
    for sleeper_id, player in players.items():
        if not isinstance(player, dict) or str(player.get("player_id")) != sleeper_id:
            raise ValueError("USAGE_CROSSWALK_CATALOG_PLAYER_ID_MISMATCH")
        gsis = player.get("gsis_id")
        if gsis is not None and str(gsis).strip():
            by_gsis.setdefault(str(gsis).strip(), set()).add(sleeper_id)
    rows = []
    counts = {name: 0 for name in
              ("MATCHED_EXACT_GSIS", "UNMATCHED_GSIS", "AMBIGUOUS_GSIS", "SOURCE_PLAYER_ID_MISSING")}
    for row in usage["rows"]:
        source_id = row["source_gsis_player_id"]
        matches = by_gsis.get(source_id[5:], set()) if source_id is not None else set()
        status = ("SOURCE_PLAYER_ID_MISSING" if source_id is None else
                  "UNMATCHED_GSIS" if not matches else
                  "AMBIGUOUS_GSIS" if len(matches) > 1 else "MATCHED_EXACT_GSIS")
        counts[status] += 1
        rows.append({
            "game_id": row["game_id"], "team": row["team"],
            "source_gsis_player_id": source_id, "source_row_index": row["source_row_index"],
            "sleeper_player_id": next(iter(matches)) if status == "MATCHED_EXACT_GSIS" else None,
            "canonical_player_id": None, "status": status,
        })
    return {
        "schema": SCHEMA, "season": usage["season"], "week": usage["week"],
        "performance_report": usage["performance_report"],
        "usage_dictionary": usage["dictionary"],
        "catalog": {"path": CATALOG.as_posix(), "sha256": digest(catalog_path),
                    "observed_at_utc": observed.isoformat(), "source": catalog["source"],
                    "raw_provider_response_archived": False},
        "player_game_rows": len(rows), "status_counts": counts, "rows": rows,
        "governance": {
            "retrospective_only": True, "target_week_pregame_feature_eligible": False,
            "canonical_identity_resolved": False, "model_or_ranking_changed": False,
            "note": "Only exact catalog GSIS IDs produce Sleeper ID candidates. The catalog is a later provider view without a bound raw response; this join cannot certify identity at the game cutoff or change prior captures.",
        },
    }


def ensure_completed(root: Path, season: int, current_week: int, as_of: datetime) -> dict:
    root = root.resolve()
    if as_of.tzinfo is None or not 1 <= current_week <= 18:
        raise ValueError("USAGE_CROSSWALK_TARGET_OR_TIME_INVALID")
    catalog_path = root / CATALOG
    if not catalog_path.is_file() or stamp(json.loads(catalog_path.read_text(encoding="utf-8"))["generated_at"]) > as_of:
        return {"status": "NO_OP_NO_OBSERVED_CATALOG", "season": season}
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
    week, _, performance_path = max(candidates, key=lambda item: (item[0], item[1], str(item[2])))
    crosswalk = build(root, performance_path, catalog_path)
    report_hash = crosswalk["performance_report"]["sha256"]
    catalog_hash = crosswalk["catalog"]["sha256"]
    dictionary_hash = crosswalk["usage_dictionary"]["sha256"]
    output = root / f"data/operations/weekly-usage-crosswalk/{season}/week_{week:02d}/crosswalk-{report_hash[:12]}-{dictionary_hash[:12]}-{catalog_hash[:12]}.json"
    result = first_write_json(output, crosswalk)
    return {"status": "CROSSWALK_CREATED" if result == "CREATED" else "NO_OP_EXISTING_CROSSWALK",
            "season": season, "week": week, "report": output.relative_to(root).as_posix(),
            "status_counts": crosswalk["status_counts"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True, help="Current week; newest stored completed report is selected")
    args = parser.parse_args()
    print(json.dumps(ensure_completed(args.root, args.season, args.week, datetime.now(timezone.utc)), sort_keys=True))


if __name__ == "__main__":
    main()

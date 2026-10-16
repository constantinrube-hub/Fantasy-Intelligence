#!/usr/bin/env python3
"""Fail-closed accounting audit for a generated FIE general-preview bundle."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from general_season_preview import PreviewError, RECONCILIATION_MAPPINGS, _number


def csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def decoded(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(str(value or "{}"))
    except json.JSONDecodeError as exc:
        raise PreviewError(f"INVALID_STATS_JSON:{exc}") from exc
    if not isinstance(loaded, dict):
        raise PreviewError("INVALID_STATS_OBJECT")
    return loaded


def stats_for(row: dict[str, Any]) -> dict[str, Any]:
    return decoded(row.get("raw_stats") if row.get("raw_stats") not in (None, "") else row.get("raw_stat_p50"))


def rows_by_team(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get("team") or "")].append(row)
    return out


def audit_rows(players: list[dict[str, Any]], team_stats: dict[str, dict[str, Any]], *, scenario: int | None = None) -> tuple[int, float]:
    regular = [x for x in players if x.get("position_model") != "UNALLOCATED"]
    unallocated = [x for x in players if x.get("position_model") == "UNALLOCATED"]
    player_teams = {str(x.get("team") or "") for x in regular}
    if player_teams != set(team_stats):
        raise PreviewError(f"TEAM_UNIVERSE_MISMATCH:scenario={scenario}:players={sorted(player_teams)}:teams={sorted(team_stats)}")
    by_team = rows_by_team(regular)
    unallocated_by_key: dict[tuple[str, str], float] = defaultdict(float)
    for row in unallocated:
        relation = str(row.get("reconciliation_relation") or "")
        if not relation:
            raise PreviewError(f"UNALLOCATED_RELATION_MISSING:scenario={scenario}")
        unallocated_by_key[(str(row.get("team") or ""), relation)] += sum(_number(v) for v in stats_for(row).values())
    checked, max_residual = 0, 0.0
    for team in sorted(team_stats):
        for relation, budget_stat, player_stat, positions in RECONCILIATION_MAPPINGS:
            allocated = sum(_number(stats_for(row).get(player_stat)) for row in by_team[team] if positions is None or row.get("position_model") in positions)
            budget = _number(team_stats[team].get(budget_stat))
            remainder = unallocated_by_key[(team, relation)]
            residual = budget - allocated - remainder
            max_residual = max(max_residual, abs(residual))
            checked += 1
            if allocated - budget > 1e-6 or abs(residual) > 1e-6:
                raise PreviewError(f"ACCOUNTING_MISMATCH:scenario={scenario}:team={team}:relation={relation}:residual={residual}")
    for row in regular:
        stats = stats_for(row)
        if _number(stats.get("completions")) - _number(stats.get("passing_attempts")) > 1e-6:
            raise PreviewError(f"QB_COMPLETIONS_EXCEED_ATTEMPTS:scenario={scenario}:player={row.get('canonical_player_id')}")
        if _number(stats.get("receptions")) - _number(stats.get("targets")) > 1e-6:
            raise PreviewError(f"RECEPTIONS_EXCEED_TARGETS:scenario={scenario}:player={row.get('canonical_player_id')}")
    return checked, max_residual


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit FIE general-preview player/team accounting")
    parser.add_argument("--phase-a-root", default="data/research/evaluation/2026/preseason/general-preview-v2")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    phase = root / args.phase_a_root
    player_path, team_path, scenario_path = (phase / "player-stat-projections.csv", phase / "team-stat-projections.csv", phase / "joint-scenarios.jsonl.gz")
    if not all(path.is_file() for path in (player_path, team_path, scenario_path)):
        raise PreviewError("PHASE_A_ACCOUNTING_ARTIFACT_MISSING")
    team_stats = {str(row["team"]): decoded(row["raw_stat_p50"]) for row in csv_rows(team_path) if row.get("entity_type") == "TEAM_OFFENSE"}
    player_rows = csv_rows(player_path)
    checked, max_residual = audit_rows(player_rows, team_stats)
    scenarios: dict[int, list[dict[str, Any]]] = defaultdict(list)
    with gzip.open(scenario_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                scenarios[int(row["scenario_id"])].append(row)
    if not scenarios:
        raise PreviewError("PHASE_A_SCENARIOS_EMPTY")
    for scenario_id, rows in sorted(scenarios.items()):
        count, residual = audit_rows(rows, team_stats, scenario=scenario_id)
        checked += count
        max_residual = max(max_residual, residual)
    print(json.dumps({"status": "PASS", "phase_a_root": str(phase.relative_to(root)), "scenario_count": len(scenarios), "relations_checked": checked, "maximum_absolute_residual": max_residual}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PreviewError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"General preview accounting audit fail-closed: {exc}")
        raise SystemExit(2)

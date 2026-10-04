#!/usr/bin/env python3
"""Build a persisted, research-only Waiver-v2 offensive outcome ledger.

The command deliberately accepts already-normalised source tables.  It does
not guess weekly roster completeness, schedule completion, scoring settings,
or player-stat completeness from a filename or a provider response.  Those
evidence assertions are explicit inputs and are recorded beside the ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from waiver_v2_outcomes import (
    OFFENSIVE_POSITIONS,
    OUTCOME_LEDGER_VERSION,
    build_dense_offensive_outcome_ledger,
    build_offensive_scoring_inventory,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scoring_signature(scoring: Mapping[str, Any]) -> str:
    """Match the canonical 16-character league-profile scoring signature."""
    canonical = json.dumps(dict(scoring), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _load_scoring(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and isinstance(payload.get("scoring_settings"), Mapping):
        payload = payload["scoring_settings"]
    elif isinstance(payload, Mapping) and isinstance(payload.get("settings"), Mapping):
        payload = payload["settings"]
    if not isinstance(payload, Mapping):
        raise ValueError("waiver-v2 scoring JSON must be an object or contain an object at settings")
    return {str(key): value for key, value in payload.items()}


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".gz":
        frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    else:
        frame.to_csv(path, index=False)


def build(
    *,
    player_stats_path: Path,
    weekly_roster_path: Path,
    team_schedule_path: Path,
    scoring_path: Path,
    output_path: Path,
    report_path: Path,
    player_stats_complete: bool,
) -> dict[str, Any]:
    """Build ledger and deterministic provenance report from explicit inputs."""
    scoring = _load_scoring(scoring_path)
    signature = scoring_signature(scoring)
    player_stats = pd.read_csv(player_stats_path, low_memory=False)
    weekly_roster = pd.read_csv(weekly_roster_path, low_memory=False)
    team_schedule = pd.read_csv(team_schedule_path, low_memory=False)
    inventories = {
        position: build_offensive_scoring_inventory(
            scoring, position=position, available_columns=set(player_stats.columns)
        )
        for position in OFFENSIVE_POSITIONS
    }
    ledger = build_dense_offensive_outcome_ledger(
        player_stats,
        weekly_roster,
        team_schedule,
        scoring,
        scoring_signature=signature,
        player_stats_complete=player_stats_complete,
    )
    _write_csv(ledger, output_path)
    statuses = ledger["outcome_status"].value_counts(dropna=False).sort_index()
    report = {
        "schema_version": 1,
        "outcome_ledger_version": OUTCOME_LEDGER_VERSION,
        "diagnostic_only": True,
        "activation_eligible": False,
        "scoring_signature": signature,
        "player_stats_complete_asserted": bool(player_stats_complete),
        "inputs": {
            "player_stats": {"path": str(player_stats_path), "sha256": _sha256(player_stats_path), "rows": int(len(player_stats))},
            "weekly_roster": {"path": str(weekly_roster_path), "sha256": _sha256(weekly_roster_path), "rows": int(len(weekly_roster))},
            "team_schedule": {"path": str(team_schedule_path), "sha256": _sha256(team_schedule_path), "rows": int(len(team_schedule))},
            "scoring": {"path": str(scoring_path), "sha256": _sha256(scoring_path), "nonzero_keys": int(sum(1 for value in scoring.values() if _nonzero(value)))},
        },
        "inventories": inventories,
        "ledger": {
            "path": str(output_path),
            "rows": int(len(ledger)),
            "complete_exact_rows": int(ledger["outcome_complete"].sum()),
            "incomplete_rows": int((~ledger["outcome_complete"]).sum()),
            "exact_scoring_rows": int(ledger["exact_scoring"].sum()),
            "status_counts": {str(key): int(value) for key, value in statuses.items()},
        },
        "limitations": [
            "This ledger is research-only and cannot activate M5, app rankings, recommendations, or transactions.",
            "A false or omitted player-stats-complete assertion leaves missing player-stat rows incomplete rather than scoring them as zero.",
            "Every non-zero position-relevant scoring key needs an explicit exact implementation before that position receives exact outcomes.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def _nonzero(value: Any) -> bool:
    try:
        return float(value) != 0.0
    except (TypeError, ValueError):
        return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a research-only Waiver-v2 offensive outcome ledger")
    parser.add_argument("--player-stats", required=True, help="Canonical player-week stat CSV or CSV.GZ")
    parser.add_argument("--weekly-roster", required=True, help="Canonical weekly roster-universe CSV or CSV.GZ")
    parser.add_argument("--team-schedule", required=True, help="Canonical team-week schedule-completeness CSV or CSV.GZ")
    parser.add_argument("--scoring-json", required=True, help="Exact league scoring settings JSON")
    parser.add_argument("--output", required=True, help="Ledger CSV or CSV.GZ output")
    parser.add_argument("--report", required=True, help="Provenance and coverage JSON output")
    parser.add_argument("--player-stats-complete", action="store_true", help="Assert player-stat source completeness for confirmed games")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = build(
        player_stats_path=Path(args.player_stats),
        weekly_roster_path=Path(args.weekly_roster),
        team_schedule_path=Path(args.team_schedule),
        scoring_path=Path(args.scoring_json),
        output_path=Path(args.output),
        report_path=Path(args.report),
        player_stats_complete=bool(args.player_stats_complete),
    )
    ledger = report["ledger"]
    print(f"Wrote {ledger['path']} | rows={ledger['rows']} | complete_exact_rows={ledger['complete_exact_rows']} | activation_eligible=false")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reproducibly build one research-only historical Waiver-v2 ledger profile.

This command is intentionally an explicit operator action.  It caches the
source files needed for a chosen completed-history window, preserves a raw
snapshot and its hashes, then invokes the source adapter and exact-ledger
builder.  It neither edits M2/M5 nor writes an app/current-snapshot artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from build_waiver_v2_outcome_ledger import build as build_ledger
from waiver_v2_source_adapter import adapt
from waiver_v2_event_ledger import build_e5_event_ledger


RUN_SCHEMA = "fie-waiver-v2-historical-ledger-run-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})


def write_source_snapshot(
    *, players: pd.DataFrame, player_stats_frames: Iterable[pd.DataFrame], weekly_roster_frames: Iterable[pd.DataFrame],
    games: pd.DataFrame, identity: pd.DataFrame, raw_dir: Path,
    pbp_frames: Iterable[pd.DataFrame] | None = None, participation_frames: Iterable[pd.DataFrame] | None = None,
) -> dict[str, dict[str, Any]]:
    """Persist the raw source envelope consumed by the fail-closed adapter."""
    player_stats = pd.concat(list(player_stats_frames), ignore_index=True, sort=False)
    weekly_roster = pd.concat(list(weekly_roster_frames), ignore_index=True, sort=False)
    paths = {
        "players": raw_dir / "players.csv.gz",
        "player_stats": raw_dir / "player-stats.csv.gz",
        "weekly_roster": raw_dir / "weekly-roster.csv.gz",
        "games": raw_dir / "games.csv.gz",
        "identity": raw_dir / "identity.csv.gz",
    }
    for key, frame in (("players", players), ("player_stats", player_stats), ("weekly_roster", weekly_roster), ("games", games), ("identity", identity)):
        _write_csv(frame, paths[key])
    snapshots = {key: {"path": str(path), "sha256": _sha256(path), "rows": int(len(frame))} for key, path, frame in (
        ("players", paths["players"], players),
        ("player_stats", paths["player_stats"], player_stats),
        ("weekly_roster", paths["weekly_roster"], weekly_roster),
        ("games", paths["games"], games),
        ("identity", paths["identity"], identity),
    )}
    for key, frames in (("pbp", pbp_frames), ("participation", participation_frames)):
        if frames is None:
            continue
        frame = pd.concat(list(frames), ignore_index=True, sort=False)
        path = raw_dir / f"{key}.csv.gz"
        _write_csv(frame, path)
        snapshots[key] = {"path": str(path), "sha256": _sha256(path), "rows": int(len(frame))}
    return snapshots


def _source_items(source_manager: Any, source: str, seasons: list[int]) -> list[dict[str, Any]]:
    """Bind raw source URLs and hashes to each event-source season."""
    return [{
        "season": int(season), "url": source_manager.url_for(source, season),
        "cache_path": str(source_manager.path_for(source, season)),
        "sha256": _sha256(source_manager.path_for(source, season)),
    } for season in seasons]


def run(
    *, seasons: list[int], cache_dir: Path, scoring_path: Path, output_dir: Path, player_stats_complete: bool,
    event_evidence: bool = True, participation_evidence: bool = False,
) -> dict[str, Any]:
    """Fetch/cache a source snapshot, then build the isolated historical ledger."""
    # Import only for the explicit networked operator path.  The canonical
    # PlayerIdentity and SourceManager owners remain in fie_research.
    from fie_research import SourceManager, build_identity

    if not seasons or any(int(season) < 1999 for season in seasons):
        raise ValueError("waiver-v2 historical runner requires at least one valid NFL season")
    requested = sorted({int(season) for season in seasons})
    source_manager = SourceManager(cache_dir)
    players = source_manager.load("players")
    ffids = source_manager.load("ff_playerids", required=False)
    identity, _ = build_identity(players, ffids)
    player_stats_frames = [source_manager.load("player_week", season) for season in requested]
    weekly_roster_frames = [source_manager.load("weekly_rosters", season) for season in requested]
    games = source_manager.load("schedules")
    pbp_frames = [source_manager.load("pbp", season) for season in requested] if event_evidence else None
    participation_frames = [source_manager.load("participation", season) for season in requested] if participation_evidence else None

    raw_dir = output_dir / "raw"
    source_snapshot = write_source_snapshot(
        players=players, player_stats_frames=player_stats_frames, weekly_roster_frames=weekly_roster_frames,
        games=games, identity=identity, raw_dir=raw_dir, pbp_frames=pbp_frames, participation_frames=participation_frames,
    )
    adapted_dir = output_dir / "adapted"
    adapter_receipt = adapt(
        raw_player_stats_path=Path(source_snapshot["player_stats"]["path"]),
        raw_weekly_roster_path=Path(source_snapshot["weekly_roster"]["path"]),
        raw_games_path=Path(source_snapshot["games"]["path"]),
        identity_path=Path(source_snapshot["identity"]["path"]),
        output_dir=adapted_dir,
    )
    event_ledger_receipt = None
    if event_evidence:
        event_ledger_receipt = build_e5_event_ledger(
            raw_pbp_path=Path(source_snapshot["pbp"]["path"]), identity_path=Path(source_snapshot["identity"]["path"]),
            canonical_player_stats_path=Path(adapter_receipt["outputs"]["player_stats"]["path"]), requested_seasons=requested,
            pbp_source_items=_source_items(source_manager, "pbp", requested),
            output_path=output_dir / "event-ledger" / "waiver-v2-event-ledger.csv.gz",
            weekly_stats_output_path=output_dir / "event-ledger" / "event-weekly-stats.csv.gz",
            report_path=output_dir / "event-ledger" / "waiver-v2-event-ledger-report.json",
        )
    ledger_dir = output_dir / "ledger"
    ledger_receipt = build_ledger(
        player_stats_path=Path(adapter_receipt["outputs"]["player_stats"]["path"]),
        weekly_roster_path=Path(adapter_receipt["outputs"]["weekly_roster"]["path"]),
        team_schedule_path=Path(adapter_receipt["outputs"]["team_schedule"]["path"]),
        scoring_path=scoring_path,
        output_path=ledger_dir / "offensive-outcome-ledger.csv.gz",
        report_path=ledger_dir / "offensive-outcome-ledger-report.json",
        player_stats_complete=player_stats_complete,
        event_weekly_stats_path=(Path(event_ledger_receipt["event_weekly_stats"]["path"]) if event_ledger_receipt else None),
        event_rule_support=(event_ledger_receipt.get("rule_support") if event_ledger_receipt else None),
    )
    report = {
        "schema": RUN_SCHEMA,
        "diagnostic_only": True,
        "activation_eligible": False,
        "requested_seasons": requested,
        "player_stats_complete_asserted": bool(player_stats_complete),
        "source_cache": str(cache_dir),
        "source_snapshot": source_snapshot,
        "source_manager_status": [asdict(status) for status in source_manager.status],
        "adapter_receipt": adapter_receipt,
        "ledger_receipt": ledger_receipt,
        "event_ledger_receipt": event_ledger_receipt,
        "limitations": [
            "This is a research-only historical reconstruction. It cannot transfer legacy M5 validation or activate recommendations.",
            "Coverage and blocker results apply only to the supplied scoring profile and source snapshot hashes.",
            "The player-stats-complete assertion is explicitly recorded and must be independently reviewed before labels can be admitted.",
            "The shared E5 event ledger remains research-only; only rule families with an exact source receipt may improve exact replay coverage.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "historical-ledger-run.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def _parse_seasons(raw: str) -> list[int]:
    text = str(raw).strip()
    if not text:
        raise ValueError("--seasons must not be empty")
    if "-" in text:
        first, last = text.split("-", 1)
        start, end = int(first), int(last)
        if end < start:
            raise ValueError("--seasons range must increase")
        return list(range(start, end + 1))
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one research-only historical Waiver-v2 outcome ledger")
    parser.add_argument("--seasons", default="2019-2025", help="Completed historical seasons, e.g. 2019-2025")
    parser.add_argument("--cache-dir", default=".cache/fie-waiver-v2")
    parser.add_argument("--scoring-json", required=True, help="Exact scoring profile JSON")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--player-stats-complete", action="store_true", help="Explicitly assert final player-stat feed completeness")
    parser.add_argument("--without-event-evidence", action="store_true", help="Do not fetch/snapshot PBP event evidence for this diagnostic run")
    parser.add_argument("--with-participation", action="store_true", help="Also fetch/snapshot participation for a later role-resolution phase")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    report = run(
        seasons=_parse_seasons(args.seasons), cache_dir=Path(args.cache_dir), scoring_path=Path(args.scoring_json),
        output_dir=Path(args.output_dir), player_stats_complete=bool(args.player_stats_complete),
        event_evidence=not bool(args.without_event_evidence), participation_evidence=bool(args.with_participation),
    )
    ledger = report["ledger_receipt"]["ledger"]
    print(json.dumps({"run": RUN_SCHEMA, "rows": ledger["rows"], "complete_exact_rows": ledger["complete_exact_rows"], "activation_eligible": False}, indent=2))


if __name__ == "__main__":
    main()

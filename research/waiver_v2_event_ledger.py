#!/usr/bin/env python3
"""Phase E1 source contract for the research-only Waiver-v2 event ledger.

This module deliberately does *not* score a league rule. It snapshots and
audits the event sources that later scoring phases may consume, and persists an
empty, schema-bound shared ledger. A later phase may add event rows only after
it can prove their exact source semantics, canonical identity and
reconciliation status.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


EVENT_LEDGER_SCHEMA = "fie-waiver-v2-event-ledger-v1"
EVENT_LEDGER_PHASE = "E1_SOURCE_CONTRACT"
EVENT_STATUSES = {
    "EXACT_EVENT_READY", "BLOCKED_EVENT_IDENTITY", "BLOCKED_EVENT_SEMANTICS",
    "BLOCKED_SOURCE_INCOMPLETE", "BLOCKED_RECONCILIATION_MISMATCH",
}
EVENT_TYPES = {
    "all_play_fumble", "pass_interception_td", "pass_sack", "qb_rushing_td",
    "fumble_recovery_td", "special_teams_td", "special_teams_forced_fumble",
    "special_teams_fumble_recovery", "kick_return_yards", "punt_return_yards",
    "field_goal_return_yards", "pass_completion_40", "pass_td_40", "pass_td_50",
    "rush_40", "rush_td_40", "rush_td_50", "reception_40", "reception_td_40",
    "reception_td_50",
}
EVENT_COLUMNS = [
    "season", "week", "game_id", "play_id", "event_type", "canonical_player_id",
    "team", "opponent", "play_type", "yards", "touchdown", "fumble", "fumble_lost",
    "fumble_recovery", "special_teams", "source_player_roles", "identity_evidence",
    "source_url", "source_sha256", "source_season", "schema_fingerprint",
    "builder_sha256", "reconciliation_status", "event_status",
]
PBP_REQUIRED_FIELDS = ("season", "week", "game_id", "play_id", "season_type", "play_type", "no_play")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_fingerprint(frame: pd.DataFrame) -> str:
    payload = [{"name": str(column), "dtype": str(frame[column].dtype)} for column in frame.columns]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _regular(frame: pd.DataFrame) -> pd.DataFrame:
    if "season_type" not in frame.columns:
        return frame.iloc[0:0].copy()
    return frame[frame["season_type"].astype(str).str.upper().isin({"REG", "REGULAR"})].copy()


def empty_event_ledger() -> pd.DataFrame:
    return pd.DataFrame(columns=EVENT_COLUMNS)


def _empty_strings(frame: pd.DataFrame, columns: list[str]) -> bool:
    return frame[columns].astype(str).apply(lambda value: value.str.strip() == "").any().any()


def validate_event_ledger(frame: pd.DataFrame) -> None:
    """Reject malformed event rows before any profile may inspect them."""
    missing = [column for column in EVENT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"waiver-v2 event ledger missing required columns: {', '.join(missing)}")
    if frame.empty:
        return
    key = ["season", "week", "game_id", "play_id", "event_type", "canonical_player_id"]
    if frame[key].isna().any().any() or _empty_strings(frame, key):
        raise ValueError("waiver-v2 event ledger has an incomplete canonical event key")
    if frame.duplicated(key).any():
        raise ValueError("waiver-v2 event ledger has duplicate canonical football events")
    invalid_types = sorted(set(frame["event_type"].astype(str)) - EVENT_TYPES)
    if invalid_types:
        raise ValueError(f"waiver-v2 event ledger has unsupported event types: {invalid_types}")
    invalid_statuses = sorted(set(frame["event_status"].astype(str)) - EVENT_STATUSES)
    if invalid_statuses:
        raise ValueError(f"waiver-v2 event ledger has unsupported event statuses: {invalid_statuses}")
    lineage = ["source_url", "source_sha256", "source_season", "schema_fingerprint", "builder_sha256", "reconciliation_status"]
    if frame[lineage].isna().any().any() or _empty_strings(frame, lineage):
        raise ValueError("waiver-v2 event ledger omits required source lineage")
    if "no_play" in frame.columns and frame["no_play"].fillna(0).astype(bool).any():
        raise ValueError("waiver-v2 event ledger contains a penalty/no-play event")


def build_source_inventory(
    pbp: pd.DataFrame, *, requested_seasons: list[int], pbp_source_items: list[Mapping[str, Any]],
    participation: pd.DataFrame | None = None, participation_source_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a per-season, field-level receipt for future event derivation."""
    seasons = sorted({int(season) for season in requested_seasons})
    source_by_season = {int(item["season"]): dict(item) for item in pbp_source_items}
    missing_fields = sorted(set(PBP_REQUIRED_FIELDS) - set(pbp.columns))
    season_values = pd.to_numeric(pbp.get("season", pd.Series(dtype="float64")), errors="coerce")
    rows: list[dict[str, Any]] = []
    for season in seasons:
        season_frame = pbp[season_values.eq(season)].copy()
        regular = _regular(season_frame)
        item = source_by_season.get(season)
        source_complete = bool(item is not None and not missing_fields and not regular.empty)
        rows.append({
            "season": season, "source_present": item is not None, "rows": int(len(season_frame)),
            "regular_rows": int(len(regular)), "missing_required_fields": missing_fields,
            "schema_fingerprint": schema_fingerprint(season_frame) if not season_frame.empty else None,
            "source_url": item.get("url") if item else None, "source_sha256": item.get("sha256") if item else None,
            "source_complete": source_complete,
            "status": "SOURCE_READY_FOR_FUTURE_EVENT_DERIVATION" if source_complete else "BLOCKED_SOURCE_INCOMPLETE",
        })
    participation_items = list(participation_source_items or [])
    requested = participation is not None
    participation_status = "NOT_REQUESTED"
    if requested:
        participation_status = "PRESENT_UNVALIDATED_FOR_FUTURE_ROLE_RESOLUTION" if participation_items and not participation.empty else "BLOCKED_SOURCE_INCOMPLETE"
    return {
        "schema": EVENT_LEDGER_SCHEMA, "phase": EVENT_LEDGER_PHASE, "requested_seasons": seasons,
        "pbp_required_fields": list(PBP_REQUIRED_FIELDS), "pbp_global_missing_required_fields": missing_fields,
        "pbp_by_season": rows, "pbp_source_complete": bool(rows) and all(row["source_complete"] for row in rows),
        "participation": {"requested": requested, "status": participation_status, "rows": int(len(participation)) if participation is not None else 0,
                          "source_items": participation_items,
                          "schema_fingerprint": schema_fingerprint(participation) if participation is not None and not participation.empty else None},
    }


def build_e1_event_ledger(
    *, raw_pbp_path: Path, requested_seasons: list[int], pbp_source_items: list[Mapping[str, Any]],
    output_path: Path, report_path: Path, raw_participation_path: Path | None = None,
    participation_source_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Persist the E1 source contract and empty shared event ledger."""
    pbp = pd.read_csv(raw_pbp_path, low_memory=False)
    participation = pd.read_csv(raw_participation_path, low_memory=False) if raw_participation_path else None
    inventory = build_source_inventory(pbp, requested_seasons=requested_seasons, pbp_source_items=pbp_source_items,
                                       participation=participation, participation_source_items=participation_source_items)
    ledger = empty_event_ledger()
    validate_event_ledger(ledger)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(output_path, index=False, compression={"method": "gzip", "mtime": 0})
    report = {
        "schema": EVENT_LEDGER_SCHEMA, "phase": EVENT_LEDGER_PHASE, "diagnostic_only": True,
        "activation_eligible": False, "event_rows": 0,
        "event_ledger": {"path": str(output_path), "sha256": _sha256(output_path), "rows": 0, "schema_columns": EVENT_COLUMNS},
        "raw_pbp": {"path": str(raw_pbp_path), "sha256": _sha256(raw_pbp_path), "rows": int(len(pbp)), "schema_fingerprint": schema_fingerprint(pbp)},
        "raw_participation": ({"path": str(raw_participation_path), "sha256": _sha256(raw_participation_path), "rows": int(len(participation)), "schema_fingerprint": schema_fingerprint(participation)} if raw_participation_path else None),
        "builder_sha256": _sha256(Path(__file__)), "source_inventory": inventory,
        "limitations": [
            "E1 writes no scoreable events and does not alter exact-scoring eligibility.",
            "A missing or incomplete season is a typed source blocker, never evidence of zero events.",
            "Participation is not assumed complete when it was not requested; a later role-resolution phase must request and validate it explicitly.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report

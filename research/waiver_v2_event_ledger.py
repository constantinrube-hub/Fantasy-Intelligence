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
import re
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
# nflverse's current CSV PBP release exposes ``play_deleted`` rather than the
# legacy ``no_play`` flag. A deleted play is an invalidated play and must be
# excluded before any event family is allowed to score it.
PBP_REQUIRED_FIELDS = ("season", "week", "game_id", "play_id", "season_type", "play_type", "play_deleted")
E2_RULE_FIELDS = {
    "fum": ("fumble", "fumbled_1_player_id", "fumbled_2_player_id"),
    "fum_lost": ("fumble", "fumble_lost", "fumbled_1_player_id", "fumbled_2_player_id"),
    "pass_int_td": ("interception", "return_touchdown", "passer_player_id"),
    "bonus_rush_td_qb": ("rush_touchdown", "rusher_player_id"),
    "pass_sack": ("sack", "passer_player_id"),
}
EXACT_GSIS_ID = re.compile(r"^00-\d{7}$")


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
    if "play_deleted" in frame.columns and frame["play_deleted"].fillna(0).astype(bool).any():
        raise ValueError("waiver-v2 event ledger contains a deleted/no-play event")


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


def _flag(value: Any) -> bool:
    if value is True:
        return True
    if value is None or pd.isna(value):
        return False
    try:
        return float(value) != 0.0
    except (TypeError, ValueError):
        return str(value).strip().lower() in {"true", "yes"}


def _clean_id(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return None if text.lower() in {"", "nan", "none", "<na>"} else text


def _canonical_resolver(identity: pd.DataFrame):
    required = {"gsis_id", "canonical_player_id"}
    if not required <= set(identity.columns):
        raise ValueError("waiver-v2 event ledger identity source requires gsis_id and canonical_player_id")
    bindings = {
        _clean_id(row.gsis_id): _clean_id(row.canonical_player_id)
        for row in identity[["gsis_id", "canonical_player_id"]].itertuples(index=False)
        if _clean_id(row.gsis_id) and _clean_id(row.canonical_player_id)
    }
    if len(bindings) != len({key for key in bindings}):
        raise ValueError("waiver-v2 event ledger identity source has duplicate gsis bindings")

    def resolve(value: Any) -> tuple[str | None, str]:
        source_id = _clean_id(value)
        if source_id is None:
            return None, "MISSING_SOURCE_PLAYER_ID"
        if source_id in bindings:
            return bindings[source_id], "IDENTITY_MAP_GSIS"
        if EXACT_GSIS_ID.fullmatch(source_id):
            return source_id, "EXACT_SOURCE_GSIS_FALLBACK"
        return None, "UNRESOLVED_SOURCE_PLAYER_ID"
    return resolve


def _team(row: pd.Series, name: str) -> str | None:
    value = _clean_id(row.get(name))
    return value.upper() if value else None


def _number(value: Any) -> float:
    parsed = pd.to_numeric(value, errors="coerce")
    return 0.0 if pd.isna(parsed) else float(parsed)


def _lineage(row: pd.Series, source_by_season: Mapping[int, Mapping[str, Any]], schema: str, builder: str) -> dict[str, Any]:
    season = int(row["season"])
    source = source_by_season.get(season) or {}
    return {
        "source_url": source.get("url"), "source_sha256": source.get("sha256"), "source_season": season,
        "schema_fingerprint": schema, "builder_sha256": builder,
    }


def _event_row(
    row: pd.Series, *, event_type: str, canonical_player_id: str, identity_evidence: str,
    source_by_season: Mapping[int, Mapping[str, Any]], schema: str, builder: str,
    fumble: bool = False, fumble_lost: bool = False, special_teams: bool = False,
) -> dict[str, Any]:
    return {
        "season": int(row["season"]), "week": int(row["week"]), "game_id": str(row["game_id"]),
        "play_id": str(row["play_id"]), "event_type": event_type, "canonical_player_id": canonical_player_id,
        "team": _team(row, "posteam"), "opponent": _team(row, "defteam"), "play_type": _clean_id(row.get("play_type")),
        "yards": _number(row.get("yards_gained")),
        "touchdown": _flag(row.get("touchdown")), "fumble": fumble, "fumble_lost": fumble_lost,
        "fumble_recovery": False, "special_teams": special_teams,
        "source_player_roles": json.dumps({"primary": event_type}, sort_keys=True),
        "identity_evidence": identity_evidence, "reconciliation_status": "NOT_YET_RECONCILED",
        "event_status": "EXACT_EVENT_READY", **_lineage(row, source_by_season, schema, builder),
    }


def _support(status: str, reason: str, column: str | None = None) -> dict[str, Any]:
    return {
        "support_status": status, "reason": reason,
        "required_columns": [column] if column else [],
    }


def build_e2_event_ledger(
    *, raw_pbp_path: Path, identity_path: Path, canonical_player_stats_path: Path,
    requested_seasons: list[int], pbp_source_items: list[Mapping[str, Any]], output_path: Path,
    weekly_stats_output_path: Path, report_path: Path,
) -> dict[str, Any]:
    """Derive E2 PBP events and rule-ready weekly aggregates fail-closed."""
    pbp = pd.read_csv(raw_pbp_path, low_memory=False)
    identity = pd.read_csv(identity_path, low_memory=False)
    stats = pd.read_csv(canonical_player_stats_path, low_memory=False)
    source_inventory = build_source_inventory(pbp, requested_seasons=requested_seasons, pbp_source_items=pbp_source_items)
    source_by_season = {int(item["season"]): dict(item) for item in pbp_source_items}
    builder = _sha256(Path(__file__))
    source_schema = schema_fingerprint(pbp)
    regular = _regular(pbp)
    if "play_deleted" in regular.columns:
        regular = regular[~regular["play_deleted"].map(_flag)].copy()
    resolver = _canonical_resolver(identity)
    supports: dict[str, dict[str, Any]] = {}
    source_ready = bool(source_inventory["pbp_source_complete"])
    for key, fields in E2_RULE_FIELDS.items():
        missing = sorted(set(fields) - set(pbp.columns))
        supports[key] = _support(
            "EXACT_EVENT_READY" if source_ready and not missing else "BLOCKED_SOURCE_INCOMPLETE",
            "confirmed E2 PBP fields and complete seasons available" if source_ready and not missing else f"missing PBP fields or incomplete source: {', '.join(missing) if missing else 'season inventory'}",
        )

    events: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    def blocked(row: pd.Series, event_type: str, status: str, reason: str) -> None:
        blockers.append({"season": int(row["season"]), "week": int(row["week"]), "game_id": str(row["game_id"]),
                         "play_id": str(row["play_id"]), "event_type": event_type, "status": status, "reason": reason})

    if supports["fum"]["support_status"] == "EXACT_EVENT_READY":
        for _, row in regular[regular["fumble"].map(_flag)].iterrows():
            identifiers = [_clean_id(row.get(column)) for column in ("fumbled_1_player_id", "fumbled_2_player_id")]
            identifiers = [value for value in identifiers if value]
            if not identifiers:
                blocked(row, "all_play_fumble", "BLOCKED_EVENT_IDENTITY", "fumble play has no exact fumbler player ID")
                continue
            if len(identifiers) != len(set(identifiers)):
                blocked(row, "all_play_fumble", "BLOCKED_EVENT_SEMANTICS", "same fumbler is repeated on one PBP play")
                continue
            lost = _flag(row.get("fumble_lost"))
            if lost and len(identifiers) != 1:
                supports["fum_lost"] = _support("BLOCKED_EVENT_SEMANTICS", "lost fumble cannot be assigned when one play has multiple fumblers")
            for source_id in identifiers:
                canonical, evidence = resolver(source_id)
                if canonical is None:
                    blocked(row, "all_play_fumble", "BLOCKED_EVENT_IDENTITY", evidence)
                    continue
                events.append(_event_row(row, event_type="all_play_fumble", canonical_player_id=canonical,
                                         identity_evidence=evidence, source_by_season=source_by_season,
                                         schema=source_schema, builder=builder, fumble=True,
                                         fumble_lost=lost and len(identifiers) == 1,
                                         special_teams=_flag(row.get("special_teams_play"))))

    if supports["pass_int_td"]["support_status"] == "EXACT_EVENT_READY":
        picks = regular[regular["interception"].map(_flag) & regular["return_touchdown"].map(_flag)]
        for _, row in picks.iterrows():
            canonical, evidence = resolver(row.get("passer_player_id"))
            if canonical is None:
                blocked(row, "pass_interception_td", "BLOCKED_EVENT_IDENTITY", evidence)
                continue
            events.append(_event_row(row, event_type="pass_interception_td", canonical_player_id=canonical,
                                     identity_evidence=evidence, source_by_season=source_by_season,
                                     schema=source_schema, builder=builder))

    if supports["bonus_rush_td_qb"]["support_status"] == "EXACT_EVENT_READY":
        rush_tds = regular[regular["rush_touchdown"].map(_flag)]
        for _, row in rush_tds.iterrows():
            canonical, evidence = resolver(row.get("rusher_player_id"))
            if canonical is None:
                blocked(row, "qb_rushing_td", "BLOCKED_EVENT_IDENTITY", evidence)
                continue
            events.append(_event_row(row, event_type="qb_rushing_td", canonical_player_id=canonical,
                                     identity_evidence=evidence, source_by_season=source_by_season,
                                     schema=source_schema, builder=builder))

    event_frame = pd.DataFrame(events, columns=EVENT_COLUMNS)
    if not event_frame.empty and event_frame.duplicated(["season", "week", "game_id", "play_id", "event_type", "canonical_player_id"]).any():
        raise ValueError("waiver-v2 E2 event derivation produced duplicate canonical events")
    validate_event_ledger(event_frame)
    blocker_statuses = {row["status"] for row in blockers}
    for key, event_type in (("fum", "all_play_fumble"), ("fum_lost", "all_play_fumble"),
                            ("pass_int_td", "pass_interception_td"), ("bonus_rush_td_qb", "qb_rushing_td")):
        relevant = [row for row in blockers if row["event_type"] == event_type]
        if relevant:
            status = "BLOCKED_EVENT_IDENTITY" if "BLOCKED_EVENT_IDENTITY" in {row["status"] for row in relevant} else "BLOCKED_EVENT_SEMANTICS"
            supports[key] = _support(status, f"{len(relevant)} {event_type} PBP events lack exact scoring attribution")

    # Reconcile sacks taken independently: the canonical weekly aggregate is
    # the scoring source, while PBP verifies its player/week accounting.
    if "sacks" not in stats.columns:
        supports["pass_sack"] = _support("BLOCKED_SOURCE_INCOMPLETE", "canonical weekly player stats lack sacks")
        sack_reconciliation = {"status": "BLOCKED_SOURCE_INCOMPLETE", "mismatch_rows": 0}
    elif supports["pass_sack"]["support_status"] != "EXACT_EVENT_READY":
        sack_reconciliation = {"status": "BLOCKED_SOURCE_INCOMPLETE", "mismatch_rows": 0}
    else:
        sack_rows = regular[regular["sack"].map(_flag)]
        pbp_sacks: list[dict[str, Any]] = []
        for _, row in sack_rows.iterrows():
            canonical, evidence = resolver(row.get("passer_player_id"))
            if canonical is None:
                blocked(row, "pass_sack", "BLOCKED_EVENT_IDENTITY", evidence)
                continue
            pbp_sacks.append({"canonical_player_id": canonical, "season": int(row["season"]), "week": int(row["week"]), "pbp_sacks": 1})
        sack_blockers = [row for row in blockers if row["event_type"] == "pass_sack"]
        if sack_blockers:
            supports["pass_sack"] = _support("BLOCKED_EVENT_IDENTITY", "sack play lacks exact passer identity")
            sack_reconciliation = {"status": "BLOCKED_EVENT_IDENTITY", "mismatch_rows": 0}
        else:
            pbp_grouped = pd.DataFrame(pbp_sacks).groupby(["canonical_player_id", "season", "week"], as_index=False)["pbp_sacks"].sum() if pbp_sacks else pd.DataFrame(columns=["canonical_player_id", "season", "week", "pbp_sacks"])
            stat_sacks = stats[stats.get("position_model", pd.Series("", index=stats.index)).eq("QB")][["canonical_player_id", "season", "week", "sacks"]].copy()
            stat_sacks["stat_sacks"] = pd.to_numeric(stat_sacks.pop("sacks"), errors="coerce")
            compared = pbp_grouped.merge(stat_sacks, on=["canonical_player_id", "season", "week"], how="outer").fillna(0.0)
            mismatches = compared[~compared["pbp_sacks"].eq(compared["stat_sacks"])]
            if mismatches.empty:
                sack_reconciliation = {"status": "EXACT_EVENT_READY", "mismatch_rows": 0}
            else:
                supports["pass_sack"] = _support("BLOCKED_RECONCILIATION_MISMATCH", "PBP passer sacks do not match canonical weekly sacks")
                sack_reconciliation = {"status": "BLOCKED_RECONCILIATION_MISMATCH", "mismatch_rows": int(len(mismatches)),
                                       "sample": mismatches.head(8).to_dict(orient="records")}

    ready = event_frame[event_frame.event_status.eq("EXACT_EVENT_READY")].copy()
    grouping = ["canonical_player_id", "season", "week"]
    weekly = ready.groupby(grouping, as_index=False).agg(
        event_fumbles=("event_type", lambda value: int((value == "all_play_fumble").sum())),
        event_fumbles_lost=("fumble_lost", lambda value: int(pd.Series(value).fillna(False).astype(bool).sum())),
        event_pass_int_td=("event_type", lambda value: int((value == "pass_interception_td").sum())),
        event_bonus_rush_td_qb=("event_type", lambda value: int((value == "qb_rushing_td").sum())),
    ) if not ready.empty else pd.DataFrame(columns=grouping + ["event_fumbles", "event_fumbles_lost", "event_pass_int_td", "event_bonus_rush_td_qb"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    event_frame.to_csv(output_path, index=False, compression={"method": "gzip", "mtime": 0})
    weekly_stats_output_path.parent.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(weekly_stats_output_path, index=False, compression={"method": "gzip", "mtime": 0})
    report = {
        "schema": EVENT_LEDGER_SCHEMA, "phase": "E2_FIRST_EXACT_PROFILES", "diagnostic_only": True,
        "activation_eligible": False, "builder_sha256": builder, "source_inventory": source_inventory,
        "rule_support": supports, "event_ledger": {"path": str(output_path), "sha256": _sha256(output_path), "rows": int(len(event_frame))},
        "event_weekly_stats": {"path": str(weekly_stats_output_path), "sha256": _sha256(weekly_stats_output_path), "rows": int(len(weekly))},
        "blockers": {"rows": int(len(blockers)), "status_counts": {status: sum(row["status"] == status for row in blockers) for status in sorted(blocker_statuses)}, "sample": blockers[:12]},
        "sack_reconciliation": sack_reconciliation,
        "limitations": ["Only E2 event families are represented.", "Blocked event attribution prevents exact rule replay; it is never converted to zero.", "This remains research-only and cannot activate M5, app rankings, recommendations, or transactions."],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report

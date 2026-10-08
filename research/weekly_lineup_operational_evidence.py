#!/usr/bin/env python3
"""Evidence-only timing and matchup helpers for In-Season PR2 lineups.

This module never fetches a provider.  A weekly capture workflow supplies its
immutable input envelopes; the lineup producer then decides whether a player
lock is proven.  That separation avoids reconstructing locks from a later
roster view or silently treating unknown game times as unlocked.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_dt(value: Any) -> datetime | None:
    try:
        text = str(value).replace("Z", "+00:00")
        result = datetime.fromisoformat(text)
        return (result if result.tzinfo else result.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception:
        return None


def player_locks(
    active_players: Iterable[dict[str, Any]],
    submitted: dict[str, Any],
    *,
    first_kickoff_utc: Any,
    lock_evidence: dict[str, Any] | None,
    as_of: datetime,
) -> dict[str, Any]:
    """Derive exact slot and bench locks only from a captured player-time map."""
    first = parse_dt(first_kickoff_utc)
    envelope = lock_evidence if isinstance(lock_evidence, dict) else {}
    base = {
        "as_of_utc": as_of.astimezone(timezone.utc).isoformat(),
        "first_kickoff_utc": first.isoformat() if first else None,
        "actionable": False,
        "locked_slot_player_ids": {},
        "locked_bench_player_ids": [],
        "evidence_sha256": sha256_value(envelope) if envelope else None,
        "schedule_games_sha256": envelope.get("schedule_games_sha256"),
        "captured_at": envelope.get("captured_at"),
    }
    if first is None:
        return {**base, "status": "BLOCKED_FIRST_KICKOFF_UNVERIFIED"}
    if as_of < first:
        return {**base, "status": "PREGAME_BEFORE_FIRST_KICKOFF", "actionable": True}
    if submitted.get("status") != "COMPLETE":
        return {**base, "status": "BLOCKED_SUBMITTED_LINEUP_UNRESOLVED_AFTER_KICKOFF"}
    times = envelope.get("player_kickoffs") if isinstance(envelope.get("player_kickoffs"), dict) else {}
    if not times:
        return {**base, "status": "BLOCKED_PLAYER_KICKOFF_EVIDENCE_MISSING"}
    starters = {str(row.get("player_id")): int(row.get("slot_index")) for row in (submitted.get("assignment") or [])}
    missing, parsed = [], {}
    for player in active_players:
        player_id = str(player.get("_canonical_player_id") or "")
        kickoff = parse_dt(times.get(player_id))
        if not player_id or kickoff is None:
            missing.append(player_id or "UNKNOWN")
        else:
            parsed[player_id] = kickoff
    if missing:
        return {**base, "status": "BLOCKED_PLAYER_KICKOFF_EVIDENCE_INCOMPLETE", "missing_player_ids": sorted(missing), "evidence_sha256": sha256_value(envelope)}
    locked_slots, locked_bench = {}, []
    for player_id, kickoff in parsed.items():
        if kickoff > as_of:
            continue
        if player_id in starters:
            locked_slots[starters[player_id]] = player_id
        else:
            locked_bench.append(player_id)
    return {
        **base,
        "status": "PLAYER_LOCKS_VERIFIED",
        "actionable": True,
        "evidence_sha256": sha256_value(envelope),
        "locked_slot_player_ids": dict(sorted(locked_slots.items())),
        "locked_bench_player_ids": sorted(locked_bench),
        "future_player_count": sum(1 for kickoff in parsed.values() if kickoff > as_of),
    }


def head_to_head_context(managed_roster_id: Any, matchup_evidence: dict[str, Any] | None) -> dict[str, Any]:
    """Return immutable Sleeper matchup context without a win-probability claim."""
    envelope = matchup_evidence if isinstance(matchup_evidence, dict) else {}
    rows = envelope.get("rows") if isinstance(envelope.get("rows"), list) else None
    if rows is None:
        return {"status": "NOT_YET_CAPTURED", "actionable": False}
    managed = str(managed_roster_id)
    own = [x for x in rows if isinstance(x, dict) and str(x.get("roster_id")) == managed]
    if len(own) != 1 or own[0].get("matchup_id") in {None, ""}:
        return {"status": "BLOCKED_MANAGED_MATCHUP_UNRESOLVED", "actionable": False, "evidence_sha256": sha256_value(envelope)}
    matchup_id = str(own[0]["matchup_id"])
    opponent = [x for x in rows if isinstance(x, dict) and str(x.get("roster_id")) != managed and str(x.get("matchup_id")) == matchup_id]
    if len(opponent) != 1:
        return {"status": "NOT_APPLICABLE_NO_DIRECT_H2H_OPPONENT", "actionable": False, "matchup_id": matchup_id, "evidence_sha256": sha256_value(envelope)}
    row = opponent[0]
    starters = row.get("starters")
    submitted = {"status": "NOT_PROVIDED_BY_CAPTURE", "player_id_namespace": "sleeper", "player_ids": None}
    if isinstance(starters, list):
        invalid = [value for value in starters if not isinstance(value, (str, int)) or isinstance(value, bool)]
        submitted = {"status": "BLOCKED_INVALID_STARTER_IDS" if invalid else "CAPTURED_SUBMITTED_STARTER_IDS",
                     "player_id_namespace": "sleeper",
                     "player_ids": None if invalid else [str(value) for value in starters if str(value).strip() not in {"", "0"}],
                     "empty_slot_count": sum(str(value).strip() in {"", "0"} for value in starters),
                     "observed_at": envelope.get("captured_at"), "final_lineup_certified": False}
    return {
        "status": "CAPTURED_H2H_CONTEXT",
        "actionable": False,
        "matchup_id": matchup_id,
        "opponent_roster_id": row.get("roster_id"),
        "opponent_reported_points": row.get("points"),
        "opponent_submitted_starters": submitted,
        "captured_at": envelope.get("captured_at"),
        "evidence_sha256": sha256_value(envelope),
        "basis": "captured direct head-to-head pairing only; not a win-probability or max-win lineup recommendation",
    }

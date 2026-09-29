#!/usr/bin/env python3
"""Canonical exact weekly-lineup assignment primitives for In-Season PR2.

This module deliberately has no provider requests and no app/runtime side
effects.  It reads the canonical JSON runtime contract instead of maintaining a
second Python roster-slot or position-alias map.  A later portfolio producer
owns evidence hydration, availability scenarios, locks and output persistence.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_CONTRACT = ROOT / "config/contracts/runtime-contracts.json"
NEGATIVE_INFINITY_COST = 10**18


class LineupEvidenceError(RuntimeError):
    """A typed, fail-closed problem with the lineup evidence contract."""


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_runtime_contract(root: Path = ROOT) -> tuple[dict[str, Any], str]:
    """Load the sole slot/alias source and return its exact file hash."""
    path = root / "config/contracts/runtime-contracts.json"
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive contract boundary
        raise LineupEvidenceError(f"BLOCKED_RUNTIME_CONTRACT_UNREADABLE:{type(exc).__name__}") from exc
    if not isinstance(contract.get("roster_slots"), dict) or not isinstance(contract.get("position_aliases"), dict):
        raise LineupEvidenceError("BLOCKED_RUNTIME_CONTRACT_INVALID")
    return contract, sha256_file(path)


def canonical_position(position: Any, contract: dict[str, Any]) -> str:
    raw = str(position or "").upper().strip()
    aliases = contract.get("position_aliases") if isinstance(contract.get("position_aliases"), dict) else {}
    return str(aliases.get(raw) or raw)


def canonical_player_id(player: dict[str, Any]) -> str | None:
    """Return a stable existing ID without guessing from a display name."""
    for key, prefix in (
        ("canonical_player_id", "canonical:"),
        ("internal_id", "canonical:"),
        ("sleeper_id", "sleeper:"),
        ("sleeperId", "sleeper:"),
        ("player_id", "legacy:"),
        ("playerId", "legacy:"),
        ("gsis_id", "gsis:"),
    ):
        value = player.get(key)
        if value is not None and str(value).strip():
            return f"{prefix}{str(value).strip()}"
    # D/ST is a team entity, not a player-name fallback.
    raw_position = str(player.get("position_model") or player.get("position") or "").upper()
    team = str(player.get("team") or "").upper().strip()
    if raw_position in {"DEF", "DST", "D/ST"} and team:
        return f"teamdef:{team}"
    return None


def player_position(player: dict[str, Any], contract: dict[str, Any]) -> str:
    raw = player.get("position_model") or player.get("position")
    if raw is None and isinstance(player.get("fantasy_positions"), list) and player["fantasy_positions"]:
        raw = player["fantasy_positions"][0]
    return canonical_position(raw, contract)


def starter_slot_instances(roster_positions: Iterable[Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand repeated starter slots and fail closed on unknown slot codes."""
    slots = contract["roster_slots"]
    out: list[dict[str, Any]] = []
    for raw in roster_positions or []:
        slot = str(raw or "").upper().strip()
        definition = slots.get(slot)
        if not isinstance(definition, dict):
            raise LineupEvidenceError(f"BLOCKED_UNKNOWN_ROSTER_SLOT:{slot or 'EMPTY'}")
        if definition.get("starter") is not True:
            continue
        positions = definition.get("positions")
        if not isinstance(positions, list) or not positions:
            raise LineupEvidenceError(f"BLOCKED_INVALID_STARTER_SLOT:{slot}")
        out.append({"slot": slot, "slot_index": len(out), "eligible_positions": [canonical_position(x, contract) for x in positions]})
    if not out:
        raise LineupEvidenceError("BLOCKED_NO_STARTER_SLOTS")
    return out


def eligible_for_slot(position: Any, slot: str, contract: dict[str, Any]) -> bool:
    definition = (contract.get("roster_slots") or {}).get(str(slot).upper())
    if not isinstance(definition, dict) or definition.get("starter") is not True:
        return False
    allowed = [canonical_position(x, contract) for x in (definition.get("positions") or [])]
    return canonical_position(position, contract) in allowed


def _hungarian_min(cost: list[list[int]]) -> list[int]:
    """Rectangular Hungarian assignment; returns selected column by row."""
    row_count, column_count = len(cost), len(cost[0]) if cost else 0
    if not row_count or not column_count:
        return []
    if row_count > column_count:
        raise LineupEvidenceError("BLOCKED_ASSIGNMENT_MATRIX_INVALID")
    u = [0] * (row_count + 1)
    v = [0] * (column_count + 1)
    p = [0] * (column_count + 1)
    way = [0] * (column_count + 1)
    for row in range(1, row_count + 1):
        p[0] = row
        col0 = 0
        minimum = [NEGATIVE_INFINITY_COST] * (column_count + 1)
        used = [False] * (column_count + 1)
        while True:
            used[col0] = True
            row0 = p[col0]
            delta = NEGATIVE_INFINITY_COST
            col1 = 0
            for col in range(1, column_count + 1):
                if used[col]:
                    continue
                current = cost[row0 - 1][col - 1] - u[row0] - v[col]
                if current < minimum[col]:
                    minimum[col] = current
                    way[col] = col0
                if minimum[col] < delta:
                    delta = minimum[col]
                    col1 = col
            for col in range(column_count + 1):
                if used[col]:
                    u[p[col]] += delta
                    v[col] -= delta
                else:
                    minimum[col] -= delta
            col0 = col1
            if p[col0] == 0:
                break
        while True:
            col1 = way[col0]
            p[col0] = p[col1]
            col0 = col1
            if col0 == 0:
                break
    assignment = [-1] * row_count
    for col in range(1, column_count + 1):
        if p[col]:
            assignment[p[col] - 1] = col - 1
    return assignment


@dataclass(frozen=True)
class Candidate:
    player_id: str
    position: str
    value: float | None
    player: dict[str, Any]


def candidates(players: Iterable[dict[str, Any]], contract: dict[str, Any], value_key: str) -> tuple[list[Candidate], list[str], list[str]]:
    """Normalize and deterministically sort candidates without name matching."""
    rows: list[Candidate] = []
    missing_identity: list[str] = []
    missing_value: list[str] = []
    seen: set[str] = set()
    for player in players or []:
        if not isinstance(player, dict):
            continue
        player_id = canonical_player_id(player)
        if not player_id:
            missing_identity.append(str(player.get("full_name") or player.get("name") or "UNKNOWN"))
            continue
        if player_id in seen:
            raise LineupEvidenceError(f"BLOCKED_DUPLICATE_CANONICAL_PLAYER:{player_id}")
        seen.add(player_id)
        value = numeric(player.get(value_key))
        if value is None:
            missing_value.append(player_id)
        rows.append(Candidate(player_id, player_position(player, contract), value, dict(player)))
    return sorted(rows, key=lambda x: x.player_id), sorted(missing_identity), sorted(missing_value)


def exact_lineup(
    players: Iterable[dict[str, Any]],
    roster_positions: Iterable[Any],
    *,
    value_key: str = "decision_weekly_projection",
    root: Path = ROOT,
    locked_slot_player_ids: Mapping[int, str] | None = None,
    locked_bench_player_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return the deterministic legal maximum-value lineup for scoreable rows.

    Missing values are reported but never converted to zero.  The caller decides
    whether its evidence policy permits a partial result to be shown.
    """
    contract, contract_sha = load_runtime_contract(root)
    slots = starter_slot_instances(roster_positions, contract)
    pool, missing_identity, missing_value = candidates(players, contract, value_key)
    locked_slots = {int(k): str(v) for k, v in (locked_slot_player_ids or {}).items()}
    locked_bench = {str(x) for x in (locked_bench_player_ids or [])}
    slot_by_index = {int(slot["slot_index"]): slot for slot in slots}
    by_id = {candidate.player_id: candidate for candidate in pool}
    if set(locked_slots) - set(slot_by_index):
        raise LineupEvidenceError("BLOCKED_LOCKED_SLOT_UNKNOWN")
    if set(locked_slots.values()) & locked_bench:
        raise LineupEvidenceError("BLOCKED_CONTRADICTORY_PLAYER_LOCK")
    if len(set(locked_slots.values())) != len(locked_slots):
        raise LineupEvidenceError("BLOCKED_DUPLICATE_LOCKED_PLAYER")
    for slot_index, player_id in locked_slots.items():
        candidate = by_id.get(player_id)
        slot = slot_by_index[slot_index]
        if candidate is None:
            raise LineupEvidenceError(f"BLOCKED_LOCKED_PLAYER_UNAVAILABLE:{player_id}")
        if candidate.value is None:
            raise LineupEvidenceError(f"BLOCKED_LOCKED_PLAYER_VALUE_UNAVAILABLE:{player_id}")
        if candidate.position not in slot["eligible_positions"]:
            raise LineupEvidenceError(f"BLOCKED_LOCKED_PLAYER_ILLEGAL_FOR_SLOT:{player_id}")
    unknown_bench = locked_bench - set(by_id)
    if unknown_bench:
        raise LineupEvidenceError(f"BLOCKED_LOCKED_BENCH_PLAYER_UNAVAILABLE:{sorted(unknown_bench)[0]}")

    free_slots = [slot for slot in slots if slot["slot_index"] not in locked_slots]
    free_pool = [candidate for candidate in pool if candidate.player_id not in set(locked_slots.values()) | locked_bench]
    # Add one dummy for each slot so an unfillable slot is explicit rather than
    # forcing an ineligible player into an assignment.
    column_count = len(free_pool) + len(free_slots)
    score_rows: list[list[float | None]] = []
    for slot in free_slots:
        values: list[float | None] = []
        for candidate in free_pool:
            values.append(candidate.value if candidate.value is not None and candidate.position in slot["eligible_positions"] else None)
        values.extend([0.0] * len(free_slots))
        score_rows.append(values)
    maximum = max([0.0, *[value for row in score_rows for value in row if value is not None]])
    # Integer micros preserve projection precision.  The column order is the
    # deterministic tie-break: canonical ID followed by dummy columns.
    cost = [
        [int(round((maximum - value) * 1_000_000)) if value is not None else NEGATIVE_INFINITY_COST for value in row]
        for row in score_rows
    ]
    assignment = _hungarian_min(cost) if free_slots else []
    used: set[str] = set(locked_slots.values())
    rows: list[dict[str, Any]] = []
    total = 0.0
    unfilled: list[dict[str, Any]] = []
    for slot_index, player_id in sorted(locked_slots.items()):
        candidate = by_id[player_id]
        slot = slot_by_index[slot_index]
        total += candidate.value or 0.0
        rows.append({
            "slot": slot["slot"], "slot_index": slot_index, "eligible_positions": slot["eligible_positions"],
            "player_id": candidate.player_id, "position": candidate.position, "value": round(candidate.value or 0.0, 6),
            "locked": True,
        })
    for slot, column in zip(free_slots, assignment):
        candidate = free_pool[column] if 0 <= column < len(free_pool) else None
        if candidate is None or candidate.value is None or candidate.position not in slot["eligible_positions"]:
            unfilled.append({"slot": slot["slot"], "slot_index": slot["slot_index"]})
            continue
        if candidate.player_id in used:  # Defensive proof against solver regressions.
            raise LineupEvidenceError(f"BLOCKED_DUPLICATE_ASSIGNMENT:{candidate.player_id}")
        used.add(candidate.player_id)
        total += candidate.value
        rows.append({
            "slot": slot["slot"],
            "slot_index": slot["slot_index"],
            "eligible_positions": slot["eligible_positions"],
            "player_id": candidate.player_id,
            "position": candidate.position,
            "value": round(candidate.value, 6),
        })
    rows.sort(key=lambda x: int(x["slot_index"]))
    return {
        "schema": "fie-in-season-pr2-exact-lineup-v1",
        "method": "canonical runtime contract + deterministic Hungarian maximum-weight assignment",
        "runtime_contract_sha256": contract_sha,
        "value_key": value_key,
        "slots": slots,
        "assignment": rows,
        "selected_player_ids": sorted(used),
        "bench_player_ids": [x.player_id for x in pool if x.player_id not in used],
        "unfilled_slots": unfilled,
        "total": round(total, 6),
        "complete_assignment": not unfilled,
        "missing_identity": missing_identity,
        "missing_value_player_ids": missing_value,
        "candidate_count": len(pool),
        "locks": {"locked_slot_player_ids": dict(sorted(locked_slots.items())), "locked_bench_player_ids": sorted(locked_bench)},
    }

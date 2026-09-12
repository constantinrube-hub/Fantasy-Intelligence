#!/usr/bin/env python3
"""Canonical conversion of nflverse schedule wall-clock times to UTC.

nflverse `gameday` plus `gametime` is published as an NFL Eastern-time
wall-clock value, including for international games.  Callers must never attach
UTC directly to that pair.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


NFL_SCHEDULE_ZONE = ZoneInfo("America/New_York")
UTC = timezone.utc


def first_present(record: Any, *names: str) -> Any:
    """Return the first non-empty mapping value without truth-testing pd.NA."""
    for name in names:
        value = record.get(name) if hasattr(record, "get") else None
        text = "" if value is None else str(value).strip()
        if text and text.lower() not in {"nan", "none", "nat"}:
            return value
    return None


def parse_nflverse_kickoff(gameday: Any, gametime: Any) -> datetime:
    """Return a UTC kickoff from nflverse date/time fields.

    A fully-qualified `gametime` timestamp retains its own offset.  A bare
    clock time is explicitly interpreted as America/New_York.
    """
    # Do not use ``value or ''`` here: pandas.NA intentionally has no boolean
    # truth value and schedule callers commonly pass Series values.
    day = "" if gameday is None else str(gameday).strip()
    clock = "" if gametime is None else str(gametime).strip()
    if not day or not clock or day.lower() in {"nan", "none"} or clock.lower() in {"nan", "none"}:
        raise ValueError("nflverse schedule row is missing gameday or gametime")
    value = clock if "T" in clock or len(clock) >= 19 else f"{day}T{clock}"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid nflverse kickoff: {day!r} {clock!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=NFL_SCHEDULE_ZONE)
    return parsed.astimezone(UTC)


def kickoff_iso(gameday: Any, gametime: Any) -> str:
    return parse_nflverse_kickoff(gameday, gametime).isoformat()

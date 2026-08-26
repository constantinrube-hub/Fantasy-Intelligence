#!/usr/bin/env python3
"""Canonical portfolio configuration and custom league-rule validation for FIE.

The portfolio config is human-controlled. Generated research registry/state remains
machine-controlled under data/research/leagues/.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

LEAGUE_ID_RE = re.compile(r"^[0-9]{6,32}$")
FORMATS = {"REDRAFT", "DYNASTY", "CHOPPED", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL"}
PRIORITIES = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "VERY_HIGH": 4}


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def canonical_priority(value: str | None) -> str:
    s = str(value or "MEDIUM").strip().upper().replace(" ", "_").replace("-", "_")
    if s == "VERYHIGH":
        s = "VERY_HIGH"
    if s not in PRIORITIES:
        raise ValueError(f"Unsupported priority {value!r}; expected one of {sorted(PRIORITIES)}")
    return s


def canonical_format(value: str | None) -> str:
    s = str(value or "").strip().upper().replace(" + ", "_").replace("+", "_").replace(" ", "_")
    aliases = {
        "REDRAFT_BEST_BALL": "REDRAFT_BESTBALL",
        "DYNASTY_BEST_BALL": "DYNASTY_BESTBALL",
        "BESTBALL_REDRAFT": "REDRAFT_BESTBALL",
        "BESTBALL_DYNASTY": "DYNASTY_BESTBALL",
    }
    s = aliases.get(s, s)
    if s not in FORMATS:
        raise ValueError(f"Unsupported format {value!r}; expected one of {sorted(FORMATS)}")
    return s


def _int_year(value: Any, field: str) -> int:
    try:
        y = int(value)
    except Exception as exc:
        raise ValueError(f"{field} must be a four-digit season") from exc
    if y < 1990 or y > 2100:
        raise ValueError(f"{field}={y} is outside the supported range")
    return y


def normalize_constraint(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("research_constraints entries must be objects")
    typ = str(raw.get("type") or "").strip()
    if typ == "nfl_entry_cohort_floor":
        floor = _int_year(raw.get("minimum_entry_season"), "minimum_entry_season")
        return {"type": typ, "minimum_entry_season": floor}
    if typ == "cohort_floor_with_legacy_cap":
        floor = _int_year(raw.get("unlimited_entry_season_min"), "unlimited_entry_season_min")
        legacy_max = _int_year(raw.get("legacy_entry_season_max", floor - 1), "legacy_entry_season_max")
        if legacy_max >= floor:
            raise ValueError("legacy_entry_season_max must be below unlimited_entry_season_min")
        caps_raw = raw.get("legacy_cap_by_season") or {}
        if not isinstance(caps_raw, dict) or not caps_raw:
            raise ValueError("cohort_floor_with_legacy_cap requires legacy_cap_by_season")
        caps: Dict[str, int] = {}
        last_cap = None
        for k, v in sorted(caps_raw.items(), key=lambda kv: int(kv[0])):
            season = _int_year(k, "legacy_cap_by_season season")
            try:
                cap = int(v)
            except Exception as exc:
                raise ValueError(f"legacy cap for {season} must be an integer") from exc
            if cap < 0:
                raise ValueError("legacy caps cannot be negative")
            if last_cap is not None and cap > last_cap:
                raise ValueError("legacy caps must be non-increasing across seasons")
            caps[str(season)] = cap
            last_cap = cap
        after = raw.get("legacy_cap_after_2030")
        if after is None:
            after = raw.get("legacy_cap_after_schedule")
        try:
            after_cap = int(after if after is not None else last_cap)
        except Exception as exc:
            raise ValueError("legacy_cap_after_2030 must be an integer") from exc
        if after_cap < 0:
            raise ValueError("legacy_cap_after_2030 cannot be negative")
        if last_cap is not None and after_cap > last_cap:
            raise ValueError("post-schedule legacy cap cannot increase")
        return {
            "type": typ,
            "unlimited_entry_season_min": floor,
            "legacy_entry_season_max": legacy_max,
            "legacy_cap_by_season": caps,
            "legacy_cap_after_2030": after_cap,
        }
    raise ValueError(f"Unsupported research constraint type {typ!r}")


def normalize_constraints(values: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    return [normalize_constraint(x) for x in (values or [])]


def normalize_entry(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Each league entry must be an object")
    lid = str(raw.get("league_id") or "").strip()
    if not LEAGUE_ID_RE.fullmatch(lid):
        raise ValueError(f"Invalid Sleeper league_id {lid!r}")
    fmt = canonical_format(raw.get("format"))
    priority = canonical_priority(raw.get("priority"))
    alias = raw.get("alias")
    alias = str(alias).strip() if alias not in (None, "") else None
    constraints = normalize_constraints(raw.get("research_constraints") or raw.get("restrictions") or [])
    return {
        "league_id": lid,
        "format": fmt,
        "priority": priority,
        "alias": alias,
        "research_constraints": constraints,
        "enabled": bool(raw.get("enabled", True)),
    }


def load_portfolio_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    cfg = load_json(p)
    if not isinstance(cfg, dict):
        raise ValueError(f"Portfolio config not found or invalid: {p}")
    schema = int(cfg.get("schema_version") or 0)
    if schema < 1:
        raise ValueError("portfolio schema_version must be >= 1")
    username = str(cfg.get("sleeper_username") or "").strip()
    if not username:
        raise ValueError("sleeper_username is required")
    rows = [normalize_entry(x) for x in (cfg.get("leagues") or [])]
    if not rows:
        raise ValueError("At least one league is required")
    ids = [x["league_id"] for x in rows]
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        raise ValueError(f"Duplicate League IDs in portfolio: {', '.join(dupes)}")
    return {"schema_version": schema, "sleeper_username": username, "leagues": rows}


def entry_for(config: Dict[str, Any], league_id: str) -> Dict[str, Any] | None:
    lid = str(league_id)
    for row in config.get("leagues") or []:
        if str(row.get("league_id")) == lid:
            return row
    return None


def priority_value(priority: str) -> int:
    return PRIORITIES[canonical_priority(priority)]


def cutoff_value(cutoff: str | None) -> int:
    s = str(cutoff or "ALL").strip().upper().replace(" ", "_")
    if s == "ALL":
        return 1
    return priority_value(s)


def qualifies_priority(priority: str, cutoff: str | None) -> bool:
    return priority_value(priority) >= cutoff_value(cutoff)

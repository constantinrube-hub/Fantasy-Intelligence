#!/usr/bin/env python3
"""Window 1C: auditable weekly actions + operational UX report layer.

The producer consumes existing governed FIE current snapshots and live app roster
snapshots. It does not train/reweight/promote a model, alter canonical rankings,
or optimize FAAB bids. The output is decision-support evidence under
``data/research/evaluation`` only.

Design constraints:
* preserve current-snapshot fail-closed profile/scoring guards;
* never use target-week realised stats;
* use the existing ``decision_weekly_projection`` contract exactly as produced;
* label FIE-governed projections separately from Sleeper fallback projections;
* never zero-impute missing weekly values;
* detect submitted-lineup upgrade alerts without replacing the production browser
  lineup optimizer;
* reserve add/drop optimization and bid sizing for Window 1D.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_LEAGUE = "fie-window1c-weekly-actions-v1"
SCHEMA_PORTFOLIO = "fie-window1c-weekly-actions-portfolio-v1"
BESTBALL_FORMATS = {"REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"}
NON_STARTER_SLOTS = {"BN", "BENCH", "IR", "RESERVE", "TAXI"}

# Sleeper roster-slot eligibility. Position aliases are normalized before use.
SLOT_ELIGIBILITY: dict[str, set[str]] = {
    "QB": {"QB"},
    "RB": {"RB"},
    "WR": {"WR"},
    "TE": {"TE"},
    "K": {"K"},
    "DEF": {"DEF"},
    "DST": {"DEF"},
    "DL": {"DL"},
    "DE": {"DL"},
    "DT": {"DL"},
    "LB": {"LB"},
    "DB": {"DB"},
    "CB": {"DB"},
    "S": {"DB"},
    "FLEX": {"RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "SUPERFLEX": {"QB", "RB", "WR", "TE"},
    "IDP_FLEX": {"DL", "LB", "DB"},
    "IDP_FLEX2": {"DL", "LB", "DB"},
}


class EvidenceError(RuntimeError):
    pass


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def normalize_position(value: Any) -> str:
    pos = str(value or "").upper().strip()
    if pos in {"DST", "D/ST"}:
        return "DEF"
    if pos in {"DE", "DT", "EDGE", "IDL"}:
        return "DL"
    if pos in {"CB", "S", "FS", "SS"}:
        return "DB"
    return pos


def valid_ids(values: Iterable[Any] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text == "0" or text in out:
            continue
        out.append(text)
    return out


def load_current(path: Path, *, root: Path) -> dict[str, Any]:
    """Hydrate split snapshots when the repository helper is available."""
    try:
        from current_snapshot_storage import load_current_snapshot  # type: ignore
        return load_current_snapshot(path, root=root)
    except ImportError:
        return read_json(path, {}) or {}
    except Exception as exc:
        raise EvidenceError(f"CURRENT_SNAPSHOT_HYDRATION_FAILED:{type(exc).__name__}:{exc}") from exc


def manifest_core(root: Path, manifest_path: Path) -> tuple[Path, dict[str, Any]]:
    manifest = read_json(manifest_path, {}) or {}
    entry = manifest.get("core") if isinstance(manifest.get("core"), dict) else None
    if entry is None:
        files = manifest.get("files") if isinstance(manifest.get("files"), list) else []
        matches = [x for x in files if isinstance(x, dict) and x.get("name") == "core"]
        if len(matches) == 1:
            entry = matches[0]
    if not isinstance(entry, dict):
        raise EvidenceError("APP_MANIFEST_CORE_MISSING")
    rel = str(entry.get("path") or "")
    expected = str(entry.get("sha256") or "")
    if not rel or not expected:
        raise EvidenceError("APP_MANIFEST_CORE_BINDING_MISSING")
    core_path = (root / rel).resolve()
    try:
        core_path.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceError("APP_CORE_PATH_OUTSIDE_REPO") from exc
    if not core_path.is_file():
        raise EvidenceError(f"APP_CORE_MISSING:{rel}")
    actual = sha256_file(core_path)
    if actual != expected:
        raise EvidenceError(f"APP_CORE_DRIFT:{expected}:{actual}")
    return core_path, read_json(core_path, {}) or {}


def player_catalog(root: Path, core: dict[str, Any]) -> dict[str, dict[str, Any]]:
    shared = core.get("shared") if isinstance(core.get("shared"), dict) else {}
    rel = str(shared.get("player_catalog") or "")
    if not rel:
        return {}
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return {}
    x = read_json(p, {}) or {}
    players = x.get("players") if isinstance(x, dict) else None
    return players if isinstance(players, dict) else {}


def current_index(current: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in current.get("players") or []:
        if not isinstance(row, dict):
            continue
        for candidate in (row.get("sleeper_id"), row.get("canonical_player_id")):
            if candidate is None:
                continue
            key = str(candidate).strip()
            if key and key not in out:
                out[key] = row
        if normalize_position(row.get("position_model")) == "DEF" and row.get("team"):
            out.setdefault(str(row.get("team")), row)
    return out


def catalog_row(catalog: dict[str, dict[str, Any]], player_id: str, row: dict[str, Any] | None = None) -> dict[str, Any]:
    c = catalog.get(str(player_id))
    if isinstance(c, dict):
        return c
    # Team defenses do not necessarily exist in the individual-player catalog.
    return {}


def player_name(player_id: str, row: dict[str, Any] | None, catalog: dict[str, dict[str, Any]]) -> str:
    c = catalog_row(catalog, player_id, row)
    if row:
        for key in ("full_name", "name", "player_name"):
            if row.get(key):
                return str(row[key])
    if c.get("full_name"):
        return str(c["full_name"])
    if row and normalize_position(row.get("position_model")) == "DEF":
        return f"{row.get('team') or player_id} D/ST"
    return str(player_id)


def injury_status(player_id: str, catalog: dict[str, dict[str, Any]]) -> str | None:
    c = catalog.get(str(player_id)) or {}
    value = c.get("injury_status")
    return str(value).strip() if value else None


def active_status(player_id: str, catalog: dict[str, dict[str, Any]]) -> str | None:
    c = catalog.get(str(player_id)) or {}
    value = c.get("status")
    return str(value).strip() if value else None


def roster_position(player_id: str, row: dict[str, Any] | None, catalog: dict[str, dict[str, Any]]) -> str:
    if row:
        pos = normalize_position(row.get("position_model") or row.get("position"))
        if pos:
            return pos
    c = catalog.get(str(player_id)) or {}
    fps = c.get("fantasy_positions") if isinstance(c.get("fantasy_positions"), list) else []
    if fps:
        return normalize_position(fps[0])
    return normalize_position(c.get("position"))


def eligible(slot: str, position: str) -> bool:
    slot_n = str(slot or "").upper().strip()
    pos_n = normalize_position(position)
    allowed = SLOT_ELIGIBILITY.get(slot_n)
    if allowed is None:
        # Exact unknown positions fail closed to exact-position eligibility only.
        return slot_n == pos_n
    return pos_n in allowed


def starter_slots(core: dict[str, Any]) -> list[str]:
    sleeper = core.get("sleeper") if isinstance(core.get("sleeper"), dict) else {}
    league = sleeper.get("league") if isinstance(sleeper.get("league"), dict) else {}
    positions = league.get("roster_positions") if isinstance(league.get("roster_positions"), list) else []
    return [str(x).upper() for x in positions if str(x).upper() not in NON_STARTER_SLOTS]


def sleeper_data(core: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sleeper = core.get("sleeper") if isinstance(core.get("sleeper"), dict) else {}
    rosters = sleeper.get("rosters") if isinstance(sleeper.get("rosters"), list) else []
    users = sleeper.get("users") if isinstance(sleeper.get("users"), list) else []
    return [x for x in rosters if isinstance(x, dict)], [x for x in users if isinstance(x, dict)]


def managed_roster(core: dict[str, Any], username: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    rosters, users = sleeper_data(core)
    needle = str(username or "").strip().lower()
    matches = [u for u in users if str(u.get("display_name") or u.get("username") or "").strip().lower() == needle]
    if len(matches) != 1:
        return None, matches[0] if len(matches) == 1 else None
    user = matches[0]
    uid = str(user.get("user_id") or "")
    owned = [
        r for r in rosters
        if str(r.get("owner_id") or "") == uid
        or uid in {str(x) for x in (r.get("co_owners") or [])}
    ]
    return (owned[0] if len(owned) == 1 else None), user


def projection_source_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "UNAVAILABLE"
    decision = numeric(row.get("decision_weekly_projection"))
    if decision is None:
        return "UNAVAILABLE"
    if bool(row.get("weekly_activation_eligible")) and numeric(row.get("fie_weekly_projection")) is not None:
        return "FIE_GOVERNED"
    if numeric(row.get("sleeper_weekly_projection")) is not None or "SLEEPER" in str(row.get("projection_source") or "").upper():
        return "SLEEPER_FALLBACK"
    return "EXISTING_DECISION_PROJECTION"


def player_action_record(player_id: str, row: dict[str, Any] | None, catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c = catalog.get(str(player_id)) or {}
    return {
        "player_id": str(player_id),
        "player_name": player_name(str(player_id), row, catalog),
        "position": roster_position(str(player_id), row, catalog),
        "team": (row or {}).get("team") or c.get("team"),
        "opponent": (row or {}).get("opponent"),
        "weekly_projection": numeric((row or {}).get("decision_weekly_projection")),
        "projection_source": (row or {}).get("projection_source"),
        "projection_source_class": projection_source_class(row),
        "fie_weekly_projection": numeric((row or {}).get("fie_weekly_projection")),
        "sleeper_weekly_projection": numeric((row or {}).get("sleeper_weekly_projection")),
        "weekly_activation_eligible": bool((row or {}).get("weekly_activation_eligible")),
        "p10": numeric((row or {}).get("p10")) if bool((row or {}).get("weekly_activation_eligible")) else None,
        "p90": numeric((row or {}).get("p90")) if bool((row or {}).get("weekly_activation_eligible")) else None,
        "confidence": numeric((row or {}).get("confidence")),
        "injury_status": injury_status(str(player_id), catalog),
        "status": active_status(str(player_id), catalog),
    }


def source_mix(ids: list[str], index: dict[str, dict[str, Any]]) -> dict[str, int]:
    c = Counter(projection_source_class(index.get(pid)) for pid in ids)
    return {k: int(c.get(k, 0)) for k in ("FIE_GOVERNED", "SLEEPER_FALLBACK", "EXISTING_DECISION_PROJECTION", "UNAVAILABLE")}


def injury_alerts(roster: dict[str, Any], index: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    starter_ids = set(valid_ids(roster.get("starters")))
    alerts: list[dict[str, Any]] = []
    for pid in valid_ids(roster.get("players")):
        inj = (injury_status(pid, catalog) or "").upper()
        if not inj:
            continue
        if inj in {"OUT", "IR", "PUP", "SUSPENDED", "NA"}:
            severity = "URGENT" if pid in starter_ids else "HIGH"
        elif inj == "DOUBTFUL":
            severity = "HIGH" if pid in starter_ids else "WATCH"
        elif inj == "QUESTIONABLE":
            severity = "WATCH"
        else:
            severity = "WATCH"
        rec = player_action_record(pid, index.get(pid), catalog)
        rec.update({"severity": severity, "starter": pid in starter_ids, "action": "CHECK_STATUS"})
        alerts.append(rec)
    order = {"URGENT": 0, "HIGH": 1, "WATCH": 2}
    alerts.sort(key=lambda x: (order.get(str(x.get("severity")), 9), 0 if x.get("starter") else 1, str(x.get("player_name"))))
    return alerts


def lineup_upgrade_alerts(
    roster: dict[str, Any],
    core: dict[str, Any],
    index: dict[str, dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    *,
    minimum_delta: float = 0.25,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    fmt = str(core.get("format") or "").upper()
    if fmt in BESTBALL_FORMATS:
        return "NOT_APPLICABLE_BEST_BALL", [], {"reason": "best-ball lineup selection is automatic"}

    slots = starter_slots(core)
    raw_starters = list(roster.get("starters") or [])
    # Sleeper uses "0" to preserve empty starter-slot position, so do not strip it before pairing.
    starters = [str(x) if x is not None else "0" for x in raw_starters]
    if len(starters) != len(slots):
        return "BLOCKED_STARTER_SLOT_MAPPING", [], {"starter_count": len(starters), "slot_count": len(slots)}

    roster_ids = valid_ids(roster.get("players"))
    starter_ids = {pid for pid in starters if pid and pid != "0"}
    bench_ids = [pid for pid in roster_ids if pid not in starter_ids]

    candidate_pairs: list[tuple[float, str, int, str]] = []
    missing_projection_ids: set[str] = set()
    empty_slots: list[dict[str, Any]] = []
    for i, (slot, starter_id) in enumerate(zip(slots, starters)):
        if starter_id == "0" or not starter_id:
            empty_slots.append({"slot": slot, "slot_index": i})
            continue
        starter_row = index.get(starter_id)
        starter_proj = numeric((starter_row or {}).get("decision_weekly_projection"))
        if starter_proj is None:
            missing_projection_ids.add(starter_id)
            continue
        for bench_id in bench_ids:
            bench_row = index.get(bench_id)
            bench_proj = numeric((bench_row or {}).get("decision_weekly_projection"))
            if bench_proj is None:
                missing_projection_ids.add(bench_id)
                continue
            if not eligible(slot, roster_position(bench_id, bench_row, catalog)):
                continue
            delta = bench_proj - starter_proj
            if delta > float(minimum_delta):
                candidate_pairs.append((delta, bench_id, i, starter_id))

    candidate_pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    used_bench: set[str] = set()
    used_slots: set[int] = set()
    actions: list[dict[str, Any]] = []
    for delta, bench_id, slot_index, starter_id in candidate_pairs:
        if bench_id in used_bench or slot_index in used_slots:
            continue
        used_bench.add(bench_id)
        used_slots.add(slot_index)
        incoming = player_action_record(bench_id, index.get(bench_id), catalog)
        outgoing = player_action_record(starter_id, index.get(starter_id), catalog)
        actions.append({
            "action": "START_OVER",
            "slot": slots[slot_index],
            "slot_index": slot_index,
            "projection_delta": round(float(delta), 4),
            "start": incoming,
            "bench": outgoing,
            "basis": "existing decision_weekly_projection; submitted-lineup positive-delta alert",
            "authoritative_lineup_optimizer": False,
        })

    if empty_slots:
        status = "ACTION_REQUIRED_EMPTY_STARTER_SLOT"
    elif actions:
        status = "ACTION_AVAILABLE"
    elif missing_projection_ids:
        status = "PARTIAL_MISSING_PROJECTIONS"
    else:
        status = "NO_CHANGE_IDENTIFIED"
    return status, actions, {
        "empty_slots": empty_slots,
        "missing_projection_player_ids": sorted(missing_projection_ids),
        "submitted_starter_count": len(starter_ids),
        "bench_count": len(bench_ids),
        "minimum_delta": float(minimum_delta),
    }


def waiver_watchlist(
    roster: dict[str, Any],
    core: dict[str, Any],
    current: dict[str, Any],
    index: dict[str, dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    *,
    limit: int = 10,
) -> tuple[str, list[dict[str, Any]]]:
    rosters, _ = sleeper_data(core)
    owned = {pid for r in rosters for pid in valid_ids(r.get("players"))}
    rosterable = set()
    for slot in starter_slots(core):
        rosterable.update(SLOT_ELIGIBILITY.get(slot, {normalize_position(slot)}))
    rows: list[dict[str, Any]] = []
    for pid, row in index.items():
        # Only the preferred Sleeper identity should create a free-agent row.
        if str(row.get("sleeper_id") or "") != pid:
            continue
        if pid in owned:
            continue
        pos = roster_position(pid, row, catalog)
        if rosterable and pos not in rosterable:
            continue
        c_status = (active_status(pid, catalog) or "").upper()
        inj = (injury_status(pid, catalog) or "").upper()
        if c_status == "INACTIVE" or inj in {"IR", "PUP", "SUSPENDED", "NA"}:
            continue
        weekly = numeric(row.get("decision_weekly_projection"))
        next3 = numeric(row.get("waiver_next3_projection"))
        waiver_ready = bool(row.get("waiver_activation_eligible")) and next3 is not None
        if weekly is None and not waiver_ready:
            continue
        rec = player_action_record(pid, row, catalog)
        rec.update({
            "waiver_model_ready": waiver_ready,
            "next3_projection": next3 if waiver_ready else None,
            "waiver_feature_coverage": numeric(row.get("waiver_feature_coverage")) if waiver_ready else None,
            "action": "REVIEW" if waiver_ready else "WATCH_ONLY",
            "bid_recommendation": None,
            "drop_recommendation": None,
        })
        rows.append(rec)

    ready = [x for x in rows if x["waiver_model_ready"]]
    if ready:
        ready.sort(key=lambda x: (-(numeric(x.get("next3_projection")) or -1e9), -(numeric(x.get("weekly_projection")) or -1e9), str(x.get("player_name"))))
        return "WAIVER_MODEL_READY", ready[:limit]
    fallback = [x for x in rows if numeric(x.get("weekly_projection")) is not None]
    fallback.sort(key=lambda x: (-(numeric(x.get("weekly_projection")) or -1e9), str(x.get("player_name"))))
    return ("WATCH_ONLY_NO_WAIVER_MODEL" if fallback else "NO_AVAILABLE_EVIDENCE"), fallback[:limit]


def prior_evaluation(root: Path, season: int, week: int, league_id: str) -> dict[str, Any] | None:
    if week <= 1:
        return None
    p = root / f"data/research/evaluation/{season}/weeks/week-{week-1}/league-{league_id}/evaluation-v1.json"
    x = read_json(p, None)
    if not isinstance(x, dict):
        return None
    keep = {k: x.get(k) for k in ("schema", "schema_version", "status", "league_id", "season", "week", "metrics") if k in x}
    return keep or None


def blocker_report(league_id: str, league_name: str, fmt: str, season: int | None, week: int | None, code: str, detail: Any = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA_LEAGUE,
        "league_id": league_id,
        "league_name": league_name,
        "format": fmt,
        "season": season,
        "week": week,
        "status": code,
        "blocker": {"code": code, "detail": detail},
        "actions": {"injury_alerts": [], "lineup": [], "waiver_watchlist": []},
        "governance": governance_payload(),
    }


def governance_payload() -> dict[str, Any]:
    return {
        "research_decision_support_only": True,
        "production_model": "M9",
        "production_model_changed": False,
        "m10_activation_changed": False,
        "canonical_rankings_changed": False,
        "app_runtime_changed": False,
        "adp_used_as_football_feature": False,
        "uses_existing_decision_weekly_projection": True,
        "zero_imputes_missing_weekly_projection": False,
        "transaction_execution": False,
        "faab_optimization": False,
        "add_drop_optimization": False,
        "window_1d_reserved_for_waiver_optimization": True,
    }


def build_league_report(
    root: Path,
    league_id: str,
    registry_row: dict[str, Any],
    *,
    username: str,
    as_of: datetime,
    target_season: int | None = None,
    target_week: int | None = None,
    minimum_lineup_delta: float = 0.25,
    waiver_limit: int = 10,
) -> dict[str, Any]:
    lid = str(league_id)
    league_root = root / "data/research/leagues" / lid
    league_name = str(registry_row.get("league_name") or lid)
    fmt = str(registry_row.get("format") or "UNKNOWN").upper()
    profile_path = league_root / "profile.json"
    current_path = league_root / "current/milestone5_current.json"
    manifest_path = league_root / "app/manifest.json"

    try:
        profile = read_json(profile_path, {}) or {}
        if not current_path.is_file():
            return blocker_report(lid, league_name, fmt, target_season, target_week, "BLOCKED_CURRENT_SNAPSHOT_MISSING")
        current = load_current(current_path, root=root)
        season = int(current.get("season") or target_season or 0) or None
        week = int(current.get("week") or target_week or 0) or None
        if target_season is not None and season != int(target_season):
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_SEASON_MISMATCH", {"target": target_season, "current": season})
        if target_week is not None and week != int(target_week):
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_WEEK_MISMATCH", {"target": target_week, "current": week})
        if current.get("target_week_realised_stats_excluded") is not True:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_REALIZED_STATS_GUARD")
        if current.get("profile_current_match") is False:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_PROFILE_DRIFT", current.get("profile_diff") or {})

        declared_fp = str(profile.get("profile_fingerprint") or "")
        registry_fp = str(registry_row.get("profile_fingerprint") or "")
        current_fp = str(current.get("profile_fingerprint") or "")
        if declared_fp and registry_fp and declared_fp != registry_fp:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_REGISTRY_PROFILE_MISMATCH")
        if declared_fp and current_fp and declared_fp != current_fp:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_CURRENT_PROFILE_MISMATCH")

        generated = parse_dt(current.get("generated_at"))
        if generated is None:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_CURRENT_TIMESTAMP_MISSING")
        max_age_hours = numeric(current.get("snapshot_max_age_hours")) or 18.0
        age_hours = (as_of - generated).total_seconds() / 3600.0
        if age_hours < -0.25:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_CURRENT_TIMESTAMP_IN_FUTURE")
        if age_hours > max_age_hours:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_STALE_CURRENT_SNAPSHOT", {"age_hours": round(age_hours, 3), "max_age_hours": max_age_hours})

        if not manifest_path.is_file():
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_APP_MANIFEST_MISSING")
        _, core = manifest_core(root, manifest_path)
        core_fp = str(core.get("profile_fingerprint") or "")
        if declared_fp and core_fp and declared_fp != core_fp:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_APP_PROFILE_MISMATCH")
        if str(core.get("league_id") or "") != lid:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_APP_LEAGUE_MISMATCH")

        catalog = player_catalog(root, core)
        index = current_index(current)
        roster, user = managed_roster(core, username)
        if roster is None:
            return blocker_report(lid, league_name, fmt, season, week, "BLOCKED_MANAGED_ROSTER_UNRESOLVED", {"username": username})

        roster_ids = valid_ids(roster.get("players"))
        inj = injury_alerts(roster, index, catalog)
        lineup_status, lineup_actions, lineup_diag = lineup_upgrade_alerts(
            roster, core, index, catalog, minimum_delta=minimum_lineup_delta
        )
        waiver_status, waiver_rows = waiver_watchlist(
            roster, core, current, index, catalog, limit=waiver_limit
        )

        urgent = sum(1 for x in inj if x.get("severity") in {"URGENT", "HIGH"} and x.get("starter"))
        action_count = len(lineup_actions) + urgent
        if lineup_status == "ACTION_REQUIRED_EMPTY_STARTER_SLOT":
            action_count += len(lineup_diag.get("empty_slots") or [])
        status = "ACTION_REQUIRED" if action_count else "READY_NO_URGENT_ACTION"
        if lineup_status.startswith("PARTIAL") or waiver_status == "NO_AVAILABLE_EVIDENCE":
            status = "PARTIAL_EVIDENCE" if status != "ACTION_REQUIRED" else status

        kickoff = parse_dt(((current.get("kickoff") or {}).get("first_kickoff_utc")))
        timing = {
            "current_generated_at": generated.isoformat(),
            "as_of_utc": as_of.isoformat(),
            "age_hours": round(age_hours, 3),
            "max_age_hours": max_age_hours,
            "first_kickoff_utc": kickoff.isoformat() if kickoff else None,
            "before_first_kickoff": (as_of < kickoff) if kickoff else None,
        }

        # If a report is generated after the first kickoff, retain evidence but do not
        # present lineup swaps as currently executable actions.
        if kickoff and as_of >= kickoff and lineup_actions:
            lineup_status = "LOCKED_AFTER_FIRST_KICKOFF"
            for row in lineup_actions:
                row["action"] = "REVIEW_ONLY_AFTER_KICKOFF"
                row["execution_guard"] = "first kickoff has passed; player-specific lock state is not reconstructed here"

        user_name = str((user or {}).get("display_name") or username)
        report = {
            "schema": SCHEMA_LEAGUE,
            "league_id": lid,
            "league_name": league_name,
            "format": fmt,
            "season": season,
            "week": week,
            "status": status,
            "managed_user": user_name,
            "managed_roster_id": roster.get("roster_id"),
            "timing": timing,
            "evidence": {
                "current_snapshot": str(current_path.relative_to(root)),
                "app_manifest": str(manifest_path.relative_to(root)),
                "profile": str(profile_path.relative_to(root)),
                "profile_fingerprint": declared_fp or None,
                "scoring_signature": current.get("scoring_signature"),
                "target_week_realised_stats_excluded": True,
                "projection_source_mix_owned_roster": source_mix(roster_ids, index),
                "fie_weekly_activation_eligible_total": int(((current.get("summary") or {}).get("weekly_activation_eligible") or 0)),
                "waiver_activation_eligible_total": int(((current.get("summary") or {}).get("waiver_activation_eligible") or 0)),
                "source_health_reason": ((current.get("source_health") or {}).get("reason")),
            },
            "actions": {
                "injury_alerts": inj,
                "lineup": lineup_actions,
                "waiver_watchlist": waiver_rows,
            },
            "action_status": {
                "lineup": lineup_status,
                "lineup_diagnostics": lineup_diag,
                "waiver_watchlist": waiver_status,
                "urgent_or_high_starter_injury_alerts": urgent,
                "action_count": action_count,
            },
            "prior_week_evaluation": prior_evaluation(root, int(season or 0), int(week or 0), lid) if season and week else None,
            "operational_ux": {
                "priority_order": [
                    "Resolve empty or unavailable starter slots",
                    "Check urgent/high starter injury alerts",
                    "Review positive submitted-lineup projection deltas",
                    "Review available-player watchlist",
                ],
                "waiver_note": "Window 1C does not size bids or choose an optimized add/drop pair; Window 1D owns that decision.",
                "projection_note": "FIE_GOVERNED and SLEEPER_FALLBACK are labeled separately; missing projections are never treated as zero.",
            },
            "governance": governance_payload(),
        }
        return report
    except EvidenceError as exc:
        text = str(exc)
        code = "BLOCKED_EVIDENCE_ERROR"
        if text.startswith("APP_CORE_DRIFT"):
            code = "BLOCKED_APP_CORE_DRIFT"
        elif text.startswith("CURRENT_SNAPSHOT_HYDRATION_FAILED"):
            code = "BLOCKED_CURRENT_SNAPSHOT_HYDRATION"
        return blocker_report(lid, league_name, fmt, target_season, target_week, code, text)


def infer_week(root: Path, registry: dict[str, Any], season: int | None) -> int | None:
    weeks: list[int] = []
    for lid, row in sorted((registry.get("leagues") or {}).items()):
        if not isinstance(row, dict) or not row.get("enabled", True):
            continue
        x = read_json(root / f"data/research/leagues/{lid}/current/milestone5_current.json", {}) or {}
        if season is not None and int(x.get("season") or 0) != int(season):
            continue
        w = x.get("week")
        if isinstance(w, int) or (isinstance(w, str) and w.isdigit()):
            weeks.append(int(w))
    if not weeks:
        return None
    counts = Counter(weeks)
    return sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))[0][0]


def markdown_portfolio(report: dict[str, Any]) -> str:
    lines = [
        f"# FIE Weekly Actions — {report.get('season')} Week {report.get('week')}",
        "",
        f"Built for **{report.get('managed_username')}** from governed current snapshots.",
        "",
        "> This is an operational decision-support report. It does not change M9, canonical rankings, or execute transactions. Window 1D owns optimized add/drop and FAAB bidding.",
        "",
        "## Portfolio summary",
        "",
        f"- Enabled leagues: **{report.get('enabled_league_count')}**",
        f"- Ready/actionable: **{report.get('ready_count')}**",
        f"- Blocked/partial: **{report.get('blocked_count')}**",
        f"- Immediate action leagues: **{report.get('action_required_count')}**",
        "",
    ]
    for league in report.get("leagues") or []:
        lines += [f"## {league.get('league_name')} ({league.get('format')})", "", f"Status: **{league.get('status')}**"]
        if league.get("blocker"):
            lines += [f"", f"Blocked: `{league['blocker'].get('code')}`", ""]
            continue
        action_status = league.get("action_status") or {}
        evidence = league.get("evidence") or {}
        lines += [
            "",
            f"- Roster: **{league.get('managed_roster_id')}**",
            f"- Lineup: **{action_status.get('lineup')}**",
            f"- Waiver watchlist: **{action_status.get('waiver_watchlist')}**",
            f"- Projection mix: `{evidence.get('projection_source_mix_owned_roster')}`",
        ]
        alerts = (league.get("actions") or {}).get("injury_alerts") or []
        if alerts:
            lines += ["", "### Injury/status checks"]
            for x in alerts[:8]:
                tag = "starter" if x.get("starter") else "bench"
                lines.append(f"- **{x.get('severity')}** {x.get('player_name')} ({tag}) — {x.get('injury_status')}")
        lineup = (league.get("actions") or {}).get("lineup") or []
        if lineup:
            lines += ["", "### Lineup alerts"]
            for x in lineup[:8]:
                inc, out = x.get("start") or {}, x.get("bench") or {}
                lines.append(f"- `{x.get('slot')}`: **{inc.get('player_name')} over {out.get('player_name')}** — +{float(x.get('projection_delta') or 0):.1f} projected pts")
        waiver = (league.get("actions") or {}).get("waiver_watchlist") or []
        if waiver:
            lines += ["", "### Available-player watchlist"]
            for x in waiver[:8]:
                n3 = x.get("next3_projection")
                n3t = f", next-3 {float(n3):.1f}" if numeric(n3) is not None else ""
                lines.append(f"- **{x.get('player_name')}** ({x.get('position')}) — week {numeric(x.get('weekly_projection')) if numeric(x.get('weekly_projection')) is not None else '—'}{n3t} — {x.get('action')}")
        prior = league.get("prior_week_evaluation")
        if isinstance(prior, dict):
            lines += ["", f"Prior-week evaluation: **{prior.get('status')}** — `{prior.get('metrics')}`"]
        lines.append("")
    lines += [
        "## Interpretation guardrails",
        "",
        "- No missing projection is treated as zero.",
        "- Sleeper fallback is explicitly labeled and is not counted as a governed FIE prediction for Window 1B evaluation.",
        "- Lineup alerts compare the currently submitted lineup with eligible bench alternatives; the production browser lineup optimizer remains authoritative.",
        "- No FAAB bid or optimized add/drop pair is produced in Window 1C.",
    ]
    return "\n".join(lines) + "\n"


def build_portfolio(
    root: Path,
    *,
    season: int,
    week: int | None,
    as_of: datetime,
    username: str | None = None,
    league_id: str | None = None,
    minimum_lineup_delta: float = 0.25,
    waiver_limit: int = 10,
) -> dict[str, Any]:
    registry = read_json(root / "data/research/leagues/registry.json", {}) or {}
    portfolio = read_json(root / "config/league-portfolio.json", {}) or {}
    managed_username = str(username or portfolio.get("sleeper_username") or "").strip()
    if not managed_username:
        raise EvidenceError("PORTFOLIO_USERNAME_MISSING")
    resolved_week = int(week) if week is not None else infer_week(root, registry, season)
    if resolved_week is None:
        raise EvidenceError("TARGET_WEEK_UNRESOLVED")

    league_rows = registry.get("leagues") if isinstance(registry.get("leagues"), dict) else {}
    selected: list[tuple[str, dict[str, Any]]] = []
    for lid, row in sorted(league_rows.items()):
        if not isinstance(row, dict) or not row.get("enabled", True):
            continue
        if league_id and str(lid) != str(league_id):
            continue
        selected.append((str(lid), row))
    if league_id and not selected:
        raise EvidenceError(f"LEAGUE_NOT_ENABLED_OR_UNKNOWN:{league_id}")

    reports = [
        build_league_report(
            root, lid, row, username=managed_username, as_of=as_of,
            target_season=season, target_week=resolved_week,
            minimum_lineup_delta=minimum_lineup_delta, waiver_limit=waiver_limit,
        )
        for lid, row in selected
    ]
    blocked = [x for x in reports if str(x.get("status") or "").startswith("BLOCKED") or x.get("status") == "PARTIAL_EVIDENCE"]
    ready = [x for x in reports if x not in blocked]
    action_required = [x for x in reports if x.get("status") == "ACTION_REQUIRED"]
    return {
        "schema": SCHEMA_PORTFOLIO,
        "season": int(season),
        "week": int(resolved_week),
        "as_of_utc": as_of.isoformat(),
        "managed_username": managed_username,
        "enabled_league_count": len(reports),
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "action_required_count": len(action_required),
        "status_counts": dict(sorted(Counter(str(x.get("status") or "UNKNOWN") for x in reports).items())),
        "leagues": reports,
        "governance": governance_payload(),
    }


def output_paths(root: Path, season: int, week: int) -> tuple[Path, Path]:
    base = root / f"data/research/evaluation/{season}/weeks/week-{week}"
    return base / "weekly-actions-portfolio-v1.json", base / "weekly-actions-portfolio-v1.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build FIE Window 1C weekly action decision-support report")
    p.add_argument("portfolio", nargs="?")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--week", type=int, default=None)
    p.add_argument("--league-id", default="")
    p.add_argument("--username", default="")
    p.add_argument("--as-of-utc", default="")
    p.add_argument("--minimum-lineup-delta", type=float, default=0.25)
    p.add_argument("--waiver-limit", type=int, default=10)
    p.add_argument("--json-output", default="")
    p.add_argument("--markdown-output", default="")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    as_of = parse_dt(args.as_of_utc) if args.as_of_utc else utc_now()
    if as_of is None:
        raise SystemExit("Invalid --as-of-utc")
    report = build_portfolio(
        root,
        season=args.season,
        week=args.week,
        as_of=as_of,
        username=args.username or None,
        league_id=args.league_id or None,
        minimum_lineup_delta=args.minimum_lineup_delta,
        waiver_limit=max(1, int(args.waiver_limit)),
    )
    default_json, default_md = output_paths(root, report["season"], report["week"])
    json_out = Path(args.json_output) if args.json_output else default_json
    md_out = Path(args.markdown_output) if args.markdown_output else default_md
    if not json_out.is_absolute():
        json_out = root / json_out
    if not md_out.is_absolute():
        md_out = root / md_out
    write_json(json_out, report)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(markdown_portfolio(report), encoding="utf-8")
    print(f"Window 1C weekly actions: season={report['season']} week={report['week']} leagues={report['enabled_league_count']} ready={report['ready_count']} blocked={report['blocked_count']} actions={report['action_required_count']}")
    print(json_out)
    print(md_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

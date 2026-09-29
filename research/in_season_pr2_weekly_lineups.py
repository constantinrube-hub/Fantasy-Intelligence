#!/usr/bin/env python3
"""In-Season PR2: fail-closed exact weekly lineup research producer.

The producer is intentionally research-only.  It reads the same verified
current-snapshot and app-core evidence as Window 1C, then delegates every slot
decision to ``weekly_lineup_decision_support.exact_lineup``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:  # Supports both ``python research/file.py`` and package-style imports.
    from weekly_lineup_decision_support import (
        LineupEvidenceError,
        canonical_player_id,
        eligible_for_slot,
        exact_lineup,
        load_runtime_contract,
        numeric,
        player_position,
        starter_slot_instances,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised by repository callers
    from research.weekly_lineup_decision_support import (
        LineupEvidenceError,
        canonical_player_id,
        eligible_for_slot,
        exact_lineup,
        load_runtime_contract,
        numeric,
        player_position,
        starter_slot_instances,
    )


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_LEAGUE = "fie-in-season-pr2-weekly-lineup-v1"
SCHEMA_PORTFOLIO = "fie-in-season-pr2-weekly-lineup-portfolio-v1"
BEST_BALL = {"REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"}
UNAVAILABLE = {"OUT", "IR", "PUP", "SUSPENDED", "INACTIVE", "NA"}
CONTINGENCY = {"QUESTIONABLE", "DOUBTFUL"}


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: Any) -> datetime | None:
    try:
        text = str(value).replace("Z", "+00:00")
        result = datetime.fromisoformat(text)
        return (result if result.tzinfo else result.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception:
        return None


def current_snapshot(path: Path, root: Path) -> dict[str, Any]:
    try:
        try:
            from current_snapshot_storage import load_current_snapshot  # type: ignore
        except ModuleNotFoundError:
            from research.current_snapshot_storage import load_current_snapshot  # type: ignore
        return load_current_snapshot(path, root=root)
    except Exception as exc:
        raise LineupEvidenceError(f"BLOCKED_CURRENT_SNAPSHOT_HYDRATION:{type(exc).__name__}") from exc


def verified_core(root: Path, manifest_path: Path) -> tuple[Path, dict[str, Any]]:
    manifest = read_json(manifest_path, {}) or {}
    core = manifest.get("core") if isinstance(manifest.get("core"), dict) else None
    if not isinstance(core, dict):
        raise LineupEvidenceError("BLOCKED_APP_MANIFEST_CORE_MISSING")
    rel, expected = str(core.get("path") or ""), str(core.get("sha256") or "")
    path = (root / rel).resolve()
    if not rel or not expected or not path.is_file():
        raise LineupEvidenceError("BLOCKED_APP_CORE_MISSING")
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise LineupEvidenceError("BLOCKED_APP_CORE_PATH_OUTSIDE_REPO") from exc
    if sha256_file(path) != expected:
        raise LineupEvidenceError("BLOCKED_APP_CORE_DRIFT")
    content = read_json(path, {}) or {}
    if not isinstance(content, dict):
        raise LineupEvidenceError("BLOCKED_APP_CORE_INVALID")
    return path, content


def catalog(root: Path, core: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rel = str(((core.get("shared") or {}).get("player_catalog") or ""))
    path = (root / rel).resolve()
    if not rel or not path.is_file():
        return {}
    rows = (read_json(path, {}) or {}).get("players")
    return rows if isinstance(rows, dict) else {}


def current_index(current: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in current.get("players") or []:
        if not isinstance(row, dict):
            continue
        for key in (row.get("sleeper_id"), row.get("canonical_player_id")):
            if key is not None and str(key).strip():
                out.setdefault(str(key).strip(), row)
        if str(row.get("position_model") or "").upper() in {"DEF", "DST", "D/ST"} and row.get("team"):
            out.setdefault(str(row["team"]).upper(), row)
    return out


def sleeper_parts(core: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    sleeper = core.get("sleeper") if isinstance(core.get("sleeper"), dict) else {}
    league = sleeper.get("league") if isinstance(sleeper.get("league"), dict) else {}
    rosters = [x for x in (sleeper.get("rosters") or []) if isinstance(x, dict)]
    users = [x for x in (sleeper.get("users") or []) if isinstance(x, dict)]
    return league, rosters, users


def valid_ids(values: Iterable[Any] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text != "0" and text not in result:
            result.append(text)
    return result


def managed_roster(core: dict[str, Any], username: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    _, rosters, users = sleeper_parts(core)
    needle = str(username).strip().lower()
    users = [u for u in users if str(u.get("display_name") or u.get("username") or "").strip().lower() == needle]
    if len(users) != 1:
        return None, None
    user = users[0]
    uid = str(user.get("user_id") or "")
    owned = [r for r in rosters if str(r.get("owner_id") or "") == uid or uid in {str(x) for x in (r.get("co_owners") or [])}]
    return (owned[0] if len(owned) == 1 else None), user


def injury_status(pid: str, player_catalog: dict[str, dict[str, Any]]) -> str | None:
    value = (player_catalog.get(pid) or {}).get("injury_status")
    return str(value).upper().strip() if value else None


def row_for_roster_id(pid: str, index: dict[str, dict[str, Any]], player_catalog: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    row = index.get(pid) or index.get(pid.upper())
    if row is None:
        return None
    result = dict(row)
    result.setdefault("sleeper_id", pid)
    result.setdefault("position_model", (player_catalog.get(pid) or {}).get("position"))
    result.setdefault("full_name", (player_catalog.get(pid) or {}).get("full_name"))
    return result


def source_class(row: dict[str, Any]) -> str:
    if numeric(row.get("decision_weekly_projection")) is None:
        return "UNAVAILABLE"
    if bool(row.get("weekly_activation_eligible")) and numeric(row.get("fie_weekly_projection")) is not None:
        return "FIE_GOVERNED"
    if numeric(row.get("sleeper_weekly_projection")) is not None or "SLEEPER" in str(row.get("projection_source") or "").upper():
        return "SLEEPER_FALLBACK"
    return "EXISTING_DECISION_PROJECTION"


def blocker(lid: str, name: str, fmt: str, season: int | None, week: int | None, code: str, detail: Any = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA_LEAGUE,
        "league_id": lid,
        "league_name": name,
        "format": fmt,
        "season": season,
        "week": week,
        "status": code,
        "blocker": {"code": code, "detail": detail},
        "primary_lineup": None,
        "governance": governance(),
    }


def governance() -> dict[str, Any]:
    return {
        "research_decision_support_only": True,
        "production_model": "M9",
        "production_model_changed": False,
        "m10_activation_changed": False,
        "canonical_rankings_changed": False,
        "app_runtime_changed": False,
        "transaction_or_lineup_execution": False,
        "adp_used_as_lineup_feature": False,
        "opponent_aware_lineup_actionable": False,
    }


def submitted_lineup(roster: dict[str, Any], slots: list[dict[str, Any]], index: dict[str, dict[str, Any]], player_catalog: dict[str, dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    starters = [str(x) if x is not None else "0" for x in (roster.get("starters") or [])]
    if len(starters) != len(slots):
        return {"status": "BLOCKED_STARTER_SLOT_MAPPING", "detail": {"starter_count": len(starters), "slot_count": len(slots)}, "assignment": [], "total": None}
    rows, total, issues = [], 0.0, []
    for slot, pid in zip(slots, starters):
        if pid == "0" or not pid:
            issues.append({"code": "EMPTY_SUBMITTED_SLOT", "slot": slot["slot"], "slot_index": slot["slot_index"]})
            continue
        row = row_for_roster_id(pid, index, player_catalog)
        if row is None:
            issues.append({"code": "SUBMITTED_PLAYER_UNRESOLVED", "player_id": pid})
            continue
        player_id = canonical_player_id(row)
        if player_id is None:
            issues.append({"code": "SUBMITTED_PLAYER_IDENTITY_UNRESOLVED", "player_id": pid})
            continue
        if not eligible_for_slot(player_position(row, contract), slot["slot"], contract):
            issues.append({"code": "SUBMITTED_PLAYER_ILLEGAL_FOR_SLOT", "player_id": player_id, "slot": slot["slot"], "slot_index": slot["slot_index"]})
            continue
        value = numeric(row.get("decision_weekly_projection"))
        if value is None:
            issues.append({"code": "SUBMITTED_PLAYER_PROJECTION_UNAVAILABLE", "player_id": player_id})
            continue
        total += value
        rows.append({"slot": slot["slot"], "slot_index": slot["slot_index"], "player_id": player_id, "position": player_position(row, contract), "value": round(value, 6)})
    return {"status": "COMPLETE" if not issues else "PARTIAL", "detail": issues, "assignment": rows, "total": round(total, 6) if not issues else None}


def changes(primary: dict[str, Any], submitted: dict[str, Any]) -> list[dict[str, Any]]:
    if submitted.get("status") != "COMPLETE":
        return []
    previous = {x["slot_index"]: x["player_id"] for x in submitted["assignment"]}
    previous_slots = {x["player_id"]: x["slot_index"] for x in submitted["assignment"]}
    out = []
    for row in primary.get("assignment") or []:
        old = previous.get(row["slot_index"])
        if old == row["player_id"]:
            continue
        action = "MOVE_SLOT" if row["player_id"] in previous_slots else "START_OVER"
        out.append({"action": action, "slot": row["slot"], "slot_index": row["slot_index"], "start_player_id": row["player_id"], "replace_player_id": old, "from_slot_index": previous_slots.get(row["player_id"]), "basis": "exact global legal assignment"})
    return out


def floor_advisory(players: list[dict[str, Any]], roster_positions: list[Any], fmt: str, root: Path) -> dict[str, Any] | None:
    if fmt != "CHOPPED":
        return None
    if any(not bool(p.get("weekly_activation_eligible")) or numeric(p.get("p10")) is None for p in players):
        return {"status": "UNAVAILABLE_INCOMPLETE_GOVERNED_INTERVAL_COVERAGE"}
    result = exact_lineup(players, roster_positions, value_key="p10", root=root)
    result["status"] = "SURVIVAL_FLOOR_ADVISORY"
    result["actionable"] = False
    result["basis"] = "maximize governed P10, tie handling delegated to deterministic exact assignment"
    return result


def build_league(root: Path, league_id: str, registry_row: dict[str, Any], *, username: str, target_season: int | None = None, target_week: int | None = None) -> dict[str, Any]:
    root = root.resolve()
    lid = str(league_id)
    league_root = root / "data/research/leagues" / lid
    name = str(registry_row.get("league_name") or lid)
    fmt = str(registry_row.get("format") or "UNKNOWN").upper()
    current_path = league_root / "current/milestone5_current.json"
    manifest_path = league_root / "app/manifest.json"
    profile_path = league_root / "profile.json"
    try:
        if not current_path.is_file():
            return blocker(lid, name, fmt, target_season, target_week, "BLOCKED_CURRENT_SNAPSHOT_MISSING")
        current = current_snapshot(current_path, root)
        season, week = int(current.get("season") or 0) or None, int(current.get("week") or 0) or None
        if target_season is not None and season != target_season:
            return blocker(lid, name, fmt, season, week, "BLOCKED_SEASON_MISMATCH")
        if target_week is not None and week != target_week:
            return blocker(lid, name, fmt, season, week, "BLOCKED_WEEK_MISMATCH")
        if current.get("target_week_realised_stats_excluded") is not True:
            return blocker(lid, name, fmt, season, week, "BLOCKED_REALIZED_STATS_GUARD")
        if current.get("profile_current_match") is False:
            return blocker(lid, name, fmt, season, week, "BLOCKED_PROFILE_DRIFT", current.get("profile_diff") or {})
        if not manifest_path.is_file() or not profile_path.is_file():
            return blocker(lid, name, fmt, season, week, "BLOCKED_LEAGUE_EVIDENCE_MISSING")
        profile = read_json(profile_path, {}) or {}
        core_path, core = verified_core(root, manifest_path)
        if str(core.get("league_id") or "") != lid:
            return blocker(lid, name, fmt, season, week, "BLOCKED_APP_LEAGUE_MISMATCH")
        if str(profile.get("profile_fingerprint") or "") != str(current.get("profile_fingerprint") or ""):
            return blocker(lid, name, fmt, season, week, "BLOCKED_PROFILE_BINDING_MISMATCH")
        contract, contract_sha = load_runtime_contract(root)
        league, _, _ = sleeper_parts(core)
        roster_positions = league.get("roster_positions") if isinstance(league.get("roster_positions"), list) else []
        slots = starter_slot_instances(roster_positions, contract)
        roster, user = managed_roster(core, username)
        if roster is None:
            return blocker(lid, name, fmt, season, week, "BLOCKED_MANAGED_ROSTER_UNRESOLVED", {"username": username})
        if fmt in BEST_BALL:
            return {
                "schema": SCHEMA_LEAGUE, "league_id": lid, "league_name": name, "format": fmt, "season": season, "week": week,
                "status": "NOT_APPLICABLE_AUTOMATIC_LINEUP", "managed_roster_id": roster.get("roster_id"),
                "primary_lineup": None, "governance": governance(),
            }
        player_catalog, index = catalog(root, core), current_index(current)
        unresolved, inactive, active = [], [], []
        for pid in valid_ids(roster.get("players")):
            row = row_for_roster_id(pid, index, player_catalog)
            if row is None:
                unresolved.append(pid)
                continue
            status = injury_status(pid, player_catalog)
            row["injury_status"] = status
            if status in UNAVAILABLE:
                inactive.append({"player_id": canonical_player_id(row), "sleeper_id": pid, "injury_status": status})
                continue
            active.append(row)
        if unresolved:
            return blocker(lid, name, fmt, season, week, "BLOCKED_ROSTER_PLAYER_UNRESOLVED", unresolved)
        material_missing = []
        for row in active:
            if numeric(row.get("decision_weekly_projection")) is not None:
                continue
            position = player_position(row, contract)
            if any(position in x["eligible_positions"] for x in slots):
                material_missing.append(canonical_player_id(row))
        if material_missing:
            return blocker(lid, name, fmt, season, week, "BLOCKED_MATERIAL_PROJECTION_MISSING", sorted(x for x in material_missing if x))
        primary = exact_lineup(active, roster_positions, root=root)
        if not primary["complete_assignment"]:
            return blocker(lid, name, fmt, season, week, "BLOCKED_INCOMPLETE_LEGAL_ASSIGNMENT", primary["unfilled_slots"])
        submitted = submitted_lineup(roster, slots, index, player_catalog, contract)
        contingency_rows = [row for row in active if str(row.get("injury_status") or "") in CONTINGENCY]
        contingencies = []
        for row in contingency_rows:
            player_id = canonical_player_id(row)
            alternate = exact_lineup([x for x in active if canonical_player_id(x) != player_id], roster_positions, root=root)
            contingencies.append({"scenario": "INACTIVE_CONTINGENCY", "player_id": player_id, "injury_status": row.get("injury_status"), "lineup": alternate if alternate["complete_assignment"] else None, "status": "READY" if alternate["complete_assignment"] else "BLOCKED_INCOMPLETE_LEGAL_ASSIGNMENT"})
        sources = Counter(source_class(row) for row in active)
        report = {
            "schema": SCHEMA_LEAGUE,
            "league_id": lid,
            "league_name": name,
            "format": fmt,
            "season": season,
            "week": week,
            "status": "ACTION_REQUIRED" if changes(primary, submitted) or inactive else "READY_NO_LINEUP_CHANGE",
            "managed_user": str((user or {}).get("display_name") or username),
            "managed_roster_id": roster.get("roster_id"),
            "evidence": {
                "profile": str(profile_path.relative_to(root)),
                "profile_fingerprint": profile.get("profile_fingerprint"),
                "scoring_signature": current.get("scoring_signature"),
                "current_snapshot": str(current_path.relative_to(root)),
                "current_snapshot_sha256": sha256_file(current_path),
                "app_core": str(core_path.relative_to(root)),
                "app_core_sha256": sha256_file(core_path),
                "runtime_contract_sha256": contract_sha,
                "target_week_realised_stats_excluded": True,
                "projection_source_mix_active_roster": {key: int(sources.get(key, 0)) for key in ("FIE_GOVERNED", "SLEEPER_FALLBACK", "EXISTING_DECISION_PROJECTION", "UNAVAILABLE")},
            },
            "primary_lineup": {**primary, "status": "OPTIMAL_LINEUP", "actionable": True, "basis": "exact max sum(decision_weekly_projection)"},
            "submitted_lineup": submitted,
            "actions": changes(primary, submitted),
            "official_unavailable": inactive,
            "contingencies": contingencies,
            "survival_floor_advisory": floor_advisory(active, roster_positions, fmt, root),
            "opponent_context": {"status": "NOT_YET_CAPTURED", "actionable": False},
            "lock_state": {"status": "WINDOW1C_FIRST_KICKOFF_GUARD_PRESERVED", "actionable": False},
            "governance": governance(),
        }
        return report
    except LineupEvidenceError as exc:
        return blocker(lid, name, fmt, None, None, str(exc))


def build_portfolio(root: Path = ROOT, *, season: int | None = None, week: int | None = None, league_id: str | None = None) -> dict[str, Any]:
    portfolio = read_json(root / "config/league-portfolio.json", {}) or {}
    username = str(portfolio.get("sleeper_username") or "")
    registry = (read_json(root / "data/research/leagues/registry.json", {}) or {}).get("leagues") or {}
    selected = [(str(lid), row) for lid, row in registry.items() if isinstance(row, dict) and row.get("enabled") and (league_id is None or str(lid) == str(league_id))]
    reports = [build_league(root, lid, row, username=username, target_season=season, target_week=week) for lid, row in sorted(selected)]
    statuses = Counter(str(x.get("status")) for x in reports)
    recoverable = sum(max(0.0, float((x.get("primary_lineup") or {}).get("total") or 0) - float((x.get("submitted_lineup") or {}).get("total") or 0)) for x in reports if (x.get("submitted_lineup") or {}).get("total") is not None)
    return {
        "schema": SCHEMA_PORTFOLIO,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "enabled_league_count": len(selected),
        "status_counts": dict(sorted(statuses.items())),
        "recoverable_submitted_lineup_points": round(recoverable, 6),
        "leagues": reports,
        "governance": governance(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build In-Season PR2 exact weekly lineup research output")
    parser.add_argument("mode", choices=["portfolio", "league"])
    parser.add_argument("--season", type=int)
    parser.add_argument("--week", type=int)
    parser.add_argument("--league-id")
    parser.add_argument("--output")
    args = parser.parse_args()
    output = build_portfolio(season=args.season, week=args.week, league_id=args.league_id if args.mode == "league" else None)
    if args.output:
        write_json(Path(args.output), output)
    else:
        print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Window 2C: point-in-time Availability v2 + opportunity redistribution scenarios.

This module upgrades the prospective Sleeper availability archive into a typed,
pre-kickoff research contract. It deliberately does *not* turn injury labels into
fantasy-point penalties. Confirmed absences and uncertain designations may create
opportunity-redistribution scenarios only when an explicit, pre-cutoff opportunity
baseline is supplied. Missing opportunity evidence remains missing.

Production model M9, canonical rankings, runtime projections, waiver values and
market/ADP handling are outside this module's write surface.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
AVAIL_SCHEMA = "fie-window2c-availability-v2"
REDIST_SCHEMA = "fie-window2c-redistribution-v2"
OPPORTUNITY_SCHEMA = "fie-opportunity-baseline-v1"
POSITIONS = {"QB", "RB", "WR", "TE"}

UNAVAILABLE_STATES = {"OUT", "IR", "PUP", "NFI", "SUSPENDED", "INACTIVE"}
UNCERTAIN_STATES = {"LIMITED", "QUESTIONABLE", "DOUBTFUL"}
ALL_STATES = {
    "AVAILABLE", "LIMITED", "QUESTIONABLE", "DOUBTFUL", "OUT", "IR", "PUP",
    "NFI", "SUSPENDED", "INACTIVE", "UNKNOWN",
}

TEAM_ALIASES = {
    "JAC": "JAX", "JAX": "JAX", "LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV",
}


class AvailabilityError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def compact_timestamp(value: str) -> str:
    return parse_time(value).strftime("%Y%m%dT%H%M%S%fZ")


def normalize_team(value: Any) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def first_write_json(path: Path, payload: Any) -> str:
    encoded = canonical_bytes(payload) + b"\n"
    if path.exists():
        if path.read_bytes() != encoded:
            raise AvailabilityError(f"IMMUTABLE_FIRST_WRITE_COLLISION:{path}")
        return "EXISTS_IDENTICAL"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return "CREATED"


def recursive_forbidden_key(payload: Any, forbidden: Iterable[str]) -> bool:
    forbidden_lower = tuple(x.lower() for x in forbidden)
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in forbidden_lower):
                return True
            if recursive_forbidden_key(value, forbidden_lower):
                return True
    elif isinstance(payload, list):
        return any(recursive_forbidden_key(value, forbidden_lower) for value in payload)
    return False


def normalize_availability_state(row: dict[str, Any]) -> tuple[str, str]:
    """Return a conservative typed state plus evidence class, never a probability."""
    roster = str(row.get("status") or "").strip().lower()
    injury = str(row.get("injury_status") or "").strip().lower()
    practice = " ".join(
        str(row.get(key) or "").strip().lower()
        for key in ("practice_participation", "practice_description")
    ).strip()

    # Long-term / administrative roster states first.
    combined = f"{roster} {injury}".strip()
    if "suspend" in combined:
        return "SUSPENDED", "ROSTER_STATUS"
    if "physically unable" in combined or "pup" in combined:
        return "PUP", "ROSTER_STATUS"
    if "non-football injury" in combined or "nfi" in combined:
        return "NFI", "ROSTER_STATUS"
    if "injured reserve" in combined or roster in {"ir", "injured_reserve"}:
        return "IR", "ROSTER_STATUS"

    # Official game-status designations.
    if injury in {"out", "o"}:
        return "OUT", "OFFICIAL_DESIGNATION"
    if injury in {"doubtful", "d"}:
        return "DOUBTFUL", "OFFICIAL_DESIGNATION"
    if injury in {"questionable", "q"}:
        return "QUESTIONABLE", "OFFICIAL_DESIGNATION"

    # Roster inactive is unavailable, but distinct from an injury designation.
    if roster in {"inactive", "inact"} or "inactive" in roster:
        return "INACTIVE", "ROSTER_STATUS"

    # Practice limitation alone is context, not confirmed absence.
    if "limited" in practice:
        return "LIMITED", "PRACTICE_CONTEXT"

    # Active with no contrary signal can be labeled available. Everything else stays unknown.
    if roster in {"active", "act"} and not injury:
        return "AVAILABLE", "ROSTER_STATUS"
    return "UNKNOWN", "UNKNOWN"


def discover_weather_context(root: Path, season: int, week: int, as_of: str) -> Path | None:
    base = root / "data/research/context/weather" / str(season) / f"week_{week:02d}"
    if not base.exists():
        return None
    limit = parse_time(as_of)
    candidates: list[tuple[datetime, Path]] = []
    for path in base.glob("*/context-evidence.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            observed = str((payload.get("provenance") or {}).get("generated_at") or "")
            if not observed:
                continue
            when = parse_time(observed)
            if when <= limit:
                candidates.append((when, path))
        except Exception:
            continue
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def load_games_from_context(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    games: list[dict[str, Any]] = []
    for raw in payload.get("games") or []:
        kickoff = raw.get("kickoff")
        home = normalize_team(raw.get("home_team"))
        away = normalize_team(raw.get("away_team"))
        if not kickoff or not home or not away:
            continue
        parse_time(str(kickoff))
        games.append({
            "game_id": str(raw.get("game_id") or f"{away}_{home}_{kickoff}"),
            "home_team": home,
            "away_team": away,
            "kickoff": parse_time(str(kickoff)).isoformat(),
        })
    games.sort(key=lambda row: (row["kickoff"], row["game_id"]))
    return games, {
        "path": str(path),
        "sha256": sha256_file(path),
        "generated_at": (payload.get("provenance") or {}).get("generated_at"),
        "prediction_cutoff": (payload.get("provenance") or {}).get("prediction_cutoff") or payload.get("cutoff"),
    }


def availability_snapshot_index(root: Path, season: int) -> list[dict[str, Any]]:
    base = root / "data/research/availability/sleeper" / str(season)
    rows: list[dict[str, Any]] = []
    if not base.exists():
        return rows
    for meta_path in sorted(base.glob("availability_*.jsonl.gz.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            captured = str(meta.get("captured_at") or "")
            if not captured:
                continue
            parse_time(captured)
            data_path = Path(str(meta_path)[:-10])  # strip '.meta.json'
            if not data_path.exists():
                continue
            rows.append({
                "captured_at": parse_time(captured).isoformat(),
                "availability_as_of": meta.get("availability_as_of"),
                "meta_path": meta_path,
                "data_path": data_path,
                "source": meta.get("source"),
            })
        except Exception:
            continue
    rows.sort(key=lambda x: parse_time(x["captured_at"]))
    return rows


def select_snapshot(index: list[dict[str, Any]], cutoff: str, as_of: str) -> dict[str, Any] | None:
    limit = min(parse_time(cutoff), parse_time(as_of))
    eligible = [row for row in index if parse_time(row["captured_at"]) <= limit]
    return max(eligible, key=lambda row: parse_time(row["captured_at"])) if eligible else None


def read_snapshot(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            rows.append(row)
    return rows


def build_availability_contract(
    *,
    root: Path,
    season: int,
    week: int,
    as_of: str,
    games: list[dict[str, Any]],
    schedule_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    as_of = parse_time(as_of).isoformat()
    index = availability_snapshot_index(root, season)
    cache: dict[Path, list[dict[str, Any]]] = {}
    game_by_team: dict[str, dict[str, Any]] = {}
    for game in games:
        for team, opponent, site in (
            (game["home_team"], game["away_team"], "HOME"),
            (game["away_team"], game["home_team"], "AWAY"),
        ):
            if team in game_by_team:
                raise AvailabilityError(f"TEAM_MULTIPLE_GAMES_IN_WEEK:{team}")
            game_by_team[team] = {**game, "team": team, "opponent": opponent, "site": site}

    typed_rows: list[dict[str, Any]] = []
    team_status: dict[str, dict[str, Any]] = {}
    source_bindings: dict[str, dict[str, Any]] = {}

    for team in sorted(game_by_team):
        game = game_by_team[team]
        selected = select_snapshot(index, game["kickoff"], as_of)
        if selected is None:
            team_status[team] = {
                "status": "BLOCKED_NO_PREKICKOFF_AVAILABILITY",
                "game_id": game["game_id"],
                "kickoff": game["kickoff"],
                "opponent": game["opponent"],
                "site": game["site"],
                "player_count": 0,
                "state_counts": {},
            }
            continue
        data_path = selected["data_path"]
        if data_path not in cache:
            cache[data_path] = read_snapshot(data_path)
        binding_key = str(data_path.relative_to(root)) if data_path.is_relative_to(root) else str(data_path)
        source_bindings[binding_key] = {
            "path": binding_key,
            "sha256": sha256_file(data_path),
            "meta_path": str(selected["meta_path"].relative_to(root)) if selected["meta_path"].is_relative_to(root) else str(selected["meta_path"]),
            "meta_sha256": sha256_file(selected["meta_path"]),
            "captured_at": selected["captured_at"],
            "source": selected.get("source"),
        }
        seen: set[str] = set()
        states: Counter[str] = Counter()
        for raw in cache[data_path]:
            if normalize_team(raw.get("team")) != team:
                continue
            pos = str(raw.get("position_model") or raw.get("position") or "").strip().upper()
            if pos not in POSITIONS:
                continue
            sid = str(raw.get("sleeper_id") or raw.get("player_id") or "").strip()
            if not sid:
                continue
            if sid in seen:
                raise AvailabilityError(f"DUPLICATE_PLAYER_IN_SNAPSHOT:{team}:{sid}")
            seen.add(sid)
            state, evidence_class = normalize_availability_state(raw)
            if state not in ALL_STATES:
                raise AvailabilityError(f"UNKNOWN_NORMALIZED_STATE:{state}")
            states[state] += 1
            depth = finite(raw.get("depth_chart_order"))
            typed_rows.append({
                "sleeper_id": sid,
                "full_name": raw.get("full_name"),
                "team": team,
                "position_model": pos,
                "role_family": pos,
                "availability_state": state,
                "evidence_class": evidence_class,
                "confirmed_unavailable": state in UNAVAILABLE_STATES,
                "uncertain_availability": state in UNCERTAIN_STATES,
                "injury_status_raw": raw.get("injury_status"),
                "roster_status_raw": raw.get("status"),
                "practice_participation_raw": raw.get("practice_participation"),
                "practice_description_raw": raw.get("practice_description"),
                "injury_body_part": raw.get("injury_body_part"),
                "injury_notes": raw.get("injury_notes"),
                "depth_chart_order": int(depth) if depth is not None and float(depth).is_integer() else depth,
                "depth_chart_position": raw.get("depth_chart_position"),
                "game_id": game["game_id"],
                "opponent": game["opponent"],
                "site": game["site"],
                "kickoff": game["kickoff"],
                "evidence_captured_at": selected["captured_at"],
                "evidence_source_path": binding_key,
            })
        team_status[team] = {
            "status": "READY_RESEARCH_ONLY" if seen else "BLOCKED_TEAM_ROWS_MISSING",
            "game_id": game["game_id"],
            "kickoff": game["kickoff"],
            "opponent": game["opponent"],
            "site": game["site"],
            "player_count": len(seen),
            "state_counts": dict(sorted(states.items())),
            "source_captured_at": selected["captured_at"],
        }

    ready_teams = sum(1 for row in team_status.values() if row["status"] == "READY_RESEARCH_ONLY")
    status = "READY_RESEARCH_ONLY" if team_status and ready_teams == len(team_status) else (
        "PARTIAL_RESEARCH_ONLY" if ready_teams else "BLOCKED_NO_ELIGIBLE_AVAILABILITY"
    )
    payload = {
        "schema": AVAIL_SCHEMA,
        "schema_version": 2,
        "generated_at": as_of,
        "research_only": True,
        "production_model": "M9",
        "season": int(season),
        "week": int(week),
        "status": status,
        "point_in_time": True,
        "target_week_realised_stats_used": False,
        "probabilistic_absence_model": False,
        "direct_fantasy_projection_adjustment": False,
        "automatic_model_promotion": False,
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "waiver_values_changed": False,
        "adp_used_as_football_feature": False,
        "schedule_binding": schedule_binding,
        "source_bindings": list(source_bindings.values()),
        "team_summary": team_status,
        "players": sorted(typed_rows, key=lambda row: (row["team"], row["position_model"], row["sleeper_id"])),
        "semantics": {
            "confirmed_unavailable": sorted(UNAVAILABLE_STATES),
            "uncertain_not_auto_absent": sorted(UNCERTAIN_STATES),
            "missing_means": "UNKNOWN_OR_MISSING_EVIDENCE_NOT_HEALTHY",
        },
    }
    if recursive_forbidden_key(payload.get("players"), ("fantasy_points", "projection_delta", "rank_delta", "adp", "market_value")):
        raise AvailabilityError("FORBIDDEN_PROJECTION_OR_MARKET_FIELD_IN_AVAILABILITY")
    return payload


def load_opportunity_baseline(path: Path | None) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, Any]]:
    if path is None:
        return {}, {"status": "NOT_BOUND", "reason": "explicit pre-cutoff opportunity baseline not supplied"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != OPPORTUNITY_SCHEMA:
        raise AvailabilityError(f"OPPORTUNITY_SCHEMA_MISMATCH:{payload.get('schema')}")
    rows = payload.get("rows") or []
    mapping: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("sleeper_id") or "").strip()
        team = normalize_team(row.get("team"))
        role = str(row.get("role_family") or row.get("position_model") or "").strip().upper()
        share = finite(row.get("baseline_share"))
        observed = row.get("observed_at")
        if not sid or not team or not role or share is None or observed is None:
            raise AvailabilityError("OPPORTUNITY_ROW_REQUIRED_FIELD_MISSING")
        if not 0.0 <= share <= 1.0:
            raise AvailabilityError(f"OPPORTUNITY_SHARE_OUT_OF_RANGE:{sid}:{share}")
        key = (team, sid, role)
        if key in mapping:
            raise AvailabilityError(f"DUPLICATE_OPPORTUNITY_PLAYER_ROLE:{team}:{sid}:{role}")
        mapping[key] = {
            "sleeper_id": sid,
            "team": team,
            "role_family": role,
            "baseline_share": share,
            "observed_at": parse_time(str(observed)).isoformat(),
            "source": row.get("source"),
        }
    return mapping, {
        "status": "BOUND",
        "path": str(path),
        "sha256": sha256_file(path),
        "schema": payload.get("schema"),
        "row_count": len(mapping),
    }


def build_redistribution_contract(
    availability: dict[str, Any],
    *,
    opportunity: dict[tuple[str, str, str], dict[str, Any]] | None = None,
    opportunity_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opportunity = opportunity or {}
    players = availability.get("players") or []
    by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for player in players:
        by_team[player["team"]].append(player)

    scenarios: list[dict[str, Any]] = []
    for trigger in players:
        state = trigger.get("availability_state")
        if state not in UNAVAILABLE_STATES and state not in UNCERTAIN_STATES:
            continue
        team = trigger["team"]
        sid = trigger["sleeper_id"]
        trigger_baselines = [
            row for (t, player_id, _role), row in opportunity.items()
            if t == team and player_id == sid
        ]
        # Without a bound baseline we can still expose same-position recipient candidates,
        # but no numeric share is invented. With a baseline, each explicit role family
        # (e.g. CARRIES, TARGETS, SNAPS) receives its own conserved scenario.
        role_inputs: list[dict[str, Any] | None] = trigger_baselines or [None]
        for baseline_row in sorted(role_inputs, key=lambda row: (row or {}).get("role_family") or trigger.get("position_model") or ""):
            role_family = (baseline_row or {}).get("role_family") or trigger.get("role_family") or trigger.get("position_model")
            scenario_kind = "CONFIRMED_ABSENCE" if state in UNAVAILABLE_STATES else "IF_ABSENT_SCENARIO"
            trigger_share = (baseline_row or {}).get("baseline_share")

            if baseline_row and parse_time(baseline_row["observed_at"]) > parse_time(trigger["kickoff"]):
                raise AvailabilityError(f"POST_CUTOFF_OPPORTUNITY_EVIDENCE:{team}:{sid}:{role_family}")

            candidates: list[dict[str, Any]] = []
            for candidate in by_team[team]:
                if candidate["sleeper_id"] == sid:
                    continue
                if candidate.get("availability_state") in UNAVAILABLE_STATES:
                    continue
                candidate_baseline = opportunity.get((team, candidate["sleeper_id"], str(role_family)))
                if baseline_row is None:
                    # Unquantified fallback is intentionally conservative: same position only.
                    if (candidate.get("position_model") or candidate.get("role_family")) != role_family:
                        continue
                elif candidate_baseline is None:
                    # A quantified explicit role can only allocate to players explicitly bound to that role.
                    continue
                if candidate_baseline and parse_time(candidate_baseline["observed_at"]) > parse_time(candidate["kickoff"]):
                    raise AvailabilityError(f"POST_CUTOFF_OPPORTUNITY_EVIDENCE:{team}:{candidate['sleeper_id']}:{role_family}")
                candidates.append({
                    "sleeper_id": candidate["sleeper_id"],
                    "full_name": candidate.get("full_name"),
                    "availability_state": candidate.get("availability_state"),
                    "depth_chart_order": candidate.get("depth_chart_order"),
                    "baseline_share": (candidate_baseline or {}).get("baseline_share"),
                })
            candidates.sort(key=lambda row: (
                row["depth_chart_order"] is None,
                row["depth_chart_order"] if row["depth_chart_order"] is not None else 999,
                row["sleeper_id"],
            ))

            if trigger_share is None:
                scenarios.append({
                    "team": team,
                    "game_id": trigger["game_id"],
                    "kickoff": trigger["kickoff"],
                    "trigger_sleeper_id": sid,
                    "trigger_name": trigger.get("full_name"),
                    "trigger_state": state,
                    "scenario_kind": scenario_kind,
                    "role_family": role_family,
                    "role_family_source": "POSITION_CONSERVATIVE_UNQUANTIFIED",
                    "status": "BLOCKED_OPPORTUNITY_BASELINE_MISSING",
                    "vacated_share": None,
                    "allocations": [],
                    "residual_unallocated_share": None,
                    "candidate_recipients_unquantified": candidates,
                    "automatic_projection_change": False,
                })
                continue

            weighted = [row for row in candidates if finite(row.get("baseline_share")) is not None and float(row["baseline_share"]) > 0]
            denom = sum(float(row["baseline_share"]) for row in weighted)
            allocations: list[dict[str, Any]] = []
            if denom > 0:
                for row in weighted:
                    increment = float(trigger_share) * float(row["baseline_share"]) / denom
                    allocations.append({
                        "sleeper_id": row["sleeper_id"],
                        "full_name": row.get("full_name"),
                        "baseline_share": float(row["baseline_share"]),
                        "redistributed_share": increment,
                        "scenario_share": float(row["baseline_share"]) + increment,
                        "availability_state": row.get("availability_state"),
                    })
                residual = 0.0
                status = "READY_RESEARCH_SCENARIO"
            else:
                residual = float(trigger_share)
                status = "PARTIAL_NO_ELIGIBLE_WEIGHTED_RECIPIENT"

            allocated = sum(float(row["redistributed_share"]) for row in allocations)
            if abs((allocated + residual) - float(trigger_share)) > 1e-9:
                raise AvailabilityError(f"REDISTRIBUTION_CONSERVATION_FAILED:{team}:{sid}:{role_family}")
            scenarios.append({
                "team": team,
                "game_id": trigger["game_id"],
                "kickoff": trigger["kickoff"],
                "trigger_sleeper_id": sid,
                "trigger_name": trigger.get("full_name"),
                "trigger_state": state,
                "scenario_kind": scenario_kind,
                "role_family": role_family,
                "role_family_source": "EXPLICIT_OPPORTUNITY_BASELINE",
                "status": status,
                "vacated_share": float(trigger_share),
                "allocations": allocations,
                "residual_unallocated_share": residual,
                "conservation_check": abs((allocated + residual) - float(trigger_share)) <= 1e-9,
                "automatic_projection_change": False,
            })

    return {
        "schema": REDIST_SCHEMA,
        "schema_version": 2,
        "generated_at": availability.get("generated_at"),
        "research_only": True,
        "production_model": "M9",
        "season": availability.get("season"),
        "week": availability.get("week"),
        "status": "READY_RESEARCH_ONLY" if availability.get("players") else "BLOCKED_AVAILABILITY_NOT_READY",
        "availability_binding": {
            "schema": availability.get("schema"),
            "generated_at": availability.get("generated_at"),
        },
        "opportunity_binding": opportunity_binding or {"status": "NOT_BOUND"},
        "direct_fantasy_projection_adjustment": False,
        "automatic_model_promotion": False,
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "waiver_values_changed": False,
        "adp_used_as_football_feature": False,
        "uncertain_states_are_automatic_absences": False,
        "scenario_count": len(scenarios),
        "scenarios": sorted(scenarios, key=lambda row: (row["team"], row["role_family"], row["trigger_sleeper_id"])),
    }


def run(
    *,
    root: Path,
    season: int,
    week: int,
    as_of: str,
    schedule_context: Path | None = None,
    opportunity_baseline: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    as_of = parse_time(as_of).isoformat()
    if schedule_context is None:
        schedule_context = discover_weather_context(root, season, week, as_of)
    if schedule_context is None or not schedule_context.exists():
        # Persist a typed blocked artifact rather than silently inventing a global cutoff.
        games: list[dict[str, Any]] = []
        schedule_binding = {"status": "BLOCKED_SCHEDULE_CONTEXT_UNAVAILABLE"}
    else:
        games, schedule_binding = load_games_from_context(schedule_context)
        schedule_binding["status"] = "BOUND"
        if schedule_binding.get("generated_at") and parse_time(schedule_binding["generated_at"]) > parse_time(as_of):
            raise AvailabilityError("SCHEDULE_CONTEXT_OBSERVED_AFTER_AS_OF")

    availability = build_availability_contract(
        root=root, season=season, week=week, as_of=as_of, games=games, schedule_binding=schedule_binding
    )
    opportunity, opportunity_binding = load_opportunity_baseline(opportunity_baseline)
    redistribution = build_redistribution_contract(
        availability, opportunity=opportunity, opportunity_binding=opportunity_binding
    )

    output_root = output_root or (root / "data/research/availability/v2")
    stamp = compact_timestamp(as_of)
    out_dir = output_root / str(season) / f"week_{week:02d}" / stamp
    availability_path = out_dir / "availability-v2.json"
    redistribution_path = out_dir / "redistribution-v2.json"
    availability_write = first_write_json(availability_path, availability)
    # Bind redistribution to the exact availability artifact without mutating the in-memory source contract.
    redistribution["availability_binding"] = {
        "path": str(availability_path.relative_to(root)) if availability_path.is_relative_to(root) else str(availability_path),
        "sha256": sha256_file(availability_path),
        "schema": availability.get("schema"),
        "generated_at": availability.get("generated_at"),
    }
    redistribution_write = first_write_json(redistribution_path, redistribution)
    return {
        "status": availability.get("status"),
        "availability": str(availability_path.relative_to(root)) if availability_path.is_relative_to(root) else str(availability_path),
        "redistribution": str(redistribution_path.relative_to(root)) if redistribution_path.is_relative_to(root) else str(redistribution_path),
        "availability_write": availability_write,
        "redistribution_write": redistribution_write,
        "players": len(availability.get("players") or []),
        "scenarios": len(redistribution.get("scenarios") or []),
        "quantified_scenarios": sum(1 for row in redistribution.get("scenarios") or [] if row.get("status") == "READY_RESEARCH_SCENARIO"),
        "blocked_unquantified_scenarios": sum(1 for row in redistribution.get("scenarios") or [] if str(row.get("status") or "").startswith("BLOCKED")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FIE Window 2C Availability v2 + redistribution")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--as-of", default=None, help="UTC ISO timestamp; defaults to current time")
    parser.add_argument("--schedule-context", default=None)
    parser.add_argument("--opportunity-baseline", default=None)
    parser.add_argument("--output-root", default="data/research/availability/v2")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    schedule = Path(args.schedule_context) if args.schedule_context else None
    if schedule is not None and not schedule.is_absolute():
        schedule = root / schedule
    opportunity = Path(args.opportunity_baseline) if args.opportunity_baseline else None
    if opportunity is not None and not opportunity.is_absolute():
        opportunity = root / opportunity
    out = Path(args.output_root)
    if not out.is_absolute():
        out = root / out

    result = run(
        root=root,
        season=args.season,
        week=args.week,
        as_of=args.as_of or utc_now(),
        schedule_context=schedule,
        opportunity_baseline=opportunity,
        output_root=out,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

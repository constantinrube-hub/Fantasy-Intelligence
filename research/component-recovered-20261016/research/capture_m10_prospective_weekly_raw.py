#!/usr/bin/env python3
"""Capture R8C public-core source envelopes before any weekly transform.

This is a transport adapter, not a projection source.  It records exact raw
responses and derives only schedule, completed-game, identity, and governed
profile inputs required by R8B's frozen weekly producer.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from build_current_snapshot import first_kickoff_utc, regular_schedule_slice
from fie_governance import sha256_file as governed_json_sha256
from fie_research import SOURCE_TEMPLATES, build_identity, normalize_position
from m10_prospective_capture_contract import ROOT, capture_hours, capture_paths, sha256_file, write_json
from m10_prospective_weekly_producer import RAW_SCHEMA, fixture_raw_envelope
from nfl_schedule_time import first_present, kickoff_iso


UA = "Fantasy-Intelligence-M10-R8C/1.0"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
STATE_URL = "https://api.sleeper.app/v1/state/nfl"


def normalize_sleeper_id(value: Any) -> str:
    """Normalize CSV numeric coercion without changing genuine string IDs."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "<na>"}:
        return ""
    return re.sub(r"^(\d+)\.0$", r"\1", text)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch(url: str, destination: Path) -> dict[str, Any]:
    response = requests.get(url, timeout=45, headers={"User-Agent": UA, "Accept": "application/json,text/csv,*/*"})
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(response.content)
    return {"path": destination, "sha256": hashlib.sha256(response.content).hexdigest(), "source_identity": url, "release_or_etag": response.headers.get("ETag") or response.headers.get("Last-Modified") or "NOT_EXPOSED"}


def _completed_game_responses(responses: Path, *, season: int, week: int) -> list[dict[str, Any]]:
    """Capture the completed history available at the forecast cutoff.

    Week 1 has no current-season completed games.  Its shared as-of features
    therefore use the prior completed season and must not request a weekly
    file that the public source cannot publish until Week 1 has finished.
    From Week 2 onward, retain that prior-season context and add the current
    season's completed-game file; an unavailable current file then remains a
    retryable source failure rather than being replaced with invented rows.
    """
    history = _fetch(
        SOURCE_TEMPLATES["player_week"].format(season=season - 1),
        responses / f"player-week-{season - 1}.csv",
    )
    if week == 1:
        return [history]
    current = _fetch(
        SOURCE_TEMPLATES["player_week"].format(season=season),
        responses / f"player-week-{season}.csv",
    )
    return [history, current]


def _number(frame: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in frame:
            return pd.to_numeric(frame[name], errors="coerce")
    return pd.Series(float("nan"), index=frame.index)


def current_roster_identity(rosters: pd.DataFrame, *, season: int, week: int) -> dict[str, Any]:
    """Bind current teams to the verified target-week NFL roster, never latest_team.

    The all-time player catalog remains an identity crosswalk for historical
    stats. A current weekly roster supplies exact GSIS identities and target
    teams, including rookies, reserves and practice players. RET/CUT rows are
    explicit departures; other unknown statuses remain retryable source gaps.
    No injury status is turned into an availability probability.
    """
    required = {"season", "week", "team", "position", "gsis_id", "status", "game_type"}
    if not required <= set(rosters.columns):
        raise ValueError("current NFL roster is missing required identity fields")
    selected = rosters[(pd.to_numeric(rosters["season"], errors="coerce") == season)
        & (pd.to_numeric(rosters["week"], errors="coerce") == week)
        & rosters["game_type"].astype(str).str.upper().isin({"REG", "REGULAR"})].copy()
    if selected.empty:
        raise ValueError(f"current NFL roster for {season} week {week} is unavailable; retry without historical-team fallback")
    selected["position_model"] = selected["position"].map(normalize_position)
    selected = selected[selected["position_model"].isin({"QB", "RB", "WR", "TE"})].copy()
    status = selected["status"].astype(str).str.strip().str.upper()
    # nflreadr's roster-status dictionary defines INA as under contract but
    # inactive, not a departure. Preserve membership without inferring whether
    # that player is available to play. Unknown codes still fail closed.
    known = status.isin({"ACT", "DEV", "RES", "EXE", "INA", "RET", "CUT"})
    if not known.all():
        unknown = status[~known].value_counts().sort_index().to_dict()
        raise ValueError(f"current NFL roster has an unrecognized membership status for {season} week {week}: {unknown}")
    exclusions = []
    departed = status.isin({"RET", "CUT"})
    for _, row in selected[departed].iterrows():
        exclusions.append({"gsis_id": None if pd.isna(row["gsis_id"]) else str(row["gsis_id"]), "reason": "NOT_CURRENT_NFL_ROSTER_MEMBER"})
    selected = selected[~departed].copy()
    ids = selected["gsis_id"].astype("string").str.strip()
    unresolved = ids.isna() | ids.isin({"", "nan", "None"})
    for _ in selected[unresolved].itertuples():
        exclusions.append({"gsis_id": None, "reason": "UNRESOLVED_CURRENT_ROSTER_GSIS_ID"})
    selected = selected[~unresolved].copy()
    selected["gsis_id"] = ids[~unresolved]
    selected["team"] = selected["team"].astype("string").str.strip().str.upper()
    if selected["team"].isna().any() or selected["team"].isin({"", "NAN", "NONE"}).any():
        raise ValueError("current NFL roster has an unresolved team")
    # Exact duplicate source rows are harmless; conflicting teams/positions for
    # one ID are excluded symmetrically rather than selected by row order.
    bindings = selected[["gsis_id", "team", "position_model"]].drop_duplicates()
    ambiguous = set(bindings.loc[bindings["gsis_id"].duplicated(keep=False), "gsis_id"])
    exclusions.extend({"gsis_id": str(pid), "reason": "AMBIGUOUS_CURRENT_ROSTER_IDENTITY"} for pid in sorted(ambiguous))
    selected = selected[~selected["gsis_id"].isin(ambiguous)].drop_duplicates("gsis_id")
    identity, _ = build_identity(selected)
    identity["team"] = selected["team"].to_numpy()
    identity["position_model"] = selected["position_model"].to_numpy()
    output_identity = identity[["canonical_player_id", "sleeper_id", "position_model", "team"]].sort_values("canonical_player_id").copy()
    output_identity["sleeper_id"] = output_identity["sleeper_id"].map(lambda value: normalize_sleeper_id(value) or None)
    players = output_identity.astype(object).where(pd.notna(output_identity), None).to_dict("records")
    if not players:
        raise ValueError("current NFL roster has no unambiguous offensive players")
    return {"governed_crosswalk": True, "ambiguous_count": len(ambiguous), "current_roster_verified": True,
        "roster_snapshot_season": season, "roster_snapshot_week": week, "players": players,
        "symmetric_identity_exclusions": exclusions}


def attach_sleeper_identity(identity_snapshot: dict[str, Any], players: pd.DataFrame) -> dict[str, Any]:
    """Attach the exact Sleeper crosswalk from the captured player catalog."""
    identity, _ = build_identity(players)
    bindings: dict[str, set[str]] = {}
    for row in identity.dropna(subset=["canonical_player_id", "sleeper_id"]).itertuples():
        canonical_id, sleeper_id = str(row.canonical_player_id), normalize_sleeper_id(row.sleeper_id)
        if sleeper_id:
            bindings.setdefault(canonical_id, set()).add(sleeper_id)
    sleeper = {canonical_id: next(iter(values)) for canonical_id, values in bindings.items() if len(values) == 1}
    for row in identity_snapshot.get("players") or []:
        row["sleeper_id"] = sleeper.get(str(row.get("canonical_player_id") or "")) or row.get("sleeper_id")
    identity_snapshot["sleeper_identity_resolved"] = sum(bool(row.get("sleeper_id")) for row in identity_snapshot.get("players") or [])
    identity_snapshot["sleeper_identity_ambiguous"] = sum(len(values) > 1 for values in bindings.values())
    return identity_snapshot


def _blocked_roster_state(league_id: str, code: str, detail: Any = None) -> dict[str, Any]:
    value = {
        "league_id": str(league_id), "complete": False, "starter_slots": 0,
        "m10_roster_positions": [], "excluded_non_m10_starter_slots": [],
        "legal_canonical_player_ids": [], "blocker": code,
    }
    if detail is not None:
        value["blocker_detail"] = detail
    return value


def _verified_core(root: Path, manifest_path: Path) -> tuple[Path, dict[str, Any]]:
    """Verify a manifest-bound JSON core with the repository's portable hash."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    core = manifest.get("core") if isinstance(manifest.get("core"), dict) else None
    if core is None:
        raise ValueError("app manifest core is missing")
    relative, expected = str(core.get("path") or ""), str(core.get("sha256") or "")
    path = (root / relative).resolve()
    if not relative or not expected or not path.is_file():
        raise ValueError("app core is missing")
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("app core path is outside the repository") from exc
    if governed_json_sha256(path) != expected:
        raise ValueError("app core hash drift")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("app core is invalid")
    return path, value


def _league_roster_state(
    root: Path,
    league_id: str,
    registry_entry: dict[str, Any],
    identity_snapshot: dict[str, Any],
    *,
    season: int,
    week: int,
    username: str,
) -> dict[str, Any]:
    """Resolve one managed Sleeper roster against cutoff-bound canonical evidence."""
    try:
        from in_season_pr2_weekly_lineups import (
            catalog, current_index, current_snapshot, managed_roster, row_for_roster_id,
            sleeper_parts, valid_ids,
        )
        from weekly_lineup_decision_support import load_runtime_contract, player_position, starter_slot_instances
    except ModuleNotFoundError:  # pragma: no cover - package-style repository callers
        from research.in_season_pr2_weekly_lineups import (
            catalog, current_index, current_snapshot, managed_roster, row_for_roster_id,
            sleeper_parts, valid_ids,
        )
        from research.weekly_lineup_decision_support import load_runtime_contract, player_position, starter_slot_instances

    lid = str(league_id)
    league_root = root / "data/research/leagues" / lid
    profile_path = root / str(registry_entry["profile_path"])
    current_path = league_root / "current/milestone5_current.json"
    manifest_path = league_root / "app/manifest.json"
    if not profile_path.is_file() or not current_path.is_file() or not manifest_path.is_file():
        return _blocked_roster_state(lid, "LEAGUE_EVIDENCE_MISSING_AT_CUTOFF")
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        current = current_snapshot(current_path, root)
        core_path, core = _verified_core(root, manifest_path)
    except Exception as exc:
        return _blocked_roster_state(lid, "LEAGUE_EVIDENCE_UNREADABLE_AT_CUTOFF", type(exc).__name__)
    if int(current.get("season") or 0) != season or int(current.get("week") or 0) != week:
        return _blocked_roster_state(lid, "CURRENT_SNAPSHOT_SEASON_WEEK_MISMATCH", {"expected": [season, week], "actual": [current.get("season"), current.get("week")]})
    if current.get("target_week_realised_stats_excluded") is not True:
        return _blocked_roster_state(lid, "CURRENT_SNAPSHOT_REALIZED_STATS_GUARD_MISSING")
    if bool((current.get("roster_evolution") or {}).get("season_complete")):
        return _blocked_roster_state(lid, "LEAGUE_SEASON_COMPLETE_AT_CUTOFF")
    if current.get("profile_current_match") is False:
        return _blocked_roster_state(lid, "PROFILE_DRIFT_AT_CUTOFF", current.get("profile_diff") or {})
    expected_fingerprint = str(registry_entry.get("profile_fingerprint") or "")
    expected_scoring = str(registry_entry.get("scoring_signature") or "")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fingerprints = {str(profile.get("profile_fingerprint") or ""), str(current.get("profile_fingerprint") or ""), str(manifest.get("profile_fingerprint") or "")}
    scoring = {str(profile.get("scoring_signature") or ""), str(current.get("profile_scoring_signature") or ""), str(manifest.get("scoring_signature") or "")}
    if fingerprints != {expected_fingerprint} or scoring != {expected_scoring}:
        return _blocked_roster_state(lid, "PROFILE_BINDING_MISMATCH_AT_CUTOFF", {"fingerprints": sorted(fingerprints), "scoring_signatures": sorted(scoring)})
    if str(core.get("league_id") or "") != lid:
        return _blocked_roster_state(lid, "APP_LEAGUE_MISMATCH_AT_CUTOFF")
    contract, contract_sha = load_runtime_contract(root)
    league, _, _ = sleeper_parts(core)
    if int(league.get("season") or 0) != season:
        return _blocked_roster_state(lid, "APP_SEASON_MISMATCH_AT_CUTOFF", {"expected": season, "actual": league.get("season")})
    roster_positions = league.get("roster_positions") if isinstance(league.get("roster_positions"), list) else []
    try:
        starter_slots = starter_slot_instances(roster_positions, contract)
    except Exception as exc:
        return _blocked_roster_state(lid, "ROSTER_SLOT_CONTRACT_INVALID_AT_CUTOFF", str(exc))
    m10_positions = {"QB", "RB", "WR", "TE"}
    m10_roster_positions = [slot["slot"] for slot in starter_slots if set(slot["eligible_positions"]) <= m10_positions]
    excluded = [slot["slot"] for slot in starter_slots if not set(slot["eligible_positions"]) <= m10_positions]
    if not m10_roster_positions:
        return _blocked_roster_state(lid, "NO_M10_STARTER_SLOTS_AT_CUTOFF", excluded)
    roster, user = managed_roster(core, username)
    if roster is None or user is None:
        return _blocked_roster_state(lid, "MANAGED_ROSTER_UNRESOLVED_AT_CUTOFF", {"username": username})
    roster_ids = valid_ids(roster.get("players"))
    if not roster_ids:
        return _blocked_roster_state(lid, "MANAGED_ROSTER_EMPTY_AT_CUTOFF", {"managed_roster_id": roster.get("roster_id")})
    identity_bindings: dict[str, set[str]] = {}
    for row in identity_snapshot.get("players") or []:
        sleeper_id = normalize_sleeper_id(row.get("sleeper_id"))
        if sleeper_id and row.get("canonical_player_id") and str(row.get("position_model") or "") in m10_positions:
            identity_bindings.setdefault(sleeper_id, set()).add(str(row["canonical_player_id"]))
    ambiguous_sleeper_ids = {sleeper_id for sleeper_id, values in identity_bindings.items() if len(values) != 1}
    sleeper_to_canonical = {sleeper_id: next(iter(values)) for sleeper_id, values in identity_bindings.items() if len(values) == 1}
    index, player_catalog = current_index(current), catalog(root, core)
    legal, unresolved, excluded_players = [], [], []
    for sleeper_id in roster_ids:
        player = row_for_roster_id(sleeper_id, index, player_catalog)
        if player is None:
            unresolved.append({"sleeper_id": sleeper_id, "reason": "CURRENT_PLAYER_UNRESOLVED"})
            continue
        position = player_position(player, contract)
        if position not in m10_positions:
            excluded_players.append({"sleeper_id": sleeper_id, "position": position})
            continue
        if sleeper_id in ambiguous_sleeper_ids:
            unresolved.append({"sleeper_id": sleeper_id, "position": position, "reason": "M10_IDENTITY_AMBIGUOUS"})
            continue
        canonical_id = sleeper_to_canonical.get(sleeper_id)
        if not canonical_id:
            unresolved.append({"sleeper_id": sleeper_id, "position": position, "reason": "M10_IDENTITY_UNRESOLVED"})
            continue
        legal.append(canonical_id)
    if unresolved:
        return _blocked_roster_state(lid, "M10_ROSTER_IDENTITY_UNRESOLVED_AT_CUTOFF", unresolved)
    if not legal:
        return _blocked_roster_state(lid, "NO_M10_ROSTER_PLAYERS_AT_CUTOFF")
    if len(legal) != len(set(legal)):
        return _blocked_roster_state(lid, "DUPLICATE_M10_CANONICAL_ID_AT_CUTOFF")
    return {
        "league_id": lid, "complete": True, "starter_slots": len(m10_roster_positions),
        "m10_roster_positions": m10_roster_positions,
        "excluded_non_m10_starter_slots": excluded,
        "legal_canonical_player_ids": sorted(legal), "blocker": None,
        "managed_roster_id": str(roster.get("roster_id") or ""),
        "excluded_non_m10_roster_players": sorted(excluded_players, key=lambda row: (row["position"], row["sleeper_id"])),
        "runtime_contract_sha256": contract_sha,
        "evidence": {
            "profile_path": profile_path.relative_to(root).as_posix(), "profile_sha256": governed_json_sha256(profile_path),
            "current_snapshot_path": current_path.relative_to(root).as_posix(), "current_snapshot_sha256": governed_json_sha256(current_path),
            "app_manifest_path": manifest_path.relative_to(root).as_posix(), "app_manifest_sha256": governed_json_sha256(manifest_path),
            "app_core_path": core_path.relative_to(root).as_posix(), "app_core_sha256": governed_json_sha256(core_path),
        },
    }


def _profile_payload(identity_snapshot: dict[str, Any], *, season: int, week: int, root: Path = ROOT) -> dict[str, Any]:
    registry = json.loads((root / "data/research/leagues/registry.json").read_text(encoding="utf-8"))
    portfolio = json.loads((root / "config/league-portfolio.json").read_text(encoding="utf-8"))
    username = str(portfolio.get("sleeper_username") or "").strip()
    if not username:
        raise ValueError("portfolio Sleeper username is unavailable")
    profiles = []
    states = []
    captured_at = _now()
    for league_id, entry in sorted((registry.get("leagues") or {}).items()):
        if entry.get("enabled") is not True: continue
        profile_path = root / str(entry["profile_path"])
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profiles.append({"league_id": str(league_id), "league_format": profile["format"], "profile_scoring_signature": profile["scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"], "scoring_settings": profile["scoring_settings"], "captured_at": captured_at})
        states.append(_league_roster_state(root, str(league_id), entry, identity_snapshot, season=season, week=week, username=username))
    assert profiles, "no enabled league profiles"
    assert len(profiles) == len(states)
    return {"enabled_league_count": len(profiles), "profiles": profiles, "league_roster_states": states, "managed_sleeper_username": username, "m10_roster_scope": ["QB", "RB", "WR", "TE"]}


def _record(role: str, normalized: Path, observed_at: str, responses: list[dict[str, Any]]) -> dict[str, Any]:
    return {"role": role, "path": normalized.name, "sha256": sha256_file(normalized), "captured_at": observed_at, "as_of": observed_at, "point_in_time_eligible": True, "historical_reconstruction": False, "source_identity": " | ".join(item["source_identity"] for item in responses), "release_or_etag": " | ".join(item["release_or_etag"] for item in responses), "response_files": [{"path": item["path"].relative_to(normalized.parent).as_posix(), "sha256": item["sha256"]} for item in responses]}


def capture(output_dir: Path, *, season: int | None, week: int | None, output_root: Path | None = None) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True); responses = output_dir / "responses"; observed = _now()
    state_response = _fetch(STATE_URL, responses / "sleeper-state.json")
    state = __import__("json").loads(state_response["path"].read_text(encoding="utf-8"))
    resolved_season, resolved_week = int(season or state["season"]), int(week or state["week"])
    if str(state.get("season_type") or "").lower() not in {"regular", "reg"}:
        print("NO_WRITE_NOT_REGULAR_SEASON"); return None
    # First-write evidence is already terminal. Check before requesting a fresh
    # schedule or football sources, whose post-cutoff updates cannot change it.
    root = output_root if output_root is not None else ROOT / "data/research/prospective/m10"
    existing = capture_paths(root, resolved_season, resolved_week)
    for key in ("manifest", "missed"):
        if existing[key].exists():
            print(f"PASS R8C weekly capture EXISTS: {existing[key]}", flush=True)
            return None
    games_response = _fetch(GAMES_URL, responses / "games.csv")
    schedule_frame = pd.read_csv(games_response["path"], low_memory=False)
    slice_ = regular_schedule_slice(schedule_frame, resolved_season, resolved_week)
    kickoff = first_kickoff_utc(schedule_frame, resolved_season, resolved_week)
    if slice_.empty or kickoff is None:
        raise ValueError("regular-season schedule or first kickoff is unverifiable")
    home = "home_team" if "home_team" in slice_ else "home"; away = "away_team" if "away_team" in slice_ else "away"
    games = [{
        "home_team": str(row[home]), "away_team": str(row[away]),
        "kickoff_at": kickoff_iso(first_present(row, "gameday", "game_date"), first_present(row, "gametime", "game_time")),
    } for _, row in slice_.iterrows()]
    schedule_path = output_dir / "schedule.json"; write_json(schedule_path, {"season": resolved_season, "week": resolved_week, "season_type": "REG", "first_kickoff_at": kickoff.isoformat(), "games": games})
    if capture_hours(observed, kickoff.isoformat()) > 18.0:
        # A next-week roster may not yet be published. The governed early exit
        # depends only on verified state/schedule, never on football sources
        # that are not required until the capture window opens.
        print("NO_WRITE_WINDOW_NOT_REACHED", flush=True)
        return None
    completed_responses = _completed_game_responses(responses, season=resolved_season, week=resolved_week)
    players_response = _fetch(SOURCE_TEMPLATES["players"], responses / "players.csv")
    stats = pd.concat([pd.read_csv(item["path"], low_memory=False) for item in completed_responses], ignore_index=True, sort=False)
    players = pd.read_csv(players_response["path"], low_memory=False)
    identity, _ = build_identity(players)
    id_map = identity[["gsis_id", "canonical_player_id", "position"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    rosters_response = _fetch(SOURCE_TEMPLATES["weekly_rosters"].format(season=resolved_season), responses / f"weekly-rosters-{resolved_season}.csv")
    roster_identity = attach_sleeper_identity(current_roster_identity(pd.read_csv(rosters_response["path"], low_memory=False), season=resolved_season, week=resolved_week), players)
    scheduled_teams = {str(game[key]) for game in games for key in ("home_team", "away_team")}
    missing_teams = scheduled_teams - {row["team"] for row in roster_identity["players"]}
    if missing_teams:
        raise ValueError(f"current NFL roster lacks scheduled teams: {sorted(missing_teams)}")
    print(f"M10_STAGE current_roster players={len(roster_identity['players'])} historical_catalog_rows={len(players)} exclusions={len(roster_identity['symmetric_identity_exclusions'])}", flush=True)
    identity_path = output_dir / "identity-snapshot.json"; write_json(identity_path, roster_identity)
    source_id = stats.get("player_id", stats.get("gsis_id", pd.Series("", index=stats.index))).astype(str)
    current = stats.assign(_source_id=source_id).merge(id_map, left_on="_source_id", right_on="gsis_id", how="inner")
    current["position_model"] = current.get("position", current.get("position_y", "")).map(normalize_position)
    current["team"] = current.get("recent_team", current.get("team", "")).astype(str)
    seasons = pd.to_numeric(current.get("season"), errors="coerce")
    weeks = pd.to_numeric(current.get("week"), errors="coerce")
    current = current[((seasons < resolved_season) | ((seasons == resolved_season) & (weeks < resolved_week))) & current["position_model"].isin(["QB", "RB", "WR", "TE"])]
    if "season_type" in current:
        current = current[current["season_type"].astype(str).str.upper().isin({"REG", "REGULAR"})]
    targets = {"attempts": ("attempts", "passing_attempts"), "completions": ("completions",), "passing_yards": ("passing_yards",), "passing_tds": ("passing_tds",), "interceptions": ("interceptions", "passing_interceptions"), "carries": ("carries", "rushing_attempts"), "rushing_yards": ("rushing_yards",), "rushing_tds": ("rushing_tds",), "targets": ("targets",), "receptions": ("receptions",), "receiving_yards": ("receiving_yards",), "receiving_tds": ("receiving_tds",)}
    normalized = pd.DataFrame({"season": pd.to_numeric(current.get("season"), errors="coerce"), "week": pd.to_numeric(current.get("week"), errors="coerce"), "canonical_player_id": current["canonical_player_id"], "position_model": current["position_model"], "team": current["team"]})
    for name, aliases in targets.items(): normalized[name] = _number(current, *aliases)
    normalized = normalized.dropna(subset=["season", "week", "canonical_player_id", "team"]).astype(object).where(pd.notna(normalized), None)
    completed_path = output_dir / "completed-games.json"; write_json(completed_path, {"player_games": normalized.to_dict("records")})
    profiles_path = output_dir / "roster-profile-snapshot.json"; write_json(profiles_path, _profile_payload(roster_identity, season=resolved_season, week=resolved_week))
    manifest = output_dir / "raw-envelope.json"
    write_json(manifest, {"schema": RAW_SCHEMA, "fixture": False, "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False, "historical_reconstruction": False, "capture": {"season": resolved_season, "week": resolved_week, "observed_at": observed, "first_kickoff_at": kickoff.isoformat(), "hours_before_first_kickoff": capture_hours(observed, kickoff.isoformat())}, "source_records": [_record("schedule", schedule_path, observed, [state_response, games_response]), _record("completed_games", completed_path, observed, completed_responses), _record("identity_snapshot", identity_path, observed, [players_response, rosters_response]), _record("roster_profile_snapshot", profiles_path, observed, [])]})
    # The governed profile snapshot is local evidence, not an HTTP response.
    value = json.loads(manifest.read_text(encoding="utf-8")); value["source_records"][-1]["source_identity"] = "governed league profiles plus verified current/app roster evidence"; value["source_records"][-1]["release_or_etag"] = "NOT_APPLICABLE_LOCAL_GOVERNED_STATE"; value["source_records"][-1]["response_files"] = [{"path": profiles_path.name, "sha256": sha256_file(profiles_path)}]; write_json(manifest, value)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", required=True); parser.add_argument("--season", type=int); parser.add_argument("--week", type=int); parser.add_argument("--fixture", action="store_true"); args = parser.parse_args(argv)
    output = Path(args.output_dir); output = output if output.is_absolute() else ROOT / output
    if args.fixture:
        fixture_raw_envelope(output); print("PASS fixture raw source envelope"); return 0
    manifest = capture(output, season=args.season, week=args.week)
    if manifest: print(f"PASS raw source envelope {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from build_current_snapshot import first_kickoff_utc, regular_schedule_slice
from fie_research import SOURCE_TEMPLATES, build_identity, normalize_position
from m10_prospective_capture_contract import ROOT, capture_hours, sha256_file, write_json
from m10_prospective_weekly_producer import RAW_SCHEMA, fixture_raw_envelope


UA = "Fantasy-Intelligence-M10-R8C/1.0"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
STATE_URL = "https://api.sleeper.app/v1/state/nfl"


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


def _profile_payload() -> dict[str, Any]:
    registry = __import__("json").loads((ROOT / "data/research/leagues/registry.json").read_text(encoding="utf-8"))
    profiles = []
    states = []
    for league_id, entry in sorted((registry.get("leagues") or {}).items()):
        if entry.get("enabled") is not True: continue
        profile_path = ROOT / str(entry["profile_path"])
        profile = __import__("json").loads(profile_path.read_text(encoding="utf-8"))
        profiles.append({"league_id": str(league_id), "league_format": profile["format"], "profile_scoring_signature": profile["scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"], "scoring_settings": profile["scoring_settings"], "captured_at": _now()})
        # A weekly forecast may be retained even when a managed legal roster
        # cannot be canonically resolved at cutoff.  The adapter emits an
        # explicit per-league blocker instead of silently optimizing a subset.
        states.append({"league_id": str(league_id), "complete": False, "starter_slots": 0, "legal_canonical_player_ids": [], "blocker": "USER_ROSTER_CANONICAL_MAPPING_UNAVAILABLE"})
    assert len(profiles) == 22
    return {"enabled_league_count": len(profiles), "profiles": profiles, "league_roster_states": states}


def _record(role: str, normalized: Path, observed_at: str, responses: list[dict[str, Any]]) -> dict[str, Any]:
    return {"role": role, "path": normalized.name, "sha256": sha256_file(normalized), "captured_at": observed_at, "as_of": observed_at, "point_in_time_eligible": True, "historical_reconstruction": False, "source_identity": " | ".join(item["source_identity"] for item in responses), "release_or_etag": " | ".join(item["release_or_etag"] for item in responses), "response_files": [{"path": item["path"].relative_to(normalized.parent).as_posix(), "sha256": item["sha256"]} for item in responses]}


def capture(output_dir: Path, *, season: int | None, week: int | None) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True); responses = output_dir / "responses"; observed = _now()
    state_response = _fetch(STATE_URL, responses / "sleeper-state.json")
    state = __import__("json").loads(state_response["path"].read_text(encoding="utf-8"))
    resolved_season, resolved_week = int(season or state["season"]), int(week or state["week"])
    if str(state.get("season_type") or "").lower() not in {"regular", "reg"}:
        print("NO_WRITE_NOT_REGULAR_SEASON"); return None
    games_response = _fetch(GAMES_URL, responses / "games.csv")
    schedule_frame = pd.read_csv(games_response["path"], low_memory=False)
    slice_ = regular_schedule_slice(schedule_frame, resolved_season, resolved_week)
    kickoff = first_kickoff_utc(schedule_frame, resolved_season, resolved_week)
    if slice_.empty or kickoff is None:
        raise ValueError("regular-season schedule or first kickoff is unverifiable")
    home = "home_team" if "home_team" in slice_ else "home"; away = "away_team" if "away_team" in slice_ else "away"
    games = [{"home_team": str(row[home]), "away_team": str(row[away]), "kickoff_at": pd.to_datetime(str(row.get("gameday") or row.get("game_date")) + " " + str(row.get("gametime")), utc=True).isoformat()} for _, row in slice_.iterrows()]
    schedule_path = output_dir / "schedule.json"; write_json(schedule_path, {"season": resolved_season, "week": resolved_week, "season_type": "REG", "first_kickoff_at": kickoff.isoformat(), "games": games})
    completed_responses = _completed_game_responses(responses, season=resolved_season, week=resolved_week)
    players_response = _fetch(SOURCE_TEMPLATES["players"], responses / "players.csv")
    stats = pd.concat([pd.read_csv(item["path"], low_memory=False) for item in completed_responses], ignore_index=True, sort=False)
    players = pd.read_csv(players_response["path"], low_memory=False)
    identity, _ = build_identity(players)
    id_map = identity[["gsis_id", "canonical_player_id", "position"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    players_out = identity[["canonical_player_id", "position"]].copy()
    players_out["team"] = players.get("latest_team", players.get("team", "")).astype(str)
    players_out["position_model"] = players_out["position"].map(normalize_position)
    player_rows = players_out[players_out["position_model"].isin(["QB", "RB", "WR", "TE"]) & players_out["canonical_player_id"].notna()][["canonical_player_id", "position_model", "team"]].drop_duplicates("canonical_player_id").to_dict("records")
    identity_path = output_dir / "identity-snapshot.json"; write_json(identity_path, {"governed_crosswalk": True, "ambiguous_count": int(identity["canonical_player_id"].duplicated().sum()), "players": player_rows})
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
    profiles_path = output_dir / "roster-profile-snapshot.json"; write_json(profiles_path, _profile_payload())
    manifest = output_dir / "raw-envelope.json"
    write_json(manifest, {"schema": RAW_SCHEMA, "fixture": False, "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False, "historical_reconstruction": False, "capture": {"season": resolved_season, "week": resolved_week, "observed_at": observed, "first_kickoff_at": kickoff.isoformat(), "hours_before_first_kickoff": capture_hours(observed, kickoff.isoformat())}, "source_records": [_record("schedule", schedule_path, observed, [state_response, games_response]), _record("completed_games", completed_path, observed, completed_responses), _record("identity_snapshot", identity_path, observed, [players_response]), _record("roster_profile_snapshot", profiles_path, observed, [])]})
    # The governed profile snapshot is local evidence, not an HTTP response.
    value = __import__("json").loads(manifest.read_text(encoding="utf-8")); value["source_records"][-1]["source_identity"] = "governed repository league profiles"; value["source_records"][-1]["release_or_etag"] = "NOT_APPLICABLE_LOCAL_GOVERNED_STATE"; value["source_records"][-1]["response_files"] = [{"path": profiles_path.name, "sha256": sha256_file(profiles_path)}]; write_json(manifest, value)
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

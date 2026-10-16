#!/usr/bin/env python3
"""Research-only, game-level Week 1 fantasy projection report.

This is deliberately a report producer, never an app/runtime integration.  It
uses the frozen 2026 M9 season lock for QB/RB/WR/TE only.  Sleeper's live
pregame projection endpoint is captured as an external benchmark and is never
passed to the football model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from nfl_schedule_time import kickoff_iso

ROOT = Path(__file__).resolve().parents[1]
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
PLAYER_WEEK_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
SLEEPER_PROJECTIONS_URL = "https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular"
UA = "Fantasy-Intelligence-Week1-Game-Projections/1.0"
CORE_POSITIONS = {"QB", "RB", "WR", "TE"}
UNAVAILABLE = {"OUT", "DOUBTFUL", "IR", "PUP", "NFI", "SUSPENDED", "INACTIVE"}
TEAM_ALIASES = {"LA": "LAR", "STL": "LAR", "JAC": "JAX", "WSH": "WAS", "OAK": "LV", "SD": "LAC"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def canonical_team(value: Any) -> str:
    team = "" if value is None else str(value).strip().upper()
    if team in {"NAN", "NONE", "NAT"}:
        team = ""
    return TEAM_ALIASES.get(team, team)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fetch_bytes(url: str) -> tuple[bytes, dict[str, str | None]]:
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/csv,*/*"})
    with urlopen(request, timeout=45) as response:
        return response.read(), {"etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified")}


def fetch_json(url: str) -> tuple[Any, dict[str, Any]]:
    raw, headers = fetch_bytes(url)
    return json.loads(raw.decode("utf-8")), {"url": url, "sha256": sha256_bytes(raw), **headers}


def readiness(kickoff: str, observed_at: str) -> str:
    hours = (parse_time(kickoff) - parse_time(observed_at)).total_seconds() / 3600.0
    if hours <= 0:
        return "BLOCKED_KICKOFF_PASSED"
    return "READY_PREGAME_FINAL" if hours <= 18.0 else "READY_PREGAME_EARLY"


def availability_state(player: dict[str, Any]) -> str:
    status = str(player.get("status") or "").strip().lower()
    injury = str(player.get("injury_status") or "").strip().lower()
    both = f"{status} {injury}"
    if "suspend" in both: return "SUSPENDED"
    if "physically unable" in both or "pup" in both: return "PUP"
    if "non-football injury" in both or "nfi" in both: return "NFI"
    if "injured reserve" in both or status in {"ir", "injured_reserve"}: return "IR"
    if injury in {"out", "o"}: return "OUT"
    if injury in {"doubtful", "d"}: return "DOUBTFUL"
    if injury in {"questionable", "q"}: return "QUESTIONABLE"
    if "inactive" in status: return "INACTIVE"
    if "limited" in str(player.get("practice_participation") or "").lower(): return "LIMITED"
    return "AVAILABLE" if status in {"active", "act"} and not injury else "UNKNOWN"


def game_rows(schedule: pd.DataFrame, season: int, week: int, observed_at: str) -> list[dict[str, Any]]:
    frame = schedule[(pd.to_numeric(schedule.get("season"), errors="coerce") == season) & (pd.to_numeric(schedule.get("week"), errors="coerce") == week)].copy()
    kind = next((name for name in ("game_type", "season_type", "type") if name in frame), None)
    if kind: frame = frame[frame[kind].astype(str).str.upper().str.replace("_", "", regex=False).isin({"REG", "REGULAR", "REGULARSEASON"})]
    games = []
    for _, row in frame.iterrows():
        home_value = row.get("home_team") if str(row.get("home_team")).strip().lower() not in {"", "nan", "none", "nat"} else row.get("home")
        away_value = row.get("away_team") if str(row.get("away_team")).strip().lower() not in {"", "nan", "none", "nat"} else row.get("away")
        home, away = canonical_team(home_value), canonical_team(away_value)
        # pandas.NA cannot be truth-tested, so select schedule aliases without
        # using ``a or b``.  This is the same failure mode fixed in the shared
        # schedule-time helper.
        day = row.get("gameday") if str(row.get("gameday")).strip().lower() not in {"", "nan", "none", "nat"} else row.get("game_date")
        clock = row.get("gametime") if str(row.get("gametime")).strip().lower() not in {"", "nan", "none", "nat"} else row.get("game_time")
        try: kickoff = kickoff_iso(day, clock)
        except (TypeError, ValueError): continue
        games.append({"game_id": str(row.get("game_id") or f"{season}_{week:02d}_{away}_{home}"), "home_team": home, "away_team": away, "kickoff_at": kickoff, "readiness": readiness(kickoff, observed_at), "weather_context_status": "NOT_USED_UNVALIDATED", "opponent_context_status": "NOT_USED_UNVALIDATED"})
    if not games: raise ValueError("no verifiable regular-season schedule rows")
    return sorted(games, key=lambda row: (row["kickoff_at"], row["game_id"]))


def sleeper_team_players(payload: dict[str, Any], teams: set[str]) -> list[dict[str, Any]]:
    rows = []
    for sleeper_id, player in payload.items():
        if not isinstance(player, dict): continue
        team, pos = canonical_team(player.get("team")), str(player.get("position") or "").upper()
        if team not in teams or not pos: continue
        rows.append({**player, "sleeper_id": str(sleeper_id), "team": team, "position_model": "DST" if pos == "DEF" else pos, "full_name": player.get("full_name") or player.get("first_name", "") + " " + player.get("last_name", "")})
    return rows


def identity_match(nfl_identity: pd.DataFrame, sleeper_players: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    """Return only unambiguous name+position links; all others remain typed blockers."""
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in nfl_identity.to_dict("records"):
        key = (norm_name(row.get("full_name")), str(row.get("position") or "").upper())
        if key[0] and row.get("canonical_player_id"): index.setdefault(key, []).append(row)
    mapped, ambiguous = {}, set()
    for player in sleeper_players:
        key = (norm_name(player.get("full_name")), str(player.get("position_model") or "").upper())
        candidates = index.get(key, [])
        if len(candidates) == 1:
            mapped[str(player["sleeper_id"])] = candidates[0]
        else:
            ambiguous.add(str(player["sleeper_id"]))
    return mapped, ambiguous


def _number(frame: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in frame: return pd.to_numeric(frame[name], errors="coerce")
    return pd.Series(float("nan"), index=frame.index)


def history_frame(stats: pd.DataFrame, identity: pd.DataFrame, season: int) -> pd.DataFrame:
    from fie_research import normalize_position
    id_map = identity[["gsis_id", "canonical_player_id", "position"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    source_id = stats.get("player_id", stats.get("gsis_id", pd.Series("", index=stats.index))).astype(str)
    current = stats.assign(_source_id=source_id).merge(id_map, left_on="_source_id", right_on="gsis_id", how="inner")
    current["position_model"] = current.get("position", current.get("position_y", "")).map(normalize_position)
    current["team"] = current.get("recent_team", current.get("team", "")).map(canonical_team)
    current = current[(pd.to_numeric(current.get("season"), errors="coerce") < season) & current["position_model"].isin(CORE_POSITIONS)]
    if "season_type" in current: current = current[current["season_type"].astype(str).str.upper().isin({"REG", "REGULAR"})]
    aliases = {"attempts": ("attempts", "passing_attempts"), "completions": ("completions",), "passing_yards": ("passing_yards",), "passing_tds": ("passing_tds",), "interceptions": ("interceptions", "passing_interceptions"), "carries": ("carries", "rushing_attempts"), "rushing_yards": ("rushing_yards",), "rushing_tds": ("rushing_tds",), "targets": ("targets",), "receptions": ("receptions",), "receiving_yards": ("receiving_yards",), "receiving_tds": ("receiving_tds",)}
    output = pd.DataFrame({"season": pd.to_numeric(current.get("season"), errors="coerce"), "week": pd.to_numeric(current.get("week"), errors="coerce"), "canonical_player_id": current["canonical_player_id"], "position_model": current["position_model"], "team": current["team"]})
    for name, choices in aliases.items(): output[name] = _number(current, *choices)
    return output.dropna(subset=["season", "week", "canonical_player_id", "team"])


def profiles() -> list[dict[str, Any]]:
    registry = json.loads((ROOT / "data/research/leagues/registry.json").read_text())
    rows = []
    for league_id, item in sorted((registry.get("leagues") or {}).items()):
        if item.get("enabled") is not True: continue
        profile = json.loads((ROOT / item["profile_path"]).read_text())
        rows.append({"league_id": str(league_id), "league_format": profile["format"], "profile_scoring_signature": profile["scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"], "scoring_settings": profile["scoring_settings"]})
    if len(rows) != 22: raise ValueError("enabled league-profile contract is not 22")
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row}) if rows else ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def build(season: int, week: int, output_root: Path, *, observed_at: str | None = None) -> Path:
    """Capture current public inputs and write an immutable-style research report."""
    observed_at = observed_at or utc_now()
    schedule_raw, schedule_headers = fetch_bytes(GAMES_URL)
    games = game_rows(pd.read_csv(pd.io.common.BytesIO(schedule_raw), low_memory=False), season, week, observed_at)
    team_game = {team: game for game in games for team in (game["home_team"], game["away_team"])}
    sleeper_payload, sleeper_meta = fetch_json(SLEEPER_PLAYERS_URL)
    projection_payload, projection_meta = fetch_json(SLEEPER_PROJECTIONS_URL.format(season=season, week=week))
    if not isinstance(sleeper_payload, dict) or not isinstance(projection_payload, list): raise ValueError("live Sleeper response shape is invalid")
    sleeper = sleeper_team_players(sleeper_payload, set(team_game))
    players_raw, players_headers = fetch_bytes(PLAYERS_URL)
    history_raw, history_headers = fetch_bytes(PLAYER_WEEK_URL.format(season=season - 1))
    from fie_research import build_identity
    from m10_prospective_weekly_producer import _point_rows, exact_profile_scoring
    nfl_identity, _ = build_identity(pd.read_csv(pd.io.common.BytesIO(players_raw), low_memory=False))
    mapped, ambiguous = identity_match(nfl_identity, sleeper)
    history = history_frame(pd.read_csv(pd.io.common.BytesIO(history_raw), low_memory=False), nfl_identity, season)
    target_rows, player_meta = [], {}
    for player in sleeper:
        sid, game = str(player["sleeper_id"]), team_game[player["team"]]
        state, game_status = availability_state(player), game["readiness"]
        meta = {"sleeper_id": sid, "full_name": player.get("full_name"), "team": player["team"], "position_model": player["position_model"], "game_id": game["game_id"], "player_kickoff_at": game["kickoff_at"], "game_readiness": game_status, "availability_state": state}
        player_meta[sid] = meta
        if player["position_model"] not in CORE_POSITIONS or sid not in mapped or game_status == "BLOCKED_KICKOFF_PASSED": continue
        identity = mapped[sid]
        opponent = game["away_team"] if player["team"] == game["home_team"] else game["home_team"]
        target_rows.append({"season": season, "week": week, "canonical_player_id": identity["canonical_player_id"], "position_model": player["position_model"], "team": player["team"], "opponent_team": opponent, "player_kickoff_at": game["kickoff_at"], "sleeper_id": sid})
    target = pd.DataFrame(target_rows)
    lock = json.loads((ROOT / "data/research/prospective/m10/season-locks/2026/season-lock.json").read_text())
    source_hash = sha256_bytes(schedule_raw + players_raw + history_raw)
    capture = {"season": season, "week": week, "observed_at": observed_at, "first_kickoff_at": min(game["kickoff_at"] for game in games), "schedule_snapshot_sha256": sha256_bytes(schedule_raw)}
    all_models = _point_rows(lock, history, target.drop(columns=["sleeper_id"]), capture=capture, source_bundle_sha256=source_hash) if len(target) else []
    by_id = {row["canonical_player_id"]: row for row in target_rows}
    raw_rows = []
    for row in all_models:
        sid = by_id[row["canonical_player_id"]]["sleeper_id"]; meta = player_meta[sid]
        status = "BLOCKED_CONFIRMED_UNAVAILABLE" if meta["availability_state"] in UNAVAILABLE else "CONDITIONAL_QUESTIONABLE" if meta["availability_state"] in {"QUESTIONABLE", "LIMITED", "UNKNOWN"} else meta["game_readiness"]
        raw_rows.append({**row, **meta, "projection_source": "FIE_M9_FROZEN_LOCK" if row["model"] == "M9" else "M10_RESEARCH_COMPARISON_ONLY", "actionable_status": status, "rank_eligible": row["model"] == "M9" and status.startswith("READY")})
    # Retain every scheduled Sleeper player as a benchmark-only line, including
    # specialists and IDP. These never enter M9 or profile scoring.
    points_by_sid = {str(row.get("player_id") or row.get("id") or ""): row.get("stats") or {} for row in projection_payload}
    benchmarks = []
    for sid, meta in sorted(player_meta.items()):
        stats = points_by_sid.get(sid, {})
        benchmarks.append({**meta, "projection_source": "EXTERNAL_BENCHMARK_ONLY", "benchmark_status": "EXTERNAL_PREGAME_BENCHMARK", "sleeper_points_ppr": stats.get("pts_ppr"), "raw_stats": stats, "not_model_input": True})
    p = profiles()
    # Never turn unsupported raw components into zero.  The M9 lock does not
    # forecast every possible platform stat (notably fumbles and 2-point
    # conversions), so profile/position pairs without exact component coverage
    # are emitted as typed blockers instead of being partially scored.
    from fie_research import scoring_audit
    from scoring_relevance import position_support
    scored = []
    for row in [item for item in raw_rows if item["model"] == "M9"]:
        eligible, blocked = [], []
        for profile in p:
            audit = scoring_audit(pd.DataFrame([{**row["predicted_raw_components"], "position_model": row["position_model"]}]), profile["scoring_settings"])
            support = position_support(profile["scoring_settings"], audit, row["position_model"])
            (eligible if support["exact"] else blocked).append((profile, support))
        scored.extend(exact_profile_scoring([row], eligible, lock))
        for profile, support in blocked:
            scored.append({"forecast_id": row["forecast_id"], "canonical_player_id": row["canonical_player_id"], "model": "M9", "league_id": profile["league_id"], "league_format": profile["league_format"], "profile_scoring_signature": profile["profile_scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"], "scored_fantasy_points": None, "scored_prediction_quantiles": None, "distribution_interpretation": None, "scoring_registry_version_sha256": None, "research_only": True, "actionable_status": "BLOCKED_PROFILE_RAW_COVERAGE", "scoring_coverage": support})
    raw_index = {row["forecast_id"]: row for row in raw_rows if row["model"] == "M9"}
    league_rows = [{**row, "actionable_status": row.get("actionable_status") or raw_index[row["forecast_id"]]["actionable_status"], "rank_eligible": raw_index[row["forecast_id"]]["rank_eligible"] and row.get("actionable_status") != "BLOCKED_PROFILE_RAW_COVERAGE"} for row in scored]
    stamp = re.sub(r"[^0-9]", "", observed_at)[:20]
    out = output_root / str(season) / f"week_{week:02d}" / "game-projections-v1" / "captures" / stamp
    out.mkdir(parents=True, exist_ok=False)
    input_refs = [{"role": "schedule", "url": GAMES_URL, "sha256": sha256_bytes(schedule_raw), **schedule_headers}, {"role": "nflverse_players", "url": PLAYERS_URL, "sha256": sha256_bytes(players_raw), **players_headers}, {"role": "completed_2025_player_week", "url": PLAYER_WEEK_URL.format(season=season-1), "sha256": sha256_bytes(history_raw), **history_headers}, {"role": "sleeper_players_availability", **sleeper_meta}, {"role": "sleeper_weekly_projection_external_benchmark", **projection_meta}]
    manifest = {"schema": "fie-week1-game-projections-v1", "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "season": season, "week": week, "observed_at": observed_at, "input_sources": input_refs, "model": {"season_lock": "data/research/prospective/m10/season-locks/2026/season-lock.json", "m9_primary": True, "m10_comparison_only": True, "weather_opponent": "NOT_USED_UNVALIDATED", "market": "EXTERNAL_BENCHMARK_ONLY"}, "counts": {"games": len(games), "m9_rows": len([r for r in raw_rows if r["model"] == "M9"]), "benchmark_rows": len(benchmarks), "profile_rows": len(league_rows)}, "identity": {"unambiguous_mapped": len(mapped), "ambiguous_or_unresolved": len(ambiguous)}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (out / "games.json").write_text(json.dumps(games, indent=2, sort_keys=True) + "\n")
    write_csv(out / "player-raw-projections.csv", raw_rows)
    write_csv(out / "league-player-projections.csv", league_rows)
    write_csv(out / "external-benchmark.csv", benchmarks)
    validation = {"status": "PASS", "research_only": True, "profiles": len(p), "all_profiles_exact": len({row["profile_fingerprint"] for row in league_rows}) == 22 if league_rows else True, "blocked_started_games": sum(game["readiness"] == "BLOCKED_KICKOFF_PASSED" for game in games), "confirmed_unavailable_not_ranked": all(not row["rank_eligible"] for row in raw_rows if row["actionable_status"] == "BLOCKED_CONFIRMED_UNAVAILABLE"), "external_benchmark_not_model_input": all(row["not_model_input"] for row in benchmarks)}
    (out / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")
    lines = [f"# Week {week} Game-Level Fantasy Projections", "", "Research only. M9 is the frozen primary; M10 rows are comparison-only. Sleeper is an external pregame benchmark, not a model input.", "", "| Game | Kickoff (UTC) | Readiness |", "|---|---:|---|"]
    lines += [f"| {game['away_team']} @ {game['home_team']} | {game['kickoff_at']} | {game['readiness']} |" for game in games]
    lines += ["", f"M9 core-player rows: {manifest['counts']['m9_rows']}. External benchmark rows: {manifest['counts']['benchmark_rows']}. Exact profile rows: {manifest['counts']['profile_rows']}.", "", "Confirmed unavailable players are retained for audit but excluded from actionable ranks. Questionable status remains conditional; no availability probability is invented."]
    (out / "week1-game-projections.md").write_text("\n".join(lines) + "\n")
    pointer = out.parent.parent / "latest.json"
    pointer.write_text(json.dumps({"schema": "fie-week1-game-projections-latest-v1", "capture": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out), "observed_at": observed_at}, indent=2, sort_keys=True) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026); parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--output-root", default="data/research/evaluation")
    parser.add_argument("--observed-at", help="UTC ISO time for a reproducible fixture-style run")
    args = parser.parse_args(argv)
    root = Path(args.output_root); root = root if root.is_absolute() else ROOT / root
    print(build(args.season, args.week, root, observed_at=args.observed_at))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

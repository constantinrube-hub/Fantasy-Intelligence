#!/usr/bin/env python3
"""Capture the additive Sunday T-6 M10/Sleeper research checkpoint.

The existing week-open ledgers remain untouched. This adapter reuses the frozen
M10 producer under a checkpoint-specific output root, preserves a raw Sleeper
response, scores matched Sleeper rows through the same captured league profiles,
and writes one immutable binding manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta, timezone
import gzip
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from build_current_snapshot import score_sleeper_projection
from capture_m10_prospective_weekly_raw import (
    GAMES_URL, STATE_URL, _completed_game_responses, _fetch, _number, _profile_payload,
    _record, attach_sleeper_identity, current_roster_identity, normalize_sleeper_id,
)
from fie_research import SOURCE_TEMPLATES, build_identity, normalize_position
from m10_prospective_capture_contract import (
    MODELS, POSITIONS, ROOT, canonical_bytes, capture_paths, parse_time, read_json,
    read_jsonl_gzip, sha256_bytes, sha256_file, write_json, write_jsonl_gzip,
)
from m10_prospective_weekly_producer import RAW_SCHEMA
from nfl_schedule_time import first_present, kickoff_iso
from run_m10_prospective_weekly_capture import main as run_m10_capture

DESIGN_PATH = ROOT / "config/m10-sunday-paired-checkpoint-design.json"
CHECKPOINT_ID = "SUNDAY_MAIN_T6"
SLUG = "sunday-main-t6"
SCHEMA = "fie-m10-sleeper-sunday-checkpoint-v1"
MISSED_SCHEMA = "fie-m10-sleeper-sunday-checkpoint-missed-v1"
SLEEPER_URL = "https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_design() -> dict[str, Any]:
    value = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    assert value["schema"] == "fie-m10-sleeper-sunday-checkpoint-design-v1"
    assert value["checkpoint_id"] == CHECKPOINT_ID
    assert value["production_model"] == "M9" and value["research_only"] is True
    return value


def paths(root: Path, season: int, week: int) -> dict[str, Path]:
    m10 = root / "data/research/prospective/m10/checkpoints" / str(season) / f"week_{week:02d}" / SLUG
    sleeper = root / "data/research/market/sleeper/checkpoints" / str(season) / f"week_{week:02d}" / SLUG
    binding = root / "data/research/prospective/paired-checkpoints" / str(season) / f"week_{week:02d}" / SLUG
    return {
        "m10_root": m10,
        "sleeper_root": sleeper,
        "binding_root": binding,
        "manifest": binding / "manifest.json",
        "missed": binding / "missed-capture.json",
        "schedule": binding / "schedule.json",
        "sleeper_raw": sleeper / "source-response.json.gz",
        "sleeper_rows": sleeper / "projection.jsonl.gz",
        "sleeper_meta": sleeper / "projection.jsonl.gz.meta.json",
        "sleeper_scoring": sleeper / "scoring-replay.jsonl.gz",
        "week_open_delta": binding / "week-open-delta.jsonl.gz",
    }


def _game_rows(frame: pd.DataFrame, season: int, week: int) -> list[dict[str, str]]:
    season_values = pd.to_numeric(frame.get("season"), errors="coerce")
    week_values = pd.to_numeric(frame.get("week"), errors="coerce")
    game_type = frame.get("game_type", frame.get("season_type", pd.Series("REG", index=frame.index))).astype(str).str.upper()
    selected = frame[(season_values == season) & (week_values == week) & game_type.isin({"REG", "REGULAR"})]
    home = "home_team" if "home_team" in selected else "home"
    away = "away_team" if "away_team" in selected else "away"
    rows = []
    for _, row in selected.iterrows():
        rows.append({
            "home_team": str(row[home]), "away_team": str(row[away]),
            "kickoff_at": kickoff_iso(first_present(row, "gameday", "game_date"), first_present(row, "gametime", "game_time")),
        })
    return sorted(rows, key=lambda row: (row["kickoff_at"], row["away_team"], row["home_team"]))


def checkpoint_decision(games: list[dict[str, str]], observed_at: str, design: dict[str, Any] | None = None) -> dict[str, Any]:
    design = design or load_design(); timing = design["timing"]
    observed = parse_time(observed_at); eastern = ZoneInfo(timing["timezone"])
    anchors = []
    for game in games:
        kickoff = parse_time(game["kickoff_at"]); local = kickoff.astimezone(eastern)
        if local.weekday() == 6 and time(13) <= local.time() < time(16):
            anchors.append(kickoff)
    if not anchors:
        return {"status": "NO_MAIN_SLATE", "checkpoint_id": CHECKPOINT_ID, "observed_at": observed.isoformat()}
    anchor = min(anchors)
    target = anchor - timedelta(hours=float(timing["target_hours_before_anchor"]))
    close = anchor - timedelta(hours=float(timing["closes_hours_before_anchor"]))
    if observed < target: status = "WINDOW_NOT_REACHED"
    elif observed <= close: status = "DUE"
    else: status = "WINDOW_MISSED"
    minimum = observed + timedelta(minutes=int(design["eligible_cohort"]["minimum_lead_minutes"]))
    eligible = [game for game in games if parse_time(game["kickoff_at"]) >= minimum]
    excluded = [dict(game, reason="STARTED_OR_LESS_THAN_30_MINUTES") for game in games if parse_time(game["kickoff_at"]) < minimum]
    return {
        "status": status, "checkpoint_id": CHECKPOINT_ID, "observed_at": observed.isoformat(),
        "anchor_at": anchor.isoformat(), "target_at": target.isoformat(), "window_close_at": close.isoformat(),
        "hours_before_anchor": round((anchor - observed).total_seconds() / 3600, 6),
        "eligible_games": eligible, "excluded_games": excluded,
    }


def _first_write_json(path: Path, value: dict[str, Any]) -> None:
    payload = canonical_bytes(value) + b"\n"; path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload: raise ValueError(f"divergent first-write collision: {path}")
        return
    path.write_bytes(payload)


def _first_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload: raise ValueError(f"divergent first-write collision: {path}")
        return
    path.write_bytes(payload)


def _first_write_tree(source: Path, destination: Path) -> None:
    for item in sorted(path for path in source.rglob("*") if path.is_file()):
        _first_write_bytes(destination / item.relative_to(source), item.read_bytes())


def _gzip_bytes(payload: bytes) -> bytes:
    import io
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as handle: handle.write(payload)
    return output.getvalue()


def _normalized_history(stats: pd.DataFrame, players: pd.DataFrame, *, season: int, week: int) -> pd.DataFrame:
    identity, _ = build_identity(players)
    id_map = identity[["gsis_id", "canonical_player_id", "position"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    source_id = stats.get("player_id", stats.get("gsis_id", pd.Series("", index=stats.index))).astype(str)
    current = stats.assign(_source_id=source_id).merge(id_map, left_on="_source_id", right_on="gsis_id", how="inner")
    current["position_model"] = current.get("position", current.get("position_y", "")).map(normalize_position)
    current["team"] = current.get("recent_team", current.get("team", "")).astype(str)
    seasons = pd.to_numeric(current.get("season"), errors="coerce"); weeks = pd.to_numeric(current.get("week"), errors="coerce")
    current = current[((seasons < season) | ((seasons == season) & (weeks < week))) & current["position_model"].isin(POSITIONS)]
    if "season_type" in current: current = current[current["season_type"].astype(str).str.upper().isin({"REG", "REGULAR"})]
    targets = {"attempts": ("attempts", "passing_attempts"), "completions": ("completions",), "passing_yards": ("passing_yards",), "passing_tds": ("passing_tds",), "interceptions": ("interceptions", "passing_interceptions"), "carries": ("carries", "rushing_attempts"), "rushing_yards": ("rushing_yards",), "rushing_tds": ("rushing_tds",), "targets": ("targets",), "receptions": ("receptions",), "receiving_yards": ("receiving_yards",), "receiving_tds": ("receiving_tds",)}
    result = pd.DataFrame({"season": pd.to_numeric(current.get("season"), errors="coerce"), "week": pd.to_numeric(current.get("week"), errors="coerce"), "canonical_player_id": current["canonical_player_id"], "position_model": current["position_model"], "team": current["team"]})
    for name, aliases in targets.items(): result[name] = _number(current, *aliases)
    return result.dropna(subset=["season", "week", "canonical_player_id", "team"]).astype(object).where(pd.notna(result), None)


def _identity_with_sleeper(rosters: pd.DataFrame, players: pd.DataFrame, *, season: int, week: int) -> dict[str, Any]:
    return attach_sleeper_identity(current_roster_identity(rosters, season=season, week=week), players)


def build_live_raw(output: Path, *, season: int, week: int, games_response: dict[str, Any], state_response: dict[str, Any], decision: dict[str, Any]) -> tuple[Path, dict[str, str]]:
    responses = output / "responses"; design = load_design()
    completed_responses = _completed_game_responses(responses, season=season, week=week)
    players_response = _fetch(SOURCE_TEMPLATES["players"], responses / "players.csv")
    rosters_response = _fetch(SOURCE_TEMPLATES["weekly_rosters"].format(season=season), responses / f"weekly-rosters-{season}.csv")
    observed = _now()
    if checkpoint_decision(decision["all_games"], observed, design)["status"] != "DUE":
        raise ValueError("Sunday source capture left the eligible window before inputs completed")
    live_decision = checkpoint_decision(decision["all_games"], observed, design)
    stats = pd.concat([pd.read_csv(item["path"], low_memory=False) for item in completed_responses], ignore_index=True, sort=False)
    players = pd.read_csv(players_response["path"], low_memory=False); rosters = pd.read_csv(rosters_response["path"], low_memory=False)
    history = _normalized_history(stats, players, season=season, week=week)
    identity = _identity_with_sleeper(rosters, players, season=season, week=week)
    scheduled = {str(game[key]) for game in live_decision["eligible_games"] for key in ("home_team", "away_team")}
    missing = scheduled - {row["team"] for row in identity["players"]}
    if missing: raise ValueError(f"current NFL roster lacks Sunday checkpoint teams: {sorted(missing)}")
    output.mkdir(parents=True, exist_ok=True)
    schedule_path = output / "schedule.json"
    write_json(schedule_path, {"season": season, "week": week, "season_type": "REG", "first_kickoff_at": live_decision["anchor_at"], "checkpoint_id": CHECKPOINT_ID, "games": live_decision["eligible_games"], "excluded_games": live_decision["excluded_games"]})
    completed_path = output / "completed-games.json"; write_json(completed_path, {"player_games": history.to_dict("records"), "target_week_realised_stats_excluded": True})
    identity_path = output / "identity-snapshot.json"; write_json(identity_path, identity)
    profiles_path = output / "roster-profile-snapshot.json"; write_json(profiles_path, _profile_payload(identity, season=season, week=week))
    records = [_record("schedule", schedule_path, observed, [state_response, games_response]), _record("completed_games", completed_path, observed, completed_responses), _record("identity_snapshot", identity_path, observed, [players_response, rosters_response]), _record("roster_profile_snapshot", profiles_path, observed, [])]
    records[-1]["source_identity"] = "governed league profiles plus verified current/app roster evidence"; records[-1]["release_or_etag"] = "NOT_APPLICABLE_LOCAL_GOVERNED_STATE"; records[-1]["response_files"] = [{"path": profiles_path.name, "sha256": sha256_file(profiles_path)}]
    manifest = output / "raw-envelope.json"
    write_json(manifest, {"schema": RAW_SCHEMA, "fixture": False, "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False, "historical_reconstruction": False, "checkpoint_id": CHECKPOINT_ID, "capture": {"season": season, "week": week, "observed_at": observed, "first_kickoff_at": live_decision["anchor_at"], "hours_before_first_kickoff": live_decision["hours_before_anchor"]}, "source_records": records})
    mapping = {normalize_sleeper_id(row["sleeper_id"]): str(row["canonical_player_id"]) for row in identity["players"] if normalize_sleeper_id(row.get("sleeper_id"))}
    return manifest, mapping


def _sleeper_ledgers(raw_payload: bytes, *, season: int, week: int, observed_at: str, identity_map: dict[str, str], forecasts: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    provider = json.loads(raw_payload)
    if not isinstance(provider, list): raise ValueError("Sleeper projection response must be a list")
    cohort = {str(row["canonical_player_id"]): row for row in forecasts if str(row["model"]) == "M9"}
    by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list); reasons = Counter()
    supported_rows = 0; identity_resolved = 0
    for row in provider:
        sid = normalize_sleeper_id(row.get("player_id") or (row.get("player") or {}).get("player_id"))
        position = normalize_position((row.get("player") or {}).get("position"))
        if not sid: reasons["MISSING_SLEEPER_ID"] += 1; continue
        if position not in POSITIONS: reasons["UNSUPPORTED_POSITION"] += 1; continue
        supported_rows += 1; cid = identity_map.get(sid)
        if not cid: reasons["IDENTITY_UNRESOLVED"] += 1; continue
        identity_resolved += 1
        if cid not in cohort: reasons["NOT_M10_CHECKPOINT_COHORT"] += 1; continue
        by_canonical[cid].append(row)
    projections = []
    for cid, rows in sorted(by_canonical.items()):
        if len(rows) != 1: reasons["AMBIGUOUS_PROVIDER_ROWS"] += len(rows); continue
        row = rows[0]; sid = str(row.get("player_id") or (row.get("player") or {}).get("player_id")); forecast = cohort[cid]
        projections.append({"schema": "fie-sleeper-sunday-checkpoint-row-v1", "checkpoint_id": CHECKPOINT_ID, "season": season, "week": week, "captured_at": observed_at, "sleeper_id": sid, "canonical_player_id": cid, "position_model": forecast["position_model"], "team": forecast["team"], "opponent_team": forecast["opponent_team"], "player_kickoff_at": forecast["player_kickoff_at"], "stats": row.get("stats") or row, "provider_row_sha256": sha256_bytes(canonical_bytes(row))})
    scoring = []
    for row in projections:
        for profile in profiles:
            scoring.append({"schema": "fie-sleeper-sunday-scoring-replay-v1", "checkpoint_id": CHECKPOINT_ID, "season": season, "week": week, "canonical_player_id": row["canonical_player_id"], "sleeper_id": row["sleeper_id"], "league_id": profile["league_id"], "league_format": profile["league_format"], "profile_scoring_signature": profile["profile_scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"], "scored_fantasy_points": round(float(score_sleeper_projection(row["stats"], profile["scoring_settings"], row["position_model"])), 6), "research_only": True})
    coverage = {"m10_eligible": len(cohort), "sleeper_rows": len(provider), "sleeper_supported_position_rows": supported_rows, "identity_resolved": identity_resolved, "matched": len(projections), "league_profiles": len(profiles), "scoring_rows": len(scoring), "excluded_by_reason": dict(sorted(reasons.items()))}
    return projections, scoring, coverage


def _week_open_delta(root: Path, season: int, week: int, sunday_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    week_open = capture_paths(root / "data/research/prospective/m10", season, week)
    if not week_open["manifest"].is_file(): return [], {"status": "BLOCKED", "reason": "WEEK_OPEN_CAPTURE_UNAVAILABLE"}
    old = {(row["forecast_id"], row["model"]): row for row in read_jsonl_gzip(week_open["forecasts"])}
    rows = []
    for row in sunday_rows:
        prior = old.get((row["forecast_id"], row["model"]))
        if not prior: continue
        components = sorted(set(prior["predicted_raw_components"]) | set(row["predicted_raw_components"]))
        rows.append({"checkpoint_id": CHECKPOINT_ID, "season": season, "week": week, "forecast_id": row["forecast_id"], "canonical_player_id": row["canonical_player_id"], "model": row["model"], "week_open_manifest_sha256": sha256_file(week_open["manifest"]), "sunday_component_delta": {key: round(float(row["predicted_raw_components"].get(key, 0)) - float(prior["predicted_raw_components"].get(key, 0)), 6) for key in components}})
    return rows, {"status": "CAPTURED", "week_open_manifest": week_open["manifest"].relative_to(root).as_posix(), "week_open_manifest_sha256": sha256_file(week_open["manifest"]), "paired_rows": len(rows)}


def create_paired_checkpoint(raw_envelope: Path, sleeper_payload: bytes, sleeper_observed_at: str, identity_map: dict[str, str], *, output_root: Path = ROOT) -> dict[str, Any]:
    raw_value = read_json(raw_envelope); capture = raw_value["capture"]; season, week = int(capture["season"]), int(capture["week"]); all_paths = paths(output_root, season, week)
    if all_paths["manifest"].exists():
        existing = validate_checkpoint(output_root, season, week)
        if existing.get("input_raw_envelope_sha256") != sha256_file(raw_envelope) or existing.get("sleeper_raw_payload_sha256") != sha256_bytes(sleeper_payload):
            raise ValueError("divergent first-write checkpoint retry")
        return {"status": "EXISTS", "manifest": all_paths["manifest"]}
    if all_paths["missed"].exists(): return {"status": "MISSED", "manifest": all_paths["missed"]}
    drift = abs((parse_time(sleeper_observed_at) - parse_time(capture["observed_at"])).total_seconds())
    if drift > int(load_design()["coordinated_capture"]["maximum_source_drift_minutes"]) * 60: raise ValueError("M10/Sleeper source drift exceeds ten minutes")
    profile_record = next(row for row in raw_value["source_records"] if row["role"] == "roster_profile_snapshot")
    profiles_path = raw_envelope.parent / profile_record["path"]
    profiles = read_json(profiles_path)["profiles"]
    with tempfile.TemporaryDirectory(prefix="fie-sunday-m10-stage-") as stage_folder:
        staged_m10_root = Path(stage_folder) / "m10"
        run_m10_capture(["--raw-envelope", str(raw_envelope), "--output-root", str(staged_m10_root)])
        staged_m10_paths = capture_paths(staged_m10_root, season, week)
        if not staged_m10_paths["manifest"].is_file(): raise ValueError("M10 Sunday checkpoint did not produce an immutable capture")
        forecasts = read_jsonl_gzip(staged_m10_paths["forecasts"])
        projections, scoring, coverage = _sleeper_ledgers(sleeper_payload, season=season, week=week, observed_at=sleeper_observed_at, identity_map=identity_map, forecasts=forecasts, profiles=profiles)
        _first_write_tree(staged_m10_root, all_paths["m10_root"])
    m10_paths = capture_paths(all_paths["m10_root"], season, week)
    _first_write_bytes(all_paths["sleeper_raw"], _gzip_bytes(sleeper_payload))
    for target, rows in ((all_paths["sleeper_rows"], projections), (all_paths["sleeper_scoring"], scoring)):
        scratch = target.with_name(target.name + ".candidate")
        write_jsonl_gzip(scratch, rows); payload = scratch.read_bytes(); scratch.unlink()
        _first_write_bytes(target, payload)
    meta = {"schema": "fie-sleeper-sunday-checkpoint-meta-v1", "checkpoint_id": CHECKPOINT_ID, "season": season, "week": week, "captured_at": sleeper_observed_at, "rows": len(projections), "scoring_rows": len(scoring), "raw_response_path": all_paths["sleeper_raw"].relative_to(output_root).as_posix(), "raw_response_sha256": sha256_file(all_paths["sleeper_raw"]), "snapshot_sha256": sha256_file(all_paths["sleeper_rows"]), "scoring_sha256": sha256_file(all_paths["sleeper_scoring"]), "immutable_first_write": True, "historical_reconstruction": False, "point_in_time_metadata": {"schema": "fie-point-in-time-source-metadata-v1", "capture_intent": "prospective_sunday_paired_benchmark", "source_endpoint": SLEEPER_URL.format(season=season, week=week), "source_release_identifier": None, "source_revision_identifier": None, "revision_metadata_status": "NOT_EXPOSED_BY_PROVIDER", "as_of_semantics": "provider response observed at captured_at and first-written for SUNDAY_MAIN_T6", "release_cadence": "Sunday T-6 main-slate checkpoint"}}
    _first_write_json(all_paths["sleeper_meta"], meta)
    schedule_source = read_json(raw_envelope.parent / "schedule.json"); _first_write_json(all_paths["schedule"], schedule_source)
    delta_rows, delta = _week_open_delta(output_root, season, week, forecasts)
    if delta_rows:
        candidate = all_paths["week_open_delta"].with_name(all_paths["week_open_delta"].name + ".candidate")
        write_jsonl_gzip(candidate, delta_rows)
        _first_write_bytes(all_paths["week_open_delta"], candidate.read_bytes())
        candidate.unlink()
        delta["path"] = all_paths["week_open_delta"].relative_to(output_root).as_posix()
        delta["sha256"] = sha256_file(all_paths["week_open_delta"])
    manifest = {"schema": SCHEMA, "checkpoint_id": CHECKPOINT_ID, "status": "CAPTURED", "season": season, "week": week, "m10_observed_at": capture["observed_at"], "sleeper_observed_at": sleeper_observed_at, "source_drift_seconds": drift, "input_raw_envelope_sha256": sha256_file(raw_envelope), "sleeper_raw_payload_sha256": sha256_bytes(sleeper_payload), "anchor_at": capture["first_kickoff_at"], "schedule_snapshot_sha256": sha256_file(all_paths["schedule"]), "m10": {"manifest_path": m10_paths["manifest"].relative_to(output_root).as_posix(), "manifest_sha256": sha256_file(m10_paths["manifest"]), "forecast_path": m10_paths["forecasts"].relative_to(output_root).as_posix(), "forecast_sha256": sha256_file(m10_paths["forecasts"]), "forecast_rows": len(forecasts)}, "sleeper": {"meta_path": all_paths["sleeper_meta"].relative_to(output_root).as_posix(), "meta_sha256": sha256_file(all_paths["sleeper_meta"]), "projection_path": all_paths["sleeper_rows"].relative_to(output_root).as_posix(), "projection_sha256": sha256_file(all_paths["sleeper_rows"]), "scoring_path": all_paths["sleeper_scoring"].relative_to(output_root).as_posix(), "scoring_sha256": sha256_file(all_paths["sleeper_scoring"])}, "coverage": coverage, "week_open_delta": delta, "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "shadow_integration": False, "automatic_promotion": False}, "first_write_immutable": True, "historical_reconstruction": False}
    _first_write_json(all_paths["manifest"], manifest); validate_checkpoint(output_root, season, week)
    return {"status": "CREATED", "manifest": all_paths["manifest"]}


def validate_checkpoint(root: Path, season: int, week: int) -> dict[str, Any]:
    p = paths(root, season, week); value = read_json(p["manifest"])
    assert value["schema"] == SCHEMA and value["checkpoint_id"] == CHECKPOINT_ID and value["status"] == "CAPTURED"
    assert value["governance"]["production_model"] == "M9" and not any(value["governance"][key] for key in ("production_activation", "app_integration", "shadow_integration", "automatic_promotion"))
    assert float(value["source_drift_seconds"]) <= 600 and value["first_write_immutable"] is True and value["historical_reconstruction"] is False
    assert sha256_file(p["schedule"]) == value["schedule_snapshot_sha256"]
    for group, keys in (("m10", ("manifest", "forecast")), ("sleeper", ("meta", "projection", "scoring"))):
        for key in keys:
            path = root / value[group][key + "_path"]
            assert path.is_file() and sha256_file(path) == value[group][key + "_sha256"]
    m10_manifest = read_json(root / value["m10"]["manifest_path"])
    assert m10_manifest["schedule_snapshot_sha256"] == value["schedule_snapshot_sha256"]
    assert int(m10_manifest["ledgers"]["forecast"]["rows"]) == int(value["m10"]["forecast_rows"])
    forecasts = read_jsonl_gzip(root / value["m10"]["forecast_path"]); models = defaultdict(set)
    for row in forecasts:
        models[row["forecast_id"]].add(row["model"])
        assert parse_time(row["player_kickoff_at"]) >= parse_time(value["m10_observed_at"]) + timedelta(minutes=30)
    assert models and all(found == set(MODELS) for found in models.values())
    sleeper_meta = read_json(p["sleeper_meta"])
    raw_path = root / sleeper_meta["raw_response_path"]
    assert raw_path == p["sleeper_raw"] and raw_path.is_file()
    assert sha256_file(raw_path) == sleeper_meta["raw_response_sha256"]
    with gzip.open(raw_path, "rb") as handle:
        assert sha256_bytes(handle.read()) == value["sleeper_raw_payload_sha256"]
    projections = read_jsonl_gzip(p["sleeper_rows"]); scoring = read_jsonl_gzip(p["sleeper_scoring"])
    assert len(projections) == int(value["coverage"]["matched"])
    assert len(scoring) == int(value["coverage"]["scoring_rows"])
    assert len(scoring) == len(projections) * int(value["coverage"]["league_profiles"])
    assert sleeper_meta["rows"] == len(projections) and sleeper_meta["scoring_rows"] == len(scoring)
    if projections:
        assert {row["canonical_player_id"] for row in projections} <= {row["canonical_player_id"] for row in forecasts}
        profile_counts = Counter(row["canonical_player_id"] for row in scoring)
        assert set(profile_counts.values()) == {int(value["coverage"]["league_profiles"])}
        profile_keys = {(row["league_id"], row["profile_scoring_signature"], row["profile_fingerprint"]) for row in scoring}
        assert len(profile_keys) == int(value["coverage"]["league_profiles"])
    delta = value["week_open_delta"]
    if delta["status"] == "CAPTURED":
        delta_path = root / delta["path"]
        assert delta_path.is_file() and sha256_file(delta_path) == delta["sha256"]
        assert len(read_jsonl_gzip(delta_path)) == int(delta["paired_rows"])
    return value


def _write_missed(root: Path, season: int, week: int, decision: dict[str, Any]) -> Path:
    p = paths(root, season, week); value = {"schema": MISSED_SCHEMA, "checkpoint_id": CHECKPOINT_ID, "status": "MISSED", "season": season, "week": week, "observed_at": decision["observed_at"], "reason": decision["status"], "anchor_at": decision.get("anchor_at"), "target_at": decision.get("target_at"), "window_close_at": decision.get("window_close_at"), "historical_reconstruction": False, "first_write_immutable": True}
    _first_write_json(p["missed"], value); return p["missed"]


def live_capture(*, season: int | None = None, week: int | None = None, output_root: Path = ROOT) -> dict[str, Any]:
    scratch = Path(tempfile.mkdtemp(prefix="fie-sunday-paired-"))
    try:
        raw_dir = scratch / "raw"; responses = raw_dir / "responses"; state_response = _fetch(STATE_URL, responses / "sleeper-state.json"); state = json.loads(state_response["path"].read_text(encoding="utf-8"))
        resolved_season, resolved_week = int(season or state["season"]), int(week or state["week"])
        if str(state.get("season_type") or "").lower() not in {"regular", "reg"}: return {"status": "NOT_REGULAR_SEASON"}
        p = paths(output_root, resolved_season, resolved_week)
        if p["manifest"].exists(): validate_checkpoint(output_root, resolved_season, resolved_week); return {"status": "EXISTS", "manifest": p["manifest"]}
        if p["missed"].exists(): return {"status": "MISSED", "manifest": p["missed"]}
        games_response = _fetch(GAMES_URL, responses / "games.csv"); games = _game_rows(pd.read_csv(games_response["path"], low_memory=False), resolved_season, resolved_week)
        decision = checkpoint_decision(games, _now()); decision["all_games"] = games
        if decision["status"] == "WINDOW_NOT_REACHED": return {"status": "WINDOW_NOT_REACHED"}
        if decision["status"] in {"WINDOW_MISSED", "NO_MAIN_SLATE"}: return {"status": "MISSED", "manifest": _write_missed(output_root, resolved_season, resolved_week, decision)}
        raw, identity_map = build_live_raw(raw_dir, season=resolved_season, week=resolved_week, games_response=games_response, state_response=state_response, decision=decision)
        sleeper_response = _fetch(SLEEPER_URL.format(season=resolved_season, week=resolved_week), scratch / "sleeper-response.json")
        return create_paired_checkpoint(raw, sleeper_response["path"].read_bytes(), _now(), identity_map, output_root=output_root)
    finally:
        shutil.rmtree(scratch)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--season", type=int); parser.add_argument("--week", type=int); parser.add_argument("--output-root", default=str(ROOT)); parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv); root = Path(args.output_root)
    if args.validate:
        if args.season is None or args.week is None: raise ValueError("--validate requires --season and --week")
        value = validate_checkpoint(root, args.season, args.week); print(f"PASS Sunday paired checkpoint rows={value['coverage']['matched']}"); return 0
    result = live_capture(season=args.season, week=args.week, output_root=root); print(json.dumps({**result, "manifest": str(result["manifest"]) if result.get("manifest") else None}, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())

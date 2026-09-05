#!/usr/bin/env python3
"""R8B's governed, frozen-lock weekly input producer.

The module has no HTTP client.  A caller must first persist and hash public-source
responses in the R7 source-envelope contract, then pass this producer the
normalized, hash-locked payloads.  Keeping transport outside this module makes
the time boundary, feature construction, and model inference independently
testable and prevents a projection endpoint from entering the candidate matrix.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from m10_prospective_capture_contract import (
    MODELS, POSITIONS, ROOT, canonical_bytes, capture_hours, read_json,
    sha256_bytes, sha256_file, write_json, write_jsonl_gzip,
)
from m10_prospective_features import FEATURES, build_features, feature_record
from m10_prospective_season_lock import HGB_SCHEMA, hgb_predict, ridge_predict
from m10_prospective_season_lock_v2 import _constrain, _reconcile


RAW_SCHEMA = "fie-m10-prospective-weekly-raw-envelope-v1"
INPUT_SCHEMA = "fie-m10-prospective-operational-input-v2"
REQUIRED_RAW_ROLES = {"schedule", "completed_games", "identity_snapshot", "roster_profile_snapshot"}


def _safe(root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("weekly producer input path must be a safe relative path")
    return root / path


def _time_record(record: dict[str, Any], observed_at: str) -> None:
    from m10_prospective_capture_contract import parse_time
    assert record.get("point_in_time_eligible") is True
    assert record.get("historical_reconstruction") is False
    assert record.get("source_identity") and record.get("sha256")
    assert parse_time(str(record["captured_at"])) <= parse_time(observed_at)
    assert parse_time(str(record["as_of"])) <= parse_time(observed_at)


def validate_raw_envelope(path: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    value, root = read_json(path), path.parent
    assert value.get("schema") == RAW_SCHEMA
    assert value.get("research_only") is True and value.get("production_model") == "M9"
    assert not any(value.get(key) for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "automatic_promotion", "historical_reconstruction"))
    capture = value["capture"]
    assert int(capture["season"]) == 2026 and int(capture["week"]) > 0
    observed, kickoff = str(capture["observed_at"]), str(capture["first_kickoff_at"])
    assert float(capture["hours_before_first_kickoff"]) == capture_hours(observed, kickoff)
    records = value.get("source_records") or []
    assert {str(row.get("role")) for row in records} == REQUIRED_RAW_ROLES
    paths: dict[str, Path] = {}
    for record in records:
        item = _safe(root, str(record["path"]))
        assert item.is_file() and sha256_file(item) == str(record["sha256"])
        _time_record(record, observed)
        paths[str(record["role"])] = item
    schedule = read_json(paths["schedule"])
    assert int(schedule["season"]) == int(capture["season"]) and int(schedule["week"]) == int(capture["week"])
    assert schedule.get("season_type") == "REG" and str(schedule["first_kickoff_at"]) == kickoff
    return value, paths


def _identity_targets(schedule: dict[str, Any], identity: dict[str, Any], *, season: int, week: int) -> pd.DataFrame:
    assert identity.get("governed_crosswalk") is True and int(identity.get("ambiguous_count", -1)) >= 0
    games = schedule.get("games") or []
    teams: dict[str, tuple[str, str]] = {}
    for game in games:
        home, away, kickoff = str(game["home_team"]), str(game["away_team"]), str(game["kickoff_at"])
        teams[home] = (away, kickoff); teams[away] = (home, kickoff)
    rows: list[dict[str, Any]] = []
    for player in identity.get("players") or []:
        position, team = str(player.get("position_model") or ""), str(player.get("team") or "")
        if position not in POSITIONS or team not in teams or not player.get("canonical_player_id"):
            continue
        opponent, kickoff = teams[team]
        rows.append({"season": season, "week": week, "canonical_player_id": str(player["canonical_player_id"]), "position_model": position, "team": team, "opponent_team": opponent, "player_kickoff_at": kickoff})
    assert rows, "no scheduled, unambiguous QB/RB/WR/TE candidates"
    assert len({row["canonical_player_id"] for row in rows}) == len(rows), "identity snapshot has duplicate canonical players"
    return pd.DataFrame(rows)


def _completed_rows(payload: dict[str, Any]) -> pd.DataFrame:
    rows = payload.get("player_games") or []
    assert rows, "completed-game public-core payload is empty"
    required = {"season", "week", "canonical_player_id", "position_model", "team"}
    assert all(required <= set(row) for row in rows)
    frame = pd.DataFrame(rows)
    assert set(frame["position_model"].astype(str)) <= set(POSITIONS)
    assert (pd.to_numeric(frame["week"], errors="coerce") > 0).all()
    return frame


def _parameter_hash(lock: dict[str, Any], position: str, model: str) -> str:
    values = {target: variants[model]["parameter_sha256"] for target, variants in lock["models"][position].items()}
    return sha256_bytes(canonical_bytes(values))


def _score(raw: dict[str, Any], scoring: dict[str, Any]) -> float:
    from fie_research import score_rows
    value = float(score_rows(pd.DataFrame([{**raw}]), scoring).iloc[0])
    if not np.isfinite(value):
        raise ValueError("exact scorer produced a non-finite value")
    return value


def _score_many(rows: list[dict[str, Any]], scoring: dict[str, Any]) -> list[float]:
    from fie_research import score_rows
    values = [float(value) for value in score_rows(pd.DataFrame(rows), scoring).tolist()]
    if not values or not all(np.isfinite(value) for value in values):
        raise ValueError("exact scorer produced a non-finite distribution")
    return values


def _residual_components(lock: dict[str, Any], row: dict[str, Any]) -> list[dict[str, float]]:
    samples = [sample for sample in lock["residual_samples"] if sample["position_model"] == row["position_model"] and sample["model"] == row["model"]]
    assert samples, "frozen residual vectors absent for position/candidate"
    point = dict(row["predicted_raw_components"])
    return [_constrain({name: float(point[name]) + float(sample["residuals"].get(name, 0.0)) for name in point}) for sample in samples]


def _quantiles(values: list[float]) -> dict[str, float]:
    assert values and all(np.isfinite(value) for value in values)
    return {str(q): float(np.quantile(np.asarray(values, dtype=float), q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}


def attach_default_distributions(rows: list[dict[str, Any]], lock: dict[str, Any]) -> None:
    """Attach only marginal default-PPR quantiles; samples remain frozen in the lock."""
    from fie_research import DEFAULT_PPR
    for row in rows:
        row["prediction_quantiles"] = _quantiles(_score_many(_residual_components(lock, row), DEFAULT_PPR))
        row["distribution_interpretation"] = "player_level_marginal_not_joint_simulation"


def exact_profile_scoring(rows: list[dict[str, Any]], profiles: list[dict[str, Any]], lock: dict[str, Any]) -> list[dict[str, Any]]:
    """Replay each frozen residual vector through each captured exact profile."""
    scorer_hash = sha256_file(ROOT / "research/fie_research.py")
    output: list[dict[str, Any]] = []
    for row in rows:
        samples = _residual_components(lock, row)
        for profile in profiles:
            scoring = dict(profile["scoring_settings"])
            output.append({
                "forecast_id": row["forecast_id"], "canonical_player_id": row["canonical_player_id"], "model": row["model"],
                "league_id": profile["league_id"], "league_format": profile["league_format"], "profile_scoring_signature": profile["profile_scoring_signature"], "profile_fingerprint": profile["profile_fingerprint"],
                "scored_fantasy_points": _score(row["predicted_raw_components"], scoring), "scored_prediction_quantiles": _quantiles(_score_many(samples, scoring)),
                "distribution_interpretation": "player_level_marginal_not_joint_simulation", "scoring_registry_version_sha256": scorer_hash, "research_only": True,
            })
    return output


def build_decision_traces(profiles: list[dict[str, Any]], roster_states: list[dict[str, Any]], scoring: list[dict[str, Any]], *, capture: dict[str, Any]) -> list[dict[str, Any]]:
    """Produce counterfactual legal-choice traces or a symmetric typed blocker."""
    by_profile: dict[str, list[dict[str, Any]]] = {}
    for row in scoring: by_profile.setdefault(str(row["league_id"]), []).append(row)
    state_by_league = {str(row.get("league_id")): row for row in roster_states}
    output: list[dict[str, Any]] = []
    for profile in profiles:
        league_id, fmt = str(profile["league_id"]), str(profile["league_format"])
        state = state_by_league.get(league_id) or {}
        domain = "chopped" if "CHOPPED" in fmt else ("best_ball" if "BESTBALL" in fmt else "start_sit")
        legal_players = {str(value) for value in state.get("legal_canonical_player_ids") or []}
        slots = int(state.get("starter_slots") or 0)
        complete = state.get("complete") is True
        rows = by_profile.get(league_id) or []
        ids_by_model = {model: {row["forecast_id"] for row in rows if row["model"] == model and row["canonical_player_id"] in legal_players} for model in MODELS}
        valid = complete and slots > 0 and all(ids_by_model[model] == ids_by_model["M9"] and len(ids_by_model[model]) >= slots for model in MODELS)
        for model in MODELS:
            base = {"trace_id": f"{capture['season']}-{int(capture['week']):02d}-{league_id}-{domain}-{model}", "season": int(capture["season"]), "week": int(capture["week"]), "captured_at": capture["captured_at"], "domain": domain, "league_id": league_id, "league_format": fmt, "model": model, "research_only": True, "production_recommendation_changed": False}
            if not valid:
                output.append({**base, "status": "BLOCKED_INCOMPLETE_LEGAL_ROSTER", "blocker": "INCOMPLETE_LEGAL_ROSTER_AT_CUTOFF", "legal_forecast_ids": [], "selected_forecast_ids": [], "predicted_utility": None})
                continue
            legal = [row for row in rows if row["model"] == model and row["forecast_id"] in ids_by_model[model]]
            key = (lambda row: (-float(row["scored_prediction_quantiles"]["0.1"]), -float(row["scored_prediction_quantiles"]["0.5"]), str(row["canonical_player_id"]))) if domain == "chopped" else (lambda row: (-float(row["scored_fantasy_points"]), str(row["canonical_player_id"])))
            chosen = sorted(legal, key=key)[:slots]
            utility = sum(float(row["scored_prediction_quantiles"]["0.1"] if domain == "chopped" else row["scored_fantasy_points"]) for row in chosen)
            output.append({**base, "status": "CAPTURED", "legal_forecast_ids": sorted(ids_by_model[model]), "selected_forecast_ids": [row["forecast_id"] for row in chosen], "predicted_utility": utility, "constraints_sha256": sha256_bytes(canonical_bytes({"league_id": league_id, "slots": slots, "domain": domain, "profile": profile["profile_fingerprint"]}))})
    return output


def _point_rows(lock: dict[str, Any], history: pd.DataFrame, target: pd.DataFrame, *, capture: dict[str, Any], source_bundle_sha256: str) -> list[dict[str, Any]]:
    features = build_features(history, target)
    prospective = features[features["_completed"] == False].copy()  # noqa: E712
    assert len(prospective) == len(target)
    rows: list[dict[str, Any]] = []
    all_targets = sorted({name for per_position in lock["models"].values() for name in per_position})
    for model in MODELS:
        predicted: list[dict[str, Any]] = []
        for item in prospective.to_dict("records"):
            position = str(item["position_model"])
            values = [float("nan") if item[name] is None or pd.isna(item[name]) else float(item[name]) for name in FEATURES]
            vector: dict[str, float] = {}
            for name, variants in lock["models"][position].items():
                spec = variants[model]
                vector[name] = (hgb_predict if spec["schema"] == HGB_SCHEMA else ridge_predict)(spec, values)
            predicted.append({"season": int(item["season"]), "week": int(item["week"]), "team": str(item["team"]), "position_model": position, "prediction": vector, "source": item})
        for item in _reconcile(predicted, all_targets):
            source, point = item["source"], item["prediction"]
            rows.append({
                "forecast_id": f"{int(source['season'])}-{int(source['week']):02d}-{source['canonical_player_id']}",
                "season": int(source["season"]), "week": int(source["week"]), "captured_at": str(capture["observed_at"]), "first_kickoff_at": str(capture["first_kickoff_at"]),
                "canonical_player_id": str(source["canonical_player_id"]), "position_model": str(source["position_model"]), "team": str(source["team"]), "opponent_team": str(source["opponent_team"]), "player_kickoff_at": str(source["player_kickoff_at"]),
                "model": model, "predicted_raw_components": _constrain(point), "features": feature_record(pd.Series(source)),
                "event_probabilities": {"any_touchdown": None, "blocker": "NOT_DEFINED_BY_2026_SEASON_LOCK"},
                "availability_probability": None, "availability_blocker": "EXTERNALLY_GOVERNED_NOT_INVENTED",
                "source_bundle_sha256": source_bundle_sha256, "model_parameter_sha256": _parameter_hash(lock, str(source["position_model"]), model),
                "schedule_snapshot_sha256": str(capture["schedule_snapshot_sha256"]),
                "subgroups": {"position": str(source["position_model"]), "week_range": "EARLY" if int(source["week"]) <= 6 else "LATE", "team_change": "UNKNOWN", "rookie_young_player": "UNKNOWN", "prior_participation_band": "UNKNOWN"},
                "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "shadow_integration": False},
            })
    assert {row["model"] for row in rows} == set(MODELS)
    grouped: dict[str, set[str]] = {}
    for row in rows: grouped.setdefault(row["forecast_id"], set()).add(row["model"])
    assert grouped and all(models == set(MODELS) for models in grouped.values())
    return sorted(rows, key=lambda row: (row["forecast_id"], row["model"]))


def build_weekly_input(raw_envelope: Path, output_dir: Path, *, source_bundle: Path) -> dict[str, Any]:
    """Make the three immutable adapter inputs from pre-captured public core data."""
    value, paths = validate_raw_envelope(raw_envelope)
    capture = value["capture"]
    hours = float(capture["hours_before_first_kickoff"])
    if hours > 18.0:
        return {"status": "WINDOW_NOT_REACHED", "manifest": None}
    if hours < 0.0:
        return {"status": "POST_KICKOFF", "manifest": None}
    from m10_prospective_activation_guard import validate_activation_lock
    lock = validate_activation_lock(ROOT)
    assert source_bundle.is_file()
    bundle = read_json(source_bundle)
    assert bundle.get("schema") == "fie-m10-prospective-weekly-source-bundle-v1"
    assert bundle.get("research_only") is True and int(bundle["season"]) == int(capture["season"]) and int(bundle["week"]) == int(capture["week"])
    source_hash = sha256_file(source_bundle)
    schedule, history, target = read_json(paths["schedule"]), _completed_rows(read_json(paths["completed_games"])), _identity_targets(read_json(paths["schedule"]), read_json(paths["identity_snapshot"]), season=int(capture["season"]), week=int(capture["week"]))
    forecasts = _point_rows(lock, history, target, capture={**capture, "schedule_snapshot_sha256": sha256_file(paths["schedule"])}, source_bundle_sha256=source_hash)
    attach_default_distributions(forecasts, lock)
    profiles_payload = read_json(paths["roster_profile_snapshot"])
    profiles = profiles_payload.get("profiles") or []
    assert int(profiles_payload.get("enabled_league_count", -1)) == 22 and len(profiles) == 22
    out = output_dir; out.mkdir(parents=True, exist_ok=True)
    forecasts_path, profiles_path, rosters_path = out / "forecast-rows.jsonl.gz", out / "profiles.json", out / "league-rosters.json"
    write_jsonl_gzip(forecasts_path, forecasts); write_json(profiles_path, {"profiles": profiles}); write_json(rosters_path, {"league_roster_states": profiles_payload.get("league_roster_states") or []})
    records = []
    for role, path in (("forecast_rows", forecasts_path), ("profile_snapshot", profiles_path), ("decision_inputs", rosters_path)):
        records.append({"role": role, "path": path.name, "sha256": sha256_file(path), "captured_at": capture["observed_at"], "as_of": capture["observed_at"], "point_in_time_eligible": True, "historical_reconstruction": False, "source_identity": "fie-r8b-governed-weekly-producer"})
    manifest = out / "input-manifest.json"
    write_json(manifest, {"schema": INPUT_SCHEMA, "fixture": bool(value.get("fixture") is True), "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False, "live_provider_request": False, "capture": {"season": capture["season"], "week": capture["week"], "captured_at": capture["observed_at"], "first_kickoff_at": capture["first_kickoff_at"], "hours_before_first_kickoff": hours, "schedule_snapshot_sha256": sha256_file(paths["schedule"])}, "season_lock_sha256": lock["season_lock_sha256"], "source_bundle_sha256": source_hash, "source_records": records})
    return {"status": "CREATED", "manifest": manifest}


def fixture_raw_envelope(root: Path, observed_at: str = "2026-09-09T06:00:00+00:00") -> Path:
    """A no-network R8B fixture with all 22 profile rows and six formats."""
    kickoff = "2026-09-10T00:00:00+00:00"
    raw = root / "raw"; raw.mkdir(parents=True, exist_ok=True)
    teams = [("AAA", "BBB"), ("CCC", "DDD"), ("EEE", "FFF"), ("GGG", "HHH")]
    positions = list(POSITIONS)
    games = [{"home_team": home, "away_team": away, "kickoff_at": kickoff} for home, away in teams]
    players = [{"canonical_player_id": f"fixture-{position.lower()}", "position_model": position, "team": teams[index][0]} for index, position in enumerate(positions)]
    completed: list[dict[str, Any]] = []
    for week in range(1, 5):
        for index, player in enumerate(players):
            volume = float(8 + index + week)
            completed.append({"season": 2026, "week": week, **player, "attempts": volume if player["position_model"] == "QB" else 0.0, "completions": max(0.0, volume - 2) if player["position_model"] == "QB" else 0.0, "passing_yards": volume * 12 if player["position_model"] == "QB" else 0.0, "passing_tds": 1.0 if player["position_model"] == "QB" else 0.0, "interceptions": 0.0, "carries": volume if player["position_model"] in {"RB", "WR", "TE"} else 2.0, "rushing_yards": volume * 2, "rushing_tds": 0.0, "targets": volume if player["position_model"] in {"RB", "WR", "TE"} else 0.0, "receptions": max(0.0, volume - 2) if player["position_model"] in {"RB", "WR", "TE"} else 0.0, "receiving_yards": volume * 5, "receiving_tds": 0.0})
    formats = ("REDRAFT", "DYNASTY", "CHOPPED", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL")
    profiles = [{"league_id": f"fixture-{index:02d}", "league_format": formats[index % len(formats)], "profile_scoring_signature": f"fixture-score-{index:02d}", "profile_fingerprint": sha256_bytes(f"fixture-profile-{index}".encode()), "scoring_settings": {"pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0, "rush_yd": 0.1, "rush_td": 6.0, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0}, "captured_at": observed_at} for index in range(22)]
    payloads = {
        "schedule": {"season": 2026, "week": 5, "season_type": "REG", "first_kickoff_at": kickoff, "games": games},
        "completed_games": {"player_games": completed},
        "identity_snapshot": {"governed_crosswalk": True, "ambiguous_count": 0, "players": players},
        "roster_profile_snapshot": {"enabled_league_count": 22, "profiles": profiles, "league_roster_states": [{"league_id": profile["league_id"], "complete": True, "starter_slots": 1, "legal_canonical_player_ids": [player["canonical_player_id"] for player in players]} for profile in profiles]},
    }
    records = []
    for role, payload in payloads.items():
        path = raw / f"{role}.json"; write_json(path, payload)
        records.append({"role": role, "path": path.name, "sha256": sha256_file(path), "captured_at": observed_at, "as_of": observed_at, "point_in_time_eligible": True, "historical_reconstruction": False, "source_identity": f"fixture-public-core-{role}", "release_or_etag": "fixture-r8b-v1"})
    manifest = raw / "raw-envelope.json"
    write_json(manifest, {"schema": RAW_SCHEMA, "fixture": True, "research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "runtime_integration": False, "shadow_integration": False, "automatic_promotion": False, "historical_reconstruction": False, "capture": {"season": 2026, "week": 5, "observed_at": observed_at, "first_kickoff_at": kickoff, "hours_before_first_kickoff": capture_hours(observed_at, kickoff)}, "source_records": records})
    return manifest

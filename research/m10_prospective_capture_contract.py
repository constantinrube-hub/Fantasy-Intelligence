#!/usr/bin/env python3
"""Stdlib-only deterministic storage contract for Tranche 7B.

This module intentionally creates only synthetic, no-network evidence.  Real
pregame M9/M10 inputs, scheduled collection, and outcome ingestion belong to
Tranche 7C after this contract has been validated.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/m10-prospective-evidence-contract.json"
SCHEMA = "fie-m10-prospective-capture-v1"
MISSED_SCHEMA = "fie-m10-prospective-missed-capture-v1"
OUTCOME_SCHEMA = "fie-m10-prospective-outcome-v1"
MODELS = ("M9", "M10_LINEAR", "M10_HGB")
POSITIONS = ("QB", "RB", "WR", "TE")
QUANTILES = ("0.1", "0.25", "0.5", "0.75", "0.9")
SUBGROUPS = ("position", "week_range", "team_change", "rookie_young_player", "prior_participation_band")
MISSED_REASONS = {"WINDOW_NOT_REACHED", "WINDOW_MISSED", "INPUTS_UNAVAILABLE", "SCHEDULE_UNVERIFIABLE", "IDENTITY_UNRESOLVED"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_contract() -> dict[str, Any]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert value["schema"] == "fie-m10-prospective-evidence-contract-v1"
    assert value["models"] == list(MODELS)
    assert value["positions"] == list(POSITIONS)
    assert value["production_model"] == "M9"
    assert not any(value[key] for key in ("production_activation", "app_integration", "shadow_integration", "automatic_promotion"))
    return value


def contract_sha256() -> str:
    return sha256_bytes(canonical_bytes(load_contract()))


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def capture_hours(captured_at: str, first_kickoff_at: str) -> float:
    return round((parse_time(first_kickoff_at) - parse_time(captured_at)).total_seconds() / 3600.0, 6)


def week_dir(root: Path, category: str, season: int, week: int) -> Path:
    return root / category / str(season) / f"week_{week:02d}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl_gzip(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write platform-independent, deterministic gzip JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="\n") as text:
                for row in rows:
                    text.write(canonical_bytes(row).decode("utf-8"))
                    text.write("\n")


def read_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def fixture_players() -> list[dict[str, Any]]:
    return [
        {"canonical_player_id": "fixture-qb", "position": "QB", "team": "AAA", "opponent_team": "BBB", "player_kickoff_at": "2026-09-10T00:00:00+00:00", "team_change": "NO", "rookie_young_player": "NO", "prior_participation_band": "HIGH"},
        {"canonical_player_id": "fixture-rb", "position": "RB", "team": "CCC", "opponent_team": "DDD", "player_kickoff_at": "2026-09-10T00:00:00+00:00", "team_change": "YES", "rookie_young_player": "YES", "prior_participation_band": "MEDIUM"},
        {"canonical_player_id": "fixture-wr", "position": "WR", "team": "EEE", "opponent_team": "FFF", "player_kickoff_at": "2026-09-13T17:00:00+00:00", "team_change": "UNKNOWN", "rookie_young_player": "NO", "prior_participation_band": "LOW"},
        {"canonical_player_id": "fixture-te", "position": "TE", "team": "GGG", "opponent_team": "HHH", "player_kickoff_at": "2026-09-13T20:25:00+00:00", "team_change": "NO", "rookie_young_player": "YES", "prior_participation_band": "MEDIUM"},
    ]


def fixture_point(position_index: int, model_index: int) -> float:
    return round(8.0 + position_index * 1.5 + model_index * 0.35, 3)


def fixture_forecasts(season: int, week: int, captured_at: str, first_kickoff_at: str) -> list[dict[str, Any]]:
    source_hash = sha256_bytes(b"tranche7b-fixture-feature-bundle-v1")
    schedule_hash = sha256_bytes(b"tranche7b-fixture-schedule-v1")
    rows: list[dict[str, Any]] = []
    for position_index, player in enumerate(fixture_players()):
        for model_index, model in enumerate(MODELS):
            point = fixture_point(position_index, model_index)
            quantiles = {q: round(max(0.0, point + offset), 3) for q, offset in zip(QUANTILES, (-4.0, -2.0, 0.0, 2.0, 4.0))}
            probability: dict[str, Any]
            if model == "M10_HGB":
                probability = {"any_touchdown": round(min(0.95, 0.15 + point / 40.0), 6)}
            else:
                probability = {"any_touchdown": None, "blocker": f"NOT_DEFINED_FOR_{model}"}
            forecast_id = f"{season}-{week:02d}-{player['canonical_player_id']}"
            rows.append({
                "forecast_id": forecast_id,
                "season": season,
                "week": week,
                "captured_at": captured_at,
                "first_kickoff_at": first_kickoff_at,
                "canonical_player_id": player["canonical_player_id"],
                "position_model": player["position"],
                "team": player["team"],
                "opponent_team": player["opponent_team"],
                "player_kickoff_at": player["player_kickoff_at"],
                "model": model,
                "predicted_raw_components": {"opportunities": round(6.0 + position_index + model_index * 0.2, 3), "yards": round(35.0 + position_index * 8 + model_index, 3)},
                "predicted_fantasy_points_default": point,
                "prediction_quantiles": quantiles,
                "event_probabilities": probability,
                "source_bundle_sha256": source_hash,
                "model_parameter_sha256": sha256_bytes(f"tranche7b-fixture-{model}-parameters-v1".encode("utf-8")),
                "schedule_snapshot_sha256": schedule_hash,
                "subgroups": {
                    "position": player["position"],
                    "week_range": "EARLY",
                    "team_change": player["team_change"],
                    "rookie_young_player": player["rookie_young_player"],
                    "prior_participation_band": player["prior_participation_band"],
                },
                "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "shadow_integration": False},
            })
    return rows


def fixture_scoring_rows(forecasts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles = [
        {"league_id": "fixture-redraft", "league_format": "REDRAFT", "profile_scoring_signature": "fixture-ppr-v1", "profile_fingerprint": sha256_bytes(b"fixture-redraft-profile")},
        {"league_id": "fixture-bestball", "league_format": "REDRAFT_BESTBALL", "profile_scoring_signature": "fixture-bestball-v1", "profile_fingerprint": sha256_bytes(b"fixture-bestball-profile")},
    ]
    registry_hash = sha256_bytes(b"tranche7b-fixture-canonical-scorer-v1")
    rows: list[dict[str, Any]] = []
    for forecast in forecasts:
        for profile_index, profile in enumerate(profiles):
            rows.append({
                "forecast_id": forecast["forecast_id"], "canonical_player_id": forecast["canonical_player_id"], "model": forecast["model"],
                **profile,
                "scored_fantasy_points": round(float(forecast["predicted_fantasy_points_default"]) + profile_index * 0.5, 3),
                "scoring_registry_version_sha256": registry_hash,
                "research_only": True,
            })
    return rows


def fixture_decision_rows(forecasts: list[dict[str, Any]], season: int, week: int, captured_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain, league_id, fmt in (("start_sit", "fixture-redraft", "REDRAFT"), ("best_ball", "fixture-bestball", "REDRAFT_BESTBALL"), ("chopped", "fixture-chopped", "CHOPPED")):
        for model in MODELS:
            eligible = [row["forecast_id"] for row in forecasts if row["model"] == model]
            chosen = max((row for row in forecasts if row["model"] == model), key=lambda row: row["predicted_fantasy_points_default"])
            rows.append({
                "trace_id": f"{season}-{week:02d}-{domain}-{model}", "season": season, "week": week, "captured_at": captured_at,
                "domain": domain, "league_id": league_id, "league_format": fmt, "model": model,
                "legal_forecast_ids": eligible, "selected_forecast_ids": [chosen["forecast_id"]],
                "predicted_utility": chosen["predicted_fantasy_points_default"], "constraints_sha256": sha256_bytes(f"fixture-{domain}-constraints-v1".encode("utf-8")),
                "research_only": True, "production_recommendation_changed": False,
            })
    return rows


def fixture_outcome_rows(forecasts: list[dict[str, Any]], season: int, week: int) -> list[dict[str, Any]]:
    unique = {row["forecast_id"]: row for row in forecasts}
    rows = []
    for forecast_id, row in sorted(unique.items()):
        rows.append({
            "outcome_id": f"outcome-{forecast_id}-r1", "forecast_id": forecast_id, "canonical_player_id": row["canonical_player_id"],
            "season": season, "week": week, "source": "TRANCHE7B_SYNTHETIC_FIXTURE", "source_release_or_commit": "fixture-r1",
            "observed_at": "2026-09-16T12:00:00+00:00", "revision": 1, "raw_outcomes": {"fantasy_points_default": 10.0},
            "source_payload_sha256": sha256_bytes(f"fixture-outcome-{forecast_id}-r1".encode("utf-8")),
        })
    return rows


def capture_paths(root: Path, season: int, week: int) -> dict[str, Path]:
    forecast = week_dir(root, "forecasts", season, week)
    return {
        "forecast_dir": forecast,
        "manifest": forecast / "capture-manifest.json",
        "missed": forecast / "missed-capture.json",
        "forecasts": forecast / "forecast.jsonl.gz",
        "scoring": week_dir(root, "scoring-replay", season, week) / "scoring-replay.jsonl.gz",
        "decisions": week_dir(root, "decision-traces", season, week) / "decision-traces.jsonl.gz",
        "outcome_dir": week_dir(root, "outcomes", season, week) / "revision_1",
    }


def create_fixture_capture(root: Path, season: int, week: int, captured_at: str, first_kickoff_at: str) -> dict[str, Any]:
    contract = load_contract()
    paths = capture_paths(root, season, week)
    if paths["missed"].exists():
        raise ValueError("cannot create a forecast where a missed-capture manifest already exists")
    if paths["manifest"].exists():
        return {"status": "EXISTS", "manifest": paths["manifest"]}
    hours = capture_hours(captured_at, first_kickoff_at)
    if not 0.0 <= hours <= 18.0:
        raise ValueError(f"fixture capture must be inside the verified 18-hour window, got {hours}")
    forecasts = fixture_forecasts(season, week, captured_at, first_kickoff_at)
    scoring = fixture_scoring_rows(forecasts)
    decisions = fixture_decision_rows(forecasts, season, week, captured_at)
    write_jsonl_gzip(paths["forecasts"], forecasts)
    write_jsonl_gzip(paths["scoring"], scoring)
    write_jsonl_gzip(paths["decisions"], decisions)
    manifest = {
        "schema": SCHEMA, "fixture": True, "status": "CAPTURED", "season": season, "week": week,
        "captured_at": captured_at, "first_kickoff_at": first_kickoff_at, "hours_before_first_kickoff": hours,
        "capture_contract_sha256": contract_sha256(), "schedule_snapshot_sha256": forecasts[0]["schedule_snapshot_sha256"],
        "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "shadow_integration": False, "automatic_promotion": False},
        "ledgers": {
            "forecast": {"path": paths["forecasts"].relative_to(root).as_posix(), "sha256": sha256_file(paths["forecasts"]), "rows": len(forecasts)},
            "scoring_replay": {"path": paths["scoring"].relative_to(root).as_posix(), "sha256": sha256_file(paths["scoring"]), "rows": len(scoring)},
            "decision_trace": {"path": paths["decisions"].relative_to(root).as_posix(), "sha256": sha256_file(paths["decisions"]), "rows": len(decisions)},
        },
        "expected_models": list(MODELS), "expected_positions": list(POSITIONS), "first_write_immutable": True,
    }
    write_json(paths["manifest"], manifest)
    return {"status": "CREATED", "manifest": paths["manifest"]}


def create_fixture_outcomes(root: Path, season: int, week: int) -> dict[str, Any]:
    paths = capture_paths(root, season, week)
    if not paths["manifest"].exists():
        raise ValueError("outcomes require a pre-existing immutable forecast capture")
    output = paths["outcome_dir"] / "outcomes.jsonl.gz"
    meta = paths["outcome_dir"] / "outcome-manifest.json"
    if meta.exists():
        return {"status": "EXISTS", "manifest": meta}
    forecasts = read_jsonl_gzip(paths["forecasts"])
    rows = fixture_outcome_rows(forecasts, season, week)
    write_jsonl_gzip(output, rows)
    write_json(meta, {"schema": OUTCOME_SCHEMA, "fixture": True, "season": season, "week": week, "revision": 1, "forecast_manifest_sha256": sha256_file(paths["manifest"]), "outcome_path": output.relative_to(root).as_posix(), "outcome_sha256": sha256_file(output), "rows": len(rows), "append_only": True})
    return {"status": "CREATED", "manifest": meta}


def create_missed_capture(root: Path, season: int, week: int, captured_at: str, first_kickoff_at: str, reason: str) -> dict[str, Any]:
    if reason not in MISSED_REASONS:
        raise ValueError(f"unknown missed-capture reason: {reason}")
    paths = capture_paths(root, season, week)
    if paths["manifest"].exists():
        raise ValueError("cannot write a missed-capture manifest where a forecast exists")
    if paths["missed"].exists():
        return {"status": "EXISTS", "manifest": paths["missed"]}
    write_json(paths["missed"], {"schema": MISSED_SCHEMA, "fixture": True, "season": season, "week": week, "captured_at": captured_at, "first_kickoff_at": first_kickoff_at, "hours_before_first_kickoff": capture_hours(captured_at, first_kickoff_at), "reason": reason, "capture_contract_sha256": contract_sha256(), "historical_reconstruction": False, "first_write_immutable": True, "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "shadow_integration": False}})
    return {"status": "CREATED", "manifest": paths["missed"]}


def validate_capture(root: Path, season: int, week: int, *, require_outcome: bool = False, require_fixture: bool | None = True) -> dict[str, Any]:
    contract = load_contract()
    paths = capture_paths(root, season, week)
    has_capture, has_missed = paths["manifest"].exists(), paths["missed"].exists()
    if has_capture == has_missed:
        raise ValueError("exactly one immutable capture or missed-capture manifest is required")
    if has_missed:
        missed = read_json(paths["missed"])
        assert missed["schema"] == MISSED_SCHEMA and missed["reason"] in MISSED_REASONS
        assert missed["historical_reconstruction"] is False and missed["first_write_immutable"] is True
        assert missed["capture_contract_sha256"] == contract_sha256()
        assert not paths["forecasts"].exists() and not paths["scoring"].exists() and not paths["decisions"].exists()
        return {"status": "MISSED", "reason": missed["reason"]}
    manifest = read_json(paths["manifest"])
    assert manifest["schema"] == SCHEMA and isinstance(manifest.get("fixture"), bool) and manifest["status"] == "CAPTURED"
    if require_fixture is not None:
        assert manifest["fixture"] is require_fixture
    assert manifest["capture_contract_sha256"] == contract_sha256()
    assert manifest["expected_models"] == list(MODELS) and manifest["expected_positions"] == list(POSITIONS)
    assert manifest["first_write_immutable"] is True
    assert 0.0 <= float(manifest["hours_before_first_kickoff"]) <= 18.0
    for key in ("production_activation", "app_integration", "shadow_integration", "automatic_promotion"):
        assert manifest["governance"][key] is False
    assert manifest["governance"]["production_model"] == "M9"
    ledger_paths = {"forecast": paths["forecasts"], "scoring_replay": paths["scoring"], "decision_trace": paths["decisions"]}
    for name, path in ledger_paths.items():
        row = manifest["ledgers"][name]
        assert path.is_file() and row["path"] == path.relative_to(root).as_posix() and row["sha256"] == sha256_file(path)
    forecasts = read_jsonl_gzip(paths["forecasts"])
    assert forecasts and {row["model"] for row in forecasts} == set(MODELS)
    paired: dict[str, set[str]] = {}
    for row in forecasts:
        for field in contract["forecast_row_required_fields"]:
            assert field in row, field
        assert row["position_model"] in POSITIONS and row["model"] in MODELS
        assert set(row["prediction_quantiles"]) == set(QUANTILES)
        assert set(row["subgroups"]) == set(SUBGROUPS)
        assert len(row["source_bundle_sha256"]) == 64 and len(row["model_parameter_sha256"]) == 64
        assert not any(key.startswith("actual") for key in row)
        paired.setdefault(row["forecast_id"], set()).add(row["model"])
    assert all(models == set(MODELS) for models in paired.values()) and len(paired) == len(POSITIONS)
    scoring = read_jsonl_gzip(paths["scoring"])
    assert scoring and {(row["forecast_id"], row["model"]) for row in scoring} >= {(row["forecast_id"], row["model"]) for row in forecasts}
    assert all(row["research_only"] is True and row["profile_scoring_signature"] and row["profile_fingerprint"] for row in scoring)
    decisions = read_jsonl_gzip(paths["decisions"])
    assert {row["model"] for row in decisions} == set(MODELS)
    assert all(row["research_only"] is True and row["production_recommendation_changed"] is False and row["legal_forecast_ids"] for row in decisions)
    outcome_meta = paths["outcome_dir"] / "outcome-manifest.json"
    if require_outcome and not outcome_meta.exists():
        raise ValueError("outcome fixture required but absent")
    if outcome_meta.exists():
        outcome = read_json(outcome_meta)
        output = paths["outcome_dir"] / "outcomes.jsonl.gz"
        assert outcome["schema"] == OUTCOME_SCHEMA and outcome["append_only"] is True and output.is_file()
        assert outcome["outcome_sha256"] == sha256_file(output)
        rows = read_jsonl_gzip(output)
        assert {row["forecast_id"] for row in rows} == set(paired)
        assert all("model" not in row and row["revision"] == 1 for row in rows)
    return {"status": "CAPTURED", "forecast_rows": len(forecasts), "scoring_rows": len(scoring), "decision_rows": len(decisions), "outcome_present": outcome_meta.exists()}

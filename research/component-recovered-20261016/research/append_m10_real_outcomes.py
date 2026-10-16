#!/usr/bin/env python3
"""Append research-only M10 outcomes from an archived retrospective player response.

No provider requests, forecast reconstruction, league scoring, or model promotion.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from capture_in_season_pr2_lineup_nflverse_outcomes import canonical_team
from m10_prospective_capture_contract import (
    canonical_bytes, capture_paths, parse_time, read_json, read_jsonl_gzip,
    sha256_bytes, sha256_file, validate_capture, write_json, write_jsonl_gzip,
)
from m10_prospective_operational_capture import OUTCOME_INPUT_SCHEMA, append_outcomes
from weekly_player_performance import build as validate_performance_source, target_rows

SOURCE = "NFLVERSE_ARCHIVED_PLAYER_WEEK"
IDENTITY_FIELDS = {"season", "week", "season_type", "player_id", "game_id", "team", "opponent_team", "player_name", "player_display_name", "position", "position_group", "headshot_url"}


def _numeric_components(row: dict) -> dict:
    components = {}
    for key, value in row.items():
        if key in IDENTITY_FIELDS or key.endswith("_list"):
            continue
        if value is None or str(value).strip() == "":
            components[key] = None
            continue
        try:
            number = float(value)
        except (ValueError, TypeError):
            # Provider-specific nonnumeric metrics are unknown, not inferred zeros.
            components[key] = None
            continue
        components[key] = number if math.isfinite(number) else None
    return components


def index_provider_rows(selected: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for provider_row in selected:
        player_id = str(provider_row.get("player_id") or "")
        if not player_id:
            continue  # Unattributed source row cannot be joined to a forecast.
        if player_id in indexed:
            raise ValueError("M10_OUTCOME_DUPLICATE_GSIS_ID")
        indexed[player_id] = provider_row
    return indexed


def prepare(root: Path, season: int, week: int, source_path: Path, *, as_of: datetime) -> tuple[list[dict], dict]:
    root = root.resolve()
    source_path = source_path.resolve()
    if not source_path.is_relative_to(root):
        raise ValueError("M10_OUTCOME_SOURCE_OUTSIDE_ROOT")
    prospective = root / "data/research/prospective/m10"
    paths = capture_paths(prospective, season, week)
    validate_capture(prospective, season, week, require_fixture=False)
    manifest = read_json(paths["manifest"])
    if manifest["fixture"] or (int(manifest["season"]), int(manifest["week"])) != (season, week):
        raise ValueError("M10_REAL_FORECAST_REQUIRED")
    source = read_json(source_path)
    if source.get("provider") != "nflverse" or source.get("capture_intent") != "OTHER_GOVERNED":
        raise ValueError("M10_OUTCOME_SOURCE_TYPE_MISMATCH")
    observed = parse_time(source["observed_at"])
    if observed <= parse_time(manifest["captured_at"]) or observed > as_of.astimezone(timezone.utc):
        raise ValueError("M10_OUTCOME_SOURCE_TIME_INVALID")
    # The established performance owner verifies the stored schedule buffer,
    # provider envelope, full raw/selected payload digests and all game/team IDs.
    report = validate_performance_source(root, source_path, season, week, as_of)
    if report["status"] not in {"AVAILABLE_PROVIDER_ROWS", "PARTIAL_UNRESOLVED_SOURCE_PLAYERS"}:
        raise ValueError("M10_OUTCOME_SOURCE_COVERAGE_BLOCKED")
    payload = source["payload"]
    raw_path = (root / payload["raw_path"]).resolve()
    raw = gzip.decompress(raw_path.read_bytes())
    selected = target_rows(raw, season, week)
    indexed = index_provider_rows(selected)
    forecasts: dict[str, dict] = {}
    for row in read_jsonl_gzip(paths["forecasts"]):
        forecast_id = str(row["forecast_id"])
        if forecast_id in forecasts:
            first = forecasts[forecast_id]
            if any(first[key] != row[key] for key in ("canonical_player_id", "position_model", "team", "opponent_team", "player_kickoff_at")):
                raise ValueError("M10_OUTCOME_MODEL_COHORT_MISMATCH")
        else:
            forecasts[forecast_id] = row
    rows = []
    counts: Counter[str] = Counter()
    for forecast_id, forecast in sorted(forecasts.items()):
        provider_row = indexed.get(str(forecast["canonical_player_id"]))
        if provider_row is None:
            status = "BLOCKED_NO_SOURCE_PLAYER_ROW"
        elif (canonical_team(provider_row["team"]) != canonical_team(forecast["team"]) or
              canonical_team(provider_row["opponent_team"]) != canonical_team(forecast["opponent_team"])):
            status = "BLOCKED_MATCHUP_MISMATCH"
        elif provider_row.get("position") != forecast["position_model"]:
            status = "BLOCKED_POSITION_MISMATCH"
        else:
            status = "OBSERVED_PROVIDER_ROW"
        counts[status] += 1
        rows.append({
            "outcome_id": f"outcome-{forecast_id}-r1", "forecast_id": forecast_id,
            "canonical_player_id": forecast["canonical_player_id"], "season": season, "week": week,
            "source": SOURCE, "source_release_or_commit": str(source["endpoint"]),
            "observed_at": source["observed_at"], "revision": 1,
            "status": status,
            "raw_outcomes": _numeric_components(provider_row) if status == "OBSERVED_PROVIDER_ROW" else None,
            "source_payload_sha256": sha256_bytes(canonical_bytes(provider_row)) if status == "OBSERVED_PROVIDER_ROW" else None,
        })
    lineage = {"forecast_manifest_sha256": sha256_file(paths["manifest"]),
               "source_envelope_sha256": sha256_file(source_path),
               "source_payload_sha256": payload["raw_response_sha256"],
               "source_archive_sha256": payload["raw_archive_sha256"],
               "counts": dict(sorted(counts.items())), "forecast_ids": len(forecasts)}
    return rows, lineage


def publish(root: Path, season: int, week: int, source_path: Path, *, as_of: datetime) -> dict:
    rows, lineage = prepare(root, season, week, source_path, as_of=as_of)
    prospective = root.resolve() / "data/research/prospective/m10"
    paths = capture_paths(prospective, season, week)
    meta = paths["outcome_dir"] / "outcome-manifest.json"
    if meta.exists():
        existing = read_json(meta)
        if (existing.get("fixture") or existing.get("forecast_manifest_sha256") != lineage["forecast_manifest_sha256"] or
            existing.get("source_release_or_commit") != SOURCE + ":" + lineage["source_envelope_sha256"] or
            existing.get("source_payload_sha256") != lineage["source_payload_sha256"] or
            read_jsonl_gzip(paths["outcome_dir"] / "outcomes.jsonl.gz") != rows):
            raise ValueError("M10_OUTCOME_FIRST_WRITE_COLLISION")
        validate_capture(prospective, season, week, require_outcome=True, require_fixture=False)
        return {"status": "EXISTS_VALIDATED", "manifest": meta, "coverage": lineage["counts"]}
    if (paths["outcome_dir"] / "outcomes.jsonl.gz").exists():
        raise ValueError("M10_OUTCOME_ORPHAN_FIRST_WRITE")
    with tempfile.TemporaryDirectory(prefix="fie-m10-outcome-") as name:
        bundle = Path(name)
        write_jsonl_gzip(bundle / "rows.jsonl.gz", rows)
        write_json(bundle / "input.json", {
            "schema": OUTCOME_INPUT_SCHEMA, "historical_reconstruction": False,
            "point_in_time_outcome_source": True, "fixture": False, "revision": 1,
            "season": season, "week": week, "rows_path": "rows.jsonl.gz",
            "rows_sha256": sha256_file(bundle / "rows.jsonl.gz"),
            "source_release_or_commit": SOURCE + ":" + lineage["source_envelope_sha256"],
            "source_payload_sha256": lineage["source_payload_sha256"],
        })
        result = append_outcomes(bundle / "input.json", prospective)
    validate_capture(prospective, season, week, require_outcome=True, require_fixture=False)
    return {"status": result["status"], "manifest": result["manifest"], "coverage": lineage["counts"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--source", type=Path, required=True, help="Stored weekly-performance source-envelope.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    source = args.source if args.source.is_absolute() else root / args.source
    now = datetime.now(timezone.utc)
    if args.dry_run:
        _, lineage = prepare(root, args.season, args.week, source, as_of=now)
        print(json.dumps({"status": "DRY_RUN", **lineage}, sort_keys=True))
    else:
        result = publish(root, args.season, args.week, source, as_of=now)
        print(json.dumps({**result, "manifest": str(result["manifest"].relative_to(root))}, sort_keys=True))


if __name__ == "__main__":
    main()

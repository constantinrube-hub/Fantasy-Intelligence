#!/usr/bin/env python3
"""Build the deterministic Tranche 6C point-in-time evidence report.

The report inventories only immutable evidence that is actually stored in this
repository.  It is deliberately not a data-recovery tool: a current provider
endpoint can never fill an earlier date, week, season, release, or revision.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fie_research_pipeline_contract import ROOT, canonical_bytes, load_json, sha256_bytes, sha256_file, write_json


SCHEMA = "fie-point-in-time-evidence-report-v1"
METADATA_SCHEMA = "fie-point-in-time-source-metadata-v1"
SEASON = 2026

ARCHIVES: dict[str, dict[str, str]] = {
    "season_market": {
        "root": "data/research/market/sleeper/2026",
        "pattern": "season_market_*.jsonl.gz.meta.json",
        "as_of_key": "market_as_of",
        "source_role": "prospective_preseason_market",
    },
    "availability": {
        "root": "data/research/availability/sleeper/2026",
        "pattern": "availability_*.jsonl.gz.meta.json",
        "as_of_key": "availability_as_of",
        "source_role": "prospective_availability",
    },
    "weekly_market_benchmark": {
        "root": "data/research/market/sleeper/2026",
        "pattern": "week_*.jsonl.gz.meta.json",
        "as_of_key": "captured_at",
        "source_role": "prospective_weekly_market_benchmark",
    },
}

SOURCE_CONTRACTS: dict[str, dict[str, Any]] = {
    "season_market": {
        "provider": "Sleeper",
        "endpoint_template": "https://api.sleeper.com/projections/nfl/{season}?season_type=regular",
        "release_cadence": "daily scheduled prospective capture",
        "revision_policy": "Provider release/revision identifiers are not exposed by this endpoint; the exact observed response is immutably first-written and SHA-256 recorded.",
        "target_time_eligibility": "Preseason market evidence is eligible only for its recorded observed-at/as-of date; it is not a historical forecast reconstruction.",
    },
    "availability": {
        "provider": "Sleeper",
        "endpoint_template": "https://api.sleeper.app/v1/players/nfl",
        "release_cadence": "daily scheduled prospective capture",
        "revision_policy": "Provider release/revision identifiers are not exposed by this endpoint; the exact observed response is immutably first-written and SHA-256 recorded.",
        "target_time_eligibility": "Availability evidence is eligible only for its recorded observed-at/as-of date; it does not backfill historical injury or depth-chart states.",
    },
    "weekly_market_benchmark": {
        "provider": "Sleeper",
        "endpoint_template": "https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular",
        "release_cadence": "verified pregame scheduled capture",
        "revision_policy": "Provider release/revision identifiers are not exposed by this endpoint; the exact observed response is immutably first-written and SHA-256 recorded.",
        "target_time_eligibility": "A weekly benchmark is eligible only when the captured sidecar records verified regular-season pregame timing; otherwise it remains preserved but ineligible for pregame evaluation.",
    },
}


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def snapshot_path_for(meta_path: Path) -> Path:
    suffix = ".meta.json"
    if not meta_path.name.endswith(suffix):
        raise ValueError(meta_path)
    return meta_path.with_name(meta_path.name[: -len(suffix)])


def input_content_sha256(path: Path) -> str | None:
    """Use semantic JSON identity while retaining exact binary evidence hashes.

    Git normalizes text line endings differently on Windows and Linux runners.
    Sidecars are JSON contracts, so their canonical content is the portable input
    identity. Compressed immutable snapshots remain byte-addressed.
    """
    if path.suffix.lower() == ".json":
        return sha256_bytes(canonical_bytes(load_json(path, {})))
    return sha256_file(path)


def metadata_view(raw: dict[str, Any], expected_role: str) -> dict[str, Any]:
    pit = raw.get("point_in_time_metadata")
    if not isinstance(pit, dict):
        return {
            "status": "LEGACY_METADATA_INCOMPLETE",
            "missing": ["point_in_time_metadata"],
            "source_release_identifier": None,
            "source_revision_identifier": None,
            "revision_metadata_status": "UNKNOWN",
        }
    required = ("schema", "capture_intent", "source_endpoint", "revision_metadata_status", "as_of_semantics", "release_cadence")
    missing = [key for key in required if not pit.get(key)]
    if pit.get("schema") != METADATA_SCHEMA:
        missing.append("schema_mismatch")
    if pit.get("capture_intent") != expected_role:
        missing.append("capture_intent_mismatch")
    return {
        "status": "COMPLETE" if not missing else "METADATA_INCOMPLETE",
        "missing": sorted(set(missing)),
        "source_endpoint": pit.get("source_endpoint"),
        "source_release_identifier": pit.get("source_release_identifier"),
        "source_revision_identifier": pit.get("source_revision_identifier"),
        "revision_metadata_status": pit.get("revision_metadata_status"),
        "as_of_semantics": pit.get("as_of_semantics"),
        "release_cadence": pit.get("release_cadence"),
    }


def records_for(kind: str, spec: dict[str, str]) -> list[dict[str, Any]]:
    root = ROOT / spec["root"]
    records: list[dict[str, Any]] = []
    for meta_path in sorted(root.glob(spec["pattern"])):
        raw = load_json(meta_path, {})
        if not isinstance(raw, dict):
            raise ValueError(f"invalid JSON sidecar: {relative(meta_path)}")
        snapshot = snapshot_path_for(meta_path)
        if not snapshot.is_file():
            raise ValueError(f"missing immutable snapshot for sidecar: {relative(meta_path)}")
        records.append({
            "snapshot_path": relative(snapshot),
            "sidecar_path": relative(meta_path),
            "snapshot_sha256": sha256_file(snapshot),
            "captured_at": raw.get("captured_at"),
            "as_of": raw.get(spec["as_of_key"]),
            "season": raw.get("season"),
            "week": raw.get("week"),
            "rows": raw.get("rows"),
            "immutable_first_write": bool(raw.get("immutable_first_write") is True or raw.get("first_write_policy") is True),
            "pregame_eligible": raw.get("pregame_eligible"),
            "metadata": metadata_view(raw, spec["source_role"]),
        })
    return records


def age_days(reference: datetime | None, captured_at: Any) -> float | None:
    captured = parse_time(captured_at)
    if not reference or not captured:
        return None
    return round(max(0.0, (reference - captured).total_seconds()) / 86400, 6)


def source_summary(kind: str, records: list[dict[str, Any]], reference: datetime | None) -> dict[str, Any]:
    times = [parse_time(row.get("captured_at")) for row in records]
    times = [x for x in times if x]
    as_of = sorted({str(row.get("as_of")) for row in records if row.get("as_of")})
    years = sorted({value[:4] for value in as_of if len(value) >= 4 and value[:4].isdigit()})
    return {
        "source_contract": SOURCE_CONTRACTS[kind],
        "snapshot_count": len(records),
        "capture_count_with_timestamp": len(times),
        "first_captured_at": times[0].isoformat() if times else None,
        "latest_captured_at": times[-1].isoformat() if times else None,
        "coverage_as_of_values": as_of,
        "coverage_years": years,
        "completed_historical_seasons": [],
        "coverage_status": "NO_CAPTURED_EVIDENCE" if not records else "PROSPECTIVE_EVIDENCE_ONLY",
        "metadata_complete_count": sum(row["metadata"]["status"] == "COMPLETE" for row in records),
        "metadata_incomplete_count": sum(row["metadata"]["status"] != "COMPLETE" for row in records),
        "immutable_first_write_count": sum(row["immutable_first_write"] for row in records),
        "latest_capture_age_days_at_report_reference": age_days(reference, times[-1].isoformat()) if times else None,
        "records": [{**row, "capture_age_days_at_report_reference": age_days(reference, row.get("captured_at"))} for row in records],
    }


def build_report() -> dict[str, Any]:
    raw_records = {kind: records_for(kind, spec) for kind, spec in ARCHIVES.items()}
    all_times = [parse_time(row.get("captured_at")) for rows in raw_records.values() for row in rows]
    all_times = sorted(x for x in all_times if x)
    reference = all_times[-1] if all_times else None
    sources = {kind: source_summary(kind, raw_records[kind], reference) for kind in ARCHIVES}
    inputs = []
    for summary in sources.values():
        for record in summary["records"]:
            inputs.extend([record["snapshot_path"], record["sidecar_path"]])
    return {
        "schema": SCHEMA,
        "schema_version": 1,
        "season": SEASON,
        "deterministic_input_sha256": sha256_bytes(canonical_bytes([
            {"path": path, "sha256": input_content_sha256(ROOT / path)} for path in sorted(inputs)
        ])),
        "governance": {
            "research_only": True,
            "production_behavior_changed": False,
            "historical_forecast_backfill": False,
            "current_endpoint_reconstruction": False,
        },
        "report_reference_captured_at": reference.isoformat() if reference else None,
        "sources": sources,
        "summary": {
            "authoritative_verdict": ["PROSPECTIVE_EVIDENCE_RECORDED", "HISTORICAL_EVIDENCE_INCOMPLETE", "PROMOTION_BLOCKED"],
            "source_count": len(sources),
            "snapshot_count": sum(source["snapshot_count"] for source in sources.values()),
            "metadata_complete_count": sum(source["metadata_complete_count"] for source in sources.values()),
            "metadata_incomplete_count": sum(source["metadata_incomplete_count"] for source in sources.values()),
            "completed_historical_seasons": [],
            "coverage_policy": "Coverage age is measured against the latest immutable capture in this report, so a report rebuild is deterministic and never consults a current endpoint.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/research/portfolio/2026/point-in-time-evidence-report.json")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    report = build_report()
    write_json(output, report)
    print(f"PASS wrote {relative(output)} snapshots={report['summary']['snapshot_count']} metadata_complete={report['summary']['metadata_complete_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

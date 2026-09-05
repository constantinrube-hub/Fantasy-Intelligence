#!/usr/bin/env python3
"""Fail-closed validator for the Tranche 6C point-in-time evidence report."""
from __future__ import annotations

import argparse
from pathlib import Path

from build_fie_point_in_time_evidence_report import ARCHIVES, SCHEMA, SOURCE_CONTRACTS, build_report
from fie_research_pipeline_contract import ROOT, canonical_bytes, load_json, sha256_file


def validate(report: dict) -> None:
    assert report.get("schema") == SCHEMA
    assert report.get("governance") == {
        "research_only": True,
        "production_behavior_changed": False,
        "historical_forecast_backfill": False,
        "current_endpoint_reconstruction": False,
    }
    summary = report.get("summary") or {}
    assert summary.get("authoritative_verdict") == ["PROSPECTIVE_EVIDENCE_RECORDED", "HISTORICAL_EVIDENCE_INCOMPLETE", "PROMOTION_BLOCKED"]
    assert summary.get("completed_historical_seasons") == []
    sources = report.get("sources") or {}
    assert set(sources) == set(ARCHIVES)
    for kind, source in sources.items():
        assert source.get("source_contract") == SOURCE_CONTRACTS[kind]
        assert source.get("completed_historical_seasons") == []
        assert source.get("coverage_status") in {"NO_CAPTURED_EVIDENCE", "PROSPECTIVE_EVIDENCE_ONLY"}
        assert source.get("metadata_complete_count", 0) + source.get("metadata_incomplete_count", 0) == source.get("snapshot_count")
        records = source.get("records") or []
        assert len(records) == source.get("snapshot_count")
        for record in records:
            snapshot = ROOT / str(record.get("snapshot_path") or "")
            assert snapshot.is_file(), snapshot
            assert record.get("snapshot_sha256") == sha256_file(snapshot)
            assert record.get("immutable_first_write") is True
            metadata = record.get("metadata") or {}
            assert metadata.get("status") in {"COMPLETE", "LEGACY_METADATA_INCOMPLETE", "METADATA_INCOMPLETE"}
            if metadata.get("status") == "COMPLETE":
                assert metadata.get("revision_metadata_status") == "NOT_EXPOSED_BY_PROVIDER"
                assert metadata.get("source_release_identifier") is None
                assert metadata.get("source_revision_identifier") is None
    assert summary.get("snapshot_count") == sum(source.get("snapshot_count", 0) for source in sources.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="data/research/portfolio/2026/point-in-time-evidence-report.json")
    parser.add_argument("--verify-deterministic", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    report = load_json(path, {})
    validate(report)
    if args.verify_deterministic:
        assert canonical_bytes(report) == canonical_bytes(build_report()), "point-in-time evidence report is stale or non-deterministic"
    print(f"PASS Tranche 6C point-in-time evidence report snapshots={report['summary']['snapshot_count']} metadata_complete={report['summary']['metadata_complete_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

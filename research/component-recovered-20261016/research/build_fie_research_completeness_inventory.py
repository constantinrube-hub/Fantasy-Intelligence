#!/usr/bin/env python3
"""Build the deterministic Tranche 6B research-completeness inventory.

This reader deliberately consumes existing research artifacts only.  It does not
train a model, reinterpret a research result, or write into a league pipeline.
The output is a fail-closed evidence matrix for the four offensive positions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from fie_research_pipeline_contract import OFFENSE, ROOT, canonical_bytes, load_json, registry_rows, sha256_bytes, write_json


SCHEMA = "fie-research-completeness-inventory-v1"
SEASON = 2026
STATES = (
    "ABSENT", "CONTRACT_ONLY", "PRESENT_UNVERIFIED", "TIME_SAFE_EVALUATED",
    "STATISTICALLY_VALIDATED", "DECISION_VALIDATED", "PRODUCTION_AUTHORIZED",
    "NOT_APPLICABLE",
)
BLOCKERS = (
    "MISSING_SOURCE", "INSUFFICIENT_HISTORY", "LEAKAGE_RISK", "STATISTICAL_FAILURE",
    "CALIBRATION_FAILURE", "DECISION_UTILITY_FAILURE", "REPRODUCIBILITY_FAILURE",
    "GOVERNANCE_BLOCKED",
)
DIMENSIONS = (
    "artifact_coverage", "source_provenance", "temporal_validation", "statistical_stability",
    "probabilistic_calibration", "decision_utility", "reproducibility", "production_authorization",
)


def path_for(league_id: str, suffix: str) -> Path:
    return ROOT / "data" / "research" / "leagues" / league_id / "performance" / str(SEASON) / suffix


def evidence_paths(league_id: str) -> dict[str, Path]:
    return {
        "readiness": path_for(league_id, "research_pipeline/readiness.json"),
        "feature_evidence": path_for(league_id, "evidence/feature_evidence.json"),
        "m91c": path_for(league_id, "m91c_challenger/m91c_meta.json"),
        "v974": path_for(league_id, "strategy/preseason_v974_validation.json"),
        "v975": path_for(league_id, "strategy/preseason_v975_validation.json"),
    }


def digest_inputs(paths: Iterable[Path]) -> str:
    """Fingerprint exact semantic JSON inputs, independent of line endings."""
    rows = []
    for path in sorted(paths, key=lambda p: p.as_posix()):
        rows.append({"path": path.relative_to(ROOT).as_posix(), "content": load_json(path, None)})
    return sha256_bytes(canonical_bytes(rows))


def source_snapshot(root: Path, prefix: str) -> dict[str, Any]:
    meta = sorted(root.glob("*.jsonl.gz.meta.json"))
    records = []
    for path in meta:
        obj = load_json(path, {})
        records.append({
            "path": path.relative_to(ROOT).as_posix(),
            "as_of": obj.get("market_as_of") or obj.get("availability_as_of"),
            "immutable_first_write": obj.get("immutable_first_write") is True,
            "rows": obj.get("rows"),
        })
    years = sorted({str(r["as_of"])[:4] for r in records if r.get("as_of")})
    return {
        "kind": prefix,
        "snapshot_count": len(records),
        "years": years,
        "immutable_first_write_count": sum(r["immutable_first_write"] for r in records),
        "records": records,
        "historical_completed_seasons": [],
    }


def state(state: str, blockers: Iterable[str], evidence: dict[str, Any]) -> dict[str, Any]:
    values = sorted(set(blockers))
    if state not in STATES:
        raise ValueError(state)
    if state != "PRODUCTION_AUTHORIZED" and not values:
        raise ValueError(f"{state} must remain fail-closed with an explicit blocker")
    if any(value not in BLOCKERS for value in values):
        raise ValueError(values)
    return {"state": state, "blockers": values, "evidence": evidence}


def feature_summary(bundle: dict[str, Any], position: str, *, artifact_present: bool) -> dict[str, Any]:
    rows = [r for r in bundle.get("phase1_feature_evidence_matrix", []) if r.get("position") == position]
    families = sorted({str(f) for row in rows for f in row.get("families", [row.get("family")]) if f})
    validated = sorted({str(f) for row in rows if row.get("evidence_status") == "validated" for f in row.get("families", [row.get("family")]) if f})
    fold_counts = [int((row.get("weekly_gate") or {}).get("folds") or 0) for row in rows]
    return {"artifact_present": artifact_present, "feature_count": len(rows), "families": families, "validated_families": validated, "max_weekly_folds": max(fold_counts, default=0)}


def dimension_rows(*, unit: str, position: str, horizon: str, domain: str, values: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "position": position,
            "horizon": horizon,
            "feature_family": unit,
            "decision_domain": domain,
            "dimension": dimension,
            **values[dimension],
        }
        for dimension in DIMENSIONS
    ]


def cells_for_position(position: str, feature: dict[str, Any], readiness: dict[str, Any], m91c: dict[str, Any], sources: dict[str, Any]) -> list[dict[str, Any]]:
    """Map current artifacts to conservative, independently auditable cells."""
    positions = readiness.get("positions") or {}
    resolver = positions.get(position) or {}
    m91c_position = resolver.get("preseason_projection_challenger") or {}
    if feature["artifact_present"]:
        m7 = {
            "artifact_coverage": state("PRESENT_UNVERIFIED", ["STATISTICAL_FAILURE"], feature),
            "source_provenance": state("CONTRACT_ONLY", ["REPRODUCIBILITY_FAILURE"], {"source_contract_present": True}),
            "temporal_validation": state("TIME_SAFE_EVALUATED", ["STATISTICAL_FAILURE"], {"outer_folds": feature["max_weekly_folds"]}),
            "statistical_stability": state("PRESENT_UNVERIFIED", ["STATISTICAL_FAILURE"], {"validated_families": feature["validated_families"]}),
            "probabilistic_calibration": state("ABSENT", ["CALIBRATION_FAILURE"], {"calibration_artifact": None}),
            "decision_utility": state("ABSENT", ["DECISION_UTILITY_FAILURE"], {"decision_gate": None}),
            "reproducibility": state("PRESENT_UNVERIFIED", ["REPRODUCIBILITY_FAILURE"], {"release_gate_separate_from_research_artifact": True}),
            "production_authorization": state("CONTRACT_ONLY", ["GOVERNANCE_BLOCKED"], {"automatic_promotion": False}),
        }
        m8 = {
            "artifact_coverage": state("PRESENT_UNVERIFIED", ["MISSING_SOURCE"], {"matchup_artifact_present": True}),
            "source_provenance": state("CONTRACT_ONLY", ["MISSING_SOURCE", "LEAKAGE_RISK"], {"validated_candidate_families": []}),
            "temporal_validation": state("CONTRACT_ONLY", ["LEAKAGE_RISK"], {"outer_folds": 0}),
            "statistical_stability": state("ABSENT", ["STATISTICAL_FAILURE"], {"validated_candidate_families": []}),
            "probabilistic_calibration": state("ABSENT", ["CALIBRATION_FAILURE"], {"calibration_artifact": None}),
            "decision_utility": state("ABSENT", ["DECISION_UTILITY_FAILURE"], {"decision_gate": None}),
            "reproducibility": state("PRESENT_UNVERIFIED", ["REPRODUCIBILITY_FAILURE"], {"release_gate_separate_from_research_artifact": True}),
            "production_authorization": state("CONTRACT_ONLY", ["GOVERNANCE_BLOCKED"], {"automatic_promotion": False}),
        }
    else:
        absent = {
            "artifact_coverage": state("ABSENT", ["MISSING_SOURCE"], {"artifact_present": False}),
            "source_provenance": state("ABSENT", ["MISSING_SOURCE"], {"source_contract_present": False}),
            "temporal_validation": state("CONTRACT_ONLY", ["MISSING_SOURCE", "LEAKAGE_RISK"], {"outer_folds": 0}),
            "statistical_stability": state("ABSENT", ["MISSING_SOURCE", "STATISTICAL_FAILURE"], {"validated_families": []}),
            "probabilistic_calibration": state("ABSENT", ["CALIBRATION_FAILURE", "MISSING_SOURCE"], {"calibration_artifact": None}),
            "decision_utility": state("ABSENT", ["DECISION_UTILITY_FAILURE", "MISSING_SOURCE"], {"decision_gate": None}),
            "reproducibility": state("ABSENT", ["MISSING_SOURCE", "REPRODUCIBILITY_FAILURE"], {"artifact_hash": None}),
            "production_authorization": state("CONTRACT_ONLY", ["GOVERNANCE_BLOCKED", "MISSING_SOURCE"], {"automatic_promotion": False}),
        }
        m7 = absent
        m8 = absent
    residual_status = str(m91c_position.get("historical_residual_gate_status") or m91c.get("residual_model_gate", {}).get("status") or "")
    m91 = {
        "artifact_coverage": state("PRESENT_UNVERIFIED", ["INSUFFICIENT_HISTORY"], {"status": m91c.get("status"), "position": m91c_position}),
        "source_provenance": state("PRESENT_UNVERIFIED", ["INSUFFICIENT_HISTORY"], {"snapshot_count": sources["market"]["snapshot_count"], "years": sources["market"]["years"]}),
        "temporal_validation": state("CONTRACT_ONLY", ["INSUFFICIENT_HISTORY"], {"historical_residual_gate_status": residual_status}),
        "statistical_stability": state("CONTRACT_ONLY", ["STATISTICAL_FAILURE", "INSUFFICIENT_HISTORY"], {"exact_rows": m91c_position.get("exact_rows")}),
        "probabilistic_calibration": state("PRESENT_UNVERIFIED", ["CALIBRATION_FAILURE", "INSUFFICIENT_HISTORY"], {"method": m91c.get("calibration", {}).get("method")}),
        "decision_utility": state("ABSENT", ["DECISION_UTILITY_FAILURE"], {"decision_gate": None}),
        "reproducibility": state("PRESENT_UNVERIFIED", ["REPRODUCIBILITY_FAILURE"], {"immutable_first_write": sources["market"]["immutable_first_write_count"]}),
        "production_authorization": state("CONTRACT_ONLY", ["GOVERNANCE_BLOCKED", "INSUFFICIENT_HISTORY"], {"production_eligible": m91c.get("production_eligible") is True}),
    }
    availability = {
        "artifact_coverage": state("PRESENT_UNVERIFIED", ["INSUFFICIENT_HISTORY"], {"snapshot_count": sources["availability"]["snapshot_count"], "years": sources["availability"]["years"]}),
        "source_provenance": state("PRESENT_UNVERIFIED", ["INSUFFICIENT_HISTORY"], {"snapshot_count": sources["availability"]["snapshot_count"], "years": sources["availability"]["years"]}),
        "temporal_validation": state("CONTRACT_ONLY", ["INSUFFICIENT_HISTORY"], {"completed_history_years": []}),
        "statistical_stability": state("ABSENT", ["STATISTICAL_FAILURE"], {"availability_model": None}),
        "probabilistic_calibration": state("ABSENT", ["CALIBRATION_FAILURE"], {"calibration_artifact": None}),
        "decision_utility": state("ABSENT", ["DECISION_UTILITY_FAILURE"], {"decision_gate": None}),
        "reproducibility": state("PRESENT_UNVERIFIED", ["REPRODUCIBILITY_FAILURE"], {"immutable_first_write": sources["availability"]["immutable_first_write_count"]}),
        "production_authorization": state("CONTRACT_ONLY", ["GOVERNANCE_BLOCKED", "INSUFFICIENT_HISTORY"], {"external_governed_input": True}),
    }
    return (
        dimension_rows(unit="m7_driver_family", position=position, horizon="weekly", domain="football_forecast", values=m7)
        + dimension_rows(unit="m8_matchup_family", position=position, horizon="weekly", domain="football_forecast", values=m8)
        + dimension_rows(unit="m91c_preseason_residual", position=position, horizon="preseason", domain="football_forecast", values=m91)
        + dimension_rows(unit="availability_history", position=position, horizon="weekly", domain="availability", values=availability)
    )


def build_inventory() -> dict[str, Any]:
    registry = registry_rows()
    overview = load_json(ROOT / "data/research/portfolio/2026/research-overview.json", {})
    overview_by_id = {str(row.get("league_id")): row for row in overview.get("leagues", [])}
    inputs = [ROOT / "data/research/portfolio/2026/research-overview.json"]
    sources = {
        "market": source_snapshot(ROOT / "data/research/market/sleeper/2026", "sleeper_market"),
        "availability": source_snapshot(ROOT / "data/research/availability/sleeper/2026", "sleeper_availability"),
    }
    inputs.extend((ROOT / "data/research/market/sleeper/2026").glob("*.jsonl.gz.meta.json"))
    inputs.extend((ROOT / "data/research/availability/sleeper/2026").glob("*.jsonl.gz.meta.json"))
    leagues = []
    all_cells: list[dict[str, Any]] = []
    for league_id in sorted(registry):
        paths = evidence_paths(league_id)
        inputs.extend(paths.values())
        readiness = load_json(paths["readiness"], {})
        bundle = load_json(paths["feature_evidence"], {})
        m91c = load_json(paths["m91c"], {})
        row = overview_by_id.get(league_id, {})
        cells = []
        for position in OFFENSE:
            cells.extend(cells_for_position(position, feature_summary(bundle, position, artifact_present=paths["feature_evidence"].is_file()), readiness, m91c, sources))
        all_cells.extend(cells)
        leagues.append({
            "league_id": league_id,
            "format": str(row.get("format") or readiness.get("league", {}).get("format") or registry[league_id].get("research_format") or ""),
            "pipeline": {"completed": row.get("pipeline_status") == "completed", "report_complete": row.get("report_complete") is True, "app_publish_complete": row.get("app_publish_complete") is True},
            "model_gate": {position: (readiness.get("positions") or {}).get(position, {}).get("decision") for position in OFFENSE},
            "m91c": {"status": m91c.get("status"), "production_eligible": m91c.get("production_eligible") is True, "residual_gate_status": (m91c.get("residual_model_gate") or {}).get("status")},
            "v974_exact_comparator_status": row.get("V974_exact_comparator_status") is True,
            "v975_qb_status": row.get("V975_QB_status"),
            "cells": cells,
        })
    states = Counter(cell["state"] for cell in all_cells)
    blockers = Counter(blocker for cell in all_cells for blocker in cell["blockers"])
    formats = sorted({league["format"] for league in leagues})
    return {
        "schema": SCHEMA,
        "schema_version": 1,
        "season": SEASON,
        "deterministic_input_sha256": digest_inputs(path for path in inputs if path.is_file()),
        "governance": {"research_only": True, "automatic_promotion": False, "production_behavior_changed": False, "cross_league_promotion": False},
        "contract": {"states": list(STATES), "blockers": list(BLOCKERS), "dimensions": list(DIMENSIONS), "positions": list(OFFENSE), "cell_key": ["position", "horizon", "feature_family", "decision_domain", "dimension"]},
        "sources": sources,
        "summary": {
            "authoritative_verdict": ["PIPELINE_COVERAGE_COMPLETE", "FOOTBALL_EVIDENCE_INCOMPLETE", "PROMOTION_BLOCKED"],
            "league_count": len(leagues), "formats": formats,
            "completed_pipeline_count": sum(league["pipeline"]["completed"] for league in leagues),
            "report_complete_count": sum(league["pipeline"]["report_complete"] for league in leagues),
            "app_publish_complete_count": sum(league["pipeline"]["app_publish_complete"] for league in leagues),
            "offense_blocked_count": sum(1 for league in leagues for decision in league["model_gate"].values() if str(decision).startswith("BLOCKED_")),
            "m91c_blocked_promotion_count": sum(league["m91c"]["status"] == "RESEARCH_ONLY_BLOCKED_PROMOTION" for league in leagues),
            "v974_exact_comparator_pass_count": sum(league["v974_exact_comparator_status"] for league in leagues),
            "cell_states": dict(sorted(states.items())), "blockers": dict(sorted(blockers.items())),
        },
        "leagues": leagues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/research/portfolio/2026/research-completeness-inventory.json")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    inventory = build_inventory()
    write_json(output, inventory)
    print(f"PASS wrote {output.relative_to(ROOT)} leagues={inventory['summary']['league_count']} cells={sum(len(x['cells']) for x in inventory['leagues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

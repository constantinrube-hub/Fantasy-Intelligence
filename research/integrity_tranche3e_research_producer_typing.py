#!/usr/bin/env python3
"""Permanent Tranche 3E typed research-producer integrity contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from fie_research_pipeline_contract import (  # noqa: E402
    PILOT_LEAGUE_ID,
    RESEARCH_STAGE_CONTRACTS,
    research_stage_contract,
    research_stage_primary_output,
    sha256_file,
)

EXPECTED = {
    "feature_evidence": {
        "artifact_type": "feature_evidence_bundle",
        "producer": "research/fie_feature_evidence_hardening.py",
        "producer_dependencies": ["research/fie_feature_evidence.py"],
        "validator": ["research/validate_feature_evidence_bundle.py", "research/validate_feature_evidence_hardening.py"],
        "schema": "fie-feature-evidence-v1",
        "primary": "evidence/feature_evidence.json",
    },
    "production_shadow": {
        "artifact_type": "production_shadow_bundle",
        "producer": "research/fie_production_shadow.py",
        "producer_dependencies": [],
        "validator": ["research/validate_production_shadow.py"],
        "schema": "fie-production-shadow-v1",
        "primary": "shadow/production_shadow.json",
    },
    "controlled_runtime": {
        "artifact_type": "controlled_runtime_bundle",
        "producer": "research/build_v96_runtime_bundle.py",
        "producer_dependencies": [],
        "validator": ["research/validate_v96_runtime_bundle.py"],
        "schema": "fie-v96-runtime-v1",
        "primary": "runtime/v96_runtime.json",
    },
}


def main() -> None:
    assert set(RESEARCH_STAGE_CONTRACTS) == set(EXPECTED)
    runner = (ROOT / "research/run_fie_league_research_pipeline.py").read_text(encoding="utf-8")
    contract_source = (ROOT / "research/fie_research_pipeline_contract.py").read_text(encoding="utf-8")
    wired_source = runner + contract_source
    manifest_path = ROOT / f"data/research/leagues/{PILOT_LEAGUE_ID}/performance/2026/research_pipeline/stage-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stages = {row.get("name"): row for row in manifest.get("stages", []) if isinstance(row, dict)}

    for name, expected in EXPECTED.items():
        contract = research_stage_contract(name)
        for key in ("artifact_type", "producer", "producer_dependencies", "validator", "schema"):
            assert contract[key] == expected[key], (name, key, contract[key])
        for rel in [expected["producer"], *expected["producer_dependencies"], *expected["validator"]]:
            assert (ROOT / rel).is_file(), rel
            assert Path(rel).name in wired_source, f"unified runner contract does not wire {rel}"

        primary = research_stage_primary_output(PILOT_LEAGUE_ID, 2026, name)
        assert primary.as_posix().endswith(expected["primary"])
        assert primary.is_file(), primary
        stage = stages[name]
        for key in ("artifact_type", "producer", "producer_dependencies", "validator", "schema"):
            assert stage[key] == expected[key], (name, key, stage.get(key))
        assert list(stage.get("outputs") or {}) == [primary.relative_to(ROOT).as_posix()]
        assert stage["outputs"][primary.relative_to(ROOT).as_posix()] == sha256_file(primary)
        assert stage.get("status") == "reused_valid"

    assert "if not primary.is_file()" in runner
    assert 'return "blocked_data"' in runner
    assert "automatic_promotion" in runner and '"automatic_promotion": False' in runner
    print("PASS Tranche 3E exact producers, validators, schemas and governed outputs are typed fail-closed")


if __name__ == "__main__":
    main()

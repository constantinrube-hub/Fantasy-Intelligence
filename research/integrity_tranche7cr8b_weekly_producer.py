#!/usr/bin/env python3
"""Controlled static boundary for the R8B governed weekly-producer preflight."""
from __future__ import annotations

import json
import re
import subprocess

from fie_research_pipeline_contract import ROOT


WORKFLOW = "validate-fie-tranche7cr8b-weekly-producer-preflight.yml"


def main() -> int:
    target = json.loads((ROOT / "config/tranche7cr8b-weekly-producer-preflight.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github/workflows" / WORKFLOW).read_text(encoding="utf-8")
    assert target["tranche"] == "7C-R8B" and target["source_r8a_closure"] == "7d0356a"
    assert target["research_only"] and target["production_model"] == "M9"
    assert not any(target[key] for key in ("production_activation", "app_integration", "runtime_integration", "shadow_integration", "scheduled_collection", "live_provider_request"))
    assert target["season_lock_schema"] == "fie-m10-prospective-season-lock-v2"
    assert set(target["required_source_envelope_fields"]) == {"source_identity", "observed_at", "release_or_etag", "sha256"}
    assert set(lifecycle["active_controlled_workflows"]) == {WORKFLOW}
    assert re.search(r"(?m)^  push:", workflow) and re.search(r"(?m)^  workflow_dispatch:", workflow) and not re.search(r"(?m)^  schedule:", workflow)
    assert "permissions: {contents: read}" in workflow
    for path in ("research/m10_prospective_weekly_producer.py", "research/m10_prospective_operational_capture.py", "research/m10_prospective_source_bundle.py"):
        assert (ROOT / path).is_file(), path
    producer = (ROOT / "research/m10_prospective_weekly_producer.py").read_text(encoding="utf-8")
    for marker in ("fie-m10-prospective-operational-input-v2", "validate_activation_lock", "build_features", "exact_profile_scoring", "BLOCKED_INCOMPLETE_LEGAL_ROSTER", "WINDOW_NOT_REACHED"):
        assert marker in producer, marker
    adapter = (ROOT / "research/m10_prospective_operational_capture.py").read_text(encoding="utf-8")
    assert "R8_INPUT_SCHEMA" in adapter and "exact_profile_scoring" in adapter
    forbidden = subprocess.run(["git", "grep", "-l", "m10_prospective_weekly_producer", "--", "app", "functions", "dist/app"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    assert not forbidden, forbidden
    print("PASS R8B preflight: frozen v2 producer remains research-only with exact replay and typed decision blockers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

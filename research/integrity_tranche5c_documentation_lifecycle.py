#!/usr/bin/env python3
"""Characterize documentation and workflow lifecycle ownership for Tranche 5C."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "docs/current/ARCHITECTURE.md",
    "docs/current/DATA_CONTRACTS.md",
    "docs/current/DEPLOYMENT.md",
    "docs/current/MODEL_GOVERNANCE.md",
    "docs/current/TESTING.md",
    "docs/current/SECURITY.md",
    "docs/current/RELEASE_CHECKLIST.md",
)


def workflow_flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


def main() -> None:
    canonical = {path: (ROOT / path).is_file() for path in CANONICAL_DOCS}
    assert all(canonical.values()), canonical

    root_legacy_patterns = (
        "APPLY_*.md",
        "APPLY_*.txt",
        "PATCH*.md",
        "PATCH*.txt",
        "*_RELEASE_NOTES.md",
        "RELEASE_NOTES_*.md",
        "*-UPLOAD-AND-VALIDATION.md",
    )
    root_legacy = sorted(
        {path.name for pattern in root_legacy_patterns for path in ROOT.glob(pattern)}
    )
    versioned_current = sorted(
        path.name
        for path in (ROOT / "docs/current").glob("*.md")
        if re.match(r"^V\d", path.name)
    )

    workflow_dir = ROOT / ".github/workflows"
    workflows = {path.name: workflow_flags(path) for path in workflow_dir.glob("*.yml")}
    completed_tranche_push = sorted(
        name
        for name, flags in workflows.items()
        if name.startswith("validate-fie-tranche")
        and "tranche5c" not in name
        and flags["push"]
    )
    scheduled = sorted(name for name, flags in workflows.items() if flags["schedule"])

    explicit_tranche4 = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "docs/audits").glob("*TRANCHE4*")
    )
    lifecycle_contract = ROOT / "config/repository-lifecycle-contract.json"

    facts = {
        "canonical_documents_present": canonical,
        "root_legacy_document_count": len(root_legacy),
        "root_legacy_documents": root_legacy,
        "versioned_current_document_count": len(versioned_current),
        "versioned_current_documents": versioned_current,
        "workflow_count": len(workflows),
        "completed_tranche_push_workflows": completed_tranche_push,
        "scheduled_workflows": scheduled,
        "explicit_tranche4_disposition": explicit_tranche4,
        "lifecycle_contract_present": lifecycle_contract.is_file(),
    }

    assert root_legacy, facts
    assert versioned_current, facts
    assert completed_tranche_push, facts
    assert scheduled, facts
    assert not explicit_tranche4, facts
    assert not lifecycle_contract.is_file(), facts

    print(
        "KNOWN_GAP_REPRODUCED documentation and workflow lifecycle ownership "
        "remain fragmented"
    )
    print(json.dumps(facts, sort_keys=True))


if __name__ == "__main__":
    main()

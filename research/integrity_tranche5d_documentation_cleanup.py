#!/usr/bin/env python3
"""Validate the evidence boundary for Tranche 5D documentation cleanup."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "config/tranche5d-documentation-cleanup-preflight.json"


def tracked_inbound_references(source: str) -> list[str]:
    """Return tracked references to a candidate basename outside its source path."""
    name = Path(source).name
    result = subprocess.run(
        ["git", "grep", "-n", "--fixed-strings", "--", name, "--", f":!{source}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.splitlines()


def main() -> None:
    data = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert data["tranche"] == "5D", data
    assert data["phase"] == "evidence_backed_cleanup_preflight", data
    assert data["production_behavior_change"] is False, data
    assert data["validated_tranche5c_head"] == "5a45ad0ab985f8549cc6512684e7d7ab6a838d8d", data

    evidence = data["evidence"]
    assert (ROOT / evidence["canonical_index"]).is_file(), evidence
    for path in evidence["canonical_guides"]:
        assert (ROOT / path).is_file(), path
    for path in evidence["archive_directories"]:
        assert (ROOT / path).is_dir(), path

    candidates = data["candidates"]
    assert len(candidates) == 29, len(candidates)
    sources = [row["source"] for row in candidates]
    destinations = [row["proposed_archive_path"] for row in candidates]
    assert len(sources) == len(set(sources)), sources
    assert len(destinations) == len(set(destinations)), destinations

    allowed_reference_paths = {
        "config/release-gate.json",
        "config/tranche5d-documentation-cleanup-preflight.json",
    }
    destinations_by_source = dict(zip(sources, destinations))
    redirectable = {
        row["source"]: row["referrer"] for row in data["redirectable_references"]
    }
    unresolved: dict[str, list[str]] = {}
    for row in candidates:
        source = row["source"]
        destination = row["proposed_archive_path"]
        assert (ROOT / source).is_file(), source
        assert not (ROOT / destination).exists(), destination
        refs = tracked_inbound_references(source)
        unexpected = []
        for line in refs:
            referrer = line.split(":", 1)[0]
            co_relocated = (
                referrer in destinations_by_source
                and Path(destinations_by_source[referrer]).parent == Path(destination).parent
            )
            if (
                referrer not in allowed_reference_paths
                and referrer != redirectable.get(source)
                and not co_relocated
            ):
                unexpected.append(line)
        if unexpected:
            unresolved[source] = unexpected
    assert not unresolved, unresolved

    retained = data["retained_path_bound_records"]
    assert len(retained) == 4, retained
    for row in retained:
        source = row["source"]
        manifest = row["tracked_historical_manifest"]
        assert (ROOT / source).is_file(), source
        assert (ROOT / manifest).is_file(), manifest
        assert any(line.startswith(f"{manifest}:") for line in tracked_inbound_references(source)), row

    lifecycle_contract = ROOT / "config/repository-lifecycle-contract.json"
    assert lifecycle_contract.is_file(), lifecycle_contract
    lifecycle = json.loads(lifecycle_contract.read_text(encoding="utf-8"))
    assert lifecycle["schema"] == "fie-repository-lifecycle-v1", lifecycle

    print("CLEANUP_EVIDENCE_CONFIRMED historical documents are safe to evaluate for archival relocation")
    print(json.dumps({"candidate_count": len(candidates), "unresolved_references": unresolved}, sort_keys=True))


if __name__ == "__main__":
    main()

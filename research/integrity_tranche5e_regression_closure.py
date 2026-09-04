#!/usr/bin/env python3
"""Bounded regression and release-hygiene integrity for Tranche 5E."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "config/tranche5e-regression-closure-preflight.json"
TARGET = ROOT / "config/tranche5e-regression-closure-target.json"


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def changed_since(commit: str) -> set[str]:
    return {
        path.replace("\\", "/")
        for path in git_output("diff", "--name-only", commit, "HEAD").splitlines()
        if path
    }


def workflow_flags(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {
        "push": bool(re.search(r"(?m)^  push:", text)),
        "schedule": bool(re.search(r"(?m)^  schedule:", text)),
        "dispatch": bool(re.search(r"(?m)^  workflow_dispatch:", text)),
    }


def manifest_drift(*, working_tree: bool) -> list[str]:
    manifest = json.loads((ROOT / "config/build-manifest.json").read_text(encoding="utf-8"))
    drift = []
    for component, row in (manifest.get("files") or {}).items():
        path = str(row["path"])
        if working_tree:
            content = (ROOT / path).read_bytes()
        else:
            content = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
        if hashlib.sha256(content).hexdigest() != row["sha256"]:
            drift.append(component)
    return sorted(drift)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "target", "release"), default="preflight")
    args = parser.parse_args()

    data = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    assert data["tranche"] == "5E", data
    assert data["phase"] == "bounded_regression_closure_preflight", data
    assert data["production_behavior_change"] is False, data
    baseline = data["validated_tranche5d_closure_head"]
    subprocess.run(["git", "merge-base", "--is-ancestor", baseline, "HEAD"], cwd=ROOT, check=True)
    for path in data["required_integrity_paths"]:
        assert (ROOT / path).is_file(), path

    lifecycle = json.loads((ROOT / "config/repository-lifecycle-contract.json").read_text(encoding="utf-8"))
    preflight_workflow = ROOT / ".github/workflows" / data["preflight_workflow"]
    release_workflow = ROOT / ".github/workflows" / data["release_workflow"]
    assert preflight_workflow.is_file(), preflight_workflow
    assert release_workflow.is_file(), release_workflow
    assert "5E regression and closure" in (ROOT / "docs/audits/AUDIT_CURRENT_STATE.md").read_text(encoding="utf-8")

    if args.mode == "preflight":
        assert not TARGET.exists(), TARGET
        assert changed_since(baseline) <= set(data["preflight_allowed_paths"])
        assert set(lifecycle.get("active_controlled_workflows") or []) == {data["preflight_workflow"]}
        assert workflow_flags(preflight_workflow) == {"push": True, "schedule": False, "dispatch": True}
        assert workflow_flags(release_workflow) == {"push": True, "schedule": False, "dispatch": True}
        assert "config/tranche5e-regression-closure-target.json" in release_workflow.read_text(encoding="utf-8")
        drift = manifest_drift(working_tree=False)
        assert drift == data["known_preflight_manifest_drift"], drift
        print("KNOWN_GAP_REPRODUCED one lifecycle-contract manifest entry is stale after prior closure synchronization")
    else:
        assert TARGET.is_file(), TARGET
        target = json.loads(TARGET.read_text(encoding="utf-8"))
        validated = target.get("validated_preflight") or {}
        commit = str(validated.get("commit") or "")
        run = str(validated.get("github_actions_run") or "")
        assert len(commit) == 40 and run.isdigit(), validated
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=True)
        assert changed_since(commit) <= set(data["target_allowed_paths"]), changed_since(commit)
        assert not (lifecycle.get("active_controlled_workflows") or []), lifecycle
        assert workflow_flags(preflight_workflow) == {"push": False, "schedule": False, "dispatch": True}
        assert workflow_flags(release_workflow) == {"push": True, "schedule": False, "dispatch": True}
        if args.mode == "release":
            assert not manifest_drift(working_tree=True), manifest_drift(working_tree=True)
            print("TARGET_RELEASE_GAP_CLOSED bounded regression closure has a fresh manifest")
        else:
            print("TARGET_GAP_CLOSED bounded regression closure is authorized from a green preflight")

    print(json.dumps({"mode": args.mode, "baseline": baseline}, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""No-network tests for refresh ordering, current inputs, and receipt lineage."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import weekly_pipeline_readiness as pipeline
from workflow_usability import classify_emission, build_report, make_summary

NOW = datetime(2026, 10, 7, 13, tzinfo=timezone.utc)
TARGET = {"season": 2026, "week": 5}
LID = "111111"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def fixture(root: Path) -> None:
    prefix = f"data/research/leagues/{LID}"
    fp, sig = "profile", "scoring"
    write(root / "data/research/leagues/registry.json", {"leagues": {
        LID: {"enabled": True, "current_refresh": True, "profile_path": prefix + "/profile.json",
              "profile_fingerprint": fp, "scoring_signature": sig},
        "retired": {"enabled": False}}})
    write(root / prefix / "profile.json", {"league_id": LID, "profile_fingerprint": fp, "scoring_signature": sig})
    for deployment in ("", "dist/"):
        base = root / deployment / prefix
        core_path = base / "app/core.json"
        write(core_path, {"league_id": LID, "profile_fingerprint": fp, "scoring_signature": sig,
                          "sleeper": {"league": {"season": "2026"}}})
        write(base / "app/manifest.json", {"league_id": LID, "profile_fingerprint": fp, "scoring_signature": sig,
            "core": {"path": prefix + "/app/core.json", "sha256": pipeline.digest(core_path)}})
        write(base / "current/milestone5_current.json", {"league_id": LID, **TARGET,
            "generated_at": "2026-10-07T12:00:00Z", "profile_fingerprint": fp,
            "scoring_signature": sig, "profile_scoring_signature": sig,
            "profile_current_match": True, "target_week_realised_stats_excluded": True, "players": []})


def verify(root: Path, **kwargs) -> dict:
    return pipeline.verify_inputs(root, target=TARGET, as_of=NOW, league_id=None, max_age_hours=36, **kwargs)


def reject(call, reason: str) -> None:
    try:
        call()
    except ValueError as exc:
        assert str(exc) == reason, str(exc)
    else:
        raise AssertionError("Expected " + reason)


def event(stage="actions") -> dict:
    return {"workflow_run": {"name": pipeline.UPSTREAM[stage], "event": "schedule" if stage == "actions" else "workflow_run",
        "status": "completed", "conclusion": "success", "head_branch": "main", "head_sha": "a" * 40,
        "head_repository": {"full_name": "owner/repo"}, "id": 12, "run_started_at": "2026-10-07T11:00:00Z"}}


def test_inputs_and_blockers() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        before = {str(p): p.read_bytes() for p in root.rglob("*.json")}
        ready = verify(root)
        assert ready["status"] == "READY" and ready["league_count"] == 1
        assert ready["league_ids"] == [LID] and len(ready["input_hashes"]) == 8
        assert before == {str(p): p.read_bytes() for p in root.rglob("*.json")}
        assert verify(root, minimum_generated_at=NOW)["reason_codes"] == ["BLOCKED_PIPELINE_REFRESH_DID_NOT_PUBLISH_LEAGUE"]
        cases = [
            ("week", 4, "BLOCKED_PIPELINE_CURRENT_WEEK_MISMATCH"),
            ("generated_at", "2026-10-01T12:00:00Z", "BLOCKED_PIPELINE_CURRENT_FRESHNESS"),
            ("generated_at", "2026-10-08T12:00:00Z", "BLOCKED_PIPELINE_CURRENT_FRESHNESS"),
            ("generated_at", "2026-10-07T12:00:00", "BLOCKED_PIPELINE_CURRENT_INPUT_INVALID"),
            ("profile_fingerprint", "foreign", "BLOCKED_PIPELINE_PROFILE_BINDING"),
            ("scoring_signature", "foreign", "BLOCKED_PIPELINE_SCORING_BINDING"),
            ("profile_current_match", False, "BLOCKED_PIPELINE_PROFILE_DRIFT"),
            ("target_week_realised_stats_excluded", False, "BLOCKED_PIPELINE_REALIZED_STATS_GUARD"),
        ]
        source = root / f"data/research/leagues/{LID}/current/milestone5_current.json"
        original = pipeline.read(source)
        for key, value, reason in cases:
            write(source, {**original, key: value})
            assert reason in verify(root)["reason_codes"], (key, verify(root))
        write(source, original)
        deploy = root / f"dist/data/research/leagues/{LID}/current/milestone5_current.json"
        write(deploy, {**original, "week": 4})
        assert "BLOCKED_PIPELINE_SOURCE_DIST_MISMATCH" in verify(root)["reason_codes"]
        write(deploy, original)
        core = root / f"data/research/leagues/{LID}/app/core.json"
        write(core, {**pipeline.read(core), "league_id": "foreign"})
        reasons = verify(root)["reason_codes"]
        assert "BLOCKED_PIPELINE_APP_CORE_HASH" in reasons and "BLOCKED_PIPELINE_APP_CORE_LEAGUE" in reasons
        deploy.unlink()
        assert "BLOCKED_PIPELINE_CURRENT_INPUT_INVALID" in verify(root)["reason_codes"]
        reject(lambda: pipeline.safe_path(root, "../foreign"), "BLOCKED_PIPELINE_PATH_OUTSIDE_ROOT")


def test_split_storage_hashes() -> None:
    from current_snapshot_storage import BASE_FORMAT, OVERLAY_FORMAT, STORAGE_FORMAT
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        for deployment in ("", "dist/"):
            tree = root / deployment
            base_rel, overlay_rel = "data/research/shared/current/base.json", "data/research/shared/current/overlay.json"
            write(tree / base_rel, {"format": BASE_FORMAT, "players": [{"sleeper_id": "player"}]})
            write(tree / overlay_rel, {"format": OVERLAY_FORMAT, "scoring_signature": "scoring", "projections": {}})
            current = tree / f"data/research/leagues/{LID}/current/milestone5_current.json"
            data = pipeline.read(current)
            data.pop("players")
            data["storage"] = {"format": STORAGE_FORMAT, "player_base": base_rel, "scoring_overlay": overlay_rel, "player_count": 1}
            write(current, data)
        ready = verify(root)
        assert ready["status"] == "READY", ready
        assert len(ready["input_hashes"]) == 12
        write(root / "data/research/shared/current/overlay.json", {"format": OVERLAY_FORMAT, "scoring_signature": "foreign"})
        assert "BLOCKED_PIPELINE_CURRENT_INPUT_INVALID" in verify(root)["reason_codes"]


def test_triggers_and_receipts() -> None:
    assert pipeline.verify_trigger(event(), stage="actions", repository="owner/repo")["run_id"] == "12"
    for key, value in [("conclusion", "failure"), ("head_branch", "candidate"), ("name", "unrelated"),
                       ("event", "pull_request"), ("status", "in_progress"), ("head_repository", {"full_name": "fork/repo"})]:
        mutated = event()
        mutated["workflow_run"][key] = value
        reject(lambda: pipeline.verify_trigger(mutated, stage="actions", repository="owner/repo"), "BLOCKED_PIPELINE_UPSTREAM_UNTRUSTED")
    current = {"league_ids": [LID], "input_hashes": {"profile": "hash"}}
    prior = {"schema": pipeline.SCHEMA, "stage": "actions", "status": "READY", "run_id": "12",
             "input_commit": "a" * 40, "verified_at": NOW.isoformat(), **current}
    pipeline.verify_prior(prior, current, upstream_run_id="12", as_of=NOW)
    reject(lambda: pipeline.verify_prior(prior, current, upstream_run_id="13", as_of=NOW), "BLOCKED_PIPELINE_UPSTREAM_RECEIPT_IDENTITY")
    reject(lambda: pipeline.verify_prior(prior, {**current, "input_hashes": {"profile": "new"}}, upstream_run_id="12", as_of=NOW), "BLOCKED_PIPELINE_UPSTREAM_INPUT_CHANGED")
    reject(lambda: pipeline.verify_prior(prior, {**current, "league_ids": []}, upstream_run_id="12", as_of=NOW), "BLOCKED_PIPELINE_UPSTREAM_RECEIPT_SCOPE")


def test_monitoring_and_workflow_contract() -> None:
    root = pipeline.ROOT
    for stage, path in [("actions", "build-fie-window1c-weekly-actions.yml"), ("waiver", "build-fie-window1d-optimal-waiver.yml")]:
        content = (root / ".github/workflows" / path).read_text()
        assert "  schedule:" not in content
        assert f'workflows: ["{pipeline.UPSTREAM[stage]}"]' in content
        assert "types: [completed]" in content and "branches: [main]" in content
        assert "workflow_dispatch:" in content and "cancel-in-progress: false" in content
        assert "github.event.workflow_run.head_repository.full_name == github.repository" in content
        assert "ref: main" in content and "steps.readiness.outputs.ready == 'true'" in content
        assert "--dependency-file .cache/fie-weekly-inputs.json" in content
        assert "--adapter weekly-pipeline" in content
        assert "name: fie-weekly-inputs" in content
        assert content.index("Verify published current inputs") < content.index("Commit only")
        if stage == "waiver":
            assert "run-id: ${{ github.event.workflow_run.id }}" in content and "actions: read" in content
            assert "producer.conclusion === 'skipped'" in content
            assert "needs.upstream.outputs.available == 'true'" in content
            assert "artifact.name === 'fie-weekly-inputs' && !artifact.expired" in content
            assert "completed weekly-actions without a live fie-weekly-inputs receipt" in content
            assert '"status":"NO_DUE"' in content and "Upload expected no-op evidence" in content
    assert "cancel-in-progress: false" in (root / ".github/workflows/build-fie-current.yml").read_text()
    refresh = (root / ".github/workflows/build-fie-current.yml").read_text()
    assert refresh.index("git checkout -B main origin/main") < refresh.index("Build league-specific current snapshots")
    assert "git rebase --abort" in refresh and "generated release artifacts must be rebuilt" in refresh
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        dependency = tmp / "receipt.json"
        write(dependency, {"schema": pipeline.SCHEMA, "status": "BLOCKED", "reason_codes": ["BLOCKED_PIPELINE_CURRENT_WEEK_MISMATCH"]})
        state, reasons, _ = classify_emission(adapter="weekly-pipeline", dependency_file=dependency, job_status="success", root=tmp)
        assert state == "BLOCKED" and reasons == ["BLOCKED_PIPELINE_CURRENT_WEEK_MISMATCH"]
        write(dependency, {"schema": pipeline.SCHEMA, "status": "NO_DUE", "reason_codes": ["PIPELINE_UPSTREAM_NOT_DUE"]})
        assert classify_emission(adapter="weekly-pipeline", dependency_file=dependency, job_status="success", root=tmp)[0] == "NO_OP"
        assert classify_emission(adapter="weekly-pipeline", dependency_file=dependency, job_status="failure", root=tmp)[0] == "INFRASTRUCTURE"
        config = pipeline.read(root / "config/workflow-usability-monitor.json")
        run = {"id": 12, "path": ".github/workflows/build-fie-window1c-weekly-actions.yml", "event": "workflow_run", "status": "completed", "conclusion": "success"}
        summary = make_summary(workflow_path=run["path"], workflow_name="actions", run_id="12", event="workflow_run", adapter="weekly-pipeline",
                               job_status="success", state="NO_OP", reasons=["PIPELINE_UPSTREAM_NOT_DUE"], detail={})
        report = build_report(config=config, runs=[run], summaries={12: summary}, generated_at=NOW.isoformat(), repository="owner/repo")
        assert report["run_count"] == 1


def test_cli_handoff_and_immutable_archive() -> None:
    from integrity_workflow_decision_context_test import schedule
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        source_schedule = root / "schedule.csv"
        source_schedule.write_bytes(schedule())
        payload, receipt, output = root / "event.json", root / "inputs.json", root / "github-output"

        def invoke(stage: str, incoming: dict, *, now=NOW, prior=None, manual=False, attempt="1") -> dict:
            write(payload, incoming)
            argv = ["pipeline", "--stage", stage, "--event", "workflow_dispatch" if manual else "workflow_run",
                    "--event-path", str(payload), "--repository", "owner/repo", "--root", str(root),
                    "--as-of-utc", now.isoformat(), "--schedule-path", str(source_schedule), "--output", str(receipt), "--archive"]
            if prior:
                argv += ["--upstream-inputs", str(prior)]
            run_id = "99" if stage == "actions" else "100"
            with patch.object(sys, "argv", argv), patch.dict(os.environ, {"GITHUB_RUN_ID": run_id, "GITHUB_RUN_ATTEMPT": attempt, "GITHUB_OUTPUT": str(output)}), \
                    patch.object(pipeline.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "a" * 40 + "\n", "")), redirect_stdout(io.StringIO()):
                pipeline.main()
            return pipeline.read(receipt)

        ready = invoke("actions", event())
        assert ready["status"] == "READY" and ready["target"]["week"] == 5 and ready["automatic"] is True
        assert "ready=true" in output.read_text()
        assert len(list((root / "data/operations/weekly-pipeline").rglob("*.json"))) == 1
        prior_path = root / "prior.json"
        write(prior_path, ready)
        chained_event = event("waiver")
        chained_event["workflow_run"]["id"] = 99
        waiver = invoke("waiver", chained_event, prior=prior_path)
        assert waiver["status"] == "READY" and waiver["source_refresh"]["run_id"] == "12"
        archive = pipeline.archive_inputs(root, ready)
        before = archive.read_bytes()
        reject(lambda: pipeline.archive_inputs(root, {**ready, "input_commit": "b" * 40}), "BLOCKED_PIPELINE_ARCHIVE_IMMUTABLE_CONFLICT")
        assert archive.read_bytes() == before
        missing = invoke("waiver", chained_event)
        assert missing["reason_codes"] == ["BLOCKED_PIPELINE_UPSTREAM_RECEIPT_MISSING"]
        # Even a same-week refresh changes the bound input evidence and must
        # not silently rerun the next stage against another snapshot.
        current = root / f"data/research/leagues/{LID}/current/milestone5_current.json"
        write(current, {**pipeline.read(current), "new_data": True})
        changed = invoke("waiver", chained_event, prior=prior_path)
        assert changed["status"] == "BLOCKED" and "BLOCKED_PIPELINE_UPSTREAM_INPUT_CHANGED" in changed["reason_codes"]
        thursday = NOW.replace(day=8)
        no_due = invoke("actions", event(), now=thursday)
        assert no_due["status"] == "NO_DUE"
        write(prior_path, no_due)
        assert invoke("waiver", chained_event, prior=prior_path, now=thursday)["status"] == "NO_DUE"
        # A manual recovery chain remains usable on a Thursday.
        manual = deepcopy(ready)
        manual.update(automatic=False, run_attempt="2")
        manual["input_hashes"] = verify(root)["input_hashes"]
        write(prior_path, manual)
        manual_receipt = invoke("waiver", chained_event, prior=prior_path, now=thursday, attempt="2")
        assert manual_receipt["automatic"] is False and manual_receipt["status"] == "READY", manual_receipt


def main() -> None:
    tests = [test_inputs_and_blockers, test_split_storage_hashes, test_triggers_and_receipts, test_monitoring_and_workflow_contract,
             test_cli_handoff_and_immutable_archive]
    for test in tests:
        test()
    print("PASS weekly pipeline ordering, freshness, source/dist binding, immutable receipt identity, and typed monitoring")


if __name__ == "__main__":
    main()

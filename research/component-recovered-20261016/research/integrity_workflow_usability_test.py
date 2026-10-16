#!/usr/bin/env python3
"""No-network regression checks for workflow usability monitoring."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from workflow_usability import (
    CONFIG_PATH,
    REPORT_SCHEMA,
    SCHEMA,
    STATES,
    build_report,
    classify_emission,
    fallback_summary,
    make_summary,
    report_markdown,
    validate_summary,
)

ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def test_contract_and_adapters() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["schema"] == "fie-workflow-usability-monitor-v1"
    assert tuple(config["states"]) == STATES
    assert config["automatic_events"] == ["schedule", "workflow_run"]
    paths = [row["path"] for row in config["workflows"]]
    assert len(paths) == len(set(paths)) == 13

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        targets, completed = root / "targets", root / "completed"
        targets.write_text("1\n2\n"); completed.write_text("1\n2\n")
        assert classify_emission(adapter="current-refresh", job_status="success", target_file=targets, completed_file=completed, root=root)[0] == "USABLE"
        completed.write_text("1\n")
        assert classify_emission(adapter="current-refresh", job_status="success", target_file=targets, completed_file=completed, root=root)[0] == "PARTIAL"

        report = root / "report.json"
        index = root / "index.json"
        write(report, {"season": 2026, "week": 5, "operational_readiness": {"status": "PARTIAL", "counts": {"ready": 2, "blocked": 1}}})
        write(index, {"report_json": str(report)})
        state, reasons, detail = classify_emission(adapter="readiness-index", job_status="success", source_file=index, root=root)
        assert state == "PARTIAL" and reasons == ["OPERATIONAL_READINESS_PARTIAL"] and detail["week"] == 5

        audit = root / "audit.json"
        waiver_index = root / "waiver-index.json"
        write(audit, {"season": 2026, "requested_weeks": [3, 4, 5], "captured_league_count": 2,
                      "invocation_status": "PARTIAL_SOURCE_FAILURE",
                      "invocation_observations": [{"source_errors": []}, {"source_errors": ["timeout"]}]})
        write(waiver_index, {"audit_path": str(audit)})
        assert classify_emission(adapter="waiver-index", job_status="success", source_file=waiver_index, root=root)[0] == "PARTIAL"

        availability = root / "availability.json"
        write(availability, {"capture_status": "CREATED", "rows": 10, "coverage": {"IDP": {"rows": 5}}})
        assert classify_emission(adapter="availability-index", job_status="success", source_file=availability, root=root)[0] == "USABLE"
        write(availability, {"capture_status": "EXISTS"})
        assert classify_emission(adapter="availability-index", job_status="success", source_file=availability, root=root)[0] == "NO_OP"

        checkpoint = root / "checkpoint.json"
        write(checkpoint, {"status": "MISSED", "manifest": "missed-capture.json"})
        assert classify_emission(adapter="checkpoint-json", job_status="success", source_file=checkpoint, root=root)[0] == "MISSED"
        assert classify_emission(adapter="policy-commit", job_status="success", policy_allowed="false", policy_reason="OUTSIDE_CHECKPOINT_WINDOW", root=root)[0] == "NO_OP"
        assert classify_emission(adapter="commit", job_status="failure", root=root)[0] == "INFRASTRUCTURE"


def test_summary_report_and_fail_closed_fallback() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    definition = config["workflows"][0]
    run = {
        "id": 11, "path": definition["path"], "name": definition["name"], "event": "schedule",
        "status": "completed",
        "created_at": "2026-10-03T10:00:00Z", "updated_at": "2026-10-03T10:02:00Z",
        "conclusion": "success", "html_url": "https://github.example/runs/11", "head_sha": "abc",
    }
    summary = make_summary(
        workflow_path=definition["path"], workflow_name=definition["name"], run_id="11", event="schedule",
        adapter="current-refresh", job_status="success", state="USABLE", reasons=["READY"], detail={},
        observed_at="2026-10-03T10:02:00Z",
    )
    assert summary["schema"] == SCHEMA and validate_summary(summary, run, definition["path"])["usable"] is True
    missing = fallback_summary(run, definition["path"], [{"name": "refresh-current", "conclusion": "success"}])
    assert missing["state"] == "BLOCKED" and missing["investigate_recommended"] is True
    skipped = fallback_summary(run, definition["path"], [
        {"name": "calendar / policy", "conclusion": "success"},
        {"name": "refresh-current", "conclusion": "skipped"},
    ])
    assert skipped["state"] == "NO_OP" and skipped["investigate_recommended"] is False
    failed_run = {**run, "id": 12, "conclusion": "failure"}
    failed = fallback_summary(failed_run, definition["path"], [])
    in_progress = {**run, "id": 13, "status": "in_progress", "conclusion": None}
    report = build_report(
        config=config, runs=[run, failed_run, in_progress], summaries={11: summary, 12: failed, 13: failed},
        generated_at="2026-10-04T08:00:00+00:00", repository="constantinrube-hub/Fantasy-Intelligence",
    )
    assert report["schema"] == REPORT_SCHEMA and report["run_count"] == 2
    assert report["usable_run_count"] == 1 and report["investigate_run_count"] == 1
    text = report_markdown(report)
    assert "Runs worth investigating" in text and "RUN_FAILURE" in text and "Expected no-ops" in text


def test_workflow_instrumentation_and_calendar() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    reusable = (ROOT / ".github/workflows/_fie-evidence-capture-reusable.yml").read_text(encoding="utf-8")
    for row in config["workflows"]:
        text = (ROOT / row["path"]).read_text(encoding="utf-8")
        if row["path"] in {
            ".github/workflows/capture-fie-waiver-evidence.yml",
            ".github/workflows/capture-fie-weather-evidence.yml",
        }:
            assert "_fie-evidence-capture-reusable.yml" in text
            assert row["path"] in reusable and row["name"] in reusable
        else:
            assert "workflow_usability.py emit" in text, row["path"]
            assert "name: fie-workflow-usability" in text, row["path"]
            assert "if: always()" in text, row["path"]
    workflow = (ROOT / ".github/workflows/report-fie-workflow-usability.yml").read_text(encoding="utf-8")
    assert "purpose: workflow_usability" in workflow
    assert "actions: read" in workflow and "contents: write" in workflow
    assert "workflow_usability.py collect" in workflow
    assert "cron: '7 10 1-11 1 *'" in workflow
    assert "* 2-3 *" not in workflow


def main() -> None:
    test_contract_and_adapters()
    test_summary_report_and_fail_closed_fallback()
    test_workflow_instrumentation_and_calendar()
    print("PASS workflow usability states, producer summaries, fail-closed aggregation, and rolling report")


if __name__ == "__main__":
    main()

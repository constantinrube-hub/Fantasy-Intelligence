#!/usr/bin/env python3
"""Emit and aggregate truthful usability evidence for automatic workflows.

This module observes workflow results.  It never changes model eligibility,
recommendations, forecast captures, or transaction behavior.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/workflow-usability-monitor.json"
SCHEMA = "fie-workflow-usability-summary-v1"
REPORT_SCHEMA = "fie-workflow-usability-report-v1"
STATES = ("USABLE", "NO_OP", "PARTIAL", "BLOCKED", "MISSED", "INFRASTRUCTURE")
UTC = timezone.utc


class StripAuthorizationOnRedirect(HTTPRedirectHandler):
    """Keep the repository token away from signed artifact-storage hosts."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
        return redirected


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def bool_value(value: str | bool | None) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _git_changed_paths(root: Path, initial_sha: str | None) -> list[str]:
    if not initial_sha:
        return []
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            text=True, capture_output=True,
        ).stdout.strip()
        if head == initial_sha:
            return []
        return [line for line in subprocess.run(
            ["git", "diff", "--name-only", f"{initial_sha}..{head}"], cwd=root,
            check=True, text=True, capture_output=True,
        ).stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return []


def _state_for_readiness(status: str) -> tuple[str, list[str]]:
    value = status.upper().strip()
    if value == "READY":
        return "USABLE", ["OPERATIONAL_READINESS_READY"]
    if value == "PARTIAL":
        return "PARTIAL", ["OPERATIONAL_READINESS_PARTIAL"]
    if value in {"NOT_APPLICABLE", "NO_DUE"}:
        return "NO_OP", [f"OPERATIONAL_READINESS_{value}"]
    if value in {"BLOCKED", "NO_LEAGUES"}:
        return "BLOCKED", [f"OPERATIONAL_READINESS_{value}"]
    return "BLOCKED", ["OPERATIONAL_READINESS_UNKNOWN", value or "EMPTY_STATUS"]


def classify_emission(
    *, adapter: str, job_status: str, source_file: Path | None = None,
    policy_allowed: str | bool | None = None, policy_reason: str | None = None,
    root: Path = ROOT, initial_sha: str | None = None,
    target_file: Path | None = None, completed_file: Path | None = None,
) -> tuple[str, list[str], dict[str, Any]]:
    status = str(job_status or "unknown").lower()
    if status != "success":
        return "INFRASTRUCTURE", [f"JOB_{status.upper()}"], {}

    allowed = bool_value(policy_allowed)
    reason = str(policy_reason or "").strip().upper()
    if allowed is False:
        state = "MISSED" if "MISSED" in reason else "NO_OP"
        return state, [reason or "POLICY_NOT_DUE"], {"policy_allowed": False}

    if adapter == "current-refresh":
        targets = [x for x in (target_file.read_text().splitlines() if target_file and target_file.is_file() else []) if x]
        completed = [x for x in (completed_file.read_text().splitlines() if completed_file and completed_file.is_file() else []) if x]
        detail = {"target_count": len(set(targets)), "completed_count": len(set(completed))}
        if not targets or not completed:
            return "BLOCKED", ["NO_CURRENT_REFRESH_OUTPUT"], detail
        if set(completed) != set(targets):
            return "PARTIAL", ["CURRENT_REFRESH_PORTFOLIO_INCOMPLETE"], detail
        return "USABLE", ["CURRENT_REFRESH_ALL_TARGETS_COMPLETE"], detail

    if adapter == "readiness-index":
        if not source_file or not source_file.is_file():
            return "BLOCKED", ["OUTPUT_INDEX_MISSING"], {}
        index = read_json(source_file)
        report_path = Path(str(index.get("report_json") or ""))
        if not report_path.is_absolute():
            report_path = root / report_path
        if not report_path.is_file():
            return "BLOCKED", ["REPORT_JSON_MISSING"], {"output_index": str(source_file)}
        report = read_json(report_path)
        readiness = report.get("operational_readiness") or {}
        state, reasons = _state_for_readiness(str(readiness.get("status") or ""))
        return state, reasons, {
            "season": report.get("season"), "week": report.get("week"),
            "counts": readiness.get("counts") or {}, "report_json": str(report_path.relative_to(root)),
        }

    if adapter == "waiver-index":
        if not source_file or not source_file.is_file():
            return "BLOCKED", ["WAIVER_OUTPUT_INDEX_MISSING"], {}
        index = read_json(source_file)
        audit_path = Path(str(index.get("audit_path") or ""))
        if not audit_path.is_absolute():
            audit_path = root / audit_path
        if not audit_path.is_file():
            return "BLOCKED", ["WAIVER_AUDIT_MISSING"], {}
        audit = read_json(audit_path)
        invocation = str(audit.get("invocation_status") or "UNKNOWN")
        detail = {
            "season": audit.get("season"), "rounds": audit.get("requested_weeks") or [],
            "captured_league_count": audit.get("captured_league_count"),
            "source_failure_league_count": sum(bool(row.get("source_errors")) for row in audit.get("invocation_observations") or []),
        }
        if invocation == "PARTIAL_SOURCE_FAILURE":
            return "PARTIAL", [invocation], detail
        if invocation == "OBSERVED_PRIVATE_BOOK_UNKNOWN":
            return "USABLE", [invocation, "PRIVATE_ABSENCE_REMAINS_UNKNOWN"], detail
        return "BLOCKED", ["WAIVER_INVOCATION_STATUS_UNKNOWN", invocation], detail

    if adapter == "availability-index":
        if not source_file or not source_file.is_file():
            return "BLOCKED", ["AVAILABILITY_OUTPUT_INDEX_MISSING"], {}
        result = read_json(source_file)
        capture_status = str(result.get("capture_status") or "UNKNOWN")
        detail = {"capture_status": capture_status, "rows": result.get("rows"), "coverage": result.get("coverage") or {}}
        if capture_status == "CREATED":
            return "USABLE", ["AVAILABILITY_CAPTURE_CREATED"], detail
        if capture_status == "EXISTS":
            return "NO_OP", ["AVAILABILITY_CAPTURE_ALREADY_EXISTS"], detail
        if capture_status.startswith("SKIPPED"):
            return "NO_OP", [capture_status], detail
        return "BLOCKED", ["AVAILABILITY_CAPTURE_STATUS_UNKNOWN", capture_status], detail

    if adapter == "checkpoint-json":
        if not source_file or not source_file.is_file():
            return "BLOCKED", ["CHECKPOINT_RESULT_MISSING"], {}
        result = read_json(source_file)
        checkpoint_status = str(result.get("status") or "UNKNOWN")
        detail = {"checkpoint_status": checkpoint_status, "manifest": result.get("manifest")}
        if checkpoint_status in {"CREATED", "COMPLETE"}:
            return "USABLE", [f"CHECKPOINT_{checkpoint_status}"], detail
        if checkpoint_status in {"EXISTS", "WINDOW_NOT_REACHED", "NOT_REGULAR_SEASON"}:
            return "NO_OP", [f"CHECKPOINT_{checkpoint_status}"], detail
        if checkpoint_status == "MISSED":
            return "MISSED", ["CHECKPOINT_MISSED"], detail
        return "BLOCKED", ["CHECKPOINT_STATUS_UNKNOWN", checkpoint_status], detail

    if adapter in {"commit", "policy-commit"}:
        changed = _git_changed_paths(root, initial_sha)
        detail = {"changed_paths": changed[:100], "changed_path_count": len(changed)}
        if changed:
            if any("missed" in Path(path).name.lower() for path in changed):
                return "MISSED", ["MISSED_CAPTURE_COMMITTED"], detail
            return "USABLE", ["NEW_CONTRACT_VALID_OUTPUT_COMMITTED"], detail
        if adapter == "policy-commit" and allowed is True:
            return "BLOCKED", [reason or "DUE_OPERATION_PRODUCED_NO_NEW_EVIDENCE"], detail
        return "NO_OP", ["NO_REPOSITORY_CHANGE"], detail

    return "BLOCKED", ["UNKNOWN_USABILITY_ADAPTER", adapter], {}


def make_summary(
    *, workflow_path: str, workflow_name: str, run_id: str, event: str,
    adapter: str, job_status: str, state: str, reasons: list[str], detail: dict[str, Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    if state not in STATES:
        raise ValueError(f"Unsupported workflow usability state: {state}")
    return {
        "schema": SCHEMA,
        "workflow_path": workflow_path,
        "workflow_name": workflow_name,
        "run_id": int(run_id),
        "event": event,
        "job_status": job_status,
        "state": state,
        "usable": state == "USABLE",
        "investigate_recommended": state in {"PARTIAL", "BLOCKED", "MISSED", "INFRASTRUCTURE"},
        "reason_codes": sorted(set(filter(None, reasons))),
        "adapter": adapter,
        "observed_at_utc": observed_at or datetime.now(UTC).isoformat(),
        "detail": detail,
    }


class GitHub:
    def __init__(self, repository: str, token: str | None):
        if not repository or "/" not in repository:
            raise ValueError("GITHUB_REPOSITORY owner/name is required")
        self.repository, self.token = repository, token
        self.opener = build_opener(StripAuthorizationOnRedirect())

    def _request(self, suffix: str, *, binary: bool = False) -> Any:
        if not suffix.startswith("/actions/"):
            raise ValueError("Workflow usability API is restricted to Actions endpoints")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FIE-Workflow-Usability/1.0",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(f"https://api.github.com/repos/{self.repository}{suffix}", headers=headers)
        try:
            with self.opener.open(request, timeout=45) as response:
                raw = response.read()
                return raw if binary else json.loads(raw or b"{}")
        except HTTPError as exc:
            raise RuntimeError(f"GitHub Actions GET {suffix}: HTTP {exc.code}") from None

    def pages(self, endpoint: str, key: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for page in range(1, 101):
            separator = "&" if "?" in endpoint else "?"
            payload = self._request(f"{endpoint}{separator}per_page=100&page={page}")
            batch = payload.get(key) or []
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise ValueError("Actions pagination limit exceeded")

    def runs(self, created_since: str) -> list[dict[str, Any]]:
        return self.pages("/actions/runs?" + urlencode({"created": f">={created_since}"}), "workflow_runs")

    def artifacts(self, run_id: int) -> list[dict[str, Any]]:
        return self.pages(f"/actions/runs/{run_id}/artifacts", "artifacts")

    def repository_artifacts(self) -> list[dict[str, Any]]:
        return self.pages("/actions/artifacts", "artifacts")

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        return self.pages(f"/actions/runs/{run_id}/jobs", "jobs")

    def artifact_summary(self, artifact: dict[str, Any]) -> dict[str, Any]:
        raw = self._request(f"/actions/artifacts/{artifact['id']}/zip", binary=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [name for name in archive.namelist() if Path(name).name == "fie-workflow-usability.json"]
            if len(names) != 1:
                raise ValueError("Usability artifact must contain exactly one summary")
            return json.loads(archive.read(names[0]))


def validate_summary(summary: dict[str, Any], run: dict[str, Any], expected_path: str) -> dict[str, Any]:
    if summary.get("schema") != SCHEMA or summary.get("state") not in STATES:
        raise ValueError("Invalid workflow usability summary contract")
    if int(summary.get("run_id")) != int(run["id"]):
        raise ValueError("Workflow usability run identity mismatch")
    if summary.get("workflow_path") != expected_path or summary.get("event") != run.get("event"):
        raise ValueError("Workflow usability workflow/event identity mismatch")
    return summary


def fallback_summary(run: dict[str, Any], expected_path: str, jobs: list[dict[str, Any]]) -> dict[str, Any]:
    conclusion = str(run.get("conclusion") or "UNKNOWN").lower()
    if conclusion != "success":
        state, reasons = "INFRASTRUCTURE", [f"RUN_{conclusion.upper()}", "USABILITY_ARTIFACT_UNAVAILABLE"]
    else:
        def calendar_job(job: dict[str, Any]) -> bool:
            name = str(job.get("name") or "").strip().lower()
            return name in {"calendar", "policy"} or name.startswith("calendar /") or name.endswith("/ policy")
        non_calendar = [job for job in jobs if not calendar_job(job)]
        if non_calendar and all(job.get("conclusion") == "skipped" for job in non_calendar):
            state, reasons = "NO_OP", ["CALENDAR_POLICY_SKIPPED_PRODUCER"]
        else:
            state, reasons = "BLOCKED", ["USABILITY_SUMMARY_MISSING_OR_LEGACY_RUN"]
    return make_summary(
        workflow_path=expected_path, workflow_name=str(run.get("name") or expected_path),
        run_id=str(run["id"]), event=str(run.get("event") or "unknown"),
        adapter="fallback", job_status=conclusion, state=state, reasons=reasons,
        detail={"summary_artifact_present": False}, observed_at=run.get("updated_at") or run.get("created_at"),
    )


def build_report(
    *, config: dict[str, Any], runs: list[dict[str, Any]], summaries: dict[int, dict[str, Any]],
    generated_at: str, repository: str,
) -> dict[str, Any]:
    monitored = {row["path"]: row for row in config["workflows"]}
    allowed_events = set(config.get("automatic_events") or ["schedule"])
    selected = [run for run in runs if run.get("path") in monitored
                and run.get("event") in allowed_events and run.get("status") == "completed"]
    rows = []
    for run in sorted(selected, key=lambda row: (row.get("created_at") or "", int(row["id"])), reverse=True):
        summary = summaries[int(run["id"])]
        rows.append({
            "run_id": int(run["id"]), "workflow_path": run["path"],
            "workflow_name": monitored[run["path"]]["name"], "event": run.get("event"),
            "created_at": run.get("created_at"), "updated_at": run.get("updated_at"),
            "conclusion": run.get("conclusion"), "html_url": run.get("html_url"),
            "head_sha": run.get("head_sha"), "state": summary["state"],
            "usable": summary["usable"], "investigate_recommended": summary["investigate_recommended"],
            "reason_codes": summary.get("reason_codes") or [], "detail": summary.get("detail") or {},
        })
    totals = Counter(row["state"] for row in rows)
    by_workflow = []
    for path, definition in monitored.items():
        subset = [row for row in rows if row["workflow_path"] == path]
        counts = Counter(row["state"] for row in subset)
        by_workflow.append({
            "workflow_path": path, "workflow_name": definition["name"], "run_count": len(subset),
            "state_counts": {state: counts[state] for state in STATES},
            "investigate_count": sum(row["investigate_recommended"] for row in subset),
            "latest_run_at": max((row["created_at"] for row in subset), default=None),
        })
    return {
        "schema": REPORT_SCHEMA, "repository": repository, "generated_at_utc": generated_at,
        "lookback_days": int(config["lookback_days"]), "automatic_events": sorted(allowed_events),
        "monitored_workflow_count": len(monitored), "run_count": len(rows),
        "state_counts": {state: totals[state] for state in STATES},
        "usable_run_count": totals["USABLE"],
        "non_usable_run_count": len(rows) - totals["USABLE"],
        "investigate_run_count": sum(row["investigate_recommended"] for row in rows),
        "by_workflow": by_workflow, "runs": rows,
        "semantics": config.get("semantics") or {},
    }


def report_markdown(report: dict[str, Any]) -> str:
    counts = report["state_counts"]
    lines = [
        "# FIE automatic workflow usability — rolling 14 days", "",
        f"Generated: `{report['generated_at_utc']}`", "",
        f"Runs: **{report['run_count']}**; usable: **{report['usable_run_count']}**; "
        f"investigate: **{report['investigate_run_count']}**.", "",
        "| State | Runs | Meaning |", "|---|---:|---|",
    ]
    for state in STATES:
        lines.append(f"| {state} | {counts[state]} | {report['semantics'].get(state, '')} |")
    lines += ["", "## Workflows", "", "| Workflow | Runs | Usable | No-op | Partial | Blocked | Missed | Infrastructure | Investigate |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in report["by_workflow"]:
        c = row["state_counts"]
        lines.append(f"| {row['workflow_name']} | {row['run_count']} | {c['USABLE']} | {c['NO_OP']} | {c['PARTIAL']} | {c['BLOCKED']} | {c['MISSED']} | {c['INFRASTRUCTURE']} | {row['investigate_count']} |")
    lines += ["", "## Runs worth investigating", "", "Expected no-ops are excluded from this table.", "", "| Time | Workflow | State | Reason | Run |", "|---|---|---|---|---|"]
    investigate = [row for row in report["runs"] if row["investigate_recommended"]]
    for row in investigate:
        reason = ", ".join(row["reason_codes"]) or "—"
        link = f"[#{row['run_id']}]({row['html_url']})" if row.get("html_url") else str(row["run_id"])
        lines.append(f"| {row.get('created_at') or '—'} | {row['workflow_name']} | {row['state']} | {reason} | {link} |")
    if not investigate:
        lines.append("| — | — | — | No runs currently require investigation | — |")
    lines += ["", "## Expected no-ops", "", "| Time | Workflow | Reason | Run |", "|---|---|---|---|"]
    no_ops = [row for row in report["runs"] if row["state"] == "NO_OP"]
    for row in no_ops:
        reason = ", ".join(row["reason_codes"]) or "—"
        link = f"[#{row['run_id']}]({row['html_url']})" if row.get("html_url") else str(row["run_id"])
        lines.append(f"| {row.get('created_at') or '—'} | {row['workflow_name']} | {reason} | {link} |")
    if not no_ops:
        lines.append("| — | — | No expected no-ops in this window | — |")
    lines += ["", "A successful GitHub conclusion is not counted as usable unless the producer emitted a valid usability summary. Legacy successes without that proof are BLOCKED, not silently promoted.", ""]
    return "\n".join(lines)


def collect_live(config: dict[str, Any], client: GitHub, generated_at: str) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    cutoff = datetime.fromisoformat(generated_at.replace("Z", "+00:00")) - timedelta(days=int(config["lookback_days"]))
    runs = client.runs(cutoff.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
    monitored = {row["path"] for row in config["workflows"]}
    events = set(config.get("automatic_events") or ["schedule"])
    summaries: dict[int, dict[str, Any]] = {}
    artifacts_by_run: dict[int, list[dict[str, Any]]] = {}
    for artifact in client.repository_artifacts():
        run_id = (artifact.get("workflow_run") or {}).get("id")
        if run_id is not None and artifact.get("name") == config["artifact_name"] and not artifact.get("expired"):
            artifacts_by_run.setdefault(int(run_id), []).append(artifact)
    for run in runs:
        if (run.get("path") not in monitored or run.get("event") not in events
                or run.get("status") != "completed"):
            continue
        artifacts = artifacts_by_run.get(int(run["id"]), [])
        if len(artifacts) > 1:
            summaries[int(run["id"])] = make_summary(
                workflow_path=run["path"], workflow_name=run.get("name") or run["path"], run_id=str(run["id"]),
                event=run.get("event") or "unknown", adapter="collector", job_status=run.get("conclusion") or "unknown",
                state="BLOCKED", reasons=["MULTIPLE_USABILITY_ARTIFACTS"], detail={"artifact_count": len(artifacts)},
                observed_at=run.get("updated_at") or run.get("created_at"),
            )
        elif artifacts:
            try:
                summaries[int(run["id"])] = validate_summary(client.artifact_summary(artifacts[0]), run, run["path"])
            except (ValueError, KeyError, TypeError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
                summaries[int(run["id"])] = make_summary(
                    workflow_path=run["path"], workflow_name=run.get("name") or run["path"], run_id=str(run["id"]),
                    event=run.get("event") or "unknown", adapter="collector", job_status=run.get("conclusion") or "unknown",
                    state="BLOCKED", reasons=["INVALID_USABILITY_ARTIFACT", type(exc).__name__], detail={},
                    observed_at=run.get("updated_at") or run.get("created_at"),
                )
        else:
            summaries[int(run["id"])] = fallback_summary(run, run["path"], client.jobs(int(run["id"])))
    return runs, summaries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser("emit")
    emit.add_argument("--workflow-path", required=True)
    emit.add_argument("--workflow-name", required=True)
    emit.add_argument("--run-id", required=True)
    emit.add_argument("--event", required=True)
    emit.add_argument("--adapter", required=True, choices=("current-refresh", "readiness-index", "waiver-index", "availability-index", "checkpoint-json", "commit", "policy-commit"))
    emit.add_argument("--job-status", required=True)
    emit.add_argument("--source-file", type=Path)
    emit.add_argument("--policy-allowed")
    emit.add_argument("--policy-reason")
    emit.add_argument("--initial-sha")
    emit.add_argument("--target-file", type=Path)
    emit.add_argument("--completed-file", type=Path)
    emit.add_argument("--output", type=Path, default=Path(".cache/fie-workflow-usability.json"))
    collect = sub.add_parser("collect")
    collect.add_argument("--config", type=Path, default=CONFIG_PATH)
    collect.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    collect.add_argument("--token", default=os.environ.get("GH_TOKEN"))
    collect.add_argument("--generated-at")
    collect.add_argument("--output-json", type=Path, required=True)
    collect.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "emit":
        state, reasons, detail = classify_emission(
            adapter=args.adapter, job_status=args.job_status, source_file=args.source_file,
            policy_allowed=args.policy_allowed, policy_reason=args.policy_reason,
            initial_sha=args.initial_sha, target_file=args.target_file, completed_file=args.completed_file,
        )
        summary = make_summary(
            workflow_path=args.workflow_path, workflow_name=args.workflow_name, run_id=args.run_id,
            event=args.event, adapter=args.adapter, job_status=args.job_status,
            state=state, reasons=reasons, detail=detail,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print("FIE_USABILITY_V1=" + json.dumps({"state": state, "reason_codes": summary["reason_codes"]}, separators=(",", ":")))
        return 0

    config = read_json(args.config)
    if config.get("schema") != "fie-workflow-usability-monitor-v1" or tuple(config.get("states") or []) != STATES:
        raise ValueError("Invalid workflow usability monitor config")
    generated_at = args.generated_at or datetime.now(UTC).isoformat()
    client = GitHub(args.repository, args.token)
    runs, summaries = collect_live(config, client, generated_at)
    report = build_report(config=config, runs=runs, summaries=summaries, generated_at=generated_at, repository=args.repository)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    args.output_markdown.write_text(report_markdown(report), encoding="utf-8", newline="\n")
    print(json.dumps({"runs": report["run_count"], "usable": report["usable_run_count"], "investigate": report["investigate_run_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify published weekly inputs before running either decision producer.

This is an operational guard, not a model/eligibility or prospective capture
owner. The schedule selects the target; stored snapshots never select it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from current_snapshot_storage import load_current_snapshot
from workflow_decision_context import default_season, resolve_target

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-weekly-pipeline-inputs-v1"
UPSTREAM = {"actions": "Refresh FIE Current Season", "waiver": "Build FIE Window 1C Weekly Actions"}


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("BLOCKED_PIPELINE_INPUT_NOT_OBJECT")
    return value


def stamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("BLOCKED_PIPELINE_TIMEZONE_MISSING")
    return parsed.astimezone(timezone.utc)


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("BLOCKED_PIPELINE_PATH_OUTSIDE_ROOT")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_trigger(event: dict, *, stage: str, repository: str) -> dict:
    run = event.get("workflow_run") or {}
    allowed_events = {"schedule", "workflow_dispatch"} if stage == "actions" else {"workflow_run", "workflow_dispatch"}
    if (not repository or run.get("name") != UPSTREAM[stage] or run.get("conclusion") != "success"
            or run.get("status") != "completed" or run.get("head_branch") != "main"
            or (run.get("head_repository") or {}).get("full_name") != repository
            or run.get("event") not in allowed_events):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_UNTRUSTED")
    if not re.fullmatch(r"[0-9a-f]{40}", str(run.get("head_sha") or "")) or not isinstance(run.get("id"), int):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_IDENTITY_MISSING")
    return {"name": run["name"], "run_id": str(run["id"]), "head_sha": run["head_sha"],
            "event": run["event"], "started_at": stamp(run["run_started_at"]).isoformat()}


def verify_inputs(root: Path, *, target: dict, as_of: datetime, league_id: str | None,
                  max_age_hours: float, minimum_generated_at: datetime | None = None) -> dict:
    if not math.isfinite(max_age_hours) or max_age_hours <= 0:
        raise ValueError("BLOCKED_PIPELINE_INVALID_MAX_AGE")
    registry_path = root / "data/research/leagues/registry.json"
    registry = read(registry_path)["leagues"]
    intended = sorted(lid for lid, entry in registry.items()
                      if entry.get("enabled") is True and entry.get("current_refresh", True))
    if league_id:
        if league_id not in intended:
            raise ValueError("BLOCKED_PIPELINE_LEAGUE_NOT_REFRESHABLE")
        intended = [league_id]
    if not intended:
        raise ValueError("BLOCKED_PIPELINE_NO_REFRESHABLE_LEAGUES")
    hashes = {"data/research/leagues/registry.json": digest(registry_path)}
    cache: dict = {}
    rows = []
    for lid in intended:
        row: dict[str, Any] = {"league_id": lid, "status": "READY", "reason_codes": []}
        def block(reason: str) -> None:
            row["status"] = "BLOCKED"
            if reason not in row["reason_codes"]:
                row["reason_codes"].append(reason)
        try:
            entry = registry[lid]
            profile_rel = str(entry["profile_path"])
            profile_path = safe_path(root, profile_rel)
            profile = read(profile_path)
            hashes[profile_rel] = digest(profile_path)
            prefix = f"data/research/leagues/{lid}"
            source = load_current_snapshot(root / prefix / "current/milestone5_current.json", root=root, cache=cache)
            source_metadata = {k: source.get(k) for k in ("season", "week", "generated_at", "profile_fingerprint", "scoring_signature")}
            row["source"] = source_metadata
            for deployment in ("", "dist/"):
                tree = root / deployment if deployment else root
                current_rel = deployment + prefix + "/current/milestone5_current.json"
                current_path = safe_path(root, current_rel)
                manifest = read(current_path)
                current = source if not deployment else load_current_snapshot(current_path, root=tree, cache=cache)
                if current.get("league_id") != lid:
                    block("BLOCKED_PIPELINE_CURRENT_LEAGUE_MISMATCH")
                if (current.get("season"), current.get("week")) != (target["season"], target["week"]):
                    block("BLOCKED_PIPELINE_CURRENT_WEEK_MISMATCH")
                generated = stamp(current["generated_at"])
                age = (as_of - generated).total_seconds() / 3600
                if age < 0 or age > max_age_hours:
                    block("BLOCKED_PIPELINE_CURRENT_FRESHNESS")
                if minimum_generated_at and generated < minimum_generated_at:
                    block("BLOCKED_PIPELINE_REFRESH_DID_NOT_PUBLISH_LEAGUE")
                if current.get("target_week_realised_stats_excluded") is not True:
                    block("BLOCKED_PIPELINE_REALIZED_STATS_GUARD")
                if current.get("profile_current_match") is not True:
                    block("BLOCKED_PIPELINE_PROFILE_DRIFT")
                app_rel = deployment + prefix + "/app/manifest.json"
                app = read(safe_path(root, app_rel))
                fingerprints = {entry.get("profile_fingerprint"), profile.get("profile_fingerprint"),
                                current.get("profile_fingerprint"), app.get("profile_fingerprint")}
                scoring = {entry.get("scoring_signature"), profile.get("scoring_signature"),
                           current.get("scoring_signature"), current.get("profile_scoring_signature"), app.get("scoring_signature")}
                if len(fingerprints) != 1 or None in fingerprints or "" in fingerprints:
                    block("BLOCKED_PIPELINE_PROFILE_BINDING")
                if len(scoring) != 1 or None in scoring or "" in scoring:
                    block("BLOCKED_PIPELINE_SCORING_BINDING")
                if deployment and any(current.get(k) != v for k, v in source_metadata.items()):
                    block("BLOCKED_PIPELINE_SOURCE_DIST_MISMATCH")
                refs = [current_rel, app_rel]
                for key in ("player_base", "scoring_overlay"):
                    if manifest.get("storage"):
                        refs.append(deployment + str(manifest["storage"][key]))
                core = app["core"]
                core_rel = deployment + str(core["path"])
                core_path = safe_path(root, core_rel)
                if digest(core_path) != core.get("sha256"):
                    block("BLOCKED_PIPELINE_APP_CORE_HASH")
                core_data = read(core_path)
                if str(core_data.get("league_id") or "") != lid:
                    block("BLOCKED_PIPELINE_APP_CORE_LEAGUE")
                if (core_data.get("profile_fingerprint") != profile.get("profile_fingerprint")
                        or core_data.get("scoring_signature") != profile.get("scoring_signature")):
                    block("BLOCKED_PIPELINE_APP_CORE_BINDING")
                if str((core_data.get("sleeper") or {}).get("league", {}).get("season") or "") != str(target["season"]):
                    block("BLOCKED_PIPELINE_APP_CORE_SEASON")
                refs.append(core_rel)
                for relative in refs:
                    if relative not in hashes:
                        hashes[relative] = digest(safe_path(root, relative))
        except (OSError, KeyError, TypeError, ValueError) as exc:
            block("BLOCKED_PIPELINE_CURRENT_INPUT_INVALID")
            row["error_type"] = type(exc).__name__
        rows.append(row)
    reasons = sorted({code for row in rows for code in row["reason_codes"]})
    return {"status": "BLOCKED" if reasons else "READY", "reason_codes": reasons,
            "league_ids": intended, "league_count": len(intended), "leagues": rows, "input_hashes": hashes}


def verify_prior(prior: dict, current: dict, *, upstream_run_id: str, as_of: datetime) -> None:
    if (prior.get("schema") != SCHEMA or prior.get("status") != "READY"
            or prior.get("stage") != "actions" or prior.get("run_id") != upstream_run_id):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_IDENTITY")
    if not re.fullmatch(r"[0-9a-f]{40}", str(prior.get("input_commit") or "")):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_COMMIT")
    if stamp(prior["verified_at"]) > as_of:
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_FUTURE")
    if prior.get("league_ids") != current.get("league_ids") or not prior.get("input_hashes"):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_SCOPE")
    if prior["input_hashes"] != current.get("input_hashes"):
        raise ValueError("BLOCKED_PIPELINE_UPSTREAM_INPUT_CHANGED")


def archive_inputs(root: Path, receipt: dict) -> Path:
    """First-write an operational input record, separate from forecast captures."""
    if receipt.get("status") != "READY" or receipt.get("stage") not in UPSTREAM:
        raise ValueError("BLOCKED_PIPELINE_ARCHIVE_NOT_READY")
    for field in ("run_id", "run_attempt"):
        if not re.fullmatch(r"[1-9][0-9]*", str(receipt.get(field) or "")):
            raise ValueError("BLOCKED_PIPELINE_ARCHIVE_RUN_IDENTITY")
    target = receipt["target"]
    path = root / f"data/operations/weekly-pipeline/{int(target['season'])}/week_{int(target['week']):02d}" / f"{receipt['stage']}-{receipt['run_id']}-{receipt['run_attempt']}.json"
    content = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as output:
            output.write(content)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != content:
            raise ValueError("BLOCKED_PIPELINE_ARCHIVE_IMMUTABLE_CONFLICT")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=tuple(UPSTREAM), required=True)
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch"))
    parser.add_argument("--event-path", type=Path)
    parser.add_argument("--upstream-inputs", type=Path)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--season", type=int)
    parser.add_argument("--week", type=int)
    parser.add_argument("--league-id")
    parser.add_argument("--as-of-utc")
    parser.add_argument("--schedule-path", type=Path)
    parser.add_argument("--max-current-age-hours", type=float, default=36)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path(".cache/fie-weekly-inputs.json"))
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()
    as_of = datetime.now(timezone.utc)
    result: dict[str, Any] = {"schema": SCHEMA, "stage": args.stage, "status": "BLOCKED",
                             "verified_at": as_of.isoformat(), "run_id": os.environ.get("GITHUB_RUN_ID"),
                             "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"), "reason_codes": []}
    try:
        as_of = stamp(args.as_of_utc) if args.as_of_utc else as_of
        result["verified_at"] = as_of.isoformat()
        if args.league_id and not re.fullmatch(r"[0-9]{6,32}", args.league_id):
            raise ValueError("BLOCKED_PIPELINE_INVALID_LEAGUE_ID")
        root = args.root.resolve()
        result["input_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                                                 capture_output=True, text=True).stdout.strip()
        upstream = None
        prior = None
        if args.event == "workflow_run":
            if not args.event_path:
                raise ValueError("BLOCKED_PIPELINE_EVENT_PAYLOAD_MISSING")
            upstream = verify_trigger(read(args.event_path), stage=args.stage, repository=args.repository)
            result["upstream"] = upstream
            subprocess.run(["git", "merge-base", "--is-ancestor", upstream["head_sha"], "HEAD"], cwd=root, check=True)
            if args.stage == "waiver":
                if not args.upstream_inputs:
                    raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_MISSING")
                prior = read(args.upstream_inputs)
                if (prior.get("schema") != SCHEMA or prior.get("stage") != "actions"
                        or prior.get("run_id") != upstream["run_id"]):
                    raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_IDENTITY")
                if prior.get("status") == "NO_DUE":
                    result.update(status="NO_DUE", reason_codes=["PIPELINE_UPSTREAM_NOT_DUE"])
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
                    if os.environ.get("GITHUB_OUTPUT"):
                        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                            print("ready=false", file=output)
                    print("PIPELINE_UPSTREAM_NOT_DUE")
                    return
                if prior.get("status") != "READY":
                    raise ValueError("BLOCKED_PIPELINE_UPSTREAM_NOT_READY")
                args.season, args.week = prior["target"]["season"], prior["target"]["week"]
                ids = prior["league_ids"]
                if not isinstance(ids, list) or not ids:
                    raise ValueError("BLOCKED_PIPELINE_UPSTREAM_RECEIPT_SCOPE")
                args.league_id = ids[0] if len(ids) == 1 else None
        elif args.event != "workflow_dispatch":
            raise ValueError("BLOCKED_PIPELINE_UNSUPPORTED_TRIGGER")
        # Preserve a bounded waiver-period cadence. Manual recovery may run any day.
        manual_chain = args.event == "workflow_dispatch" or (upstream and upstream["event"] == "workflow_dispatch") or (prior and prior.get("automatic") is False)
        result["automatic"] = not bool(manual_chain)
        if upstream and not manual_chain and as_of.astimezone(ZoneInfo("America/New_York")).weekday() not in (1, 2):
            result.update(status="NO_DUE", reason_codes=["PIPELINE_OUTSIDE_TUESDAY_WEDNESDAY"])
        else:
            target = resolve_target(season=args.season or default_season(as_of), week=args.week,
                                    as_of=as_of, schedule_path=args.schedule_path)
            result["target"] = target
            if prior:
                live_target = resolve_target(season=default_season(as_of), week=None, as_of=as_of, schedule_path=args.schedule_path)
                if (live_target["season"], live_target["week"]) != (target["season"], target["week"]):
                    raise ValueError("BLOCKED_PIPELINE_UPSTREAM_TARGET_EXPIRED")
            state = verify_inputs(root, target=target, as_of=as_of, league_id=args.league_id,
                                  max_age_hours=args.max_current_age_hours,
                                  minimum_generated_at=stamp(upstream["started_at"]) if upstream and args.stage == "actions" else None)
            result.update(state)
            if prior:
                verify_prior(prior, state, upstream_run_id=upstream["run_id"], as_of=as_of)
                result["source_refresh"] = prior.get("upstream")
            if args.archive and result["status"] == "READY":
                archive_inputs(root, result)
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        code = str(exc) if str(exc).startswith("BLOCKED_") else "BLOCKED_PIPELINE_CONTEXT_INVALID"
        result.update(status="BLOCKED", reason_codes=sorted(set(result["reason_codes"] + [code])), error_type=type(exc).__name__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "reason_codes": result["reason_codes"], "league_count": result.get("league_count")}, sort_keys=True))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            print("ready=" + str(result["status"] == "READY").lower(), file=output)
            for key in ("season", "week", "as_of_utc"):
                print(f"{key}={(result.get('target') or {}).get(key, '')}", file=output)
            scope = args.league_id if re.fullmatch(r"[0-9]{6,32}", args.league_id or "") else ""
            print(f"league_id={scope}", file=output)
    # Typed input blockers are successful observations; consumers check `ready`.


if __name__ == "__main__":
    main()

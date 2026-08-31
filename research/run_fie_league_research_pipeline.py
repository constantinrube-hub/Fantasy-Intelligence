#!/usr/bin/env python3
"""Unified one-league FIE research orchestrator.

This file deliberately orchestrates existing builders. It does not copy M1-M9,
V9.7, market, current, D/ST, kicker or Value Finder algorithms. Fail-closed
research results remain untouched and no promotion is performed.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from fie_research_pipeline_contract import (
    PIPELINE_SCHEMA, ROOT, STAGES, build_pipeline_fingerprint, current_path,
    derived_dir, league_root, league_row, load_json, load_profile, pipeline_dir,
    profile_fingerprint, profile_format, repo_relative, resolve_adp_key,
    roster_positions, roster_signature, scoring_signature, sha256_file,
    source_commit, stage_template, strategy_dir, team_count, utc_now,
    validate_status, write_json,
)


class StageFailure(RuntimeError):
    pass


def run(cmd: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    print("+", " ".join(shlex.quote(str(x)) for x in cmd), flush=True)
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=ROOT, text=True, check=check, env=merged)


def _stage_file(out: Path, index: int, name: str) -> Path:
    return out / "stages" / f"{index:02d}-{name}.json"


def _finish(stage: dict, status: str, *, reason: str | None = None, outputs: dict | None = None) -> dict:
    stage["status"] = validate_status(status)
    stage["finished_at"] = utc_now()
    if reason is not None:
        stage["reason"] = reason
    if outputs:
        stage["outputs"] = outputs
    return stage


def _hash_outputs(paths: list[Path]) -> dict:
    return {repo_relative(p): sha256_file(p) for p in paths if p.is_file()}


def validate_profile(league_id: str, row: dict, profile: dict) -> None:
    lid = str(profile.get("league_id") or (profile.get("league") or {}).get("league_id") or league_id)
    if lid != str(league_id):
        raise StageFailure(f"profile league ID mismatch: {lid} != {league_id}")
    if not roster_positions(profile):
        raise StageFailure("profile roster_positions empty")
    if team_count(profile) <= 0:
        raise StageFailure("profile team count invalid")
    if not scoring_signature(row, profile):
        raise StageFailure("scoring signature missing")
    declared_pf = str(profile.get("profile_fingerprint") or profile.get("fingerprint") or "")
    registry_pf = str(row.get("profile_fingerprint") or "")
    if declared_pf and registry_pf and declared_pf != registry_pf:
        raise StageFailure("profile fingerprint differs from registry")
    declared_sc = str(profile.get("scoring_signature") or "")
    registry_sc = str(row.get("scoring_signature") or "")
    if declared_sc and registry_sc and declared_sc != registry_sc:
        raise StageFailure("profile scoring signature differs from registry")


def ensure_m1_m9(league_id: str, season: int, fmt: str, *, force: bool = False) -> tuple[str, list[Path]]:
    root = league_root(league_id); dd = derived_dir(league_id)
    m9 = root / "milestone9.json"; board = root / "performance" / str(season) / "season_board.csv"; pw = dd / "player_week.csv.gz"
    existing = m9.is_file() and board.is_file() and pw.is_file()
    if existing and not force:
        return "reused_valid", [root / f"milestone{i}.json" for i in range(1, 10)] + [board, pw]
    run([sys.executable, "research/build_performance_research.py", "--league-id", league_id, "--format", fmt, "--season", str(season), "--rebuild-base", "--stop-after-m8"])
    run([sys.executable, "research/build_performance_research.py", "--league-id", league_id, "--format", fmt, "--season", str(season), "--resume-from-m9", "--capture-market", "--build-report"])
    if not (m9.is_file() and board.is_file() and pw.is_file()):
        raise StageFailure("M1-M9 builder completed without required M9/season/player_week artifacts")
    return "complete", [root / f"milestone{i}.json" for i in range(1, 10)] + [board, pw]


def ensure_current(league_id: str, season: int, *, no_refresh: bool) -> tuple[str, str]:
    root = league_root(league_id); cur = current_path(league_id)
    if cur.is_file():
        try:
            from current_snapshot_storage import load_current_snapshot
            x = load_current_snapshot(cur)
        except Exception as exc:
            if no_refresh:
                return "blocked_data", f"current snapshot hydration failed: {exc}"
            x = {}
        if x and int(x.get("season") or season) == int(season):
            return "reused_valid", str((x.get("v96_runtime") or {}).get("status") or x.get("status") or "current_available")
    if no_refresh:
        return "blocked_data", "current snapshot missing and --no-current-refresh set"
    args = [
        sys.executable, "research/build_current_snapshot.py",
        "--league-id", league_id,
        "--league-profile", str(root / "profile.json"),
        "--m4-bundle", str(root / "milestone4.json"),
        "--m5-bundle", str(root / "milestone5.json"),
        "--m6-bundle", str(root / "milestone6.json"),
        "--cache-dir", str(ROOT / ".cache/fie-current/leagues" / league_id),
        "--sleeper-archive", str(ROOT / "data/research/market/sleeper"),
        "--output", str(cur), "--season", str(season),
    ]
    run(args)
    if not cur.is_file():
        return "blocked_data", "current builder did not produce snapshot"
    # Preserve the current V9.6 governance contract: the unified preseason run does
    # not force runtime activation.  Existing V9.6 output is consumed if present.
    try:
        from current_snapshot_storage import load_current_snapshot
        x = load_current_snapshot(cur)
    except Exception:
        x = load_json(cur, {})
    return "complete", str((x.get("v96_runtime") or {}).get("status") or x.get("status") or "current_built")


def capture_market(season: int, league_id: str, *, disabled: bool) -> tuple[str, str]:
    root = ROOT / "data/research/market/sleeper" / str(season)
    existing = sorted(root.glob("season_market_*.jsonl.gz")) if root.is_dir() else []
    if disabled:
        return ("reused_valid", f"market capture disabled; existing snapshots={len(existing)}") if existing else ("blocked_data", "market capture disabled and no snapshot exists")
    cp = run([sys.executable, "research/capture_sleeper_season_market.py", "--season", str(season), "--derived-dir", str(derived_dir(league_id)), "--output-root", "data/research/market/sleeper"], check=False)
    existing = sorted(root.glob("season_market_*.jsonl.gz")) if root.is_dir() else []
    if cp.returncode == 0 and existing:
        return "complete", f"snapshots={len(existing)}"
    if existing:
        return "reused_valid", f"capture failed but immutable market snapshot exists; snapshots={len(existing)}"
    return "blocked_data", "market capture failed and no immutable snapshot exists"


def capture_availability() -> tuple[str, str]:
    cp = run([sys.executable, "research/capture_fie_availability.py", "--output-root", "data/research/availability/sleeper"], check=False)
    return ("complete", "availability capture complete") if cp.returncode == 0 else ("blocked_data", "availability capture unavailable; retained as non-blocking prospective evidence")


def build_strategy(league_id: str, season: int, adp_key: str) -> None:
    sdir = strategy_dir(league_id, season); sdir.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "research/build_fie_strategy_stack.py", "--league-root", str(league_root(league_id)), "--season", str(season), "--derived-dir", str(derived_dir(league_id)), "--adp-key", adp_key, "--output-dir", str(sdir)])
    run([sys.executable, "research/validate_fie_strategy_stack.py", str(sdir)])


def build_v974(league_id: str, season: int) -> None:
    sdir = strategy_dir(league_id, season); dd = derived_dir(league_id)
    cmd = [sys.executable, "research/preseason_projection_v4.py", "--player-week", str(dd / "player_week.csv.gz")]
    if (dd / "player_identity.csv.gz").is_file():
        cmd += ["--identity", str(dd / "player_identity.csv.gz")]
    cmd += ["--scoring-json", str(league_root(league_id) / "milestone1.json"), "--output-json", str(sdir / "preseason_v974_validation.json"), "--predictions-csv", str(sdir / "preseason_v974_predictions.csv"), "--calibration-csv", str(sdir / "preseason_v974_calibration.csv")]
    run(cmd); run([sys.executable, "research/validate_v974_preseason.py", str(sdir)])


def build_v975(league_id: str, season: int) -> tuple[str, str]:
    sdir = strategy_dir(league_id, season)
    if not (sdir / "preseason_v974_validation.json").is_file() or not (sdir / "preseason_v974_predictions.csv").is_file():
        return "not_applicable", "V9.7.4 prerequisite unavailable"
    run([sys.executable, "research/preseason_projection_v5.py", "--v974-json", str(sdir / "preseason_v974_validation.json"), "--v974-predictions", str(sdir / "preseason_v974_predictions.csv"), "--output-json", str(sdir / "preseason_v975_validation.json"), "--predictions-csv", str(sdir / "preseason_v975_predictions.csv"), "--params-csv", str(sdir / "preseason_v975_params.csv"), "--calibration-csv", str(sdir / "preseason_v975_calibration.csv")])
    run([sys.executable, "research/validate_v975_preseason.py", str(sdir)])
    x = load_json(sdir / "preseason_v975_validation.json", {})
    return "complete_research_only", str(((x.get("per_position") or {}).get("QB") or {}).get("status") or x.get("status") or "complete_research_only")


def derive_strategy_stage_statuses(league_id: str, season: int) -> dict[str, tuple[str, str]]:
    sdir = strategy_dir(league_id, season)
    v2 = load_json(sdir / "preseason_v2.json", {})
    stack = load_json(sdir / "strategy_stack.json", {})
    v973 = load_json(sdir / "preseason_v973_validation.json", {})
    phase = stack.get("phase_readiness") or {}
    pos_status = (phase.get("preseason_v2") or {})
    v971_reason = ", ".join(f"{p}:{v}" for p, v in sorted(pos_status.items())) or str(v2.get("status") or "unknown")
    shadow = phase.get("season_projection_v972") or {}
    return {
        "feature_evidence": ("complete_research_only", "existing strategy stack component evidence"),
        "production_shadow": ("complete_research_only", str(shadow.get("status") or "V9.7.2 shadow built")),
        "preseason_v971": ("complete_research_only", v971_reason),
        "preseason_v972": ("complete_research_only", f"shadow_applied={shadow.get('shadow_applied', 0)}; validated={shadow.get('validated_positions', [])}"),
        "preseason_v973": ("complete_research_only", f"status={v973.get('status')}; review={v973.get('football_model_promotion_review_positions', [])}"),
        "league_value": ("complete_research_only", str((stack.get("league_value_meta") or {}).get("status") or "existing strategy league value complete")),
    }


def _stage_manifest_skeleton(league_id: str, season: int, resolved_adp: str, fingerprint: str) -> dict:
    return {
        "schema": PIPELINE_SCHEMA, "schema_version": 1,
        "league_id": str(league_id), "season": int(season),
        "source_commit": source_commit(), "pipeline_fingerprint": fingerprint,
        "resolved_adp_key": resolved_adp, "started_at": utc_now(), "finished_at": None,
        "status": "running", "stages": [],
        "governance": {"automatic_promotion": False, "adp_in_football_model": False, "statistical_gates_lowered": False},
    }


def orchestrate(a: argparse.Namespace) -> int:
    row = league_row(a.league_id); profile = load_profile(a.league_id, row); validate_profile(a.league_id, row, profile)
    fmt = profile_format(profile, row)
    if a.format.upper() != "AUTO" and a.format.upper() != fmt:
        raise StageFailure(f"requested format {a.format} does not match canonical profile format {fmt}")
    resolved_adp, expected_adp = resolve_adp_key(profile, a.adp_key)
    out = Path(a.output_root) if a.output_root else pipeline_dir(a.league_id, a.season); out.mkdir(parents=True, exist_ok=True); (out / "stages").mkdir(exist_ok=True)
    fingerprint = build_pipeline_fingerprint(league_id=a.league_id, season=a.season, row=row, profile=profile, resolved_adp_key=resolved_adp)
    manifest = _stage_manifest_skeleton(a.league_id, a.season, resolved_adp, fingerprint)

    def record(name: str, status: str, reason: str, outputs: list[Path] | None = None, inputs: dict | None = None):
        idx = STAGES.index(name); st = stage_template(name); st["started_at"] = utc_now(); st["inputs"] = inputs or {}; _finish(st, status, reason=reason, outputs=_hash_outputs(outputs or [])); write_json(_stage_file(out, idx, name), st); manifest["stages"].append(st); return st

    record("profile", "complete", "canonical registry/profile validated", [league_root(a.league_id)/"profile.json"], {"format": fmt, "teams": team_count(profile), "profile_fingerprint": profile_fingerprint(row, profile), "scoring_signature": scoring_signature(row, profile), "roster_signature": roster_signature(profile), "resolved_adp_key": resolved_adp, "expected_adp_key": expected_adp})

    if a.mode == "report_only":
        if not (out/"readiness.json").is_file() or not (out/"final_player_board.csv").is_file():
            raise StageFailure("report_only requires existing readiness.json and final_player_board.csv")
        run([sys.executable,"research/build_fie_league_research_report.py","--league-id",a.league_id,"--season",str(a.season),"--output-dir",str(out)])
        record("report","complete_research_only","report rebuilt from existing canonical board",[out/"league-report.json",out/"league-report.md",out/"report-summary.json"])
    else:
        force = a.force_rebuild or "m1_m9" in a.force_stage or "historical_backbone" in a.force_stage
        mstatus, mouts = ensure_m1_m9(a.league_id,a.season,fmt,force=force)
        record("historical_backbone",mstatus,"existing M1 derived historical backbone" if mstatus=="reused_valid" else "historical backbone rebuilt",[derived_dir(a.league_id)/"player_week.csv.gz",derived_dir(a.league_id)/"player_identity.csv.gz"])
        record("m1_m9",mstatus,"existing M1-M9 builders reused without gate changes",mouts)

        cstatus, creason = ensure_current(a.league_id,a.season,no_refresh=a.no_current_refresh)
        record("current",cstatus,creason,[current_path(a.league_id)])
        # Controlled runtime is contextual only and is never forced by this preseason workflow.
        try:
            from current_snapshot_storage import load_current_snapshot
            cur=load_current_snapshot(current_path(a.league_id)) if current_path(a.league_id).is_file() else {}
        except Exception: cur=load_json(current_path(a.league_id),{})
        v96=str((cur.get("v96_runtime") or {}).get("status") or "not_present")
        record("controlled_runtime","reused_valid" if cur else "blocked_data",f"existing V9.6 context: {v96}",[current_path(a.league_id)])

        mkt_status,mkt_reason=capture_market(a.season,a.league_id,disabled=a.no_market_capture); record("market",mkt_status,mkt_reason)
        av_status,av_reason=capture_availability(); record("availability",av_status,av_reason)

        build_strategy(a.league_id,a.season,resolved_adp)
        for name,(status,reason) in derive_strategy_stage_statuses(a.league_id,a.season).items():
            record(name,status,reason,[strategy_dir(a.league_id,a.season)/"strategy_stack.json"])

        build_v974(a.league_id,a.season)
        v974=load_json(strategy_dir(a.league_id,a.season)/"preseason_v974_validation.json",{})
        record("preseason_v974","complete_research_only",f"review={v974.get('football_model_promotion_review_positions', [])}; production_activation_allowed={v974.get('production_activation_allowed')}",[strategy_dir(a.league_id,a.season)/"preseason_v974_validation.json",strategy_dir(a.league_id,a.season)/"preseason_v974_predictions.csv"])
        v975_status,v975_reason=build_v975(a.league_id,a.season); record("preseason_v975",v975_status,v975_reason,[strategy_dir(a.league_id,a.season)/"preseason_v975_validation.json",strategy_dir(a.league_id,a.season)/"preseason_v975_predictions.csv"])

        # Refresh fingerprint after historical assets exist/rebuild, so output binds exact inputs.
        fingerprint=build_pipeline_fingerprint(league_id=a.league_id,season=a.season,row=row,profile=profile,resolved_adp_key=resolved_adp); manifest["pipeline_fingerprint"]=fingerprint
        run([sys.executable,"research/resolve_fie_position_models.py","--league-id",a.league_id,"--season",str(a.season),"--adp-key",resolved_adp,"--pipeline-fingerprint",fingerprint,"--output",str(out/"readiness.json")])
        record("model_resolver","complete_research_only","per-position selection resolved; no automatic promotion",[out/"readiness.json"])
        run([sys.executable,"research/build_fie_final_league_board.py","--league-id",a.league_id,"--season",str(a.season),"--readiness",str(out/"readiness.json"),"--output-dir",str(out)])
        record("final_board","complete_research_only","canonical M9 league-value board plus challenger evidence",[out/"final_player_board.csv",out/"rankings.json",out/"board-meta.json"])
        run([sys.executable,"research/build_fie_league_research_report.py","--league-id",a.league_id,"--season",str(a.season),"--output-dir",str(out)])
        record("report","complete_research_only","deterministic report generated from canonical final board",[out/"league-report.json",out/"league-report.md",out/"report-summary.json"])

        for validator in ("research/validate_fie_research_pipeline.py","research/validate_fie_league_report.py"):
            run([sys.executable,validator,"--league-id",a.league_id,"--season",str(a.season),"--output-dir",str(out)])

    manifest["finished_at"]=utc_now(); manifest["status"]="complete_research_only"; manifest["source_commit"]=source_commit(); write_json(out/"stage-manifest.json",manifest)
    print(json.dumps({"schema":PIPELINE_SCHEMA,"league_id":a.league_id,"season":a.season,"status":manifest["status"],"pipeline_fingerprint":manifest["pipeline_fingerprint"],"automatic_promotion":False},indent=2))
    return 0


def parse_args(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--league-id",required=True); p.add_argument("--season",type=int,required=True); p.add_argument("--format",default="AUTO"); p.add_argument("--adp-key",default="AUTO"); p.add_argument("--mode",choices=["full","research_only","report_only"],default="full"); p.add_argument("--force-stage",action="append",default=[]); p.add_argument("--force-rebuild",action="store_true"); p.add_argument("--no-current-refresh",action="store_true"); p.add_argument("--no-market-capture",action="store_true"); p.add_argument("--output-root",default=""); return p.parse_args(argv)


def main(argv=None) -> int:
    a=parse_args(argv)
    try: return orchestrate(a)
    except (StageFailure, subprocess.CalledProcessError, ValueError, RuntimeError) as exc:
        print(f"FIE unified pipeline failed closed: {exc}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())

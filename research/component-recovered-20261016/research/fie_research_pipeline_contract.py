#!/usr/bin/env python3
"""Canonical contracts for the FIE unified per-league research pipeline.

The module is intentionally stdlib-only.  It centralises orchestration paths,
statuses, league identity/fingerprint checks and deterministic artifact helpers;
it does not implement a football model, market model, replacement model or rank
calculation.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SCHEMA = "fie-research-pipeline-v1"
READINESS_SCHEMA = "fie-research-readiness-v1"
FINAL_BOARD_SCHEMA = "fie-final-league-board-v1"
REPORT_SCHEMA = "fie-league-research-report-v1"
PORTFOLIO_SCHEMA = "fie-portfolio-research-report-v1"
PILOT_LEAGUE_ID = "1391803939736801280"

STAGES = (
    "profile",
    "historical_backbone",
    "m1_m9",
    "current",
    "feature_evidence",
    "production_shadow",
    "controlled_runtime",
    "preseason_v971",
    "preseason_v972",
    "preseason_v973",
    "preseason_v974",
    "preseason_v975",
    "market",
    "availability",
    "league_value",
    "model_resolver",
    "final_board",
    "report",
    "app_publish",
)

STAGE_STATUSES = {
    "complete",
    "complete_research_only",
    "reused_valid",
    "blocked_data",
    "blocked_scoring",
    "blocked_statistics",
    "blocked_profile",
    "not_applicable",
    "failed_integrity",
}

MODEL_DECISIONS = {
    "PRODUCTION_EXISTING",
    "PROMOTION_REVIEW_READY",
    "DIAGNOSTIC_ONLY",
    "BLOCKED_DATA",
    "BLOCKED_SCORING",
    "BLOCKED_STATISTICS",
    "BLOCKED_PROFILE",
    "NOT_APPLICABLE",
}

OFFENSE = ("QB", "RB", "WR", "TE")
SPECIAL = ("DST", "K")
REPORT_POSITIONS = OFFENSE + SPECIAL
IDP_CANONICAL = ("EDGE", "IDL", "LB", "CB", "S")

PIPELINE_FILES = {
    "readiness": "readiness.json",
    "board_csv": "final_player_board.csv",
    "rankings": "rankings.json",
    "report_json": "league-report.json",
    "report_md": "league-report.md",
    "report_summary": "report-summary.json",
    "stage_manifest": "stage-manifest.json",
    "matrix_status": "matrix-job-status.json",
}

# Exact, repository-owned provenance for research artifacts that predate the
# unified runner.  These are evidence/runtime bundles, not football-model
# promotion decisions.  A stage may only claim a successful status after the
# listed validator(s) accept its primary artifact.
RESEARCH_STAGE_CONTRACTS = {
    "feature_evidence": {
        "artifact_type": "feature_evidence_bundle",
        "producer": "research/fie_feature_evidence_hardening.py",
        "producer_dependencies": ["research/fie_feature_evidence.py"],
        "validator": [
            "research/validate_feature_evidence_bundle.py",
            "research/validate_feature_evidence_hardening.py",
        ],
        "schema": "fie-feature-evidence-v1",
        "output_dir": "evidence",
        "primary_output": "feature_evidence.json",
    },
    "production_shadow": {
        "artifact_type": "production_shadow_bundle",
        "producer": "research/fie_production_shadow.py",
        "producer_dependencies": [],
        "validator": ["research/validate_production_shadow.py"],
        "schema": "fie-production-shadow-v1",
        "output_dir": "shadow",
        "primary_output": "production_shadow.json",
    },
    "controlled_runtime": {
        "artifact_type": "controlled_runtime_bundle",
        "producer": "research/build_v96_runtime_bundle.py",
        "producer_dependencies": [],
        "validator": ["research/validate_v96_runtime_bundle.py"],
        "schema": "fie-v96-runtime-v1",
        "output_dir": "runtime",
        "primary_output": "v96_runtime.json",
    },
}


def research_stage_contract(name: str) -> dict:
    """Return a defensive copy of one typed research-stage contract."""
    if name not in RESEARCH_STAGE_CONTRACTS:
        raise ValueError(f"no typed research-stage contract for {name}")
    contract = dict(RESEARCH_STAGE_CONTRACTS[name])
    contract["producer_dependencies"] = list(contract["producer_dependencies"])
    contract["validator"] = list(contract["validator"])
    return contract


def research_stage_primary_output(league_id: str, season: int | str, name: str) -> Path:
    contract = research_stage_contract(name)
    return league_root(league_id) / "performance" / str(season) / contract["output_dir"] / contract["primary_output"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.is_file():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def json_safe(obj: Any) -> Any:
    """Normalize serialization-only missing/non-finite scalars to JSON null.

    This is an artifact-boundary conversion only. It does not impute model inputs,
    change rankings/projections, weaken statistical gates, or reinterpret missing
    evidence as zero.
    """
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None

    # numpy/pandas scalar types expose item(); keep this module dependency-free.
    item = getattr(obj, "item", None)
    if callable(item):
        try:
            scalar = item()
        except Exception:
            scalar = obj
        if scalar is not obj:
            return json_safe(scalar)
    return obj


def canonical_bytes(obj: Any) -> bytes:
    safe = json_safe(obj)
    return (json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def write_json(path: str | Path, obj: Any, *, pretty: bool = True) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    safe = json_safe(obj)
    if pretty:
        text = json.dumps(safe, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
        p.write_text(text, encoding="utf-8")
    else:
        p.write_bytes(canonical_bytes(safe))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_content_sha256(path: str | Path) -> str | None:
    """Hash JSON by canonical content; hash other artifacts by exact bytes.

    Canonical JSON avoids operating-system line-ending drift while retaining an
    exact semantic content identity. Invalid JSON still fails closed.
    """
    p = Path(path)
    if not p.is_file():
        return None
    if p.suffix.lower() == ".json":
        return sha256_bytes(canonical_bytes(load_json(p)))
    return sha256_file(p)


def short_hash(obj: Any, n: int = 16) -> str:
    return sha256_bytes(canonical_bytes(obj))[:n]


def registry_path() -> Path:
    return ROOT / "data/research/leagues/registry.json"


def registry_rows(path: str | Path | None = None) -> dict[str, dict]:
    reg = load_json(path or registry_path(), {})
    rows = reg.get("leagues") if isinstance(reg, dict) else None
    if isinstance(rows, dict):
        return {str(k): dict(v or {}) for k, v in rows.items()}
    if isinstance(reg, list):
        out: dict[str, dict] = {}
        for row in reg:
            if not isinstance(row, dict):
                continue
            lid = str(row.get("league_id") or "").strip()
            if lid:
                out[lid] = dict(row)
        return out
    raise ValueError("registry.json must expose a leagues object or list")


def enabled_league_rows(path: str | Path | None = None) -> dict[str, dict]:
    return {lid: row for lid, row in registry_rows(path).items() if row.get("enabled", True)}


def league_row(league_id: str, *, require_enabled: bool = True) -> dict:
    lid = str(league_id)
    rows = registry_rows()
    if lid not in rows:
        raise ValueError(f"league {lid} not present in registry")
    row = rows[lid]
    if require_enabled and not row.get("enabled", True):
        raise ValueError(f"league {lid} is disabled in registry")
    return row


def league_root(league_id: str) -> Path:
    return ROOT / "data/research/leagues" / str(league_id)


def profile_path(league_id: str, row: dict | None = None) -> Path:
    row = row or league_row(league_id, require_enabled=False)
    raw = row.get("profile_path")
    p = Path(raw) if raw else league_root(league_id) / "profile.json"
    if not p.is_absolute():
        p = ROOT / p
    return p


def load_profile(league_id: str, row: dict | None = None) -> dict:
    p = profile_path(league_id, row)
    x = load_json(p, {})
    if not x:
        raise ValueError(f"profile missing/invalid for league {league_id}: {p}")
    return x


def scoring_settings(profile: dict) -> dict:
    scoring = profile.get("scoring_settings")
    if isinstance(scoring, dict):
        return scoring
    scoring = profile.get("scoring")
    if isinstance(scoring, dict):
        if isinstance(scoring.get("settings"), dict):
            return scoring["settings"]
        return scoring
    league = profile.get("league") or {}
    return league.get("scoring_settings") or {}


def roster_positions(profile: dict) -> list[str]:
    raw = profile.get("roster_positions") or (profile.get("league") or {}).get("roster_positions") or []
    return [str(x).upper() for x in raw]


def team_count(profile: dict) -> int:
    for raw in (profile.get("total_rosters"), (profile.get("settings") or {}).get("num_teams"), ((profile.get("league") or {}).get("settings") or {}).get("num_teams")):
        try:
            if int(raw) > 0:
                return int(raw)
        except (TypeError, ValueError):
            pass
    return 0


def profile_format(profile: dict, row: dict | None = None) -> str:
    return str(profile.get("format") or (profile.get("league") or {}).get("format") or (row or {}).get("research_format") or (row or {}).get("format") or "").upper()


def has_superflex(profile: dict) -> bool:
    slots = roster_positions(profile)
    return any(s in {"SUPER_FLEX", "SUPERFLEX", "SF"} for s in slots) or sum(s == "QB" for s in slots) >= 2


def roster_signature(profile: dict) -> str:
    payload = {
        "teams": team_count(profile),
        "format": profile_format(profile),
        "roster_positions": roster_positions(profile),
        "reserve_slots": (profile.get("settings") or {}).get("reserve_slots"),
        "taxi_slots": (profile.get("settings") or {}).get("taxi_slots"),
    }
    return short_hash(payload)


def profile_fingerprint(row: dict, profile: dict) -> str:
    return str(row.get("profile_fingerprint") or profile.get("profile_fingerprint") or profile.get("fingerprint") or sha256_file(profile_path(str(row.get("league_id") or profile.get("league_id") or ""), row)) or "")


def scoring_signature(row: dict, profile: dict) -> str:
    return str(row.get("scoring_signature") or profile.get("scoring_signature") or short_hash(scoring_settings(profile)))


def resolve_adp_key(profile: dict, requested: str = "AUTO") -> tuple[str, str]:
    """Delegate ADP-market resolution to the existing strategy stack.

    Import is delayed so this contract stays stdlib-only for fixture/integrity tests.
    There is deliberately no second ADP mapping here.
    """
    try:
        from build_fie_strategy_stack import resolve_adp_key as existing_resolver  # type: ignore
    except ImportError:
        try:
            from research.build_fie_strategy_stack import resolve_adp_key as existing_resolver  # type: ignore
        except ImportError as exc:
            raise RuntimeError("existing build_fie_strategy_stack.resolve_adp_key is required") from exc
    return existing_resolver(profile, requested)


def pipeline_dir(league_id: str, season: int | str, output_root: str | Path | None = None) -> Path:
    if output_root:
        return Path(output_root)
    return league_root(league_id) / "performance" / str(season) / "research_pipeline"


def strategy_dir(league_id: str, season: int | str) -> Path:
    return league_root(league_id) / "performance" / str(season) / "strategy"


def derived_dir(league_id: str) -> Path:
    return ROOT / ".cache/fie-research/leagues" / str(league_id) / "derived"


def current_path(league_id: str) -> Path:
    return league_root(league_id) / "current/milestone5_current.json"


def source_commit() -> str | None:
    env = str(os.environ.get("GITHUB_SHA") or "").strip()
    if env:
        return env
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip() or None
    except Exception:
        return None


def research_code_hash() -> str:
    paths = [
        "research/build_performance_research.py",
        "research/build_fie_strategy_stack.py",
        "research/fie_strategy_stack.py",
        "research/preseason_projection.py",
        "research/preseason_projection_v2.py",
        "research/preseason_projection_v3.py",
        "research/preseason_projection_v4.py",
        "research/preseason_projection_v5.py",
        "research/fie_research_pipeline_contract.py",
        "research/run_fie_league_research_pipeline.py",
        "research/resolve_fie_position_models.py",
        "research/build_fie_final_league_board.py",
        "research/build_fie_league_research_report.py",
    ]
    payload = []
    for rel in paths:
        p = ROOT / rel
        payload.append((rel, sha256_file(p)))
    return short_hash(payload, 32)


def historical_data_hash(league_id: str, season: int | str) -> str:
    root = league_root(league_id)
    dd = derived_dir(league_id)
    payload = {
        "m1": sha256_file(root / "milestone1.json"),
        "m9": sha256_file(root / "milestone9.json"),
        "player_week": sha256_file(dd / "player_week.csv.gz"),
        "identity": sha256_file(dd / "player_identity.csv.gz"),
        "season_board": sha256_file(root / "performance" / str(season) / "season_board.csv"),
    }
    return short_hash(payload, 32)


def build_pipeline_fingerprint(*, league_id: str, season: int | str, row: dict, profile: dict, resolved_adp_key: str) -> str:
    payload = {
        "league_id": str(league_id),
        "season": int(season),
        "profile_fingerprint": profile_fingerprint(row, profile),
        "scoring_signature": scoring_signature(row, profile),
        "roster_signature": roster_signature(profile),
        "format": profile_format(profile, row),
        "adp_key": resolved_adp_key,
        "research_code_hash": research_code_hash(),
        "historical_data_hash": historical_data_hash(league_id, season),
    }
    return sha256_bytes(canonical_bytes(payload))


def strip_volatile(obj: Any) -> Any:
    """Canonicalize structural output for determinism comparisons."""
    volatile = {"generated_at", "started_at", "finished_at", "latest_market_as_of", "source_commit"}
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in sorted(obj.items()) if k not in volatile}
    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]
    return obj


def structural_hash(obj: Any) -> str:
    return sha256_bytes(canonical_bytes(strip_volatile(obj)))


def applicable_positions(profile: dict) -> list[str]:
    slots = roster_positions(profile)
    out: list[str] = []
    roster_aliases = {
        "DEF": "DST", "DST": "DST", "D/ST": "DST",
        "DL": "IDL", "DE": "EDGE", "DT": "IDL", "DB": "S",
    }
    sf = any(slot in {"SUPER_FLEX", "SUPERFLEX", "SF", "Q/W/R/T", "OP"} for slot in slots)
    flex = any(slot in {"FLEX", "WRT", "W/R/T", "RB/WR/TE", "REC_FLEX", "WRRB_FLEX"} for slot in slots)
    if "QB" in slots or sf:
        out.append("QB")
    for pos in ("RB", "WR", "TE"):
        if pos in slots or flex or sf:
            out.append(pos)
    for slot in slots:
        if slot == "DB":
            for p in ("CB", "S"):
                if p not in out: out.append(p)
            continue
        if slot == "DL":
            for p in ("EDGE", "IDL"):
                if p not in out: out.append(p)
            continue
        p = roster_aliases.get(slot, slot)
        if p in {"DST", "K", *IDP_CANONICAL} and p not in out:
            out.append(p)
    return out


def stage_template(name: str) -> dict:
    if name not in STAGES:
        raise ValueError(f"unknown stage {name}")
    return {"name": name, "status": "blocked_data", "started_at": None, "finished_at": None, "inputs": {}, "outputs": {}, "reason": "not_run"}


def validate_status(status: str) -> str:
    if status not in STAGE_STATUSES:
        raise ValueError(f"invalid pipeline stage status {status}")
    return status


def repo_relative(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return p.as_posix()

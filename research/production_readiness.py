#!/usr/bin/env python3
"""Audit whether the multi-league FIE repository is ready for production refreshes.

This is intentionally a repository audit rather than a model validator.  It checks
that registered League IDs are isolated, expected artifacts exist, profile identity
is consistent, and immutable Sleeper market snapshots still match their manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
REGISTRY = RESEARCH / "leagues" / "registry.json"
REQUIRED = ["profile.json", "milestone1.json", "milestone2.json", "milestone3.json", "milestone4.json", "milestone5.json", "milestone6.json"]


def load(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verified_market_meta(row: dict, sidecar: dict) -> tuple[bool, str]:
    meta = sidecar or row or {}
    if not meta.get("pregame_eligible"):
        return True, "not_eligible"
    try: ver = int(meta.get("capture_policy_version") or 0)
    except Exception: ver = 0
    if ver < 2:
        return False, "eligible benchmark lacks capture-policy-v2 timing evidence"
    if str(meta.get("season_type") or "").lower() != "regular":
        return False, "eligible benchmark is not marked regular season"
    try:
        h = float(meta.get("hours_before_kickoff")); w = float(meta.get("capture_window_hours"))
    except Exception:
        return False, "eligible benchmark lacks auditable kickoff-window fields"
    if not (0 < h <= w):
        return False, f"eligible benchmark captured outside window ({h:.2f}h, max {w:.2f}h)"
    if not meta.get("first_kickoff_utc"):
        return False, "eligible benchmark lacks first_kickoff_utc"
    return True, "verified"


def audit_market(issues: list[str], warnings: list[str]) -> int:
    root = RESEARCH / "market" / "sleeper"
    manifest = load(root / "manifest.json", {}) or {}
    entries = manifest.get("snapshots") or {}
    for key, row in entries.items():
        path = Path(row.get("path") or "")
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            issues.append(f"market {key}: manifest path missing: {path}")
            continue
        expected = str(row.get("sha256") or "")
        got = sha(path)
        if expected and got != expected:
            issues.append(f"market {key}: SHA-256 mismatch, immutable archive changed")
        sidecar_path = path.with_suffix(path.suffix + ".meta.json")
        sidecar = load(sidecar_path, {}) or {}
        ok_timing, timing_reason = verified_market_meta(row, sidecar)
        if not ok_timing:
            issues.append(f"market {key}: {timing_reason}; quarantine/repair before benchmarking")
        elif not row.get("pregame_eligible"):
            warnings.append(f"market {key}: preserved but not eligible as a pregame benchmark")
    # Legacy snapshots may predate the manifest.  They are not lost, but should be
    # registered on the next build so integrity can be checked centrally.
    snaps = list(root.glob("*/week_*.jsonl.gz"))
    if snaps and not entries:
        warnings.append(f"market archive has {len(snaps)} snapshot(s) but no manifest yet")
    return len(snaps)


def audit_league(lid: str, row: dict, issues: list[str], warnings: list[str]) -> dict:
    if not re.fullmatch(r"[0-9]{6,32}", lid):
        issues.append(f"registry contains invalid League ID: {lid!r}")
        return {"league_id": lid, "ready": False}
    root = RESEARCH / "leagues" / lid
    missing = [x for x in REQUIRED if not (root / x).exists()]
    if missing:
        issues.append(f"league {lid}: missing {', '.join(missing)}")
    profile = load(root / "profile.json", {}) or {}
    fp = str(profile.get("profile_fingerprint") or "")
    sig = str(profile.get("scoring_signature") or "")
    if str(profile.get("league_id") or "") != lid:
        issues.append(f"league {lid}: profile League ID mismatch")
    if row.get("profile_fingerprint") and str(row.get("profile_fingerprint")) != fp:
        issues.append(f"league {lid}: registry/profile fingerprint mismatch")
    for n in range(1, 7):
        p = root / f"milestone{n}.json"
        if not p.exists():
            continue
        b = load(p, {}) or {}
        if str(b.get("league_id") or "") != lid:
            issues.append(f"league {lid}: M{n} namespace mismatch")
        if fp and str(b.get("profile_fingerprint") or "") != fp:
            issues.append(f"league {lid}: M{n} profile fingerprint mismatch")
        bsig = str(b.get("profile_scoring_signature") or b.get("scoring_signature") or "")
        if sig and bsig and bsig != sig:
            issues.append(f"league {lid}: M{n} scoring signature mismatch")
    current = root / "current" / "milestone5_current.json"
    gov = root / "governance" / "active_release.json"
    if row.get("current_refresh", True) and not current.exists():
        warnings.append(f"league {lid}: no namespaced current snapshot yet")
    if current.exists():
        cur = load(current, {}) or {}
        st = str(cur.get("season_type") or "").lower()
        if not st:
            warnings.append(f"league {lid}: current snapshot predates season-type semantics; refresh current snapshot")
        elif st in {"pre", "preseason"} and int(cur.get("week") or 0) != 1:
            issues.append(f"league {lid}: preseason snapshot is labeled as regular Week {cur.get('week')}; rebuild current snapshot")
    if not gov.exists():
        warnings.append(f"league {lid}: no namespaced governance release yet")

    m5 = load(root / "milestone5.json", {}) or {}
    rev = int(m5.get("contract_revision") or 1)
    wspec = m5.get("waiver_integration", {}).get("model_specs", {}) or {}
    required_folds = int(wspec.get("required_promotion_folds") or 4)
    max_folds = int(wspec.get("max_valid_folds") or max([int(x.get("folds") or 0) for x in m5.get("waiver_integration", {}).get("aggregate", [])] or [0]))
    if max_folds < required_folds:
        msg = f"league {lid}: waiver validation has only {max_folds} fold(s) but promotion requires {required_folds}"
        if rev >= 3:
            issues.append(msg)
        else:
            warnings.append(msg + "; legacy M5 should be rebuilt with the full-history waiver panel")
    if rev >= 4:
        aggregates = m5.get("waiver_integration", {}).get("aggregate", []) or []
        by_pos = {str(r.get("position")): r for r in aggregates if r.get("position")}
        gated = set(m5.get("activation", {}).get("decision_gates", {}).get("waiver_policy_positions", []) or [])
        for pos in sorted(gated):
            r = by_pos.get(pos) or {}
            if r.get("forecast_status") != "validated_candidate" or r.get("decision_ranking_status") != "validated_candidate":
                issues.append(f"league {lid}: waiver gate exposes {pos} without both forecast and decision-ranking validation")
        for pos, r in by_pos.items():
            if r.get("status") == "validated_candidate" and pos not in gated:
                issues.append(f"league {lid}: validated waiver aggregate {pos} missing from activation gate")
    return {
        "league_id": lid,
        "format": profile.get("format") or row.get("format"),
        "ready": not missing and bool(fp) and bool(sig),
        "current": current.exists(),
        "governance": gov.exists(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit non-zero for an empty registry or any warning")
    ap.add_argument("--league-id", help="audit one registered League ID")
    ap.add_argument("--json-output")
    a = ap.parse_args()
    reg = load(REGISTRY, {}) or {}
    leagues = reg.get("leagues") or {}
    if a.league_id:
        leagues = {a.league_id: leagues.get(a.league_id, {})} if a.league_id in leagues else {}
    issues, warnings = [], []
    if not leagues:
        warnings.append("no League IDs are registered; run the one-time legacy migration/add-league workflow before scheduled refreshes")
    rows = [audit_league(str(lid), row or {}, issues, warnings) for lid, row in sorted(leagues.items())]
    market_count = audit_market(issues, warnings)
    result = {
        "status": "FAIL" if issues else ("WARN" if warnings else "READY"),
        "registered_leagues": rows,
        "market_snapshots": market_count,
        "issues": issues,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    if a.json_output:
        Path(a.json_output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if issues or (a.strict and warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

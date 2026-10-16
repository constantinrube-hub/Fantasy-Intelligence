#!/usr/bin/env python3
"""Canonical non-committing League-ID M1-M6 builder used by bulk onboarding.

This script deliberately performs no git operations. Parallel jobs can therefore
build isolated League-ID artifacts safely, upload them, and let one merge job
commit once.

Resilience contract:
- Existing profile.json is preserved until a fresh Sleeper profile is written.
- Sleeper profile refresh is retried with exponential backoff.
- If Sleeper is temporarily unavailable, a recent internally-consistent profile
  may be reused for at most seven days, with exact league/format/portfolio checks.
- M1 replays the scoring embedded in that profile instead of making a second
  network call to Sleeper.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from league_profile import (
    SCHEMA_VERSION,
    scoring_signature,
    sha256_json,
    structural_contract,
    update_registry,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FALLBACK_MAX_AGE_DAYS = 7.0


def run(*parts: str) -> None:
    cmd = [str(x) for x in parts]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def run_with_retries(*parts: str, attempts: int = 4, base_delay: float = 2.0) -> None:
    """Retry a short network-sensitive subprocess without masking its final error."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    cmd = [str(x) for x in parts]
    last: Optional[subprocess.CalledProcessError] = None
    for attempt in range(1, attempts + 1):
        print("+", " ".join(cmd), flush=True)
        try:
            subprocess.run(cmd, cwd=ROOT, check=True)
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            if attempt >= attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            print(
                f"WARNING: transient command failure attempt {attempt}/{attempts}; "
                f"retrying in {delay:.0f}s: {' '.join(cmd)}",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(delay)
    assert last is not None
    raise last


def season_windows() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    last_complete = now.year - 2 if now.month == 1 else now.year - 1
    return f"2019-{last_complete}", f"2016-{last_complete}"


def _load_json(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return obj


def _portfolio_entry(path: Path, league_id: str) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        cfg = _load_json(path)
    except Exception:
        return None
    leagues = cfg.get("leagues") or []
    if not isinstance(leagues, list):
        return None
    for entry in leagues:
        if isinstance(entry, dict) and str(entry.get("league_id") or "") == league_id:
            return entry
    return None


def _parse_utc_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def reusable_profile(
    path: Path,
    league_id: str,
    requested_format: str,
    portfolio_config: Path,
    *,
    now: Optional[datetime] = None,
    max_age_days: float = PROFILE_FALLBACK_MAX_AGE_DAYS,
) -> tuple[bool, str, Optional[Dict[str, Any]]]:
    """Fail-closed validation for a cached league profile used during API outage."""
    if not path.exists():
        return False, "profile_missing", None
    try:
        profile = _load_json(path)
    except Exception as exc:
        return False, f"profile_unreadable:{type(exc).__name__}", None

    if int(profile.get("schema_version") or 0) != int(SCHEMA_VERSION):
        return False, "schema_mismatch", profile
    if str(profile.get("league_id") or "") != str(league_id):
        return False, "league_id_mismatch", profile

    entry = _portfolio_entry(portfolio_config, str(league_id))
    resolved_format = str(requested_format or "AUTO").upper()
    if resolved_format == "AUTO" and entry and entry.get("format"):
        resolved_format = str(entry.get("format")).upper()
    if resolved_format != "AUTO" and str(profile.get("format") or "").upper() != resolved_format:
        return False, "format_mismatch", profile

    expected_constraints = list((entry or {}).get("research_constraints") or [])
    actual_constraints = list(profile.get("research_constraints") or [])
    if actual_constraints != expected_constraints:
        return False, "portfolio_constraints_mismatch", profile

    scoring = profile.get("scoring_settings") or {}
    if profile.get("scoring_signature") != scoring_signature(scoring):
        return False, "scoring_signature_mismatch", profile

    contract = structural_contract(
        str(league_id),
        str(profile.get("format") or ""),
        scoring,
        profile.get("roster_positions") or [],
        profile.get("settings") or {},
        profile.get("total_rosters"),
        profile.get("season"),
        profile.get("season_type"),
        actual_constraints,
    )
    if profile.get("profile_fingerprint") != sha256_json(contract):
        return False, "profile_fingerprint_mismatch", profile

    captured = _parse_utc_timestamp(profile.get("captured_at"))
    if captured is None:
        return False, "captured_at_missing_or_invalid", profile
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age_days = (current - captured).total_seconds() / 86400.0
    if age_days < -1.0:
        return False, "captured_at_in_future", profile
    if age_days > float(max_age_days):
        return False, f"profile_too_old:{age_days:.1f}d", profile

    return True, f"recent_valid_profile:{max(age_days, 0.0):.1f}d", profile


def _write_scoring_snapshot(profile: Dict[str, Any], cache: Path) -> Path:
    scoring = profile.get("scoring_settings")
    if not isinstance(scoring, dict) or not scoring:
        raise RuntimeError("league profile has no scoring_settings; refusing default-scoring fallback")
    path = cache / "scoring_settings_from_profile.json"
    path.write_text(json.dumps(scoring, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _stamp_m1_scoring_provenance(m1_path: Path, profile: Dict[str, Any], profile_status: str) -> None:
    bundle = _load_json(m1_path)
    scoring = bundle.setdefault("scoring", {})
    if scoring.get("signature") != profile.get("scoring_signature"):
        raise RuntimeError("M1 scoring signature differs from league profile")
    scoring["provenance"] = {
        "type": "league_profile",
        "league_id": str(profile.get("league_id") or ""),
        "league_name": profile.get("league_name"),
        "profile_fingerprint": profile.get("profile_fingerprint"),
        "profile_refresh_status": profile_status,
    }
    m1_path.write_text(json.dumps(bundle, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--format", required=True)
    ap.add_argument("--portfolio-config", default="config/league-portfolio.json")
    ap.add_argument("--league-root")
    ap.add_argument("--derived-dir")
    ap.add_argument("--cache-dir")
    ap.add_argument("--registry", default="/tmp/fie-bulk-registry.json")
    ap.add_argument("--full-raw-cache", action="store_true")
    args = ap.parse_args()

    lid = str(args.league_id)
    if not lid.isdigit() or not (6 <= len(lid) <= 32):
        raise SystemExit("invalid Sleeper League ID")
    league_root = Path(args.league_root or f"data/research/leagues/{lid}")
    derived = Path(args.derived_dir or f".cache/fie-research/leagues/{lid}/derived")
    cache = Path(args.cache_dir or f".cache/fie-research/leagues/{lid}")
    portfolio_config = Path(args.portfolio_config)
    registry = Path(args.registry)
    league_root.mkdir(parents=True, exist_ok=True)
    derived.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    primary, extended = season_windows()

    # Historical outputs are intentionally rebuilt.  Do NOT delete profile.json:
    # it is the fail-closed short-lived fallback if Sleeper is temporarily down.
    for i in range(1, 7):
        p = league_root / f"milestone{i}.json"
        if p.exists():
            p.unlink()
    prof = league_root / "profile.json"

    profile_status = "fresh_sleeper_profile"
    try:
        run_with_retries(
            "python", "research/league_profile.py", "build",
            "--league-id", lid, "--format", args.format,
            "--output", str(prof), "--registry", str(registry),
            "--portfolio-config", str(portfolio_config),
            attempts=4, base_delay=2.0,
        )
    except subprocess.CalledProcessError:
        ok, reason, cached = reusable_profile(prof, lid, args.format, portfolio_config)
        if not ok or cached is None:
            print(f"ERROR: Sleeper profile refresh failed and cached profile is unusable: {reason}", file=sys.stderr)
            raise
        profile_status = f"cached_profile_fallback:{reason}"
        print(
            "WARNING: Sleeper profile refresh exhausted retries; using recent validated "
            f"profile.json ({reason}). Structural/scoring fingerprint remains unchanged.",
            file=sys.stderr,
            flush=True,
        )
        update_registry(registry, cached)

    profile = _load_json(prof)
    ok, reason, _ = reusable_profile(
        prof, lid, args.format, portfolio_config,
        # A just-refreshed profile must pass exactly the same contract; allow 7d for both paths.
        max_age_days=PROFILE_FALLBACK_MAX_AGE_DAYS,
    )
    if not ok:
        raise RuntimeError(f"league profile failed post-build contract validation: {reason}")

    scoring_snapshot = _write_scoring_snapshot(profile, cache)
    m1_path = league_root / "milestone1.json"
    m1 = [
        "python", "research/fie_research.py",
        "--seasons", primary,
        "--extended-seasons", extended,
        "--output", str(m1_path),
        "--derived-dir", str(derived),
        "--league-id", lid,
        "--scoring-json", str(scoring_snapshot),
    ]
    if args.full_raw_cache:
        m1.append("--full-raw-cache")
    run(*m1)
    _stamp_m1_scoring_provenance(m1_path, profile, profile_status)
    run("python", "research/validate_bundle.py", str(m1_path))

    run("python", "research/fie_m2.py", "--m1-derived-dir", str(derived), "--m1-bundle", str(m1_path),
        "--derived-dir", str(derived), "--output", str(league_root / "milestone2.json"))
    run("python", "research/validate_m2_bundle.py", str(league_root / "milestone2.json"))

    run("python", "research/fie_m3.py", "--derived-dir", str(derived), "--m1-bundle", str(m1_path),
        "--m2-bundle", str(league_root / "milestone2.json"), "--cache-dir", str(cache), "--seasons", primary,
        "--output", str(league_root / "milestone3.json"))
    run("python", "research/validate_m3_bundle.py", str(league_root / "milestone3.json"))

    run("python", "research/fie_m4.py", "--derived-dir", str(derived), "--m1-bundle", str(m1_path),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--cache-dir", str(cache), "--sleeper-archive", "data/research/market/sleeper", "--seasons", primary,
        "--output", str(league_root / "milestone4.json"))
    run("python", "research/validate_m4_bundle.py", str(league_root / "milestone4.json"))

    run("python", "research/fie_m5.py", "--derived-dir", str(derived), "--m1-bundle", str(m1_path),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--m4-bundle", str(league_root / "milestone4.json"), "--output", str(league_root / "milestone5.json"))
    run("python", "research/validate_m5_bundle.py", str(league_root / "milestone5.json"))

    run("python", "research/fie_m6.py", "--derived-dir", str(derived), "--m1-bundle", str(m1_path),
        "--m2-bundle", str(league_root / "milestone2.json"), "--m3-bundle", str(league_root / "milestone3.json"),
        "--m4-bundle", str(league_root / "milestone4.json"), "--m5-bundle", str(league_root / "milestone5.json"),
        "--cache-dir", str(cache), "--seasons", primary, "--output", str(league_root / "milestone6.json"))
    run("python", "research/validate_m6_bundle.py", str(league_root / "milestone6.json"))

    run("python", "research/stamp_league_artifacts.py", "--profile", str(prof),
        *[str(league_root / f"milestone{i}.json") for i in range(1, 7)])
    for i, validator in [(1, "validate_bundle.py"), (2, "validate_m2_bundle.py"), (3, "validate_m3_bundle.py"),
                         (4, "validate_m4_bundle.py"), (5, "validate_m5_bundle.py"), (6, "validate_m6_bundle.py")]:
        run("python", f"research/{validator}", str(league_root / f"milestone{i}.json"))

    run("python", "research/fie_governance.py", "--league-id", lid, "--league-profile", str(prof),
        "--m4-bundle", str(league_root / "milestone4.json"), "--m5-bundle", str(league_root / "milestone5.json"),
        "--m6-bundle", str(league_root / "milestone6.json"), "--current-snapshot", str(league_root / "current/milestone5_current.json"),
        "--operator-override", str(league_root / "governance/operator_override.json"),
        "--global-operator-override", "data/research/governance/operator_override.json",
        "--output", str(league_root / "governance/active_release.json"))

    print(f"Bulk build complete for {lid}: {league_root}")


if __name__ == "__main__":
    main()

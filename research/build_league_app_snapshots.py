#!/usr/bin/env python3
"""Build compact browser-ready league shell snapshots for fast league switching.

This deliberately contains only Sleeper state needed to hydrate the existing
league loader quickly. Heavy FIE research remains in its existing namespaced
artifacts and is lazy-loaded by the app.

Failure policy: never replace a last-known-good snapshot unless all required
Sleeper endpoints succeed and the generated core validates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-league-core-v1"
INDEX_SCHEMA = "fie-league-index-v1"
USER_AGENT = "Fantasy-Intelligence-Engine/league-snapshot-v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, obj: Any) -> tuple[str, int]:
    data = canonical_bytes(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return sha256_bytes(data), len(data)


def fetch_json(url: str, *, timeout: int = 15, retries: int = 2) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {url}")
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"Sleeper fetch failed after {retries + 1} attempts: {url}: {last}")


def validate_core(core: dict[str, Any], league_id: str) -> None:
    if core.get("schema") != SCHEMA:
        raise ValueError("league core schema mismatch")
    if str(core.get("league_id") or "") != str(league_id):
        raise ValueError("league core league_id mismatch")
    league = core.get("sleeper", {}).get("league")
    rosters = core.get("sleeper", {}).get("rosters")
    users = core.get("sleeper", {}).get("users")
    if not isinstance(league, dict) or str(league.get("league_id") or "") != str(league_id):
        raise ValueError("Sleeper league payload mismatch")
    if not isinstance(rosters, list):
        raise ValueError("Sleeper rosters payload must be a list")
    if not isinstance(users, list):
        raise ValueError("Sleeper users payload must be a list")


def build_core(league_id: str, registry_row: dict[str, Any], getter: Callable[[str], Any] = fetch_json) -> dict[str, Any]:
    base = f"https://api.sleeper.app/v1/league/{league_id}"
    league = getter(base)
    rosters = getter(base + "/rosters")
    users = getter(base + "/users")
    core = {
        "schema": SCHEMA,
        "schema_version": 1,
        "league_id": str(league_id),
        "generated_at": now_iso(),
        "stale_after_seconds": 21600,
        "profile_fingerprint": str(registry_row.get("profile_fingerprint") or ""),
        "scoring_signature": str(registry_row.get("scoring_signature") or ""),
        "format": str(registry_row.get("format") or ""),
        "priority": str(registry_row.get("priority") or ""),
        "league_name": str(registry_row.get("league_name") or league.get("name") or ""),
        "sleeper": {"league": league, "rosters": rosters, "users": users},
        "research": {
            "profile": f"data/research/leagues/{league_id}/profile.json",
            "current": f"data/research/leagues/{league_id}/current/milestone5_current.json",
            "governance": f"data/research/leagues/{league_id}/governance/active_release.json",
        },
        "live_overlay": {
            "automatic": True,
            "blocking": False,
            "endpoints": ["league", "rosters", "users"],
            "historical_transactions": "lazy-manual",
        },
    }
    validate_core(core, league_id)
    return core


def manifest_for(core: dict[str, Any], core_sha: str, core_bytes: int) -> dict[str, Any]:
    league_id = str(core["league_id"])
    return {
        "schema": "fie-league-manifest-v1",
        "schema_version": 1,
        "league_id": league_id,
        "generated_at": core["generated_at"],
        "profile_fingerprint": core.get("profile_fingerprint", ""),
        "scoring_signature": core.get("scoring_signature", ""),
        "core": {
            "path": f"data/research/leagues/{league_id}/app/core.json",
            "sha256": core_sha,
            "bytes": core_bytes,
        },
    }


def existing_entry(league_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
    app = ROOT / "data/research/leagues" / league_id / "app"
    core_path, manifest_path = app / "core.json", app / "manifest.json"
    if not core_path.exists() or not manifest_path.exists():
        return None
    try:
        core = json.loads(core_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_core(core, league_id)
        raw = core_path.read_bytes()
        if manifest.get("core", {}).get("sha256") != sha256_bytes(raw):
            return None
        return index_entry(league_id, row, manifest, fallback=True)
    except Exception:
        return None


def index_entry(league_id: str, row: dict[str, Any], manifest: dict[str, Any], *, fallback: bool = False) -> dict[str, Any]:
    return {
        "league_id": str(league_id),
        "league_name": str(row.get("league_name") or ""),
        "format": str(row.get("format") or ""),
        "priority": str(row.get("priority") or ""),
        "profile_fingerprint": str(row.get("profile_fingerprint") or ""),
        "scoring_signature": str(row.get("scoring_signature") or ""),
        "manifest": f"data/research/leagues/{league_id}/app/manifest.json",
        "core": manifest["core"]["path"],
        "core_sha256": manifest["core"]["sha256"],
        "core_bytes": manifest["core"]["bytes"],
        "generated_at": manifest.get("generated_at"),
        "last_known_good": bool(fallback),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="data/research/leagues/registry.json")
    ap.add_argument("--league-id", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--strict", action="store_true", help="Fail if any selected league cannot be refreshed and has no valid fallback")
    args = ap.parse_args()

    registry_path = ROOT / args.registry
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = registry.get("leagues") or {}
    selected = set(map(str, args.league_id)) if args.league_id else {
        str(lid) for lid, row in rows.items() if row.get("enabled", True) and row.get("current_refresh", True)
    }
    unknown = selected - set(map(str, rows))
    if unknown:
        raise SystemExit(f"Unknown league IDs: {', '.join(sorted(unknown))}")

    entries: list[dict[str, Any]] = []
    failures: list[str] = []
    for league_id in sorted(selected):
        row = rows[league_id]
        try:
            getter = lambda url, _t=args.timeout: fetch_json(url, timeout=_t)  # noqa: E731
            core = build_core(league_id, row, getter)
            app_dir = ROOT / "data/research/leagues" / league_id / "app"
            core_sha, core_size = atomic_write_json(app_dir / "core.json", core)
            manifest = manifest_for(core, core_sha, core_size)
            atomic_write_json(app_dir / "manifest.json", manifest)
            entries.append(index_entry(league_id, row, manifest))
            print(f"OK {league_id}: core={core_size} bytes")
        except Exception as exc:
            fallback = existing_entry(league_id, row)
            if fallback:
                entries.append(fallback)
                print(f"WARN {league_id}: refresh failed, preserved last-known-good: {exc}")
            else:
                failures.append(league_id)
                print(f"ERROR {league_id}: no valid snapshot: {exc}")

    # Preserve valid enabled snapshots not targeted by a one-league manual run.
    for league_id, row in sorted(rows.items()):
        if str(league_id) in selected or not row.get("enabled", True):
            continue
        fallback = existing_entry(str(league_id), row)
        if fallback:
            entries.append(fallback)

    entries.sort(key=lambda x: (x.get("priority") not in {"VERY_HIGH", "HIGH"}, x.get("league_name", ""), x["league_id"]))
    index = {
        "schema": INDEX_SCHEMA,
        "schema_version": 1,
        "generated_at": now_iso(),
        "prefetch": {"concurrency": 2, "good_connection": "all", "save_data": "disabled", "slow_connection": "priority-only"},
        "leagues": entries,
    }
    atomic_write_json(ROOT / "data/research/app/league-index.json", index)
    print(f"Built league app index: {len(entries)} snapshots, failures={len(failures)}")
    if args.strict and failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

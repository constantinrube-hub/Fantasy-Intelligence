#!/usr/bin/env python3
"""Build compact browser-ready league shell snapshots for fast league switching.

V9.3.4A also publishes one shared compact Sleeper NFL player catalog. The
browser primes that catalog before a league switch, which keeps the very large
raw Sleeper /players payload off the interactive critical path.

Failure policy: never replace a last-known-good snapshot or player catalog
unless the replacement validates completely.
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
PLAYER_CATALOG_SCHEMA = "fie-player-catalog-v1"
PLAYER_CATALOG_PATH = Path("data/research/app/player-catalog.json")
PLAYER_CATALOG_URL = "https://api.sleeper.app/v1/players/nfl"
USER_AGENT = "Fantasy-Intelligence-Engine/league-snapshot-v934"

# This is deliberately the subset consumed by buildPlayerUniverse and the
# injury/identity UI. Public nflverse enrichment remains separate and lazy.
PLAYER_FIELDS = (
    "player_id",
    "sport",
    "team",
    "full_name",
    "first_name",
    "last_name",
    "position",
    "fantasy_positions",
    "years_exp",
    "age",
    "gsis_id",
    "status",
    "injury_status",
    "depth_chart_order",
    "depth_chart_position",
    "search_rank",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(obj: Any) -> bytes:
    return (
        json.dumps(
            obj,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, obj: Any) -> tuple[str, int]:
    data = canonical_bytes(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return sha256_bytes(data), len(data)


def fetch_json(
    url: str,
    *,
    timeout: int = 15,
    retries: int = 2,
) -> Any:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(
                req,
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"HTTP {response.status} for {url}"
                    )
                return json.loads(
                    response.read().decode("utf-8")
                )
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            RuntimeError,
        ) as exc:
            last = exc
            if attempt < retries:
                time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(
        "Sleeper fetch failed after "
        f"{retries + 1} attempts: {url}: {last}"
    )


def compact_player_catalog(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Sleeper player catalog payload must be an object")

    players: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        player_id = str(value.get("player_id") or key or "").strip()
        team = str(value.get("team") or "").strip().upper()
        sport = str(value.get("sport") or "nfl").strip().lower()
        if not player_id or not team or sport != "nfl":
            continue

        row = {
            field: value.get(field)
            for field in PLAYER_FIELDS
            if value.get(field) is not None
        }
        row["player_id"] = player_id
        row["sport"] = "nfl"
        row["team"] = team

        # buildPlayerUniverse requires a usable identity and position. D/ST
        # entries are retained because they have a team and DEF/DST position.
        name = str(
            row.get("full_name")
            or " ".join(
                str(row.get(x) or "").strip()
                for x in ("first_name", "last_name")
            ).strip()
            or ""
        ).strip()
        position = str(row.get("position") or "").strip()
        fantasy_positions = row.get("fantasy_positions")
        if not name or (not position and not fantasy_positions):
            continue

        if isinstance(fantasy_positions, tuple):
            row["fantasy_positions"] = list(fantasy_positions)
        players[player_id] = row

    catalog = {
        "schema": PLAYER_CATALOG_SCHEMA,
        "schema_version": 1,
        "generated_at": now_iso(),
        "source": "Sleeper /v1/players/nfl",
        "player_count": len(players),
        "fields": list(PLAYER_FIELDS),
        "players": players,
    }
    validate_player_catalog(catalog)
    return catalog


def validate_player_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema") != PLAYER_CATALOG_SCHEMA:
        raise ValueError("player catalog schema mismatch")
    players = catalog.get("players")
    if not isinstance(players, dict):
        raise ValueError("player catalog players must be an object")
    if len(players) < 500:
        raise ValueError(
            f"player catalog unexpectedly small: {len(players)}"
        )
    if int(catalog.get("player_count") or -1) != len(players):
        raise ValueError("player catalog count mismatch")
    for player_id, row in list(players.items())[:200]:
        if not isinstance(row, dict):
            raise ValueError("player catalog row must be an object")
        if str(row.get("player_id") or "") != str(player_id):
            raise ValueError("player catalog key/player_id mismatch")
        if not row.get("team"):
            raise ValueError("player catalog row missing team")
        if str(row.get("sport") or "").lower() != "nfl":
            raise ValueError("player catalog contains non-NFL row")


def player_catalog_meta(
    catalog: dict[str, Any],
    sha256: str,
    size: int,
    *,
    fallback: bool = False,
) -> dict[str, Any]:
    return {
        "path": str(PLAYER_CATALOG_PATH).replace("\\", "/"),
        "sha256": sha256,
        "bytes": size,
        "player_count": int(catalog.get("player_count") or 0),
        "generated_at": catalog.get("generated_at"),
        "last_known_good": bool(fallback),
    }


def existing_player_catalog() -> tuple[dict[str, Any], dict[str, Any]] | None:
    path = ROOT / PLAYER_CATALOG_PATH
    if not path.exists():
        return None
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        validate_player_catalog(catalog)
        raw = path.read_bytes()
        return catalog, player_catalog_meta(
            catalog,
            sha256_bytes(raw),
            len(raw),
            fallback=True,
        )
    except Exception:
        return None


def build_player_catalog(
    getter: Callable[[str], Any] = fetch_json,
) -> dict[str, Any]:
    return compact_player_catalog(getter(PLAYER_CATALOG_URL))


def validate_core(core: dict[str, Any], league_id: str) -> None:
    if core.get("schema") != SCHEMA:
        raise ValueError("league core schema mismatch")
    if str(core.get("league_id") or "") != str(league_id):
        raise ValueError("league core league_id mismatch")
    league = core.get("sleeper", {}).get("league")
    rosters = core.get("sleeper", {}).get("rosters")
    users = core.get("sleeper", {}).get("users")
    if (
        not isinstance(league, dict)
        or str(league.get("league_id") or "") != str(league_id)
    ):
        raise ValueError("Sleeper league payload mismatch")
    if not isinstance(rosters, list):
        raise ValueError("Sleeper rosters payload must be a list")
    if not isinstance(users, list):
        raise ValueError("Sleeper users payload must be a list")


def build_core(
    league_id: str,
    registry_row: dict[str, Any],
    getter: Callable[[str], Any] = fetch_json,
) -> dict[str, Any]:
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
        "profile_fingerprint": str(
            registry_row.get("profile_fingerprint") or ""
        ),
        "scoring_signature": str(
            registry_row.get("scoring_signature") or ""
        ),
        "format": str(registry_row.get("format") or ""),
        "priority": str(registry_row.get("priority") or ""),
        "league_name": str(
            registry_row.get("league_name")
            or league.get("name")
            or ""
        ),
        "sleeper": {
            "league": league,
            "rosters": rosters,
            "users": users,
        },
        "shared": {
            "player_catalog": str(PLAYER_CATALOG_PATH).replace("\\", "/"),
        },
        "research": {
            "profile": (
                f"data/research/leagues/{league_id}/profile.json"
            ),
            "current": (
                "data/research/leagues/"
                f"{league_id}/current/milestone5_current.json"
            ),
            "governance": (
                "data/research/leagues/"
                f"{league_id}/governance/active_release.json"
            ),
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


def manifest_for(
    core: dict[str, Any],
    core_sha: str,
    core_bytes: int,
) -> dict[str, Any]:
    league_id = str(core["league_id"])
    return {
        "schema": "fie-league-manifest-v1",
        "schema_version": 1,
        "league_id": league_id,
        "generated_at": core["generated_at"],
        "profile_fingerprint": core.get("profile_fingerprint", ""),
        "scoring_signature": core.get("scoring_signature", ""),
        "core": {
            "path": (
                f"data/research/leagues/{league_id}/app/core.json"
            ),
            "sha256": core_sha,
            "bytes": core_bytes,
        },
    }


def existing_entry(
    league_id: str,
    row: dict[str, Any],
) -> dict[str, Any] | None:
    app = ROOT / "data/research/leagues" / league_id / "app"
    core_path = app / "core.json"
    manifest_path = app / "manifest.json"
    if not core_path.exists() or not manifest_path.exists():
        return None
    try:
        core = json.loads(core_path.read_text(encoding="utf-8"))
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        validate_core(core, league_id)
        raw = core_path.read_bytes()
        if manifest.get("core", {}).get("sha256") != sha256_bytes(raw):
            return None
        return index_entry(
            league_id,
            row,
            manifest,
            fallback=True,
        )
    except Exception:
        return None


def index_entry(
    league_id: str,
    row: dict[str, Any],
    manifest: dict[str, Any],
    *,
    fallback: bool = False,
) -> dict[str, Any]:
    return {
        "league_id": str(league_id),
        "league_name": str(row.get("league_name") or ""),
        "format": str(row.get("format") or ""),
        "priority": str(row.get("priority") or ""),
        "profile_fingerprint": str(
            row.get("profile_fingerprint") or ""
        ),
        "scoring_signature": str(
            row.get("scoring_signature") or ""
        ),
        "manifest": (
            f"data/research/leagues/{league_id}/app/manifest.json"
        ),
        "core": manifest["core"]["path"],
        "core_sha256": manifest["core"]["sha256"],
        "core_bytes": manifest["core"]["bytes"],
        "generated_at": manifest.get("generated_at"),
        "last_known_good": bool(fallback),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--registry",
        default="data/research/leagues/registry.json",
    )
    ap.add_argument("--league-id", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument(
        "--player-timeout",
        type=int,
        default=45,
        help="Timeout for the one shared Sleeper player catalog fetch",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Fail if a selected league or the shared player catalog "
            "cannot be refreshed and has no valid fallback"
        ),
    )
    args = ap.parse_args()

    registry_path = ROOT / args.registry
    registry = json.loads(
        registry_path.read_text(encoding="utf-8")
    )
    rows = registry.get("leagues") or {}
    selected = (
        set(map(str, args.league_id))
        if args.league_id
        else {
            str(lid)
            for lid, row in rows.items()
            if row.get("enabled", True)
            and row.get("current_refresh", True)
        }
    )
    unknown = selected - set(map(str, rows))
    if unknown:
        raise SystemExit(
            f"Unknown league IDs: {', '.join(sorted(unknown))}"
        )

    catalog_failure = False
    try:
        catalog_getter = lambda url: fetch_json(  # noqa: E731
            url,
            timeout=max(args.timeout, args.player_timeout),
        )
        catalog = build_player_catalog(catalog_getter)
        catalog_sha, catalog_size = atomic_write_json(
            ROOT / PLAYER_CATALOG_PATH,
            catalog,
        )
        catalog_meta = player_catalog_meta(
            catalog,
            catalog_sha,
            catalog_size,
        )
        print(
            "OK shared player catalog: "
            f"players={catalog['player_count']} "
            f"bytes={catalog_size}"
        )
    except Exception as exc:
        fallback = existing_player_catalog()
        if fallback:
            catalog, catalog_meta = fallback
            print(
                "WARN shared player catalog refresh failed, "
                f"preserved last-known-good: {exc}"
            )
        else:
            catalog_failure = True
            catalog = None
            catalog_meta = {
                "path": str(PLAYER_CATALOG_PATH).replace("\\", "/"),
                "error": str(exc),
            }
            print(
                "ERROR shared player catalog: no valid fallback: "
                f"{exc}"
            )

    entries: list[dict[str, Any]] = []
    failures: list[str] = []
    for league_id in sorted(selected):
        row = rows[league_id]
        try:
            getter = lambda url, _t=args.timeout: fetch_json(  # noqa: E731
                url,
                timeout=_t,
            )
            core = build_core(league_id, row, getter)
            app_dir = (
                ROOT
                / "data/research/leagues"
                / league_id
                / "app"
            )
            core_sha, core_size = atomic_write_json(
                app_dir / "core.json",
                core,
            )
            manifest = manifest_for(
                core,
                core_sha,
                core_size,
            )
            atomic_write_json(
                app_dir / "manifest.json",
                manifest,
            )
            entries.append(
                index_entry(
                    league_id,
                    row,
                    manifest,
                )
            )
            print(
                f"OK {league_id}: core={core_size} bytes"
            )
        except Exception as exc:
            fallback = existing_entry(league_id, row)
            if fallback:
                entries.append(fallback)
                print(
                    f"WARN {league_id}: refresh failed, "
                    f"preserved last-known-good: {exc}"
                )
            else:
                failures.append(league_id)
                print(
                    f"ERROR {league_id}: no valid snapshot: {exc}"
                )

    # Preserve valid enabled snapshots not targeted by a one-league manual run.
    for league_id, row in sorted(rows.items()):
        if str(league_id) in selected or not row.get("enabled", True):
            continue
        fallback = existing_entry(str(league_id), row)
        if fallback:
            entries.append(fallback)

    entries.sort(
        key=lambda x: (
            x.get("priority") not in {"VERY_HIGH", "HIGH"},
            x.get("league_name", ""),
            x["league_id"],
        )
    )
    index = {
        "schema": INDEX_SCHEMA,
        "schema_version": 1,
        "generated_at": now_iso(),
        "prefetch": {
            "concurrency": 2,
            "good_connection": "all",
            "save_data": "disabled",
            "slow_connection": "priority-only",
        },
        "player_catalog": catalog_meta,
        "leagues": entries,
    }
    atomic_write_json(
        ROOT / "data/research/app/league-index.json",
        index,
    )
    print(
        "Built league app index: "
        f"{len(entries)} snapshots, "
        f"failures={len(failures)}, "
        f"catalog={'ok' if not catalog_failure else 'missing'}"
    )
    if args.strict and (failures or catalog_failure):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

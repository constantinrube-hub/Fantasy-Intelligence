#!/usr/bin/env python3
"""Fail closed when fast-switch artifacts are absent or incomplete.

V9.3.4A extends the contract with the shared compact Sleeper player catalog
that removes the raw global Sleeper player payload from interactive league
switches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER_CATALOG_SCHEMA = "fie-player-catalog-v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_player_catalog(base: Path, index: dict) -> tuple[int, int]:
    meta = index.get("player_catalog") or {}
    rel = str(meta.get("path") or "data/research/app/player-catalog.json")
    path = base / rel
    assert path.exists(), f"shared player catalog missing: {rel}"
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert obj.get("schema") == PLAYER_CATALOG_SCHEMA, "player catalog schema mismatch"
    players = obj.get("players")
    assert isinstance(players, dict), "player catalog players must be an object"
    assert len(players) >= 500, f"player catalog unexpectedly small: {len(players)}"
    assert int(obj.get("player_count") or -1) == len(players), "player catalog count mismatch"
    expected = str(meta.get("sha256") or "")
    if expected:
        assert expected == sha256(path), "player catalog hash mismatch"
    meta_count = int(meta.get("player_count") or len(players))
    assert meta_count == len(players), "player catalog index count mismatch"
    sample = list(players.items())[:200]
    for player_id, row in sample:
        assert isinstance(row, dict), "player catalog row must be an object"
        assert str(row.get("player_id") or "") == str(player_id), "player catalog key mismatch"
        assert str(row.get("sport") or "").lower() == "nfl", "non-NFL player in compact catalog"
        assert row.get("team"), "compact player catalog row missing team"
        assert row.get("position") or row.get("fantasy_positions"), "compact player catalog row missing position"
    size = path.stat().st_size
    assert size < 8_000_000, f"compact player catalog unexpectedly large: {size} bytes"
    return len(players), size


def check_tree(base: Path, enabled: list[str], index: dict) -> tuple[int, int]:
    by_id = {str(row.get("league_id")): row for row in index.get("leagues") or []}
    missing: list[str] = []
    total_bytes = 0

    for league_id in enabled:
        if league_id not in by_id:
            missing.append(f"{league_id}:index")
            continue

        core = base / "data" / "research" / "leagues" / league_id / "app" / "core.json"
        manifest = base / "data" / "research" / "leagues" / league_id / "app" / "manifest.json"
        if not core.exists():
            missing.append(f"{league_id}:core")
        if not manifest.exists():
            missing.append(f"{league_id}:manifest")

        if core.exists():
            obj = json.loads(core.read_text(encoding="utf-8"))
            if obj.get("schema") != "fie-league-core-v1":
                missing.append(f"{league_id}:invalid-schema")
            if str(obj.get("league_id")) != league_id:
                missing.append(f"{league_id}:wrong-league-id")
            shared = obj.get("shared") or {}
            if str(shared.get("player_catalog") or "") != "data/research/app/player-catalog.json":
                missing.append(f"{league_id}:player-catalog-ref")
            total_bytes += core.stat().st_size

        if core.exists() and manifest.exists():
            manifest_obj = json.loads(manifest.read_text(encoding="utf-8"))
            expected = str((manifest_obj.get("core") or {}).get("sha256") or "")
            actual = sha256(core)
            if expected != actual:
                missing.append(f"{league_id}:hash")

    if missing:
        raise AssertionError("Fast-switch artifacts incomplete: " + ", ".join(missing[:30]))
    return len(enabled), total_bytes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-dist", action="store_true")
    args = parser.parse_args()

    registry_path = ROOT / "data" / "research" / "leagues" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    enabled = sorted(
        str(league_id)
        for league_id, row in (registry.get("leagues") or {}).items()
        if row.get("enabled", True) and row.get("current_refresh", True)
    )
    assert enabled, "registry contains no enabled current-refresh leagues"

    index_path = ROOT / "data" / "research" / "app" / "league-index.json"
    assert index_path.exists(), "data/research/app/league-index.json missing: fast switch cannot prefetch"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index.get("schema") == "fie-league-index-v1", "league index schema mismatch"

    catalog_count, catalog_bytes = check_player_catalog(ROOT, index)
    count, source_bytes = check_tree(ROOT, enabled, index)
    index_ids = {str(row.get("league_id")) for row in index.get("leagues") or []}
    missing_index_ids = set(enabled) - index_ids
    assert not missing_index_ids, "league index missing enabled leagues: " + ", ".join(sorted(missing_index_ids))

    dist_bytes = None
    dist_catalog_bytes = None
    if args.require_dist:
        dist_index_path = ROOT / "dist" / "data" / "research" / "app" / "league-index.json"
        assert dist_index_path.exists(), "dist league-index missing: Cloudflare cannot serve fast-switch data"
        dist_index = json.loads(dist_index_path.read_text(encoding="utf-8"))
        dist_catalog_count, dist_catalog_bytes = check_player_catalog(ROOT / "dist", dist_index)
        assert dist_catalog_count == catalog_count, "source/dist compact player catalog count differs"
        dist_count, dist_bytes = check_tree(ROOT / "dist", enabled, dist_index)
        assert dist_count == count, "source/dist league count does not match"

    average_bytes = source_bytes / max(1, count)
    assert average_bytes < 750_000, f"average league core unexpectedly large: {average_bytes:.0f} bytes"

    message = (
        "PASS fast-switch artifacts "
        f"leagues={count} source_core_bytes={source_bytes} avg_core_bytes={average_bytes:.0f} "
        f"player_catalog={catalog_count} player_catalog_bytes={catalog_bytes}"
    )
    if dist_bytes is not None:
        message += f" dist_core_bytes={dist_bytes} dist_player_catalog_bytes={dist_catalog_bytes}"
    print(message)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Deduplicate league current snapshots into shared base + scoring overlays.

The script is idempotent and accepts a mixture of legacy full snapshots and
already-split manifests. It rewrites every namespaced current snapshot as a tiny
manifest, preserves the logical hydrated JSON contract, and prunes unreferenced
shared artifacts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from current_snapshot_storage import (
    BASE_FORMAT,
    OVERLAY_FORMAT,
    ROOT,
    STORAGE_FORMAT,
    PROJECTION_FIELDS,
    content_hash,
    load_current_snapshot,
    player_id,
    projection_is_default,
    projection_pair,
    read_json,
    write_json,
)

LEAGUES = ROOT / "data" / "research" / "leagues"
SHARED = ROOT / "data" / "research" / "shared" / "current"


def compatible_partition(items: list[tuple[Path, dict]]) -> list[list[tuple[Path, dict]]]:
    """Group snapshots by logical time slice.

    Player-row differences are represented as sparse league overlays instead
    of forcing duplicate multi-megabyte player bases.
    """
    buckets: dict[tuple, list[tuple[Path, dict]]] = defaultdict(list)
    for p, snap in items:
        key = (
            snap.get("season"),
            snap.get("week"),
            str(snap.get("season_type") or ""),
        )
        buckets[key].append((p, snap))
    return list(buckets.values())


def shared_player_rows(
    group: list[tuple[Path, dict]],
) -> tuple[dict[str, dict], dict[Path, dict[str, dict]]]:
    """Build one common player base and sparse exact league overrides."""
    appearances: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    overrides: dict[Path, dict[str, dict]] = {p: {} for p, _ in group}

    for p, snap in group:
        for row in snap.get("players") or []:
            pid = player_id(row)
            stripped = {
                k: v for k, v in row.items()
                if k not in PROJECTION_FIELDS
            }
            appearances[pid].append((p, stripped))

    shared: dict[str, dict] = {}

    for pid, entries in appearances.items():
        first = entries[0][1]

        common = {
            k: v
            for k, v in first.items()
            if all(k in row and row[k] == v for _, row in entries[1:])
        }

        if player_id(common) != pid:
            raise ValueError(
                f"Player identity is not invariant across current snapshots: {pid}"
            )

        shared[pid] = common

        for p, row in entries:
            diff = {
                k: v
                for k, v in row.items()
                if k not in common or common[k] != v
            }
            if diff:
                overrides[p][pid] = diff

    return shared, overrides


def optimize(paths: list[Path], prune: bool = True) -> dict:
    cache: dict = {}
    loaded: list[tuple[Path, dict]] = []
    for p in paths:
        snap = load_current_snapshot(p, root=ROOT, cache=cache)
        if not snap or not isinstance(snap.get("players"), list):
            continue
        loaded.append((p, snap))
    groups = compatible_partition(loaded)
    refs: set[Path] = set()
    before_paths = {p.resolve() for p, _ in loaded if p.exists()}
    for p, _ in loaded:
        raw = read_json(p, {}) or {}
        st = raw.get("storage") or {}
        for key in ("player_base", "scoring_overlay"):
            ref = st.get(key)
            if ref:
                rp = ROOT / str(ref)
                if rp.exists(): before_paths.add(rp.resolve())
    before = sum(p.stat().st_size for p in before_paths)
    manifests = 0
    bases = 0
    overlays = 0

    for group in groups:
        union, overrides_for = shared_player_rows(group)
        # Preserve the canonical row order from the broadest snapshot. This keeps
        # hydration byte-for-byte equivalent at the logical JSON level for
        # subset leagues (for example, leagues without D/ST rows).
        anchor = max(group, key=lambda item: len(item[1].get("players") or []))[1]
        ordered_ids = []
        seen_ids = set()
        for r in anchor.get("players") or []:
            pid = player_id(r)
            if pid in union and pid not in seen_ids:
                ordered_ids.append(pid); seen_ids.add(pid)
        for _, snap in group:
            for r in snap.get("players") or []:
                pid = player_id(r)
                if pid in union and pid not in seen_ids:
                    ordered_ids.append(pid); seen_ids.add(pid)
        if len(ordered_ids) != len(union):
            raise ValueError("Unable to establish canonical shared player order")
        base_obj = {
            "format": BASE_FORMAT,
            "schema_version": 1,
            "season": group[0][1].get("season"),
            "week": group[0][1].get("week"),
            "season_type": group[0][1].get("season_type"),
            "player_count": len(ordered_ids),
            "players": [union[x] for x in ordered_ids],
        }
        bh = content_hash(base_obj)
        base_rel = Path("data/research/shared/current") / f"player_base.{bh}.json"
        base_path = ROOT / base_rel
        write_json(base_path, base_obj, compact=True)
        refs.add(base_path.resolve()); bases += 1

        overlay_ref_for: dict[Path, Path] = {}

        for pth, snap in group:
            sig = str(snap.get("scoring_signature") or "unknown")

            projections = {}
            for r in snap.get("players") or []:
                pair = projection_pair(r)
                if not projection_is_default(pair):
                    projections[player_id(r)] = pair

            player_overrides = overrides_for.get(pth) or {}

            overlay_obj = {
                "format": OVERLAY_FORMAT,
                "schema_version": 1,
                "season": snap.get("season"),
                "week": snap.get("week"),
                "scoring_signature": sig,
                "scoring_settings": snap.get("scoring_settings") or {},
                "projection_fields": [
                    "decision_weekly_projection",
                    "sleeper_weekly_projection",
                ],
                "default_projection": [0.0, 0.0],
                "nonzero_player_count": len(projections),
                "projections": projections,
                "override_player_count": len(player_overrides),
                "player_overrides": player_overrides,
            }

            oh = content_hash(overlay_obj)
            overlay_rel = (
                Path("data/research/shared/current/scoring")
                / f"{sig}.{oh}.json"
            )
            overlay_path = ROOT / overlay_rel

            write_json(overlay_path, overlay_obj, compact=True)
            refs.add(overlay_path.resolve())
            overlays += 1
            overlay_ref_for[pth] = overlay_rel

        all_ids = set(union)
        for p, snap in group:
            own_ids = {player_id(r) for r in snap.get("players") or []}
            excluded = sorted(all_ids - own_ids, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
            manifest = {k: v for k, v in snap.items() if k not in {"players", "scoring_settings"}}
            manifest["storage"] = {
                "format": STORAGE_FORMAT,
                "player_base": base_rel.as_posix(),
                "scoring_overlay": overlay_ref_for[p].as_posix(),
                "player_count": len(own_ids),
                "excluded_player_ids": excluded,
            }
            write_json(p, manifest, compact=False)
            manifests += 1

    if prune and SHARED.exists():
        for p in SHARED.rglob("*.json"):
            if p.resolve() not in refs:
                p.unlink()
        for d in sorted((p for p in SHARED.rglob("*") if p.is_dir()), reverse=True):
            try: d.rmdir()
            except OSError: pass

    after = sum(p.stat().st_size for p in paths if p.exists())
    shared_bytes = sum(p.stat().st_size for p in SHARED.rglob("*.json")) if SHARED.exists() else 0
    return {
        "snapshots": manifests,
        "compatibility_groups": len(groups),
        "base_files_written": len({(read_json(p, {}) or {}).get("storage", {}).get("player_base") for p in paths if p.exists()} - {None}),
        "overlay_files_written": len({(read_json(p, {}) or {}).get("storage", {}).get("scoring_overlay") for p in paths if p.exists()} - {None}),
        "manifest_bytes": after,
        "shared_bytes": shared_bytes,
        "stored_bytes": after + shared_bytes,
        "previous_current_bytes": before,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Deduplicate league-specific M5 current snapshots")
    ap.add_argument("--no-prune", action="store_true")
    args = ap.parse_args()
    paths = sorted(LEAGUES.glob("*/current/milestone5_current.json"))
    if not paths:
        raise SystemExit("No league current snapshots found")
    result = optimize(paths, prune=not args.no_prune)
    saved = result["previous_current_bytes"] - result["stored_bytes"]
    print(
        "Optimized current snapshots: "
        f"leagues={result['snapshots']} bases={result['base_files_written']} overlays={result['overlay_files_written']} "
        f"before={result['previous_current_bytes']} stored={result['stored_bytes']} saved={saved}"
    )


if __name__ == "__main__":
    main()

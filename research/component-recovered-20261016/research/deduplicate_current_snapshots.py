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
    DEFAULT_REGISTRY,
    OVERLAY_FORMAT,
    PROJECTION_FIELDS,
    ROOT,
    STORAGE_FORMAT,
    active_current_snapshot_paths,
    content_hash,
    load_current_snapshot,
    player_id,
    projection_is_default,
    projection_pair,
    read_json,
    split_manifest_shared_refs,
    write_json,
)

LEAGUES = ROOT / "data" / "research" / "leagues"
SHARED = ROOT / "data" / "research" / "shared" / "current"


def compatible_partition(items: list[tuple[Path, dict]]) -> list[list[tuple[Path, dict]]]:
    """Group all snapshots from the same logical time slice.

    League-specific/scoring-specific row differences are represented later as
    sparse player_overrides rather than forcing duplicate full player bases.
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
    """Return common player rows plus exact sparse per-snapshot differences."""
    appearances: dict[str, list[dict]] = defaultdict(list)
    rows_by_path: dict[Path, dict[str, dict]] = {}

    for path, snap in group:
        rows: dict[str, dict] = {}
        for row in snap.get("players") or []:
            pid = player_id(row)
            stripped = {
                key: value
                for key, value in row.items()
                if key not in PROJECTION_FIELDS
            }
            if pid in rows:
                raise ValueError(
                    f"Duplicate governed player identity {pid} in {path}"
                )
            rows[pid] = stripped
            appearances[pid].append(stripped)
        rows_by_path[path] = rows

    common: dict[str, dict] = {}

    for pid, rows in appearances.items():
        shared_keys = set(rows[0])
        for row in rows[1:]:
            shared_keys &= set(row)

        shared = {}
        for key in sorted(shared_keys):
            value = rows[0][key]
            if all(row[key] == value for row in rows[1:]):
                shared[key] = value

        # Identity is never allowed to become a league-specific override.
        # If the governed ID fields disagree, fail closed.
        try:
            shared_pid = player_id(shared)
        except Exception as exc:
            raise ValueError(
                f"Governed identity is not invariant for player {pid}"
            ) from exc
        if shared_pid != pid:
            raise ValueError(
                f"Governed identity conflict for player {pid}: {shared_pid}"
            )

        common[pid] = shared

    overrides: dict[Path, dict[str, dict]] = {}

    for path, rows in rows_by_path.items():
        per_player: dict[str, dict] = {}

        for pid, row in rows.items():
            base = common[pid]
            diff = {
                key: value
                for key, value in row.items()
                if key not in base or base[key] != value
            }
            if diff:
                per_player[pid] = diff

        overrides[path] = per_player

    return common, overrides


def optimize(
    paths: list[Path],
    prune: bool = True,
    protected_refs: set[Path] | None = None,
) -> dict:
    protected_refs = {
        Path(p).resolve() for p in (protected_refs or set())
    }
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
            for row in snap.get("players") or []:
                pair = projection_pair(row)
                if not projection_is_default(pair):
                    projections[player_id(row)] = pair

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
        keep_refs = refs | protected_refs
        for p in SHARED.rglob("*.json"):
            if p.resolve() not in keep_refs:
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
    ap.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help="Generated active league registry; retired namespaces remain preserved on disk",
    )
    args = ap.parse_args()

    paths = active_current_snapshot_paths(
        args.registry,
        root=ROOT,
        leagues_root=LEAGUES,
    )

    if not paths:
        raise SystemExit("No active-registry current snapshots found")

    # Retired namespaces remain historical evidence. Exclude them from active
    # normalization but protect shared files that their split manifests need.
    all_current = sorted(
        LEAGUES.glob("*/current/milestone5_current.json")
    )
    active = {p.resolve() for p in paths}
    retired_current = [
        p for p in all_current if p.resolve() not in active
    ]
    protected_refs = split_manifest_shared_refs(
        retired_current,
        root=ROOT,
    )

    result = optimize(
        paths,
        prune=not args.no_prune,
        protected_refs=protected_refs,
    )

    saved = (
        result["previous_current_bytes"]
        - result["stored_bytes"]
    )

    print(
        "Optimized current snapshots: "
        f"leagues={result['snapshots']} "
        f"bases={result['base_files_written']} "
        f"overlays={result['overlay_files_written']} "
        f"before={result['previous_current_bytes']} "
        f"stored={result['stored_bytes']} "
        f"saved={saved} "
        f"retired_manifests_preserved={len(retired_current)} "
        f"retired_shared_refs_protected={len(protected_refs)}"
    )


if __name__ == "__main__":
    main()

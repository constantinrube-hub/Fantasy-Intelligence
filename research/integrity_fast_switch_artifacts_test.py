#!/usr/bin/env python3
"""Fail closed when fast-switch artifacts are absent or incomplete."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1 << 20),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def check_tree(
    base: Path,
    enabled: list[str],
    index: dict,
) -> tuple[int, int]:
    by_id = {
        str(row.get("league_id")): row
        for row in index.get("leagues") or []
    }

    missing: list[str] = []
    total_bytes = 0

    for league_id in enabled:
        if league_id not in by_id:
            missing.append(
                f"{league_id}:index"
            )
            continue

        core = (
            base
            / "data"
            / "research"
            / "leagues"
            / league_id
            / "app"
            / "core.json"
        )

        manifest = (
            base
            / "data"
            / "research"
            / "leagues"
            / league_id
            / "app"
            / "manifest.json"
        )

        if not core.exists():
            missing.append(
                f"{league_id}:core"
            )

        if not manifest.exists():
            missing.append(
                f"{league_id}:manifest"
            )

        if core.exists():
            obj = json.loads(
                core.read_text(
                    encoding="utf-8"
                )
            )

            if (
                obj.get("schema")
                != "fie-league-core-v1"
            ):
                missing.append(
                    f"{league_id}:invalid-schema"
                )

            if (
                str(obj.get("league_id"))
                != league_id
            ):
                missing.append(
                    f"{league_id}:wrong-league-id"
                )

            total_bytes += (
                core.stat().st_size
            )

        if (
            core.exists()
            and manifest.exists()
        ):
            manifest_obj = json.loads(
                manifest.read_text(
                    encoding="utf-8"
                )
            )

            expected = str(
                (
                    manifest_obj.get("core")
                    or {}
                ).get("sha256")
                or ""
            )

            actual = sha256(core)

            if expected != actual:
                missing.append(
                    f"{league_id}:hash"
                )

    if missing:
        raise AssertionError(
            "Fast-switch artifacts incomplete: "
            + ", ".join(missing[:30])
        )

    return (
        len(enabled),
        total_bytes,
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--require-dist",
        action="store_true",
    )

    args = parser.parse_args()

    registry_path = (
        ROOT
        / "data"
        / "research"
        / "leagues"
        / "registry.json"
    )

    registry = json.loads(
        registry_path.read_text(
            encoding="utf-8"
        )
    )

    enabled = sorted(
        str(league_id)
        for league_id, row
        in (
            registry.get("leagues")
            or {}
        ).items()
        if (
            row.get("enabled", True)
            and row.get(
                "current_refresh",
                True,
            )
        )
    )

    assert enabled, (
        "registry contains no enabled "
        "current-refresh leagues"
    )

    index_path = (
        ROOT
        / "data"
        / "research"
        / "app"
        / "league-index.json"
    )

    assert index_path.exists(), (
        "data/research/app/"
        "league-index.json missing: "
        "fast switch cannot prefetch"
    )

    index = json.loads(
        index_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        index.get("schema")
        == "fie-league-index-v1"
    ), "league index schema mismatch"

    count, source_bytes = check_tree(
        ROOT,
        enabled,
        index,
    )

    index_ids = {
        str(row.get("league_id"))
        for row in (
            index.get("leagues")
            or []
        )
    }

    missing_index_ids = (
        set(enabled) - index_ids
    )

    assert not missing_index_ids, (
        "league index missing enabled "
        "leagues: "
        + ", ".join(
            sorted(
                missing_index_ids
            )
        )
    )

    dist_bytes = None

    if args.require_dist:
        dist_index_path = (
            ROOT
            / "dist"
            / "data"
            / "research"
            / "app"
            / "league-index.json"
        )

        assert dist_index_path.exists(), (
            "dist league-index missing: "
            "Cloudflare cannot serve "
            "fast-switch data"
        )

        dist_index = json.loads(
            dist_index_path.read_text(
                encoding="utf-8"
            )
        )

        dist_count, dist_bytes = (
            check_tree(
                ROOT / "dist",
                enabled,
                dist_index,
            )
        )

        assert (
            dist_count == count
        ), (
            "source/dist league count "
            "does not match"
        )

    average_bytes = (
        source_bytes
        / max(1, count)
    )

    assert average_bytes < 750_000, (
        "average league core "
        "unexpectedly large: "
        f"{average_bytes:.0f} bytes"
    )

    message = (
        "PASS fast-switch artifacts "
        f"leagues={count} "
        f"source_core_bytes={source_bytes} "
        f"avg_core_bytes="
        f"{average_bytes:.0f}"
    )

    if dist_bytes is not None:
        message += (
            f" dist_core_bytes="
            f"{dist_bytes}"
        )

    print(message)


if __name__ == "__main__":
    main()

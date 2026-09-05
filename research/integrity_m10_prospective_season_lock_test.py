#!/usr/bin/env python3
"""No-network behavioural test for the portable 2026 season lock."""
from __future__ import annotations

import tempfile
from pathlib import Path

from m10_prospective_season_lock import MODELS, POSITIONS, build_lock, first_write, make_fixture_input, validate_lock


def main() -> int:
    lock = build_lock(make_fixture_input()); validate_lock(lock)
    assert set(lock["models"]) == set(POSITIONS)
    for position in POSITIONS:
        for target, variants in lock["models"][position].items():
            assert target and set(variants) == set(MODELS)
            assert variants["M9"]["alpha"] == 10.0 and variants["M10_LINEAR"]["alpha"] == 6.0
            assert variants["M10_HGB"]["schema"] == "fie-hgb-tree-v1"
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "season-lock.json"
        assert first_write(path, lock) == "CREATED" and first_write(path, lock) == "EXISTS"
        altered = dict(lock); altered["season_lock_sha256"] = "0" * 64
        try: validate_lock(altered)
        except AssertionError: pass
        else: raise AssertionError("tampered lock must fail")
    print("PASS deterministic portable season-lock fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

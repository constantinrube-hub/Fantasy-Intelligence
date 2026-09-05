#!/usr/bin/env python3
"""No-network behavioural proof for the corrected R8A v2 season lock."""
from __future__ import annotations

import tempfile
from pathlib import Path

from m10_prospective_activation_guard import LOCK_PATH, validate_activation_lock
from m10_prospective_season_lock import build_lock as build_v1, make_fixture_input as fixture_v1
from m10_prospective_season_lock_v2 import build_lock, first_write, make_fixture_input, validate_lock


def rejects(callable_) -> None:
    try:
        callable_()
    except (AssertionError, ValueError):
        return
    raise AssertionError("unsafe or invalid corrected-lock state was accepted")


def main() -> int:
    lock = build_lock(make_fixture_input())
    validate_lock(lock)
    assert lock["schema"] == "fie-m10-prospective-season-lock-v2"
    assert lock["forbidden_outcome_seasons"] == [2026]
    assert {row["model"] for row in lock["residual_samples"]} == {"M9", "M10_LINEAR", "M10_HGB"}
    assert any(float(value) < 0.0 for row in lock["residual_samples"] for value in row["residuals"].values())
    with tempfile.TemporaryDirectory(prefix="fie-m10-v2-") as directory:
        root = Path(directory)
        target = root / "lock.json"
        assert first_write(target, lock) == "CREATED" and first_write(target, lock) == "EXISTS"
        tampered = dict(lock); tampered["residual_manifest_sha256"] = "0" * 64
        rejects(lambda: validate_lock(tampered))
        v1_path = root / LOCK_PATH; v1_path.parent.mkdir(parents=True, exist_ok=True)
        v1_path.write_text(__import__("json").dumps(build_v1(fixture_v1())), encoding="utf-8")
        rejects(lambda: validate_activation_lock(root))
        v1_path.write_text(__import__("json").dumps(lock), encoding="utf-8")
        assert validate_activation_lock(root)["schema"] == "fie-m10-prospective-season-lock-v2"
    print("PASS corrected v2 lock binds OOS residuals, provenance, and v1 activation rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

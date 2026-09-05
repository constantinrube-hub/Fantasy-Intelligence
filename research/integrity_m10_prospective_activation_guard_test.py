#!/usr/bin/env python3
"""No-network proof that prospective activation is fail-closed."""
from __future__ import annotations

import tempfile
from pathlib import Path

from m10_prospective_activation_guard import LOCK_PATH, validate_activation_lock, validate_write_plan


def rejects(callable_):
    try:
        callable_()
    except ValueError:
        return
    raise AssertionError("unsafe activation condition was accepted")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-m10-activation-") as directory:
        root = Path(directory)
        rejects(lambda: validate_activation_lock(root))
    rejects(lambda: validate_write_plan("refs/heads/audit-implementation-2026-09", []))
    rejects(lambda: validate_write_plan("refs/heads/main", ["app/main.js"]))
    validate_write_plan("refs/heads/main", [])
    validate_write_plan("refs/heads/main", ["data/research/prospective/m10/forecasts/2026/week_01/manifest.json"])
    print("PASS prospective activation requires main, a real lock, and research-only writes")


if __name__ == "__main__":
    main()

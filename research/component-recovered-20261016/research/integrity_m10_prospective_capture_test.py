#!/usr/bin/env python3
"""Focused no-network behavior checks for the Tranche 7B capture contract."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from m10_prospective_capture_contract import (
    capture_paths,
    create_fixture_capture,
    create_fixture_outcomes,
    create_missed_capture,
    sha256_file,
    validate_capture,
)


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="fie-tranche7b-"))
    try:
        created = create_fixture_capture(root, 2026, 1, "2026-09-09T06:00:00+00:00", "2026-09-10T00:00:00+00:00")
        assert created["status"] == "CREATED"
        paths = capture_paths(root, 2026, 1)
        before = {name: sha256_file(path) for name, path in paths.items() if path.is_file()}
        assert create_fixture_capture(root, 2026, 1, "2026-09-09T06:00:00+00:00", "2026-09-10T00:00:00+00:00")["status"] == "EXISTS"
        after = {name: sha256_file(path) for name, path in paths.items() if path.is_file()}
        assert before == after
        assert validate_capture(root, 2026, 1)["status"] == "CAPTURED"
        assert create_fixture_outcomes(root, 2026, 1)["status"] == "CREATED"
        assert validate_capture(root, 2026, 1, require_outcome=True)["outcome_present"] is True
        try:
            create_missed_capture(root, 2026, 1, "2026-09-09T06:00:00+00:00", "2026-09-10T00:00:00+00:00", "WINDOW_MISSED")
        except ValueError:
            pass
        else:
            raise AssertionError("missed capture overwrote an existing forecast")
        missed_root = root / "missed"
        assert create_missed_capture(missed_root, 2026, 2, "2026-09-10T02:00:00+00:00", "2026-09-10T00:00:00+00:00", "WINDOW_MISSED")["status"] == "CREATED"
        assert validate_capture(missed_root, 2026, 2)["status"] == "MISSED"
        try:
            create_fixture_capture(root / "late", 2026, 1, "2026-09-10T00:00:01+00:00", "2026-09-10T00:00:00+00:00")
        except ValueError:
            pass
        else:
            raise AssertionError("late capture was accepted")
    finally:
        shutil.rmtree(root)
    print("PASS Tranche 7B fixture, first-write, missed-window, and outcome-separation contract")


if __name__ == "__main__":
    main()

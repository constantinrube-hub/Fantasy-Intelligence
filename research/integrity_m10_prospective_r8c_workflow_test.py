#!/usr/bin/env python3
"""No-network proof of R8C's raw envelope, capture, and write guard."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from capture_m10_prospective_weekly_raw import main as capture_raw
from m10_prospective_capture_contract import validate_capture
from m10_prospective_activation_guard import validate_write_plan
from run_m10_prospective_weekly_capture import main as run_capture


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="fie-r8c-"))
    try:
        raw, output = root / "raw", root / "output"
        assert capture_raw(["--fixture", "--output-dir", str(raw)]) == 0
        assert run_capture(["--raw-envelope", str(raw / "raw" / "raw-envelope.json"), "--output-root", str(output)]) == 0
        assert validate_capture(output, 2026, 5, require_fixture=True)["status"] == "CAPTURED"
        validate_write_plan("refs/heads/main", ["data/research/prospective/m10/forecasts/2026/week_05/capture-manifest.json", "data/research/prospective/m10/scoring-replay/2026/week_05/scoring-replay.jsonl.gz", "data/research/prospective/m10/decision-traces/2026/week_05/decision-traces.jsonl.gz"])
        try:
            validate_write_plan("refs/heads/main", ["data/research/league_current_snapshots/2026/5/x.json"])
        except ValueError:
            pass
        else:
            raise AssertionError("current snapshot write was accepted")
    finally:
        shutil.rmtree(root)
    print("PASS R8C no-network raw envelope, main-only path guard, and immutable capture")


if __name__ == "__main__":
    main()

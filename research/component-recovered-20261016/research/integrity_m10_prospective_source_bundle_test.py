#!/usr/bin/env python3
"""No-network proof for source-envelope timing and first-write behavior."""
from __future__ import annotations
import tempfile
from pathlib import Path
from m10_prospective_source_bundle import create_bundle, fixture_input, validate_input

def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root=Path(raw); manifest=fixture_input(root); validate_input(manifest)
        assert create_bundle(manifest,root/"out")["status"] == "CREATED"
        assert create_bundle(manifest,root/"out")["status"] == "EXISTS"
        early=fixture_input(root/"early","2026-09-08T00:00:00+00:00")
        assert create_bundle(early,root/"early-out")["status"] == "WINDOW_NOT_REACHED"
    print("PASS time-safe source-envelope and immutable weekly bundle fixture")
    return 0
if __name__ == "__main__": raise SystemExit(main())

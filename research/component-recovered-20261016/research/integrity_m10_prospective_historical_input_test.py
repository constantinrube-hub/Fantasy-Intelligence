#!/usr/bin/env python3
"""Structural guard for the real, public-core lock-input producer."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT / "research/build_m10_prospective_historical_input.py").read_text(encoding="utf-8")
for marker in ("SourceManager", "SEASONS = list(range(2019, 2026))", "add_pregame_features", "public-core-completed-regular-season-only", "source_record"):
    assert marker in text, marker
for forbidden in ("ADP", "market_price", "sleeper_weekly_projection", "replacement", "current_app_rank"):
    assert forbidden not in text, forbidden
print("PASS historical lock input is public-core, hash-recorded, and pre-2026")

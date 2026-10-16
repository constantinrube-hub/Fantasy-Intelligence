#!/usr/bin/env python3
"""Regression proof for the prospective Week 1 completed-game boundary."""
from __future__ import annotations

import tempfile
from pathlib import Path

import capture_m10_prospective_weekly_raw as raw


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="fie-m10-week1-source-"))
    calls: list[str] = []
    original = raw._fetch

    def fake_fetch(url: str, destination: Path) -> dict:
        calls.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("fixture", encoding="utf-8")
        return {"path": destination, "sha256": "a" * 64, "source_identity": url, "release_or_etag": "fixture"}

    raw._fetch = fake_fetch
    try:
        week_one = raw._completed_game_responses(root, season=2026, week=1)
        assert len(week_one) == 1
        assert calls == [raw.SOURCE_TEMPLATES["player_week"].format(season=2025)]

        calls.clear()
        week_two = raw._completed_game_responses(root, season=2026, week=2)
        assert len(week_two) == 2
        assert calls == [
            raw.SOURCE_TEMPLATES["player_week"].format(season=2025),
            raw.SOURCE_TEMPLATES["player_week"].format(season=2026),
        ]
    finally:
        raw._fetch = original
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        root.rmdir()
    print("PASS Week 1 uses only completed prior-season history; Week 2 requires current-season evidence")


if __name__ == "__main__":
    main()

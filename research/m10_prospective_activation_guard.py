"""Fail-closed prerequisites for the future M10 prospective write workflow."""
from __future__ import annotations

from pathlib import Path

LOCK_PATH = Path("data/research/prospective/m10/season-locks/2026/season-lock.json")
WRITE_PREFIXES = (
    "data/research/prospective/m10/season-locks/2026/",
    "data/research/prospective/m10/forecasts/",
    "data/research/prospective/m10/scoring-replay/",
    "data/research/prospective/m10/decision-traces/",
    "data/research/prospective/m10/outcomes/",
    "data/research/prospective/m10/source-bundles/",
)


def validate_activation_lock(root: Path) -> dict:
    path = root / LOCK_PATH
    if not path.is_file():
        raise ValueError("2026 immutable season lock is absent")
    from m10_prospective_season_lock_v2 import LOCK_SCHEMA, load_json, validate_lock
    lock = load_json(path)
    if lock.get("schema") != LOCK_SCHEMA:
        raise ValueError("operational collection requires the corrected R8A v2 season lock")
    validate_lock(lock)
    if any("fixture" in str(row.get("path", "")).lower() for row in lock.get("source_files", [])):
        raise ValueError("fixture season lock cannot activate operational collection")
    return lock


def validate_write_plan(github_ref: str, changed_paths: list[str]) -> None:
    if github_ref != "refs/heads/main":
        raise ValueError("operational writes are permitted only on main")
    if not changed_paths:
        return
    forbidden = [path for path in changed_paths if not any(path.startswith(prefix) for prefix in WRITE_PREFIXES)]
    if forbidden:
        raise ValueError("write plan contains paths outside the research-only allowlist: " + ", ".join(forbidden))

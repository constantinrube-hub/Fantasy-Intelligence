#!/usr/bin/env python3
"""Source-bound M10 outcome replay and fail-closed integrity checks."""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from append_m10_real_outcomes import _numeric_components, index_provider_rows, prepare, publish
from m10_prospective_capture_contract import capture_paths, read_json, read_jsonl_gzip, validate_capture

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("data/operations/weekly-performance/2026/week_04/sources/20261008T012111879533Z/source-envelope.json")
NOW = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)


def fails(code: str, operation) -> None:
    try:
        operation()
    except (AssertionError, ValueError, KeyError, FileNotFoundError) as exc:
        assert code in str(exc), f"expected {code}, got {exc}"
    else:
        raise AssertionError(f"expected {code}")


def copy_evidence(target: Path) -> None:
    for rel in (
        "data/research/prospective/m10/forecasts/2026/week_04",
        "data/research/prospective/m10/scoring-replay/2026/week_04",
        "data/research/prospective/m10/decision-traces/2026/week_04",
        "data/operations/weekly-performance/2026/week_04/sources",
        "data/research/context/weather/2026/week_04",
    ):
        shutil.copytree(ROOT / rel, target / rel)


def main() -> None:
    rows, lineage = prepare(ROOT, 2026, 4, ROOT / SOURCE, as_of=NOW)
    assert len(rows) == lineage["forecast_ids"] == 782
    assert sum(lineage["counts"].values()) == len(rows)
    assert lineage["counts"]["OBSERVED_PROVIDER_ROW"] > 0
    assert lineage["counts"]["BLOCKED_NO_SOURCE_PLAYER_ROW"] > 0
    assert len({row["forecast_id"] for row in rows}) == len(rows)
    assert all("model" not in row and row["revision"] == 1 for row in rows)
    assert all(row["raw_outcomes"] is None for row in rows if row["status"].startswith("BLOCKED"))
    assert _numeric_components({"passing_yards": "", "receptions": "0", "player_id": "a"}) == {"passing_yards": None, "receptions": 0.0}
    fails("M10_OUTCOME_DUPLICATE_GSIS_ID", lambda: index_provider_rows([{"player_id": "a"}, {"player_id": "a"}]))
    assert len(index_provider_rows([{"player_id": ""}, {"player_id": "a"}])) == 1
    fails("M10_OUTCOME_SOURCE_TIME_INVALID", lambda: prepare(ROOT, 2026, 4, ROOT / SOURCE, as_of=datetime(2026, 10, 5, tzinfo=timezone.utc)))

    with tempfile.TemporaryDirectory(prefix="fie-m10-real-test-") as name:
        target = Path(name)
        copy_evidence(target)
        source = target / SOURCE
        initial = publish(target, 2026, 4, source, as_of=NOW)
        assert initial["status"] == "CREATED"
        assert publish(target, 2026, 4, source, as_of=NOW)["status"] == "EXISTS_VALIDATED"
        prospective = target / "data/research/prospective/m10"
        validate_capture(prospective, 2026, 4, require_outcome=True, require_fixture=False)
        paths = capture_paths(prospective, 2026, 4)
        assert read_json(paths["outcome_dir"] / "outcome-manifest.json")["fixture"] is False
        assert read_jsonl_gzip(paths["outcome_dir"] / "outcomes.jsonl.gz") == rows
        meta = paths["outcome_dir"] / "outcome-manifest.json"
        original_meta = meta.read_bytes()
        wrong = read_json(meta)
        wrong["source_release_or_commit"] = "different-source"
        meta.write_text(json.dumps(wrong), encoding="utf-8")
        fails("M10_OUTCOME_FIRST_WRITE_COLLISION", lambda: publish(target, 2026, 4, source, as_of=NOW))
        meta.write_bytes(original_meta)
        wrong = read_json(meta)
        wrong["forecast_manifest_sha256"] = "0" * 64
        meta.write_text(json.dumps(wrong), encoding="utf-8")
        fails("", lambda: validate_capture(prospective, 2026, 4, require_outcome=True, require_fixture=False))
        meta.write_bytes(original_meta)
        archive = next((target / SOURCE.parent).glob("*.csv.gz"))
        archive.write_bytes(archive.read_bytes() + b"tampered")
        fails("PERFORMANCE_RAW_ARCHIVE_HASH_MISMATCH", lambda: prepare(target, 2026, 4, source, as_of=NOW))

    print("M10 real outcomes: source replay, paired identity, immutable write, missing/null, and tamper checks passed")


if __name__ == "__main__":
    main()

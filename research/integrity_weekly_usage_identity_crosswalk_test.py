#!/usr/bin/env python3
"""Exact retrospective ID joins are hash-bound and cannot grant authority."""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import weekly_usage_identity_crosswalk as crosswalk


def expect_error(fn, code):
    try:
        fn()
    except ValueError as exc:
        assert code in str(exc), exc
    else:
        raise AssertionError(f"Expected {code}")


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    catalog_path = root / crosswalk.CATALOG
    catalog_path.parent.mkdir(parents=True)
    catalog = {
        "schema": "fie-player-catalog-v1", "schema_version": 1,
        "source": "Sleeper /v1/players/nfl", "generated_at": "2026-10-10T12:00:00Z",
        "player_count": 4, "players": {
            "100": {"player_id": "100", "gsis_id": "g1"},
            "200": {"player_id": "200", "gsis_id": "g2"},
            "201": {"player_id": "201", "gsis_id": "g2"},
            "300": {"player_id": "300"},
        },
    }
    catalog_path.write_text(json.dumps(catalog))
    report_path = root / "data/operations/weekly-performance/2026/week_04/reports/report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(json.dumps({"as_of_utc": "2026-10-08T02:00:00Z"}))
    usage = {
        "season": 2026, "week": 4,
        "performance_report": {"path": report_path.relative_to(root).as_posix(), "sha256": "a" * 64},
        "dictionary": {"path": "config/weekly-usage-dictionary.json", "sha256": "b" * 64},
        "rows": [
            {"game_id": "game", "team": "AAA", "source_gsis_player_id": pid, "source_row_index": index}
            for index, pid in enumerate(("gsis:g1", "gsis:g2", "gsis:g3", None))
        ],
    }
    with patch.object(crosswalk, "build_usage", return_value=usage):
        output = crosswalk.build(root, report_path, catalog_path)
        assert [row["status"] for row in output["rows"]] == [
            "MATCHED_EXACT_GSIS", "AMBIGUOUS_GSIS", "UNMATCHED_GSIS", "SOURCE_PLAYER_ID_MISSING"]
        assert [row["sleeper_player_id"] for row in output["rows"]] == ["100", None, None, None]
        assert all(row["canonical_player_id"] is None for row in output["rows"])
        assert output["catalog"]["sha256"] == crosswalk.digest(catalog_path)
        assert output["governance"]["target_week_pregame_feature_eligible"] is False
        first = crosswalk.ensure_completed(root, 2026, 5, datetime(2026, 10, 10, 13, tzinfo=timezone.utc))
        second = crosswalk.ensure_completed(root, 2026, 5, datetime(2026, 10, 10, 13, tzinfo=timezone.utc))
        assert first["status"] == "CROSSWALK_CREATED" and second["status"] == "NO_OP_EXISTING_CROSSWALK"
        stored = json.loads((root / first["report"]).read_text())
        assert stored["catalog"]["sha256"] == output["catalog"]["sha256"]
        assert crosswalk.ensure_completed(root, 2026, 5, datetime(2026, 10, 10, 11, tzinfo=timezone.utc))["status"] == "NO_OP_NO_OBSERVED_CATALOG"
        catalog["players"]["100"]["player_id"] = "wrong"
        catalog_path.write_text(json.dumps(catalog))
        expect_error(lambda: crosswalk.build(root, report_path, catalog_path), "CATALOG_PLAYER_ID_MISMATCH")
        catalog["players"]["100"]["player_id"] = "100"
        catalog["player_count"] = 3
        catalog_path.write_text(json.dumps(catalog))
        expect_error(lambda: crosswalk.build(root, report_path, catalog_path), "CATALOG_CONTRACT_INVALID")

print("PASS weekly usage crosswalk: exact, ambiguous, missing, catalog hash, retrospective first-write")

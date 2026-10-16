#!/usr/bin/env python3
"""No-network tests for automatic PR2 completed-week target resolution."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import resolve_in_season_pr2_lineup_outcome_target as r
from in_season_pr2_weekly_lineups import SCHEMA_PORTFOLIO, capture_payload
from weekly_lineup_operational_evidence import sha256_value


SCHEDULE = (
    b"season,week,game_type,home_team,away_team,gameday,gametime,game_id\n"
    b"2026,4,REG,AAA,BBB,2026-10-01,20:15,thu\n"
    b"2026,4,REG,CCC,DDD,2026-10-05,20:15,mon\n"
)


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def add_capture(root: Path, *, generated_at: str, marker: str) -> tuple[Path, dict]:
    value = {
        "schema": SCHEMA_PORTFOLIO,
        "generated_at": generated_at,
        "enabled_league_count": 1,
        "status_counts": {"READY_NO_LINEUP_CHANGE": 1},
        "leagues": [{"league_id": "1", "season": 2026, "week": 4, "status": "READY_NO_LINEUP_CHANGE"}],
        "fixture_marker": marker,
    }
    digest = sha256_value(capture_payload(value))
    value.update({"capture_id": digest[:16], "capture_content_sha256": digest})
    path = root / "data/research/evaluation/2026/weeks/week-4/lineups/captures" / f"portfolio-{digest[:16]}.json"
    write(path, value)
    return path, value


def test_latest_immutable_capture_becomes_due_after_stabilization_buffer() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        add_capture(root, generated_at="2026-10-01T18:00:00+00:00", marker="old")
        newest_path, newest = add_capture(root, generated_at="2026-10-01T18:30:00+00:00", marker="new")
        waiting = r.automatic_outcome_decision(root, SCHEDULE, season=2026, as_of="2026-10-06T11:59:00+00:00")
        assert waiting["capture_allowed"] is False and waiting["reason"] == "WAITING_FOR_OUTCOME_STABILIZATION"
        due = r.automatic_outcome_decision(root, SCHEDULE, season=2026, as_of="2026-10-06T12:15:00+00:00")
        assert due["capture_allowed"] is True and due["week"] == 4
        assert due["capture_id"] == newest["capture_id"]
        assert due["capture_path"] == newest_path.relative_to(root).as_posix()
        assert due["outcome_revision_id"] == f"nflverse-initial-v1-{newest['capture_id']}"


def test_existing_lineage_bound_outcome_suppresses_duplicate() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _, capture = add_capture(root, generated_at="2026-10-01T18:00:00+00:00", marker="only")
        revision = f"nflverse-initial-v1-{capture['capture_id']}"
        write(
            root / f"data/research/evaluation/2026/weeks/week-4/lineups/outcomes/{revision}/outcome.json",
            {"capture_id": capture["capture_id"], "outcome_revision_id": revision},
        )
        result = r.automatic_outcome_decision(root, SCHEDULE, season=2026, as_of="2026-10-06T18:00:00+00:00")
        assert result["capture_allowed"] is False and result["reason"] == "CAPTURES_ALREADY_EVALUATED"


def test_no_capture_is_a_clean_noop() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = r.automatic_outcome_decision(Path(td), SCHEDULE, season=2026, as_of="2026-10-06T18:00:00+00:00")
        assert result["capture_allowed"] is False and result["reason"] == "NO_IMMUTABLE_CAPTURE"


def test_capture_content_drift_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        path, _ = add_capture(root, generated_at="2026-10-01T18:00:00+00:00", marker="before")
        value = json.loads(path.read_text(encoding="utf-8"))
        value["fixture_marker"] = "tampered"
        write(path, value)
        try:
            r.automatic_outcome_decision(root, SCHEDULE, season=2026, as_of="2026-10-06T18:00:00+00:00")
        except ValueError as exc:
            assert "content binding" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("tampered capture accepted")


def main() -> None:
    tests = [
        test_latest_immutable_capture_becomes_due_after_stabilization_buffer,
        test_existing_lineage_bound_outcome_suppresses_duplicate,
        test_no_capture_is_a_clean_noop,
        test_capture_content_drift_fails_closed,
    ]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 automatic outcome schedule ({len(tests)} tests)")


if __name__ == "__main__":
    main()

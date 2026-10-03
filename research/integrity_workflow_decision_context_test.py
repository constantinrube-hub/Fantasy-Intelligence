#!/usr/bin/env python3
"""No-network regression checks for operational week and coverage failures."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import window1c_weekly_actions as actions
import window1d_optimal_waiver as waivers
from integrity_window1c_weekly_actions_test import league_fixture, setup_root, write
from integrity_window1d_optimal_waiver_test import current, live, profile, rosters, users
from workflow_decision_context import default_season, projection_coverage, resolve_target, summarize_readiness, write_output_index

UTC = timezone.utc


def schedule() -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["season", "week", "game_type", "gameday", "gametime", "result"])
    writer.writeheader()
    for week in range(1, 19):
        monday = datetime(2026, 9, 14) + timedelta(weeks=week - 1)
        for day, clock in [(monday - timedelta(days=4), "20:15"), (monday, "20:15")]:
            writer.writerow({"season": 2026, "week": week, "game_type": "REG",
                             "gameday": day.date().isoformat(), "gametime": clock, "result": "0"})
    writer.writerow({"season": 2026, "week": 0, "game_type": "PRE", "gameday": "2026-08-01", "gametime": "20:00"})
    return output.getvalue().encode()


def reject(call, code: str) -> None:
    try:
        call()
    except (ValueError, actions.EvidenceError, waivers.EvidenceError) as exc:
        assert code in str(exc), str(exc)
    else:
        raise AssertionError(f"expected rejection: {code}")


def test_schedule_target_boundaries() -> None:
    raw = schedule()
    for timestamp, expected in [
        ("2026-08-20T12:00:00+00:00", 1),
        ("2026-09-28T23:00:00+00:00", 3),  # Monday, before the late game
        ("2026-09-29T03:59:00+00:00", 3),  # still Monday Eastern
        ("2026-09-29T04:00:00+00:00", 4),  # Tuesday boundary
        ("2026-10-03T01:20:58+00:00", 4),  # Thursday has played; Sunday remains
        ("2026-11-03T04:59:00+00:00", 8),  # DST changed: still Monday Eastern
        ("2026-11-03T05:00:00+00:00", 9),
    ]:
        result = resolve_target(season=2026, week=None, as_of=datetime.fromisoformat(timestamp), fetcher=lambda: raw)
        assert result["week"] == expected, result
        assert result["schedule_sha256"] == hashlib.sha256(raw).hexdigest()
    assert default_season(datetime(2027, 1, 10, tzinfo=UTC)) == 2026
    assert default_season(datetime(2027, 5, 2, tzinfo=UTC)) == 2027


def test_late_game_and_missing_schedule_fail_closed() -> None:
    as_of = datetime(2026, 9, 29, 4, tzinfo=UTC)
    raw = schedule().replace(b"2026,3,REG,2026-09-28,20:15,0", b"2026,3,REG,2026-09-28,20:15,")
    reject(lambda: resolve_target(season=2026, week=None, as_of=as_of, fetcher=lambda: raw), "TARGET_PREVIOUS_WEEK_NOT_FINAL:3")
    for raw in (b"", b"season,week,game_type,gameday\n2026,3,REG,2026-09-28\n"):
        reject(lambda: resolve_target(season=2026, week=None, as_of=as_of, fetcher=lambda: raw), "TARGET_REGULAR_SCHEDULE_INCOMPLETE")
    reject(lambda: resolve_target(season=2027, week=None, as_of=as_of, fetcher=schedule), "TARGET_REGULAR_SCHEDULE_INCOMPLETE")
    reject(lambda: resolve_target(season=2026, week=None, as_of=datetime(2027, 2, 1, tzinfo=UTC), fetcher=schedule), "TARGET_REGULAR_SEASON_COMPLETE")


def test_explicit_historical_week_never_fetches() -> None:
    def forbidden():
        raise AssertionError("explicit week attempted provider access")
    result = resolve_target(season=2025, week=18, as_of=datetime(2026, 10, 3, tzinfo=UTC), fetcher=forbidden)
    assert result["week"] == 18 and result["basis"] == "EXPLICIT_OPERATOR_WEEK"
    for week in (0, 19, True):
        reject(lambda: resolve_target(season=2026, week=week, as_of=datetime.now(UTC), fetcher=forbidden), "TARGET_REGULAR_WEEK_OUT_OF_RANGE")


def test_stale_snapshots_do_not_select_actions_week() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "111111")  # stored Week 2, not the intended Week 4
        write(root / "data/research/leagues/registry.json", {"leagues": {"111111": {
            "enabled": True, "profile_fingerprint": "fp-live", "format": "REDRAFT"}}})
        source = root / "schedule.csv"
        source.write_bytes(schedule())
        result = actions.build_portfolio(root, season=2026, week=None, as_of=datetime(2026, 9, 29, 12, tzinfo=UTC), schedule_path=source)
        assert result["week"] == 4 and result["operational_readiness"]["status"] == "BLOCKED"
        row = result["leagues"][0]
        assert row["status"] == "BLOCKED_WEEK_MISMATCH" and row["week"] == 4
        assert row["input_readiness"]["current_week"] == 2
        assert row["input_readiness"]["target_week"] == 4
        assert row["input_readiness"]["profile_sha256"]


def test_waivers_use_same_target_and_keep_blocked_diagnostics() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lid = "123456789012345678"
        write(root / "config/league-portfolio.json", {"sleeper_username": "C0nstant1n"})
        write(root / "data/research/leagues/registry.json", {"leagues": {lid: {"enabled": True}}})
        write(root / f"data/research/leagues/{lid}/profile.json", profile())
        write(root / f"data/research/leagues/{lid}/current/milestone5_current.json", current())
        source = root / "schedule.csv"
        source.write_bytes(schedule())

        def fetcher(url):
            assert "state/nfl" not in url, "waivers used a separate week source"
            if "/transactions/" in url:
                return []
            if url.endswith("/rosters"):
                return rosters()
            if url.endswith("/users"):
                return users()
            return live()

        with patch.object(waivers, "live_profile_matches", return_value=(True, "fp", {})):
            result = waivers.build_portfolio(root=root, season=2026, week=None, league_id=None,
                max_history_seasons=1, max_current_age_hours=36, fetcher=fetcher,
                as_of=datetime(2026, 9, 29, 12, tzinfo=UTC), schedule_path=source)
        assert result["week"] == 4 and result["operational_readiness"]["counts"]["blocked"] == 1
        row = result["leagues"][0]
        assert row["status"] == "BLOCKED_CURRENT_WEEK_MISMATCH"
        assert row["input_readiness"]["current_week"] == 2
        assert result["governance"]["target_week_outcome_leakage_allowed"] is False


def test_scoring_identity_mismatch_blocks_actions() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        setup_root(root)
        league_fixture(root, "111111")
        p = root / "data/research/leagues/111111/current/milestone5_current.json"
        value = json.loads(p.read_text())
        value["scoring_signature"] = "different-scoring"
        write(p, value)
        row = actions.build_league_report(root, "111111", {"profile_fingerprint": "fp-live"},
            username="C0nstant1n", as_of=datetime(2026, 9, 8, 12, tzinfo=UTC), target_season=2026, target_week=2)
        assert row["status"] == "BLOCKED_CURRENT_SCORING_MISMATCH"


def test_coverage_categories_and_exact_output_pointer() -> None:
    coverage = projection_coverage({"players": [
        {"position_model": "LB", "waiver_activation_eligible": True},
        {"position_model": "QB", "weekly_activation_eligible": False},
    ]})
    assert coverage["by_model_position"]["QB"]["waiver_eligible_rows"] == 0
    assert coverage["by_model_position"]["LB"]["waiver_eligible_rows"] == 1
    assert coverage["unit"] == "source_rows_before_identity_deduplication"
    summary = summarize_readiness([
        {"status": "READY"}, {"status": "NOT_APPLICABLE_ADDS_DISABLED"},
        {"status": "BLOCKED_CURRENT_WEEK_MISMATCH"}, {"status": "UNKNOWN_NEW_STATUS"},
        {"status": "ACTION_REQUIRED", "action_status": {"lineup": "LOCKED_AFTER_FIRST_KICKOFF", "waiver_watchlist": "WATCH_ONLY_NO_WAIVER_MODEL"}},
    ])
    assert summary["status"] == "PARTIAL"
    assert summary["counts"] == {"ready": 1, "partial": 1, "blocked": 1, "not_applicable": 1, "unknown": 1}
    assert summary["lineup_status_counts"]["LOCKED_AFTER_FIRST_KICKOFF"] == 1
    assert summarize_readiness([{"status": "NOT_APPLICABLE_ADDS_DISABLED"}])["status"] == "NOT_APPLICABLE"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        report, markdown = root / "week4.json", root / "week4.md"
        report.write_text('{"week":4}')
        markdown.write_text("Week 4")
        (root / "newer-but-unrelated-week3.md").write_text("Week 3")
        write_output_index(root / "index.json", season=2026, report_json=report, report_markdown=markdown)
        index = json.loads((root / "index.json").read_text())
        assert Path(index["report_markdown"]).read_text() == "Week 4"
        assert index["report_sha256"] == hashlib.sha256(report.read_bytes()).hexdigest()


def test_live_profile_uses_canonical_research_contract() -> None:
    from league_profile import build_profile
    live_league = {"league_id": "123456789012345678", "name": "Fixture",
                   "season": "2026", "season_type": "regular", "total_rosters": 4,
                   "scoring_settings": {"rec": 1}, "roster_positions": ["QB", "RB", "WR", "BN"],
                   "settings": {"type": 0, "daily_waivers": 1, "daily_waivers_days": 10921,
                                "waiver_budget": 100}}
    stored = build_profile(live_league["league_id"], "REDRAFT", league_json=live_league)
    operational = deepcopy(live_league)
    operational["settings"].update({"daily_waivers": 0, "daily_waivers_days": 13655, "best_ball": 0})
    match, live_fp, evidence = waivers.live_profile_matches(stored, operational, None, season=2026, week=4)
    assert match and live_fp != stored["profile_fingerprint"]
    assert evidence["stored_research_fingerprint"] == evidence["live_research_fingerprint"]
    for field, value in [("scoring_settings", {"rec": .5}), ("total_rosters", 5),
                         ("season", "2027"), ("roster_positions", ["QB", "RB", "WR", "FLEX", "BN"])]:
        changed = deepcopy(operational)
        changed[field] = value
        assert not waivers.live_profile_matches(stored, changed, None, season=2026, week=4)[0], field
    reserve = deepcopy(operational)
    reserve["roster_positions"].append("BN")
    assert waivers.live_profile_matches(stored, reserve, None, season=2026, week=4)[0]
    reserve["scoring_settings"] = {"rec": .5}
    assert not waivers.live_profile_matches(stored, reserve, None, season=2026, week=4)[0]
    evolved = deepcopy(stored)
    evolved["roster_evolution"] = {"season": 2026, "application_weekday": "TUESDAY",
                                   "season_complete_week": 18, "weekly_additions": {"4": ["FLEX"]}}
    stage = deepcopy(operational)
    stage["roster_positions"].append("FLEX")
    assert waivers.live_profile_matches(evolved, stage, None, season=2026, week=4)[0]
    stage["scoring_settings"] = {"rec": .5}
    assert not waivers.live_profile_matches(evolved, stage, None, season=2026, week=4)[0]


def main() -> None:
    tests = [test_schedule_target_boundaries, test_late_game_and_missing_schedule_fail_closed,
             test_explicit_historical_week_never_fetches, test_stale_snapshots_do_not_select_actions_week,
             test_waivers_use_same_target_and_keep_blocked_diagnostics, test_scoring_identity_mismatch_blocks_actions,
             test_coverage_categories_and_exact_output_pointer, test_live_profile_uses_canonical_research_contract]
    for test in tests:
        test()
    print(f"PASS workflow decision context ({len(tests)} regression scenarios)")


if __name__ == "__main__":
    main()

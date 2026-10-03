#!/usr/bin/env python3
"""No-network capture tests for rollover, revisions, failures and schedule policy."""
from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import capture_fie_waivers as capture
from point_in_time_capture import build_envelope, canonical_bytes, compact_timestamp, first_write_json, sha256_bytes
from waiver_capture_reconciliation import automatic_capture_allowed, automatic_capture_due, reconcile, rolling_rounds, validate_reconciliation
from validate_window1a_evidence import validate_waivers

LID = "123456789012345678"


def write_observation(root, week, stamp, transactions, users=None, errors=None):
    env = build_envelope(capture_id=f"test-{week}-{stamp}", capture_intent="WAIVER_TRANSACTION",
        provider="Sleeper", endpoint=f"/league/{LID}/transactions/{week}", observed_at=stamp,
        as_of_semantics="Observed response; no private claim inference",
        payload={"transactions": transactions, "league": {"league_id": LID}, "users": users,
                 "source_errors": errors or []})
    path = root / "2026" / f"week_{week:02d}" / LID / compact_timestamp(stamp) / "source-envelope.json"
    first_write_json(path, env)
    return path


def transaction(status="pending", updated=1):
    return {"transaction_id": "claim", "type": "waiver", "status": status,
            "created": 1, "status_updated": updated, "creator": "user", "roster_ids": [1],
            "adds": {"player": 1}, "settings": {"waiver_bid": 11}, "metadata": {}}


def test_rounds_and_calendar():
    assert rolling_rounds({"season_type": "regular", "week": 4}) == [2, 3, 4]
    assert rolling_rounds({"season_type": "regular", "week": 1}) == [0, 1]
    assert rolling_rounds({"season_type": "regular", "week": 18}) == [16, 17, 18]
    assert rolling_rounds({"season_type": "pre", "week": 3}) == [0]
    assert rolling_rounds({"season_type": "regular", "week": 4}, 0) == [4]
    for state in ({"season_type": "regular", "week": True}, {"season_type": "regular", "week": 19},
                  {"season_type": "regular"}, {"season_type": "post", "week": 1}):
        try:
            rolling_rounds(state)
        except ValueError:
            pass
        else:
            raise AssertionError(state)
    for stamp, allowed in [
        ("2026-09-28T22:17:00+00:00", True),  # Tuesday 00:17 CEST
        ("2026-10-26T23:17:00+00:00", True),  # Tuesday 00:17 CET
        ("2027-01-05T23:17:00+00:00", True),  # Wednesday January
        ("2027-01-10T07:17:00+00:00", True),  # Sunday 08:17 CET
        ("2027-01-10T08:30:00+00:00", True),  # queued Sunday run
        ("2027-01-10T11:17:00+00:00", False), # Sunday 12:17 poll
        ("2027-01-11T07:17:00+00:00", True),
        ("2027-01-11T23:17:00+00:00", False), # January 12 in Berlin
        ("2027-04-25T06:17:00+00:00", False),
        ("2027-04-26T06:17:00+00:00", False), # preseason not activated here
        ("2027-08-31T22:17:00+00:00", True),  # September 1 Berlin
    ]:
        assert automatic_capture_allowed(datetime.fromisoformat(stamp)) is allowed, stamp
    source = Path(__file__).resolve().parents[1] / ".github/workflows/capture-fie-waiver-evidence.yml"
    text = source.read_text(encoding="utf-8")
    assert 'cron: "17 */4 * 9-12 2-4"' in text
    assert 'cron: "17 8 * 9-12 0,1,5,6"' in text
    assert 'cron: "17 */4 1-11 1 *"' in text
    assert text.count('timezone: "Europe/Berlin"') == 3
    assert "automatic_capture:" in text


def test_revisions_and_no_double_counting():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pending = transaction()
        complete = transaction("complete", 2)
        users = [{"user_id": "user", "display_name": "Observed Manager"}]
        original = write_observation(root, 3, "2026-09-29T05:00:00+00:00", [pending])
        original_bytes = original.read_bytes()
        write_observation(root, 3, "2026-09-29T09:00:00+00:00", [complete, complete], users)
        write_observation(root, 4, "2026-09-29T09:00:00+00:00", [complete], users)
        write_observation(root, 4, "2026-09-29T13:00:00+00:00", [complete], users)
        write_observation(root, 4, "2026-09-29T17:00:00+00:00", None, errors=["TIMEOUT"])
        later = transaction("failed", 3)
        write_observation(root, 4, "2026-09-30T05:00:00+00:00", [later])
        cutoff = "2026-09-29T18:00:00+00:00"
        report = reconcile(root, 2026, LID, cutoff)
        validate_reconciliation(report, root)
        assert report["unique_transaction_count"] == 1
        row = report["transactions"][0]
        assert row["distinct_revision_count"] == 2 and row["source_observation_count"] == 4
        assert row["observed_rounds"] == [3, 4]
        assert row["latest_observed"]["transaction"]["status"] == "complete"
        assert row["latest_observed"]["creator_display_name"] == "Observed Manager"
        assert report["source_failure_observation_count"] == 1
        assert report["latest_round_sources"][-1]["transaction_source_status"] == "SOURCE_UNAVAILABLE"
        assert reconcile(root, 2026, LID, cutoff) == report
        assert original.read_bytes() == original_bytes
        # Later responses cannot appear in an earlier research cutoff.
        future = reconcile(root, 2026, LID, "2026-09-30T06:00:00+00:00")
        assert future["transactions"][0]["distinct_revision_count"] == 3
        assert future["transactions"][0]["latest_observed"]["transaction"]["status"] == "failed"
        broken = deepcopy(report)
        broken["transactions"][0]["revisions"][0]["raw_transaction_sha256"] = "0" * 64
        try:
            validate_reconciliation(broken, root)
        except AssertionError:
            pass
        else:
            raise AssertionError("tampered transaction accepted")
        broken = deepcopy(report)
        broken["transactions"][0]["latest_observed"]["transaction"]["waiver_bid"] = 999
        try:
            validate_reconciliation(broken, root)
        except AssertionError:
            pass
        else:
            raise AssertionError("tampered latest bid accepted")


def test_absence_unknown_claims_and_round_zero():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tx = transaction("failed")
        tx["settings"] = {}
        write_observation(root, 0, "2026-09-01T05:00:00+00:00", [tx])
        write_observation(root, 0, "2026-09-01T09:00:00+00:00", [])
        report = reconcile(root, 2026, LID, "2026-09-01T10:00:00+00:00")
        row = report["transactions"][0]
        assert row["observed_rounds"] == [0]
        assert row["latest_observed"]["transaction"]["waiver_bid"] is None
        assert row["latest_observed"]["creator_display_name"] is None
        assert row["latest_observed"]["transaction"]["failure_reason"] is None
        assert report["private_claim_absence_inferred"] is False and report["decision_model_eligible"] is False
        assert capture.visibility_for_payload([transaction()])[0] == "UNKNOWN"


def test_capture_failed_and_malformed_sources():
    for transactions in (None, {"error": "not a list"}, ["invalid row"]):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); repo = root / "repo"
            profile = repo / "profile.json"
            profile.parent.mkdir(); profile.write_text('{"settings":{"waiver_budget":100}}')
            def fetch(url):
                if "/transactions/" in url:
                    return transactions, "TIMEOUT" if transactions is None else None
                if url.endswith("/rosters"):
                    return [{"roster_id": 1, "settings": {"waiver_budget_used": 5}}], None
                if url.endswith("/users"):
                    return None, "USERS_TIMEOUT"
                return {"league_id": LID, "settings": {"waiver_budget": 200}}, None
            with patch.object(capture, "ROOT", repo), patch.object(capture, "enabled_leagues", return_value={LID: {"format": "REDRAFT", "profile_path": "profile.json"}}), \
                 patch.object(capture, "safe_fetch_json", side_effect=fetch), patch.object(capture, "utc_now", return_value="2026-10-03T12:00:00+00:00"):
                audit = capture.capture(output_root=root / "out", season=2026, weeks=[0, 1])
            assert audit["captured_league_count"] == 1
            assert all(x["source_status"] == "SOURCE_UNAVAILABLE" for x in audit["invocation_observations"])
            assert all(x["transaction_count"] == 0 for x in audit["invocation_observations"])
            for path in (root / "out").glob("*/week_*/*/*/cycle-state.json"):
                cycle = json.loads(path.read_text())
                assert cycle["visibility_status"] == "SOURCE_UNAVAILABLE"
                assert cycle["teams"][0]["faab_remaining"] == 195 # observed budget, not stale profile 100
            assert validate_waivers(root / "out") == 2


def test_fixture_retry_and_budget_deduplication():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        capture.capture(output_root=root, season=2026, weeks=[0, 1], fixture=True)
        before = {p: p.read_bytes() for p in root.rglob("*.json")}
        capture.capture(output_root=root, season=2026, weeks=[0, 1], fixture=True)
        assert {p: p.read_bytes() for p in root.rglob("*.json")} == before
        assert validate_waivers(root) == 2
        profile, rosters, payload = capture.fixture_payload()
        win = payload["transactions"][0]
        cycle = capture.cycle_state(league_id=LID, season=2026, week=1, observed_at="2026-09-01T00:00:00+00:00",
            profile=profile, rosters=rosters, player_ids=set(), transactions=[win, win])
        assert cycle["teams"][0]["observed_completed_waiver_spend"] == 41


def test_season_binding_and_exact_output_index():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        registry = {LID: {"format": "REDRAFT", "profile_path": "profile.json"}}
        (root / "profile.json").write_text('{"season":2025}')
        with patch.object(capture, "ROOT", root), patch.object(capture, "enabled_leagues", return_value=registry), \
             patch.object(capture, "safe_fetch_json", side_effect=AssertionError("foreign season requested provider")):
            try:
                capture.capture(output_root=root / "out", season=2026, weeks=[1])
            except ValueError as exc:
                assert "LEAGUE_PROFILE_SEASON_MISMATCH" in str(exc)
            else:
                raise AssertionError("foreign season accepted")
        index = root / "index.json"
        assert capture.main(["--fixture", "--output-root", str(root / "fixture"), "--output-index", str(index)]) == 0
        actual = json.loads(index.read_text())
        assert Path(actual["audit_path"]).is_file() and actual["season"] == 2026
        audit = json.loads(Path(actual["audit_path"]).read_text())
        assert audit["captured_league_count"] == 1 and audit["requested_weeks"] == [1]


def test_delayed_daily_poll_is_not_a_second_capture():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sunday = datetime.fromisoformat("2027-01-10T08:30:00+00:00")
        assert automatic_capture_due(root, sunday, 23)
        path = root / "2026/visibility-audits/audit_test.json"
        path.parent.mkdir(parents=True)
        row = {"capture_mode": "AUTOMATIC", "capture_schedule_date": "2027-01-10", "captured_league_count": 23}
        path.write_text(json.dumps(row))
        assert not automatic_capture_due(root, sunday, 23)
        assert automatic_capture_due(root, sunday, 24) # registry changed; old partial portfolio is insufficient
        row["capture_mode"] = "MANUAL"
        path.write_text(json.dumps(row))
        assert automatic_capture_due(root, sunday, 23)
        assert automatic_capture_due(root, datetime.fromisoformat("2027-01-12T07:17:00+00:00"), 23) is False


def main():
    tests = [test_rounds_and_calendar, test_revisions_and_no_double_counting,
             test_absence_unknown_claims_and_round_zero, test_capture_failed_and_malformed_sources,
             test_fixture_retry_and_budget_deduplication, test_season_binding_and_exact_output_index,
             test_delayed_daily_poll_is_not_a_second_capture]
    for test in tests:
        test()
    print(f"PASS waiver capture reconciliation ({len(tests)} scenario groups)")


if __name__ == "__main__":
    main()

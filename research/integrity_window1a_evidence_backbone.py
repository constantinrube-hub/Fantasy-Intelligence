#!/usr/bin/env python3
"""Deterministic no-network acceptance suite for Window 1A."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from capture_fie_availability import compact
from capture_fie_waivers import capture as capture_waivers, enabled_leagues, normalize_transactions, observed_bid_book_summary, visibility_for_payload
from capture_fie_weather import capture as capture_weather
from fie_research_pipeline_contract import ROOT
from freeze_fie_2026_baseline import build_baseline, validate_baseline
from point_in_time_capture import build_envelope, first_write_json, latest_eligible, sha256_file, validate_envelope


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_envelope_and_first_write(root: Path) -> None:
    payload = {"missing": None, "negative_legal_value": -4}
    envelope = build_envelope(
        capture_id="fixture", capture_intent="OTHER_GOVERNED", provider="fixture",
        endpoint="fixture://source", observed_at="2026-09-06T09:00:00Z",
        as_of_semantics="fixture known at observation", payload=payload,
        revision_metadata_status="NOT_EXPOSED_BY_PROVIDER",
    )
    validate_envelope(envelope)
    target = root / "first-write.json"
    assert first_write_json(target, envelope) == "CREATED"
    before = target.read_bytes()
    assert first_write_json(target, envelope) == "EXISTS" and target.read_bytes() == before
    changed = {**envelope, "payload": {"missing": 0, "negative_legal_value": -4}}
    try:
        first_write_json(target, changed)
    except ValueError as error:
        assert "collision" in str(error)
    else:
        raise AssertionError("G11/R807 first-write collision must fail closed")


def test_availability_compatibility() -> None:
    raw = {
        "1": {"player_id": "1", "full_name": "Fixture RB", "team": "AAA", "position": "RB", "status": "Active", "injury_status": None},
        "2": {"player_id": "2", "full_name": "Fixture CB", "team": "BBB", "position": "CB", "status": "Active"},
    }
    rows = compact(raw, "2026-09-06T09:00:00+00:00", "2026-09-06")
    assert rows == [{
        "captured_at": "2026-09-06T09:00:00+00:00", "availability_as_of": "2026-09-06",
        "source": "Sleeper /v1/players/nfl", "sleeper_id": "1", "full_name": "Fixture RB",
        "team": "AAA", "position_model": "RB", "status": "Active",
    }]
    assert "schema_version" not in rows[0] and "payload_sha256" not in rows[0]


def test_waivers(root: Path) -> None:
    audit = capture_waivers(output_root=root, season=2026, weeks=[1], fixture=True)
    assert audit["enabled_league_count"] == 1 and audit["bid_probability_or_optimization"] is False
    capture_dir = next((root / "2026/week_01/123456789012345678").iterdir())
    rows = load(capture_dir / "normalized-transactions.json")
    by_id = {row["transaction"]["transaction_id"]: row for row in rows}
    assert by_id["tx_win"]["source_observation_type"] == "COMPLETED_WAIVER"
    assert by_id["tx_win"]["transaction"]["waiver_bid"] == 41
    assert by_id["tx_fail"]["source_observation_type"] == "FAILED_OR_REJECTED_WAIVER"
    assert by_id["tx_fail"]["transaction"]["failure_reason"] == "This player was claimed by another owner."
    assert by_id["tx_fa"]["source_observation_type"] == "FREE_AGENT_ADD"
    assert by_id["tx_fa"]["transaction"]["waiver_bid"] is None
    assert all(row["visibility"]["losing_claim_visibility"] == "PARTIAL_OBSERVED" for row in rows if row["transaction"]["type"] == "waiver")
    assert load(capture_dir / "cycle-state.json")["visibility_status"] == "PARTIAL_BEHAVIOR_ONLY"
    assert load(capture_dir / "behavior-features.json")["managers"][0]["reliability"] == "LEAGUE_FALLBACK"
    winner = [{"transaction_id": "winner", "type": "waiver", "status": "complete", "settings": {"waiver_bid": 41}}]
    assert visibility_for_payload(winner)[0] == "WINNER_ONLY_OBSERVED"
    normalized = normalize_transactions(winner, league_id="123456789012345678", week=2, fetched_at="2026-09-16T07:00:00+00:00", raw_sha256="1" * 64)
    assert normalized[0]["visibility"]["losing_claim_visibility"] == "WINNER_ONLY_OBSERVED"
    no_settings = [{"transaction_id": "unknown-bid", "type": "waiver", "status": "complete", "settings": {}}]
    assert normalize_transactions(no_settings, league_id="123456789012345678", week=2, fetched_at="2026-09-16T07:00:00+00:00", raw_sha256="1" * 64)[0]["transaction"]["waiver_bid"] is None
    complete = observed_bid_book_summary([41, 27, 10], source_complete=True)
    assert complete["second_highest_observed_bid"] == 27 and complete["over_second"] == 14
    incomplete = observed_bid_book_summary([41], source_complete=False)
    assert incomplete["second_highest_observed_bid"] is None and incomplete["over_second"] is None
    duplicate = [winner[0], {**winner[0]}]
    assert len(normalize_transactions(duplicate, league_id="123456789012345678", week=2, fetched_at="2026-09-16T07:00:00+00:00", raw_sha256="1" * 64)) == 1


def test_weather_cutoff(root: Path) -> None:
    rows = [
        {"observed_at": "2026-10-08T12:10:00+00:00", "wind_mph": 25},
        {"observed_at": "2026-10-08T18:10:00+00:00", "wind_mph": 10},
    ]
    assert latest_eligible(rows, cutoff="2026-10-08T16:00:00+00:00")["wind_mph"] == 25
    context = load(capture_weather(output_root=root, season=2026, week=5, fixture=True))
    assert context["games"][0]["environment"]["wind_mph"] == 25
    assert context["games"][0]["environment"]["forecast_observed_at"] < context["cutoff"]


def test_portfolio_and_baseline() -> None:
    leagues = enabled_leagues(ROOT / "data/research/leagues/registry.json")
    assert len(leagues) == 22
    assert {row["format"] for row in leagues.values()} == {"REDRAFT", "DYNASTY", "CHOPPED", "REDRAFT_BESTBALL", "DYNASTY_BESTBALL", "CHOPPED_BESTBALL"}
    games = ("game_id,season,game_type,week,gameday,gametime,home_team,away_team\n"
             "2026_01_AAA_BBB,2026,REG,1,2026-09-09,20:20,BBB,AAA\n").encode()
    baseline = build_baseline(root=ROOT, season=2026, games_csv=games, created_at="2026-09-06T09:00:00+00:00")
    validate_baseline(baseline, ROOT)
    assert baseline["eligibility"] == "PRESEASON_ELIGIBLE"
    assert all(row["profile_fingerprint"] and row["scoring_signature"] for row in baseline["leagues"])
    assert baseline["governance"]["production_model"] == "M9"
    assert baseline["governance"]["production_or_runtime_changed"] is False
    assert baseline["governance"]["market_or_adp_used_as_football_feature"] is False


def test_closure_contract() -> None:
    contract = load(ROOT / "config/window1a-evidence-backbone.json")
    assert contract["window"] == "1A" and contract["governance"]["production_model"] == "M9"
    assert not any(contract["governance"][key] for key in (
        "m10_production_or_shadow_integration", "app_or_runtime_integration", "rankings_changed",
        "waiver_probability_or_optimization", "adp_or_market_as_football_feature", "historical_backfill",
    ))
    for item in contract["immutable_evidence"].values():
        path = ROOT / item["path"]
        assert path.is_file() and sha256_file(path) == item["sha256"], path
    trace = contract["existing_transaction_producer"]
    assert trace["load_owner"] == "index.html::loadLeagueTransactions"
    assert trace["profile_owner"] == "index.html::buildTransactionProfiles"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        test_envelope_and_first_write(root / "envelope")
        test_availability_compatibility()
        test_waivers(root / "waivers")
        test_weather_cutoff(root / "weather")
    test_portfolio_and_baseline()
    test_closure_contract()
    print("PASS Window 1A cross-cutting, WE01-WE16 contract semantics, CT03/CT05 and availability compatibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

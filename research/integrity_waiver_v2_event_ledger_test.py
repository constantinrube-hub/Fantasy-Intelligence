#!/usr/bin/env python3
"""Adversarial E1 integrity checks for the Waiver-v2 shared event contract."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from waiver_v2_event_ledger import (
    EVENT_COLUMNS, EVENT_TYPES, build_e1_event_ledger, build_e2_event_ledger, build_e3_event_ledger, build_e4_event_ledger, build_e5_event_ledger, build_source_inventory,
    validate_event_ledger, _canonical_resolver, _blocker_receipt,
)
from run_waiver_v2_historical_ledger import write_source_snapshot


def source_rows() -> pd.DataFrame:
    return pd.DataFrame([
        {"season": 2024, "week": 1, "game_id": "2024_01_A_B", "play_id": 10, "season_type": "REG", "play_type": "pass", "play_deleted": 0},
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 11, "season_type": "REG", "play_type": "kickoff", "play_deleted": 0},
        # Postseason rows cannot prove the completed regular-season envelope.
        {"season": 2025, "week": 19, "game_id": "2025_wc_A_B", "play_id": 12, "season_type": "POST", "play_type": "punt", "play_deleted": 0},
    ])


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    pbp = source_rows()
    source_items = [
        {"season": 2024, "url": "https://example.test/pbp-2024.csv", "sha256": "a" * 64},
        {"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "b" * 64},
    ]
    inventory = build_source_inventory(pbp, requested_seasons=[2024, 2025], pbp_source_items=source_items)
    assert inventory["pbp_source_complete"]
    assert inventory["participation"]["status"] == "NOT_REQUESTED"
    assert all(row["regular_rows"] == 1 for row in inventory["pbp_by_season"])
    try:
        build_source_inventory(pbp, requested_seasons=[2024, 2025], pbp_source_items=source_items + source_items[:1])
        raise AssertionError("duplicate season source receipts must fail before event derivation")
    except ValueError as error:
        assert "duplicate season receipts" in str(error)

    for second_binding in ("PLAYER_ONE", "PLAYER_TWO"):
        identity_collision = pd.DataFrame([
            {"gsis_id": "00-0000001", "canonical_player_id": "PLAYER_ONE"},
            {"gsis_id": "00-0000001", "canonical_player_id": second_binding},
        ])
        try:
            _canonical_resolver(identity_collision)
            raise AssertionError("duplicate GSIS bindings must fail before dictionary collapse")
        except ValueError as error:
            assert "duplicate gsis bindings" in str(error)

    missing = pbp.drop(columns=["play_deleted"])
    blocked = build_source_inventory(missing, requested_seasons=[2024, 2025], pbp_source_items=source_items)
    assert not blocked["pbp_source_complete"]
    assert blocked["pbp_by_season"][0]["status"] == "BLOCKED_SOURCE_INCOMPLETE"

    pbp_path = root / "pbp.csv.gz"
    pbp.to_csv(pbp_path, index=False, compression={"method": "gzip", "mtime": 0})
    receipt = build_e1_event_ledger(
        raw_pbp_path=pbp_path, requested_seasons=[2024, 2025], pbp_source_items=source_items,
        output_path=root / "event" / "ledger.csv.gz", report_path=root / "event" / "receipt.json",
    )
    persisted = pd.read_csv(root / "event" / "ledger.csv.gz")
    assert persisted.empty and list(persisted.columns) == EVENT_COLUMNS
    assert receipt == json.loads((root / "event" / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["event_rows"] == 0 and receipt["activation_eligible"] is False

    # Every future event family has a stable, identity-bearing fixture shape.
    fixtures = []
    for index, event_type in enumerate(sorted(EVENT_TYPES)):
        fixtures.append({
            "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": index + 1,
            "event_type": event_type, "canonical_player_id": f"00-003{index:04d}",
            "team": "A", "opponent": "B", "play_type": "fixture", "yards": 0.0,
            "touchdown": False, "fumble": False, "fumble_lost": False, "fumble_recovery": False,
            "special_teams": False, "source_player_roles": "{}", "identity_evidence": "fixture_exact_gsis",
            "source_url": "https://example.test/pbp-2025.csv", "source_sha256": "b" * 64,
            "source_season": 2025, "schema_fingerprint": "schema", "builder_sha256": "builder",
            "reconciliation_status": "NOT_YET_RECONCILED", "event_status": "BLOCKED_EVENT_SEMANTICS",
        })
    fixture_events = pd.DataFrame(fixtures)
    validate_event_ledger(fixture_events)
    try:
        validate_event_ledger(pd.concat([fixture_events, fixture_events.iloc[[0]]], ignore_index=True))
        raise AssertionError("duplicate football event must fail")
    except ValueError as error:
        assert "duplicate canonical football events" in str(error)
    no_play = fixture_events.copy()
    no_play["play_deleted"] = False
    no_play.loc[0, "play_deleted"] = True
    try:
        validate_event_ledger(no_play)
        raise AssertionError("penalty/no-play event must fail")
    except ValueError as error:
        assert "deleted/no-play" in str(error)

    snapshot = write_source_snapshot(
        players=pd.DataFrame([{"gsis_id": "p1"}]),
        player_stats_frames=[pd.DataFrame([{"season": 2025, "week": 1}])],
        weekly_roster_frames=[pd.DataFrame([{"season": 2025, "week": 1}])],
        games=pd.DataFrame([{"season": 2025, "week": 1}]), identity=pd.DataFrame([{"gsis_id": "p1"}]),
        raw_dir=root / "snapshot", pbp_frames=[pbp], participation_frames=[pd.DataFrame([{"game_id": "2025_01_A_B"}])],
    )
    assert {"pbp", "participation"} <= set(snapshot)
    assert snapshot["pbp"]["rows"] == len(pbp)

    # E2 derives only rows with exact IDs and reconciles QB sacks against the
    # published weekly stat. Pick-sixes, all-play fumbles and QB rushing-TD
    # adjustments all originate in the single shared event ledger.
    e2_pbp = pd.DataFrame([
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 1, "season_type": "REG", "play_type": "pass", "play_deleted": 0,
         "fumble": 1, "fumble_lost": 1, "fumbled_1_player_id": "00-0000001", "fumbled_2_player_id": None,
         "interception": 0, "return_touchdown": 0, "passer_player_id": "00-0000001", "rush_touchdown": 0, "rusher_player_id": None,
         "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 0, "touchdown": 0, "special_teams_play": 0},
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 2, "season_type": "REG", "play_type": "pass", "play_deleted": 0,
         "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
         "interception": 1, "return_touchdown": 1, "passer_player_id": "00-0000001", "rush_touchdown": 0, "rusher_player_id": None,
         "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 0, "touchdown": 1, "special_teams_play": 0},
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 3, "season_type": "REG", "play_type": "run", "play_deleted": 0,
         "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
         "interception": 0, "return_touchdown": 0, "passer_player_id": None, "rush_touchdown": 1, "rusher_player_id": "00-0000001",
         "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 3, "touchdown": 1, "special_teams_play": 0},
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 4, "season_type": "REG", "play_type": "pass", "play_deleted": 0,
         "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
         "interception": 0, "return_touchdown": 0, "passer_player_id": "00-0000001", "rush_touchdown": 0, "rusher_player_id": None,
         "sack": 1, "posteam": "A", "defteam": "B", "yards_gained": -7, "touchdown": 0, "special_teams_play": 0},
    ])
    non_qb_sack = e2_pbp.iloc[-1].copy()
    non_qb_sack["play_id"] = 99
    non_qb_sack["passer_player_id"] = "00-0000002"
    e2_pbp = pd.concat([e2_pbp, non_qb_sack.to_frame().T], ignore_index=True)
    e2_pbp_path, e2_identity_path, e2_stats_path = root / "e2-pbp.csv.gz", root / "e2-identity.csv", root / "e2-stats.csv"
    e2_pbp.to_csv(e2_pbp_path, index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame([{"gsis_id": "00-0000001", "canonical_player_id": "QB1"}, {"gsis_id": "00-0000002", "canonical_player_id": "WR1"}]).to_csv(e2_identity_path, index=False)
    pd.DataFrame([{"canonical_player_id": "QB1", "season": 2025, "week": 1, "position_model": "QB", "sacks": 1}, {"canonical_player_id": "WR1", "season": 2025, "week": 1, "position_model": "WR", "sacks": 0}]).to_csv(e2_stats_path, index=False)
    e2 = build_e2_event_ledger(
        raw_pbp_path=e2_pbp_path, identity_path=e2_identity_path, canonical_player_stats_path=e2_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "c" * 64}],
        output_path=root / "e2" / "events.csv.gz", weekly_stats_output_path=root / "e2" / "weekly.csv.gz", report_path=root / "e2" / "report.json",
    )
    assert all(e2["rule_support"][key]["support_status"] == "EXACT_EVENT_READY" for key in ("fum", "fum_lost", "pass_int_td", "bonus_rush_td_qb", "pass_sack"))
    assert e2["sack_reconciliation"]["excluded_non_qb_pbp_events"] == 1
    weekly = pd.read_csv(root / "e2" / "weekly.csv.gz").iloc[0]
    assert weekly.event_fumbles == 1 and weekly.event_fumbles_lost == 1
    assert weekly.event_pass_int_td == 1 and weekly.event_bonus_rush_td_qb == 1

    # E3 admits direct, individual PBP roles only.  A recovery touchdown may
    # also be a special-teams touchdown and recovery, but each Sleeper rule
    # receives its own single, de-duplicated event family row.
    e3_pbp = e2_pbp.copy()
    for column, value in {
        "td_player_id": None, "fumble_recovery_1_player_id": None, "fumble_recovery_2_player_id": None,
        "fumble_forced": 0, "fumble_out_of_bounds": 0,
        "forced_fumble_player_1_player_id": None, "forced_fumble_player_2_player_id": None,
    }.items():
        e3_pbp[column] = value
    e3_pbp.loc[len(e3_pbp)] = {
        "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 5, "season_type": "REG", "play_type": "kickoff", "play_deleted": 0,
        "fumble": 1, "fumble_lost": 1, "fumbled_1_player_id": "00-0000004", "fumbled_2_player_id": None,
        "interception": 0, "return_touchdown": 1, "passer_player_id": None, "rush_touchdown": 0, "rusher_player_id": None,
        "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 97, "touchdown": 1, "special_teams_play": 1,
        "td_player_id": "00-0000003", "fumble_recovery_1_player_id": "00-0000003", "fumble_recovery_2_player_id": None,
        "fumble_forced": 1, "fumble_out_of_bounds": 0,
        "forced_fumble_player_1_player_id": "00-0000002", "forced_fumble_player_2_player_id": None,
    }
    e3_pbp_path, e3_identity_path = root / "e3-pbp.csv.gz", root / "e3-identity.csv"
    e3_pbp.to_csv(e3_pbp_path, index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame([
        {"gsis_id": "00-0000001", "canonical_player_id": "QB1"},
        {"gsis_id": "00-0000002", "canonical_player_id": "ST_FORCE"},
        {"gsis_id": "00-0000003", "canonical_player_id": "ST_REC"},
        {"gsis_id": "00-0000004", "canonical_player_id": "ST_FUM"},
    ]).to_csv(e3_identity_path, index=False)
    e3 = build_e3_event_ledger(
        raw_pbp_path=e3_pbp_path, identity_path=e3_identity_path, canonical_player_stats_path=e2_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "d" * 64}],
        output_path=root / "e3" / "events.csv.gz", weekly_stats_output_path=root / "e3" / "weekly.csv.gz", report_path=root / "e3" / "report.json",
    )
    assert all(e3["rule_support"][key]["support_status"] == "EXACT_EVENT_READY" for key in ("fum_rec_td", "st_td", "st_ff", "st_fum_rec"))
    e3_weekly = pd.read_csv(root / "e3" / "weekly.csv.gz").set_index("canonical_player_id")
    assert e3_weekly.loc["ST_REC", "event_fumble_recovery_tds"] == 1
    assert e3_weekly.loc["ST_REC", "event_special_teams_tds"] == 1
    assert e3_weekly.loc["ST_REC", "event_special_teams_fumble_recoveries"] == 1
    assert e3_weekly.loc["ST_FORCE", "event_special_teams_forced_fumbles"] == 1

    # E4 accepts dedicated kickoff/punt returner roles only and reconciles
    # their PBP yardage to the published player-week aggregates. A non-zero
    # lateral return has a team total but no player split, so it blocks rather
    # than being assigned to the first returner.
    e4_pbp = e3_pbp.copy()
    for column, value in {
        "return_yards": 0, "return_team": None, "kickoff_returner_player_id": None,
        "lateral_kickoff_returner_player_id": None, "punt_returner_player_id": None,
        "lateral_punt_returner_player_id": None,
    }.items():
        e4_pbp[column] = value
    e4_pbp.loc[len(e4_pbp)] = {
        "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 6, "season_type": "REG", "play_type": "kickoff", "play_deleted": 0,
        "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
        "interception": 0, "return_touchdown": 0, "passer_player_id": None, "rush_touchdown": 0, "rusher_player_id": None,
        "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 25, "touchdown": 0, "special_teams_play": 1,
        "td_player_id": None, "fumble_recovery_1_player_id": None, "fumble_recovery_2_player_id": None,
        "fumble_forced": 0, "fumble_out_of_bounds": 0, "forced_fumble_player_1_player_id": None, "forced_fumble_player_2_player_id": None,
        "return_yards": 25, "return_team": "B", "kickoff_returner_player_id": "00-0000003", "lateral_kickoff_returner_player_id": None,
        "punt_returner_player_id": None, "lateral_punt_returner_player_id": None,
    }
    e4_pbp_path, e4_stats_path = root / "e4-pbp.csv.gz", root / "e4-stats.csv"
    e4_pbp.to_csv(e4_pbp_path, index=False, compression={"method": "gzip", "mtime": 0})
    pd.DataFrame([
        {"canonical_player_id": "QB1", "season": 2025, "week": 1, "position_model": "QB", "sacks": 1, "kickoff_return_yards": 0, "punt_return_yards": 0},
        {"canonical_player_id": "ST_REC", "season": 2025, "week": 1, "position_model": "WR", "sacks": 0, "kickoff_return_yards": 25, "punt_return_yards": 0},
    ]).to_csv(e4_stats_path, index=False)
    e4 = build_e4_event_ledger(
        raw_pbp_path=e4_pbp_path, identity_path=e3_identity_path, canonical_player_stats_path=e4_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "e" * 64}],
        output_path=root / "e4" / "events.csv.gz", weekly_stats_output_path=root / "e4" / "weekly.csv.gz", report_path=root / "e4" / "report.json",
    )
    assert e4["rule_support"]["kr_yd"]["support_status"] == "EXACT_EVENT_READY"
    assert e4["rule_support"]["pr_yd"]["support_status"] == "EXACT_EVENT_READY"
    assert e4["rule_support"]["fg_ret_yd"]["support_status"] == "BLOCKED_SOURCE_INCOMPLETE"
    e4_weekly = pd.read_csv(root / "e4" / "weekly.csv.gz").set_index("canonical_player_id")
    assert e4_weekly.loc["ST_REC", "event_kick_return_yards"] == 25
    e4_lateral = e4_pbp.copy()
    e4_lateral.loc[e4_lateral.play_id.eq(6), "lateral_kickoff_returner_player_id"] = "00-0000002"
    e4_lateral_path = root / "e4-lateral-pbp.csv.gz"
    e4_lateral.to_csv(e4_lateral_path, index=False, compression={"method": "gzip", "mtime": 0})
    lateral = build_e4_event_ledger(
        raw_pbp_path=e4_lateral_path, identity_path=e3_identity_path, canonical_player_stats_path=e4_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "f" * 64}],
        output_path=root / "e4-lateral" / "events.csv.gz", weekly_stats_output_path=root / "e4-lateral" / "weekly.csv.gz", report_path=root / "e4-lateral" / "report.json",
    )
    assert lateral["rule_support"]["kr_yd"]["support_status"] == "BLOCKED_EVENT_SEMANTICS"

    # E5 counts individual qualifying events, rather than awarding a single
    # weekly bonus from aggregate yards. A 55-yard passing touchdown therefore
    # stacks its completion, 40-yard TD and 50-yard TD counters; the analogous
    # rushing and receiving counters are independently attributed.
    e5_pbp = e4_pbp.copy()
    for column, value in {
        "complete_pass": 0, "passing_yards": 0, "pass_touchdown": 0,
        "receiver_player_id": None, "receiving_yards": 0,
        "lateral_receiver_player_id": None, "lateral_receiving_yards": 0,
        "rush_attempt": 0, "rushing_yards": 0,
        "lateral_rusher_player_id": None, "lateral_rushing_yards": 0,
        "two_point_attempt": 0,
    }.items():
        e5_pbp[column] = value
    e5_pbp.loc[len(e5_pbp)] = {
        "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 7, "season_type": "REG", "play_type": "pass", "play_deleted": 0,
        "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
        "interception": 0, "return_touchdown": 0, "passer_player_id": "00-0000001", "rush_touchdown": 0, "rusher_player_id": None,
        "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 55, "touchdown": 1, "special_teams_play": 0,
        "td_player_id": "00-0000003", "fumble_recovery_1_player_id": None, "fumble_recovery_2_player_id": None,
        "fumble_forced": 0, "fumble_out_of_bounds": 0, "forced_fumble_player_1_player_id": None, "forced_fumble_player_2_player_id": None,
        "return_yards": 0, "return_team": None, "kickoff_returner_player_id": None, "lateral_kickoff_returner_player_id": None,
        "punt_returner_player_id": None, "lateral_punt_returner_player_id": None,
        "complete_pass": 1, "passing_yards": 55, "pass_touchdown": 1, "receiver_player_id": "00-0000003", "receiving_yards": 55,
        "lateral_receiver_player_id": None, "lateral_receiving_yards": 0, "rush_attempt": 0, "rushing_yards": 0,
        "lateral_rusher_player_id": None, "lateral_rushing_yards": 0, "two_point_attempt": 0,
    }
    e5_pbp.loc[len(e5_pbp)] = {
        "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 8, "season_type": "REG", "play_type": "run", "play_deleted": 0,
        "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
        "interception": 0, "return_touchdown": 0, "passer_player_id": None, "rush_touchdown": 1, "rusher_player_id": "00-0000003",
        "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 51, "touchdown": 1, "special_teams_play": 0,
        "td_player_id": "00-0000003", "fumble_recovery_1_player_id": None, "fumble_recovery_2_player_id": None,
        "fumble_forced": 0, "fumble_out_of_bounds": 0, "forced_fumble_player_1_player_id": None, "forced_fumble_player_2_player_id": None,
        "return_yards": 0, "return_team": None, "kickoff_returner_player_id": None, "lateral_kickoff_returner_player_id": None,
        "punt_returner_player_id": None, "lateral_punt_returner_player_id": None,
        "complete_pass": 0, "passing_yards": 0, "pass_touchdown": 0, "receiver_player_id": None, "receiving_yards": 0,
        "lateral_receiver_player_id": None, "lateral_receiving_yards": 0, "rush_attempt": 1, "rushing_yards": 51,
        "lateral_rusher_player_id": None, "lateral_rushing_yards": 0, "two_point_attempt": 0,
    }
    # Two-point tries are deliberately excluded from long-play counters and
    # their null official rush yard field must not create a false blocker.
    e5_pbp.loc[len(e5_pbp)] = {
        "season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 9, "season_type": "REG", "play_type": "run", "play_deleted": 0,
        "fumble": 0, "fumble_lost": 0, "fumbled_1_player_id": None, "fumbled_2_player_id": None,
        "interception": 0, "return_touchdown": 0, "passer_player_id": None, "rush_touchdown": 0, "rusher_player_id": "00-0000003",
        "sack": 0, "posteam": "A", "defteam": "B", "yards_gained": 2, "touchdown": 0, "special_teams_play": 0,
        "fumble_forced": 0, "fumble_out_of_bounds": 0, "forced_fumble_player_1_player_id": None, "forced_fumble_player_2_player_id": None,
        "return_yards": 0, "return_team": None, "kickoff_returner_player_id": None, "lateral_kickoff_returner_player_id": None,
        "punt_returner_player_id": None, "lateral_punt_returner_player_id": None,
        "complete_pass": 0, "passing_yards": 0, "pass_touchdown": 0, "receiver_player_id": None, "receiving_yards": 0,
        "lateral_receiver_player_id": None, "lateral_receiving_yards": 0, "rush_attempt": 1, "rushing_yards": None,
        "lateral_rusher_player_id": None, "lateral_rushing_yards": None, "two_point_attempt": 1,
    }
    e5_pbp_path = root / "e5-pbp.csv.gz"
    e5_pbp.to_csv(e5_pbp_path, index=False, compression={"method": "gzip", "mtime": 0})
    e5 = build_e5_event_ledger(
        raw_pbp_path=e5_pbp_path, identity_path=e3_identity_path, canonical_player_stats_path=e4_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "g" * 64}],
        output_path=root / "e5" / "events.csv.gz", weekly_stats_output_path=root / "e5" / "weekly.csv.gz", report_path=root / "e5" / "report.json",
    )
    e5_rules = ("pass_cmp_40p", "pass_td_40p", "pass_td_50p", "rush_40p", "rush_td_40p", "rush_td_50p", "rec_40p", "rec_td_40p", "rec_td_50p")
    assert all(e5["rule_support"][key]["support_status"] == "EXACT_EVENT_READY" for key in e5_rules)
    e5_weekly = pd.read_csv(root / "e5" / "weekly.csv.gz").set_index("canonical_player_id")
    assert e5_weekly.loc["QB1", ["event_pass_completions_40", "event_pass_tds_40", "event_pass_tds_50"]].tolist() == [1, 1, 1]
    assert e5_weekly.loc["ST_REC", ["event_receptions_40", "event_reception_tds_40", "event_reception_tds_50", "event_rushes_40", "event_rush_tds_40", "event_rush_tds_50"]].tolist() == [1, 1, 1, 1, 1, 1]

    # A lost fumble with two different fumblers remains unassigned. The E5
    # receipt must retain its E2 play-level blocker, including phase and hash.
    ambiguous_pbp = e5_pbp.copy()
    ambiguous = ambiguous_pbp.iloc[0].copy()
    ambiguous["play_id"] = 10
    ambiguous["fumbled_2_player_id"] = "00-0000002"
    ambiguous_pbp = pd.concat([ambiguous_pbp, ambiguous.to_frame().T], ignore_index=True)
    ambiguous_path = root / "e5-ambiguous-pbp.csv.gz"
    ambiguous_pbp.to_csv(ambiguous_path, index=False, compression={"method": "gzip", "mtime": 0})
    ambiguous_report = root / "e5-ambiguous" / "report.json"
    ambiguous_receipt = build_e5_event_ledger(
        raw_pbp_path=ambiguous_path, identity_path=e3_identity_path, canonical_player_stats_path=e4_stats_path,
        requested_seasons=[2025], pbp_source_items=[{"season": 2025, "url": "https://example.test/pbp-2025.csv", "sha256": "h" * 64}],
        output_path=root / "e5-ambiguous" / "events.csv.gz", weekly_stats_output_path=root / "e5-ambiguous" / "weekly.csv.gz", report_path=ambiguous_report,
    )
    assert ambiguous_receipt["rule_support"]["fum_lost"]["support_status"] == "BLOCKED_EVENT_SEMANTICS"
    blocker_receipt = ambiguous_receipt["blockers"]
    assert blocker_receipt["phase_counts"]["E2"] >= 1 and blocker_receipt["season_counts"]["2025"] >= 1
    blocker_path = Path(blocker_receipt["path"])
    preserved = [json.loads(line) for line in blocker_path.read_text(encoding="utf-8").splitlines()]
    assert any(row["play_id"] == "10" and row["phase"] == "E2" for row in preserved)
    blocker_path.write_text(blocker_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    try:
        _blocker_receipt(ambiguous_report, [], "E6", ambiguous_receipt)
        raise AssertionError("changed prior blocker evidence must fail")
    except ValueError as error:
        assert "blocker ledger is missing or changed" in str(error)

print("OK waiver-v2 E1 event-source inventory and adversarial ledger contract")

#!/usr/bin/env python3
"""Adversarial E1 integrity checks for the Waiver-v2 shared event contract."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from waiver_v2_event_ledger import (
    EVENT_COLUMNS, EVENT_TYPES, build_e1_event_ledger, build_source_inventory,
    validate_event_ledger,
)
from run_waiver_v2_historical_ledger import write_source_snapshot


def source_rows() -> pd.DataFrame:
    return pd.DataFrame([
        {"season": 2024, "week": 1, "game_id": "2024_01_A_B", "play_id": 10, "season_type": "REG", "play_type": "pass", "no_play": 0},
        {"season": 2025, "week": 1, "game_id": "2025_01_A_B", "play_id": 11, "season_type": "REG", "play_type": "kickoff", "no_play": 0},
        # Postseason rows cannot prove the completed regular-season envelope.
        {"season": 2025, "week": 19, "game_id": "2025_wc_A_B", "play_id": 12, "season_type": "POST", "play_type": "punt", "no_play": 0},
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

    missing = pbp.drop(columns=["no_play"])
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
    no_play["no_play"] = False
    no_play.loc[0, "no_play"] = True
    try:
        validate_event_ledger(no_play)
        raise AssertionError("penalty/no-play event must fail")
    except ValueError as error:
        assert "penalty/no-play" in str(error)

    snapshot = write_source_snapshot(
        players=pd.DataFrame([{"gsis_id": "p1"}]),
        player_stats_frames=[pd.DataFrame([{"season": 2025, "week": 1}])],
        weekly_roster_frames=[pd.DataFrame([{"season": 2025, "week": 1}])],
        games=pd.DataFrame([{"season": 2025, "week": 1}]), identity=pd.DataFrame([{"gsis_id": "p1"}]),
        raw_dir=root / "snapshot", pbp_frames=[pbp], participation_frames=[pd.DataFrame([{"game_id": "2025_01_A_B"}])],
    )
    assert {"pbp", "participation"} <= set(snapshot)
    assert snapshot["pbp"]["rows"] == len(pbp)

print("OK waiver-v2 E1 event-source inventory and adversarial ledger contract")

#!/usr/bin/env python3
"""No-network proof for canonical M10 roster mapping and exact assignments."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from capture_m10_prospective_weekly_raw import (
    ROOT, _league_roster_state, attach_sleeper_identity, normalize_sleeper_id,
)
from in_season_pr2_weekly_lineups import current_snapshot
from m10_prospective_operational_capture import validate_decisions
from m10_prospective_weekly_producer import MODELS, build_decision_traces


def repository_identity() -> dict:
    registry = json.loads((ROOT / "data/research/leagues/registry.json").read_text(encoding="utf-8"))
    players = []
    for league_id, entry in registry["leagues"].items():
        if entry.get("enabled") is not True:
            continue
        current = current_snapshot(ROOT / f"data/research/leagues/{league_id}/current/milestone5_current.json", ROOT)
        players.extend(row for row in current.get("players") or [] if row.get("sleeper_id") and row.get("canonical_player_id"))
    return {"players": players}


def mapping_checks() -> None:
    assert normalize_sleeper_id("10859.0") == "10859"
    assert normalize_sleeper_id("alpha.0") == "alpha.0"
    identity = {"players": [{"canonical_player_id": "00-1", "sleeper_id": None}]}
    catalog = pd.DataFrame([{"gsis_id": "00-1", "sleeper_id": 10859.0, "position": "TE", "full_name": "Fixture"}])
    attached = attach_sleeper_identity(identity, catalog)
    assert attached["players"][0]["sleeper_id"] == "10859"
    ambiguous = attach_sleeper_identity(
        {"players": [{"canonical_player_id": "00-1", "sleeper_id": None}]},
        pd.DataFrame([
            {"gsis_id": "00-1", "sleeper_id": 10859.0, "position": "TE", "full_name": "Fixture"},
            {"gsis_id": "00-1", "sleeper_id": 20859.0, "position": "TE", "full_name": "Fixture"},
        ]),
    )
    assert ambiguous["players"][0]["sleeper_id"] is None and ambiguous["sleeper_identity_ambiguous"] == 1

    registry = json.loads((ROOT / "data/research/leagues/registry.json").read_text(encoding="utf-8"))["leagues"]
    portfolio = json.loads((ROOT / "config/league-portfolio.json").read_text(encoding="utf-8"))
    username = portfolio["sleeper_username"]
    live_identity = repository_identity()
    league_id = "1387106650413887488"  # Complete mapping plus K/D/ST exclusions.
    # Bind repository-backed fixtures to their snapshots, so weekly rollover
    # exercises the guards without turning a valid refresh into a failure.
    current = current_snapshot(ROOT / f"data/research/leagues/{league_id}/current/milestone5_current.json", ROOT)
    season, week = int(current["season"]), int(current["week"])
    assert season > 0 and week > 0
    ready = _league_roster_state(ROOT, league_id, registry[league_id], live_identity, season=season, week=week, username=username)
    assert ready["complete"] is True and ready["legal_canonical_player_ids"]
    assert ready["excluded_non_m10_starter_slots"] == ["K", "DEF"]
    assert ready["m10_roster_positions"] == ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]
    assert len(ready["runtime_contract_sha256"]) == 64

    stale = _league_roster_state(ROOT, league_id, registry[league_id], live_identity, season=season, week=week + 1, username=username)
    assert stale["blocker"] == "CURRENT_SNAPSHOT_SEASON_WEEK_MISMATCH"
    drifted = {**registry[league_id], "profile_fingerprint": "0" * 64}
    drift = _league_roster_state(ROOT, league_id, drifted, live_identity, season=season, week=week, username=username)
    assert drift["blocker"] == "PROFILE_BINDING_MISMATCH_AT_CUTOFF"
    # Remove one offensive binding, not a deliberately excluded K/D/ST row.
    missing_id = next(
        normalize_sleeper_id(row["sleeper_id"])
        for row in live_identity["players"]
        if str(row.get("canonical_player_id")) in set(ready["legal_canonical_player_ids"])
    )
    missing = {"players": [row for row in live_identity["players"] if normalize_sleeper_id(row.get("sleeper_id")) != missing_id]}
    unresolved = _league_roster_state(ROOT, league_id, registry[league_id], missing, season=season, week=week, username=username)
    assert unresolved["blocker"] == "M10_ROSTER_IDENTITY_UNRESOLVED_AT_CUTOFF"

    empty_id = "1400561646463672320"
    empty_current = current_snapshot(ROOT / f"data/research/leagues/{empty_id}/current/milestone5_current.json", ROOT)
    empty = _league_roster_state(ROOT, empty_id, registry[empty_id], live_identity, season=int(empty_current["season"]), week=int(empty_current["week"]), username=username)
    assert empty["blocker"] == "MANAGED_ROSTER_EMPTY_AT_CUTOFF"


def scoring_rows(league_id: str, values: dict[str, tuple[str, float, float]]) -> list[dict]:
    rows = []
    for model in MODELS:
        for canonical_id, (position, mean, p10) in values.items():
            rows.append({
                "forecast_id": f"forecast-{canonical_id}", "canonical_player_id": canonical_id,
                "position_model": position, "model": model, "league_id": league_id,
                "scored_fantasy_points": mean,
                "scored_prediction_quantiles": {"0.1": p10, "0.5": mean},
            })
    return rows


def exact_assignment_checks() -> None:
    capture = {"season": 2026, "week": 4, "captured_at": "2026-10-04T11:00:00+00:00"}
    profile = {"league_id": "fixture", "league_format": "REDRAFT", "profile_fingerprint": "f" * 64}
    state = {
        "league_id": "fixture", "complete": True,
        "m10_roster_positions": ["FLEX", "WR"], "excluded_non_m10_starter_slots": ["K"],
        "legal_canonical_player_ids": ["wr", "rb"],
    }
    # A greedy FLEX-first assignment would consume WR and leave the WR slot
    # empty. The exact solver must place RB in FLEX and WR in WR.
    rows = build_decision_traces([profile], [state], scoring_rows("fixture", {
        "wr": ("WR", 20.0, 10.0), "rb": ("RB", 19.0, 9.0),
    }), capture=capture)
    assert len(rows) == len(MODELS) and all(row["status"] == "CAPTURED" for row in rows)
    assert all([item["canonical_player_id"] for item in row["lineup_assignment"]] == ["rb", "wr"] for row in rows)
    assert all(row["assignment_method"] == "canonical_exact_hungarian" for row in rows)
    assert all(row["decision_scope"] == "QB_RB_WR_TE_STARTER_SLOTS_ONLY" for row in rows)
    validate_decisions(rows, {"forecast-wr", "forecast-rb"})

    superflex = {**state, "m10_roster_positions": ["QB", "SUPER_FLEX"], "legal_canonical_player_ids": ["qb", "rb", "wr"]}
    super_rows = build_decision_traces([profile], [superflex], scoring_rows("fixture", {
        "qb": ("QB", 20.0, 12.0), "rb": ("RB", 19.0, 11.0), "wr": ("WR", 18.0, 10.0),
    }), capture=capture)
    assert all({item["canonical_player_id"] for item in row["lineup_assignment"]} == {"qb", "rb"} for row in super_rows)

    # One RB cannot fill FLEX + WR. Every model must receive the same typed
    # blocker; no partial decision or asymmetric model cohort is allowed.
    blocked = build_decision_traces([profile], [{**state, "legal_canonical_player_ids": ["rb"]}], scoring_rows("fixture", {
        "rb": ("RB", 5.0, -2.0),
    }), capture=capture)
    assert len(blocked) == len(MODELS)
    assert all(row["status"] == "BLOCKED_INCOMPLETE_LEGAL_ROSTER" for row in blocked)
    validate_decisions(blocked, {"forecast-rb"})


def main() -> None:
    mapping_checks()
    exact_assignment_checks()
    print("PASS M10 canonical roster mapping, offensive-scope exclusions, and exact legal assignment")


if __name__ == "__main__":
    main()

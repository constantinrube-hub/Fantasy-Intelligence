#!/usr/bin/env python3
"""Focused no-network integrity tests for the In-Season PR2 exact solver."""
from __future__ import annotations

from weekly_lineup_decision_support import (
    LineupEvidenceError,
    exact_lineup,
    load_runtime_contract,
)


def player(pid: str, pos: str, value: float | None, **extra):
    return {"sleeper_id": pid, "position_model": pos, "decision_weekly_projection": value, **extra}


def selected_by_slot(result):
    return {row["slot_index"]: row["player_id"] for row in result["assignment"]}


def test_exact_flex_assignment_beats_greedy_pairing():
    # Greedy slot-by-slot would put RB a in RB, leaving WR c for FLEX (38).
    # Exact assignment correctly uses RB b in RB and RB a in FLEX (39).
    result = exact_lineup(
        [player("a", "RB", 20), player("b", "RB", 19), player("c", "WR", 18)],
        ["RB", "FLEX", "BN"],
    )
    assert result["complete_assignment"]
    assert result["total"] == 39
    assert set(result["selected_player_ids"]) == {"sleeper:a", "sleeper:b"}


def test_superflex_and_no_double_assignment():
    result = exact_lineup(
        [player("q", "QB", 24), player("r", "RB", 18), player("w", "WR", 17)],
        ["QB", "SUPER_FLEX", "FLEX", "BN"],
    )
    assert result["complete_assignment"]
    assert result["total"] == 59
    assert len(result["selected_player_ids"]) == len(set(result["selected_player_ids"])) == 3
    assert selected_by_slot(result) == {0: "sleeper:q", 1: "sleeper:r", 2: "sleeper:w"}


def test_idp_kicker_and_team_defense_aliases():
    result = exact_lineup(
        [
            player("edge", "EDGE", 9),
            player("safety", "S", 8),
            player("k", "K", 7),
            {"position_model": "DST", "team": "BUF", "decision_weekly_projection": 6},
        ],
        ["IDP_FLEX", "K", "DST", "BN"],
    )
    assert result["complete_assignment"]
    assert result["total"] == 22
    assert {row["position"] for row in result["assignment"]} == {"DL", "K", "DEF"}
    assert "teamdef:BUF" in result["selected_player_ids"]


def test_missing_value_is_never_zero_imputed():
    result = exact_lineup([player("q", "QB", None)], ["QB", "BN"])
    assert result["complete_assignment"] is False
    assert result["total"] == 0
    assert result["missing_value_player_ids"] == ["sleeper:q"]
    assert result["unfilled_slots"] == [{"slot": "QB", "slot_index": 0}]


def test_verified_slot_and_bench_locks_constrain_the_global_solver():
    result = exact_lineup(
        [player("a", "RB", 20), player("b", "RB", 19), player("c", "WR", 18)],
        ["RB", "FLEX", "BN"],
        locked_slot_player_ids={0: "sleeper:b"},
        locked_bench_player_ids=["sleeper:a"],
    )
    assert result["complete_assignment"]
    assert selected_by_slot(result) == {0: "sleeper:b", 1: "sleeper:c"}
    assert result["locks"]["locked_bench_player_ids"] == ["sleeper:a"]


def test_interval_advisory_ties_break_by_primary_mean():
    result = exact_lineup(
        [player("a", "RB", 10, p10=5), player("b", "RB", 12, p10=5)],
        ["RB", "BN"],
        value_key="p10",
        tie_break_value_key="decision_weekly_projection",
    )
    assert selected_by_slot(result) == {0: "sleeper:b"}


def test_unknown_slot_fails_closed():
    try:
        exact_lineup([player("q", "QB", 12)], ["QB", "FAKE_SLOT"])
    except LineupEvidenceError as exc:
        assert str(exc) == "BLOCKED_UNKNOWN_ROSTER_SLOT:FAKE_SLOT"
    else:  # pragma: no cover - assertion control flow
        raise AssertionError("unknown roster slot did not block")


def test_runtime_contract_is_the_only_slot_owner():
    contract, digest = load_runtime_contract()
    assert digest and contract["roster_slots"]["SUPER_FLEX"]["positions"] == ["QB", "RB", "WR", "TE"]
    text = open(__file__.replace("integrity_weekly_lineup_exact_solver_test.py", "weekly_lineup_decision_support.py"), encoding="utf-8").read()
    assert '"SUPER_FLEX"' not in text
    assert '"IDP_FLEX"' not in text


def main() -> None:
    tests = [
        test_exact_flex_assignment_beats_greedy_pairing,
        test_superflex_and_no_double_assignment,
        test_idp_kicker_and_team_defense_aliases,
        test_missing_value_is_never_zero_imputed,
        test_verified_slot_and_bench_locks_constrain_the_global_solver,
        test_interval_advisory_ties_break_by_primary_mean,
        test_unknown_slot_fails_closed,
        test_runtime_contract_is_the_only_slot_owner,
    ]
    for test in tests:
        test()
    print(f"PASS In-Season PR2 exact lineup solver ({len(tests)} tests)")


if __name__ == "__main__":
    main()

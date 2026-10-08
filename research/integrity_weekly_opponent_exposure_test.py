#!/usr/bin/env python3
"""Observed opponent starters remain capture-bound and separate from advice."""
from __future__ import annotations

from copy import deepcopy

from weekly_opponent_exposure import captured_exposure

CAPTURE = {"capture_id": "abc", "capture_sha256": "a" * 64, "capture_path": "lineups/captures/portfolio-abc.json"}
NOW = "2026-10-08T12:00:00+00:00"


def fixtures() -> tuple[dict, dict]:
    player = {"player_id": "gsis-1", "player_name": "One", "team": "AAA", "position": "WR",
              "sleeper_id": "123", "owned_by_user": False, "rostered_in_league": True,
              "fie_mean": None, "sleeper_mean": 12.0}
    current = {"season": 2026, "week": 5, "as_of_utc": NOW, "leagues": [
        {"league_id": lid, "status": "BOUND_CURRENT_ROSTER", "active_operational_scope": True,
         "scoring_signature": "score", "profile_fingerprint": "profile", "players": [deepcopy(player)]}
        for lid in ("h2h-a", "h2h-b", "chopped")
    ]}
    opponent = {"status": "CAPTURED_H2H_CONTEXT", "captured_at": "2026-10-08T10:00:00+00:00",
                "matchup_id": "7", "opponent_roster_id": 2,
                "opponent_submitted_starters": {"status": "CAPTURED_SUBMITTED_STARTER_IDS",
                                                 "player_id_namespace": "sleeper", "player_ids": ["123"]},
                "opponent_lineup": {"status": "EXACT_MAX_MEAN_ADVISORY", "selected_player_ids": ["different-id"]}}
    pr2 = {"season": 2026, "week": 5, "leagues": [
        {"league_id": lid, "league_name": lid, "format": "CHOPPED" if lid == "chopped" else "REDRAFT",
         "season": 2026, "week": 5, "evidence": {"scoring_signature": "score", "profile_fingerprint": "profile"},
         "opponent_context": deepcopy(opponent)} for lid in ("h2h-a", "h2h-b", "chopped")
    ]}
    return pr2, current


def main() -> None:
    pr2, current = fixtures()
    result = captured_exposure(pr2, current, CAPTURE)
    assert result["players"][0]["opponent_start_league_count"] == 2
    assert result["players"][0]["contexts"][0]["capture_id"] == "abc"
    assert result["players"][0]["contexts"][0]["scoring_signature"] == "score"
    assert result["league_status_counts"] == {"CAPTURED_SUBMITTED_STARTERS": 2, "BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED": 1}
    assert result["players"][0]["player_id"] == "gsis-1"  # Max-mean advisory's different ID cannot leak.
    assert result["governance"]["actionable"] is False
    field = {"status": "CAPTURED_FIELD_ROWS_ACTIVE_UNVERIFIED", "evidence_sha256": "field-hash",
             "captured_at": "2026-10-08T10:00:00+00:00", "active_field_certified": False,
             "rosters": [{"roster_id": "2", "player_ids": ["123"], "status": "CAPTURED_SUBMITTED_STARTERS"}]}
    captured = deepcopy(pr2)
    captured["leagues"][2]["field_context"] = field
    captured["leagues"][2]["evidence"]["matchup_evidence_sha256"] = "field-hash"
    result = captured_exposure(captured, current, CAPTURE)
    assert result["players"][0]["opponent_start_league_count"] == 2
    assert result["field_players"][0]["observed_field_roster_count"] == 1
    assert result["field_players"][0]["observed_field_league_count"] == 1
    assert result["leagues"][2]["status"] == "PARTIAL_MATCHUP_FIELD_ACTIVE_UNVERIFIED"
    assert result["leagues"][2]["active_field_certified"] is False
    broken = deepcopy(captured); broken["leagues"][2]["evidence"]["matchup_evidence_sha256"] = "tampered"
    assert captured_exposure(broken, current, CAPTURE)["leagues"][2]["status"] == "BLOCKED_FIELD_EVIDENCE_HASH_MISMATCH"
    broken = deepcopy(captured); broken["leagues"][2]["field_context"]["captured_at"] = "2026-10-08T13:00:00+00:00"
    assert captured_exposure(broken, current, CAPTURE)["leagues"][2]["status"] == "BLOCKED_FIELD_CAPTURE_AFTER_SURFACE"
    broken = deepcopy(captured); broken["leagues"][2]["field_context"]["rosters"].append(deepcopy(field["rosters"][0]))
    assert captured_exposure(broken, current, CAPTURE)["leagues"][2]["status"] == "BLOCKED_FIELD_ROSTER_SCOPE_INVALID"
    bestball = deepcopy(pr2); bestball["leagues"][2]["format"] = "CHOPPED_BESTBALL"
    result = captured_exposure(bestball, current, CAPTURE)
    assert result["leagues"][2]["kind"] == "CHOPPED_FIELD"
    assert result["league_status_counts"]["BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED"] == 1

    altered = deepcopy(pr2); altered["leagues"][0]["opponent_context"]["opponent_submitted_starters"]["player_ids"] = ["missing"]
    result = captured_exposure(altered, current, CAPTURE)
    assert result["league_status_counts"]["PARTIAL_UNRESOLVED_SUBMITTED_STARTERS"] == 1
    assert result["players"][0]["opponent_start_league_count"] == 1
    altered = deepcopy(pr2); altered["leagues"][0]["evidence"]["profile_fingerprint"] = "other"
    result = captured_exposure(altered, current, CAPTURE)
    assert result["league_status_counts"]["BLOCKED_PROFILE_OR_TARGET_MISMATCH"] == 1
    assert result["players"][0]["opponent_start_league_count"] == 1
    altered = deepcopy(pr2); altered["leagues"][0]["opponent_context"]["captured_at"] = "2026-10-08T13:00:00+00:00"
    assert captured_exposure(altered,current,CAPTURE)["league_status_counts"]["BLOCKED_MATCHUP_CAPTURE_AFTER_SURFACE"] == 1
    altered = deepcopy(pr2); altered["leagues"][0]["opponent_context"]["opponent_submitted_starters"]["player_ids"] = ["123","123"]
    assert captured_exposure(altered,current,CAPTURE)["league_status_counts"]["BLOCKED_OPPONENT_SUBMITTED_IDS_INVALID"] == 1
    altered = deepcopy(current); altered["leagues"][0]["active_operational_scope"] = False
    assert captured_exposure(pr2,altered,CAPTURE)["league_status_counts"]["NOT_APPLICABLE_RESEARCH_ONLY_LEAGUE"] == 1
    altered = deepcopy(current); altered["leagues"][0]["players"][0]["owned_by_user"] = True
    assert captured_exposure(pr2,altered,CAPTURE)["players"][0]["opponent_start_league_count"] == 1
    try:
        captured_exposure(pr2,current,{})
    except ValueError as exc:
        assert "CAPTURE_UNVERIFIED" in str(exc)
    else:
        raise AssertionError("unbound PR2 capture accepted")
    print("PASS opponent exposure: submitted identity, scoring and time binding, Chopped/research isolation, advisory separation")


if __name__ == "__main__":
    main()

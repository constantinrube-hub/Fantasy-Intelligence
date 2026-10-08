#!/usr/bin/env python3
"""Read-only opponent starter exposure from immutable PR2 and current portfolio.

Only observed submitted Sleeper IDs join to the current canonical player view.
The opponent's max-mean advisory is never a submitted lineup or action.
"""
from __future__ import annotations

from collections import Counter

from weekly_evidence_audit import stamp


def captured_exposure(pr2: dict, surface: dict, capture_binding: dict) -> dict:
    season, week = surface["season"], surface["week"]
    if (pr2.get("season", season), pr2.get("week", week)) != (season, week):
        raise ValueError("OPPONENT_EXPOSURE_TARGET_MISMATCH")
    if not capture_binding.get("capture_sha256") or not capture_binding.get("capture_id"):
        raise ValueError("OPPONENT_EXPOSURE_CAPTURE_UNVERIFIED")
    current_at = stamp(surface["as_of_utc"])
    indexed = {str(row["league_id"]): row for row in surface["leagues"]}
    if len(indexed) != len(surface["leagues"]):
        raise ValueError("OPPONENT_EXPOSURE_DUPLICATE_SURFACE_LEAGUE")
    league_rows = []
    exposure: dict[str, dict] = {}
    for league in pr2["leagues"]:
        lid = str(league["league_id"])
        current = indexed.get(lid)
        base = {"league_id": lid, "league_name": league.get("league_name"), "season": season, "week": week,
                "kind": "CHOPPED_FIELD" if league.get("format") in {"CHOPPED", "CHOPPED_BESTBALL"} else "DIRECT_H2H",
                "capture_id": capture_binding["capture_id"], "capture_sha256": capture_binding["capture_sha256"],
                "actionable": False}
        if current is None or current.get("status") not in {"BOUND_CURRENT_ROSTER", "PARTIAL_UNRESOLVED_PLAYERS"}:
            league_rows.append({**base, "status": "BLOCKED_CURRENT_LEAGUE_UNBOUND", "players": []})
            continue
        if not current.get("active_operational_scope"):
            league_rows.append({**base, "status": "NOT_APPLICABLE_RESEARCH_ONLY_LEAGUE", "players": []})
            continue
        if base["kind"] == "CHOPPED_FIELD":
            league_rows.append({**base, "status": "BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED", "players": []})
            continue
        evidence = league.get("evidence") or {}
        if ((league.get("season"), league.get("week")) != (season, week) or
            not evidence.get("scoring_signature") or not evidence.get("profile_fingerprint") or
            evidence["scoring_signature"] != current.get("scoring_signature") or
            evidence["profile_fingerprint"] != current.get("profile_fingerprint")):
            league_rows.append({**base, "status": "BLOCKED_PROFILE_OR_TARGET_MISMATCH", "players": []})
            continue
        opponent = league.get("opponent_context") or {}
        if opponent.get("status") != "CAPTURED_H2H_CONTEXT":
            league_rows.append({**base, "status": opponent.get("status", "BLOCKED_MATCHUP_CAPTURE_REQUIRED"), "players": []})
            continue
        observed = opponent.get("captured_at")
        if not observed or stamp(observed) > current_at:
            league_rows.append({**base, "status": "BLOCKED_MATCHUP_CAPTURE_AFTER_SURFACE", "players": []})
            continue
        submitted = opponent.get("opponent_submitted_starters") or {}
        if submitted.get("status") != "CAPTURED_SUBMITTED_STARTER_IDS" or submitted.get("player_id_namespace") != "sleeper":
            league_rows.append({**base, "status": "BLOCKED_OPPONENT_SUBMITTED_STARTERS_UNAVAILABLE", "players": []})
            continue
        ids = submitted.get("player_ids")
        if not isinstance(ids, list) or not ids or any(not isinstance(pid, str) or not pid for pid in ids) or len(set(ids)) != len(ids):
            league_rows.append({**base, "status": "BLOCKED_OPPONENT_SUBMITTED_IDS_INVALID", "players": []})
            continue
        player_index = {}
        duplicates = set()
        for player in current["players"]:
            pid = player.get("sleeper_id")
            if pid:
                if pid in player_index: duplicates.add(pid)
                player_index[pid] = player
        if duplicates:
            league_rows.append({**base, "status": "BLOCKED_CURRENT_DUPLICATE_SLEEPER_ID", "players": [], "duplicate_sleeper_ids": sorted(duplicates)})
            continue
        players, unresolved = [], []
        for pid in ids:
            player = player_index.get(pid)
            if (player is None or not player.get("player_id") or
                player.get("owned_by_user") or not player.get("rostered_in_league")):
                unresolved.append(pid)
            else:
                players.append({"player_id": player["player_id"], "player_name": player.get("player_name"),
                                "team": player.get("team"), "position": player.get("position"),
                                "sleeper_id": pid, "fie_mean": player.get("fie_mean"),
                                "sleeper_mean": player.get("sleeper_mean")})
        status = "CAPTURED_SUBMITTED_STARTERS" if not unresolved else "PARTIAL_UNRESOLVED_SUBMITTED_STARTERS"
        league_rows.append({**base, "status": status, "opponent_roster_id": opponent.get("opponent_roster_id"),
                            "matchup_id": opponent.get("matchup_id"), "observed_at": observed,
                            "scoring_signature": current["scoring_signature"], "profile_fingerprint": current["profile_fingerprint"],
                            "players": players, "unresolved_sleeper_ids": sorted(unresolved),
                            "submitted_starter_count": len(ids)})
        for player in players:
            record = exposure.setdefault(player["player_id"], {"player_id": player["player_id"],
                "player_name": player["player_name"], "team": player["team"], "position": player["position"], "contexts": []})
            record["contexts"].append({"league_id": lid, "league_name": league.get("league_name"),
                                       "scoring_signature": current["scoring_signature"], "profile_fingerprint": current["profile_fingerprint"],
                                       "capture_id": capture_binding["capture_id"], "observed_at": observed})
    for record in exposure.values():
        record["opponent_start_league_count"] = len(record["contexts"])
    return {"schema": "fie-captured-opponent-exposure-v1", "season": season, "week": week,
        "surface_as_of_utc": surface["as_of_utc"], "capture_path": capture_binding["capture_path"],
        "capture_sha256": capture_binding["capture_sha256"], "capture_id": capture_binding["capture_id"],
        "leagues": league_rows, "players": sorted(exposure.values(), key=lambda row: (-row["opponent_start_league_count"], str(row["player_id"]))),
        "league_status_counts": dict(Counter(row["status"] for row in league_rows)),
        "semantics": "Observed submitted opponent starters at the PR2 capture time; not a final lineup, predicted intention, Chopped-field exposure, or recommendation.",
        "governance": {"read_only": True, "actionable": False, "opponent_lineup_advisory_used": False}}

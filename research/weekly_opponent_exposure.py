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
    field_exposure: dict[str, dict] = {}
    not_eliminated_exposure: dict[str, dict] = {}
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
        evidence = league.get("evidence") or {}
        if ((league.get("season"), league.get("week")) != (season, week) or
            not evidence.get("scoring_signature") or not evidence.get("profile_fingerprint") or
            evidence["scoring_signature"] != current.get("scoring_signature") or
            evidence["profile_fingerprint"] != current.get("profile_fingerprint")):
            league_rows.append({**base, "status": "BLOCKED_PROFILE_OR_TARGET_MISMATCH", "players": []})
            continue
        if base["kind"] == "CHOPPED_FIELD":
            field = league.get("field_context") or {}
            certified = field.get("status") == "CAPTURED_PROVIDER_NOT_ELIMINATED_FIELD"
            if field.get("status") not in {"CAPTURED_FIELD_ROWS_ACTIVE_UNVERIFIED", "PARTIAL_FIELD_STARTERS_ACTIVE_UNVERIFIED", "CAPTURED_PROVIDER_NOT_ELIMINATED_FIELD"}:
                league_rows.append({**base, "status": field.get("status", "BLOCKED_CAPTURED_ACTIVE_FIELD_REQUIRED"), "players": []})
                continue
            if not field.get("evidence_sha256") or field["evidence_sha256"] != evidence.get("matchup_evidence_sha256"):
                league_rows.append({**base, "status": "BLOCKED_FIELD_EVIDENCE_HASH_MISMATCH", "players": []})
                continue
            observed = field.get("captured_at")
            if not observed or stamp(observed) > current_at:
                league_rows.append({**base, "status": "BLOCKED_FIELD_CAPTURE_AFTER_SURFACE", "players": []})
                continue
            rosters = field.get("rosters")
            ids = [str(row.get("roster_id") or "") for row in rosters] if isinstance(rosters, list) and all(isinstance(row, dict) for row in rosters) else []
            if not ids or not all(ids) or len(set(ids)) != len(ids) or field.get("active_field_certified") is not certified:
                league_rows.append({**base, "status": "BLOCKED_FIELD_ROSTER_SCOPE_INVALID", "players": []})
                continue
            if certified:
                source_at = field.get("elimination_source_observed_at")
                try:
                    source_time = stamp(source_at) if source_at else None
                except (ValueError, TypeError, AttributeError):
                    source_time = None
                if (field.get("elimination_source_core_sha256") != evidence.get("app_core_sha256") or
                    not evidence.get("app_core_sha256") or field.get("last_completed_chopped_leg") != week - 1 or
                    source_time is None or source_time > stamp(observed) or
                    (stamp(observed) - source_time).total_seconds() > 6 * 3600):
                    league_rows.append({**base, "status": "BLOCKED_FIELD_ELIMINATION_SOURCE_MISMATCH", "players": []})
                    continue
                states = [row.get("provider_elimination_state") for row in rosters]
                count = states.count("NOT_MARKED_ELIMINATED")
                if (set(states) - {"NOT_MARKED_ELIMINATED", "ELIMINATED"} or
                    count != field.get("not_eliminated_roster_count") or
                    states.count("ELIMINATED") != field.get("eliminated_matchup_roster_count") or count == 0):
                    league_rows.append({**base, "status": "BLOCKED_FIELD_ELIMINATION_SCOPE_INVALID", "players": []})
                    continue
            player_index = {str(row.get("sleeper_id")): row for row in current["players"] if row.get("sleeper_id")}
            if len(player_index) != sum(bool(row.get("sleeper_id")) for row in current["players"]):
                league_rows.append({**base, "status": "BLOCKED_CURRENT_DUPLICATE_SLEEPER_ID", "players": []})
                continue
            entries, not_eliminated_entries, unresolved, submitted_ids = [], [], [], set()
            invalid = False
            for roster in rosters:
                pids = roster.get("player_ids")
                if not isinstance(pids, list) or any(not isinstance(pid, str) or not pid for pid in pids) or len(set(pids)) != len(pids) or submitted_ids.intersection(pids):
                    invalid = True
                    break
                submitted_ids.update(pids)
                for pid in pids:
                    player = player_index.get(pid)
                    if not player or not player.get("player_id") or player.get("owned_by_user") or not player.get("rostered_in_league"):
                        unresolved.append({"roster_id": roster["roster_id"], "sleeper_id": pid})
                    else:
                        entry = {"roster_id": roster["roster_id"], "sleeper_id": pid,
                                        "player_id": player["player_id"], "player_name": player.get("player_name"),
                                        "position": player.get("position")}
                        entries.append(entry)
                        if certified and roster["provider_elimination_state"] == "NOT_MARKED_ELIMINATED":
                            not_eliminated_entries.append(entry)
            if invalid:
                league_rows.append({**base, "status": "BLOCKED_FIELD_SUBMITTED_IDS_INVALID", "players": []})
                continue
            active_unresolved = any(row["roster_id"] in {r["roster_id"] for r in rosters if r.get("provider_elimination_state") == "NOT_MARKED_ELIMINATED"} for row in unresolved)
            status = ("CAPTURED_PROVIDER_NOT_ELIMINATED_FIELD" if certified and not active_unresolved and
                      all(row.get("status") == "CAPTURED_SUBMITTED_STARTERS" for row in rosters if row.get("provider_elimination_state") == "NOT_MARKED_ELIMINATED")
                      else "PARTIAL_PROVIDER_NOT_ELIMINATED_FIELD" if certified else
                      "PARTIAL_MATCHUP_FIELD_ACTIVE_UNVERIFIED" if submitted_ids else "BLOCKED_FIELD_STARTERS_UNAVAILABLE")
            league_rows.append({**base, "status": status,
                                "observed_at": observed, "observed_roster_count": len(rosters),
                                "submitted_starter_count": len(submitted_ids), "players": entries,
                                "not_eliminated_field_players": not_eliminated_entries,
                                "not_eliminated_roster_count": field.get("not_eliminated_roster_count", 0),
                                "unresolved_sleeper_ids": unresolved,
                                "active_field_certified": certified, "roster_membership_certified": certified})
            for entry in entries:
                record = field_exposure.setdefault(entry["player_id"], {"player_id": entry["player_id"],
                    "player_name": entry["player_name"], "position": entry["position"], "contexts": []})
                record["contexts"].append({"league_id": lid, "roster_id": entry["roster_id"],
                    "capture_id": capture_binding["capture_id"], "observed_at": observed,
                    "scoring_signature": current["scoring_signature"], "profile_fingerprint": current["profile_fingerprint"]})
            for entry in not_eliminated_entries:
                record = not_eliminated_exposure.setdefault(entry["player_id"], {"player_id": entry["player_id"],
                    "player_name": entry["player_name"], "position": entry["position"], "contexts": []})
                record["contexts"].append({"league_id": lid, "roster_id": entry["roster_id"],
                    "capture_id": capture_binding["capture_id"], "observed_at": observed,
                    "app_core_sha256": evidence["app_core_sha256"]})
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
    for record in field_exposure.values():
        record["observed_field_roster_count"] = len(record["contexts"])
        record["observed_field_league_count"] = len({row["league_id"] for row in record["contexts"]})
    for record in not_eliminated_exposure.values():
        record["not_eliminated_field_roster_count"] = len(record["contexts"])
        record["not_eliminated_field_league_count"] = len({row["league_id"] for row in record["contexts"]})
    return {"schema": "fie-captured-opponent-exposure-v1", "season": season, "week": week,
        "surface_as_of_utc": surface["as_of_utc"], "capture_path": capture_binding["capture_path"],
        "capture_sha256": capture_binding["capture_sha256"], "capture_id": capture_binding["capture_id"],
        "leagues": league_rows, "players": sorted(exposure.values(), key=lambda row: (-row["opponent_start_league_count"], str(row["player_id"]))),
        "field_players": sorted(field_exposure.values(), key=lambda row: (-row["observed_field_league_count"], str(row["player_id"]))),
        "not_eliminated_field_players": sorted(not_eliminated_exposure.values(), key=lambda row: (-row["not_eliminated_field_league_count"], str(row["player_id"]))),
        "league_status_counts": dict(Counter(row["status"] for row in league_rows)),
        "semantics": "Direct H2H submitted opponents, raw Chopped matchup rows, and separately source-bound provider not-eliminated roster starters at PR2 capture time. Future survivors and final Best Ball lineups are not certified; no recommendation or predicted intention.",
        "governance": {"read_only": True, "actionable": False, "opponent_lineup_advisory_used": False}}

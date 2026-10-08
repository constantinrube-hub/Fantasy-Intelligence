"""Explain the evidence still needed by each weekly product without certifying it."""
from collections import Counter


def _counts(rows):
    return dict(sorted(Counter(str(row.get("status") or "UNKNOWN") for row in rows).items()))


def assess(products: dict, sources: dict) -> None:
    """Attach read-only diagnostics to the already validated owner outputs.

    A current source is necessary, but a report's complete contract also needs
    product-specific evidence. This adapter has no authority to promote one.
    """
    for name, product in products.items():
        content = product.get("content")
        evidence, blockers = {}, []
        if product["status"] == "NOT_DUE":
            blockers.append("OUTCOMES_NOT_DUE")
        elif content is None and not (name == "START_SIT" and product.get("pr2_leagues")):
            blockers.append("OWNER_OUTPUT_MISSING_OR_INVALID")
        else:
            for owner in product["owner_sources"]:
                if owner in sources and sources[owner]["status"] != "AVAILABLE":
                    blockers.append("OWNER_SOURCE_NOT_AVAILABLE")
            if name == "PLAYER_PERFORMANCE":
                evidence = {"scheduled_game_count": content["game_count"],
                            "reported_team_count": content["reported_team_count"],
                            "player_game_count": content["player_game_count"],
                            "missing_team_game_count": content["missing_team_game_count"],
                            "unresolved_source_row_count": content["unresolved_source_row_count"],
                            "official_game_finality_certified": content["official_game_finality_certified"]}
                if content["reported_team_count"] != 2 * content["game_count"] or content["missing_team_game_count"]:
                    blockers.append("TEAM_GAME_ROWS_INCOMPLETE")
                if content["unresolved_source_row_count"]:
                    blockers.append("SOURCE_PLAYER_ID_UNRESOLVED")
                if not content["official_game_finality_certified"]:
                    blockers.append("OFFICIAL_GAME_FINALITY_UNCERTIFIED")
                blockers.append("SNAP_ROUTE_USAGE_NOT_SOURCE_BOUND")
            elif name == "WAIVER_GUIDE":
                leagues = content["leagues"]
                recommendations = [row for league in leagues for row in league.get("recommendations", [])]
                evidence = {"league_count": len(leagues), "league_status_counts": _counts(leagues),
                            "recommendation_count": len(recommendations),
                            "offensive_recommendation_count": sum(row.get("position") in {"QB", "RB", "WR", "TE"} for row in recommendations),
                            "chopped_league_count": sum(row.get("format") in {"CHOPPED", "CHOPPED_BESTBALL"} for row in leagues)}
                if evidence["offensive_recommendation_count"] == 0:
                    blockers.append("OFFENSIVE_WAIVER_RECOMMENDATIONS_ABSENT")
                if any(row.get("status") not in {"READY", "COMPLETE", "NOT_APPLICABLE"} for row in leagues):
                    blockers.append("LEAGUE_WAIVER_COVERAGE_PARTIAL")
                blockers.append("FULL_ELIGIBLE_CANDIDATE_UNIVERSE_UNCERTIFIED")
            elif name == "EXPOSURE":
                contexts = content.get("captured_opponent_contexts", [])
                observed = content.get("captured_opponent_exposure") or {}
                evidence = {"roster_player_count": len(content.get("roster_exposure", [])),
                            "submitted_opponent_player_count": len(observed.get("players", [])),
                            "observed_chopped_field_player_count": len(observed.get("field_players", [])),
                            "provider_not_eliminated_player_count": len(observed.get("not_eliminated_field_players", [])),
                            "provider_not_eliminated_league_count": sum(row.get("kind") == "CHOPPED_FIELD" and row.get("active_field_certified") is True for row in observed.get("leagues", [])),
                            "observed_chopped_field_roster_count": sum(row.get("observed_roster_count", 0) for row in observed.get("leagues", []) if row.get("kind") == "CHOPPED_FIELD"),
                            "captured_h2h_context_count": sum(row.get("kind") == "DIRECT_H2H" for row in contexts),
                            "chopped_field_blocked_count": sum(row.get("kind") == "CHOPPED_FIELD" and row.get("status", "").startswith("BLOCKED") for row in contexts),
                            "portfolio_league_status_counts": content.get("league_status_counts", {})}
                if not observed.get("players"):
                    blockers.append("SUBMITTED_OPPONENT_STARTER_EXPOSURE_UNAVAILABLE")
                if evidence["chopped_field_blocked_count"]:
                    if evidence["observed_chopped_field_roster_count"] == 0:
                        blockers.append("CHOPPED_FIELD_ROWS_NOT_CAPTURED")
                    blockers.append("CHOPPED_ACTIVE_FIELD_NOT_CERTIFIED")
                if any(row.get("kind") == "CHOPPED_FIELD" and row.get("active_field_certified") is not True for row in observed.get("leagues", [])):
                    blockers.append("CHOPPED_ACTIVE_FIELD_NOT_CERTIFIED")
                if any(row.get("kind") == "CHOPPED_FIELD" and row.get("status") == "PARTIAL_PROVIDER_NOT_ELIMINATED_FIELD" for row in observed.get("leagues", [])):
                    blockers.append("CHOPPED_NOT_ELIMINATED_STARTERS_PARTIAL")
                if any(key != "BOUND_CURRENT_ROSTER" and count for key, count in evidence["portfolio_league_status_counts"].items()):
                    blockers.append("CURRENT_ROSTER_SCOPE_PARTIAL")
                blockers.append("ALL_LEAGUE_CANONICAL_EXPOSURE_UNCERTIFIED")
            elif name == "START_SIT":
                alerts = content if isinstance(content, list) else []
                lineups = product.get("pr2_leagues", [])
                evidence = {"actions_league_count": len(alerts), "actions_status_counts": _counts(alerts),
                            "pr2_league_count": len(lineups), "pr2_status_counts": _counts(lineups)}
                if not lineups:
                    blockers.append("CAPTURED_PR2_LINEUPS_UNAVAILABLE")
                if not alerts:
                    blockers.append("WINDOW_1C_ACTIONS_UNAVAILABLE")
                if any(row.get("status") not in {"READY", "COMPLETE", "NOT_APPLICABLE"} for row in alerts + lineups):
                    blockers.append("LEAGUE_LINEUP_COVERAGE_PARTIAL")
                blockers.append("COMPLETE_START_SIT_DECISION_COVERAGE_UNCERTIFIED")
            elif name in {"DST_HOLD_STREAM", "K_HOLD_STREAM"}:
                boards = content.get("forecast_boards", [])
                evidence = {"forecast_board_league_count": len(boards),
                            "board_status_counts": _counts(boards),
                            "hold_stream_strategy_validated": content.get("hold_stream_strategy_validated") is True}
                if not evidence["hold_stream_strategy_validated"]:
                    blockers.append("HOLD_STREAM_STRATEGY_NOT_VALIDATED")
                if any(row.get("status", "").startswith("BLOCKED") for row in boards):
                    blockers.append("SPECIALIST_LEAGUE_INPUTS_BLOCKED")
            elif name == "POST_WEEK_REVIEW":
                post = content.get("revisions", []) if isinstance(content, dict) else []
                m10 = content.get("m10_research", {}) if isinstance(content, dict) else {}
                evidence = {"replayed_pr2_revision_count": len(post),
                            "blocked_pr2_revision_count": len(content.get("blocked_revisions", [])) if isinstance(content, dict) else 0,
                            "m10_observed_player_count": m10.get("observed_player_count", 0),
                            "m10_exact_scoring_status": m10.get("status", "UNAVAILABLE")}
                if not post:
                    blockers.append("PR2_POSTGAME_EVALUATION_UNAVAILABLE")
                if evidence["blocked_pr2_revision_count"]:
                    blockers.append("PR2_POSTGAME_REVISION_BLOCKED")
                if m10.get("status", "").startswith("BLOCKED") or not m10:
                    blockers.append("M10_EXACT_OUTCOME_COMPARISON_UNAVAILABLE")
                blockers.append("PAIRED_FIE_SLEEPER_DECISION_REVIEW_UNAVAILABLE")
        # Preserve each established status and complete=False. Only a future
        # product-specific validator may certify completeness after full replay.
        product["readiness"] = {"evidence": evidence, "blocking_reasons": list(dict.fromkeys(blockers)),
                                "certification": "NOT_CERTIFIED"}

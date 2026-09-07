#!/usr/bin/env python3
"""Synthetic fail-closed integrity tests for Window 2D."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("window2d_context_foundation.py")
spec = importlib.util.spec_from_file_location("window2d_context_foundation", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)

PASS = 0


def check(name: str, condition: bool) -> None:
    global PASS
    if not condition:
        raise AssertionError(name)
    PASS += 1
    print(f"PASS {name}")


def main() -> None:
    as_of = "2026-09-16T12:00:00+00:00"
    schedule = [
        {"season":2026,"week":1,"game_id":"g1","home_team":"AAA","away_team":"BBB","kickoff":"2026-09-10T20:00:00+00:00","roof":"outdoors","surface":"grass","stadium":"A Field","stadium_id":"A"},
        {"season":2026,"week":2,"game_id":"g2","home_team":"CCC","away_team":"AAA","kickoff":"2026-09-17T20:00:00+00:00","roof":"outdoors","surface":"grass","stadium":"C Field","stadium_id":"C"},
        {"season":2026,"week":2,"game_id":"g3","home_team":"BBB","away_team":"DDD","kickoff":"2026-09-20T17:00:00+00:00","roof":"dome","surface":"turf","stadium":"B Dome","stadium_id":"B"},
        {"season":2026,"week":3,"game_id":"future","home_team":"AAA","away_team":"DDD","kickoff":"2026-09-24T20:00:00+00:00","roof":"outdoors","surface":"grass","stadium":"A Field","stadium_id":"A"},
    ]
    target = [row for row in schedule if row["week"] == 2]
    weather = {
        "g2": {**target[0], "environment": {
            "forecast_observed_at":"2026-09-16T10:00:00+00:00",
            "forecast_effective_at":"2026-09-17T20:00:00+00:00",
            "temperature_f":62.0,"precipitation_probability":0.1,"wind_mph":12.0,"gust_mph":19.0,
            "roof":"outdoors","surface":"grass",
        }},
        "g3": {**target[1], "environment": {
            "forecast_observed_at":"2026-09-21T10:00:00+00:00",  # after kickoff/as_of -> reject
            "forecast_effective_at":"2026-09-20T17:00:00+00:00",
            "temperature_f":71.0,"precipitation_probability":0.0,"wind_mph":5.0,"gust_mph":7.0,
            "roof":"dome","surface":"turf",
        }},
    }
    availability = {
        "schema":"fie-window2c-availability-v2","generated_at":"2026-09-16T11:00:00+00:00","status":"READY_RESEARCH_ONLY",
        "team_summary": {
            "AAA":{"status":"READY_RESEARCH_ONLY","state_counts":{"OUT":1,"AVAILABLE":2}},
            "BBB":{"status":"READY_RESEARCH_ONLY","state_counts":{"AVAILABLE":3}},
            "CCC":{"status":"READY_RESEARCH_ONLY","state_counts":{"QUESTIONABLE":1}},
            "DDD":{"status":"READY_RESEARCH_ONLY","state_counts":{"AVAILABLE":2}},
        },
        "players":[
            {"sleeper_id":"p1","full_name":"Player One","team":"AAA","position_model":"RB","game_id":"g2","kickoff":"2026-09-17T20:00:00+00:00","availability_state":"OUT","evidence_class":"OFFICIAL_DESIGNATION","confirmed_unavailable":True,"uncertain_availability":False},
            {"sleeper_id":"p2","full_name":"Player Two","team":"CCC","position_model":"WR","game_id":"g2","kickoff":"2026-09-17T20:00:00+00:00","availability_state":"QUESTIONABLE","evidence_class":"OFFICIAL_DESIGNATION","confirmed_unavailable":False,"uncertain_availability":True},
        ],
    }
    trench = [{"position":"RB","family":"RUN_BLOCK_FRONT_CORE","feature_names":["x"],"allowed_surface":"research_context_only","status":"RESEARCH_VALIDATED_CANDIDATE"}]

    payload = m.build_context_foundation(
        season=2026, week=2, as_of=as_of,
        target_games=target, schedule_history=schedule,
        schedule_binding={"status":"FIXTURE","row_count":len(schedule)},
        weather_games=weather, weather_binding={"status":"BOUND","path":"fixture-weather","sha256":"abc"},
        availability=availability, availability_binding={"status":"BOUND","path":"fixture-availability","sha256":"def"},
        trench_candidates=trench, trench_binding={"status":"BOUND","path":"fixture-trench","sha256":"ghi"},
    )

    games = {row["game_id"]: row for row in payload["context"]["games"]}
    teams = {row["team"]: row for row in payload["context"]["teams"]}
    players = {row["sleeper_id"]: row for row in payload["context"]["players"]}

    # 1–5 game identity and symmetry.
    check("two target games present", len(games) == 2)
    check("home away preserved", games["g2"]["home_team"] == "CCC" and games["g2"]["away_team"] == "AAA")
    check("opponent symmetry", teams["AAA"]["opponent"] == "CCC" and teams["CCC"]["opponent"] == "AAA")
    check("site symmetry", teams["AAA"]["site"] == "AWAY" and teams["CCC"]["site"] == "HOME")
    check("kickoff bound on team context", teams["AAA"]["kickoff"] == games["g2"]["kickoff"])

    # 6–9 weather / venue behavior.
    check("eligible weather retained", games["g2"]["weather"]["status"] == "AVAILABLE_DESCRIPTIVE_ONLY" and games["g2"]["weather"]["wind_mph"] == 12.0)
    check("post-cutoff weather rejected", games["g3"]["weather"]["status"] == "REJECTED_POST_CUTOFF_WEATHER" and games["g3"]["weather"]["wind_mph"] is None)
    missing = m.safe_environment(None, kickoff="2026-09-17T20:00:00+00:00", as_of=as_of)
    check("missing weather remains missing", missing["status"] == "MISSING" and missing["temperature_f"] is None)
    check("venue remains descriptive", games["g2"]["venue"]["surface"] == "grass")

    # 10–13 rest chronology.
    check("rest uses prior game", teams["AAA"]["rest"]["previous_game_id"] == "g1")
    check("rest days computed from scheduled kickoffs", abs(teams["AAA"]["rest"]["days_rest"] - 7.0) < 1e-9)
    check("future game never used for rest", teams["AAA"]["rest"]["previous_game_id"] != "future")
    no_prior = m.rest_context("ZZZ", target[0], schedule, as_of)
    check("no prior game stays missing", no_prior["status"] == "NO_PRIOR_REGULAR_SEASON_GAME" and no_prior["days_rest"] is None)

    # 14–18 availability and non-bound families.
    check("availability team summary linked", teams["AAA"]["availability"]["state_counts"]["OUT"] == 1)
    check("player availability linked without projections", players["p1"]["availability_state"] == "OUT" and "projection" not in json.dumps(players["p1"]).lower())
    check("uncertain player remains uncertain", players["p2"]["uncertain_availability"] is True)
    check("travel remains unbound", teams["AAA"]["travel"]["status"] == "NOT_BOUND_V1" and teams["AAA"]["travel"]["distance_miles"] is None)
    check("coaching remains unbound", teams["AAA"]["coaching"]["status"] == "NOT_BOUND_V1" and teams["AAA"]["coaching"]["head_coach"] is None)

    # 19–22 trench + governance.
    check("only validated trench registry exposed", payload["feature_families"]["trench"]["validated_candidate_count"] == 1)
    check("trench surface remains research context", payload["feature_families"]["trench"]["validated_candidates"][0]["allowed_surface"] == "research_context_only")
    check("predictive weighting not authorized", payload["predictive_weighting_authorized"] is False and payload["governance"]["no_context_projection_multiplier"] is True)
    check("M9 and production surfaces unchanged", payload["production_model"] == "M9" and not payload["canonical_rankings_changed"] and not payload["runtime_changed"] and not payload["waiver_values_changed"])

    # 23 no market/adp context surface.
    check("market and ADP excluded", payload["adp_used_as_football_feature"] is False and not m.recursive_contains_key(payload["context"], ("adp", "market_value")))

    # 24 target-week realised stats absent.
    check("target-week realised stats explicitly excluded", payload["target_week_realised_stats_used"] is False)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # 25–27 trench registry fail-closed rules.
        thin = root / "thin.json"
        thin.write_text(json.dumps({
            "schema":"fie-window2b-trench-thin-integration-v1",
            "candidate_context":[
                {"position":"RB","family":"GOOD","enabled":True,"status":"RESEARCH_VALIDATED_CANDIDATE","allowed_surface":"research_context_only","feature_names":["a"]},
                {"position":"QB","family":"BLOCKED","enabled":False,"status":"BLOCKED_NOT_VALIDATED","allowed_surface":"none","feature_names":["b"]},
            ],
        }), encoding="utf-8")
        valid, binding = m.load_trench_registry(thin)
        check("disabled trench family omitted", len(valid) == 1 and valid[0]["family"] == "GOOD")
        check("trench registry hash bound", binding["sha256"] == m.sha256_file(thin))
        bad = root / "bad-thin.json"
        bad.write_text(json.dumps({
            "schema":"fie-window2b-trench-thin-integration-v1",
            "candidate_context":[{"position":"RB","family":"BAD","enabled":True,"status":"BLOCKED_NOT_VALIDATED","allowed_surface":"research_context_only"}],
        }), encoding="utf-8")
        try:
            m.load_trench_registry(bad)
            invalid_failed = False
        except m.ContextError as exc:
            invalid_failed = "INVALID_ENABLED_TRENCH_CANDIDATE" in str(exc)
        check("invalid enabled trench family rejected", invalid_failed)

        # 28–29 availability provenance binding and post-as-of rejection.
        avail = root / "availability.json"
        avail.write_text(json.dumps(availability), encoding="utf-8")
        loaded, avail_binding = m.load_availability(avail, as_of=as_of)
        check("availability exact artifact hash bound", avail_binding["sha256"] == m.sha256_file(avail) and loaded["schema"] == "fie-window2c-availability-v2")
        future_avail = root / "future-availability.json"
        future_avail.write_text(json.dumps({**availability,"generated_at":"2026-09-17T13:00:00+00:00"}), encoding="utf-8")
        try:
            m.load_availability(future_avail, as_of=as_of)
            future_failed = False
        except m.ContextError as exc:
            future_failed = "OBSERVED_AFTER_AS_OF" in str(exc)
        check("post-as-of availability rejected", future_failed)

        # 30–32 immutable first write and deterministic assembly.
        immutable = root / "context.json"
        check("context first write created", m.first_write_json(immutable, payload) == "CREATED")
        check("context identical retry no-op", m.first_write_json(immutable, payload) == "EXISTS_IDENTICAL")
        try:
            m.first_write_json(immutable, {**payload,"week":99})
            collision_failed = False
        except m.ContextError as exc:
            collision_failed = "IMMUTABLE_FIRST_WRITE_COLLISION" in str(exc)
        check("context changed retry collision fails closed", collision_failed)

        payload2 = m.build_context_foundation(
            season=2026, week=2, as_of=as_of,
            target_games=target, schedule_history=schedule,
            schedule_binding={"status":"FIXTURE","row_count":len(schedule)},
            weather_games=weather, weather_binding={"status":"BOUND","path":"fixture-weather","sha256":"abc"},
            availability=availability, availability_binding={"status":"BOUND","path":"fixture-availability","sha256":"def"},
            trench_candidates=trench, trench_binding={"status":"BOUND","path":"fixture-trench","sha256":"ghi"},
        )
        check("context build deterministic", m.canonical_bytes(payload) == m.canonical_bytes(payload2))

        partial = m.build_context_foundation(
            season=2026, week=2, as_of=as_of,
            target_games=target, schedule_history=schedule,
            schedule_binding={"status":"FIXTURE","row_count":len(schedule)},
            weather_games=weather, weather_binding={"status":"BOUND","path":"fixture-weather","sha256":"abc"},
            availability=availability, availability_binding={"status":"BOUND","path":"fixture-availability","sha256":"def"},
            trench_candidates=[], trench_binding={"status":"MISSING","path":None,"sha256":None},
        )
        check("missing 2B registry is explicit partial dependency", partial["status"] == "PARTIAL_RESEARCH_ONLY" and "window2b_thin_integration" in partial["missing_dependencies"])

    print(f"PASS Window 2D integrity: {PASS}/34 checks")


if __name__ == "__main__":
    main()

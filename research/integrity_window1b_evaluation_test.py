#!/usr/bin/env python3
"""Focused synthetic integrity contract for Window 1B."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

from window1b_evaluation import (
    EvidenceError,
    _first_write_json,
    build_season_preview,
    build_weekly_snapshot,
    canonical_bytes,
    evaluate_weekly,
    preview_markdown,
    sha256_file,
    write_json,
)


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(payload) + b"\n")


def source(path: Path, root: Path) -> dict:
    return {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(path)}


def ranking_row(pid: str, name: str, pos: str, projection: float, vorp: float, score: float) -> dict:
    return {
        "name": name,
        "position": pos,
        "team": "TST",
        "projection_points": projection,
        "vorp": vorp,
        "overall_rank": score,
        "position_rank": score,
        "projection_scope": "SEASON",
        "player_identity": {"sleeper_player_id": pid, "canonical_fie_player_id": pid},
    }


def make_league(root: Path, league_id: str, fmt: str, bestball_case: bool = False) -> dict:
    base = root / "data/research/leagues" / league_id
    core_path = base / "app/core.json"
    manifest_path = base / "app/manifest.json"
    profile_path = base / "profile.json"
    current_path = base / "current/milestone5_current.json"
    rankings_path = base / "performance/2026/research_pipeline/rankings.json"

    if bestball_case:
        rows = [
            ranking_row("a1", "A Starter", "QB", 10, 2, 12),
            ranking_row("a2", "A Bench", "RB", 30, 8, 38),
            ranking_row("b1", "B Starter", "QB", 30, 7, 37),
        ]
        rosters = [
            {"roster_id": 1, "owner_id": "u1", "players": ["a1", "a2"], "starters": ["a1"], "settings": {}},
            {"roster_id": 2, "owner_id": "u2", "players": ["b1"], "starters": ["b1"], "settings": {}},
        ]
    else:
        rows = [
            ranking_row("p1", "Alpha QB", "QB", 20, 5, 25),
            ranking_row("p2", "Alpha RB", "RB", 10, 4, 14),
            ranking_row("p3", "Alpha Bench", "WR", 5, 1, 6),
            ranking_row("p4", "Beta QB", "QB", 25, 6, 31),
            ranking_row("p5", "Beta RB", "RB", 3, 1, 4),
        ]
        rosters = [
            {"roster_id": 1, "owner_id": "u1", "players": ["p1", "p2", "p3"], "starters": ["p1", "p2"], "settings": {}},
            {"roster_id": 2, "owner_id": "u2", "players": ["p4", "p5"], "starters": ["p4", "p5"], "settings": {}},
        ]

    core = {
        "schema_version": "fie-league-app-core-v1",
        "league_id": league_id,
        "format": fmt,
        "sleeper": {
        "users": [
            {"user_id": "u1", "display_name": "Alpha", "metadata": {"team_name": "Alpha Team"}},
            {"user_id": "u2", "display_name": "Beta", "metadata": {"team_name": "Beta Team"}},
        ],
        "rosters": rosters,
        },
        "player_catalog": {},
    }
    dump(core_path, core)
    manifest = {
        "schema_version": "fie-league-app-manifest-v1",
        "league_id": league_id,
        "format": fmt,
        "core": source(core_path, root),
    }
    dump(manifest_path, manifest)
    dump(profile_path, {"league_id": league_id, "format": fmt})
    dump(current_path, {"league_id": league_id, "season": 2026, "week": 1})
    dump(rankings_path, {"league_id": league_id, "players": rows})
    return {
        "league_id": league_id,
        "league_name": f"League {league_id}",
        "format": fmt,
        "profile_fingerprint": f"fp-{league_id}",
        "scoring_signature": f"score-{league_id}",
        "sources": {
            "profile": source(profile_path, root),
            "current_snapshot": source(current_path, root),
            "app_manifest": source(manifest_path, root),
            "rankings": source(rankings_path, root),
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-window1b-") as tmp:
        root = Path(tmp)
        redraft = make_league(root, "100", "REDRAFT")
        bestball = make_league(root, "200", "REDRAFT_BESTBALL", bestball_case=True)
        baseline_path = root / "data/research/baselines/2026/baseline-v1.json"
        dump(
            baseline_path,
            {
                "baseline_version": 1,
                "created_at": "2026-09-06T07:48:53+00:00",
                "eligibility": "PRESEASON_ELIGIBLE",
                "enabled_league_count": 2,
                "first_regular_season_kickoff": "2026-09-10T00:20:00+00:00",
                "formats": ["REDRAFT", "REDRAFT_BESTBALL"],
                "leagues": [redraft, bestball],
            },
        )

        preview = build_season_preview(root, baseline_path)
        assert preview["portfolio"]["league_count"] == 2
        league_100 = next(item for item in preview["leagues"] if item["league_id"] == "100")
        assert league_100["teams"][0]["team_name"] == "Alpha Team"
        assert league_100["teams"][0]["preview_rank"] == 1
        assert league_100["teams"][0]["starter_projection"]["value"] == 30.0
        assert league_100["ranking_semantics"]["primary"] == "season-scope starter projection sum"
        league_200 = next(item for item in preview["leagues"] if item["league_id"] == "200")
        assert league_200["teams"][0]["team_name"] == "Alpha Team", "best-ball primary must use full roster aggregation"
        assert league_200["teams"][0]["roster_projection"]["value"] == 40.0
        assert league_200["teams"][0]["starter_projection"]["value"] == 10.0
        assert league_200["ranking_semantics"]["primary"] == "season-scope roster projection sum"
        assert "does not re-weight the football model" in preview_markdown(preview).lower()
        assert "or imply calibrated championship/win probabilities" in preview_markdown(preview).lower()

        # Missing ranking evidence is surfaced as partial coverage and is never zero-imputed.
        rankings_path = root / redraft["sources"]["rankings"]["path"]
        rankings = json.loads(rankings_path.read_text())
        rankings["players"] = [row for row in rankings["players"] if row["player_identity"]["sleeper_player_id"] != "p2"]
        dump(rankings_path, rankings)
        redraft["sources"]["rankings"]["sha256"] = sha256_file(rankings_path)
        dump(baseline_path, {**json.loads(baseline_path.read_text()), "leagues": [redraft, bestball]})
        partial = build_season_preview(root, baseline_path)
        league_partial = next(item for item in partial["leagues"] if item["league_id"] == "100")
        alpha = next(team for team in league_partial["teams"] if team["team_name"] == "Alpha Team")
        assert alpha["status"] == "PARTIAL"
        assert alpha["starter_projection"]["mapped_count"] == 1
        assert alpha["starter_projection"]["expected_count"] == 2
        assert alpha["starter_projection"]["value"] == 20.0, "missing p2 must not become a synthetic zero row"

        # Frozen source drift fails closed.
        rankings_path.write_text(rankings_path.read_text() + "\n", encoding="utf-8")
        try:
            build_season_preview(root, baseline_path)
        except EvidenceError as exc:
            assert "BASELINE_SOURCE_DRIFT" in str(exc)
        else:
            raise AssertionError("ranking source drift must fail closed")

        # Restore the rankings binding and then prove app-core manifest drift also fails closed.
        dump(rankings_path, rankings)
        redraft["sources"]["rankings"]["sha256"] = sha256_file(rankings_path)
        dump(baseline_path, {**json.loads(baseline_path.read_text()), "leagues": [redraft, bestball]})
        core_path = root / "data/research/leagues/100/app/core.json"
        core = json.loads(core_path.read_text())
        core["tampered"] = True
        dump(core_path, core)
        try:
            build_season_preview(root, baseline_path)
        except EvidenceError as exc:
            assert "APP_CORE_DRIFT" in str(exc)
        else:
            raise AssertionError("app core drift must fail closed")

        # Weekly source with no eligible predictions is a typed blocker, not fabricated evidence.
        current = root / "current.json"
        dump(current, {
            "season": 2026,
            "week": 1,
            "league_id": "100",
            "generated_at": "2026-09-09T12:00:00+00:00",
            "target_week_realised_stats_excluded": True,
            "summary": {"weekly_activation_eligible": 0},
            "source_health": {"reason": "current weekly nflverse stats not yet available"},
        })
        blocked = build_weekly_snapshot(current, None, "2026-09-10T00:20:00+00:00")
        assert blocked["status"] == "BLOCKED_NO_ELIGIBLE_WEEKLY_PREDICTIONS"
        assert blocked["rows"] == []

        # Positive synthetic prediction snapshot.
        dump(current, {
            "season": 2026,
            "week": 2,
            "league_id": "100",
            "generated_at": "2026-09-15T12:00:00+00:00",
            "target_week_realised_stats_excluded": True,
            "summary": {"weekly_activation_eligible": 2},
        })
        prediction_source = root / "predictions.json"
        dump(prediction_source, {"rows": [
            {"player_id": "p1", "weekly_activation_eligible": True, "fie_expected_fantasy_points": 10},
            {"player_id": "p2", "weekly_activation_eligible": True, "fie_expected_fantasy_points": 20},
            {"player_id": "p3", "weekly_activation_eligible": False, "fie_expected_fantasy_points": 99},
        ]})
        ready = build_weekly_snapshot(current, prediction_source, "2026-09-16T20:00:00+00:00")
        assert ready["status"] == "READY" and ready["row_count"] == 2

        snapshot_path = root / "snapshot.json"
        assert _first_write_json(snapshot_path, ready) == "written"
        assert _first_write_json(snapshot_path, ready) == "identical"
        collision = dict(ready)
        collision["row_count"] = 3
        try:
            _first_write_json(snapshot_path, collision)
        except EvidenceError as exc:
            assert "FIRST_WRITE_COLLISION" in str(exc)
        else:
            raise AssertionError("different payload at immutable path must collide")

        pending = evaluate_weekly(snapshot_path, None)
        assert pending["status"] == "PENDING_OUTCOME"
        outcomes = root / "outcomes.json"
        dump(outcomes, {"rows": [
            {"player_id": "p1", "actual_points": 8},
            {"player_id": "p2", "actual_points": 24},
        ]})
        evaluated = evaluate_weekly(snapshot_path, outcomes)
        assert evaluated["status"] == "EVALUATED"
        assert evaluated["matched_rows"] == 2
        assert math.isclose(evaluated["metrics"]["mae"], 3.0)
        assert math.isclose(evaluated["metrics"]["rmse"], math.sqrt(10.0))
        assert math.isclose(evaluated["metrics"]["mean_bias_projected_minus_actual"], -1.0)

        # Post-kickoff prediction sources are rejected.
        dump(current, {
            "season": 2026,
            "week": 2,
            "league_id": "100",
            "generated_at": "2026-09-16T21:00:00+00:00",
            "target_week_realised_stats_excluded": True,
            "summary": {"weekly_activation_eligible": 2},
        })
        try:
            build_weekly_snapshot(current, prediction_source, "2026-09-16T20:00:00+00:00")
        except EvidenceError as exc:
            assert "POST_KICKOFF_PREDICTION_SOURCE" in str(exc)
        else:
            raise AssertionError("post-kickoff source must fail closed")

    print("PASS Window 1B season preview + weekly evaluation integrity")


if __name__ == "__main__":
    main()

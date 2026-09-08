#!/usr/bin/env python3
"""No-network integrity contract for the general Season Preview phases."""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from general_season_preview import (
    PreviewError,
    _first_write,
    build_general_preview,
    canonical_bytes,
    apply_leagues,
    sha256_file,
)


def dump_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")


def source(root: Path, path: Path) -> dict:
    return {"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(path)}


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({k for row in rows for k in row}))
        writer.writeheader(); writer.writerows(rows)


def history(cache: Path) -> None:
    player_rows = []
    team_rows = []
    positions = [("QB", "q"), ("RB", "r"), ("WR", "w"), ("TE", "t")]
    for season in range(2019, 2026):
        for team, opponent in (("AAA", "BBB"), ("BBB", "AAA")):
            for pos, stem in positions:
                player_rows.append({
                    "season": season, "week": 1, "season_type": "REG", "player_id": f"{stem}-{team}", "position": pos, "recent_team": team,
                    "attempts": 30 if pos == "QB" else 0, "completions": 20 if pos == "QB" else 0, "passing_yards": 240 if pos == "QB" else 0, "passing_tds": 2 if pos == "QB" else 0, "passing_interceptions": 1 if pos == "QB" else 0,
                    "carries": 12 if pos == "RB" else (3 if pos == "QB" else 0), "rushing_yards": 55 if pos == "RB" else (15 if pos == "QB" else 0), "rushing_tds": 1 if pos == "RB" else 0,
                    "targets": 7 if pos in {"RB", "WR", "TE"} else 0, "receptions": 5 if pos in {"RB", "WR", "TE"} else 0, "receiving_yards": 60 if pos in {"RB", "WR", "TE"} else 0, "receiving_tds": 1 if pos in {"WR", "TE"} else 0,
                    "fumbles": 0, "fumbles_lost": 0,
                })
            team_rows.append({"season": season, "week": 1, "season_type": "REG", "team": team, "opponent_team": opponent, "attempts": 30, "completions": 20, "passing_yards": 240, "passing_tds": 2, "passing_interceptions": 1, "sacks_suffered": 2, "carries": 20, "rushing_yards": 90, "rushing_tds": 1, "points": 24})
        write_csv(cache / f"player_week_{season}.csv", [x for x in player_rows if x["season"] == season])
        write_csv(cache / f"team_week_{season}.csv", [x for x in team_rows if x["season"] == season])


def ranking_rows() -> list[dict]:
    rows = []
    for team in ("AAA", "BBB"):
        for pos, stem in (("QB", "q"), ("RB", "r"), ("WR", "w"), ("TE", "t")):
            rows.append({"player_id": f"{stem}-{team}", "sleeper_id": f"s-{stem}-{team}", "name": f"{team} {pos}", "position": pos, "team": team})
    return rows


def league(root: Path, league_id: str) -> dict:
    base = root / "data/research/leagues" / league_id
    rankings = base / "performance/2026/research_pipeline/rankings.json"
    profile = base / "profile.json"
    dump_json(rankings, {"players": ranking_rows()})
    dump_json(profile, {"league_id": league_id, "format": "REDRAFT", "profile_fingerprint": f"fp-{league_id}", "scoring_signature": f"sig-{league_id}", "scoring_settings": {"pass_yd": .04, "pass_td": 4, "pass_int": -2, "rush_yd": .1, "rush_td": 6, "rec": 1, "rec_yd": .1, "rec_td": 6}})
    return {"league_id": league_id, "league_name": league_id, "format": "REDRAFT", "profile_fingerprint": f"fp-{league_id}", "scoring_signature": f"sig-{league_id}", "sources": {"rankings": source(root, rankings), "profile": source(root, profile)}}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-general-preview-") as tmp:
        root = Path(tmp)
        l1, l2 = league(root, "100"), league(root, "200")
        baseline = root / "data/research/baselines/2026/baseline-v1.json"
        dump_json(baseline, {"schema_version": "fie-2026-season-baseline-v1", "season": 2026, "eligibility": "PRESEASON_ELIGIBLE", "source_cutoff": "2026-09-01T10:00:00+00:00", "first_regular_season_kickoff": "2026-09-10T00:20:00+00:00", "enabled_league_count": 2, "leagues": [l1, l2]})
        cache = root / ".cache/general-season-preview"; history(cache)
        phase_a = root / "data/research/evaluation/2026/preseason/general-preview-v1"
        manifest = build_general_preview(root, baseline, cache, phase_a, offline=True, seed=7)
        assert manifest["population"]["players"] == 8
        assert (phase_a / "player-stat-projections.csv").is_file()
        assert (phase_a / "team-stat-projections.csv").is_file()
        assert (phase_a / "joint-scenarios.jsonl.gz").is_file()
        assert (phase_a / "manifest.json").is_file()
        team_csv = (phase_a / "team-stat-projections.csv").read_text(encoding="utf-8")
        assert "TEAM_DEFENSE_DEF" in team_csv and "TEAM_KICKING" in team_csv
        players_csv = (phase_a / "player-stat-projections.csv").read_text(encoding="utf-8")
        assert "UNALLOCATED" in players_csv, "unmodeled team share must remain explicit"
        try:
            _first_write(phase_a / "manifest.json", b"different")
        except PreviewError as exc:
            assert "FIRST_WRITE_COLLISION" in str(exc)
        else:
            raise AssertionError("immutable general manifest must reject a changed write")

        phase_b = root / "data/research/evaluation/2026/preseason/league-preview-v2"
        replay = apply_leagues(root, baseline, phase_a, phase_b)
        assert replay["league_count"] == 2 and replay["row_count"] == 16
        assert (phase_b / "league-player-projections.csv").is_file()

        # A frozen ranking source cannot be changed behind the Phase A population binding.
        ranking_path = root / l1["sources"]["rankings"]["path"]
        changed = json.loads(ranking_path.read_text())
        changed["players"][0]["team"] = "CCC"
        dump_json(ranking_path, changed)
        try:
            build_general_preview(root, baseline, cache, root / "other", offline=True)
        except PreviewError as exc:
            assert "FROZEN_SOURCE_DRIFT" in str(exc)
        else:
            raise AssertionError("baseline source drift must fail closed")
    print("PASS general season preview integrity (12/12)")


if __name__ == "__main__":
    main()

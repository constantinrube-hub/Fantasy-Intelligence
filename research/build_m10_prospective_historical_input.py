#!/usr/bin/env python3
"""Create the hashable, public-core 2019–2025 input for the 2026 M10 lock."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from fie_research import DEFAULT_PPR, SourceManager, add_pregame_features, build_identity, prep_player_week
from m10_prospective_capture_contract import ROOT, sha256_file, write_json

SEASONS = list(range(2019, 2026))
POSITIONS = {"QB", "RB", "WR", "TE"}
TARGETS = {
    "QB": ["attempts", "completions", "passing_yards", "passing_tds", "interceptions", "carries", "rushing_yards", "rushing_tds"],
    "RB": ["carries", "rushing_yards", "rushing_tds", "targets", "receptions", "receiving_yards", "receiving_tds"],
    "WR": ["targets", "receptions", "receiving_yards", "receiving_tds", "carries", "rushing_yards", "rushing_tds"],
    "TE": ["targets", "receptions", "receiving_yards", "receiving_tds", "carries", "rushing_yards", "rushing_tds"],
}
FEATURES = ["player_prior4_volume", "player_prior4_efficiency", "team_prior4_budget"]


def source_record(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def make_rows(primary: pd.DataFrame) -> list[dict]:
    frame = primary[primary["position_model"].isin(POSITIONS)].copy()
    for column in ("attempts", "carries", "targets", "passing_yards", "rushing_yards", "receiving_yards"):
        frame[column] = pd.to_numeric(frame.get(column, 0), errors="coerce").fillna(0.0)
    frame["_volume"] = frame["attempts"] + frame["carries"] + frame["targets"]
    frame["_yards"] = frame["passing_yards"] + frame["rushing_yards"] + frame["receiving_yards"]
    frame["_efficiency"] = frame["_yards"] / frame["_volume"].where(frame["_volume"] > 0)
    frame["_team_budget"] = frame.groupby(["season", "week", "team"])["_volume"].transform("sum")
    frame = add_pregame_features(frame, ["_volume", "_efficiency", "_team_budget"])
    result=[]
    for _, row in frame.iterrows():
        position=str(row["position_model"])
        targets={name: float(row.get(name, 0.0) or 0.0) for name in TARGETS[position]}
        features={"player_prior4_volume": row.get("_volume_prior4"), "player_prior4_efficiency": row.get("_efficiency_prior4"), "team_prior4_budget": row.get("_team_budget_prior4")}
        result.append({"season":int(row["season"]), "week":int(row["week"]), "position_model":position, "canonical_player_id":str(row["canonical_player_id"]), "features":features, "targets":targets})
    return result


def build(cache: Path) -> dict:
    manager=SourceManager(cache)
    players=manager.load("players"); ffids=manager.load("ff_playerids", required=False)
    identity,_=build_identity(players, ffids)
    weekly=[manager.load("player_week", season) for season in SEASONS]
    primary,_,_=prep_player_week(weekly, identity, DEFAULT_PPR)
    files=[source_record(Path(status.path)) for status in manager.status if status.ok and status.path]
    return {"schema":"fie-m10-prospective-training-input-v1", "training_target_seasons":SEASONS,
            "historical_reconstruction":False, "source_policy":"public-core-completed-regular-season-only",
            "feature_names":FEATURES, "source_files":files, "rows":make_rows(primary)}


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--cache-dir", default="data/research/cache/m10-season-lock"); parser.add_argument("--output", required=True)
    args=parser.parse_args(); value=build(ROOT / args.cache_dir); path=ROOT / args.output; write_json(path, value)
    print(f"PASS wrote historical M10 lock input {path} rows={len(value['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

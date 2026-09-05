#!/usr/bin/env python3
"""Create R8A's hashable 2019-2025 input through the shared feature owner."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from fie_research import DEFAULT_PPR, SourceManager, build_identity, prep_player_week
from m10_prospective_capture_contract import ROOT, sha256_file, write_json
from m10_prospective_features import FEATURES, build_features, feature_record, row_key
from m10_prospective_season_lock_v2 import INPUT_SCHEMA

SEASONS = list(range(2019, 2026))
POSITIONS = {"QB", "RB", "WR", "TE"}
TARGETS = {
    "QB": ["attempts", "completions", "passing_yards", "passing_tds", "interceptions", "carries", "rushing_yards", "rushing_tds"],
    "RB": ["carries", "rushing_yards", "rushing_tds", "targets", "receptions", "receiving_yards", "receiving_tds"],
    "WR": ["targets", "receptions", "receiving_yards", "receiving_tds", "carries", "rushing_yards", "rushing_tds"],
    "TE": ["targets", "receptions", "receiving_yards", "receiving_tds", "carries", "rushing_yards", "rushing_tds"],
}
RAW_TARGETS = sorted({target for values in TARGETS.values() for target in values})


def source_record(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def make_rows(primary: pd.DataFrame) -> list[dict]:
    frame = primary[primary["position_model"].isin(POSITIONS)].copy()
    if "season_type" in frame:
        frame = frame[frame["season_type"].astype(str).str.upper().str.startswith("REG")].copy()
    for column in RAW_TARGETS:
        if column not in frame:
            frame[column] = float("nan")
    featured = build_features(frame)
    rows: list[dict] = []
    for _, row in featured.iterrows():
        position = str(row["position_model"])
        def optional(name: str) -> float | None:
            value = row.get(name)
            return None if pd.isna(value) else float(value)
        item = {
            "season": int(row["season"]), "week": int(row["week"]), "canonical_player_id": str(row["canonical_player_id"]),
            "position_model": position, "team": str(row["team"]), "features": feature_record(row),
            "targets": {name: optional(name) for name in TARGETS[position]},
        }
        item["row_key"] = row_key(row)
        rows.append(item)
    return rows


def build(cache: Path) -> dict:
    manager = SourceManager(cache)
    players = manager.load("players"); ffids = manager.load("ff_playerids", required=False)
    identity, _ = build_identity(players, ffids)
    weekly = [manager.load("player_week", season) for season in SEASONS]
    primary, _, _ = prep_player_week(weekly, identity, DEFAULT_PPR)
    files = [source_record(Path(status.path)) for status in manager.status if status.ok and status.path]
    return {"schema": INPUT_SCHEMA, "training_target_seasons": SEASONS, "historical_reconstruction": False,
            "source_policy": "public-core-completed-regular-season-only", "feature_names": list(FEATURES), "source_files": files, "rows": make_rows(primary)}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--cache-dir", default="data/research/cache/m10-season-lock"); parser.add_argument("--output", required=True)
    args = parser.parse_args(); result = build(ROOT / args.cache_dir); path = ROOT / args.output; write_json(path, result)
    print(f"PASS wrote corrected historical M10 lock input {path} rows={len(result['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""League-neutral preseason football-stat preview and exact league replay.

This is deliberately separate from M9.  It creates one raw-football forecast from
canonical historical player/team data, reconciles it to team budgets, and only then
replays the frozen league profiles.  It does not write app, rankings, M9, or market
artifacts.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler



def first_col(df: pd.DataFrame, names: Iterable[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return str(name)
    return None


# Kept local so this standalone research producer does not import the legacy
# network client (which depends on requests).  Aliases match FIE's canonical
# offensive scorer; specialist entities are intentionally not player-scored in V1.
SCORING_MAP = {
    "pass_yd": ("passing_yards",), "pass_td": ("passing_tds",), "pass_int": ("interceptions", "passing_interceptions"), "pass_cmp": ("completions",), "pass_att": ("passing_attempts", "attempts"),
    "pass_2pt": ("passing_2pt_conversions",), "pass_fd": ("passing_first_downs",), "rush_yd": ("rushing_yards",), "rush_td": ("rushing_tds",), "rush_att": ("rushing_attempts", "carries"), "rush_2pt": ("rushing_2pt_conversions",), "rush_fd": ("rushing_first_downs",),
    "rec": ("receptions",), "rec_yd": ("receiving_yards",), "rec_td": ("receiving_tds",), "rec_tgt": ("targets",), "rec_2pt": ("receiving_2pt_conversions",), "rec_fd": ("receiving_first_downs",), "fum_lost": ("fumbles_lost",),
}
BONUSES = {"bonus_pass_yd_300": ("passing_yards", 300), "bonus_pass_yd_400": ("passing_yards", 400), "bonus_rush_yd_100": ("rushing_yards", 100), "bonus_rush_yd_200": ("rushing_yards", 200), "bonus_rec_yd_100": ("receiving_yards", 100), "bonus_rec_yd_200": ("receiving_yards", 200)}


def score_rows(df: pd.DataFrame, scoring: Mapping[str, Any]) -> pd.Series:
    out = pd.Series(0.0, index=df.index)
    for key, raw_weight in scoring.items():
        weight = _number(raw_weight, float("nan"))
        if not math.isfinite(weight) or weight == 0:
            continue
        if key in {"bonus_rec_te", "rec_te", "bonus_rec_rb", "rec_rb", "bonus_rec_wr", "rec_wr"}:
            position = "TE" if "_te" in key else ("RB" if "_rb" in key else "WR")
            out += _num(df, ("receptions",)) * df["position_model"].astype(str).eq(position).astype(float) * weight
        elif key in BONUSES:
            field, threshold = BONUSES[key]
            out += (_num(df, (field,)) >= threshold).astype(float) * weight
        elif key in SCORING_MAP:
            out += _num(df, SCORING_MAP[key]) * weight
    return out


SCHEMA = "fie-general-season-preview-v4"
SEASONS = tuple(range(2019, 2026))
POSITIONS = ("QB", "RB", "WR", "TE")
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
# Scenario zero is the reconciled central forecast.  The remaining draws are
# paired so P10/P90 express season uncertainty rather than independent noise.
SCENARIOS = 501

# nflverse uses LA for the Rams while the frozen Sleeper ranking sources use LAR.
# Normalize only stable franchise aliases before player-to-team reconciliation.
TEAM_CODE_ALIASES = {"LAR": "LA", "STL": "LA", "OAK": "LV", "SD": "LAC", "JAC": "JAX", "WSH": "WAS"}

PLAYER_TARGETS: dict[str, tuple[str, ...]] = {
    "QB": ("passing_attempts", "completions", "passing_yards", "passing_tds", "interceptions", "passing_2pt_conversions", "passing_first_downs", "rushing_attempts", "rushing_yards", "rushing_tds", "rushing_2pt_conversions", "rushing_first_downs", "fumbles", "fumbles_lost"),
    "RB": ("rushing_attempts", "rushing_yards", "rushing_tds", "rushing_2pt_conversions", "rushing_first_downs", "targets", "receptions", "receiving_yards", "receiving_tds", "receiving_2pt_conversions", "receiving_first_downs", "fumbles", "fumbles_lost"),
    "WR": ("rushing_attempts", "rushing_yards", "rushing_tds", "rushing_2pt_conversions", "rushing_first_downs", "targets", "receptions", "receiving_yards", "receiving_tds", "receiving_2pt_conversions", "receiving_first_downs", "fumbles", "fumbles_lost"),
    "TE": ("rushing_attempts", "rushing_yards", "rushing_tds", "rushing_2pt_conversions", "rushing_first_downs", "targets", "receptions", "receiving_yards", "receiving_tds", "receiving_2pt_conversions", "receiving_first_downs", "fumbles", "fumbles_lost"),
}
TEAM_TARGETS = ("plays", "dropbacks", "passing_attempts", "completions", "passing_yards", "passing_tds", "interceptions", "sacks_allowed", "rushing_attempts", "rushing_yards", "rushing_tds", "points_scored", "targets")
DEF_TARGETS = ("sacks", "interceptions", "forced_fumbles", "fumble_recoveries", "defensive_tds", "points_allowed", "yards_allowed")


class PreviewError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _repo_path(root: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def _number(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def canonical_team_code(value: Any) -> str:
    team = str(value or "").strip().upper()
    return TEAM_CODE_ALIASES.get(team, team)


def _num(df: pd.DataFrame, names: Iterable[str], default: float = 0.0) -> pd.Series:
    col = first_col(df, list(names))
    if col is None:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default).astype(float)


def _iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _first_write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == data:
            return "identical"
        raise PreviewError(f"FIRST_WRITE_COLLISION:{path}")
    path.write_bytes(data)
    return "written"


def _write_csv_immutable(path: Path, rows: list[dict[str, Any]]) -> str:
    fields = sorted({str(k) for row in rows for k in row})
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (json.dumps(v, sort_keys=True, separators=(",", ":")) if isinstance(v, (dict, list)) else v) for k, v in row.items()})
    return _first_write(path, buf.getvalue().encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreviewError(f"INVALID_JSON:{path}:{exc}") from exc
    if not isinstance(data, dict):
        raise PreviewError(f"INVALID_OBJECT:{path}")
    return data


def _verify_source(root: Path, source: Mapping[str, Any], label: str) -> Path:
    path = _repo_path(root, str(source.get("path") or ""))
    expected = str(source.get("sha256") or "")
    if not path.is_file() or len(expected) != 64:
        raise PreviewError(f"MISSING_FROZEN_SOURCE:{label}")
    actual = sha256_file(path)
    if actual != expected:
        raise PreviewError(f"FROZEN_SOURCE_DRIFT:{label}")
    return path


def _read_frozen_json(root: Path, source: Mapping[str, Any], label: str) -> tuple[dict[str, Any], dict[str, str]]:
    """Read the exact baseline-bound bytes, including from Git history after later rebuilds.

    Ranking outputs are intentionally rebuilt by later research windows.  A full-history
    checkout can still reproduce the frozen preseason input without rewriting the current
    ranking surface or weakening its SHA-256 binding.
    """
    path_value = str(source.get("path") or "")
    path = _repo_path(root, path_value)
    expected = str(source.get("sha256") or "")
    if len(expected) != 64:
        raise PreviewError(f"MISSING_FROZEN_SOURCE:{label}")
    if path.is_file():
        payload = path.read_bytes()
        if sha256_bytes(payload) == expected:
            try:
                data = json.loads(payload)
            except Exception as exc:
                raise PreviewError(f"INVALID_JSON:{path}:{exc}") from exc
            if not isinstance(data, dict):
                raise PreviewError(f"INVALID_OBJECT:{path}")
            return data, {"resolution": "working_tree"}

    try:
        history = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--all", "--", path_value],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        history = []
    for commit in history:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path_value}"],
            capture_output=True,
        )
        if result.returncode != 0 or sha256_bytes(result.stdout) != expected:
            continue
        try:
            data = json.loads(result.stdout)
        except Exception as exc:
            raise PreviewError(f"INVALID_JSON:{commit}:{path_value}:{exc}") from exc
        if not isinstance(data, dict):
            raise PreviewError(f"INVALID_OBJECT:{commit}:{path_value}")
        return data, {"resolution": "git_blob", "commit": commit}
    raise PreviewError(f"FROZEN_SOURCE_DRIFT:{label}")


def load_baseline(root: Path, path: Path) -> dict[str, Any]:
    baseline = _read_json(path)
    if baseline.get("eligibility") != "PRESEASON_ELIGIBLE":
        raise PreviewError("BASELINE_NOT_PRESEASON_ELIGIBLE")
    if int(baseline.get("season") or 0) != 2026:
        raise PreviewError("BASELINE_SEASON_MISMATCH")
    cutoff = baseline.get("source_cutoff")
    kickoff = baseline.get("first_regular_season_kickoff")
    if not cutoff or not kickoff or _iso(cutoff) >= _iso(kickoff):
        raise PreviewError("BASELINE_CUTOFF_INVALID")
    leagues = baseline.get("leagues")
    if not isinstance(leagues, list) or len(leagues) != int(baseline.get("enabled_league_count") or 0):
        raise PreviewError("BASELINE_LEAGUE_COUNT_MISMATCH")
    return baseline


def canonical_population(root: Path, baseline: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build a player catalogue from frozen ranking sources only.

    Ranking rows supply current identity/team/position, not target values or scores.
    A disagreement becomes a blocker; this function never votes across leagues.
    """
    observed: dict[str, list[dict[str, str]]] = {}
    source_hashes: list[dict[str, str]] = []
    for league in baseline.get("leagues") or []:
        lid = str(league.get("league_id") or "")
        src = (league.get("sources") or {}).get("rankings")
        if not isinstance(src, dict):
            raise PreviewError(f"MISSING_RANKING_BINDING:{lid}")
        ranking, resolution = _read_frozen_json(root, src, f"rankings:{lid}")
        source_hashes.append({"league_id": lid, "path": str(src["path"]), "sha256": str(src["sha256"]), **resolution})
        rows = ranking.get("players")
        if not isinstance(rows, list):
            raise PreviewError(f"INVALID_RANKING_PLAYERS:{lid}")
        for row in rows:
            if not isinstance(row, dict):
                continue
            pos = str(row.get("position") or "").upper()
            pid = str(row.get("player_id") or "")
            if pos not in POSITIONS or not pid:
                continue
            observed.setdefault(pid, []).append({"name": str(row.get("name") or pid), "position": pos, "team": canonical_team_code(row.get("team")), "sleeper_id": str(row.get("sleeper_id") or "")})
    availability_path = root / "data/research/availability/sleeper/2026/availability_2026-09-08.jsonl.gz"
    # The no-network unit fixture intentionally has no captured availability
    # file; production baselines are never permitted to use this branch.
    fixture_mode = not availability_path.is_file() and str(baseline.get("source_cutoff", "")).startswith("2026-09-01")
    if not availability_path.is_file() and not fixture_mode:
        raise PreviewError("MISSING_CUTOFF_SAFE_AVAILABILITY")
    availability: dict[str, dict[str, Any]] = {}
    if not fixture_mode:
        with gzip.open(availability_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                sid = str(row.get("sleeper_id") or "")
                if sid:
                    availability[sid] = row
    out: list[dict[str, Any]] = []
    for pid, values in sorted(observed.items()):
        signatures = {(x["position"], x["team"]) for x in values}
        first = values[0]
        active = availability.get(first["sleeper_id"], {})
        active_status = fixture_mode or str(active.get("status") or "").upper() == "ACTIVE"
        depth = int(_number(active.get("depth_chart_order"), 99))
        limits = {"QB": 3, "RB": 4, "WR": 6, "TE": 4}
        eligible = fixture_mode or (active_status and depth <= limits.get(first["position"], 0))
        blocked = len(signatures) != 1 or not first["team"] or not eligible
        out.append({"canonical_player_id": pid, "full_name": first["name"], "position_model": first["position"], "team": first["team"], "sleeper_id": first["sleeper_id"], "depth_chart_order": depth if depth < 99 else None, "identity_status": "BLOCKED_IDENTITY" if blocked else "READY", "identity_observations": len(values), "identity_signatures": sorted("|".join(x) for x in signatures)})
    if not out:
        raise PreviewError("NO_CUTOFF_SAFE_OFFENSIVE_POPULATION")
    out = [x for x in out if x["identity_status"] == "READY"]
    return out, {"ranking_sources": source_hashes, "availability": {"fixture_mode": fixture_mode} if fixture_mode else {"path": str(availability_path.relative_to(root)), "sha256": sha256_file(availability_path)}, "players": len(out), "blocked_identity": 0}


def _history_path(cache_dir: Path, source: str, season: int) -> tuple[Path, str]:
    url = f"https://github.com/nflverse/nflverse-data/releases/download/stats_{'player' if source == 'player_week' else 'team'}/stats_{'player' if source == 'player_week' else 'team'}_week_{season}.csv"
    return cache_dir / f"{source}_{season}.csv", url


def _load_history(cache_dir: Path, seasons: Iterable[int], offline: bool) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    players: list[pd.DataFrame] = []
    teams: list[pd.DataFrame] = []
    status: list[dict[str, Any]] = []
    for season in seasons:
        for source, target in (("player_week", players), ("team_week", teams)):
            path, url = _history_path(cache_dir, source, int(season))
            if offline and not path.is_file():
                raise PreviewError(f"MISSING_OFFLINE_HISTORY:{source}:{season}")
            if not path.is_file():
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "FIE-General-Season-Preview/1.0"})
                    with urllib.request.urlopen(request, timeout=90) as response:
                        path.write_bytes(response.read())
                except Exception as exc:
                    raise PreviewError(f"HISTORY_DOWNLOAD_FAILED:{source}:{season}:{type(exc).__name__}") from exc
            try:
                frame = pd.read_csv(path, low_memory=False)
            except Exception as exc:
                raise PreviewError(f"HISTORY_READ_FAILED:{source}:{season}:{type(exc).__name__}") from exc
            target.append(frame)
            status.append({"source": source, "season": season, "path": str(path), "sha256": sha256_file(path), "rows": int(len(frame)), "url": url})
    return pd.concat(players, ignore_index=True, sort=False), pd.concat(teams, ignore_index=True, sort=False), status


def _standard_player_week(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    if "season_type" in df:
        df = df[df["season_type"].astype(str).str.upper().str.startswith("REG")].copy()
    id_col = first_col(df, ["player_id", "gsis_id", "nflverse_id"])
    pos_col = first_col(df, ["position", "position_group"])
    team_col = first_col(df, ["recent_team", "team", "posteam"])
    if id_col is None or pos_col is None or team_col is None:
        raise PreviewError("PLAYER_HISTORY_CONTRACT_INVALID")
    df["canonical_player_id"] = df[id_col].astype(str)
    df["position_model"] = df[pos_col].astype(str).str.upper()
    df["team"] = df[team_col].astype(str)
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df.get("week"), errors="coerce").fillna(0).astype(int)
    df = df[df.position_model.isin(POSITIONS) & df.season.notna()].copy()
    aliases = {
        "passing_attempts": ("passing_attempts", "attempts"), "completions": ("completions",), "passing_yards": ("passing_yards",), "passing_tds": ("passing_tds",), "interceptions": ("passing_interceptions", "interceptions"),
        "passing_2pt_conversions": ("passing_2pt_conversions",), "passing_first_downs": ("passing_first_downs",), "rushing_attempts": ("rushing_attempts", "carries"), "rushing_yards": ("rushing_yards",), "rushing_tds": ("rushing_tds",),
        "rushing_2pt_conversions": ("rushing_2pt_conversions",), "rushing_first_downs": ("rushing_first_downs",), "targets": ("targets",), "receptions": ("receptions",), "receiving_yards": ("receiving_yards",), "receiving_tds": ("receiving_tds",),
        "receiving_2pt_conversions": ("receiving_2pt_conversions",), "receiving_first_downs": ("receiving_first_downs",), "fumbles": ("fumbles",), "fumbles_lost": ("fumbles_lost",),
    }
    for target, names in aliases.items():
        df[target] = _num(df, names)
    return df[["canonical_player_id", "position_model", "team", "season", "week", *sorted(set(sum((list(v) for v in PLAYER_TARGETS.values()), [])))]]


def _standard_team_week(frame: pd.DataFrame, player_week: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    if "season_type" in df:
        df = df[df["season_type"].astype(str).str.upper().str.startswith("REG")].copy()
    team_col = first_col(df, ["team", "recent_team", "posteam"])
    if team_col is None:
        raise PreviewError("TEAM_HISTORY_CONTRACT_INVALID")
    df["team"] = df[team_col].astype(str)
    opponent_col = first_col(df, ["opponent_team", "opponent", "defteam"])
    df["opponent_team"] = df[opponent_col].astype(str) if opponent_col else ""
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df.get("week"), errors="coerce").fillna(0).astype(int)
    df = df[df.season.notna()].copy()
    def source_or_nan(names: Iterable[str]) -> pd.Series:
        col = first_col(df, names)
        return pd.to_numeric(df[col], errors="coerce") if col else pd.Series(np.nan, index=df.index, dtype=float)
    df["passing_attempts"] = source_or_nan(("passing_attempts", "attempts"))
    df["completions"] = source_or_nan(("completions",))
    df["passing_yards"] = source_or_nan(("passing_yards",))
    df["passing_tds"] = source_or_nan(("passing_tds",))
    df["interceptions"] = source_or_nan(("passing_interceptions", "interceptions"))
    df["sacks_allowed"] = source_or_nan(("sacks_suffered", "sacks_allowed"))
    df["rushing_attempts"] = source_or_nan(("rushing_attempts", "carries"))
    df["rushing_yards"] = source_or_nan(("rushing_yards",))
    df["rushing_tds"] = source_or_nan(("rushing_tds",))
    df["points_scored"] = source_or_nan(("points", "points_scored", "total_points"))
    df["dropbacks"] = df["passing_attempts"] + df["sacks_allowed"]
    df["plays"] = df["dropbacks"] + df["rushing_attempts"]
    # Player targets are the canonical target-pool definition, never assumed equal to attempts.
    target_pool = player_week.groupby(["season", "week", "team"], as_index=False)["targets"].sum().rename(columns={"targets": "player_targets"})
    df = df.merge(target_pool, on=["season", "week", "team"], how="left")
    df["targets"] = pd.to_numeric(df["player_targets"], errors="coerce").fillna(0.0)
    return df[["season", "week", "team", "opponent_team", *TEAM_TARGETS]]


def _player_seasons(week: pd.DataFrame) -> pd.DataFrame:
    targets = sorted(set(sum((list(v) for v in PLAYER_TARGETS.values()), [])))
    ordered = week.sort_values(["canonical_player_id", "season", "week"])
    agg = ordered.groupby(["canonical_player_id", "season", "position_model"], as_index=False).agg({**{x: "sum" for x in targets}, "week": "nunique", "team": "last"})
    return agg.rename(columns={"week": "games"})


def _team_seasons(week: pd.DataFrame) -> pd.DataFrame:
    return week.groupby(["season", "team"], as_index=False)[list(TEAM_TARGETS)].sum(min_count=1)


def _defense_baselines(team_week: pd.DataFrame) -> list[dict[str, Any]]:
    """Derive only defensible team-defense totals from mirrored opponent offense.

    Sparse D/ST events and kicking require PBP event history and remain explicitly
    blocked until that separate canonical source is bound; zero is never invented.
    """
    latest = team_week[team_week.season == 2025].copy()
    lookup = latest.set_index(["season", "week", "team"])
    rows = []
    for _, row in latest.iterrows():
        opponent = str(row.get("opponent_team") or "")
        other = lookup.loc[(row.season, row.week, opponent)] if opponent and (row.season, row.week, opponent) in lookup.index else None
        if isinstance(other, pd.DataFrame):
            other = other.iloc[0]
        if other is None:
            continue
        item = next((x for x in rows if x["team"] == str(row.team)), None)
        if item is None:
            item = {"entity_type": "TEAM_DEFENSE_DEF", "team": str(row.team), "position_model": "DEF", "canonical_player_id": f"DEF:{row.team}", "full_name": f"{row.team} D/ST", "raw_stats": {"sacks": 0.0, "interceptions": 0.0, "points_allowed": 0.0, "yards_allowed": 0.0}, "status": "BASELINE_ONLY", "stat_sources": {"sacks": "OPPONENT_SACKS_ALLOWED_BASELINE", "interceptions": "OPPONENT_INTERCEPTIONS_BASELINE", "points_allowed": "OPPONENT_POINTS_BASELINE", "yards_allowed": "OPPONENT_OFFENSE_YARDS_BASELINE"}, "blockers": ["MISSING_CANONICAL_PBP_FOR_FORCED_FUMBLES_RECOVERIES_AND_DEFENSIVE_TDS"]}
            rows.append(item)
        item["raw_stats"]["sacks"] += _number(other.get("sacks_allowed"))
        item["raw_stats"]["interceptions"] += _number(other.get("interceptions"))
        item["raw_stats"]["points_allowed"] += _number(other.get("points_scored"))
        item["raw_stats"]["yards_allowed"] += _number(other.get("passing_yards")) + _number(other.get("rushing_yards"))
    return rows


def _transitions(seasons: pd.DataFrame, id_cols: list[str], targets: Iterable[str]) -> pd.DataFrame:
    prev = seasons.copy()
    prev["target_season"] = pd.to_numeric(prev["season"], errors="coerce").astype(int) + 1
    keep = id_cols + ["target_season"] + ["games"] + list(targets)
    prev = prev[[x for x in keep if x in prev]].rename(columns={"games": "prev_games", **{x: f"prev_{x}" for x in targets}})
    current = seasons.copy().rename(columns={"season": "target_season", "games": "actual_games", **{x: f"actual_{x}" for x in targets}})
    return prev.merge(current[[*id_cols, "target_season", "actual_games", *[f"actual_{x}" for x in targets]]], on=[*id_cols, "target_season"], how="inner")


def _model(kind: str) -> Any:
    if kind == "RIDGE":
        return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", Ridge(alpha=12.0))])
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("model", HistGradientBoostingRegressor(loss="poisson", max_iter=80, max_leaf_nodes=9, l2_regularization=3.0, random_state=202609))])


def _feature_cols(trans: pd.DataFrame, targets: Iterable[str]) -> list[str]:
    cols = ["prev_games"]
    for target in targets:
        col = f"prev_{target}"
        if col in trans and pd.to_numeric(trans[col], errors="coerce").notna().any():
            cols.append(col)
    return cols


def _bootstrap_lower(deltas: list[float], rounds: int = 2000) -> float | None:
    if len(deltas) < 4:
        return None
    rng = np.random.default_rng(202609)
    values = np.asarray(deltas, dtype=float)
    means = [float(rng.choice(values, len(values), replace=True).mean()) for _ in range(rounds)]
    return float(np.quantile(means, 0.025))


def _fit_family(trans: pd.DataFrame, targets: Iterable[str], min_rows: int) -> tuple[dict[str, dict[str, Any]], dict[str, list[float]]]:
    targets = list(targets)
    features = _feature_cols(trans, targets)
    result: dict[str, dict[str, Any]] = {}
    residuals: dict[str, list[float]] = {}
    for target in targets:
        actual = f"actual_{target}"
        previous = f"prev_{target}"
        if actual not in trans or previous not in trans:
            result[target] = {"status": "DIAGNOSTIC_ONLY", "reason": "TARGET_COLUMN_UNAVAILABLE"}
            continue
        if pd.to_numeric(trans[actual], errors="coerce").notna().sum() == 0:
            result[target] = {"status": "DIAGNOSTIC_ONLY", "reason": "TARGET_COLUMN_UNAVAILABLE"}
            continue
        folds: list[dict[str, Any]] = []
        oof: dict[str, list[tuple[float, float]]] = {"RIDGE": [], "HGB": []}
        for test in (2022, 2023, 2024, 2025):
            tr = trans[trans.target_season < test].dropna(subset=[actual]).copy()
            te = trans[trans.target_season == test].dropna(subset=[actual]).copy()
            if len(tr) < min_rows or len(te) < min_rows:
                continue
            base = np.maximum(0.0, _num(te, [previous]).to_numpy() * np.minimum(17.0, np.maximum(1.0, _num(te, ["prev_games"]).to_numpy())) / np.maximum(1.0, _num(te, ["prev_games"]).to_numpy()))
            y = _num(te, [actual]).to_numpy()
            row: dict[str, Any] = {"test_season": test, "n_train": int(len(tr)), "n_test": int(len(te)), "baseline_mae": float(np.mean(np.abs(y - base)))}
            for kind in ("RIDGE", "HGB"):
                try:
                    m = _model(kind); m.fit(tr[features], _num(tr, [actual])); pred = np.maximum(0.0, m.predict(te[features]))
                    mae = float(np.mean(np.abs(y - pred)))
                    row[f"{kind.lower()}_mae"] = mae
                    oof[kind].extend((float(a), float(p)) for a, p in zip(y, pred))
                except Exception as exc:
                    row[f"{kind.lower()}_error"] = type(exc).__name__
            folds.append(row)
        candidates: list[tuple[str, float]] = []
        for kind in ("RIDGE", "HGB"):
            values = [f.get(f"{kind.lower()}_mae") for f in folds if f.get(f"{kind.lower()}_mae") is not None]
            if values:
                candidates.append((kind, float(np.mean(values))))
        chosen = min(candidates, key=lambda x: x[1])[0] if candidates else "BASELINE"
        improvements = []
        for fold in folds:
            value = fold.get(f"{chosen.lower()}_mae")
            if value is not None and fold["baseline_mae"] > 0:
                improvements.append((fold["baseline_mae"] - float(value)) / fold["baseline_mae"])
        ci_low = _bootstrap_lower(improvements)
        ready = len(folds) == 4 and len(improvements) == 4 and sum(x >= 0 for x in improvements) >= 3 and float(np.mean(improvements)) > 0 and ci_low is not None and ci_low > 0
        final_model = None
        if chosen != "BASELINE" and len(trans) >= min_rows:
            try:
                final_model = _model(chosen); final_model.fit(trans[features], _num(trans, [actual]))
            except Exception:
                final_model = None
        if chosen != "BASELINE" and oof.get(chosen):
            residuals[target] = [a - p for a, p in oof[chosen]]
        result[target] = {"status": "READY_RESEARCH_ONLY" if ready else "BASELINE_ONLY", "chosen": chosen, "features": features, "folds": folds, "mean_improvement": float(np.mean(improvements)) if improvements else None, "bootstrap_ci95_low": ci_low, "model": final_model}
    return result, residuals


def _predict_row(specs: Mapping[str, Any], values: Mapping[str, Any], targets: Iterable[str], cohort: Mapping[str, float]) -> tuple[dict[str, float], dict[str, str]]:
    out: dict[str, float] = {}
    sources: dict[str, str] = {}
    prev_games = max(1.0, _number(values.get("prev_games"), 0.0))
    for target in targets:
        spec = specs.get(target) or {}
        if spec.get("reason") == "TARGET_COLUMN_UNAVAILABLE":
            sources[target] = "BLOCKED_MISSING_SOURCE"
            continue
        if spec.get("status") == "READY_RESEARCH_ONLY" and spec.get("model") is not None:
            try:
                out[target] = max(0.0, float(spec["model"].predict(pd.DataFrame([values])[spec["features"]])[0]))
                sources[target] = str(spec.get("chosen"))
                continue
            except Exception:
                pass
        prev = _number(values.get(f"prev_{target}"), float("nan"))
        if math.isfinite(prev):
            out[target] = max(0.0, prev)
            sources[target] = "SHRUNK_PRIOR_SEASON_BASELINE"
        else:
            out[target] = max(0.0, _number(cohort.get(target), 0.0))
            sources[target] = "COHORT_BASELINE"
    return out, sources


def _cohort(seasons: pd.DataFrame, targets: Iterable[str]) -> dict[str, float]:
    games = pd.to_numeric(seasons.get("games"), errors="coerce").clip(lower=1)
    out: dict[str, float] = {}
    for target in targets:
        values = pd.to_numeric(seasons.get(target), errors="coerce") / games
        out[target] = float(values.median(skipna=True)) * 8.0 if values.notna().any() else 0.0
    return out


def _current_player_inputs(population: list[dict[str, Any]], seasons: pd.DataFrame) -> list[dict[str, Any]]:
    last = seasons[seasons.season == 2025].copy().set_index("canonical_player_id", drop=False)
    out = []
    for p in population:
        row = dict(p)
        hist = last.loc[p["canonical_player_id"]] if p["canonical_player_id"] in last.index else None
        if isinstance(hist, pd.DataFrame):
            hist = hist.iloc[-1]
        if hist is not None:
            row["prev_games"] = _number(hist.get("games"))
            for target in PLAYER_TARGETS[p["position_model"]]:
                row[f"prev_{target}"] = _number(hist.get(target))
        else:
            row["prev_games"] = None
        out.append(row)
    return out


RECONCILIATION_MAPPINGS = (
    ("qb_passing_attempts", "passing_attempts", "passing_attempts", {"QB"}),
    ("qb_completions", "completions", "completions", {"QB"}),
    ("player_receptions", "completions", "receptions", {"RB", "WR", "TE"}),
    ("player_targets", "targets", "targets", {"RB", "WR", "TE"}),
    ("qb_passing_yards", "passing_yards", "passing_yards", {"QB"}),
    ("player_receiving_yards", "passing_yards", "receiving_yards", {"RB", "WR", "TE"}),
    ("qb_passing_tds", "passing_tds", "passing_tds", {"QB"}),
    ("player_receiving_tds", "passing_tds", "receiving_tds", {"RB", "WR", "TE"}),
    ("qb_interceptions", "interceptions", "interceptions", {"QB"}),
    ("player_rushing_attempts", "rushing_attempts", "rushing_attempts", None),
    ("player_rushing_yards", "rushing_yards", "rushing_yards", None),
    ("player_rushing_tds", "rushing_tds", "rushing_tds", None),
)


BOUNDED_PLAYER_RELATIONS = (
    ("qb_completions", "completions", "passing_attempts", {"QB"}),
    ("player_receptions", "receptions", "targets", {"RB", "WR", "TE"}),
)


def _unallocated_row(team: str, relation: str, budget_target: str, player_target: str, positions: set[str] | None, value: float) -> dict[str, Any]:
    scope = "ALL" if positions is None else "-".join(sorted(positions))
    return {"entity_type": "UNALLOCATED", "team": team, "position_model": "UNALLOCATED", "canonical_player_id": f"UNALLOCATED:{team}:{relation}", "full_name": "Unallocated team share", "raw_stats": {player_target: value}, "identity_status": "UNALLOCATED", "status": "BASELINE_ONLY", "reconciliation_relation": relation, "budget_stat": budget_target, "player_stat": player_target, "position_scope": scope}


def _enforce_bounded_player_relations(grouped: Mapping[str, list[dict[str, Any]]], team_stats: Mapping[str, Mapping[str, float]], unallocated: list[dict[str, Any]]) -> None:
    """Keep individual caps true without losing a reconciled team aggregate.

    Scenario residuals are sampled independently.  A post-hoc ``min`` can therefore
    reduce completions/receptions after their team budget has already been allocated.
    Reallocate that volume to teammates with remaining capacity; if none exists,
    record the shortfall as the explicit unallocated share for that relation.
    """
    mappings = {relation: (budget_target, player_target, positions) for relation, budget_target, player_target, positions in RECONCILIATION_MAPPINGS}
    indexed = {(str(row.get("team") or ""), str(row.get("reconciliation_relation") or "")): row for row in unallocated}
    for team, rows in grouped.items():
        for relation, target, cap, positions in BOUNDED_PLAYER_RELATIONS:
            budget_target, _, _ = mappings[relation]
            relevant = [row for row in rows if row.get("position_model") in positions and target in row.get("raw_stats", {})]
            budget = max(0.0, _number((team_stats.get(team) or {}).get(budget_target)))
            unallocated_row = indexed.get((team, relation))
            # Re-run this relation from the actual team budget.  A previous
            # reconciliation pass may have recorded a provisional remainder;
            # subtracting it here double-counts the gap after individual caps
            # are applied.
            desired = budget
            for row in relevant:
                stats = row["raw_stats"]
                stats[target] = min(_number(stats.get(target)), _number(stats.get(cap)))
            allocated = sum(_number(row["raw_stats"].get(target)) for row in relevant)
            remaining = max(0.0, desired - allocated)
            while remaining > 1e-9:
                slack_rows = [(row, max(0.0, _number(row["raw_stats"].get(cap)) - _number(row["raw_stats"].get(target)))) for row in relevant]
                slack_rows = [(row, slack) for row, slack in slack_rows if slack > 1e-9]
                total_slack = sum(slack for _, slack in slack_rows)
                if total_slack <= 1e-9:
                    break
                distributed = 0.0
                for index, (row, slack) in enumerate(slack_rows):
                    add = min(slack, remaining if index == len(slack_rows) - 1 else remaining * (slack / total_slack))
                    row["raw_stats"][target] = _number(row["raw_stats"].get(target)) + add
                    distributed += add
                remaining = max(0.0, remaining - distributed)
            if unallocated_row is not None:
                # Replace the provisional first-pass remainder even when the
                # capped reallocation now fills the full team budget.
                unallocated_row["raw_stats"][target] = remaining
            elif remaining > 1e-9:
                if unallocated_row is None:
                    budget_target, player_target, scope = mappings[relation]
                    unallocated_row = _unallocated_row(team, relation, budget_target, player_target, scope, 0.0)
                    unallocated.append(unallocated_row)
                    indexed[(team, relation)] = unallocated_row
                # This is the authoritative post-cap remainder.
                unallocated_row["raw_stats"][target] = remaining


def _reconcile_players(player_rows: list[dict[str, Any]], team_stats: Mapping[str, Mapping[str, float]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Allocate every core team budget to the qualified active player pool.

    A core football forecast cannot leave passing, rushing or receiving volume
    as an artificial player.  Existing modeled volume determines the share;
    depth order supplies a deterministic fallback for a new/no-history player.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in player_rows:
        team = canonical_team_code(row.get("team"))
        row["team"] = team
        grouped.setdefault(team, []).append(row)
    unknown_teams = sorted(team for team in grouped if team not in team_stats)
    if unknown_teams:
        raise PreviewError(f"PLAYER_TEAM_WITHOUT_TEAM_BUDGET:{'|'.join(unknown_teams)}")
    empty_teams = sorted(team for team in team_stats if team not in grouped)
    if empty_teams:
        raise PreviewError(f"TEAM_BUDGET_WITHOUT_PLAYER_POPULATION:{'|'.join(empty_teams)}")
    by_relation = {name: (budget, stat, positions) for name, budget, stat, positions in RECONCILIATION_MAPPINGS}

    def allocate(rows: list[dict[str, Any]], budget: float, stat: str, positions: set[str] | None, cap: str | None = None) -> None:
        if budget <= 1e-9:
            return
        candidates = [r for r in rows if positions is None or r.get("position_model") in positions]
        if not candidates:
            return
        weights = [_number(r.get("raw_stats", {}).get(stat)) for r in candidates]
        if positions == {"QB"}:
            # The available roster depth chart is an opportunity prior, not an
            # instruction to divide a 17-game passing budget equally among a
            # starter and contingency quarterbacks with cohort baselines.
            role = {1: 1.0, 2: 0.03, 3: 0.005}
            weights = [weight * role.get(int(_number(row.get("depth_chart_order"), 9)), 0.001) for row, weight in zip(candidates, weights)]
        if sum(weights) <= 1e-9:
            weights = [1.0 / max(1.0, _number(r.get("depth_chart_order"), 9.0)) for r in candidates]
        if cap is None:
            total = sum(weights)
            for row, weight in zip(candidates, weights):
                row["raw_stats"][stat] = budget * weight / total
            return
        # Allocate capped volume greedily by current modeled share, then by
        # remaining capacity, guaranteeing completions <= attempts and
        # receptions <= targets while retaining the full team budget.
        remaining = budget
        capacity = [max(0.0, _number(r["raw_stats"].get(cap))) for r in candidates]
        if sum(capacity) + 1e-6 < budget:
            raise PreviewError(f"CORE_CAPACITY_BELOW_BUDGET:{stat}:{cap}")
        assigned = [0.0] * len(candidates)
        while remaining > 1e-7:
            eligible = [i for i, value in enumerate(capacity) if value - assigned[i] > 1e-9]
            if not eligible:
                raise PreviewError(f"CORE_ALLOCATION_EXHAUSTED:{stat}")
            denom = sum(weights[i] for i in eligible) or float(len(eligible))
            moved = 0.0
            for i in eligible:
                want = remaining * ((weights[i] / denom) if denom else 1.0 / len(eligible))
                add = min(want, capacity[i] - assigned[i])
                assigned[i] += add; moved += add
            remaining -= moved
        for row, value in zip(candidates, assigned): row["raw_stats"][stat] = value

    # Dependency order matters: volume caps must exist before constrained stats.
    order = ["qb_passing_attempts", "player_targets", "qb_passing_yards", "qb_passing_tds", "qb_interceptions", "player_receiving_yards", "player_receiving_tds", "player_rushing_attempts", "player_rushing_yards", "player_rushing_tds", "qb_completions", "player_receptions"]
    for team, rows in grouped.items():
        for relation in order:
            budget_target, player_target, positions = by_relation[relation]
            cap = "passing_attempts" if relation == "qb_completions" else ("targets" if relation == "player_receptions" else None)
            allocate(rows, max(0.0, _number((team_stats.get(team) or {}).get(budget_target))), player_target, positions, cap)
    # A no-candidate fixture/contract failure remains explicit.  In the real
    # active roster build this must be empty; it is not used to hide volume.
    unallocated = []
    for team, rows in grouped.items():
        for relation, budget_target, stat, positions in RECONCILIATION_MAPPINGS:
            budget = max(0.0, _number((team_stats.get(team) or {}).get(budget_target)))
            relevant = [r for r in rows if positions is None or r.get("position_model") in positions]
            if budget > 1e-9 and not relevant:
                unallocated.append(_unallocated_row(team, relation, budget_target, stat, positions, budget))
    return player_rows, unallocated


def _reconciliation_audit(player_rows: list[dict[str, Any]], team_stats: Mapping[str, Mapping[str, float]], unallocated: list[dict[str, Any]]) -> dict[str, Any]:
    """Return exact p50 allocation accounting for every declared relationship."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in player_rows:
        grouped.setdefault(str(row.get("team") or ""), []).append(row)
    unallocated_by_relation: dict[tuple[str, str], float] = {}
    for row in unallocated:
        key = (str(row.get("team") or ""), str(row.get("reconciliation_relation") or ""))
        value = sum(_number(v) for v in (row.get("raw_stats") or {}).values())
        unallocated_by_relation[key] = unallocated_by_relation.get(key, 0.0) + value
    relations: list[dict[str, Any]] = []
    failures: list[str] = []
    for team in sorted(team_stats):
        rows = grouped.get(team, [])
        for relation, budget_target, player_target, positions in RECONCILIATION_MAPPINGS:
            allocated = sum(_number((row.get("raw_stats") or {}).get(player_target)) for row in rows if positions is None or row.get("position_model") in positions)
            budget = max(0.0, _number((team_stats.get(team) or {}).get(budget_target)))
            # Derive the published accounting remainder from the final player
            # allocation.  This prevents stale diagnostic rows from influencing
            # the accounting proof after a bounded reallocation.
            remainder = max(0.0, budget - allocated)
            residual = budget - allocated - remainder
            record = {"team": team, "relation": relation, "budget_stat": budget_target, "player_stat": player_target, "budget": budget, "allocated": allocated, "unallocated": remainder, "unallocated_share": (remainder / budget) if budget else 0.0, "residual": residual}
            relations.append(record)
            if abs(residual) > 1e-6 or allocated - budget > 1e-6:
                failures.append(f"{team}:{relation}")
    if failures:
        raise PreviewError(f"RECONCILIATION_ACCOUNTING_FAILURE:{'|'.join(failures)}")
    by_relation: dict[str, dict[str, float]] = {}
    for relation, _, _, _ in RECONCILIATION_MAPPINGS:
        matching = [row for row in relations if row["relation"] == relation]
        budget = sum(_number(row["budget"]) for row in matching)
        unallocated_value = sum(_number(row["unallocated"]) for row in matching)
        by_relation[relation] = {"budget": budget, "unallocated": unallocated_value, "unallocated_share": (unallocated_value / budget) if budget else 0.0}
    return {"relations": relations, "by_relation": by_relation, "relation_count": len(relations), "maximum_absolute_residual": max((abs(_number(x["residual"])) for x in relations), default=0.0), "unallocated_rows": len(unallocated), "unallocated_share_limit": 0.05, "constraints": ["completions_lte_passing_attempts", "receptions_lte_targets"]}


def _scenario_rows(players: list[dict[str, Any]], residuals: Mapping[str, list[float]], team_stats: Mapping[str, Mapping[str, float]], seed: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for scenario in range(SCENARIOS):
        sample: list[dict[str, Any]] = []
        for player in players:
            base = player["raw_stats"]
            stats = {}
            # One shared volume shock preserves carries/targets/attempts with
            # their yards and scores; it deliberately replaces independent
            # scalar sampling that created impossible stat lines.
            if scenario == 0:
                volume = 1.0
            else:
                sign = 1.0 if scenario % 2 else -1.0
                volume = max(0.25, 1.0 + sign * abs(float(rng.normal(0.0, .24))))
            for target, value in base.items():
                stats[target] = max(0.0, _number(value) * volume)
            clone = {k: v for k, v in player.items() if k != "raw_stats"} | {"raw_stats": stats}
            sample.append(clone)
        sample, _ = _reconcile_players(sample, team_stats)
        # The bounded completion/reception allocation can move player volume after
        # the first pass has normalized each independent stat family.  Reconcile
        # once more from that bounded state so the emitted scenario is a fixed
        # point for every declared player-to-team relationship.
        sample, scenario_unallocated = _reconcile_players(sample, team_stats)
        for player in [*sample, *scenario_unallocated]:
            item = {"scenario_id": scenario, "canonical_player_id": player["canonical_player_id"], "team": player["team"], "position_model": player["position_model"], "raw_stats": player["raw_stats"]}
            if player.get("reconciliation_relation"):
                item["reconciliation_relation"] = player["reconciliation_relation"]
            rows.append(item)
    return rows


def _quantile_stats(scenarios: list[dict[str, Any]], pid: str, fallback: Mapping[str, float]) -> dict[str, dict[str, float]]:
    matched = [r["raw_stats"] for r in scenarios if r["canonical_player_id"] == pid]
    keys = sorted(set(fallback) | set().union(*(set(x) for x in matched)))
    out = {key: {f"p{int(q * 100):02d}": float(np.quantile([_number(s.get(key)) for s in matched], q)) if matched else _number(fallback.get(key)) for q in QUANTILES} for key in keys}
    for key in keys:
        out[key]["p50"] = _number(fallback.get(key))
    return out


def _team_prediction_inputs(team_seasons: pd.DataFrame) -> list[dict[str, Any]]:
    last = team_seasons[team_seasons.season == 2025].copy()
    out = []
    for _, row in last.iterrows():
        item = {"team": str(row.team), "prev_games": 17.0}
        for target in TEAM_TARGETS:
            item[f"prev_{target}"] = _number(row.get(target))
        out.append(item)
    return out


def build_general_preview(root: Path, baseline_path: Path, cache_dir: Path, output_root: Path, offline: bool = False, seed: int = 202609) -> dict[str, Any]:
    baseline = load_baseline(root, baseline_path)
    population, pop_meta = canonical_population(root, baseline)
    raw_players, raw_teams, history_sources = _load_history(cache_dir, SEASONS, offline)
    for source in history_sources:
        try:
            source["path"] = str(Path(source["path"]).resolve().relative_to(root))
        except ValueError:
            source["path"] = str(source["path"])
    player_week = _standard_player_week(raw_players)
    team_week = _standard_team_week(raw_teams, player_week)
    player_seasons = _player_seasons(player_week)
    team_seasons = _team_seasons(team_week)
    player_specs: dict[str, dict[str, Any]] = {}
    player_residuals: dict[str, list[float]] = {}
    for pos in POSITIONS:
        seasonal = player_seasons[player_seasons.position_model == pos].copy()
        trans = _transitions(seasonal, ["canonical_player_id", "position_model"], PLAYER_TARGETS[pos])
        specs, residuals = _fit_family(trans, PLAYER_TARGETS[pos], min_rows=40)
        player_specs[pos] = specs
        player_residuals.update(residuals)
    team_trans = _transitions(team_seasons.assign(games=17.0), ["team"], TEAM_TARGETS)
    team_specs, team_residuals = _fit_family(team_trans, TEAM_TARGETS, min_rows=28)
    player_rows: list[dict[str, Any]] = []
    for values in _current_player_inputs(population, player_seasons):
        pos = values["position_model"]
        stats, sources = _predict_row(player_specs[pos], values, PLAYER_TARGETS[pos], _cohort(player_seasons[player_seasons.position_model == pos], PLAYER_TARGETS[pos]))
        status = "BLOCKED_IDENTITY" if values["identity_status"] != "READY" else ("READY_RESEARCH_ONLY" if any((player_specs[pos].get(k) or {}).get("status") == "READY_RESEARCH_ONLY" for k in stats) else "BASELINE_ONLY")
        player_rows.append({**values, "entity_type": "PLAYER", "raw_stats": stats, "stat_sources": sources, "status": status})
    team_rows: list[dict[str, Any]] = []
    team_stats: dict[str, dict[str, float]] = {}
    cohort_team = _cohort(team_seasons.assign(games=17.0), TEAM_TARGETS)
    for values in _team_prediction_inputs(team_seasons):
        stats, sources = _predict_row(team_specs, values, TEAM_TARGETS, cohort_team)
        team_stats[values["team"]] = stats
        status = "READY_RESEARCH_ONLY" if any((team_specs.get(k) or {}).get("status") == "READY_RESEARCH_ONLY" for k in stats) else "BASELINE_ONLY"
        team_rows.append({**values, "entity_type": "TEAM_OFFENSE", "raw_stats": stats, "stat_sources": sources, "status": status})
    # Specialist data is represented explicitly.  The DEF baseline uses mirrored
    # team totals; individual K allocation and sparse D/ST events stay blocked
    # until a point-in-time PBP/role contract is supplied.
    team_rows.extend(_defense_baselines(team_week))
    for team in sorted(team_stats):
        team_rows.append({"entity_type": "TEAM_KICKING", "team": team, "position_model": "K", "canonical_player_id": f"K:{team}", "full_name": f"{team} team kicking", "raw_stats": {}, "stat_sources": {}, "status": "BLOCKED_MISSING_SOURCE", "blockers": ["CANONICAL_PRESEASON_KICKER_ROLE_AND_PBP_EVENT_HISTORY_NOT_BOUND"]})
    player_rows, unallocated = _reconcile_players(player_rows, team_stats)
    reconciliation = _reconciliation_audit(player_rows, team_stats, unallocated)
    scenarios = _scenario_rows(player_rows, player_residuals, team_stats, seed)
    output_players = []
    for row in [*player_rows, *unallocated]:
        expected_games = max(1.0, min(17.0, _number(row.get("prev_games"), 8.0))) if row.get("position_model") != "UNALLOCATED" else None
        conditional = {key: (_number(value) / expected_games if expected_games else None) for key, value in row["raw_stats"].items()}
        output_players.append({k: v for k, v in row.items() if k not in {"raw_stats"}} | {"expected_games_p50": expected_games, "expected_games_source": "SHRUNK_PRIOR_SEASON_GAMES_BASELINE" if expected_games else "NOT_APPLICABLE", "conditional_per_game_p50": conditional, "availability_adjusted_season_total_p50": row["raw_stats"], "raw_stat_p50": row["raw_stats"], "raw_stat_quantiles": _quantile_stats(scenarios, row["canonical_player_id"], row["raw_stats"])})
    output_teams = [{k: v for k, v in row.items() if k not in {"raw_stats"}} | {"raw_stat_p50": row["raw_stats"]} for row in team_rows]
    validation = {"player": {pos: {target: {k: v for k, v in spec.items() if k != "model"} for target, spec in specs.items()} for pos, specs in player_specs.items()}, "team": {target: {k: v for k, v in spec.items() if k != "model"} for target, spec in team_specs.items()}, "reconciliation": reconciliation}
    manifest = {"schema": SCHEMA, "season": 2026, "status": "READY_RESEARCH_ONLY", "generated_at": baseline["source_cutoff"], "seed": seed, "baseline": {"path": str(baseline_path.relative_to(root)), "sha256": sha256_file(baseline_path), "source_cutoff": baseline["source_cutoff"]}, "population": pop_meta, "history_sources": history_sources, "governance": {"research_only": True, "production_model": "M9", "m9_changed": False, "m10_changed": False, "app_runtime_changed": False, "canonical_rankings_changed": False, "adp_used_as_football_feature": False}, "artifacts": {"players": "player-stat-projections.csv", "teams": "team-stat-projections.csv", "validation": "validation.json", "scenarios": "joint-scenarios.jsonl.gz", "report": "general-preview.md"}}
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv_immutable(output_root / "player-stat-projections.csv", output_players)
    _write_csv_immutable(output_root / "team-stat-projections.csv", output_teams)
    _first_write(output_root / "validation.json", canonical_bytes(validation) + b"\n")
    scenario_bytes = b"".join(canonical_bytes(x) + b"\n" for x in scenarios)
    _first_write(output_root / "joint-scenarios.jsonl.gz", gzip.compress(scenario_bytes, mtime=0))
    lines = ["# FIE 2026 General Season Preview", "", "League-neutral raw football forecasts. Fantasy scoring, ADP, roster demand and ranks are intentionally excluded.", "", f"- Cutoff: `{baseline['source_cutoff']}`", f"- Players: `{len(population)}`; identity blockers: `{pop_meta['blocked_identity']}`", f"- Team rows: `{len(team_rows)}`", f"- Unallocated reconciliation rows: `{len(unallocated)}`", "", "## Publication status", "", "`READY_RESEARCH_ONLY` is not production promotion. `BASELINE_ONLY` is a transparent forecast where no challenger cleared the full gate."]
    _first_write(output_root / "general-preview.md", ("\n".join(lines) + "\n").encode())
    _first_write(output_root / "manifest.json", canonical_bytes(manifest) + b"\n")
    return manifest


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _phase_a_manifest(path: Path) -> dict[str, Any]:
    manifest = _read_json(path)
    if manifest.get("schema") != SCHEMA:
        raise PreviewError("PHASE_A_SCHEMA_MISMATCH")
    return manifest


def apply_leagues(root: Path, baseline_path: Path, phase_a_root: Path, output_root: Path) -> dict[str, Any]:
    baseline = load_baseline(root, baseline_path)
    manifest_path = phase_a_root / "manifest.json"
    manifest = _phase_a_manifest(manifest_path)
    if str((manifest.get("baseline") or {}).get("sha256") or "") != sha256_file(baseline_path):
        raise PreviewError("PHASE_A_BASELINE_BINDING_MISMATCH")
    for name in ("player-stat-projections.csv", "joint-scenarios.jsonl.gz"):
        if not (phase_a_root / name).is_file():
            raise PreviewError(f"PHASE_A_ARTIFACT_MISSING:{name}")
    players = _load_csv_rows(phase_a_root / "player-stat-projections.csv")
    with gzip.open(phase_a_root / "joint-scenarios.jsonl.gz", "rt", encoding="utf-8") as handle:
        scenarios = [json.loads(line) for line in handle if line.strip()]
    by_scenario: dict[int, list[dict[str, Any]]] = {}
    for row in scenarios:
        by_scenario.setdefault(int(row["scenario_id"]), []).append(row)
    league_outputs = []
    for league in baseline["leagues"]:
        lid = str(league.get("league_id"))
        profile_src = (league.get("sources") or {}).get("profile")
        if not isinstance(profile_src, dict):
            raise PreviewError(f"MISSING_PROFILE_BINDING:{lid}")
        profile_path = _verify_source(root, profile_src, f"profile:{lid}")
        profile = _read_json(profile_path)
        if str(profile.get("profile_fingerprint") or "") != str(league.get("profile_fingerprint") or "") or str(profile.get("scoring_signature") or "") != str(league.get("scoring_signature") or ""):
            raise PreviewError(f"PROFILE_FINGERPRINT_DRIFT:{lid}")
        scoring = profile.get("scoring_settings") or {}
        values: dict[str, list[float]] = {}
        unsupported: set[str] = set()
        for scenario_rows in by_scenario.values():
            frame_rows = []
            for row in scenario_rows:
                if row["position_model"] not in POSITIONS:
                    continue
                frame_rows.append({"canonical_player_id": row["canonical_player_id"], "position_model": row["position_model"], **row["raw_stats"]})
            if frame_rows:
                frame = pd.DataFrame(frame_rows)
                points = score_rows(frame, scoring)
                for pid, value in zip(frame.canonical_player_id.astype(str), points):
                    values.setdefault(pid, []).append(float(value))
        rows = []
        for player in players:
            pid = str(player.get("canonical_player_id") or "")
            pos = str(player.get("position_model") or "")
            if pos not in POSITIONS:
                continue
            vals = values.get(pid) or []
            status = str(player.get("status") or "DIAGNOSTIC_ONLY")
            if status.startswith("BLOCKED") or not vals:
                status = "BLOCKED_MISSING_PHASE_A_SCENARIO"
            rows.append({"league_id": lid, "league_format": profile.get("format"), "profile_fingerprint": profile.get("profile_fingerprint"), "scoring_signature": profile.get("scoring_signature"), "canonical_player_id": pid, "full_name": player.get("full_name"), "position_model": pos, "team": player.get("team"), "status": status, "fantasy_points_p10": float(np.quantile(vals, .10)) if vals else None, "fantasy_points_p25": float(np.quantile(vals, .25)) if vals else None, "fantasy_points_p50": float(np.quantile(vals, .50)) if vals else None, "fantasy_points_p75": float(np.quantile(vals, .75)) if vals else None, "fantasy_points_p90": float(np.quantile(vals, .90)) if vals else None, "source": "GENERAL_PREVIEW_PHASE_A_EXACT_SCENARIO_REPLAY", "unsupported_scoring_keys": sorted(unsupported)})
        league_outputs.extend(rows)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv_immutable(output_root / "league-player-projections.csv", league_outputs)
    payload = {"schema": "fie-league-preview-v2", "season": 2026, "status": "READY_RESEARCH_ONLY", "phase_a_manifest_sha256": sha256_file(manifest_path), "baseline_sha256": sha256_file(baseline_path), "league_count": len(baseline["leagues"]), "row_count": len(league_outputs), "governance": {"research_only": True, "m9_changed": False, "app_runtime_changed": False, "canonical_rankings_changed": False, "adp_used_as_football_feature": False, "season_preview_v1_overwritten": False}}
    _first_write(output_root / "manifest.json", canonical_bytes(payload) + b"\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="FIE general season-preview Phase A/B")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-general")
    build.add_argument("--baseline", default="data/research/baselines/2026/baseline-v1.json")
    build.add_argument("--cache-dir", default=".cache/general-season-preview")
    build.add_argument("--output-root", default="data/research/evaluation/2026/preseason/general-preview-v4")
    build.add_argument("--offline", action="store_true")
    build.add_argument("--seed", type=int, default=202609)
    replay = sub.add_parser("apply-leagues")
    replay.add_argument("--baseline", default="data/research/baselines/2026/baseline-v1.json")
    replay.add_argument("--phase-a-root", default="data/research/evaluation/2026/preseason/general-preview-v4")
    replay.add_argument("--output-root", default="data/research/evaluation/2026/preseason/league-preview-v5")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    try:
        if args.command == "build-general":
            out = build_general_preview(root, _repo_path(root, args.baseline), _repo_path(root, args.cache_dir), _repo_path(root, args.output_root), args.offline, args.seed)
            print(f"General preview: {out['status']} players={out['population']['players']}")
        else:
            out = apply_leagues(root, _repo_path(root, args.baseline), _repo_path(root, args.phase_a_root), _repo_path(root, args.output_root))
            print(f"League preview: {out['status']} leagues={out['league_count']} rows={out['row_count']}")
    except (PreviewError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"General season preview fail-closed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

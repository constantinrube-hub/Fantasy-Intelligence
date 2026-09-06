#!/usr/bin/env python3
"""Window 2B: Trench Research + Thin Integration.

Chronologically tests whether Window 2A team trench evidence adds predictive
value beyond a fixed player-form baseline. The benchmark is deliberately
research-only. It never changes M9, canonical rankings, runtime projections,
waiver values, or market/ADP handling.

Key controls
------------
* Same-row comparison: baseline and challenger are fitted/evaluated on exactly
  the same complete-case rows within every position/family benchmark.
* Historical features are pregame: Window 2A snapshots contain only plays from
  weeks strictly before the target week.
* Player-form features are lagged within season and never use target-week
  fantasy points.
* Chronological folds train only on seasons strictly before the test season.
* Ridge alpha and all validation gates are fixed in advance; no tuning or
  winner-picking is performed.
* Missing trench values are never zero-imputed.
* A validated family is exposed only through a research-context registry.
  Production use requires a separate formal promotion decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "fie-window2b-trench-research-v1"
THIN_SCHEMA = "fie-window2b-trench-thin-integration-v1"
PLAYER_STATS_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
UA = "Fantasy-Intelligence-Window2B/1.0"
BASELINE_FEATURES = ("fp_prior1", "fp_prior4_mean", "fp_season_to_date_mean", "prior_games")

# Pre-specified families. QB-hit rates are intentionally not part of the
# confirmatory family because Window 2A classifies them as optional evidence.
FAMILIES = {
    "QB": {
        "PASS_PROTECTION_FRONT_CORE": (
            "own_sack_rate_allowed",
            "opp_sack_rate_generated",
        ),
    },
    "RB": {
        "RUN_BLOCK_FRONT_CORE": (
            "own_rush_epa_per_attempt",
            "own_rush_success_rate",
            "own_stuff_rate_allowed",
            "opp_rush_epa_allowed_per_attempt",
            "opp_rush_success_rate_allowed",
            "opp_stuff_rate_forced",
        ),
    },
    "WR": {
        "PASS_PROTECTION_FRONT_CORE": (
            "own_sack_rate_allowed",
            "opp_sack_rate_generated",
        ),
    },
    "TE": {
        "PASS_PROTECTION_FRONT_CORE": (
            "own_sack_rate_allowed",
            "opp_sack_rate_generated",
        ),
    },
}

GATES = {
    "min_total_eval_rows": 300,
    "min_test_folds": 3,
    "min_test_rows_per_fold": 25,
    "min_train_rows_per_fold": 100,
    "min_relative_mae_improvement": 0.005,
    "min_relative_rmse_improvement": 0.0,
    "min_fold_win_share": 0.60,
    "max_single_fold_mae_deterioration": 0.05,
    "bootstrap_ci_level": 0.95,
    "bootstrap_draws": 2000,
    "ridge_alpha": 10.0,
    "minimum_prior_player_games": 2,
}

TEAM_ALIASES = {"JAC": "JAX", "JAX": "JAX", "LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV"}


class ResearchError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_team(value: Any) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_seasons(value: str) -> list[int]:
    out: list[int] = []
    for token in str(value or "").replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(token))
    return sorted(set(out))


def download_player_stats(season: int, cache_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"stats_player_week_{int(season)}.csv"
    url = PLAYER_STATS_URL.format(season=int(season))
    if out.exists() and out.stat().st_size > 1000:
        return out, {"season": int(season), "url": url, "status": "AVAILABLE_CACHE", "sha256": sha256_file(out), "bytes": out.stat().st_size}
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            with tempfile.NamedTemporaryFile(delete=False, dir=str(cache_dir), suffix=".tmp") as handle:
                shutil.copyfileobj(response, handle)
                tmp = Path(handle.name)
        if tmp.stat().st_size <= 1000:
            tmp.unlink(missing_ok=True)
            raise ResearchError("PLAYER_STATS_DOWNLOAD_TOO_SMALL")
        tmp.replace(out)
        return out, {"season": int(season), "url": url, "status": "AVAILABLE_LIVE", "sha256": sha256_file(out), "bytes": out.stat().st_size}
    except Exception as exc:
        return None, {"season": int(season), "url": url, "status": "UNAVAILABLE", "sha256": None, "bytes": None, "error": f"{type(exc).__name__}:{exc}"}


def _value(row: pd.Series, names: Iterable[str], default: float = 0.0) -> float:
    for name in names:
        if name in row.index:
            v = finite(row.get(name))
            if v is not None:
                return v
    return float(default)


def ppr_target(row: pd.Series) -> float | None:
    """Stable screening target for QB/RB/WR/TE only, not league scoring."""
    direct = finite(row.get("fantasy_points_ppr")) if "fantasy_points_ppr" in row.index else None
    if direct is not None:
        return direct
    # nflverse aliases are intentionally explicit. This is standard PPR and is
    # used only to screen for incremental football signal.
    value = (
        0.04 * _value(row, ("passing_yards",))
        + 4.0 * _value(row, ("passing_tds",))
        - 2.0 * _value(row, ("interceptions", "passing_interceptions"))
        + 0.1 * _value(row, ("rushing_yards",))
        + 6.0 * _value(row, ("rushing_tds",))
        + 1.0 * _value(row, ("receptions",))
        + 0.1 * _value(row, ("receiving_yards",))
        + 6.0 * _value(row, ("receiving_tds",))
        - 2.0 * _value(row, ("rushing_fumbles_lost", "receiving_fumbles_lost", "fumbles_lost"))
    )
    return float(value) if math.isfinite(value) else None


def canonical_position(value: Any) -> str:
    p = str(value or "").strip().upper()
    return p if p in {"QB", "RB", "WR", "TE"} else ""


def prepare_player_rows(raw: pd.DataFrame, season: int) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    required = {"week", "team", "opponent_team"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ResearchError("PLAYER_STATS_REQUIRED_COLUMNS_MISSING:" + ",".join(missing))
    if "season_type" in raw.columns:
        raw = raw[raw["season_type"].astype(str).str.upper().eq("REG")].copy()
    if "season" in raw.columns:
        raw = raw[pd.to_numeric(raw["season"], errors="coerce").eq(int(season))].copy()
    pos_col = "position" if "position" in raw.columns else ("position_group" if "position_group" in raw.columns else None)
    id_col = "player_id" if "player_id" in raw.columns else None
    if pos_col is None or id_col is None:
        raise ResearchError("PLAYER_STATS_ID_OR_POSITION_MISSING")
    raw["position_model"] = raw[pos_col].map(canonical_position)
    raw = raw[raw["position_model"].ne("")].copy()
    raw["player_id"] = raw[id_col].astype(str)
    raw["season"] = int(season)
    raw["week"] = pd.to_numeric(raw["week"], errors="coerce")
    raw = raw[raw["week"].notna()].copy()
    raw["week"] = raw["week"].astype(int)
    raw["team"] = raw["team"].map(normalize_team)
    raw["opponent_team"] = raw["opponent_team"].map(normalize_team)
    raw["fantasy_target"] = raw.apply(ppr_target, axis=1)
    raw = raw[raw["fantasy_target"].notna() & raw["team"].ne("") & raw["opponent_team"].ne("")].copy()
    raw = raw.sort_values(["player_id", "week"]).drop_duplicates(["player_id", "week"], keep="last")

    # All baseline signals use only prior games from the same season.
    group = raw.groupby("player_id", sort=False)["fantasy_target"]
    raw["fp_prior1"] = group.shift(1)
    raw["fp_prior4_mean"] = group.transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    raw["fp_season_to_date_mean"] = group.transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    raw["prior_games"] = group.cumcount().astype(float)
    return raw


def load_player_matrix(seasons: Iterable[int], cache_dir: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    for season in sorted({int(x) for x in seasons}):
        path, status = download_player_stats(season, cache_dir)
        provenance.append(status)
        if path is None:
            continue
        try:
            raw = pd.read_csv(path, low_memory=False)
            frames.append(prepare_player_rows(raw, season))
        except Exception as exc:
            status["status"] = f"BLOCKED_PARSE:{type(exc).__name__}:{exc}"
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), provenance


def flatten_trench_history(root: Path, seasons: Iterable[int]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for season in sorted({int(x) for x in seasons}):
        path = root / "data" / "research" / "trench" / "historical" / f"season_{season}-v1.json"
        if not path.exists():
            provenance.append({"season": season, "path": str(path.relative_to(root)), "status": "MISSING"})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        provenance.append({"season": season, "path": str(path.relative_to(root)), "status": "AVAILABLE", "sha256": sha256_file(path)})
        if not payload.get("target_week_realised_stats_excluded"):
            raise ResearchError(f"TRENCH_LEAKAGE_GUARD_MISSING:{season}")
        for snapshot in payload.get("snapshots") or []:
            if snapshot.get("status") != "READY_RESEARCH_ONLY":
                continue
            target_week = int(snapshot.get("target_week") or 0)
            max_input_week = snapshot.get("max_input_week")
            if max_input_week is not None and int(max_input_week) >= target_week:
                raise ResearchError(f"TRENCH_TARGET_WEEK_LEAKAGE:{season}:{target_week}:{max_input_week}")
            for team, team_row in (snapshot.get("teams") or {}).items():
                off = team_row.get("offense") or {}
                deff = team_row.get("defense") or {}
                rows.append({
                    "season": season,
                    "week": target_week,
                    "team": normalize_team(team),
                    "own_sack_rate_allowed": finite(off.get("sack_rate_allowed")),
                    "own_qb_hit_rate_allowed": finite(off.get("qb_hit_rate_allowed")),
                    "own_rush_epa_per_attempt": finite(off.get("rush_epa_per_attempt")),
                    "own_rush_success_rate": finite(off.get("rush_success_rate")),
                    "own_stuff_rate_allowed": finite(off.get("stuff_rate_allowed")),
                    "own_offense_proxy": finite(off.get("research_proxy_v1")),
                    "own_sack_rate_generated": finite(deff.get("sack_rate_generated")),
                    "own_qb_hit_rate_generated": finite(deff.get("qb_hit_rate_generated")),
                    "own_rush_epa_allowed_per_attempt": finite(deff.get("rush_epa_allowed_per_attempt")),
                    "own_rush_success_rate_allowed": finite(deff.get("rush_success_rate_allowed")),
                    "own_stuff_rate_forced": finite(deff.get("stuff_rate_forced")),
                    "own_defense_proxy": finite(deff.get("research_proxy_v1")),
                })
    return pd.DataFrame(rows), provenance


def join_trench(player_rows: pd.DataFrame, trench: pd.DataFrame) -> pd.DataFrame:
    if player_rows.empty or trench.empty:
        return pd.DataFrame()
    key = ["season", "week", "team"]
    own = trench.copy()
    joined = player_rows.merge(own, on=key, how="left", validate="many_to_one")
    opp = trench.rename(columns={
        "team": "opponent_team",
        "own_sack_rate_generated": "opp_sack_rate_generated",
        "own_qb_hit_rate_generated": "opp_qb_hit_rate_generated",
        "own_rush_epa_allowed_per_attempt": "opp_rush_epa_allowed_per_attempt",
        "own_rush_success_rate_allowed": "opp_rush_success_rate_allowed",
        "own_stuff_rate_forced": "opp_stuff_rate_forced",
        "own_defense_proxy": "opp_defense_proxy",
    })
    keep = [
        "season", "week", "opponent_team",
        "opp_sack_rate_generated", "opp_qb_hit_rate_generated",
        "opp_rush_epa_allowed_per_attempt", "opp_rush_success_rate_allowed",
        "opp_stuff_rate_forced", "opp_defense_proxy",
    ]
    joined = joined.merge(opp[keep], on=["season", "week", "opponent_team"], how="left", validate="many_to_one")
    return joined


def fixed_model(alpha: float) -> Pipeline:
    return Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=float(alpha)))])


def metric_summary(y: np.ndarray, pred: np.ndarray) -> tuple[float, float]:
    err = y - pred
    return float(np.mean(np.abs(err))), float(np.sqrt(np.mean(np.square(err))))


def bootstrap_mean_ci(values: np.ndarray, *, draws: int, level: float, seed: int) -> tuple[float | None, float | None]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return None, None
    rng = np.random.default_rng(int(seed))
    # Chunk draws to keep memory bounded even for large WR/TE samples.
    means = np.empty(int(draws), dtype=float)
    n = len(values)
    for i in range(int(draws)):
        means[i] = float(np.mean(values[rng.integers(0, n, size=n)]))
    a = (1.0 - float(level)) / 2.0
    return float(np.quantile(means, a)), float(np.quantile(means, 1.0 - a))


@dataclass
class FoldResult:
    test_season: int
    train_rows: int
    test_rows: int
    baseline_mae: float
    challenger_mae: float
    relative_mae_improvement: float
    baseline_rmse: float
    challenger_rmse: float
    relative_rmse_improvement: float


def validate_family(
    frame: pd.DataFrame,
    *,
    position: str,
    family: str,
    feature_names: Iterable[str],
    gates: dict[str, Any] | None = None,
    seed: int = 20260906,
) -> dict[str, Any]:
    gates = dict(GATES if gates is None else gates)
    features = list(feature_names)
    required = ["season", "fantasy_target", *BASELINE_FEATURES, *features]
    missing_cols = [c for c in required if c not in frame.columns]
    if missing_cols:
        return {"position": position, "family": family, "status": "BLOCKED_REQUIRED_COLUMNS_MISSING", "missing_columns": missing_cols, "features": features}

    subset = frame[frame["position_model"].eq(position)].copy()
    subset = subset[subset["prior_games"] >= float(gates["minimum_prior_player_games"])].copy()
    # Exact same complete-case rows for baseline and challenger.
    subset = subset.dropna(subset=["fantasy_target", *BASELINE_FEATURES, *features]).copy()
    subset = subset[np.isfinite(subset[["fantasy_target", *BASELINE_FEATURES, *features]].to_numpy(dtype=float)).all(axis=1)].copy()
    if subset.empty:
        return {"position": position, "family": family, "status": "BLOCKED_INSUFFICIENT_EVIDENCE", "features": features, "same_row_comparison": True, "complete_case_rows": 0, "folds": []}

    folds: list[FoldResult] = []
    row_improvements: list[float] = []
    seasons = sorted(int(x) for x in subset["season"].unique())
    for test_season in seasons:
        train = subset[subset["season"] < test_season]
        test = subset[subset["season"] == test_season]
        if train["season"].nunique() < 2:
            continue
        if len(train) < int(gates["min_train_rows_per_fold"]) or len(test) < int(gates["min_test_rows_per_fold"]):
            continue
        y_train = train["fantasy_target"].to_numpy(dtype=float)
        y_test = test["fantasy_target"].to_numpy(dtype=float)
        xb_train = train[list(BASELINE_FEATURES)].to_numpy(dtype=float)
        xb_test = test[list(BASELINE_FEATURES)].to_numpy(dtype=float)
        xc_train = train[[*BASELINE_FEATURES, *features]].to_numpy(dtype=float)
        xc_test = test[[*BASELINE_FEATURES, *features]].to_numpy(dtype=float)

        baseline = fixed_model(gates["ridge_alpha"])
        challenger = fixed_model(gates["ridge_alpha"])
        baseline.fit(xb_train, y_train)
        challenger.fit(xc_train, y_train)
        bp = baseline.predict(xb_test)
        cp = challenger.predict(xc_test)
        b_mae, b_rmse = metric_summary(y_test, bp)
        c_mae, c_rmse = metric_summary(y_test, cp)
        mae_rel = (b_mae - c_mae) / b_mae if b_mae > 0 else 0.0
        rmse_rel = (b_rmse - c_rmse) / b_rmse if b_rmse > 0 else 0.0
        folds.append(FoldResult(test_season, len(train), len(test), b_mae, c_mae, float(mae_rel), b_rmse, c_rmse, float(rmse_rel)))
        row_improvements.extend((np.abs(y_test - bp) - np.abs(y_test - cp)).tolist())

    if len(folds) < int(gates["min_test_folds"]):
        return {
            "position": position, "family": family, "status": "BLOCKED_INSUFFICIENT_EVIDENCE", "features": features,
            "same_row_comparison": True, "complete_case_rows": int(len(subset)), "test_fold_count": len(folds),
            "minimum_test_folds": int(gates["min_test_folds"]), "folds": [f.__dict__ for f in folds],
        }

    total_n = sum(f.test_rows for f in folds)
    weighted_b_mae = sum(f.baseline_mae * f.test_rows for f in folds) / total_n
    weighted_c_mae = sum(f.challenger_mae * f.test_rows for f in folds) / total_n
    # RMSE is recomputed from fold RMSE^2 weighted by n.
    weighted_b_rmse = math.sqrt(sum((f.baseline_rmse ** 2) * f.test_rows for f in folds) / total_n)
    weighted_c_rmse = math.sqrt(sum((f.challenger_rmse ** 2) * f.test_rows for f in folds) / total_n)
    rel_mae = (weighted_b_mae - weighted_c_mae) / weighted_b_mae if weighted_b_mae > 0 else 0.0
    rel_rmse = (weighted_b_rmse - weighted_c_rmse) / weighted_b_rmse if weighted_b_rmse > 0 else 0.0
    win_share = sum(1 for f in folds if f.relative_mae_improvement > 0) / len(folds)
    worst_fold = min(f.relative_mae_improvement for f in folds)
    improvements = np.asarray(row_improvements, dtype=float)
    ci_low, ci_high = bootstrap_mean_ci(improvements, draws=int(gates["bootstrap_draws"]), level=float(gates["bootstrap_ci_level"]), seed=seed)
    mean_abs_error_improvement = float(np.mean(improvements)) if len(improvements) else None

    checks = {
        "enough_total_eval_rows": total_n >= int(gates["min_total_eval_rows"]),
        "positive_minimum_relative_mae_gain": rel_mae >= float(gates["min_relative_mae_improvement"]),
        "rmse_not_worse": rel_rmse >= float(gates["min_relative_rmse_improvement"]),
        "fold_win_share": win_share >= float(gates["min_fold_win_share"]),
        "no_catastrophic_fold": worst_fold >= -float(gates["max_single_fold_mae_deterioration"]),
        "bootstrap_ci_lower_above_zero": ci_low is not None and ci_low > 0.0,
    }
    status = "RESEARCH_VALIDATED_CANDIDATE" if all(checks.values()) else "BLOCKED_NOT_VALIDATED"
    return {
        "position": position,
        "family": family,
        "status": status,
        "features": features,
        "same_row_comparison": True,
        "complete_case_rows": int(len(subset)),
        "evaluation_rows": int(total_n),
        "test_fold_count": len(folds),
        "test_seasons": [f.test_season for f in folds],
        "baseline_mae": float(weighted_b_mae),
        "challenger_mae": float(weighted_c_mae),
        "mean_incremental_mae_improvement": float(rel_mae),
        "baseline_rmse": float(weighted_b_rmse),
        "challenger_rmse": float(weighted_c_rmse),
        "mean_incremental_rmse_improvement": float(rel_rmse),
        "mean_absolute_error_improvement_points": mean_abs_error_improvement,
        "bootstrap_ci95_low": ci_low,
        "bootstrap_ci95_high": ci_high,
        "fold_win_share": float(win_share),
        "worst_fold_mae_improvement": float(worst_fold),
        "gate_checks": checks,
        "folds": [f.__dict__ for f in folds],
    }


def build_thin_integration(results: list[dict[str, Any]], source_bindings: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for r in results:
        validated = r.get("status") == "RESEARCH_VALIDATED_CANDIDATE"
        rows.append({
            "position": r.get("position"),
            "family": r.get("family"),
            "status": r.get("status"),
            "feature_names": r.get("features") or [],
            "enabled": bool(validated),
            "allowed_surface": "research_context_only" if validated else "none",
            "prohibited_surfaces": ["production_projection", "canonical_ranking", "waiver_value", "runtime", "automatic_model_promotion"],
            "evidence_reference": {"mean_incremental_mae_improvement": r.get("mean_incremental_mae_improvement"), "bootstrap_ci95_low": r.get("bootstrap_ci95_low")},
        })
    return {
        "schema": THIN_SCHEMA,
        "schema_version": 1,
        "generated_at": utc_now(),
        "research_only": True,
        "production_model": "M9",
        "automatic_promotion": False,
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "adp_used_as_football_feature": False,
        "source_bindings": source_bindings,
        "candidate_context": rows,
    }


def markdown_report(payload: dict[str, Any], thin: dict[str, Any]) -> str:
    lines = [
        "# FIE Window 2B: Trench Research + Thin Integration", "",
        "## Governance", "",
        "This is a research-only chronological benchmark. M9 remains the production champion. A validated trench family may appear only as research context; it does not change projections, canonical rankings, waiver values, runtime behavior, or ADP handling.", "",
        "## Validation design", "",
        "- Baseline and challenger use exactly the same complete-case player rows.",
        "- Window 2A trench features use only weeks strictly before the target week.",
        "- Player-form baseline uses only prior games from the same season.",
        "- Each test season is predicted by models trained only on earlier seasons.",
        "- Ridge alpha and all gates are fixed before seeing results; no hyperparameter tuning or family winner-picking occurs.",
        "- Standard PPR is only a cross-league screening target. Any production promotion would still require the normal league-scoring governance path.", "",
        "## Results", "",
        "| Position | Family | Status | OOS rows | Folds | MAE improvement | CI low | RMSE improvement | Fold wins |", 
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in payload.get("results") or []:
        def pct(x: Any) -> str:
            v = finite(x)
            return "—" if v is None else f"{100*v:+.2f}%"
        ci = finite(r.get("bootstrap_ci95_low"))
        lines.append(
            f"| {r.get('position')} | {r.get('family')} | {r.get('status')} | {r.get('evaluation_rows', 0)} | {r.get('test_fold_count', 0)} | {pct(r.get('mean_incremental_mae_improvement'))} | {'—' if ci is None else f'{ci:+.3f} pts'} | {pct(r.get('mean_incremental_rmse_improvement'))} | {pct(r.get('fold_win_share'))} |"
        )
    lines += ["", "## D/ST", "", "D/ST is intentionally `BLOCKED_TARGET_CONTRACT_NOT_BOUND` in Window 2B. The player-week screening target is not a trustworthy D/ST fantasy-scoring target, so no synthetic team-defense outcome is invented.", "", "## Thin integration", ""]
    enabled = [x for x in thin.get("candidate_context") or [] if x.get("enabled")]
    if enabled:
        for x in enabled:
            lines.append(f"- {x['position']} / {x['family']}: research-context only ({', '.join(x['feature_names'])}).")
    else:
        lines.append("- No family cleared every pre-specified gate. Thin integration remains empty and fail-closed.")
    lines += ["", "## Interpretation", "", "A blocked result is a valid scientific outcome. Correlation, intuitive football logic, or a single winning season is not sufficient for integration. Window 2C can consume only the explicit research-context registry, never an unvalidated trench proxy.", ""]
    return "\n".join(lines)


def run_research(*, root: Path, seasons: Iterable[int], cache_dir: Path, output_dir: Path, seed: int = 20260906) -> dict[str, Any]:
    seasons = sorted({int(x) for x in seasons})
    trench, trench_provenance = flatten_trench_history(root, seasons)
    players, player_provenance = load_player_matrix(seasons, cache_dir)
    if trench.empty:
        raise ResearchError("NO_WINDOW2A_TRENCH_HISTORY_AVAILABLE")
    if players.empty:
        raise ResearchError("NO_PLAYER_WEEK_EVIDENCE_AVAILABLE")
    joined = join_trench(players, trench)
    results: list[dict[str, Any]] = []
    for position, families in FAMILIES.items():
        for family, features in families.items():
            results.append(validate_family(joined, position=position, family=family, feature_names=features, seed=seed))
    results.append({
        "position": "D/ST", "family": "TRENCH_MATCHUP_CONTEXT", "status": "BLOCKED_TARGET_CONTRACT_NOT_BOUND",
        "features": [], "same_row_comparison": True,
        "reason": "nflverse player-week standard-PPR screening target is not a trustworthy D/ST fantasy target",
    })
    source_bindings = {"window2a_history": trench_provenance, "player_week": player_provenance}
    payload = {
        "schema": SCHEMA,
        "schema_version": 1,
        "generated_at": utc_now(),
        "research_only": True,
        "production_model": "M9",
        "automatic_promotion": False,
        "canonical_rankings_changed": False,
        "runtime_changed": False,
        "waiver_values_changed": False,
        "adp_used_as_football_feature": False,
        "seasons": seasons,
        "screening_target": "standard_ppr_player_week",
        "screening_target_scope": ["QB", "RB", "WR", "TE"],
        "screening_target_warning": "research screening only; not a replacement for per-league scoring replay",
        "baseline_features": list(BASELINE_FEATURES),
        "fixed_gates": GATES,
        "source_bindings": source_bindings,
        "joined_row_count": int(len(joined)),
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "window2b-trench-research-v1.json"
    thin_path = output_dir / "thin-integration-v1.json"
    md_path = output_dir / "window2b-trench-research-v1.md"
    atomic_json(json_path, payload)
    thin = build_thin_integration(results, source_bindings={"research_result": {"path": str(json_path.relative_to(root)), "sha256": sha256_file(json_path)}})
    atomic_json(thin_path, thin)
    md_path.write_text(markdown_report(payload, thin), encoding="utf-8")
    return {
        "status": "READY_RESEARCH_ONLY",
        "research": str(json_path.relative_to(root)),
        "thin_integration": str(thin_path.relative_to(root)),
        "markdown": str(md_path.relative_to(root)),
        "validated_candidate_count": sum(1 for r in results if r.get("status") == "RESEARCH_VALIDATED_CANDIDATE"),
        "blocked_count": sum(1 for r in results if str(r.get("status") or "").startswith("BLOCKED")),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Window 2B trench research + thin integration")
    ap.add_argument("--seasons", default="2019-2025")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--cache-dir", default=".cache/window2b-player-stats")
    ap.add_argument("--output-dir", default="data/research/evaluation/2026/trench")
    ap.add_argument("--seed", type=int, default=20260906)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    cache = Path(args.cache_dir)
    if not cache.is_absolute():
        cache = root / cache
    out = Path(args.output_dir)
    if not out.is_absolute():
        out = root / out
    result = run_research(root=root, seasons=parse_seasons(args.seasons), cache_dir=cache, output_dir=out, seed=args.seed)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

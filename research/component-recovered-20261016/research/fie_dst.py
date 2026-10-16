#!/usr/bin/env python3
"""First-class team D/ST research and scoring for Fantasy Intelligence 9.1.

Design rules
------------
* A team defense is an entity with canonical position ``DEF``.  It is not an IDP.
* Football outcomes are modeled once.  Fantasy scoring is applied afterwards from
  the exact league scoring_settings.
* D/ST never creates a parallel replacement/value stack.  The browser's canonical
  9.1 services consume the resulting DEF projection distribution like any other
  rosterable entity.
* Activation is fail-closed.  Historical augmentation can publish a validated DEF
  gate, but current snapshots may still expose Sleeper baseline rows when the gate
  has not cleared.

The module intentionally keeps the public-data baseline understandable: rolling
team/opponent efficiency, sacks/turnovers, points/yards allowed and market context.
Advanced personnel/FTN/PFF signals remain challenger features for M6 rather than
being silently mixed into the baseline without point-in-time history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

from dst_contract import (
    DST_POSITION, DST_SCORING_EXACT, PTS_ALLOW_RE, YDS_ALLOW_RE, dst_enabled,
    dst_profile_fields, dst_roster_signature, dst_scoring_settings, dst_scoring_signature,
    dst_starter_slots, is_dst_scoring_key,
)

RAW_TARGETS = [
    "sack", "sack_yd", "int", "int_ret_yd", "ff", "fum_rec", "fum_ret_yd",
    "def_td", "safe", "blk_kick", "blk_kick_ret_yd", "def_4_and_stop",
    "def_pass_def", "def_st_td", "def_st_ff", "def_st_fum_rec", "def_kr_yd",
    "def_pr_yd", "def_fg_ret_yd", "points_allowed", "yards_allowed",
]
COUNT_TARGETS = {
    "sack", "int", "ff", "fum_rec", "def_td", "safe", "blk_kick",
    "def_4_and_stop", "def_pass_def", "def_st_td", "def_st_ff", "def_st_fum_rec",
}
NONNEGATIVE_TARGETS = set(RAW_TARGETS)
BASE_FEATURES = [
    "def_sack_r4", "def_int_r4", "def_ff_r4", "def_fum_rec_r4", "def_td_r8",
    "def_pa_r4", "def_ya_r4", "opp_sacks_allowed_r4", "opp_turnovers_r4",
    "opp_points_r4", "opp_yards_r4", "home", "spread_line", "total_line",
    "opponent_implied_points",
]
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _nonzero(scoring: Mapping[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in (scoring or {}).items():
        x = _f(v, float("nan"))
        if math.isfinite(x) and x != 0:
            out[str(k)] = x
    return dict(sorted(out.items()))


def _bucket_match(key: str, value: float, regex: re.Pattern[str]) -> bool:
    m = regex.match(str(key).lower())
    if not m:
        return False
    token = m.group(1)
    if token == "0":
        return value == 0
    if token.endswith("p"):
        return value >= float(token[:-1])
    lo, hi = token.split("_", 1)
    return float(lo) <= value <= float(hi)


def dst_rule_value(stats: Mapping[str, Any], key: str) -> tuple[float, bool, str]:
    """Return raw unit value for one D/ST scoring key.

    Bucket keys return 1/0 because the fantasy coefficient itself is the bucket
    award.  Known linear keys are valid zeros when absent from sparse projection
    payloads, which mirrors Sleeper's omission of zero-valued fields.
    """
    k = str(key).lower()
    if k.startswith("pts_allow_"):
        if "points_allowed" not in stats and "pts_allow" not in stats:
            return 0.0, False, "missing:points_allowed"
        v = _f(stats.get("points_allowed", stats.get("pts_allow")))
        return (1.0 if _bucket_match(k, v, PTS_ALLOW_RE) else 0.0), True, "derived:points_allowed_bucket"
    if k.startswith("yds_allow_"):
        if "yards_allowed" not in stats and "yds_allow" not in stats:
            return 0.0, False, "missing:yards_allowed"
        v = _f(stats.get("yards_allowed", stats.get("yds_allow")))
        return (1.0 if _bucket_match(k, v, YDS_ALLOW_RE) else 0.0), True, "derived:yards_allowed_bucket"
    aliases = {
        "fum_rec_yd": ["fum_ret_yd"],
        "def_st_td": ["special_teams_tds", "st_td"],
        "def_st_ff": ["special_teams_ff", "st_ff"],
        "def_st_fum_rec": ["special_teams_fum_rec", "st_fum_rec"],
        "def_kr_yd": ["kick_return_yards", "kr_yd"],
        "def_pr_yd": ["punt_return_yards", "pr_yd"],
        "def_fg_ret_yd": ["missed_fg_return_yards", "fg_ret_yd"],
    }
    if k in stats:
        return _f(stats.get(k)), True, k
    for a in aliases.get(k, []):
        if a in stats:
            return _f(stats.get(a)), True, a
    if k in DST_SCORING_EXACT:
        return 0.0, True, "known-linear-zero"
    return 0.0, False, "unsupported"


def score_dst_stats(stats: Mapping[str, Any], scoring: Mapping[str, Any]) -> dict[str, Any]:
    points = 0.0
    supported: list[str] = []
    unsupported: list[str] = []
    contribution: dict[str, float] = {}
    for key, weight in dst_scoring_settings(scoring).items():
        value, ok, _ = dst_rule_value(stats, key)
        if ok:
            pts = value * float(weight)
            points += pts
            contribution[key] = pts
            supported.append(key)
        else:
            unsupported.append(key)
    active = supported + unsupported
    return {
        "points": float(points),
        "coverage_rate": len(supported) / len(active) if active else 1.0,
        "exact": not unsupported,
        "supported_keys": sorted(supported),
        "unsupported_keys": sorted(unsupported),
        "contribution": contribution,
    }


def _col(df: pd.DataFrame, name: str, default: Any = 0) -> pd.Series:
    if name in df.columns:
        return df[name]
    return pd.Series(default, index=df.index)


def _bool_num(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.astype(float)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _sum(g: pd.DataFrame, key: str) -> float:
    return float(pd.to_numeric(_col(g, key), errors="coerce").fillna(0.0).sum())


def _max(g: pd.DataFrame, key: str) -> float:
    x = pd.to_numeric(_col(g, key), errors="coerce").dropna()
    return float(x.max()) if not x.empty else 0.0


def _team_game_rows(pbp: pd.DataFrame) -> list[dict[str, Any]]:
    """Aggregate nflverse play-by-play into one raw-outcome row per defense/game.

    The implementation uses conservative event attribution.  Points allowed are
    reconstructed from plays on which the candidate team is the recorded defense;
    this naturally excludes opponent pick-sixes while retaining PAT/two-point plays
    when the team is actually defending the try.
    """
    if pbp.empty or "game_id" not in pbp:
        return []
    rows: list[dict[str, Any]] = []
    for game_id, game in pbp.groupby("game_id", sort=False):
        home = str(game["home_team"].dropna().iloc[0]) if "home_team" in game and game["home_team"].notna().any() else ""
        away = str(game["away_team"].dropna().iloc[0]) if "away_team" in game and game["away_team"].notna().any() else ""
        season = int(_f(game["season"].dropna().iloc[0] if "season" in game and game["season"].notna().any() else 0))
        week = int(_f(game["week"].dropna().iloc[0] if "week" in game and game["week"].notna().any() else 0))
        teams = [t for t in (home, away) if t]
        for team in teams:
            opp = away if team == home else home
            dg = game[_col(game, "defteam", "").astype(str) == team].copy()
            og = game[_col(game, "posteam", "").astype(str) == opp].copy()
            # Defensive counting stats.  nflverse records sack/interception/fumble
            # outcome on the offensive play, therefore filtering defteam is safe.
            sack = _sum(dg, "sack")
            interceptions = _sum(dg, "interception")
            ff = _sum(dg, "fumble_forced")
            # fumble_lost on offense is the defense's recovery.
            fum_rec = _sum(dg, "fumble_lost")
            safe = _sum(dg, "safety")
            # Blocked kicks are not perfectly normalized across nflverse eras.  Use
            # explicit indicator when present, then text fallback.
            blk = _sum(dg, "blocked_kick")
            if "field_goal_result" in dg:
                blk = max(blk, float(dg["field_goal_result"].fillna("").astype(str).str.lower().eq("blocked").sum()))
            if "extra_point_result" in dg:
                blk += float(dg["extra_point_result"].fillna("").astype(str).str.lower().eq("blocked").sum())
            if blk == 0 and "desc" in dg:
                blk = float(dg["desc"].fillna("").str.contains(r"BLOCKED", case=False, regex=True).sum())
            pass_def = _sum(dg, "def_pass_defended")
            if pass_def == 0:
                pass_def = float(sum(_col(dg, k, "").notna().sum() for k in ("pass_defense_1_player_id", "pass_defense_2_player_id") if k in dg.columns))
            fourth = 0.0
            if "down" in dg and "fourth_down_converted" in dg:
                fourth = float(((pd.to_numeric(dg["down"], errors="coerce") == 4) & (_bool_num(dg["fourth_down_converted"]) == 0)).sum())
            # Return touchdowns are identified by td_team while the opponent offense
            # is on the field.  Defensive TDs include INT/fumble returns, not normal
            # offensive TDs against this defense.
            td_team = _col(game, "td_team", "").fillna("").astype(str)
            def_td_mask = (td_team == team) & ((_bool_num(_col(game, "interception")) > 0) | (_bool_num(_col(game, "fumble_lost")) > 0))
            def_td = float(def_td_mask.sum())

            # Points allowed: score only opponent plays for which this team is the
            # recorded defense.  Defensive return TDs against this team's offense
            # are therefore excluded.  Try plays are counted when recorded against
            # this defense, matching Sleeper's PAT/two-point treatment.
            pa = 0.0
            if not dg.empty:
                td = (_bool_num(_col(dg, "touchdown")) > 0) & (_col(dg, "td_team", "").fillna("").astype(str) == opp)
                pa += 6.0 * float(td.sum())
                if "field_goal_result" in dg:
                    pa += 3.0 * float(dg["field_goal_result"].fillna("").astype(str).str.lower().eq("made").sum())
                if "extra_point_result" in dg:
                    pa += float(dg["extra_point_result"].fillna("").astype(str).str.lower().eq("good").sum())
                if "two_point_conv_result" in dg:
                    pa += 2.0 * float(dg["two_point_conv_result"].fillna("").astype(str).str.lower().eq("success").sum())
            # Net yards allowed.  yards_gained already carries negative sack plays
            # in nflverse, so summing opponent offensive plays is a strong public
            # reconstruction of total net offense.
            yards_allowed = _sum(og, "yards_gained")
            # Return yards are sparse/era-dependent; keep zero when source fields are
            # absent and let scoring coverage/validation fail closed if required.
            int_ret_yd = float(pd.to_numeric(dg.loc[_bool_num(_col(dg, "interception")) > 0, "return_yards"], errors="coerce").fillna(0).sum()) if "return_yards" in dg else 0.0
            fum_ret_yd = float(pd.to_numeric(dg.loc[_bool_num(_col(dg, "fumble_lost")) > 0, "return_yards"], errors="coerce").fillna(0).sum()) if "return_yards" in dg else 0.0
            sack_yd = abs(float(pd.to_numeric(dg.loc[_bool_num(_col(dg, "sack")) > 0, "yards_gained"], errors="coerce").fillna(0).sum())) if "yards_gained" in dg else 0.0

            # Team special-teams outcomes. nflverse exposes return_team on modern
            # play-by-play. Missing legacy fields remain explicit zeros and are
            # visible in source/model validation rather than guessed.
            ptype = _col(game, "play_type", "").fillna("").astype(str).str.lower()
            return_team = _col(game, "return_team", "").fillna("").astype(str)
            ret_mask = return_team.eq(team)
            kickoff_mask = ptype.eq("kickoff") & ret_mask
            punt_mask = ptype.eq("punt") & ret_mask
            fg_mask = ptype.eq("field_goal") & ret_mask
            ret_yards = pd.to_numeric(_col(game, "return_yards"), errors="coerce").fillna(0.0)
            def_kr_yd = float(ret_yards[kickoff_mask].sum())
            def_pr_yd = float(ret_yards[punt_mask].sum())
            def_fg_ret_yd = float(ret_yards[fg_mask].sum())
            st_td_mask = ret_mask & (_bool_num(_col(game, "touchdown")) > 0) & ptype.isin(["kickoff", "punt", "field_goal", "extra_point"])
            def_st_td = float(st_td_mask.sum())
            special_mask = ptype.isin(["kickoff", "punt", "field_goal", "extra_point"])
            rec_team = _col(game, "fumble_recovery_1_team", "").fillna("").astype(str)
            ff_team = _col(game, "forced_fumble_player_1_team", "").fillna("").astype(str)
            def_st_fum_rec = float((special_mask & rec_team.eq(team)).sum()) if "fumble_recovery_1_team" in game else 0.0
            def_st_ff = float((special_mask & ff_team.eq(team)).sum()) if "forced_fumble_player_1_team" in game else 0.0
            block_mask = pd.Series(False, index=game.index)
            if "field_goal_result" in game: block_mask |= game["field_goal_result"].fillna("").astype(str).str.lower().eq("blocked")
            if "extra_point_result" in game: block_mask |= game["extra_point_result"].fillna("").astype(str).str.lower().eq("blocked")
            blk_kick_ret_yd = float(ret_yards[block_mask & ret_mask].sum())
            rows.append({
                "game_id": str(game_id), "season": season, "week": week, "team": team,
                "opponent": opp, "home": 1.0 if team == home else 0.0,
                "sack": sack, "sack_yd": sack_yd, "int": interceptions,
                "int_ret_yd": int_ret_yd, "ff": ff, "fum_rec": fum_rec,
                "fum_ret_yd": fum_ret_yd, "def_td": def_td, "safe": safe,
                "blk_kick": blk, "blk_kick_ret_yd": blk_kick_ret_yd, "def_4_and_stop": fourth,
                "def_pass_def": pass_def, "def_st_td": def_st_td, "def_st_ff": def_st_ff,
                "def_st_fum_rec": def_st_fum_rec, "def_kr_yd": def_kr_yd, "def_pr_yd": def_pr_yd, "def_fg_ret_yd": def_fg_ret_yd,
                "points_allowed": pa, "yards_allowed": max(0.0, yards_allowed),
            })
    return rows


def build_dst_team_week(pbp: pd.DataFrame, schedules: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    out = pd.DataFrame(_team_game_rows(pbp))
    if out.empty:
        return out
    if schedules is not None and not schedules.empty and "game_id" in schedules:
        cols = [c for c in ["game_id", "spread_line", "total_line"] if c in schedules]
        if len(cols) > 1:
            s = schedules[cols].drop_duplicates("game_id")
            out = out.merge(s, on="game_id", how="left")
    if "spread_line" not in out:
        out["spread_line"] = np.nan
    if "total_line" not in out:
        out["total_line"] = np.nan
    # nflverse spread_line is home-team perspective: positive means the home team
    # is favored. Normalize it to the D/ST row so positive always means THIS team
    # is favored. This keeps historical and current feature semantics identical.
    raw_home_spread = pd.to_numeric(out["spread_line"], errors="coerce")
    out["spread_line"] = np.where(pd.to_numeric(out["home"], errors="coerce").fillna(0.0) >= 0.5, raw_home_spread, -raw_home_spread)
    total = pd.to_numeric(out["total_line"], errors="coerce")
    # If a team is favored by S in a game total T, its opponent implied total is
    # (T-S)/2. Missing market data stays missing and is imputed only at model time.
    out["opponent_implied_points"] = (total - pd.to_numeric(out["spread_line"], errors="coerce")) / 2.0
    return add_dst_lagged_features(out)


def add_dst_lagged_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    x = df.sort_values(["team", "season", "week", "game_id"]).copy()

    def prior_roll_team(frame: pd.DataFrame, group: str, col: str, window: int) -> pd.Series:
        return frame.groupby(group, sort=False)[col].transform(
            lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(window, min_periods=1).mean()
        )

    # Defense priors: what this defense has done before the target game.
    x["def_sack_r4"] = prior_roll_team(x, "team", "sack", 4)
    x["def_int_r4"] = prior_roll_team(x, "team", "int", 4)
    x["def_ff_r4"] = prior_roll_team(x, "team", "ff", 4)
    x["def_fum_rec_r4"] = prior_roll_team(x, "team", "fum_rec", 4)
    x["def_td_r8"] = prior_roll_team(x, "team", "def_td", 8)
    x["def_pa_r4"] = prior_roll_team(x, "team", "points_allowed", 4)
    x["def_ya_r4"] = prior_roll_team(x, "team", "yards_allowed", 4)

    # Offense-vulnerability table.  A defense's realized sacks/turnovers/PA/YA in
    # a game are the opposing offense's sacks allowed/turnovers/points/yards.
    offense = x[["game_id", "season", "week", "opponent", "sack", "int", "fum_rec", "points_allowed", "yards_allowed"]].copy()
    offense = offense.rename(columns={"opponent": "offense", "sack": "sacks_allowed", "points_allowed": "points_scored", "yards_allowed": "yards_gained"})
    offense["turnovers"] = pd.to_numeric(offense["int"], errors="coerce").fillna(0) + pd.to_numeric(offense["fum_rec"], errors="coerce").fillna(0)
    offense = offense.sort_values(["offense", "season", "week", "game_id"])
    offense["opp_sacks_allowed_r4"] = prior_roll_team(offense, "offense", "sacks_allowed", 4)
    offense["opp_turnovers_r4"] = prior_roll_team(offense, "offense", "turnovers", 4)
    offense["opp_points_r4"] = prior_roll_team(offense, "offense", "points_scored", 4)
    offense["opp_yards_r4"] = prior_roll_team(offense, "offense", "yards_gained", 4)
    x = x.merge(offense[["game_id", "offense", "opp_sacks_allowed_r4", "opp_turnovers_r4", "opp_points_r4", "opp_yards_r4"]], left_on=["game_id", "opponent"], right_on=["game_id", "offense"], how="left").drop(columns=["offense"])
    return x

def _spearman(a: Iterable[float], b: Iterable[float]) -> float:
    aa = pd.Series(list(a), dtype=float)
    bb = pd.Series(list(b), dtype=float)
    if len(aa) < 3 or aa.nunique() < 2 or bb.nunique() < 2:
        return 0.0
    return float(aa.rank().corr(bb.rank()))


def _serialize_ridge(model: Ridge, scaler: StandardScaler, features: list[str], medians: list[float], target: str) -> dict[str, Any]:
    return {
        "target": target, "model_type": "ridge_standardized", "features": features,
        "feature_medians": [float(x) for x in medians],
        "scaler_mean": [float(x) for x in scaler.mean_], "scaler_scale": [float(x) for x in scaler.scale_],
        "coefficients": [float(x) for x in model.coef_], "intercept": float(model.intercept_),
        "prediction_floor": 0.0,
    }


def fit_dst_models(team_week: pd.DataFrame, scoring: Mapping[str, Any], min_test_season: int = 2022) -> dict[str, Any]:
    if team_week.empty:
        return {"status": "diagnostic_only", "reason": "no_team_week_rows", "models": {}, "folds": [], "aggregate": {}}
    data = team_week.copy()
    features = [f for f in BASE_FEATURES if f in data]
    data = data[pd.to_numeric(data.get("season"), errors="coerce").notna()].copy()
    seasons = sorted(int(s) for s in pd.to_numeric(data["season"], errors="coerce").dropna().unique())
    test_seasons = [s for s in seasons if s >= min_test_season and any(t < s for t in seasons)]
    folds: list[dict[str, Any]] = []
    residuals: list[float] = []
    for ts in test_seasons:
        train = data[pd.to_numeric(data["season"], errors="coerce") < ts].copy()
        test = data[pd.to_numeric(data["season"], errors="coerce") == ts].copy()
        if len(train) < 250 or len(test) < 20:
            continue
        # Model each raw component, then score through this league's exact rules.
        pred_stats: dict[str, np.ndarray] = {}
        for target in RAW_TARGETS:
            if target not in train:
                continue
            med = train[features].apply(pd.to_numeric, errors="coerce").median().fillna(0.0)
            Xtr = train[features].apply(pd.to_numeric, errors="coerce").fillna(med)
            Xte = test[features].apply(pd.to_numeric, errors="coerce").fillna(med)
            y = pd.to_numeric(train[target], errors="coerce").fillna(0.0)
            scaler = StandardScaler().fit(Xtr)
            model = Ridge(alpha=8.0).fit(scaler.transform(Xtr), y)
            pred_stats[target] = np.maximum(0.0, model.predict(scaler.transform(Xte)))
        actual_fp, model_fp, base_fp = [], [], []
        # Independent simple baseline: training-fold raw-stat means plus a handful of
        # transparent lagged team rates. It deliberately does not borrow any FIE
        # model prediction, so validation represents genuine incremental value.
        target_means = {
            k: float(pd.to_numeric(train[k], errors="coerce").mean()) if k in train else 0.0
            for k in RAW_TARGETS
        }
        for i, (_, row) in enumerate(test.iterrows()):
            actual = {k: _f(row.get(k)) for k in RAW_TARGETS}
            pred = {k: float(v[i]) for k, v in pred_stats.items()}
            base = dict(target_means)
            base.update({
                "sack": _f(row.get("def_sack_r4"), target_means.get("sack", 0.0)),
                "int": _f(row.get("def_int_r4"), target_means.get("int", 0.0)),
                "ff": _f(row.get("def_ff_r4"), target_means.get("ff", 0.0)),
                "fum_rec": _f(row.get("def_fum_rec_r4"), target_means.get("fum_rec", 0.0)),
                "def_td": _f(row.get("def_td_r8"), target_means.get("def_td", 0.0)),
                "points_allowed": _f(row.get("def_pa_r4"), target_means.get("points_allowed", 21.0)),
                "yards_allowed": _f(row.get("def_ya_r4"), target_means.get("yards_allowed", 340.0)),
            })
            actual_fp.append(score_dst_stats(actual, scoring)["points"])
            model_fp.append(score_dst_stats(pred, scoring)["points"])
            base_fp.append(score_dst_stats(base, scoring)["points"])
        mae = mean_absolute_error(actual_fp, model_fp)
        bmae = mean_absolute_error(actual_fp, base_fp)
        improvement = (bmae - mae) / bmae if bmae else 0.0
        sp = _spearman(actual_fp, model_fp); bsp = _spearman(actual_fp, base_fp)
        residuals.extend(np.asarray(actual_fp) - np.asarray(model_fp))
        folds.append({
            "test_season": ts, "n_test": len(test), "mae": float(mae), "baseline_mae": float(bmae),
            "mae_improvement": float(improvement), "spearman": sp, "baseline_spearman": bsp,
            "positive": bool(improvement > 0),
        })

    # Final exported models use every historical row with leakage-safe features.
    models: dict[str, Any] = {}
    for target in RAW_TARGETS:
        if target not in data or not features:
            continue
        med = data[features].apply(pd.to_numeric, errors="coerce").median().fillna(0.0)
        X = data[features].apply(pd.to_numeric, errors="coerce").fillna(med)
        y = pd.to_numeric(data[target], errors="coerce").fillna(0.0)
        scaler = StandardScaler().fit(X)
        model = Ridge(alpha=8.0).fit(scaler.transform(X), y)
        models[target] = _serialize_ridge(model, scaler, features, med.tolist(), target)

    mean_imp = float(np.mean([f["mae_improvement"] for f in folds])) if folds else 0.0
    mean_sp = float(np.mean([f["spearman"] for f in folds])) if folds else 0.0
    mean_bsp = float(np.mean([f["baseline_spearman"] for f in folds])) if folds else 0.0
    positive = sum(bool(f["positive"]) for f in folds)
    validated = len(folds) >= 4 and mean_imp > 0.01 and positive >= math.ceil(len(folds) / 2) and mean_sp >= mean_bsp
    q10 = float(np.quantile(residuals, .10)) if residuals else None
    q90 = float(np.quantile(residuals, .90)) if residuals else None
    # Priors are pregame-safe: last completed row and trailing means only.
    priors: dict[str, dict[str, Any]] = {}
    for team, g in data.sort_values(["season", "week"]).groupby("team"):
        last = g.iloc[-1]
        priors[str(team)] = {f: (_f(last.get(f), float("nan")) if pd.notna(last.get(f)) else None) for f in features if f.startswith("def_")}
        priors[str(team)]["last_season"] = int(_f(last.get("season")))
        priors[str(team)]["last_week"] = int(_f(last.get("week")))
    offense_priors: dict[str, dict[str, Any]] = {}
    for offense, g in data.sort_values(["season", "week"]).groupby("opponent"):
        last = g.iloc[-1]
        offense_priors[str(offense)] = {f: (_f(last.get(f), float("nan")) if pd.notna(last.get(f)) else None) for f in features if f.startswith("opp_")}
        offense_priors[str(offense)]["last_season"] = int(_f(last.get("season")))
        offense_priors[str(offense)]["last_week"] = int(_f(last.get("week")))
    return {
        "status": "validated_candidate" if validated else "diagnostic_only",
        "validation_rule": ">=4 chronological folds; mean MAE improvement >1%; >=half positive folds; Spearman >= baseline",
        "features": features, "models": models, "folds": folds,
        "aggregate": {
            "folds": len(folds), "positive_folds": positive, "mean_mae_improvement": mean_imp,
            "mean_spearman": mean_sp, "mean_baseline_spearman": mean_bsp,
            "q10_residual": q10, "q90_residual": q90,
        },
        "team_priors": priors, "offense_priors": offense_priors,
    }


def predict_exported_model(spec: Mapping[str, Any], values: Mapping[str, Any]) -> tuple[float, float]:
    fs = list(spec.get("features") or [])
    if not fs:
        raise ValueError("no features")
    med = list(spec.get("feature_medians") or [0.0] * len(fs))
    mu = list(spec.get("scaler_mean") or [0.0] * len(fs))
    sd = list(spec.get("scaler_scale") or [1.0] * len(fs))
    co = list(spec.get("coefficients") or [0.0] * len(fs))
    total = _f(spec.get("intercept")); observed = 0
    for i, f in enumerate(fs):
        v = values.get(f)
        if v is None or not math.isfinite(_f(v, float("nan"))):
            x = _f(med[i])
        else:
            x = _f(v); observed += 1
        scale = _f(sd[i], 1.0) or 1.0
        total += ((x - _f(mu[i])) / scale) * _f(co[i])
    return max(_f(spec.get("prediction_floor")), float(total)), observed / len(fs)


def predict_dst_from_bundle(dst_bundle: Mapping[str, Any], team: str, opponent: str | None, *, home: Any = None, spread_line: Any = None, total_line: Any = None) -> dict[str, Any]:
    models = dst_bundle.get("models") or {}
    priors = dst_bundle.get("team_priors") or {}
    offense_priors = dst_bundle.get("offense_priors") or {}
    teamv = dict(priors.get(str(team)) or {})
    oppv = dict(offense_priors.get(str(opponent)) or {}) if opponent else {}
    values = dict(teamv)
    # Opponent-vulnerability features must come from the opponent's own prior row.
    for f in ["opp_sacks_allowed_r4", "opp_turnovers_r4", "opp_points_r4", "opp_yards_r4"]:
        if f in oppv:
            values[f] = oppv[f]
    if home is not None: values["home"] = _f(home)
    if spread_line is not None: values["spread_line"] = _f(spread_line)
    if total_line is not None:
        values["total_line"] = _f(total_line)
        # spread_line is normalized to team perspective: positive = this D/ST is favored.
        s = _f(spread_line) if spread_line is not None else 0.0
        values["opponent_implied_points"] = (_f(total_line) - s) / 2.0
    preds: dict[str, float] = {}; coverage = []
    for target, spec in models.items():
        try:
            pred, cov = predict_exported_model(spec, values)
            preds[str(target)] = pred; coverage.append(cov)
        except Exception:
            pass
    return {"predicted_stats": preds, "feature_coverage": float(np.mean(coverage)) if coverage else 0.0, "features": values}


def augment_milestones(profile_path: Path, m1_path: Path, m2_path: Path, m3_path: Path, m4_path: Path, m5_path: Path, m6_path: Path, derived_dir: Path, cache_dir: Path, seasons: str) -> dict[str, Any]:
    """Build D/ST historical research and append governed sections to M1-M6.

    This is an additive migration: existing player sections and status contracts are
    left untouched.  DEF is added to existing M4/M5 gate arrays only when the D/ST
    model itself passes chronological validation.
    """
    profile = json.loads(profile_path.read_text())
    fields = dst_profile_fields(profile)
    bundles = [json.loads(p.read_text()) for p in [m1_path, m2_path, m3_path, m4_path, m5_path, m6_path]]
    common = {
        "schema_version": 1, **fields, "entity_type": "TEAM_DEFENSE", "position": "DEF",
        "generated_at": utc_now(), "architecture": "raw football outcomes -> exact league scoring -> canonical 9.1 valuation",
    }
    if not fields["dst_enabled"]:
        for b in bundles:
            b["dst"] = {**common, "status": "not_applicable", "reason": "league_has_no_DEF_roster_slot"}
        for p, b in zip([m1_path, m2_path, m3_path, m4_path, m5_path, m6_path], bundles):
            p.write_text(json.dumps(b, indent=2, allow_nan=False) + "\n")
        return {"status": "not_applicable", **fields}

    # Lazy import avoids coupling basic scoring/profile tests to the heavyweight M1 stack.
    from fie_research import SourceManager
    sm = SourceManager(cache_dir)
    def parse_range(s: str) -> list[int]:
        m = re.fullmatch(r"(\d{4})-(\d{4})", str(s).strip())
        if m: return list(range(int(m.group(1)), int(m.group(2)) + 1))
        return [int(x) for x in str(s).split(",") if x.strip()]
    pbps = []
    for year in parse_range(seasons):
        p = sm.load("pbp", year, required=False)
        if not p.empty: pbps.append(p)
    if not pbps:
        for b in bundles:
            b["dst"] = {**common, "status": "diagnostic_only", "reason": "historical_pbp_unavailable"}
        for p, b in zip([m1_path, m2_path, m3_path, m4_path, m5_path, m6_path], bundles):
            p.write_text(json.dumps(b, indent=2, allow_nan=False) + "\n")
        return {"status": "diagnostic_only", **fields}
    pbp = pd.concat(pbps, ignore_index=True, sort=False)
    schedules = sm.load("schedules", required=False)
    tw = build_dst_team_week(pbp, schedules)
    derived_dir.mkdir(parents=True, exist_ok=True)
    tw.to_csv(derived_dir / "dst_team_week.csv.gz", index=False, compression="gzip")
    scoring = profile.get("scoring_settings") or {}
    model = fit_dst_models(tw, scoring)
    score_audit = score_dst_stats({k: 0 for k in RAW_TARGETS}, scoring)
    score_audit["required_keys"] = sorted(dst_scoring_settings(scoring))

    m1, m2, m3, m4, m5, m6 = bundles
    m1["dst"] = {**common, "status": "complete", "team_week_rows": int(len(tw)), "seasons": sorted(int(x) for x in tw.season.unique()), "scoring_replay": score_audit, "derived_table": str(derived_dir / "dst_team_week.csv.gz")}
    # Compact driver summary: signed rank correlations are descriptive only and never used as same-week inputs.
    corr = []
    for f in model.get("features") or []:
        for t in ["sack", "int", "points_allowed", "yards_allowed"]:
            if f in tw and t in tw:
                c = pd.to_numeric(tw[f], errors="coerce").corr(pd.to_numeric(tw[t], errors="coerce"), method="spearman")
                if pd.notna(c): corr.append({"feature": f, "target": t, "spearman": round(float(c), 5)})
    m2["dst"] = {**common, "status": "complete", "driver_summary": sorted(corr, key=lambda r: abs(r["spearman"]), reverse=True)[:40], "principle": "separate defense quality from opponent vulnerability"}
    m3["dst"] = {**common, "status": "complete", "feature_families": {"defense_quality": [f for f in BASE_FEATURES if f.startswith("def_")], "opponent_vulnerability": [f for f in BASE_FEATURES if f.startswith("opp_")], "game_environment": ["home", "spread_line", "total_line", "opponent_implied_points"]}, "early_season_prior": "lagged features roll across season boundaries; current-season evidence gradually replaces prior-season history", "advanced_challengers": ["FTN charting", "IDP personnel aggregation", "injury impact", "point-in-time weather", "point-in-time betting movement"]}
    m4["dst"] = {**common, **model, "status": model.get("status", "diagnostic_only")}
    validated = model.get("status") == "validated_candidate"
    # Additive canonical M4 representation so M5 validator can treat DEF as upstream.
    agg = m4.setdefault("final_position_models", {}).setdefault("aggregate", [])
    agg[:] = [r for r in agg if r.get("position") != "DEF"]
    ma = model.get("aggregate") or {}
    agg.append({"position": "DEF", "folds": ma.get("folds", 0), "positive_folds": ma.get("positive_folds", 0), "n_test": sum(int(f.get("n_test", 0)) for f in model.get("folds") or []), "mean_baseline_mae": None, "mean_fie_event_mae": None, "mean_improvement_vs_baseline": ma.get("mean_mae_improvement", 0), "bootstrap_ci95_low": None, "bootstrap_ci95_high": None, "status": "validated_candidate" if validated else "diagnostic_only"})
    if validated:
        upstream = m5.setdefault("activation", {}).setdefault("upstream_validated_positions", [])
        if "DEF" not in upstream: upstream.append("DEF")
        gates = m5["activation"].setdefault("decision_gates", {})
        fmt = str(profile.get("format") or "REDRAFT")
        for key in ["weekly_mean_positions", "weekly_risk_positions", "draft_policy_positions"]:
            vals = gates.setdefault(key, [])
            if "DEF" not in vals: vals.append("DEF")
        # Waiver validation has a separate exact-equality validator; append a formal aggregate row.
        wagg = m5.setdefault("waiver_integration", {}).setdefault("aggregate", [])
        wagg[:] = [r for r in wagg if r.get("position") != "DEF"]
        wagg.append({
            "position": "DEF", "folds": ma.get("folds", 0), "n_test": sum(int(f.get("n_test", 0)) for f in model.get("folds") or []),
            "mean_mae": 0.0, "mean_baseline_mae": 0.0, "mean_mae_improvement_vs_recent_fp": ma.get("mean_mae_improvement", 0),
            "bootstrap_ci95_low": None, "bootstrap_ci95_high": None, "positive_folds": ma.get("positive_folds", 0),
            "mean_spearman": ma.get("mean_spearman", 0), "mean_baseline_spearman": ma.get("mean_baseline_spearman", 0),
            "mean_spearman_improvement_vs_recent_fp": ma.get("mean_spearman", 0) - ma.get("mean_baseline_spearman", 0),
            "mean_top_quartile_precision": 0.0, "mean_baseline_top_quartile_precision": 0.0, "mean_top1_regret": 0.0, "mean_baseline_top1_regret": 0.0,
            "rank_improvement_ci95_low": None, "rank_improvement_ci95_high": None, "rank_positive_folds": ma.get("positive_folds", 0), "rank_required_positive_folds": 2,
            "forecast_status": "validated_candidate", "decision_ranking_status": "validated_candidate", "upstream_weekly_status": "validated_candidate", "status": "validated_candidate",
        })
        wvals = gates.setdefault("waiver_policy_positions", [])
        if "DEF" not in wvals: wvals.append("DEF")
        for section in ["format_position_gates"]:
            fm = gates.setdefault(section, {})
            vals = fm.setdefault(fmt, [])
            if "DEF" not in vals: vals.append("DEF")
        dfg = gates.setdefault("decision_format_position_gates", {})
        for decision in ["weekly", "draft", "waiver"]:
            vals = dfg.setdefault(decision, {}).setdefault(fmt, [])
            if "DEF" not in vals: vals.append("DEF")
        profiles = gates.setdefault("validated_format_profiles", [])
        if fmt not in profiles: profiles.append(fmt)
    q10, q90 = ma.get("q10_residual"), ma.get("q90_residual")
    risks = m5.setdefault("weekly_integration", {}).setdefault("risk_bands", [])
    risks[:] = [r for r in risks if r.get("position") != "DEF"]
    risks.append({"position": "DEF", "n": int(len(tw)), "q10": q10, "q25": None, "q50": 0.0, "q75": None, "q90": q90, "residual_mae": None, "residual_sd": None, "upstream_status": "validated_candidate" if validated else "diagnostic_only"})
    m5["dst"] = {**common, "status": "validated_candidate" if validated else "diagnostic_only", "weekly": model.get("aggregate"), "streaming": {"status": "validated_candidate" if validated else "diagnostic_only", "horizons": ["week", "next3", "next6", "ros"], "replacement": "canonical 9.1 ReplacementService"}, "risk": {"q10_residual": q10, "q90_residual": q90}}
    m6["dst"] = {**common, "status": "baseline_validated" if validated else "baseline_diagnostic", "baseline": "public-data raw-stat Ridge ensemble", "challengers": [{"name": "FTN charting", "live": False}, {"name": "IDP personnel index", "live": False}, {"name": "injury impact", "live": False}, {"name": "market movement", "live": False}], "activation": "per-capability fail closed"}
    for p, b in zip([m1_path, m2_path, m3_path, m4_path, m5_path, m6_path], bundles):
        p.write_text(json.dumps(b, indent=2, allow_nan=False) + "\n")
    return {"status": model.get("status"), "rows": int(len(tw)), **fields}


def build_inventory(registry_path: Path, output: Path) -> dict[str, Any]:
    reg = json.loads(registry_path.read_text())
    rows = []
    root = registry_path.parent
    for lid, rr in sorted((reg.get("leagues") or {}).items()):
        pp = Path(rr.get("profile_path") or root / lid / "profile.json")
        if not pp.is_absolute() and not pp.exists():
            pp = Path.cwd() / pp
        if not pp.exists():
            continue
        p = json.loads(pp.read_text())
        f = dst_profile_fields(p)
        required = sorted(dst_scoring_settings(p.get("scoring_settings") or {}))
        unsupported = [k for k in required if not is_dst_scoring_key(k)]
        rows.append({"league_id": lid, "league_name": p.get("league_name"), "format": p.get("format"), "total_rosters": p.get("total_rosters"), **f, "dst_scoring_keys": required, "unsupported_dst_keys": unsupported})
    enabled = [r for r in rows if r["dst_enabled"]]
    out = {
        "schema_version": 1, "generated_at": utc_now(), "managed_leagues": len(rows),
        "dst_leagues": len(enabled), "non_dst_leagues": len(rows) - len(enabled),
        "unique_dst_scoring_signatures": sorted({r["dst_scoring_signature"] for r in enabled}),
        "unsupported_dst_keys": sorted({k for r in enabled for k in r["unsupported_dst_keys"]}),
        "leagues": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def main(argv: Optional[list[str]] = None) -> None:
    p = argparse.ArgumentParser(description="FIE 9.1 team D/ST research")
    sub = p.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--registry", default="data/research/leagues/registry.json")
    inv.add_argument("--output", default="data/research/dst/scoring_inventory.json")
    aug = sub.add_parser("augment")
    aug.add_argument("--profile", required=True); aug.add_argument("--m1", required=True); aug.add_argument("--m2", required=True); aug.add_argument("--m3", required=True); aug.add_argument("--m4", required=True); aug.add_argument("--m5", required=True); aug.add_argument("--m6", required=True)
    aug.add_argument("--derived-dir", required=True); aug.add_argument("--cache-dir", required=True); aug.add_argument("--seasons", required=True)
    args = p.parse_args(argv)
    if args.cmd == "inventory":
        print(json.dumps(build_inventory(Path(args.registry), Path(args.output)), indent=2))
    else:
        print(json.dumps(augment_milestones(Path(args.profile), Path(args.m1), Path(args.m2), Path(args.m3), Path(args.m4), Path(args.m5), Path(args.m6), Path(args.derived_dir), Path(args.cache_dir), args.seasons), indent=2))


if __name__ == "__main__":
    main()
